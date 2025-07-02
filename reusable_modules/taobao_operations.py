"""
淘宝操作模块
包含与淘宝平台交互的通用操作
"""

import logging
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

from playwright.sync_api import Page, Browser, sync_playwright
from .selector_manager import SelectorManager

logger = logging.getLogger("RPA_Logger")

# 全局选择器管理器实例
_selector_manager = None


def get_selector_manager(config: dict) -> SelectorManager:
    """获取选择器管理器实例"""
    global _selector_manager
    if _selector_manager is None:
        _selector_manager = SelectorManager(config)
    return _selector_manager


def get_smart_selector(
    page: Page,
    config: Dict[str, Any],
    selector_name: str,
    target_description: Optional[str] = None,
    target_text: Optional[str] = None,
    target_attributes: Optional[Dict[str, Any]] = None,
) -> str:
    """
    智能获取选择器，如果失效则自动生成新的

    Args:
        page: Playwright页面对象
        config: 配置字典
        selector_name: 选择器名称
        target_description: 目标元素描述
        target_text: 目标元素文本
        target_attributes: 目标元素属性

    Returns:
        有效的选择器字符串

    Raises:
        TaobaoOperationError: 如果无法获取有效选择器
    """
    selector_manager = get_selector_manager(config)

    # 尝试从配置中获取默认选择器
    default_selector = config.get("selectors", {}).get(selector_name)
    if default_selector:
        # 将默认选择器添加到管理器
        selector_manager.add_selector(
            name=selector_name,
            selector=default_selector,
            description=target_description or selector_name,
            method="config_default",
            confidence=1.0,
        )

    # 获取智能选择器
    selector = selector_manager.get_selector(
        page, selector_name, target_description, target_text, target_attributes
    )

    if not selector:
        raise TaobaoOperationError(f"无法获取有效的选择器: {selector_name}")

    return selector


class TaobaoOperationError(Exception):
    """淘宝操作相关的自定义异常"""

    pass


class BrowserLaunchError(TaobaoOperationError):
    """浏览器启动失败异常"""

    pass


class NavigationError(TaobaoOperationError):
    """页面导航失败异常"""

    pass


class VerificationError(TaobaoOperationError):
    """页面验证失败异常"""

    pass


class PageLoadError(Exception):
    """页面加载错误异常类。"""

    pass


class LoginError(TaobaoOperationError):
    """登录失败异常"""

    pass


