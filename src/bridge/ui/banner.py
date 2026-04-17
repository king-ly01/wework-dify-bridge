"""ASCII 艺术横幅"""

import time
from .styles import purple, dark_purple, white


def print_lines(lines: list, delay: float = 0.03) -> None:
    """逐行打印，带延迟效果"""
    for line in lines:
        print(line)
        time.sleep(delay)


def print_banner() -> None:
    """打印 BRIDGE 大横幅 - 超宽震撼版，逐行展开"""
    width = 76
    art_width = 46
    padding = (width - art_width) // 2
    left_pad = " " * padding
    lines = [
        purple("  ╔" + "═" * width + "╗"),
        purple("  ║") + white(left_pad + "  ██████╗ ██████╗ ██╗██████╗  ██████╗ ███████╗") + purple(" " * (width - padding - art_width) + "║"),
        purple("  ║") + white(left_pad + "  ██╔══██╗██╔══██╗██║██╔══██╗██╔════╝ ██╔════╝") + purple(" " * (width - padding - art_width) + "║"),
        purple("  ║") + white(left_pad + "  ██████╔╝██████╔╝██║██║  ██║██║  ███╗█████╗  ") + purple(" " * (width - padding - art_width) + "║"),
        purple("  ║") + white(left_pad + "  ██╔══██╗██╔══██╗██║██║  ██║██║   ██║██╔══╝  ") + purple(" " * (width - padding - art_width) + "║"),
        purple("  ║") + white(left_pad + "  ██████╔╝██║  ██║██║██████╔╝╚██████╔╝███████╗") + purple(" " * (width - padding - art_width) + "║"),
        purple("  ║") + white(left_pad + "  ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝") + purple(" " * (width - padding - art_width) + "║"),
        purple("  ╚" + "═" * width + "╝"),
    ]
    print_lines(lines, delay=0.06)


def print_bridge_art() -> None:
    """打印石拱桥 ASCII 艺术 - 逐行动画"""
    lines = [
        dark_purple("                     ██      ██     ██     ██      ██          "),
        dark_purple("                     ████████████████████████████████                 "),
        dark_purple("                    ██████████████████████████████████                 "),
        dark_purple("                  ██ ██ ██ ██ ██ ██ ██ ██ ██ ██ ██ ██ ██                "),
        dark_purple("                ██ ██ ██ ██ ██              ██ ██ ██ ██ ██              "),
        dark_purple("              ██ ██ ██ ██ ██                  ██ ██ ██ ██ ██            "),
        dark_purple("            ██ ██ ██ ██ ██                      ██ ██ ██ ██ ██          "),
        dark_purple("          ██ ██ ██ ██ ██                          ██ ██ ██ ██ ██        "),
        dark_purple("         ████████████████████████████████████████████████████████       "),
        white("         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓     "),
    ]
    print_lines(lines, delay=0.08)


def print_title(text: str) -> None:
    """打印带装饰的标题 - 逐行动画"""
    width = 56
    padding = (width - len(text) * 2) // 2
    lines = [
        "",
        purple("  ╔" + "═" * width + "╗"),
        purple("  ║") + white(" " * padding + text + " " * (width - padding - len(text) * 2)) + purple("║"),
        purple("  ╚" + "═" * width + "╝"),
    ]
    print_lines(lines, delay=0.05)


def print_section(title: str) -> None:
    """打印分节标题"""
    print()
    print(purple(f"  ▓▓▓ {white(title)} {purple('▓▓▓'.rjust(50 - len(title)))}"))
    print(purple("  " + "─" * 56))
