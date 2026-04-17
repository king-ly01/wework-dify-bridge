"""文件系统工具"""

import os


def ensure_dir(path: str) -> None:
    """
    确保目录存在，不存在则创建
    
    Args:
        path: 目录路径
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
