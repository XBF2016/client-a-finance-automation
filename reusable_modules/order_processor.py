"""
����������ģ��
���ڴ�����ƽ̨�������ݣ������ϲ�����׼���͵���
"""

import logging
import os
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from .platform_factory import create_all_platforms
from .platforms.base_platform import PlatformOperationsBase

logger = logging.getLogger("RPA_Logger")


class OrderProcessor:
    """
    订单处理器
    负责多平台订单数据的获取、合并、标准化和导出
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化订单处理器

        Args:
            config: 全局配置字典
        """
        self.config = config
        self.platforms: Dict[str, PlatformOperationsBase] = {}  # 平台实例字典
        self.raw_orders: Dict[str, List[Dict[str, Any]]] = (
            {}
        )  # 原始订单数据，按平台分组
        self.standardized_orders: List[Dict[str, Any]] = []  # 标准化后的订单数?

    def initialize_platforms(
        self,
        platform_names: Optional[List[str]] = None,
        share_browser_context: bool = True,
    ) -> bool:
        """
        初始化指定的平台

        Args:
            platform_names: 需要初始化的平台名称列表，如果为None则使用配置中的平台列�?            share_browser_context: 是否共享浏览器上下文，默认为True

        Returns:
            如果所有平台初始化成功返回True，否则返回False
        """
        try:
            # 如果没有指定平台名称，则使用配置中的平台列表
            if platform_names is None:
                platform_names = self.config.get("platforms", {}).get("enabled", [])

            # 创建平台实例
            self.platforms = create_all_platforms(
                platform_names, self.config, share_browser_context
            )

            return len(self.platforms) > 0
        except Exception as e:
            logger.error(f"初始化平台时出错: {e}")
            return False

    def login_all_platforms(self) -> bool:
        """
        登录所有平�?
        Returns:
            如果所有平台登录成功返回True，否则返回False
        """
        success_count = 0
        failed_platforms = []

        for platform_name, platform in self.platforms.items():
            try:
                logger.info(f"开始登录平�? {platform_name}")

                # 实现登录重试逻辑，最多尝�?次（初始 + 2次重试）
                login_success = False
                retry_count = 0
                max_retries = 2

                while not login_success and retry_count <= max_retries:
                    if retry_count > 0:
                        logger.warning(
                            f"平台 {platform_name} 登录失败，第 {retry_count} 次重�?.."
                        )
                        time.sleep(5)  # 按需求文档要求，每次重试间隔5�?
                    # 尝试登录
                    page, screenshot = platform.login()
                    login_success = platform.is_logged_in()

                    if login_success:
                        logger.info(f"平台 {platform_name} 登录成功")
                        success_count += 1
                        break
                    else:
                        retry_count += 1

                if not login_success:
                    logger.error(
                        f"平台 {platform_name} 登录失败，已尝试 {retry_count} 次重试"
                    )
                    failed_platforms.append(platform_name)
                    # 记录屏幕截图以便分析
                    error_screenshot = platform.take_screenshot(
                        f"login_failed_after_retries_{platform_name}"
                    )
                    logger.error(f"登录失败截图保存�? {error_screenshot}")

            except Exception as e:
                logger.error(f"登录平台 {platform_name} 时出�? {e}")
                failed_platforms.append(platform_name)
                # 尝试捕获错误屏幕截图
                try:
                    if hasattr(platform, "page") and platform.page:
                        error_screenshot = platform.take_screenshot(
                            f"login_error_{platform_name}"
                        )
                        logger.error(f"错误截图保存�? {error_screenshot}")
                except Exception as screenshot_error:
                    logger.error(f"尝试截图时出�? {screenshot_error}")

        # 如果有登录失败的平台，记录到日志
        if failed_platforms:
            logger.warning(f"以下平台登录失败: {', '.join(failed_platforms)}")

        return success_count == len(self.platforms)

    def fetch_all_orders(self, days: int = 7) -> bool:
        """
        获取所有平台的订单数据

        Args:
            days: 获取最近几天的订单，默�?�?
        Returns:
            如果所有平台获取订单成功返回True，否则返回False
        """
        self.raw_orders = {}
        success_count = 0
        failed_platforms = []

        for platform_name, platform in self.platforms.items():
            try:
                logger.info(f"开始获取平台 {platform_name} 的订单数据")

                # login()方法已确保我们在订单页面，直接获取订单
                # 不再调用navigate_to_orders_page避免重复导航

                # 获取订单数据
                orders = platform.get_orders(days)
                self.raw_orders[platform_name] = orders

                if orders:
                    logger.info(f"平台 {platform_name} 获取到 {len(orders)} 条订单")
                    success_count += 1
                else:
                    logger.warning(f"平台 {platform_name} 未获取到任何订单数据")
                    # 即使没有订单也算成功，因为这可能是正常情况
                    success_count += 1

            except Exception as e:
                logger.error(f"获取平台 {platform_name} 订单时出错: {e}")
                self.raw_orders[platform_name] = []
                failed_platforms.append(platform_name)

                # 尝试截图记录错误状态
                try:
                    if hasattr(platform, "page") and platform.page:
                        error_screenshot = platform.take_screenshot(
                            f"order_fetch_error_{platform_name}"
                        )
                        logger.error(f"错误截图保存至 {error_screenshot}")
                except Exception as screenshot_error:
                    logger.error(f"尝试截图时出错: {screenshot_error}")

        # 如果有获取订单失败的平台，记录到日志
        if failed_platforms:
            logger.warning(f"以下平台获取订单失败: {', '.join(failed_platforms)}")

        # 即使部分平台失败，只要有一个平台成功就继续流程
        return success_count > 0

    def standardize_all_orders(self) -> bool:
        """
        标准化所有平台的订单数据

        Returns:
            如果标准化成功返回True，否则返回False
        """
        self.standardized_orders = []

        try:
            for platform_name, orders in self.raw_orders.items():
                if not orders:
                    logger.info(f"平台 {platform_name} 没有订单数据，跳过标准化")
                    continue

                platform = self.platforms.get(platform_name)
                if not platform:
                    logger.warning(f"找不到平台 {platform_name} 的实例，跳过标准化")
                    continue

                logger.info(f"开始标准化平台 {platform_name} 的订单数据")
                std_orders = platform.standardize_orders(orders)
                logger.info(f"平台 {platform_name} 标准化后有 {len(std_orders)} 条订单")

                # 添加到标准化订单列表
                self.standardized_orders.extend(std_orders)

            logger.info(f"所有平台共标准化 {len(self.standardized_orders)} 条订单")
            return True

        except Exception as e:
            logger.error(f"标准化订单数据时出错: {e}")
            return False

    def export_to_excel(self) -> str:
        """
        将标准化的订单数据导出到Excel

        Returns:
            导出的Excel文件路径，如果导出失败则返回空字符串
        """
        try:
            # 检查是否有订单数据
            if not self.standardized_orders:
                logger.warning("没有订单数据可导出")
                # 创建一个空的DataFrame，但包含所有标准列
                df = pd.DataFrame(
                    columns=[
                        "订单号",
                        "平台来源",
                        "收件人姓名",
                        "联系电话",
                        "收货地址",
                        "商品名称",
                        "数量",
                        "下单时间",
                    ]
                )
            else:
                # 创建DataFrame
                df = pd.DataFrame(self.standardized_orders)

            # 创建输出目录
            output_dir = self.config.get("paths", {}).get(
                "output_folder", "data/output"
            )
            os.makedirs(output_dir, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"合并发货单_{timestamp}.xlsx"
            filepath = os.path.join(output_dir, filename)

            # 导出到Excel
            # 添加Excel样式
            with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="合并订单")

                # 获取工作簿
                worksheet = writer.sheets["合并订单"]

                # 导入相关模块
                from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
                from openpyxl.utils import get_column_letter

                # 设置标题行样式
                header_font = Font(bold=True, size=12, color="FFFFFF")
                header_fill = PatternFill(
                    start_color="4F81BD", end_color="4F81BD", fill_type="solid"
                )
                border = Border(
                    left=Side(style="thin"),
                    right=Side(style="thin"),
                    top=Side(style="thin"),
                    bottom=Side(style="thin"),
                )

                # 应用样式到标题行
                for col_num, column_title in enumerate(df.columns, 1):
                    cell = worksheet.cell(row=1, column=col_num)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.border = border
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                # 调整列宽
                for idx, col in enumerate(df.columns):
                    # 根据列内容的最大长度设置列宽
                    column_width = max(
                        df[col].astype(str).map(len).max(), len(str(col))
                    )
                    # 设置最小和最大宽度限制
                    column_width = max(10, min(column_width + 2, 50))
                    worksheet.column_dimensions[get_column_letter(idx + 1)].width = (
                        column_width
                    )

                # 设置单元格边框和对齐方式
                for row in range(2, len(df) + 2):  # 数据行
                    for col_num in range(1, len(df.columns) + 1):
                        cell = worksheet.cell(row=row, column=col_num)
                        cell.border = border

                        # 为不同类型的列设置不同的对齐方式
                        if col_num == df.columns.get_loc("数量") + 1:  # 数量列
                            cell.alignment = Alignment(horizontal="center")
                        elif col_num == df.columns.get_loc("联系电话") + 1:  # 电话列
                            cell.alignment = Alignment(horizontal="center")
                        else:
                            cell.alignment = Alignment(horizontal="left")

            logger.info(f"订单数据已导出到: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"导出订单数据到Excel时出错: {e}")
            return ""

    def close_all_platforms(self):
        """
        关闭所有平台资源
        """
        for platform_name, platform in self.platforms.items():
            try:
                logger.info(f"关闭平台 {platform_name} 资源")
                platform.close()
            except Exception as e:
                logger.warning(f"关闭平台 {platform_name} 资源时出错: {e}")

    def process(
        self,
        days: int = 7,
        platform_names: Optional[List[str]] = None,
        share_browser_context: bool = True,
    ) -> str:
        """
        执行完整的订单处理流程
        Args:
            days: 获取最近几天的订单，默认7天
            platform_names: 需要处理的平台名称列表，默认为None（使用配置中的平台列表）
            share_browser_context: 是否共享浏览器上下文，默认为True

        Returns:
            导出的Excel文件路径，如果处理失败则返回空字符串
        """
        try:
            # 初始化平台
            if not self.initialize_platforms(platform_names, share_browser_context):
                logger.error("初始化平台失败，终止处理")
                return ""

            # 登录所有平台
            if not self.login_all_platforms():
                logger.warning("部分平台登录失败，将继续处理已登录的平台")

            # 获取所有订单
            self.fetch_all_orders(days)

            # 标准化订单
            if not self.standardize_all_orders():
                logger.error("标准化订单失败，终止处理")
                return ""

            # 导出到Excel
            return self.export_to_excel()

        except Exception as e:
            logger.error(f"订单处理过程中出错: {e}")
            return ""
        finally:
            # 确保资源被释放
            self.close_all_platforms()
