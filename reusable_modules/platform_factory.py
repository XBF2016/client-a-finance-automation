"""
平台工厂模块
用于根据配置动态创建平台实例
"""

import logging
from typing import Dict, Any, Optional, List
from playwright.sync_api import Page, BrowserContext

from .platforms.base_platform import PlatformOperationsBase
from .platforms.taobao import TaobaoPlatform
from .platforms.jd import JDPlatform

logger = logging.getLogger("RPA_Logger")


def create_platform(
    platform_name: str,
    config: Dict[str, Any],
    page: Page = None,
    shared_context: BrowserContext = None,
) -> Optional[PlatformOperationsBase]:
    """
    创建平台实例

    Args:
        platform_name: 平台名称，如 'taobao', 'jd'
        config: 全局配置字典
        page: 可选的Page对象，如果提供则使用现有页面
        shared_context: 可选的共享浏览器上下文，用于多平台共享同一个浏览器实例

    Returns:
        平台实例，如果平台不支持则返回None
    """
    logger.info(f"创建平台实例: {platform_name}")

    # 如果提供了共享上下文，将其添加到配置中
    if shared_context:
        config = config.copy()  # 创建配置副本，避免修改原始配置
        config["browser_context"] = shared_context

    # 根据平台名称创建对应的实例
    if platform_name.lower() == "taobao":
        return TaobaoPlatform(config, page)
    elif platform_name.lower() == "jd":
        return JDPlatform(config, page)
    else:
        logger.error(f"不支持的平台: {platform_name}")
        return None


def get_available_platforms() -> list:
    """
    获取所有可用的平台列表

    Returns:
        平台名称列表
    """
    return ["taobao", "jd"]


def create_all_platforms(
    platform_names: List[str],
    config: Dict[str, Any],
    share_browser_context: bool = True,
) -> Dict[str, PlatformOperationsBase]:
    """
    创建指定的平台实例

    Args:
        platform_names: 需要创建的平台名称列表
        config: 全局配置字典
        share_browser_context: 是否共享浏览器上下文，默认为True

    Returns:
        平台实例字典，键为平台名称，值为平台实例
    """
    platforms = {}
    shared_context = None

    # 如果没有指定启用的平台，则使用所有可用平台
    if not platform_names:
        platform_names = get_available_platforms()

    # 创建每个平台的实例
    for i, platform_name in enumerate(platform_names):
        # 第一个平台创建浏览器上下文，后续平台共享
        if share_browser_context and i == 0:
            platform = create_platform(platform_name, config)
            if platform and hasattr(platform, "browser_context"):
                shared_context = platform.browser_context
        else:
            platform = create_platform(
                platform_name, config, shared_context=shared_context
            )

        if platform:
            platforms[platform_name] = platform

    logger.info(f"已创建 {len(platforms)} 个平台实例: {', '.join(platforms.keys())}")
    return platforms
