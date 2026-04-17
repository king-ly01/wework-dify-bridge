#!/usr/bin/env python3
"""
Bridge CLI - 企微-Dify 桥接管理工具
"""

import json
import os
import secrets
import sys

# 导入 TUI 组件
from .tui import (
    interactive_menu, confirm_dialog, input_dialog, info_dialog,
    print_config_result, print_banner, print_line, 
    BLUE, BRIGHT_BLUE, CYAN, WHITE, GRAY, RESET, BOLD, clear
)

# 导入核心模块
from .core import (
    CONFIG_FILE, PID_FILE, LOG_FILE,
    load_config, save_config,
    is_running, start_service, stop_service, reload_config,
    validate_bot_id_uniqueness
)

# 导入网络模块（不动之前调好的代码）
from .network import (
    test_wecom_connection,
    test_dify_connection,
    wait_for_chatid,
    send_welcome_message
)

# 导入工具
from .utils import get_host_ip


class CancelledError(Exception):
    """用户取消"""
    pass


def cmd_start():
    """启动服务"""
    success, msg = start_service(PID_FILE, LOG_FILE)
    if success:
        print(f"{CYAN}✓ {msg}{RESET}")
    else:
        print(f"{GRAY}{msg}{RESET}")


def cmd_stop():
    """停止服务"""
    success, msg = stop_service(PID_FILE)
    if success:
        print(f"{CYAN}✓ {msg}{RESET}")
    else:
        print(f"{GRAY}{msg}{RESET}")


def cmd_restart():
    """重启服务（智能：先停止再启动，保证只有一个进程）"""
    print(f"{GRAY}正在重启服务...{RESET}")
    
    # 先停止
    running, pid = is_running(PID_FILE)
    if running:
        print(f"{GRAY}  停止现有服务 (PID: {pid})...{RESET}")
        success, msg = stop_service(PID_FILE)
        if success:
            print(f"{CYAN}  ✓ {msg}{RESET}")
        else:
            print(f"{GRAY}  {msg}{RESET}")
    
    # 等待确保进程已停止
    import time
    time.sleep(1)
    
    # 再启动
    print(f"{GRAY}  启动新服务...{RESET}")
    success, msg = start_service(PID_FILE, LOG_FILE)
    if success:
        print(f"{CYAN}  ✓ {msg}{RESET}")
    else:
        print(f"{GRAY}  {msg}{RESET}")


def cmd_status():
    """查看服务状态"""
    running, pid = is_running(PID_FILE)
    cfg = load_config()
    port = cfg.get("service", {}).get("notify_port", 8899)
    
    clear()
    print_banner()
    print_line("═")
    print(f"  {BRIGHT_BLUE}{BOLD}服务状态{RESET}")
    print_line("─")
    
    if running:
        print(f"  状态: {CYAN}运行中{RESET}")
        print(f"  PID: {pid}")
    else:
        print(f"  状态: {GRAY}已停止{RESET}")
    
    print(f"  端口: {port}")
    print_line("─")
    print()


def cmd_logs(lines: int = 50, follow: bool = False):
    """查看日志"""
    if not os.path.exists(LOG_FILE):
        print(f"{GRAY}日志文件不存在{RESET}")
        return
    
    if follow:
        print(f"{GRAY}按 Ctrl+C 退出日志跟踪{RESET}")
        try:
            import subprocess
            subprocess.run(["tail", "-f", LOG_FILE])
        except KeyboardInterrupt:
            print()
    else:
        try:
            with open(LOG_FILE, 'r') as f:
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    print(line, end='')
        except Exception as e:
            print(f"读取日志失败: {e}")