class TaobaoOperations:
    """淘宝操作类，封装了与淘宝相关的所有操作"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化淘宝操作类

        Args:
            config: 配置字典
        """
        self.config = config
        self.browser = None
        self.browser_context = None

        # 如果配置中已有浏览器上下文，直接使用
        if "browser_context" in config:
            self.browser_context = config["browser_context"]

    def launch_browser(self) -> Optional[Browser]:
        """
        启动浏览器实例。

        Returns:
            Browser: Playwright的Browser对象。

        Raises:
            BrowserLaunchError: 如果浏览器启动失败。
        """
        try:
            logger.info("正在启动浏览器...")

            # 获取浏览器配置
            browser_settings = self.config.get("browser_settings", {})
            headless = browser_settings.get("headless", False)
            slow_mo = browser_settings.get("slow_mo", 1000)

            # 尝试获取自定义浏览器路径
            browser_path = browser_settings.get("browser_path", "")
            use_system_browser = browser_settings.get("use_system_browser", False)
            browser_type = browser_settings.get("browser_type", "chromium").lower()

            # 获取用户数据相关配置
            enable_user_data = browser_settings.get("enable_user_data", False)
            user_data_dir_name = browser_settings.get(
                "user_data_dir_name", "user_data_dir"
            )

            logger.info(
                f"浏览器配置: headless={headless}, slow_mo={slow_mo}, browser_type={browser_type}"
            )
            if browser_path:
                logger.info(f"使用自定义浏览器路径: {browser_path}")
            if use_system_browser:
                logger.info("将使用系统已安装的浏览器")

            # 启动Playwright
            playwright = sync_playwright().start()

            # 根据配置选择浏览器类型
            if browser_type == "firefox":
                browser_launcher = playwright.firefox
            elif browser_type == "webkit":
                browser_launcher = playwright.webkit
            else:
                browser_launcher = playwright.chromium

            # 检查是否需要使用用户数据目录
            use_persistent_context = enable_user_data or (
                not headless and (browser_path or use_system_browser)
            )

            if use_persistent_context:
                # 设置用户数据目录
                user_data_dir = os.path.join(os.getcwd(), user_data_dir_name)
                os.makedirs(user_data_dir, exist_ok=True)
                logger.info(f"已启用用户数据保留，将使用目录: {user_data_dir}")

                # 创建一个标记文件，表示这是正常的配置文件
                flag_file = os.path.join(user_data_dir, "not_incognito.flag")
                with open(flag_file, "w") as f:
                    f.write(
                        f"Created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                logger.info(f"已创建非匿名模式标记文件: {flag_file}")

                # 准备持久化上下文的选项
                persistent_options = {"headless": headless, "slow_mo": slow_mo}

                # 如果指定了浏览器路径，添加相应选项
                if browser_path:
                    persistent_options["executable_path"] = browser_path
                elif use_system_browser:
                    # 尝试使用已安装的浏览器
                    if browser_type == "chromium":
                        # 常见的Chrome或基于Chromium的浏览器路径
                        possible_paths = [
                            # Chrome
                            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                            # Edge
                            "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                            "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
                            # 搜狗浏览器
                            "C:\\Program Files (x86)\\SogouExplorer\\SogouExplorer.exe",
                            "C:\\Program Files\\SogouExplorer\\SogouExplorer.exe",
                            # 其他常见路径
                            "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe",
                            "C:\\Users\\Administrator\\AppData\\Local\\Microsoft\\Edge\\Application\\msedge.exe",
                        ]

                        # 检查路径是否存在
                        for path in possible_paths:
                            if os.path.exists(path):
                                persistent_options["executable_path"] = path
                                logger.info(f"找到系统浏览器路径: {path}")
                                break

                # 设置其他选项
                persistent_options.update(
                    {
                        "viewport": {"width": 1280, "height": 800},
                        "ignore_default_args": ["--enable-automation"],
                        "args": [
                            "--no-sandbox",
                            "--disable-infobars",
                            "--disable-blink-features=AutomationControlled",
                            "--start-maximized",
                        ],
                    }
                )

                # 如果是搜狗浏览器，添加特殊处理
                if "SogouExplorer.exe" in persistent_options.get("executable_path", ""):
                    persistent_options["args"].append("--disable-extensions")

                logger.info(f"使用持久化上下文启动浏览器，选项: {persistent_options}")

                # 使用持久化上下文启动浏览器
                self.browser_context = browser_launcher.launch_persistent_context(
                    user_data_dir=user_data_dir, **persistent_options
                )

                # 将上下文对象保存到配置中，供后续使用
                self.config["browser_context"] = self.browser_context

                # 在这种情况下，我们将返回None作为Browser对象
                # 因为我们直接使用持久化上下文来创建页面
                logger.info("使用持久化上下文，不返回Browser对象")
                self.browser = None

            else:
                # 标准启动选项
                launch_options = {"headless": headless, "slow_mo": slow_mo}

                # 如果指定了浏览器路径，添加相应选项
                if browser_path:
                    launch_options["executable_path"] = browser_path

                logger.info(f"标准模式启动浏览器，选项: {launch_options}")
                self.browser = browser_launcher.launch(**launch_options)

            logger.info("浏览器启动成功。")
            return self.browser

        except Exception as e:
            error_msg = f"浏览器启动失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise BrowserLaunchError(error_msg) from e

    def create_page(self) -> Optional[Page]:
        """
        创建新的页面实例。

        Returns:
            Page: Playwright的Page对象。
        """
        try:
            # 如果已经有browser_context，直接使用它创建页面
            if self.browser_context:
                logger.info("使用现有浏览器上下文创建页面")
                return self.browser_context.new_page()

            # 如果没有browser_context但有browser，用browser创建页面
            if self.browser:
                logger.info("使用现有浏览器创建页面")
                return self.browser.new_page()

            # 如果既没有browser_context也没有browser，尝试启动浏览器
            logger.info("没有可用的浏览器，尝试启动新浏览器")
            try:
                # 尝试启动浏览器
                self.launch_browser()

                # 检查是否成功创建了browser_context或browser
                if self.browser_context:
                    logger.info("成功创建浏览器上下文，使用它创建页面")
                    return self.browser_context.new_page()
                elif self.browser:
                    logger.info("成功创建浏览器，使用它创建页面")
                    return self.browser.new_page()
                else:
                    logger.error("无法创建浏览器或浏览器上下文")
                    return None
            except Exception as e:
                logger.error(f"启动浏览器失败: {e}")
                return None
        except Exception as e:
            logger.error(f"创建页面时出错: {e}")
            return None

    def take_screenshot(self, page: Page, filename: Optional[str] = None) -> str:
        """
        截取页面截图。

        Args:
            page: Playwright的Page对象。
            filename: 截图文件名，可选。

        Returns:
            str: 截图文件路径。
        """
        try:
            # 创建截图目录
            screenshots_folder = self.config.get("paths", {}).get(
                "screenshots_folder", "data/screenshots"
            )
            os.makedirs(screenshots_folder, exist_ok=True)

            # 生成文件名
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            else:
                # 确保文件名以.png结尾
                if not filename.endswith(".png"):
                    filename = f"{filename}.png"

            filepath = os.path.join(screenshots_folder, filename)

            # 截图
            page.screenshot(path=filepath)
            logger.info(f"截图已保存: {filepath}")

            return filepath
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")
            return ""

    def navigate_to_taobao(self, page: Page) -> None:
        """
        导航到淘宝首页。

        Args:
            page: Playwright的Page对象。

        Raises:
            NavigationError: 如果导航失败。
        """
        try:
            taobao_url = self.config.get("urls", {}).get(
                "taobao_homepage", "https://www.taobao.com"
            )
            logger.info(f"正在导航到淘宝首页: {taobao_url}")

            # 导航到淘宝首页
            page.goto(taobao_url)

            # 等待页面加载
            page.wait_for_load_state("networkidle")
            time.sleep(2)  # 额外等待确保UI加载完成

            logger.info("已成功导航到淘宝首页")
        except Exception as e:
            error_msg = f"导航到淘宝首页失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise NavigationError(error_msg) from e

    def close(self):
        """
        关闭浏览器和相关资源。
        """
        try:
            if self.browser:
                logger.info("关闭浏览器")
                self.browser.close()
                self.browser = None

            if self.browser_context:
                logger.info("关闭浏览器上下文")
                self.browser_context.close()
                self.browser_context = None
        except Exception as e:
            logger.warning(f"关闭资源时出错: {e}")
