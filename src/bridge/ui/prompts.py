"""交互式输入组件"""

import time
import readline


class CancelledError(Exception):
    """用户取消输入"""
    pass


def type_print(text: str, delay: float = 0.01) -> None:
    """打字机效果输出"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)


def prompt(message: str, default: str = "", required: bool = True) -> str:
    """
    提示用户输入，支持默认值和必填验证
    
    Args:
        message: 提示信息
        default: 默认值
        required: 是否必填
    
    Returns:
        用户输入的值
    
    Raises:
        CancelledError: 用户按 Ctrl+C 取消
    """
    try:
        if default:
            hint = f" [{default}]"
        else:
            hint = ""
        
        while True:
            try:
                value = input(f"  {message}{hint}: ").strip()
            except KeyboardInterrupt:
                print()
                raise CancelledError()
            
            if not value and default:
                return default
            
            if required and not value:
                print("  ⚠️  此项为必填项")
                continue
            
            return value
    except EOFError:
        return default
