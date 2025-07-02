"""
京东平台操作实现
实现了京东平台的特定操作逻辑
"""

import os
import time
import logging
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime
from playwright.sync_api import Page

from ..taobao_operations import TaobaoOperations
from .base_platform import PlatformOperationsBase

logger = logging.getLogger("RPA_Logger")


class JDPlatform(PlatformOperationsBase):
    """
    京东平台操作实现类
    """

    def __init__(self, config: Dict[str, Any], page: Page = None):
        """
        初始化京东平台操作

        Args:
            config: 全局配置字典
            page: 可选的Page对象，如果提供则使用现有页面
        """
        super().__init__(config, page)
        self.platform_config = config.get("platforms", {}).get("jd", {})
        self.taobao_ops = TaobaoOperations(config)  # 暂时复用淘宝的浏览器操作
        self.login_url = self.platform_config.get(
            "login_url", "https://passport.jd.com/new/login.aspx"
        )
        self.orders_url = self.platform_config.get(
            "orders_url", "https://order.jd.com/center/list.action"
        )
        self.username = config.get("credentials", {}).get("jd_username", "")
        self.password = config.get("credentials", {}).get("jd_password", "")

        # 登录状态评分阈值，用于判断是否已登录
        self.login_score_threshold = self.platform_config.get(
            "login_score_threshold", 3
        )

    def login(self) -> Tuple[Page, str]:
        """
        登录京东平台

        Returns:
            包含Page对象和截图路径的元组
        """
        logger.info(f"[{self.platform_name}] 开始登录流程")

        try:
            # 检查是否已经登录
            if self.is_logged_in():
                logger.info(f"[{self.platform_name}] 检测到用户已经登录，跳过登录流程")
                screenshot_path = self.take_screenshot("already_logged_in")
                return self.page, screenshot_path

            # 如果未登录，执行登录流程
            logger.info(f"[{self.platform_name}] 用户未登录，开始登录流程")

            # 如果没有页面对象，创建一个
            if not self.page:
                # 如果有共享浏览器上下文，使用它创建页面
                if self.browser_context:
                    self.page = self.browser_context.new_page()
                else:
                    # 否则创建新的浏览器和页面
                    self.page = self.taobao_ops.create_page()

            # 访问登录页面
            logger.info(f"[{self.platform_name}] 访问登录页面: {self.login_url}")
            self.page.goto(self.login_url)

            # 等待页面加载
            self.page.wait_for_load_state("networkidle")

            # 切换到账号密码登录
            logger.info(f"[{self.platform_name}] 切换到账号密码登录")
            self.page.click("div.login-tab-r")
            time.sleep(1)

            # 填写账号密码
            logger.info(f"[{self.platform_name}] 填写账号密码")
            self.page.fill("#loginname", self.username)
            self.page.fill("#nloginpwd", self.password)

            # 点击登录按钮
            logger.info(f"[{self.platform_name}] 点击登录按钮")
            self.page.click("div.login-btn a")

            # 等待登录完成，可能需要手动验证
            logger.info(f"[{self.platform_name}] 等待登录完成，可能需要手动验证")
            self.page.wait_for_load_state("networkidle")

            # 等待一段时间，让用户完成可能的验证
            time.sleep(5)

            # 检查登录状态
            if self.is_logged_in():
                logger.info(f"[{self.platform_name}] 登录成功")
                screenshot_path = self.take_screenshot("login_success")
                return self.page, screenshot_path
            else:
                logger.warning(f"[{self.platform_name}] 登录失败或需要手动验证")
                screenshot_path = self.take_screenshot("login_failed")
                return self.page, screenshot_path

        except Exception as e:
            logger.error(f"[{self.platform_name}] 登录过程中出错: {e}")
            if self.page:
                screenshot_path = self.take_screenshot("login_error")
                return self.page, screenshot_path
            return None, ""

    def is_logged_in(self) -> bool:
        """
        检查是否已登录京东

        Returns:
            如果已登录返回True，否则返回False
        """
        try:
            # 如果没有页面对象，创建一个
            if not self.page:
                # 如果有共享浏览器上下文，使用它创建页面
                if self.browser_context:
                    self.page = self.browser_context.new_page()
                else:
                    # 否则创建新的浏览器和页面
                    self.page = self.taobao_ops.create_page()

            # 访问京东首页
            self.page.goto("https://www.jd.com")
            self.page.wait_for_load_state("networkidle")

            # 截图记录当前状态
            self.take_screenshot("login_check")

            # 检查登录状态的特征
            login_score = 0

            # 检查是否有用户名显示
            if self.page.query_selector("#ttbar-login .nickname"):
                login_score += 2

            # 检查是否有"我的订单"链接
            if self.page.query_selector('a:text("我的订单")'):
                login_score += 1

            # 检查是否有"我的京东"链接
            if self.page.query_selector('a:text("我的京东")'):
                login_score += 1

            logger.info(
                f"[{self.platform_name}] 登录状态评分: {login_score}/{self.login_score_threshold}, 阈值: {self.login_score_threshold}"
            )
            logger.info(
                f"[{self.platform_name}] 登录状态判断: {'已登录' if login_score >= self.login_score_threshold else '未登录'}"
            )

            # 如果评分达到阈值，认为已登录
            return login_score >= self.login_score_threshold

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
            # 确保已登录
            if not self.is_logged_in():
                logger.warning(f"[{self.platform_name}] 用户未登录，无法访问订单页面")
                return False, ""

            # 直接访问订单页面
            logger.info(f"[{self.platform_name}] 导航到订单页面: {self.orders_url}")
            self.page.goto(self.orders_url)
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)  # 等待页面完全加载

            # 截图
            screenshot_path = self.take_screenshot("orders_page")

            # 验证是否成功导航到订单页面
            if "订单中心" in self.page.content():
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
        获取京东订单数据

        Args:
            days: 获取最近几天的订单，默认7天

        Returns:
            订单数据列表
        """
        try:
            # 导航到订单页面
            success, _ = self.navigate_to_orders_page()
            if not success:
                logger.error(
                    f"[{self.platform_name}] 无法访问订单页面，无法获取订单数据"
                )
                return []

            # 开始抓取订单数据
            logger.info(f"[{self.platform_name}] 开始抓取订单数据")

            # 选择时间范围（最近7天）
            try:
                # 点击时间选择下拉框
                self.page.click("#ordersHost .order-date-item")
                time.sleep(1)

                # 选择最近days天
                if days <= 7:
                    self.page.click(
                        "#ordersHost .order-date-item li:nth-child(1)"
                    )  # 近三个月
                elif days <= 30:
                    self.page.click(
                        "#ordersHost .order-date-item li:nth-child(2)"
                    )  # 近三个月
                else:
                    self.page.click(
                        "#ordersHost .order-date-item li:nth-child(3)"
                    )  # 近一年

                time.sleep(2)  # 等待页面刷新
            except Exception as e:
                logger.warning(f"[{self.platform_name}] 选择时间范围失败: {e}")

            # 等待订单列表加载
            try:
                self.page.wait_for_selector(".order-item", timeout=10000)
            except Exception:
                logger.warning(
                    f"[{self.platform_name}] 等待订单列表超时，可能没有订单或页面结构变化"
                )

            # 获取所有订单项
            order_elements = self.page.query_selector_all(".order-item")
            logger.info(f"[{self.platform_name}] 找到 {len(order_elements)} 个订单")

            orders = []
            for index, order_elem in enumerate(order_elements):
                try:
                    # 提取订单ID
                    order_id_elem = order_elem.query_selector(".order-number")
                    order_id = (
                        order_id_elem.text_content()
                        .strip()
                        .replace("订单号：", "")
                        .strip()
                        if order_id_elem
                        else "Unknown"
                    )

                    # 提取订单时间
                    order_time_elem = order_elem.query_selector(".order-time")
                    order_time = (
                        order_time_elem.text_content().strip()
                        if order_time_elem
                        else ""
                    )

                    # 提取商品信息
                    items = []
                    item_elems = order_elem.query_selector_all(".goods-item")
                    for item_elem in item_elems:
                        item_title_elem = item_elem.query_selector(".goods-name")
                        item_title = (
                            item_title_elem.text_content().strip()
                            if item_title_elem
                            else "Unknown"
                        )

                        item_price_elem = item_elem.query_selector(".goods-price")
                        item_price = (
                            item_price_elem.text_content().strip()
                            if item_price_elem
                            else "0.00"
                        )

                        # 尝试获取商品数量
                        item_quantity_elem = item_elem.query_selector(".goods-number")
                        item_quantity = (
                            item_quantity_elem.text_content().strip()
                            if item_quantity_elem
                            else "1"
                        )

                        items.append(
                            {
                                "name": item_title,
                                "price": item_price,
                                "quantity": item_quantity,
                            }
                        )

                    # 点击订单详情按钮获取买家信息
                    buyer_info = self._get_buyer_info_from_detail(order_elem, order_id)

                    # 构建订单对象
                    order = {
                        "order_id": order_id,
                        "order_time": order_time,
                        "items": items,
                        "buyer": buyer_info,
                        "platform": "jd",
                    }

                    orders.append(order)
                    logger.info(
                        f"[{self.platform_name}] 成功解析订单 {index+1}/{len(order_elements)}: {order_id}"
                    )

                except Exception as e:
                    logger.error(f"[{self.platform_name}] 解析订单时出错: {e}")

            if not orders:
                logger.warning(f"[{self.platform_name}] 未找到任何订单数据")

            return orders

        except Exception as e:
            logger.error(f"[{self.platform_name}] 获取订单数据时出错: {e}")
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
                '.order-detail a:has-text("订单详情")'
            )
            if not detail_button:
                detail_button = order_elem.query_selector(
                    '.order-operate a:has-text("详情")'
                )
            if not detail_button:
                detail_button = order_elem.query_selector('a:has-text("查看详情")')

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
                f"jd_order_detail_{order_id}_{timestamp}.png",
            )
            detail_page.screenshot(path=screenshot_path)
            logger.info(
                f"[{self.platform_name}] 订单 {order_id} 详情页截图: {screenshot_path}"
            )

            # 尝试查找收货信息区域
            try:
                # 可能的选择器模式
                address_selectors = [
                    ".consignee-info",
                    ".consignee-detail",
                    ".address-detail",
                    ".consignee-address",
                    'div:has-text("收货人信息")',
                    'div:has-text("收货地址")',
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
                        r"收货人[：:]\s*([^\s,，:：]{2,4})", address_text
                    )
                    if name_match:
                        buyer_info["name"] = name_match.group(1).strip()

                    # 电话通常是11位数字，可能有星号(*)脱敏
                    phone_match = re.search(r"电话[：:]\s*([\d\*]{7,11})", address_text)
                    if not phone_match:
                        phone_match = re.search(
                            r"手机[：:]\s*([\d\*]{7,11})", address_text
                        )
                    if not phone_match:
                        # 尝试直接匹配手机号格式
                        phone_match = re.search(r"(1[\d\*]{10})", address_text)

                    if phone_match:
                        buyer_info["phone"] = phone_match.group(1).strip()

                    # 地址通常比较长，包含省市区街道等
                    address_match = re.search(
                        r"地址[：:]\s*(.+?)(?=电话|手机|$)", address_text
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
        标准化京东订单数据

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
                    mappings["platform"]: "京东",  # 使用中文平台名称
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
