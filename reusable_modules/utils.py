import sys
import os
import logging
import getpass
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, Any
import yaml

# 尝试导入dotenv，如果不存在则跳过
try:
    from dotenv import load_dotenv

    has_dotenv = True
except ImportError:
    has_dotenv = False
    print("警告: python-dotenv 模块未安装，环境变量功能将不可用")


def get_resource_path(relative_path: str) -> str:
    """获取资源的绝对路径, 兼容开发环境和PyInstaller打包环境。"""
    if getattr(sys, "frozen", False):
        # 如果是打包状态 (被PyInstaller打包)
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    else:
        # 如果是开发状态
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def setup_logger(log_folder: str = "logs", log_level=logging.INFO) -> logging.Logger:
    """配置日志记录器, 同时输出到控制台和文件, 并按天分割。"""
    log_dir = get_resource_path(log_folder)
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("RPA_Logger")
    logger.setLevel(log_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    log_file_path = os.path.join(log_dir, "rpa_process.log")
    file_handler = TimedRotatingFileHandler(
        log_file_path, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger


def load_config(config_file: str = "config/config.yml") -> Dict[str, Any]:
    """加载 .env 和 config.yml 文件, 并将环境变量注入到配置字典中。"""
    # 如果dotenv可用，则加载环境变量
    if has_dotenv:
        load_dotenv()

    config_path = get_resource_path(config_file)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件未找到: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    def substitute_env_vars(cfg):
        if isinstance(cfg, dict):
            for k, v in cfg.items():
                cfg[k] = substitute_env_vars(v)
        elif isinstance(cfg, list):
            for i, item in enumerate(cfg):
                cfg[i] = substitute_env_vars(item)
        elif isinstance(cfg, str) and cfg.startswith("${") and cfg.endswith("}"):
            env_var = cfg[2:-1]
            return os.getenv(env_var, "")
        return cfg

    return substitute_env_vars(config)


def load_credentials(
    config: Dict[str, Any], env_file: str = "config/.env"
) -> Dict[str, Any]:
    """
    从.env文件或用户输入加载各平台的登录凭据，并更新配置

    Args:
        config: 配置字典
        env_file: .env文件路径

    Returns:
        更新了凭据的配置字典
    """
    logger = logging.getLogger("RPA_Logger")

    # 加载.env文件中的环境变量
    if has_dotenv:
        load_dotenv(env_file)
        logger.info(f"已尝试加载环境变量文件: {env_file}")

    # 确保配置中存在credentials部分
    if "credentials" not in config:
        config["credentials"] = {}

    # 获取已启用的平台列表
    platforms = config.get("platforms", {}).get("enabled", [])

    for platform in platforms:
        username_key = f"{platform.upper()}_USERNAME"
        password_key = f"{platform.upper()}_PASSWORD"

        username = os.environ.get(username_key, "")
        password = os.environ.get(password_key, "")

        if not username or not password:
            logger.info(f"未在环境变量中找到{platform}的账号密码，需要手动输入")
            print("=" * 50)
            print(f"请输入 {platform.capitalize()} 账号和密码")
            print("=" * 50)
            if not username:
                username = input(f"{platform.capitalize()} 账号: ")
            if not password:
                password = getpass.getpass(f"{platform.capitalize()} 密码: ")

        # 更新配置中的凭据
        config["credentials"][f"{platform}_username"] = username
        config["credentials"][f"{platform}_password"] = password

        # 为了兼容旧的'username'/'password'键
        if platform == "taobao":
            config["credentials"]["username"] = username
            config["credentials"]["password"] = password

    logger.info(f"已加载 {len(platforms)} 个平台的登录凭据")
    return config