def cmd_id(bot_id: str = None):
    """查看机器人列表或详情"""
    cfg = load_config()
    bots = cfg.get("bots", [])
    port = cfg.get("service", {}).get("notify_port", 8899)
    host_ip = get_host_ip()
    
    clear()
    print_banner()
    
    if bot_id:
        for bot in bots:
            if bot.get("id") == bot_id:
                token = bot.get('token', '')
                url = f"http://{host_ip}:{port}/notify?token={token}"
                
                print_line("═")
                print(f"  {BRIGHT_BLUE}{BOLD}机器人详情{RESET}")
                print_line("─")
                print(f"  ID: {CYAN}{bot.get('id')}{RESET}")
                print(f"  配置人: {bot.get('owner')}")
                print(f"  功能: {bot.get('description')}")
                print()
                print_line("─")
                print(f"  {BRIGHT_BLUE}【URL】{RESET}")
                print(f"  {url}")
                print()
                print_line("─")
                print(f"  {BRIGHT_BLUE}【Body】{RESET}")
                print(f"  {{{{#LLM.text#}}}}")
                print_line("─")
                print()
                return
        print(f"找不到机器人: {bot_id}")
    else:
        print_line("═")
        print(f"  {BRIGHT_BLUE}{BOLD}机器人列表{RESET}")
        print_line("─")
        
        if not bots:
            print(f"  {GRAY}暂无配置的机器人{RESET}")
        else:
            for bot in bots:
                bid = bot.get('id', 'N/A')
                owner = bot.get('owner', 'N/A')
                desc = bot.get('description', '无描述')
                token = bot.get('token', '')[:20] + "..."
                url = f"http://{host_ip}:{port}/notify?token={token}"
                
                print(f"  {CYAN}{bid}{RESET} ({owner})")
                print(f"    {GRAY}{desc}{RESET}")
                print(f"    {GRAY}URL: {url}{RESET}")
                print()
        
        print_line("─")
        print(f"  {GRAY}查看详情: bridge id <机器人ID>{RESET}")
        print()


