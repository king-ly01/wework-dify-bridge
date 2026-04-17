"""网络连接测试模块"""

from .wecom import test_wecom_connection, wait_for_chatid, send_welcome_message
from .dify import test_dify_connection

__all__ = [
    'test_wecom_connection',
    'wait_for_chatid',
    'send_welcome_message',
    'test_dify_connection'
]
