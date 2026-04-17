#!/usr/bin/env python3
"""
TUI (Text User Interface) 模块
使用 curses 实现可靠的终端界面
"""

import sys
import os
import time
import readline  # 导入 readline 以正确处理中文输入

# 颜色定义
BLUE = "\033[38;5;39m"
BRIGHT_BLUE = "\033[38;5;51m"
CYAN = "\033[96m"
WHITE = "\033[97m"
GRAY = "\033[38;5;245m"
RESET = "\033[0m"
BOLD = "\033[1m"

# 控制字符
CLEAR_SCREEN = "\033[2J\033[H"

# 宽度设置 - 适应标准终端
WIDTH = 54


def clear():
    """清屏 - 清除屏幕和滚动缓冲区"""
    # 使用 ANSI 转义序列清除屏幕和滚动缓冲区
    print("\033[2J\033[H\033[3J", end="")
    sys.stdout.flush()
    # 同时调用系统 clear 命令作为备用
    os.system('clear 2>/dev/null || printf "\033[2J\033[H"')


def print_line(char="─"):
    """打印分隔线"""
    print(f"{BLUE}{char * WIDTH}{RESET}")


def print_banner(animated=True):
    """打印 Banner - WEDBRIDGE 智能桥接平台"""
    lines = [
        "",
        f"{BLUE}  ╔══════════════════════════════════════════════════╗{RESET}",
        f"{BLUE}  ║{RESET}{BRIGHT_BLUE}{BOLD} ██╗    ██╗███████╗██████╗ ██████╗ ██████╗ ██╗██████╗ ███████╗{RESET}{BLUE} ║{RESET}",
        f"{BLUE}  ║{RESET}{BRIGHT_BLUE}{BOLD} ██║    ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗██╔════╝{RESET}{BLUE} ║{RESET}",
        f"{BLUE}  ║{RESET}{BRIGHT_BLUE}{BOLD} ██║ █╗ ██║█████╗  ██║  ██║██████╔╝██████╔╝██║██║  ██║█████╗  {RESET}{BLUE} ║{RESET}",
        f"{BLUE}  ║{RESET}{BRIGHT_BLUE}{BOLD} ██║███╗██║██╔══╝  ██║  ██║██╔══██╗██╔══██╗██║██║  ██║██╔══╝  {RESET}{BLUE} ║{RESET}",
        f"{BLUE}  ║{RESET}{BRIGHT_BLUE}{BOLD} ╚███╔███╔╝███████╗██████╔╝██████╔╝██║  ██║██║██████╔╝███████╗{RESET}{BLUE} ║{RESET}",
        f"{BLUE}  ║{RESET}{BRIGHT_BLUE}{BOLD}  ╚══╝╚══╝ ╚══════╝╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝ ╚══════╝{RESET}{BLUE} ║{RESET}",
        f"{BLUE}  ╚══════════════════════════════════════════════════╝{RESET}",
        f"{GRAY}        企业微信 + Dify 智能桥接平台{RESET}",
        "",
        f"{BLUE}               █████████████████████          {RESET}",
        f"{BLUE}             ██                     █         {RESET}",
        f"{BLUE}           ██    ▓▓▓▓        ▓▓▓▓    ██       {RESET}",
        f"{BLUE}         ██    ▓▓    ▓▓    ▓▓    ▓▓    ██     {RESET}",
        f"{BLUE}       ██    ▓▓        ▓▓▓▓        ▓▓    ██   {RESET}",
        f"{BLUE}     ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██ {RESET}",
        ""
    ]
    
    if animated:
        for line in lines:
            print(line)
            time.sleep(0.03)
    else:
        for line in lines:
            print(line)


def print_menu(title, options, selected=0, animated=False):
    """打印菜单 - 带逐行动画"""
    lines = [
        "",
        f"{BLUE}{'═' * WIDTH}{RESET}",
        f"  {BRIGHT_BLUE}{BOLD}{title}{RESET}",
        f"{BLUE}{'─' * WIDTH}{RESET}",
    ]
    
    for idx, (key, label) in enumerate(options):
        if idx == selected:
            lines.append(f"  {CYAN}{BOLD}● {label}{RESET}")
        else:
            lines.append(f"    {label}")
    
    lines.extend([
        f"{BLUE}{'─' * WIDTH}{RESET}",
        f"  {GRAY}↑↓ 选择    {BRIGHT_BLUE}Enter 确认    {GRAY}0 返回{RESET}",
        ""
    ])
    
    if animated:
        for line in lines:
            print(line)
            time.sleep(0.02)
    else:
        for line in lines:
            print(line)