def create_robot_tui():
    """TUI 创建机器人"""
    cfg = load_config()
    
    clear()
    print_banner()
    
    try:
        # 1. 基本信息
        print_line("═")
        print(f"  {BRIGHT_BLUE}{BOLD}基本信息{RESET}")
        print_line("─")
        
        owner = input_dialog("您的姓名")
        if not owner:
            raise CancelledError()
        
        # 2. 机器人信息
        clear()
        print_banner()
        print_line("═")
        print(f"  {BRIGHT_BLUE}{BOLD}机器人信息{RESET}")
        print_line("─")
        
        while True:
            bot_id = input_dialog("机器人 ID")
            if not bot_id:
                raise CancelledError()
            
            valid, msg = validate_bot_id_uniqueness(cfg.get("bots", []), owner, bot_id)
            if valid:
                break
            
            clear()
            print_banner()
            print(f"  {GRAY}✗ {msg}{RESET}")
            print()
        
        description = input_dialog("机器人用途描述")
        if not description:
            raise CancelledError()
        
        # 3. 企业微信配置（带连接测试）
        clear()
        print_banner()
        print_line("═")
        print(f"  {BRIGHT_BLUE}{BOLD}企业微信配置{RESET}")
        print_line("─")
        
        while True:
            wecom_bot_id = input_dialog("Bot ID")
            if not wecom_bot_id:
                raise CancelledError()
            
            wecom_secret = input_dialog("Secret")
            if not wecom_secret:
                raise CancelledError()
            
            print()
            print(f"  {GRAY}正在测试企业微信连接...{RESET}")
            
            success, msg = test_wecom_connection(wecom_bot_id, wecom_secret)
            
            if success:
                print(f"  {CYAN}✓ 连接成功！{RESET}")
                break
            else:
                print(f"  {GRAY}✗ 连接失败: {msg}{RESET}")
                print()
                retry = input_dialog("是否重新输入 (y/n)")
                if retry.lower() != "y":
                    raise CancelledError()
        
        # 4. 获取 chatid
        clear()
        print_banner()
        print_line("═")
        print(f"  {BRIGHT_BLUE}{BOLD}获取 Chat ID{RESET}")
        print_line("─")
        print(f"  {GRAY}请在企业微信中给机器人发送一条消息{RESET}")
        print(f"  {GRAY}（例如：'你好' 或 '开始配置'）{RESET}")
        print()
        print(f"  {GRAY}正在等待消息...（60秒超时）{RESET}")
        print()
        
        success, result = wait_for_chatid(wecom_bot_id, wecom_secret, timeout=60)
        
        if success:
            chatid = result
            print(f"  {CYAN}✓ 已收到消息！{RESET}")
            
            # 发送欢迎消息
            print()
            print(f"  {GRAY}正在发送欢迎消息...{RESET}")
            if send_welcome_message(wecom_bot_id, wecom_secret, chatid, owner, bot_id):
                print(f"  {CYAN}✓ 欢迎消息已发送！{RESET}")
            else:
                print(f"  {GRAY}⚠ 欢迎消息发送失败{RESET}")
        else:
            print(f"  {GRAY}⚠ {result}{RESET}")
            print()
            print(f"  {GRAY}未收到机器人消息，返回主菜单...{RESET}")
            print()
            input(f"  按回车键继续...")
            raise CancelledError()
        
        # 5. Dify 配置
        clear()
        print_banner()
        print_line("═")
        print(f"  {BRIGHT_BLUE}{BOLD}Dify 配置{RESET}")
        print_line("─")
        
        while True:
            dify_api_base = input_dialog("API Base URL", default="http://127.0.0.1/v1")
            if not dify_api_base:
                raise CancelledError()
            
            dify_api_key = input_dialog("API Key (app-xxx)")
            if not dify_api_key:
                raise CancelledError()
            
            print()
            print(f"  {GRAY}正在测试 Dify 连接...{RESET}")
            
            success, msg = test_dify_connection(dify_api_base, dify_api_key)
            
            if success:
                print(f"  {CYAN}✓ Dify 连接成功！{RESET}")
                break
            else:
                print(f"  {GRAY}✗ 连接失败: {msg}{RESET}")
                print()
                retry = input_dialog("是否重新输入 (y/n)")
                if retry.lower() != "y":
                    raise CancelledError()
        
        # 6. 生成 token 并保存
        token = secrets.token_hex(20)
        
        bot_entry = {
            "id": bot_id,
            "owner": owner,
            "description": description,
            "token": token,
            "wecom": {
                "bot_id": wecom_bot_id,
                "secret": wecom_secret
            },
            "dify": {
                "api_base": dify_api_base,
                "api_key": dify_api_key,
                "workflow_id": "",
                "input_variable": "input",
                "output_variable": "text",
                "timeout": 60
            },
            "default_chatid": chatid,
            "welcome_message": f"你好！我是{description}，有什么可以帮你的吗？",
            "thinking_message": "⏳ 思考中..."
        }
        
        cfg["bots"].append(bot_entry)
        save_config(cfg)
        
        # 7. 显示结果
        port = cfg.get("service", {}).get("notify_port", 8899)
        host_ip = get_host_ip()
        
        docker_url = f"http://host.docker.internal:{port}/notify?token={token}"
        host_url = f"http://{host_ip}:{port}/notify?token={token}"
        
        print_config_result(bot_id, owner, description, docker_url, host_url, port)
    
    except CancelledError:
        print()
        print(f"  {GRAY}⚠ 配置已取消{RESET}")
        print()


