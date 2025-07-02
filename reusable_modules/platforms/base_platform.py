from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
from playwright.sync_api import Page
from datetime import datetime
import logging
import os

logger = logging.getLogger("RPA_Logger")


class PlatformOperationsBase(ABC):
    """
    所有平台操作的抽象基类。
    定义了与电商平台交互所需的标准化接口。
    """

    def __init__(self, config: Dict[str, Any], page: Page = None):
        """
        初始化平台操作基类。

        Args:
            config: 全局配置字典。
            page: Playwright 的 Page 对象，用于与浏览器交互。如果为None，将在需要时创建。
        """
        self.config = config
        self.platform_name = self.__class__.__name__.replace("Platform", "").lower()
        self.page = page
        self.browser = None
        self.browser_context = None

        # 检查是否提供了共享的浏览器上下文
        if "browser_context" in config:
            self.browser_context = config["browser_context"]
            logger.info(f"[{self.platform_name}] 使用共享浏览器上下文")

        logger.info(f"[{self.platform_name}] 平台操作已初始化。")

    @abstractmethod
    def login(self) -> Tuple[Page, str]:
        """
        执行平台登录。

        Returns:
            (已登录的Page对象, 登录过程的截图路径)
        """
        pass

    @abstractmethod
    def is_logged_in(self) -> bool:
        """
        检查当前是否处于登录状态。

        Returns:
            如果已登录，返回 True，否则返回 False。
        """
        pass

    @abstractmethod
    def navigate_to_orders_page(self) -> Tuple[bool, str]:
        """
        导航到"已卖出宝贝"或类似的订单列表页面。

        Returns:
            (导航是否成功, 截图路径)
        """
        pass

    @abstractmethod
    def get_orders(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        从当前订单列表页面抓取订单数据。

        Args:
            days: 获取最近几天的订单，默认7天

        Returns:
            一个包含原始订单数据的字典列表。
        """
        pass

    @abstractmethod
    def standardize_orders(
        self, raw_orders: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        将平台的原始订单数据标准化为统一格式。

        Args:
            raw_orders: 从 get_orders() 获取的原始订单列表。

        Returns:
            一个包含标准化订单数据的字典列表。标准字段包括：
            - order_id: 订单号
            - platform: 平台来源
            - buyer_name: 收件人姓名
            - phone: 联系电话
            - address: 收货地址
            - items: 商品信息列表
            - quantity: 数量
            - order_time: 下单时间
        """
        pass

    def take_screenshot(self, name: str) -> str:
        """
        截取当前页面，并以标准格式保存。

        Args:
            name: 截图名称

        Returns:
            截图文件的保存路径。
        """
        if not self.page:
            logger.warning(f"[{self.platform_name}] 无法截图：页面对象不存在")
            return ""

        try:
            # 创建截图目录
            screenshot_dir = self.config.get("paths", {}).get(
                "screenshot_folder", "data/screenshots"
            )
            os.makedirs(screenshot_dir, exist_ok=True)

            # 生成截图文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{self.platform_name}_{timestamp}.png"
            filepath = os.path.join(screenshot_dir, filename)

            # 保存截图
            self.page.screenshot(path=filepath)
            logger.info(f"[{self.platform_name}] 截图已保存: {filepath}")

            return filepath
        except Exception as e:
            logger.error(f"[{self.platform_name}] 截图时出错: {e}")
            return ""

    def close(self):
        """
        关闭平台相关的所有资源。
        """
        try:
            if (
                self.page and not self.browser_context
            ):  # 如果使用共享上下文，不要关闭页面
                logger.info(f"[{self.platform_name}] 关闭页面")
                self.page.close()
                self.page = None

            if (
                self.browser and not self.browser_context
            ):  # 如果使用共享上下文，不要关闭浏览器
                logger.info(f"[{self.platform_name}] 关闭浏览器")
                self.browser.close()
                self.browser = None
        except Exception as e:
            logger.warning(f"[{self.platform_name}] 关闭资源时出错: {e}")
