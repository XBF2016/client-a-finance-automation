#!/usr/bin/env python3
"""
多平台订单自动合并程序 - PoC 版本
用于从多个电商平台获取订单数据，合并并导出为统一格式的Excel文件
"""

import os
import sys
import time
import yaml
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv
from playwright.sync_api import (
    sync_playwright,
    Page,
    Browser,
    BrowserContext,
    TimeoutError,
)

# =============== 配置加载 ===============


def load_config(config_path: str = "config.yml") -> dict:
    """加载配置文件"""
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        sys.exit(1)


def load_credentials() -> dict:
    """加载环境变量中的凭据"""
    # 加载环境变量
    load_dotenv("credentials.env")

    credentials = {
        "taobao": {
            "username": os.getenv("TAOBAO_USERNAME", ""),
            "password": os.getenv("TAOBAO_PASSWORD", ""),
        },
        "jd": {
            "username": os.getenv("JD_USERNAME", ""),
            "password": os.getenv("JD_PASSWORD", ""),
        },
    }

    # 简单验证
    if not credentials["taobao"]["username"] or not credentials["taobao"]["password"]:
        print("警告: 淘宝账号或密码未设置")

    if not credentials["jd"]["username"] or not credentials["jd"]["password"]:
        print("警告: 京东账号或密码未设置")

    return credentials


# =============== 浏览器操作 ===============


def setup_browser(config: dict) -> Tuple[Browser, BrowserContext]:
    """设置浏览器实例"""
    browser_settings = config.get("browser_settings", {})
    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=browser_settings.get("headless", False),
        slow_mo=browser_settings.get("slow_mo", 300),
    )

    context = browser.new_context(viewport={"width": 1280, "height": 800})

    return browser, context


# =============== 平台通用操作 ===============


def wait_for_navigation_or_timeout(page: Page, timeout: int = 60000) -> bool:
    """等待页面导航完成或超时"""
    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
        return True
    except TimeoutError:
        print("等待页面加载超时")
        return False


def take_screenshot(page: Page, filename: str, config: dict) -> str:
    """截取当前页面"""
    try:
        # 确保输出目录存在
        output_dir = config.get("output", {}).get("folder", "output")
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(output_dir, f"{filename}_{timestamp}.png")

        # 保存截图
        page.screenshot(path=filepath)
        print(f"截图已保存: {filepath}")
        return filepath
    except Exception as e:
        print(f"截图失败: {e}")
        return ""


# =============== 淘宝平台操作 ===============


def taobao_login(page: Page, config: dict, credentials: dict) -> bool:
    """登录淘宝平台"""
    try:
        # 访问登录页
        login_url = config["urls"]["taobao_login"]
        page.goto(login_url)
        print("正在访问淘宝登录页面...")

        # 切换到密码登录（如果需要）
        try:
            password_login = page.locator('text="密码登录"').first
            if password_login.is_visible():
                password_login.click()
                time.sleep(1)
        except:
            print("已经是密码登录页面或无需切换")

        # 填写账号密码
        username_selector = config["selectors"]["taobao_login_username"]
        password_selector = config["selectors"]["taobao_login_password"]
        submit_selector = config["selectors"]["taobao_login_submit"]

        page.fill(username_selector, credentials["taobao"]["username"])
        page.fill(password_selector, credentials["taobao"]["password"])

        # 点击登录
        page.click(submit_selector)
        print("已点击登录按钮，请在浏览器中完成可能的验证...")

        # 等待登录完成（可能需要手动验证）
        # 给用户足够的时间完成验证
        page.wait_for_url(lambda url: "login.taobao.com" not in url, timeout=120000)

        # 检查是否登录成功
        return taobao_is_logged_in(page, config)

    except Exception as e:
        print(f"淘宝登录过程出错: {e}")
        return False


def taobao_is_logged_in(page: Page, config: dict) -> bool:
    """检查是否已登录淘宝"""
    try:
        # 访问订单页面
        orders_url = config["orders_urls"]["taobao"]
        page.goto(orders_url, timeout=30000)

        # 如果URL包含login，说明被重定向到登录页
        if "login.taobao.com" in page.url:
            print("淘宝未登录，被重定向到登录页")
            return False

        # 检查登录成功标识
        success_selector = config["selectors"]["taobao_login_success"]
        return page.locator(success_selector).is_visible(timeout=5000)
    except Exception as e:
        print(f"检查淘宝登录状态时出错: {e}")
        return False


