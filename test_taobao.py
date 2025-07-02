#!/usr/bin/env python3
"""
淘宝打开功能测试脚本
用于验证淘宝首页自动化打开功能是否正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reusable_modules.utils import setup_logger, load_config
from reusable_modules.taobao_operations import (
    open_taobao_homepage,
)


def test_taobao_open():
    """测试淘宝首页打开功能"""
    logger = setup_logger()

    try:
        logger.info("开始测试淘宝首页打开功能...")

        # 加载配置
        config = load_config()
        logger.info("配置加载成功")

        # 执行淘宝打开流程
        browser, page, screenshot_path = open_taobao_homepage(config)

        logger.info("✅ 测试成功！")
        logger.info(f"截图路径: {screenshot_path}")

        # 保持浏览器打开5秒
        import time

        time.sleep(5)

        # 清理资源
        page.close()
        browser.close()

        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_taobao_open()
    sys.exit(0 if success else 1)
