"""
自动选择器测试脚本
演示自动选择器生成和管理功能
"""

import logging
import yaml
from playwright.sync_api import sync_playwright
from reusable_modules.auto_selector import AutoSelectorGenerator
from reusable_modules.selector_manager import SelectorManager
from reusable_modules.taobao_operations import (
    open_taobao_homepage,
    get_selector_manager,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config():
    """加载配置文件"""
    with open("config/config.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_auto_selector_generation():
    """测试自动选择器生成功能"""
    logger.info("开始测试自动选择器生成功能...")

    config = load_config()

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(
            headless=config["browser_settings"]["headless"],
            slow_mo=config["browser_settings"]["slow_mo"],
        )

        page = browser.new_page()

        try:
            # 导航到淘宝首页
            page.goto(config["urls"]["taobao_homepage"])
            page.wait_for_load_state("domcontentloaded")

            # 创建自动选择器生成器
            auto_generator = AutoSelectorGenerator(config)

            # 测试生成搜索框选择器
            logger.info("测试生成搜索框选择器...")
            search_selector = auto_generator.generate_selector(
                page=page,
                target_description="搜索输入框",
                target_text="搜索",
                target_attributes={"type": "text", "placeholder": "搜索"},
            )

            if search_selector:
                logger.info(f"生成的搜索框选择器: {search_selector}")

                # 验证选择器是否有效
                element = page.query_selector(search_selector)
                if element and element.is_visible():
                    logger.info("✅ 搜索框选择器验证成功")
                else:
                    logger.warning("❌ 搜索框选择器验证失败")
            else:
                logger.warning("❌ 无法生成搜索框选择器")

            # 测试生成Logo选择器
            logger.info("测试生成Logo选择器...")
            logo_selector = auto_generator.generate_selector(
                page=page, target_description="淘宝Logo", target_text="淘宝"
            )

            if logo_selector:
                logger.info(f"生成的Logo选择器: {logo_selector}")

                # 验证选择器是否有效
                element = page.query_selector(logo_selector)
                if element and element.is_visible():
                    logger.info("✅ Logo选择器验证成功")
                else:
                    logger.warning("❌ Logo选择器验证失败")
            else:
                logger.warning("❌ 无法生成Logo选择器")

            # 测试生成登录按钮选择器
            logger.info("测试生成登录按钮选择器...")
            login_selector = auto_generator.generate_selector(
                page=page, target_description="登录按钮", target_text="登录"
            )

            if login_selector:
                logger.info(f"生成的登录按钮选择器: {login_selector}")

                # 验证选择器是否有效
                element = page.query_selector(login_selector)
                if element and element.is_visible():
                    logger.info("✅ 登录按钮选择器验证成功")
                else:
                    logger.warning("❌ 登录按钮选择器验证失败")
            else:
                logger.warning("❌ 无法生成登录按钮选择器")

        except Exception as e:
            logger.error(f"测试过程中出错: {e}")
        finally:
            browser.close()


def test_selector_manager():
    """测试选择器管理器功能"""
    logger.info("开始测试选择器管理器功能...")

    config = load_config()

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(
            headless=config["browser_settings"]["headless"],
            slow_mo=config["browser_settings"]["slow_mo"],
        )

        page = browser.new_page()

        try:
            # 导航到淘宝首页
            page.goto(config["urls"]["taobao_homepage"])
            page.wait_for_load_state("domcontentloaded")

            # 创建选择器管理器
            selector_manager = SelectorManager(config)

            # 测试添加选择器
            logger.info("测试添加选择器...")
            success = selector_manager.add_selector(
                name="test_search_input",
                selector="#q",
                description="测试搜索输入框",
                method="manual",
                confidence=1.0,
                attributes={"type": "text"},
                text_content="",
            )

            if success:
                logger.info("✅ 添加选择器成功")
            else:
                logger.error("❌ 添加选择器失败")

            # 测试获取选择器
            logger.info("测试获取选择器...")
            selector = selector_manager.get_selector(
                page=page,
                selector_name="test_search_input",
                target_description="测试搜索输入框",
            )

            if selector:
                logger.info(f"✅ 获取选择器成功: {selector}")
            else:
                logger.warning("❌ 获取选择器失败")

            # 测试选择器统计
            logger.info("测试选择器统计...")
            stats = selector_manager.get_selector_stats("test_search_input")
            if stats:
                logger.info(f"选择器统计: {stats}")

            # 测试所有统计
            all_stats = selector_manager.get_all_stats()
            logger.info(f"所有选择器统计: {all_stats}")

            # 测试导出选择器
            logger.info("测试导出选择器...")
            export_success = selector_manager.export_selectors(
                "config/exported_selectors.json"
            )
            if export_success:
                logger.info("✅ 导出选择器成功")
            else:
                logger.error("❌ 导出选择器失败")

        except Exception as e:
            logger.error(f"测试过程中出错: {e}")
        finally:
            browser.close()


def test_integrated_taobao_operations():
    """测试集成的淘宝操作功能"""
    logger.info("开始测试集成的淘宝操作功能...")

    config = load_config()

    try:
        # 使用集成的自动选择器功能打开淘宝首页
        browser, page, screenshot_path = open_taobao_homepage(config)

        logger.info(f"✅ 成功打开淘宝首页，截图保存至: {screenshot_path}")

        # 获取选择器管理器并查看统计
        selector_manager = get_selector_manager(config)
        stats = selector_manager.get_all_stats()
        logger.info(f"选择器使用统计: {stats}")

        # 测试智能选择器功能
        logger.info("测试智能选择器功能...")

        # 测试获取搜索框选择器
        search_selector = selector_manager.get_selector(
            page=page,
            selector_name="search_input",
            target_description="搜索输入框",
            target_attributes={"type": "text"},
        )

        if search_selector:
            logger.info(f"✅ 智能获取搜索框选择器: {search_selector}")

            # 尝试在搜索框中输入内容
            page.fill(search_selector, "测试商品")
            logger.info("✅ 成功在搜索框中输入内容")
        else:
            logger.warning("❌ 无法获取搜索框选择器")

        # 测试获取Logo选择器
        logo_selector = selector_manager.get_selector(
            page=page,
            selector_name="taobao_logo",
            target_description="淘宝Logo",
            target_text="淘宝",
        )

        if logo_selector:
            logger.info(f"✅ 智能获取Logo选择器: {logo_selector}")
        else:
            logger.warning("❌ 无法获取Logo选择器")

        # 关闭浏览器
        browser.close()

    except Exception as e:
        logger.error(f"测试过程中出错: {e}")


def main():
    """主函数"""
    logger.info("开始自动选择器功能测试...")

    try:
        # 测试1: 自动选择器生成
        test_auto_selector_generation()

        # 测试2: 选择器管理器
        test_selector_manager()

        # 测试3: 集成的淘宝操作
        test_integrated_taobao_operations()

        logger.info("所有测试完成！")

    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")


if __name__ == "__main__":
    main()