def query_robots_tui():
    """TUI 查询机器人 - 显示完整配置信息"""
    cfg = load_config()
    bots = cfg.get("bots", [])
    port = cfg.get("service", {}).get("notify_port", 8899)
    host_ip = get_host_ip()
    
    owner = input_dialog("请输入您的姓名")
    if not owner:
        return
    
    owner_bots = [bot for bot in bots if bot.get("owner") == owner]
    
    if not owner_bots:
        info_dialog(f"未找到 {owner} 的机器人")
        return
    
    # 显示详细信息
    clear()
    print_banner()
    print_line("═")
    print(f"  {BRIGHT_BLUE}{BOLD}{owner} 的机器人配置{RESET}")
    print_line("═")
    
    for idx, bot in enumerate(owner_bots, 1):
        bid = bot.get('id', 'N/A')
        desc = bot.get('description', '无描述')
        token = bot.get('token', '')
        url = f"http://{host_ip}:{port}/notify?token={token}"
        
        wecom = bot.get('wecom', {})
        dify = bot.get('dify', {})
        
        print()
        print(f"  {CYAN}{idx}. {bid}{RESET}")
        print_line("─")
        print(f"     功能: {desc}")
        print()
        print(f"     {BRIGHT_BLUE}【URL】{RESET}")
        print(f"     {url}")
        print()
        print(f"     {BRIGHT_BLUE}【Dify】{RESET}")
        print(f"     API: {dify.get('api_base', 'N/A')}")
        print(f"     Key: {dify.get('api_key', 'N/A')[:20]}...")
        print()
        print(f"     {BRIGHT_BLUE}【企业微信】{RESET}")
        print(f"     Bot ID: {wecom.get('bot_id', 'N/A')}")
        print(f"     Secret: {wecom.get('secret', 'N/A')[:20]}...")
    
    print()
    print_line("─")
    input(f"  {GRAY}按回车键返回...{RESET}")


def control_robots_tui():
    """TUI 管控机器人 - 查看状态并启停"""
    cfg = load_config()
    bots = cfg.get("bots", [])
    port = cfg.get("service", {}).get("notify_port", 8899)
    host_ip = get_host_ip()
    
    if not bots:
        info_dialog("没有配置任何机器人")
        return
    
    while True:
        clear()
        print_banner()
        print_line("═")
        print(f"  {BRIGHT_BLUE}{BOLD}机器人管控{RESET}")
        print_line("─")
        print(f"  {GRAY}选择机器人进行启用/禁用操作{RESET}")
        print()
        
        # 构建菜单项
        menu_items = []
        for idx, bot in enumerate(bots, 1):
            bid = bot.get('id', 'N/A')
            desc = bot.get('description', '无描述')
            owner = bot.get('owner', '未知')
            enabled = bot.get('enabled', True)
            status_icon = f"{CYAN}●{RESET}" if enabled else f"{GRAY}○{RESET}"
            status_text = "启用" if enabled else "禁用"
            menu_items.append((str(idx), f"{status_icon} {bid} - {desc} [{owner}] ({status_text})"))
        
        menu_items.append(("back", "< 返回上一页"))
        
        choice = interactive_menu("选择机器人", menu_items)
        
        if choice is None or choice == "back":
            break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(bots):
                bot = bots[idx]
                bid = bot.get('id', 'N/A')
                
                current_enabled = bot.get('enabled', True)
                
                # 显示详情并确认操作
                clear()
                print_banner()
                print_line("═")
                print(f"  {BRIGHT_BLUE}{BOLD}机器人详情{RESET}")
                print_line("─")
                print(f"  ID: {bid}")
                print(f"  描述: {bot.get('description', '无描述')}")
                print(f"  归属: {bot.get('owner', '未知')}")
                print(f"  当前状态: {'启用' if current_enabled else '禁用'}")
                print()
                
                action = "禁用" if current_enabled else "启用"
                if confirm_dialog(f"确认{action}此机器人 {bid} 吗？"):
                    bot['enabled'] = not current_enabled
                    save_config(cfg)
                    # 重启服务使配置生效
                    running, pid = is_running(PID_FILE)
                    if running:
                        stop_service(PID_FILE)
                    start_service(PID_FILE, LOG_FILE)
                    info_dialog(f"机器人 {bid} 已{action}\n服务已重启生效")
                
        except (ValueError, IndexError):
            pass