def interactive_menu(title, options):
    """
    交互式菜单 - 带逐行动画效果
    """
    import tty
    import termios
    import select
    
    selected = 0
    
    # 首次显示 - 带动画
    clear()
    print_banner(animated=True)
    print_menu(title, options, selected, animated=True)
    
    # 保存终端设置
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        # 设置终端为 cbreak 模式（不是 raw 模式）
        # cbreak 模式：可以读取单个字符，但仍保留一些终端处理
        tty.setcbreak(sys.stdin.fileno())
        
        while True:
            # 等待输入
            if select.select([sys.stdin], [], [], 0.1)[0]:
                char = sys.stdin.read(1)
                
                # ESC 序列（箭头键）
                if char == '\x1b':
                    next_char = sys.stdin.read(1)
                    if next_char == '[':
                        arrow = sys.stdin.read(1)
                        if arrow == 'A':  # 上
                            selected = (selected - 1) % len(options)
                        elif arrow == 'B':  # 下
                            selected = (selected + 1) % len(options)
                        # 重绘（无动画）
                        clear()
                        print_banner(animated=False)
                        print_menu(title, options, selected, animated=False)
                
                # Enter
                elif char == '\r' or char == '\n':
                    return options[selected][0]
                
                # 数字键直接选择（1-9）
                elif char in '123456789':
                    num = int(char)
                    if num <= len(options):
                        return options[num - 1][0]
                
                # 0 返回
                elif char == '0':
                    return None
                
                # Ctrl+C
                elif char == '\x03':
                    raise KeyboardInterrupt()
                
                # q 或 n 返回/取消
                elif char.lower() in ('q', 'n'):
                    return None
    
    finally:
        # 恢复终端设置
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def confirm_dialog(message):
    """确认对话框"""
    import tty
    import termios
    import select
    
    selected = 0
    options = ["否 (n)", "是 (y)"]
    
    def draw(animated=False):
        clear()
        print_banner(animated=animated)
        lines = [
            f"{BLUE}{'═' * WIDTH}{RESET}",
            f"  {BRIGHT_BLUE}{BOLD}确认{RESET}",
            f"{BLUE}{'─' * WIDTH}{RESET}",
        ]
        for line in message.split('\n'):
            lines.append(f"  {line}")
        lines.append(f"{BLUE}{'─' * WIDTH}{RESET}")
        for idx, opt in enumerate(options):
            if idx == selected:
                lines.append(f"  {CYAN}{BOLD}● {opt}{RESET}")
            else:
                lines.append(f"    {opt}")
        lines.extend([
            f"{BLUE}{'─' * WIDTH}{RESET}",
            f"  {GRAY}↑↓ 选择    {BRIGHT_BLUE}Enter 确认{RESET}",
            ""
        ])
        
        if animated:
            for line in lines:
                print(line)
                time.sleep(0.02)
        else:
            for line in lines:
                print(line)
    
    draw(animated=True)
    
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        tty.setcbreak(sys.stdin.fileno())
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                char = sys.stdin.read(1)
                
                if char == '\x1b':
                    next_char = sys.stdin.read(1)
                    if next_char == '[':
                        arrow = sys.stdin.read(1)
                        if arrow == 'B':  # 下
                            selected = (selected + 1) % 2
                            draw(animated=False)
                        elif arrow == 'A':  # 上
                            selected = (selected - 1) % 2
                            draw(animated=False)
                
                elif char == '\r' or char == '\n':
                    return selected == 1
                
                elif char == '\x03':
                    raise KeyboardInterrupt()
    
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def input_dialog(prompt_text, default=""):
    """输入对话框"""
    clear()
    print_banner(animated=False)
    print_line("═")
    print(f"  {BRIGHT_BLUE}{BOLD}{prompt_text}{RESET}")
    print_line("─")
    print()
    
    if default:
        print(f"  {GRAY}默认值: {default}{RESET}")
    
    try:
        value = input(f"  {CYAN}>{RESET} ")
        return value.strip()
    
    except KeyboardInterrupt:
        print()
        raise


def info_dialog(message):
    """信息对话框"""
    clear()
    print_banner()
    print_line("═")
    for line in message.split('\n'):
        print(f"  {line}")
    print_line("─")
    print()
    input(f"  {GRAY}按回车键继续...{RESET}")


def print_config_result(bot_id, owner, description, docker_url, host_url, port):
    """打印配置结果 - 自动检测主机 IP"""
    # 自动获取主机 IP
    from .utils import get_host_ip
    host_ip = get_host_ip()
    
    # 生成正确的 URL
    docker_url_linux = f"http://{host_ip}:{port}/notify?token={docker_url.split('token=')[1]}"
    
    clear()
    print_banner()
    print_line("═")
    print(f"  {BRIGHT_BLUE}{BOLD}配置成功{RESET}")
    print_line("─")
    print()
    print(f"  机器人: {CYAN}{bot_id}{RESET}")
    print(f"  配置人: {CYAN}{owner}{RESET}")
    print(f"  功能: {description}")
    print()
    print_line("─")
    print(f"  {BRIGHT_BLUE}【Docker Desktop (Mac/Win)】{RESET}")
    print(f"  {GRAY}http://host.docker.internal:{port}/notify?token=...{RESET}")
    print()
    print(f"  {BRIGHT_BLUE}【Docker (Linux) - 推荐】{RESET}")
    print(f"  {CYAN}{docker_url_linux}{RESET}")
    print()
    print(f"  {BRIGHT_BLUE}【服务器部署】{RESET}")
    print(f"  {host_url}")
    print()
    print_line("─")
    print(f"  Body: {CYAN}{{#LLM.text#}}{RESET}")
    print()
    print(f"  {GRAY}按回车键返回主菜单，或按 Ctrl+C 退出{RESET}")
    print()
    try:
        input()
    except KeyboardInterrupt:
        print()
        sys.exit(0)
