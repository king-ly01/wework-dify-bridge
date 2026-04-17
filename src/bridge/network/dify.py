"""Dify 连接模块"""

import ssl
import urllib.request
import urllib.error


def test_dify_connection(api_base: str, api_key: str) -> tuple[bool, str]:
    """
    测试 Dify 连接
    
    Args:
        api_base: API 基础 URL
        api_key: API Key
    
    Returns:
        (是否成功, 消息)
    """
    try:
        # 构建测试 URL（获取应用信息）
        url = f"{api_base}/info"
        if not url.startswith("http"):
            url = f"http://{url}"
        
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        # 禁用 SSL 验证（针对本地测试）
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                if resp.status == 200:
                    return True, "连接成功"
                else:
                    return False, f"HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, "API Key 无效"
            elif e.code == 404:
                return False, "Dify 服务未找到，请检查地址"
            else:
                return False, f"HTTP {e.code}"
        except urllib.error.URLError as e:
            return False, f"无法连接到 Dify: {e.reason}"
            
    except Exception as e:
        return False, f"测试失败: {e}"