def delete_robot_tui():
    """TUI 删除机器人"""
    cfg = load_config()
    bots = cfg.get("bots", [])
    
    owner = input_dialog("请输入您的姓名")
    if not owner:
        return
    
    owner_bots = [bot for bot in bots if bot.get("owner") == owner]
    
    if not owner_bots:
        info_dialog(f"未找到 {owner} 的机器人")
        return
    
    # 选择要删除的机器人
    options = [(bot.get('id'), f"{bot.get('id')} - {bot.get('description', '无描述')}") 
               for bot in owner_bots]
    
    choice = interactive_menu(f"{owner} 的机器人 - 选择删除", options)
    if choice is None:
        return
    
    # 确认删除
    if not confirm_dialog(f"确定要删除机器人 {choice} 吗？"):
        return
    
    # 执行删除
    cfg["bots"] = [bot for bot in bots if not (bot.get("owner") == owner and bot.get("id") == choice)]
    save_config(cfg)
    
    info_dialog(f"机器人 {choice} 已删除")


def modify_robot_tui():
    """TUI 修改机器人 - 先创建新配置，成功后再删除旧配置"""
    cfg = load_config()
    bots = cfg.get("bots", [])
    
    owner = input_dialog("请输入您的姓名")
    if not owner:
        return
    
    owner_bots = [bot for bot in bots if bot.get("owner") == owner]
    
    if not owner_bots:
        info_dialog(f"未找到 {owner} 的机器人")
        return
    
    # 选择要修改的机器人
    options = [(bot.get('id'), f"{bot.get('id')} - {bot.get('description', '无描述')}") 
               for bot in owner_bots]
    
    choice = interactive_menu(f"{owner} 的机器人 - 选择修改", options)
    if choice is None:
        return
    
    # 保存旧机器人信息用于恢复
    old_bot = None
    for bot in owner_bots:
        if bot.get('id') == choice:
            old_bot = bot.copy()
            break
    
    info_dialog(f"将重新配置机器人 {choice}，请按提示完成配置")
    
    # 先尝试创建新配置
    try:
        # 临时标记旧机器人为修改中（不删除）
        for bot in cfg["bots"]:
            if bot.get("owner") == owner and bot.get("id") == choice:
                bot["_modifying"] = True
                break
        save_config(cfg)
        
        # 执行创建流程
        create_robot_tui()
        
        # 创建成功后删除旧配置
        cfg = load_config()  # 重新加载，因为 create_robot_tui 可能修改了配置
        cfg["bots"] = [bot for bot in cfg.get("bots", []) 
                       if not (bot.get("owner") == owner and bot.get("id") == choice and bot.get("_modifying"))]
        save_config(cfg)
        
        info_dialog(f"机器人 {choice} 修改成功")
        
    except Exception as e:
        # 创建失败，恢复旧配置
        if old_bot:
            # 移除临时标记
            for bot in cfg["bots"]:
                if bot.get("_modifying"):
                    del bot["_modifying"]
                    break
            save_config(cfg)
        info_dialog(f"修改失败，保留原配置: {str(e)}")


def cmd_config():
    """配置机器人（TUI 入口）"""
    cfg = load_config()
    bots = cfg.get("bots", [])
    enabled_count = sum(1 for b in bots if b.get("enabled", True))
    total_count = len(bots)
    
    while True:
        choice = interactive_menu(
            f"机器人管理  (启用: {enabled_count}/{total_count})",
            [
                ("1", "新增机器人连接"),
                ("2", "修改机器人连接"),
                ("3", "管控机器人连接"),
                ("4", "查询机器人连接"),
                ("5", "删除机器人连接"),
                ("back", "< 返回上一页"),
            ]
        )
        
        if choice is None or choice == "back":
            break
        
        if choice == "1":
            create_robot_tui()
        elif choice == "2":
            modify_robot_tui()
        elif choice == "3":
            control_robots_tui()
        elif choice == "4":
            query_robots_tui()
        elif choice == "5":
            delete_robot_tui()
        
        # 刷新数量
        cfg = load_config()
        bots = cfg.get("bots", [])
        enabled_count = sum(1 for b in bots if b.get("enabled", True))
        total_count = len(bots)


