"""
淘宝平台操作实现
实现了淘宝平台的特定操作逻辑
"""

import os
import time
import logging
import re
import pandas as pd
from typing import Dict, Any, List, Tuple
from datetime import datetime
from playwright.sync_api import Page

from ..taobao_operations import TaobaoOperations
from .base_platform import PlatformOperationsBase

logger = logging.getLogger("RPA_Logger")


class TaobaoPlatform(PlatformOperationsBase):
    """
    淘宝平台操作实现类
    """

    def __init__(self, config: Dict[str, Any], page: Page = None):
        """
        初始化淘宝平台操作

        Args:
            config: 全局配置字典
            page: 可选的Page对象，如果提供则使用现有页面
        """
        super().__init__(config, page)
        self.platform_config = config.get("platforms", {}).get("taobao", {})
        self.taobao_ops = TaobaoOperations(config)
        self.login_url = self.platform_config.get(
            "login_url", "https://login.taobao.com"
        )
        self.orders_url = self.platform_config.get(
            "orders_url",
            "https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm",
        )
        self.username = config.get("credentials", {}).get("username", "")
        self.password = config.get("credentials", {}).get("password", "")

        # 登录状态评分阈值，用于判断是否已登录
        self.login_score_threshold = self.platform_config.get(
            "login_score_threshold", 4
        )

    def login(self) -> Tuple[Page, str]:
        """
        登录淘宝平台。
        如果已登录，会确保页面在订单页。
        如果未登录，会执行登录流程，并尝试导航到订单页。

        Returns:
            包含Page对象和截图路径的元组
        """
        logger.info(f"[{self.platform_name}] 开始登录或验证流程")

        try:
            # is_logged_in 会尝试访问订单页，如果成功则返回True，且页面已在订单页
            if self.is_logged_in():
                logger.info(f"[{self.platform_name}] 用户已登录，并成功导航到订单页面")
                screenshot_path = self.take_screenshot(
                    "already_logged_in_on_orders_page"
                )
                return self.page, screenshot_path

            # 如果 is_logged_in 返回 False，说明被重定向到了登录页
            logger.info(f"[{self.platform_name}] 用户未登录，执行登录操作")

            # 确保页面对象存在
            if not self.page:
                # 如果有共享浏览器上下文，使用它创建页面
                if self.browser_context:
                    self.page = self.browser_context.new_page()
                else:
                    # 否则创建新的浏览器和页面
                    self.page = self.taobao_ops.create_page()

            # 切换到账号密码登录 (如果需要)
            try:
                password_login_button = self.page.locator('text="密码登录"').first
                if password_login_button.is_visible():
                    logger.info(f"[{self.platform_name}] 切换到账号密码登录")
                    password_login_button.click()
                    time.sleep(1)
            except Exception as e:
                logger.warning(
                    f"[{self.platform_name}] 查找'密码登录'按钮失败或不需要切换: {e}"
                )

            # 填写账号密码
            logger.info(f"[{self.platform_name}] 填写账号密码")
            self.page.fill("#fm-login-id", self.username)
            self.page.fill("#fm-login-password", self.password)

            # 点击登录按钮
            logger.info(f"[{self.platform_name}] 点击登录按钮")
            self.page.click('button[type="submit"]')

            # 等待登录完成，可能需要手动验证
            logger.info(f"[{self.platform_name}] 等待登录跳转，最长60秒...")
            try:
                # 等待URL变化，不再是登录页
                self.page.wait_for_url(
                    lambda url: "login.taobao.com" not in url, timeout=60000
                )
                logger.info(
                    f"[{self.platform_name}] 页面已跳转，当前URL: {self.page.url}"
                )
            except Exception as e:
                logger.error(f"[{self.platform_name}] 等待登录跳转超时或失败: {e}")
                screenshot_path = self.take_screenshot("login_redirect_failed")
                return self.page, screenshot_path

            # 再次检查是否登录成功并跳转到订单页
            if self.is_logged_in():
                logger.info(f"[{self.platform_name}] 登录成功，并已导航到订单页面")
                screenshot_path = self.take_screenshot("login_success_on_orders_page")
                return self.page, screenshot_path
            else:
                logger.warning(f"[{self.platform_name}] 登录后仍无法访问订单页面")
                screenshot_path = self.take_screenshot("login_failed_after_redirect")
                return self.page, screenshot_path

        except Exception as e:
            logger.error(f"[{self.platform_name}] 登录过程中出错: {e}")
            if self.page:
                screenshot_path = self.take_screenshot("login_error")
                return self.page, screenshot_path
            return None, ""

    def is_logged_in(self) -> bool:
        """
        通过直接访问订单页来检查是否已登录淘宝。
        如果成功，页面将停留在订单页。
        如果失败，页面将停留在登录页。

        Returns:
            如果已登录返回True，否则返回False
        """
        try:
            # 确保页面对象存在
            if not self.page:
                # 如果有共享浏览器上下文，使用它创建页面
                if self.browser_context:
                    self.page = self.browser_context.new_page()
                else:
                    # 否则创建新的浏览器和页面
                    self.page = self.taobao_ops.create_page()

            logger.info(
                f"[{self.platform_name}] 尝试访问订单页面以检查登录状态: {self.orders_url}"
            )
            self.page.goto(
                self.orders_url, wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(3)  # 等待可能的重定向

            current_url = self.page.url
            logger.info(f"[{self.platform_name}] 检查登录状态，当前URL: {current_url}")

            # 如果被重定向到登录页，则未登录
            if "login.taobao.com" in current_url:
                logger.info(f"[{self.platform_name}] 已重定向到登录页面，判断为未登录")
                return False

            # 检查订单页面的关键元素
            try:
                self.page.wait_for_selector(
                    'div:has-text("已买到的宝贝")', timeout=5000
                )
                logger.info(
                    f"[{self.platform_name}] 在订单页面找到关键元素，判断为已登录"
                )
                return True
            except Exception:
                # 如果关键元素未找到，但URL是正确的，也认为登录了
                if "buyertrade.taobao.com" in current_url:
                    logger.warning(
                        f"[{self.platform_name}] 未找到'已买到的宝贝'元素，但URL正确，判断为已登录"
                    )
                    return True

            logger.warning(
                f"[{self.platform_name}] 无法根据URL或页面内容判断登录状态，判断为未登录"
            )
            return False

        except Exception as e:
            logger.error(f"[{self.platform_name}] 检查登录状态时出错: {e}")
            return False

    def navigate_to_orders_page(self) -> Tuple[bool, str]:
        """
        导航到订单页面

        Returns:
            包含导航是否成功和截图路径的元组
        """
        try:
            # 直接访问订单页面
            logger.info(f"[{self.platform_name}] 导航到订单页面: {self.orders_url}")
            self.page.goto(self.orders_url)
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)  # 等待页面完全加载

            # 截图
            screenshot_path = self.take_screenshot("orders_page")

            # 验证是否成功导航到订单页面
            if "已买到的宝贝" in self.page.content():
                logger.info(f"[{self.platform_name}] 成功导航到订单页面")
                return True, screenshot_path
            else:
                logger.warning(f"[{self.platform_name}] 导航到订单页面失败")
                return False, screenshot_path

        except Exception as e:
            logger.error(f"[{self.platform_name}] 导航到订单页面时出错: {e}")
            if self.page:
                screenshot_path = self.take_screenshot("orders_page_error")
                return False, screenshot_path
            return False, ""

    def get_orders(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        通过点击"导出订单"按钮，下载并解析订单文件来获取淘宝订单数据。

        Args:
            days: 获取最近几天的订单，这个参数在这里可能不会被直接使用，
                  因为导出功能通常有自己的时间范围选择，我们会依赖它的默认行为或简单配置。

        Returns:
            订单数据列表
        """
        logger.info(
            f"[{self.platform_name}] 开始执行新的订单获取流程：通过导出文件获取"
        )
        try:
            # 1. 点击"导出订单"按钮
            export_button_selector = "div.exportBtn--jnP1Ru6K"
            logger.info(
                f"[{self.platform_name}] 查找'导出订单'按钮，选择器: {export_button_selector}"
            )

            try:
                export_button = self.page.locator(export_button_selector).first
                export_button.wait_for(state="visible", timeout=15000)
                logger.info(f"[{self.platform_name}] '导出订单'按钮可见，准备点击。")
                export_button.click()
            except Exception as e:
                logger.error(
                    f"[{self.platform_name}] 查找或点击'导出订单'按钮失败: {e}"
                )
                self.take_screenshot("export_button_click_failed")
                return []

            # 2. 等待并点击"下载订单"按钮，并同时监听下载事件
            download_button_selector = 'button.ant-btn-primary:has-text("下载订单")'
            logger.info(
                f"[{self.platform_name}] 等待'下载订单'按钮出现，选择器: {download_button_selector}"
            )

            try:
                download_button = self.page.locator(download_button_selector).first
                download_button.wait_for(
                    state="visible", timeout=20000
                )  # 等待弹窗和按钮出现
                logger.info(f"[{self.platform_name}] '下载订单'按钮可见。")

                # 开始监听下载事件
                with self.page.expect_download(timeout=60000) as download_info:
                    logger.info(
                        f"[{self.platform_name}] 点击'下载订单'按钮并等待文件下载..."
                    )
                    download_button.click()

                download = download_info.value
                logger.info(
                    f"[{self.platform_name}] 文件下载成功: {download.suggested_filename}"
                )

            except Exception as e:
                logger.error(
                    f"[{self.platform_name}] 等待或点击'下载订单'按钮失败，或下载超时: {e}"
                )
                self.take_screenshot("download_button_or_event_failed")
                return []

            # 3. 保存并解析下载的文件
            try:
                # 创建一个临时文件路径
                output_dir = self.config.get("paths", {}).get(
                    "output_folder", "data/output"
                )
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                # 检查下载文件的扩展名
                file_ext = os.path.splitext(download.suggested_filename)[1].lower()
                temp_file_path = os.path.join(
                    output_dir, f"temp_taobao_orders_{timestamp}{file_ext}"
                )

                download.save_as(temp_file_path)
                logger.info(
                    f"[{self.platform_name}] 订单文件已保存到: {temp_file_path}"
                )

                # 解析文件
                orders = self._parse_exported_file(temp_file_path)

                # 删除临时文件
                os.remove(temp_file_path)
                logger.info(f"[{self.platform_name}] 已删除临时文件: {temp_file_path}")

                return orders

            except Exception as e:
                logger.error(
                    f"[{self.platform_name}] 保存或解析导出的订单文件时出错: {e}"
                )
                self.take_screenshot("order_file_processing_failed")
                return []

        except Exception as e:
            logger.error(f"[{self.platform_name}] 'get_orders'方法发生严重错误: {e}")
            self.take_screenshot("get_orders_fatal_error")
            return []

    def _parse_exported_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析从淘宝导出的订单文件（支持Excel和CSV格式）。

        注意：此方法基于对淘宝导出文件格式的通用假设，如果淘宝更改格式，
        此处的列名和解析逻辑可能需要更新。

        Args:
            file_path: 下载的文件路径

        Returns:
            解析后的订单数据列表
        """
        logger.info(f"[{self.platform_name}] 开始解析订单文件: {file_path}")
        try:
            # 根据文件扩展名决定如何读取
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext in [".xlsx", ".xls"]:
                logger.info(
                    f"[{self.platform_name}] 检测到Excel文件，使用pandas的read_excel读取"
                )
                # 对于Excel文件，尝试直接读取
                df = pd.read_excel(file_path)
            else:
                # 对于CSV文件，保留原来的逻辑
                logger.info(f"[{self.platform_name}] 检测到CSV文件，尝试查找表头")
                header_row_index = 0
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f):
                            if "订单编号" in line and "买家会员名" in line:
                                header_row_index = i
                                break
                except Exception as e:
                    logger.debug(f"[{self.platform_name}] 使用UTF-8读取文件失败: {e}")
                    # 如果UTF-8失败，尝试GBK或GB18030
                    with open(file_path, "r", encoding="gb18030", errors="ignore") as f:
                        for i, line in enumerate(f):
                            if "订单编号" in line and "买家会员名" in line:
                                header_row_index = i
                                break

                logger.info(
                    f"[{self.platform_name}] 检测到文件表头在第 {header_row_index + 1} 行"
                )
                # 尝试不同的编码方式读取CSV
                try:
                    df = pd.read_csv(
                        file_path, encoding="utf-8", skiprows=header_row_index
                    )
                except Exception as e:
                    logger.debug(
                        f"[{self.platform_name}] 使用UTF-8编码读取CSV失败: {e}"
                    )
                    try:
                        df = pd.read_csv(
                            file_path, encoding="gb18030", skiprows=header_row_index
                        )
                    except Exception as e:
                        logger.debug(
                            f"[{self.platform_name}] 使用GB18030编码读取CSV失败: {e}"
                        )
                        df = pd.read_csv(
                            file_path, encoding="latin1", skiprows=header_row_index
                        )

            # 清理列名中的潜在空格
            df.columns = df.columns.str.strip()

            # 输出文件的所有列名，帮助调试
            logger.info(f"[{self.platform_name}] 文件包含以下列: {df.columns.tolist()}")

            # 检查关键列是否存在
            expected_columns = [
                "订单编号",
                "收货地址",
                "宝贝标题",
                "宝贝总数量",
                "订单创建时间",
            ]
            available_columns = df.columns.tolist()

            # 将期望列和实际列都转换为小写进行匹配，更加灵活
            expected_lower = [col.lower() for col in expected_columns]
            available_lower = [col.lower() for col in available_columns]

            # 检查每个期望的列是否都能在实际列中找到类似的
            missing_columns = []
            for i, expected_col in enumerate(expected_lower):
                found = False
                for avail_col in available_lower:
                    if expected_col in avail_col or avail_col in expected_col:
                        found = True
                        break
                if not found:
                    missing_columns.append(expected_columns[i])

            if missing_columns:
                logger.error(
                    f"[{self.platform_name}] 导出的文件缺少关键列: {missing_columns}, 实际列: {available_columns}"
                )
                self.take_screenshot("exported_file_missing_columns")
                # 即使缺少某些列，我们还是尝试处理，可能会用默认值替代

            # 对导出的数据进行预处理
            # 对地址信息进行解析
            address_column = None
            # 查找可能的地址列
            for col in df.columns:
                if "地址" in col or "收货" in col:
                    address_column = col
                    break

            if not address_column:
                logger.warning(f"[{self.platform_name}] 未找到包含地址信息的列")
                # 如果没有找到，看看能否找到与收货人/联系方式相关的列
                buyer_name_col = None
                buyer_phone_col = None
                buyer_address_col = None

                for col in df.columns:
                    if "收件人" in col or "收货人" in col or "姓名" in col:
                        buyer_name_col = col
                    elif "电话" in col or "手机" in col or "联系方式" in col:
                        buyer_phone_col = col
                    elif "地址" in col:
                        buyer_address_col = col

                # 如果找到了单独的列，直接使用
                if buyer_name_col:
                    df["buyer_name"] = df[buyer_name_col]
                else:
                    df["buyer_name"] = "Unknown"

                if buyer_phone_col:
                    df["buyer_phone"] = df[buyer_phone_col]
                else:
                    df["buyer_phone"] = "Unknown"

                if buyer_address_col:
                    df["buyer_address"] = df[buyer_address_col]
                else:
                    df["buyer_address"] = "Unknown"
            else:
                # 找到了地址列，尝试解析
                logger.info(f"[{self.platform_name}] 找到地址列: {address_column}")

                def parse_address_info(address_str):
                    if not isinstance(address_str, str):
                        return "Unknown", "Unknown", "Unknown"

                    # 尝试不同的地址格式
                    # 格式1: "张三,13800138000,浙江省杭州市余杭区文一西路969号,311121"
                    if "," in address_str:
                        parts = address_str.split(",")
                        name = parts[0].strip() if len(parts) > 0 else "Unknown"
                        phone = parts[1].strip() if len(parts) > 1 else "Unknown"
                        address = (
                            (",".join(parts[2:-1])).strip()
                            if len(parts) > 2
                            else "Unknown"
                        )
                        return name, phone, address

                    # 格式2: 可能的其他格式，根据需要添加更多解析逻辑
                    # 如果无法解析，返回默认值
                    return "Unknown", "Unknown", address_str

                try:
                    address_details = df[address_column].apply(parse_address_info)
                    df[["buyer_name", "buyer_phone", "buyer_address"]] = pd.DataFrame(
                        address_details.tolist(), index=df.index
                    )
                except Exception as parse_error:
                    logger.error(
                        f"[{self.platform_name}] 解析地址信息时出错: {parse_error}"
                    )
                    df["buyer_name"] = "Unknown"
                    df["buyer_phone"] = "Unknown"
                    df["buyer_address"] = df[address_column].astype(str)

            # 查找可能的订单编号列
            order_id_column = None
            for col in df.columns:
                if "订单" in col and ("编号" in col or "号" in col):
                    order_id_column = col
                    break

            if not order_id_column:
                logger.error(f"[{self.platform_name}] 未找到订单编号列，无法继续处理")
                return []

            # 查找可能的商品名称列
            item_name_column = None
            for col in df.columns:
                if "宝贝" in col and "标题" in col or "名称" in col:
                    item_name_column = col
                    break

            if not item_name_column:
                # 尝试找其他可能的列
                for col in df.columns:
                    if "商品" in col or "货品" in col:
                        item_name_column = col
                        break

            if not item_name_column:
                logger.warning(f"[{self.platform_name}] 未找到商品名称列，将使用默认值")
                # 添加一个虚拟列
                df["默认商品"] = "未知商品"
                item_name_column = "默认商品"

            # 查找可能的订单时间列
            order_time_column = None
            for col in df.columns:
                if ("订单" in col or "交易" in col) and (
                    "时间" in col or "日期" in col
                ):
                    order_time_column = col
                    break

            if not order_time_column:
                logger.warning(
                    f"[{self.platform_name}] 未找到订单时间列，将使用当前时间"
                )
                # 添加一个虚拟列
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                df["默认时间"] = current_time
                order_time_column = "默认时间"

            # 查找可能的数量列
            quantity_column = None
            for col in df.columns:
                if "数量" in col:
                    quantity_column = col
                    break

            if not quantity_column:
                logger.warning(f"[{self.platform_name}] 未找到数量列，将默认为1")
                df["默认数量"] = 1
                quantity_column = "默认数量"

            # 按订单编号分组
            try:
                orders_grouped = df.groupby(order_id_column)
            except Exception as e:
                logger.error(f"[{self.platform_name}] 按订单编号分组时出错: {e}")
                # 尝试将订单编号列转换为字符串
                df[order_id_column] = df[order_id_column].astype(str)
                try:
                    orders_grouped = df.groupby(order_id_column)
                except Exception as e:
                    logger.error(
                        f"[{self.platform_name}] 无法按订单编号分组，将每行作为一个订单处理: {e}"
                    )
                    # 如果还是失败，将每行作为一个单独的订单
                    df["unique_id"] = range(len(df))
                    orders_grouped = df.groupby("unique_id")

            parsed_orders = []
            logger.info(
                f"[{self.platform_name}] 文件包含 {len(orders_grouped)} 个独立订单，准备处理..."
            )

            for order_id, order_group in orders_grouped:
                try:
                    first_row = order_group.iloc[0]
                    items = []

                    # 循环处理订单中的每个商品
                    for _, item_row in order_group.iterrows():
                        # 获取商品名称，使用之前找到的列
                        item_name = item_row.get(item_name_column, "Unknown")

                        # 获取数量，使用之前找到的列
                        quantity = item_row.get(quantity_column, 1)

                        # 尝试查找价格列
                        price = "0.00"
                        for col in item_row.index:
                            if "价格" in col or "金额" in col:
                                price = item_row.get(col, "0.00")
                                break

                        items.append(
                            {"name": item_name, "price": price, "quantity": quantity}
                        )

                    buyer_info = {
                        "name": first_row.get("buyer_name", "Unknown"),
                        "phone": first_row.get("buyer_phone", "Unknown"),
                        "address": first_row.get("buyer_address", "Unknown"),
                    }

                    # 创建订单对象
                    order = {
                        "order_id": str(order_id),
                        "order_time": first_row.get(order_time_column, ""),
                        "items": items,
                        "buyer": buyer_info,
                        "platform": "taobao",
                    }
                    parsed_orders.append(order)
                except Exception as order_error:
                    logger.error(
                        f"[{self.platform_name}] 处理订单 {order_id} 时出错: {order_error}"
                    )

            logger.info(f"[{self.platform_name}] 成功解析 {len(parsed_orders)} 个订单")
            return parsed_orders

        except FileNotFoundError:
            logger.error(f"[{self.platform_name}] 订单文件未找到: {file_path}")
            return []
        except Exception as e:
            logger.error(f"[{self.platform_name}] 解析订单文件时发生错误: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return []

    def _get_buyer_info_from_detail(self, order_elem, order_id: str) -> Dict[str, str]:
        """
        从订单详情页获取买家信息

        Args:
            order_elem: 订单元素
            order_id: 订单ID

        Returns:
            买家信息字典
        """
        buyer_info = {"name": "Unknown", "phone": "Unknown", "address": "Unknown"}

        try:
            # 查找并点击订单详情按钮
            detail_button = order_elem.query_selector(
                '.order-operations a:has-text("订单详情")'
            )
            if not detail_button:
                detail_button = order_elem.query_selector(
                    '.order-operations a:has-text("详情")'
                )

            if not detail_button:
                logger.warning(
                    f"[{self.platform_name}] 找不到订单 {order_id} 的详情按钮"
                )
                return buyer_info

            # 在新标签页中打开详情页
            with self.page.context.expect_page() as new_page_info:
                detail_button.click()

            # 等待新页面打开
            detail_page = new_page_info.value
            detail_page.wait_for_load_state("networkidle")
            time.sleep(2)  # 等待页面完全加载

            # 截图记录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(
                self.config.get("paths", {}).get(
                    "screenshots_folder", "data/screenshots"
                ),
                f"order_detail_{order_id}_{timestamp}.png",
            )
            detail_page.screenshot(path=screenshot_path)
            logger.info(
                f"[{self.platform_name}] 订单 {order_id} 详情页截图: {screenshot_path}"
            )

            # 尝试查找收货信息区域
            try:
                # 可能的选择器模式
                address_selectors = [
                    ".logistic-info",
                    ".address-detail",
                    ".logistics-info",
                    ".addr-detail",
                    'div:has-text("收货地址")',
                    'div:has-text("收货信息")',
                ]

                address_section = None
                for selector in address_selectors:
                    address_section = detail_page.query_selector(selector)
                    if address_section:
                        logger.info(
                            f"[{self.platform_name}] 使用选择器 {selector} 找到收货信息"
                        )
                        break

                if address_section:
                    # 获取完整地址文本
                    address_text = address_section.text_content().strip()
                    logger.info(
                        f"[{self.platform_name}] 获取到收货信息文本: {address_text[:50]}..."
                    )

                    # 尝试解析地址、姓名和电话
                    # 使用正则表达式匹配姓名、电话和地址
                    # 姓名通常是2-4个中文字符
                    name_match = re.search(
                        r"收货人\s*[:：]\s*([^\s,，:：]{2,4})", address_text
                    )
                    if name_match:
                        buyer_info["name"] = name_match.group(1).strip()

                    # 电话通常是11位数字，可能有星号(*)脱敏
                    phone_match = re.search(
                        r"电话\s*[:：]\s*([\d\*]{7,11})", address_text
                    )
                    if not phone_match:
                        phone_match = re.search(
                            r"手机\s*[:：]\s*([\d\*]{7,11})", address_text
                        )
                    if not phone_match:
                        # 尝试直接匹配手机号格式
                        phone_match = re.search(r"(1[\d\*]{10})", address_text)

                    if phone_match:
                        buyer_info["phone"] = phone_match.group(1).strip()

                    # 地址通常比较长，包含省市区街道等
                    address_match = re.search(
                        r"地址\s*[:：]\s*(.+?)(?=电话|手机|$)", address_text
                    )
                    if not address_match:
                        # 如果没有找到明确的地址标签，尝试提取除了姓名和电话外的其他信息作为地址
                        if (
                            buyer_info["name"] != "Unknown"
                            and buyer_info["phone"] != "Unknown"
                        ):
                            # 移除已识别的姓名和电话信息
                            cleaned_text = address_text
                            if buyer_info["name"] != "Unknown":
                                cleaned_text = cleaned_text.replace(
                                    buyer_info["name"], ""
                                )
                            if buyer_info["phone"] != "Unknown":
                                cleaned_text = cleaned_text.replace(
                                    buyer_info["phone"], ""
                                )

                            # 移除常见标签
                            for tag in [
                                "收货人",
                                "电话",
                                "手机",
                                "地址",
                                "：",
                                ":",
                                "，",
                                ",",
                            ]:
                                cleaned_text = cleaned_text.replace(tag, "")

                            # 分割并清理文本
                            address_parts = [
                                part.strip()
                                for part in cleaned_text.split()
                                if part.strip()
                            ]
                            if address_parts:
                                # 取最长的部分作为地址
                                buyer_info["address"] = max(address_parts, key=len)
                    else:
                        buyer_info["address"] = address_match.group(1).strip()

                    logger.info(
                        f"[{self.platform_name}] 解析买家信息: 姓名={buyer_info['name']}, 电话={buyer_info['phone']}, 地址={buyer_info['address'][:20]}..."
                    )
                else:
                    logger.warning(
                        f"[{self.platform_name}] 找不到订单 {order_id} 的收货信息区域"
                    )
            except Exception as e:
                logger.error(
                    f"[{self.platform_name}] 解析订单 {order_id} 的收货信息时出错: {e}"
                )

            # 关闭详情页
            detail_page.close()

        except Exception as e:
            logger.error(f"[{self.platform_name}] 获取订单 {order_id} 详情时出错: {e}")

        return buyer_info

    def standardize_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        标准化淘宝订单数据

        Args:
            orders: 原始订单数据列表

        Returns:
            标准化后的订单数据列表
        """
        standardized = []

        try:
            # 获取字段映射配置
            field_mappings = self.platform_config.get("field_mappings", {})

            # 默认映射
            default_mappings = {
                "buyer_name": "收件人姓名",
                "phone": "联系电话",
                "address": "收货地址",
                "order_id": "订单号",
                "platform": "平台来源",
                "items": "商品名称",
                "quantity": "数量",
                "order_time": "下单时间",
            }

            # 合并默认映射和配置映射
            mappings = {**default_mappings, **field_mappings}

            for order in orders:
                # 提取基本信息
                order_id = order.get("order_id", "")
                order_time = order.get("order_time", "")
                items = order.get("items", [])
                buyer = order.get("buyer", {})

                # 计算商品总数量
                total_quantity = 0
                items_names = []

                for item in items:
                    # 提取商品数量，可能是字符串如"x2"或数字
                    quantity_str = item.get("quantity", "1")
                    if isinstance(quantity_str, str):
                        # 提取数字部分
                        quantity_match = re.search(r"(\d+)", quantity_str)
                        if quantity_match:
                            try:
                                quantity = int(quantity_match.group(1))
                            except ValueError:
                                quantity = 1
                        else:
                            quantity = 1
                    else:
                        quantity = int(quantity_str)

                    total_quantity += quantity
                    items_names.append(item.get("name", "Unknown Item"))

                # 商品名称合并为一个字符串，用逗号分隔
                items_str = ", ".join(items_names)

                # 构建标准化订单
                std_order = {
                    mappings["order_id"]: order_id,
                    mappings["platform"]: "淘宝",  # 使用中文平台名称
                    mappings["buyer_name"]: buyer.get("name", "Unknown"),
                    mappings["phone"]: buyer.get("phone", "Unknown"),
                    mappings["address"]: buyer.get("address", "Unknown"),
                    mappings["items"]: items_str,
                    mappings["quantity"]: total_quantity,
                    mappings["order_time"]: order_time,
                }

                standardized.append(std_order)

            logger.info(f"[{self.platform_name}] 标准化了 {len(standardized)} 条订单")
            return standardized

        except Exception as e:
            logger.error(f"[{self.platform_name}] 标准化订单数据时出错: {e}")
            return []
