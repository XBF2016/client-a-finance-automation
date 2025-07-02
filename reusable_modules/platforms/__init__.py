"""
平台模块包
包含各个电商平台的操作实现
"""

from .base_platform import PlatformOperationsBase
from .taobao import TaobaoPlatform
from .jd import JDPlatform

__all__ = ["PlatformOperationsBase", "TaobaoPlatform", "JDPlatform"]