def cmd_gateway():
    """网关配置（TUI）"""
    cfg = load_config()
    service = cfg.get("service", {})
    
    while True:
        choice = interactive_menu(
            "网关配置",
            [
                ("view", f"查看配置 (端口: {service.get('notify_port', 8899)})"),
                ("port", "修改端口"),
                ("log", f"日志级别: {service.get('log_level', 'INFO')}"),
                ("back", "< 返回上一页"),
            ]
        )
        
        if choice is None or choice == "back":
            break
        
        if choice == "view":
            clear()
            print_banner()
            print_line("═")
            print(f"  {BRIGHT_BLUE}{BOLD}当前网关配置{RESET}")
            print_line("─")
            print(f"  端口: {service.get('notify_port', 8899)}")
            print(f"  日志级别: {service.get('log_level', 'INFO')}")
            print_line("─")
            print()
            input(f"  {GRAY}按回车键继续...{RESET}")
        
        elif choice == "port":
            new_port = input_dialog("新端口", default=str(service.get('notify_port', 8899)))
            if new_port and new_port.isdigit():
                cfg["service"]["notify_port"] = int(new_port)
                save_config(cfg)
                info_dialog(f"端口已修改为 {new_port}")
        
        elif choice == "log":
            log_choice = interactive_menu(
                "选择日志级别",
                [
                    ("DEBUG", "DEBUG"),
                    ("INFO", "INFO"),
                    ("WARNING", "WARNING"),
                    ("ERROR", "ERROR"),
                    ("back", "< 返回上一页"),
                ]
            )
            if log_choice and log_choice != "back":
                cfg["service"]["log_level"] = log_choice
                save_config(cfg)
                info_dialog(f"日志级别已修改为 {log_choice}")


def main():
    """主入口"""
    if len(sys.argv) < 2:
        clear()
        print_banner()
        print()
        print(f"  {BRIGHT_BLUE}{BOLD}用法:{RESET} bridge <command>")
        print()
        print(f"  {CYAN}start{RESET}      启动服务")
        print(f"  {CYAN}stop{RESET}       停止服务")
        print(f"  {CYAN}restart{RESET}    重启服务")
        print(f"  {CYAN}status{RESET}     查看状态")
        print(f"  {CYAN}logs{RESET}       查看日志 (logs -f 实时跟踪, logs 100 查看100行)")
        print(f"  {CYAN}id{RESET}         查看机器人")
        print(f"  {CYAN}config{RESET}     配置机器人")
        print(f"  {CYAN}gateway{RESET}    网关配置")
        print()
        return
    
    cmd = sys.argv[1]
    
    try:
        if cmd == "start":
            cmd_start()
        elif cmd == "stop":
            cmd_stop()
        elif cmd == "restart":
            cmd_restart()
        elif cmd == "status":
            cmd_status()
        elif cmd == "logs":
            # 解析参数: logs [-f] [行数]
            follow_mode = "-f" in sys.argv or "--follow" in sys.argv
            lines = 50
            for i, arg in enumerate(sys.argv[2:], 2):
                if arg not in ["-f", "--follow"] and arg.isdigit():
                    lines = int(arg)
                    break
            cmd_logs(lines=lines, follow=follow_mode)
        elif cmd == "id":
            bot_id = sys.argv[2] if len(sys.argv) > 2 else None
            cmd_id(bot_id)
        elif cmd == "config":
            cmd_config()
        elif cmd == "gateway":
            cmd_gateway()
        else:
            print(f"未知命令: {cmd}")
    except KeyboardInterrupt:
        print()
        print(f"{GRAY}已取消{RESET}")


if __name__ == "__main__":
    main()
