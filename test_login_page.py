"""
登录页面测试脚本
测试从淘宝首页跳转到登录页面的功能
"""

import logging
import yaml
from reusable_modules.taobao_operations import (
    open_taobao_login_page,
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


def test_login_page_navigation():
    """测试登录页面跳转功能"""
    logger.info("开始测试登录页面跳转功能...")

    config = load_config()

    try:
        # 使用新的登录页面功能
        browser, page, screenshot_path = open_taobao_login_page(config)

        logger.info(f"✅ 成功跳转到登录页面，截图保存至: {screenshot_path}")

        # 获取选择器管理器并查看统计
        selector_manager = get_selector_manager(config)
        stats = selector_manager.get_all_stats()
        logger.info(f"选择器使用统计: {stats}")

        # 测试登录页面上的选择器
        logger.info("测试登录页面选择器...")

        # 测试用户名输入框选择器
        try:
            username_selector = selector_manager.get_selector(
                page=page,
                selector_name="username_input",
                target_description="用户名输入框",
                target_attributes={"type": "text"},
            )
            if username_selector:
                logger.info(f"✅ 找到用户名输入框: {username_selector}")
            else:
                logger.warning("❌ 未找到用户名输入框")
        except Exception as e:
            logger.warning(f"获取用户名输入框选择器失败: {e}")

        # 测试密码输入框选择器
        try:
            password_selector = selector_manager.get_selector(
                page=page,
                selector_name="password_input",
                target_description="密码输入框",
                target_attributes={"type": "password"},
            )
            if password_selector:
                logger.info(f"✅ 找到密码输入框: {password_selector}")
            else:
                logger.warning("❌ 未找到密码输入框")
        except Exception as e:
            logger.warning(f"获取密码输入框选择器失败: {e}")

        # 测试登录按钮选择器
        try:
            submit_selector = selector_manager.get_selector(
                page=page,
                selector_name="login_submit_button",
                target_description="登录提交按钮",
                target_text="登录",
            )
            if submit_selector:
                logger.info(f"✅ 找到登录提交按钮: {submit_selector}")
            else:
                logger.warning("❌ 未找到登录提交按钮")
        except Exception as e:
            logger.warning(f"获取登录提交按钮选择器失败: {e}")

        # 显示当前页面信息
        current_url = page.url
        page_title = page.title()
        logger.info(f"当前页面URL: {current_url}")
        logger.info(f"当前页面标题: {page_title}")

        # 关闭浏览器
        browser.close()
        logger.info("✅ 测试完成，浏览器已关闭")

    except Exception as e:
        logger.error(f"测试过程中出错: {e}")


def main():
    """主函数"""
    logger.info("开始登录页面功能测试...")

    try:
        test_login_page_navigation()
        logger.info("所有测试完成！")

    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")


if __name__ == "__main__":
    main()
