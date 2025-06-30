import sys
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import yaml
from dotenv import load_dotenv

def get_resource_path(relative_path: str) -> str:
    """获取资源的绝对路径, 兼容开发环境和PyInstaller打包环境。"""
    if getattr(sys, 'frozen', False):
        # 如果是打包状态 (被PyInstaller打包)
        base_path = sys._MEIPASS
    else:
        # 如果是开发状态
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def setup_logger(log_folder: str = 'logs', log_level=logging.INFO) -> logging.Logger:
    """配置日志记录器, 同时输出到控制台和文件, 并按天分割。"""
    log_dir = get_resource_path(log_folder)
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("RPA_Logger")
    logger.setLevel(log_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    log_format = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    log_file_path = os.path.join(log_dir, 'rpa_process.log')
    file_handler = TimedRotatingFileHandler(
        log_file_path, when='midnight', interval=1, backupCount=30, encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger

def load_config(config_file: str = 'config/config.yml') -> dict:
    """加载 .env 和 config.yml 文件, 并将环境变量注入到配置字典中。"""
    load_dotenv()
    config_path = get_resource_path(config_file)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件未找到: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    def substitute_env_vars(cfg):
        if isinstance(cfg, dict):
            for k, v in cfg.items():
                cfg[k] = substitute_env_vars(v)
        elif isinstance(cfg, list):
            for i, item in enumerate(cfg):
                cfg[i] = substitute_env_vars(item)
        elif isinstance(cfg, str) and cfg.startswith('${') and cfg.endswith('}'):
            env_var = cfg[2:-1]
            return os.getenv(env_var, '')
        return cfg

    return substitute_env_vars(config)