def taobao_get_orders(page: Page, config: dict, days: int = 7) -> List[Dict[str, Any]]:
    """获取淘宝订单数据"""
    try:
        # 确保在订单页面
        orders_url = config["orders_urls"]["taobao"]
        page.goto(orders_url)
        print(f"正在获取最近{days}天的淘宝订单...")

        # 等待订单容器加载
        container_selector = config["selectors"]["taobao_orders_container"]
        page.wait_for_selector(container_selector, timeout=30000)

        # 获取所有订单元素
        order_elements = page.locator(container_selector).all()

        if not order_elements:
            print("未找到淘宝订单")
            return []

        orders = []
        for elem in order_elements:
            try:
                # 获取订单基本信息
                order_id = (
                    elem.locator(config["selectors"]["taobao_order_id"])
                    .inner_text()
                    .strip()
                )
                order_time_text = (
                    elem.locator(config["selectors"]["taobao_order_time"])
                    .inner_text()
                    .strip()
                )

                # 解析日期，这里简化处理
                try:
                    order_time = datetime.strptime(order_time_text, "%Y-%m-%d %H:%M:%S")
                except:
                    order_time = datetime.now()  # 解析失败时使用当前时间

                # 获取商品和收件人信息
                buyer_name = ""
                try:
                    buyer_name = (
                        elem.locator(config["selectors"]["taobao_buyer_name"])
                        .inner_text()
                        .strip()
                    )
                except:
                    pass

                # 从商品列表构建数据
                items = []
                try:
                    item_elems = elem.locator(".item-mod__item-title").all()
                    for item in item_elems:
                        items.append(item.inner_text().strip())
                except:
                    items = ["未能获取商品信息"]

                # 构建订单数据
                order_data = {
                    "order_id": order_id,
                    "platform": "淘宝",
                    "buyer_name": buyer_name,
                    "order_time": order_time,
                    "items": ", ".join(items),
                    "quantity": len(items),
                }

                orders.append(order_data)

            except Exception as e:
                print(f"处理单个淘宝订单时出错: {e}")
                continue

        print(f"成功获取 {len(orders)} 条淘宝订单")
        return orders

    except Exception as e:
        print(f"获取淘宝订单数据时出错: {e}")
        return []


# =============== 京东平台操作 ===============


def jd_login(page: Page, config: dict, credentials: dict) -> bool:
    """登录京东平台"""
    try:
        # 访问登录页
        login_url = config["urls"]["jd_login"]
        page.goto(login_url)
        print("正在访问京东登录页面...")

        # 切换到账号密码登录（如果需要）
        try:
            page.locator('text="账户登录"').click()
            time.sleep(1)
        except:
            print("已经是账户登录页面或无需切换")

        # 填写账号密码
        username_selector = config["selectors"]["jd_login_username"]
        password_selector = config["selectors"]["jd_login_password"]
        submit_selector = config["selectors"]["jd_login_submit"]

        page.fill(username_selector, credentials["jd"]["username"])
        page.fill(password_selector, credentials["jd"]["password"])

        # 点击登录
        page.click(submit_selector)
        print("已点击登录按钮，请在浏览器中完成可能的验证...")

        # 等待登录完成（可能需要手动验证）
        page.wait_for_url(lambda url: "passport.jd.com" not in url, timeout=120000)

        # 检查是否登录成功
        return jd_is_logged_in(page, config)

    except Exception as e:
        print(f"京东登录过程出错: {e}")
        return False


def jd_is_logged_in(page: Page, config: dict) -> bool:
    """检查是否已登录京东"""
    try:
        # 访问订单页面
        orders_url = config["orders_urls"]["jd"]
        page.goto(orders_url, timeout=30000)

        # 如果URL包含passport，说明被重定向到登录页
        if "passport.jd.com" in page.url:
            print("京东未登录，被重定向到登录页")
            return False

        # 检查登录成功标识
        success_selector = config["selectors"]["jd_login_success"]
        return page.locator(success_selector).is_visible(timeout=5000)
    except Exception as e:
        print(f"检查京东登录状态时出错: {e}")
        return False


def jd_get_orders(page: Page, config: dict, days: int = 7) -> List[Dict[str, Any]]:
    """获取京东订单数据"""
    try:
        # 确保在订单页面
        orders_url = config["orders_urls"]["jd"]
        page.goto(orders_url)
        print(f"正在获取最近{days}天的京东订单...")

        # 等待订单容器加载
        container_selector = config["selectors"]["jd_orders_container"]
        page.wait_for_selector(container_selector, timeout=30000)

        # 获取所有订单元素
        order_elements = page.locator(container_selector).all()

        if not order_elements:
            print("未找到京东订单")
            return []

        orders = []
        for elem in order_elements:
            try:
                # 获取订单基本信息
                order_id = (
                    elem.locator(config["selectors"]["jd_order_id"])
                    .inner_text()
                    .strip()
                )
                order_time_text = (
                    elem.locator(config["selectors"]["jd_order_time"])
                    .inner_text()
                    .strip()
                )

                # 解析日期，这里简化处理
                try:
                    order_time = datetime.strptime(order_time_text, "%Y-%m-%d %H:%M:%S")
                except:
                    order_time = datetime.now()  # 解析失败时使用当前时间

                # 获取收件人信息
                buyer_name = ""
                try:
                    buyer_name = (
                        elem.locator(config["selectors"]["jd_buyer_name"])
                        .inner_text()
                        .strip()
                    )
                except:
                    pass

                # 从商品列表构建数据
                items = []
                try:
                    item_elems = elem.locator(".p-name").all()
                    for item in item_elems:
                        items.append(item.inner_text().strip())
                except:
                    items = ["未能获取商品信息"]

                # 构建订单数据
                order_data = {
                    "order_id": order_id,
                    "platform": "京东",
                    "buyer_name": buyer_name,
                    "order_time": order_time,
                    "items": ", ".join(items),
                    "quantity": len(items),
                }

                orders.append(order_data)

            except Exception as e:
                print(f"处理单个京东订单时出错: {e}")
                continue

        print(f"成功获取 {len(orders)} 条京东订单")
        return orders

    except Exception as e:
        print(f"获取京东订单数据时出错: {e}")
        return []


