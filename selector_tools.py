"""
选择器管理工具
提供命令行界面来管理选择器
"""

import argparse
import logging
import yaml
from typing import Dict, Any, Optional
from reusable_modules.selector_manager import SelectorManager

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open("config/config.yml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}


def list_selectors():
    """列出所有选择器"""
    config = load_config()
    selector_manager = SelectorManager(config)

    stats = selector_manager.get_all_stats()

    print("\n=== 选择器统计信息 ===")
    print(f"总选择器数量: {stats['total_selectors']}")
    print(f"活跃选择器数量: {stats['active_selectors']}")
    print(f"总使用次数: {stats['total_uses']}")
    print(f"总成功次数: {stats['total_success']}")
    print(f"总失败次数: {stats['total_failures']}")

    if stats["total_uses"] > 0:
        success_rate = stats["total_success"] / stats["total_uses"] * 100
        print(f"成功率: {success_rate:.2f}%")

    print("\n=== 详细选择器信息 ===")
    for name, selector_stats in stats["selectors"].items():
        if selector_stats:
            print(f"\n选择器: {name}")
            print(f"  选择器: {selector_stats['selector']}")
            print(f"  置信度: {selector_stats['confidence']}")
            print(f"  版本: {selector_stats['version']}")
            print(f"  成功次数: {selector_stats['success_count']}")
            print(f"  失败次数: {selector_stats['failure_count']}")
            if selector_stats["success_count"] + selector_stats["failure_count"] > 0:
                rate = selector_stats["success_rate"] * 100
                print(f"  成功率: {rate:.2f}%")
            print(f"  最后使用: {selector_stats['last_used']}")
            print(f"  状态: {'活跃' if selector_stats['is_active'] else '非活跃'}")


def add_selector(
    name: str, selector: str, description: str = "", confidence: float = 1.0
):
    """添加选择器"""
    config = load_config()
    selector_manager = SelectorManager(config)

    success = selector_manager.add_selector(
        name=name, selector=selector, description=description, confidence=confidence
    )

    if success:
        print(f"✅ 成功添加选择器: {name} -> {selector}")
    else:
        print(f"❌ 添加选择器失败: {name}")


def remove_selector(name: str):
    """移除选择器"""
    config = load_config()
    selector_manager = SelectorManager(config)

    success = selector_manager.remove_selector(name)

    if success:
        print(f"✅ 成功移除选择器: {name}")
    else:
        print(f"❌ 移除选择器失败: {name}")


def update_selector(name: str, new_selector: str, confidence: Optional[float] = None):
    """更新选择器"""
    config = load_config()
    selector_manager = SelectorManager(config)

    success = selector_manager.update_selector(
        name=name, new_selector=new_selector, confidence=confidence
    )

    if success:
        print(f"✅ 成功更新选择器: {name} -> {new_selector}")
    else:
        print(f"❌ 更新选择器失败: {name}")


def show_selector(name: str):
    """显示选择器详细信息"""
    config = load_config()
    selector_manager = SelectorManager(config)

    stats = selector_manager.get_selector_stats(name)

    if stats:
        print(f"\n=== 选择器详细信息: {name} ===")
        print(f"选择器: {stats['selector']}")
        print(f"置信度: {stats['confidence']}")
        print(f"版本: {stats['version']}")
        print(f"成功次数: {stats['success_count']}")
        print(f"失败次数: {stats['failure_count']}")
        if stats["success_count"] + stats["failure_count"] > 0:
            rate = stats["success_rate"] * 100
            print(f"成功率: {rate:.2f}%")
        print(f"最后使用: {stats['last_used']}")
        print(f"状态: {'活跃' if stats['is_active'] else '非活跃'}")
    else:
        print(f"❌ 选择器不存在: {name}")


def export_selectors(file_path: str):
    """导出选择器"""
    config = load_config()
    selector_manager = SelectorManager(config)

    success = selector_manager.export_selectors(file_path)

    if success:
        print(f"✅ 成功导出选择器到: {file_path}")
    else:
        print("❌ 导出选择器失败")


def import_selectors(file_path: str, overwrite: bool = False):
    """导入选择器"""
    config = load_config()
    selector_manager = SelectorManager(config)

    success = selector_manager.import_selectors(file_path, overwrite)

    if success:
        print(f"✅ 成功导入选择器从: {file_path}")
    else:
        print("❌ 导入选择器失败")


def clear_cache():
    """清除选择器缓存"""
    config = load_config()
    selector_manager = SelectorManager(config)

    selector_manager.clear_cache()
    print("✅ 选择器缓存已清除")


def show_cache_stats():
    """显示缓存统计"""
    config = load_config()
    selector_manager = SelectorManager(config)

    cache_stats = selector_manager.auto_generator.get_cache_stats()

    print("\n=== 缓存统计信息 ===")
    print(f"缓存大小: {cache_stats['cache_size']}")
    print(f"缓存启用: {cache_stats['cache_enabled']}")
    print(f"缓存持续时间: {cache_stats['cache_duration']} 秒")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="选择器管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 列出选择器
    subparsers.add_parser("list", help="列出所有选择器")

    # 添加选择器
    add_parser = subparsers.add_parser("add", help="添加选择器")
    add_parser.add_argument("name", help="选择器名称")
    add_parser.add_argument("selector", help="选择器字符串")
    add_parser.add_argument("--description", "-d", default="", help="选择器描述")
    add_parser.add_argument(
        "--confidence", "-c", type=float, default=1.0, help="置信度"
    )

    # 移除选择器
    remove_parser = subparsers.add_parser("remove", help="移除选择器")
    remove_parser.add_argument("name", help="选择器名称")

    # 更新选择器
    update_parser = subparsers.add_parser("update", help="更新选择器")
    update_parser.add_argument("name", help="选择器名称")
    update_parser.add_argument("selector", help="新选择器字符串")
    update_parser.add_argument("--confidence", "-c", type=float, help="新置信度")

    # 显示选择器
    show_parser = subparsers.add_parser("show", help="显示选择器详细信息")
    show_parser.add_argument("name", help="选择器名称")

    # 导出选择器
    export_parser = subparsers.add_parser("export", help="导出选择器")
    export_parser.add_argument("file_path", help="导出文件路径")

    # 导入选择器
    import_parser = subparsers.add_parser("import", help="导入选择器")
    import_parser.add_argument("file_path", help="导入文件路径")
    import_parser.add_argument(
        "--overwrite", "-o", action="store_true", help="覆盖现有选择器"
    )

    # 清除缓存
    cache_parser = subparsers.add_parser("cache", help="缓存管理")
    cache_subparsers = cache_parser.add_subparsers(
        dest="cache_command", help="缓存命令"
    )

    cache_subparsers.add_parser("clear", help="清除缓存")
    cache_subparsers.add_parser("stats", help="显示缓存统计")

    args = parser.parse_args()

    if args.command == "list":
        list_selectors()
    elif args.command == "add":
        add_selector(args.name, args.selector, args.description, args.confidence)
    elif args.command == "remove":
        remove_selector(args.name)
    elif args.command == "update":
        update_selector(args.name, args.selector, args.confidence)
    elif args.command == "show":
        show_selector(args.name)
    elif args.command == "export":
        export_selectors(args.file_path)
    elif args.command == "import":
        import_selectors(args.file_path, args.overwrite)
    elif args.command == "cache":
        if args.cache_command == "clear":
            clear_cache()
        elif args.cache_command == "stats":
            show_cache_stats()
        else:
            cache_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
