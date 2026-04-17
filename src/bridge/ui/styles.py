"""UI 样式定义"""


class Style:
    """紫色主题配色"""
    PURPLE = "\033[95m"      # 亮紫
    DARK_PURPLE = "\033[35m" # 深紫
    WHITE = "\033[97m"     # 白色
    BLACK = "\033[30m"     # 黑色
    BOLD = "\033[1m"
    RESET = "\033[0m"


def purple(s: str) -> str:
    return f"{Style.PURPLE}{s}{Style.RESET}"


def dark_purple(s: str) -> str:
    return f"{Style.DARK_PURPLE}{s}{Style.RESET}"


def white(s: str) -> str:
    return f"{Style.WHITE}{s}{Style.RESET}"


def black_on_white(s: str) -> str:
    return f"\033[30;47m{s}{Style.RESET}"


# 简洁颜色别名
class C:
    """简洁颜色别名"""
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def red(s: str) -> str:
    return f"{C.RED}{s}{C.RESET}"


def green(s: str) -> str:
    return f"{C.GREEN}{s}{C.RESET}"


def yellow(s: str) -> str:
    return f"{C.YELLOW}{s}{C.RESET}"


def blue(s: str) -> str:
    return f"{C.BLUE}{s}{C.RESET}"


def cyan(s: str) -> str:
    return f"{C.CYAN}{s}{C.RESET}"


def gray(s: str) -> str:
    return f"{C.GRAY}{s}{C.RESET}"


def bold(s: str) -> str:
    return f"{C.BOLD}{s}{C.RESET}"