# =============== 数据处理与导出 ===============


def merge_orders(
    taobao_orders: List[Dict[str, Any]], jd_orders: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """合并多平台订单数据"""
    all_orders = []

    # 添加淘宝订单
    for order in taobao_orders:
        all_orders.append(order)

    # 添加京东订单
    for order in jd_orders:
        all_orders.append(order)

    # 按时间排序（从新到旧）
    all_orders.sort(key=lambda x: x.get("order_time", datetime.now()), reverse=True)

    return all_orders


def export_to_excel(orders: List[Dict[str, Any]], config: dict) -> str:
    """导出订单数据到Excel"""
    try:
        # 如果没有订单，创建一个空的DataFrame但包含所有列
        if not orders:
            df = pd.DataFrame(
                columns=[
                    "订单号",
                    "平台来源",
                    "收件人姓名",
                    "下单时间",
                    "商品信息",
                    "数量",
                ]
            )
        else:
            # 创建标准化的数据行
            rows = []
            for order in orders:
                row = {
                    "订单号": order.get("order_id", ""),
                    "平台来源": order.get("platform", ""),
                    "收件人姓名": order.get("buyer_name", ""),
                    "下单时间": order.get("order_time", ""),
                    "商品信息": order.get("items", ""),
                    "数量": order.get("quantity", 0),
                }
                rows.append(row)

            df = pd.DataFrame(rows)

        # 确保输出目录存在
        output_folder = config.get("output", {}).get("folder", "output")
        os.makedirs(output_folder, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = (
            config.get("output", {})
            .get("filename", "orders_{timestamp}.xlsx")
            .replace("{timestamp}", timestamp)
        )
        filepath = os.path.join(output_folder, filename)

        # 导出到Excel
        df.to_excel(filepath, index=False, engine="openpyxl")
        print(f"订单数据已导出到: {filepath}")

        return filepath
    except Exception as e:
        print(f"导出Excel时出错: {e}")
        return ""


# =============== 主程序 ===============


def main():
    """主程序入口"""
    try:
        print("\n" + "=" * 50)
        print("多平台订单自动合并工具 - PoC 版本")
        print("=" * 50 + "\n")

        # 切换到脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)

        # 加载配置和凭据
        config = load_config()
        credentials = load_credentials()

        # 确保输出目录存在
        output_folder = config.get("output", {}).get("folder", "output")
        os.makedirs(output_folder, exist_ok=True)

        # 询问要获取的天数
        default_days = config.get("default_days_to_fetch", 7)
        days_input = input(
            f"请输入要获取的订单天数 (默认{default_days}天，直接回车使用默认值): "
        ).strip()
        days = int(days_input) if days_input else default_days

        print("\n重要提示:")
        print("1. 如果出现验证码或安全验证，请在浏览器窗口中手动完成")
        print("2. 整个过程中请勿关闭浏览器窗口\n")

        # 启动浏览器
        browser, context = setup_browser(config)

        try:
            # ===== 处理淘宝平台 =====
            taobao_orders = []

            print("\n[淘宝] 开始处理淘宝平台...")
            taobao_page = context.new_page()

            # 登录淘宝
            if taobao_login(taobao_page, config, credentials):
                print("[淘宝] 登录成功!")
                # 获取订单
                taobao_orders = taobao_get_orders(taobao_page, config, days)
            else:
                print("[淘宝] 登录失败，无法获取订单")

            # ===== 处理京东平台 =====
            jd_orders = []

            print("\n[京东] 开始处理京东平台...")
            jd_page = context.new_page()

            # 登录京东
            if jd_login(jd_page, config, credentials):
                print("[京东] 登录成功!")
                # 获取订单
                jd_orders = jd_get_orders(jd_page, config, days)
            else:
                print("[京东] 登录失败，无法获取订单")

            # ===== 合并订单数据 =====
            print("\n开始合并订单数据...")
            all_orders = merge_orders(taobao_orders, jd_orders)

            # ===== 导出Excel =====
            excel_path = export_to_excel(all_orders, config)

            if excel_path:
                print(f"\n订单处理完成！共处理 {len(all_orders)} 条订单。")
                print(f"数据已导出到: {excel_path}")
            else:
                print("\n订单导出失败")

        finally:
            # 关闭浏览器
            browser.close()

        print("\n程序执行完毕。10秒后自动退出...")
        time.sleep(10)

    except Exception as e:
        print(f"\n程序运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
