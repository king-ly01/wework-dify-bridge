"""IP 地址工具"""

import socket


def get_host_ip() -> str:
    """
    获取本机 IP 地址
    
    Returns:
        本机 IP 地址，获取失败返回 127.0.0.1
    """
    try:
        # 尝试连接外部地址来获取本机 IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # 回退到本地解析
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"
