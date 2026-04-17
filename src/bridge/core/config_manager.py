"""配置管理模块"""

import json
import os


# 项目配置目录 - 使用项目目录下的 config 文件夹
PROJECT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
PROJECT_DIR = os.path.abspath(PROJECT_DIR)
CONFIG_FILE = os.path.join(PROJECT_DIR, "config.json")
PID_FILE = os.path.join(PROJECT_DIR, "bridge.pid")
LOG_FILE = os.path.join(PROJECT_DIR, "bridge.log")


def ensure_project_dir() -> None:
    """确保配置目录存在"""
    if not os.path.exists(PROJECT_DIR):
        os.makedirs(PROJECT_DIR)
    # 初始化默认配置
    if not os.path.exists(CONFIG_FILE):
        default_cfg = {
            "service": {"notify_port": 8899, "log_level": "INFO"},
            "bots": []
        }
        save_config(default_cfg)


def load_config() -> dict:
    """加载配置文件"""
    ensure_project_dir()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"service": {"notify_port": 8899, "log_level": "INFO"}, "bots": []}


def save_config(cfg: dict) -> None:
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
