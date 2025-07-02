#!/usr/bin/env python3
"""
多平台订单自动合并程序
用于从多个电商平台获取订单数据，合并并导出为统一格式的Excel文件
"""

import os
import sys
import time
from typing import Dict, Any

from reusable_modules.utils import setup_logger, load_config, load_credentials
from reusable_modules.order_processor import OrderProcessor

# 初始化日志记录器
logger = setup_logger()


class FinanceAutomationApp:
    """封装财务自动化应用的核心逻辑"""

    def __init__(self, config_path: str = "config/config.yml"):
        """
        初始化应用
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_and_prepare_config(config_path)
        self.processor = OrderProcessor(self.config)

        # 定义菜单选项
        self.menu_options = {
            "1": {
                "desc": "获取所有平台订单并合并导出",
                "platforms": self.config.get("platforms", {}).get("enabled", []),
                "share_context": True,
            },
            "2": {
                "desc": "仅获取淘宝订单并导出",
                "platforms": ["taobao"],
                "share_context": False,
            },
            "3": {
                "desc": "仅获取京东订单并导出",
                "platforms": ["jd"],
                "share_context": False,
            },
            "4": {"desc": "退出程序", "action": "exit"},
        }

    def _load_and_prepare_config(self, config_path: str) -> Dict[str, Any]:
        """加载、准备和验证配置"""
        logger.info("=" * 50)
        logger.info("流程启动: 多平台订单自动合并")
        logger.info("=" * 50)

        # 加载配置文件
        logger.info(f"加载配置文件: {config_path}...")
        config = load_config(config_path)
        logger.info("配置文件加载成功。")

        # 如果浏览器设置中有debug标志，根据debug模式设置浏览器参数
        if "browser_settings" in config:
            debug_mode = config.get("browser_settings", {}).get("debug", False)
            if debug_mode:
                logger.info("启用调试模式，设置非无头浏览器和缓慢执行")
                config["browser_settings"]["headless"] = False
                config["browser_settings"]["slow_mo"] = 500

        # 创建输出目录
        output_folder = config.get("paths", {}).get("output_folder", "data/output")
        os.makedirs(output_folder, exist_ok=True)

        # 加载并更新凭据
        config = load_credentials(config)

        return config

    def _display_menu(self):
        """显示操作菜单"""
        print("\n" + "=" * 80)
        print("【多平台订单自动合并】- 请选择要执行的操作：")

        # 根据菜单选项字典动态生成菜单
        for key, option in self.menu_options.items():
            print(f"{key}. {option['desc']}")

        print("=" * 80)
        return input("\n请输入选项(1-4): ").strip()

    def _input_days(self) -> int:
        """获取用户输入的天数"""
        # 从配置中获取默认天数
        default_days = self.config.get("default_days_to_fetch", 7)

        while True:
            try:
                days_input = input(
                    f"\n请输入要获取的订单天数 (默认{default_days}天，直接回车使用默认值): "
                ).strip()
                if not days_input:
                    return default_days
                days = int(days_input)
                if days <= 0:
                    print("天数必须大于0，请重新输入")
                    continue
                return days
            except ValueError:
                print("请输入有效的数字")

    def _show_important_notes(self):
        """显示重要提示"""
        print("\n" + "=" * 80)
        print("重要提示：")
        print("1. 如果出现滑动验证码，请在浏览器窗口中手动完成验证")
        print("2. 如果出现其他安全验证（如短信验证码），也需要手动完成")
        print("3. 完成验证后，程序将自动继续执行")
        print("4. 整个过程中请不要关闭浏览器窗口")
        print("=" * 80 + "\n")

    def run(self):
        """运行应用主循环"""
        self._show_important_notes()

        choice = self._display_menu()
        logger.info(f"用户选择了选项: {choice}")

        try:
            # 获取选择的菜单选项
            option = self.menu_options.get(choice)

            if not option:
                logger.warning(f"无效的选项: {choice}")
                print("\n无效的选项，将退出程序")
                return

            # 处理退出选项
            if "action" in option and option["action"] == "exit":
                logger.info("用户选择退出程序")
                print("\n正在退出程序...")
                return

            # 获取订单天数
            days = self._input_days()

            # 处理订单
            excel_path = self.processor.process(
                days=days,
                platform_names=option["platforms"],
                share_browser_context=option.get("share_context", True),
            )

            if excel_path:
                print(f"\n订单数据已成功合并并导出到: {excel_path}")
            else:
                print("\n订单导出失败，请检查日志")

            # 完成处理后的收尾工作
            print("\n处理已完成，程序将在10秒后自动退出...")
            time.sleep(10)

        except Exception as e:
            logger.critical(f"流程遭遇未处理的致命错误, 即将终止: {e}", exc_info=True)
            print(f"\n程序出错: {e}")
            sys.exit(1)


def main():
    """程序主入口"""
    try:
        app = FinanceAutomationApp()
        app.run()
    except Exception as e:
        logger.critical(f"程序启动失败: {e}", exc_info=True)
        print(f"\n程序启动时发生严重错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
