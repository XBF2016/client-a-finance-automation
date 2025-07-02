#!/usr/bin/env python3
"""
多平台架构测试脚本
用于测试平台接口和订单处理器
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reusable_modules.utils import setup_logger, load_config
from reusable_modules.platform_factory import create_platform, get_available_platforms
from reusable_modules.order_processor import OrderProcessor


def test_platform_factory():
    """测试平台工厂"""
    logger = setup_logger()

    try:
        logger.info("开始测试平台工厂...")

        # 加载配置
        config = load_config()
        logger.info("配置加载成功")

        # 获取可用平台列表
        available_platforms = get_available_platforms()
        logger.info(f"可用平台: {available_platforms}")

        # 测试创建淘宝平台
        taobao_platform = create_platform("taobao", config)
        if taobao_platform:
            logger.info("✅ 淘宝平台创建成功")
        else:
            logger.error("❌ 淘宝平台创建失败")
            return False

        # 测试创建京东平台
        jd_platform = create_platform("jd", config)
        if jd_platform:
            logger.info("✅ 京东平台创建成功")
        else:
            logger.error("❌ 京东平台创建失败")
            return False

        # 测试创建不存在的平台
        unknown_platform = create_platform("unknown", config)
        if unknown_platform is None:
            logger.info("✅ 正确处理了不存在的平台")
        else:
            logger.error("❌ 未正确处理不存在的平台")
            return False

        logger.info("平台工厂测试成功")
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


def test_order_processor():
    """测试订单处理器"""
    logger = setup_logger()

    try:
        logger.info("开始测试订单处理器...")

        # 加载配置
        config = load_config()
        logger.info("配置加载成功")

        # 创建订单处理器
        processor = OrderProcessor(config)
        logger.info("订单处理器创建成功")

        # 测试初始化平台
        if processor.initialize_platforms():
            logger.info("✅ 平台初始化成功")
        else:
            logger.error("❌ 平台初始化失败")
            return False

        # 注意：以下测试需要真实的账号密码，可能会打开浏览器
        # 如果不想执行实际的登录和抓取操作，可以注释掉这些测试

        # # 测试登录
        # logger.info("测试登录功能 (将打开浏览器)")
        # if processor.login_all_platforms():
        #     logger.info("✅ 所有平台登录成功")
        # else:
        #     logger.warning("⚠️ 部分平台登录失败")

        # # 测试获取订单
        # logger.info("测试获取订单功能")
        # if processor.fetch_all_orders(days=7):
        #     logger.info("✅ 获取订单成功")
        # else:
        #     logger.warning("⚠️ 部分平台获取订单失败")

        # # 测试标准化订单
        # logger.info("测试标准化订单功能")
        # if processor.standardize_all_orders():
        #     logger.info("✅ 标准化订单成功")
        # else:
        #     logger.error("❌ 标准化订单失败")
        #     return False

        # # 测试导出Excel
        # logger.info("测试导出Excel功能")
        # excel_path = processor.export_to_excel()
        # if excel_path:
        #     logger.info(f"✅ 导出Excel成功: {excel_path}")
        # else:
        #     logger.error("❌ 导出Excel失败")
        #     return False

        logger.info("订单处理器测试成功")
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False
    finally:
        # 确保资源被释放
        if "processor" in locals():
            processor.close_all_platforms()


if __name__ == "__main__":
    print("开始测试多平台架构...")

    # 测试平台工厂
    factory_success = test_platform_factory()
    print(f"平台工厂测试: {'成功' if factory_success else '失败'}")

    # 测试订单处理器
    processor_success = test_order_processor()
    print(f"订单处理器测试: {'成功' if processor_success else '失败'}")

    # 总体结果
    success = factory_success and processor_success
    print(f"测试总结: {'全部通过' if success else '部分失败'}")

    sys.exit(0 if success else 1)
