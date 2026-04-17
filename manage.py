#!/usr/bin/env python3
# encoding:utf-8
"""
wework-dify-bridge 管理工具

用法：
    python manage.py list              查看所有机器人
    python manage.py add               添加机器人（交互式）
    python manage.py delete <id>       删除机器人
    python manage.py token <id>        查看 / 重新生成 token
    python manage.py show <id>         查看单个机器人详情
"""

import json
import os
import secrets
import sys

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
EXAMPLE_FILE = os.path.join(os.path.dirname(__file__), "config.example.json")

# ── 颜色 ────────────────────────────────────────────────────
class C:
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    GRAY   = "\033[90m"
    RESET  = "\033[0m"

def bold(s):   return f"{C.BOLD}{s}{C.RESET}"
def green(s):  return f"{C.GREEN}{s}{C.RESET}"
def yellow(s): return f"{C.YELLOW}{s}{C.RESET}"
def red(s):    return f"{C.RED}{s}{C.RESET}"
def cyan(s):   return f"{C.CYAN}{s}{C.RESET}"
def gray(s):   return f"{C.GRAY}{s}{C.RESET}"


# ── 配置读写 ──────────────────────────────────────────────────
def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        if os.path.exists(EXAMPLE_FILE):
            with open(EXAMPLE_FILE, encoding="utf-8") as f:
                cfg = json.load(f)
            # 清空示例 bots
            cfg["bots"] = []
            save_config(cfg)
            print(green("✅ 已从模板初始化 config.json"))
        else:
            cfg = {"service": {"notify_port": 8899, "log_level": "INFO"}, "bots": []}
            save_config(cfg)
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def get_bots(cfg: dict) -> list:
    return cfg.get("bots", [])

def find_bot(cfg: dict, bot_id: str) -> dict | None:
    for b in get_bots(cfg):
        if b["id"] == bot_id:
            return b
    return None


# ── 生成 Token ────────────────────────────────────────────────
def gen_token() -> str:
    return secrets.token_hex(20)


# ── 输入辅助 ─────────────────────────────────────────────────
def prompt(label: str, default: str = "", required: bool = True) -> str:
    hint = f" [{default}]" if default else ""
    while True:
        val = input(f"  {bold(label)}{hint}: ").strip()
        if not val:
            val = default
        if val or not required:
            return val
        print(red("  此项必填，请重新输入"))


# ── 命令：list ────────────────────────────────────────────────
def cmd_list():
    cfg = load_config()
    bots = get_bots(cfg)
    port = cfg.get("service", {}).get("notify_port", 8899)

    print()
    print(bold("=" * 62))
    print(bold(f"  wework-dify-bridge  |  Notify 端口: {port}"))
    print(bold("=" * 62))

    if not bots:
        print(yellow("  暂无机器人，使用 python manage.py add 添加"))
        print()
        return

    print(f"  共 {cyan(str(len(bots)))} 个机器人\n")
    for i, b in enumerate(bots, 1):
        status_chatid = green(b.get('default_chatid', '') or gray('(未设置)'))
        print(f"  {bold(str(i))}. [{cyan(b['id'])}]  {gray(b.get('description', ''))}")
        print(f"     Token       : {yellow(b['token'])}")
        print(f"     企微 Bot ID : {b['wecom']['bot_id'][:20]}...")
        print(f"     Dify API Key: {b['dify']['api_key'][:20]}...")
        print(f"     默认 chatid : {status_chatid}")
        print()
    print(bold("=" * 62))
    print()


# ── 命令：add ─────────────────────────────────────────────────
def cmd_add():
    cfg = load_config()
    bots = get_bots(cfg)
    existing_ids = {b["id"] for b in bots}

    print()
    print(bold("━━━ 添加新机器人 ━━━"))
    print()

    # 1. 基本信息
    while True:
        bot_id = prompt("机器人 ID（唯一标识，如 bot-meeting）")
        if bot_id in existing_ids:
            print(red(f"  ID [{bot_id}] 已存在，请换一个"))
        else:
            break

    description = prompt("描述（备注，可留空）", required=False)

    # 2. 企业微信
    print()
    print(bold("  ── 企业微信配置 ──"))
    wecom_bot_id = prompt("企微机器人 Bot ID")
    wecom_secret = prompt("企微机器人 Secret")

    # 3. Dify
    print()
    print(bold("  ── Dify 配置 ──"))
    dify_api_base = prompt("Dify API Base", default="http://127.0.0.1/v1")
    dify_api_key  = prompt("Dify API Key（app-xxx）")
    dify_input    = prompt("工作流输入变量名", default="input")
    dify_output   = prompt("工作流输出变量名", default="text")
    dify_timeout  = prompt("超时秒数", default="60")

    # 4. 其他
    print()
    print(bold("  ── 其他配置 ──"))
    default_chatid  = prompt("默认 chatid（可留空，后续从日志获取）", required=False)
    welcome_message = prompt("欢迎语", default="你好！有什么可以帮你的吗？")
    thinking_message= prompt("等待提示", default="⏳ 思考中...")

    # 5. 生成 Token
    token = gen_token()

    bot_entry = {
        "id":          bot_id,
        "description": description,
        "token":       token,
        "wecom": {
            "bot_id": wecom_bot_id,
            "secret": wecom_secret,
        },
        "dify": {
            "api_base":       dify_api_base,
            "api_key":        dify_api_key,
            "input_variable": dify_input,
            "output_variable":dify_output,
            "timeout":        int(dify_timeout),
        },
        "default_chatid":  default_chatid,
        "welcome_message": welcome_message,
        "thinking_message":thinking_message,
    }

    cfg["bots"].append(bot_entry)
    save_config(cfg)

    print()
    print(bold("=" * 62))
    print(green(f"  ✅ 机器人 [{bot_id}] 添加成功！"))
    print(bold("=" * 62))
    print()
    print(f"  机器人 ID  : {cyan(bot_id)}")
    print(f"  描述       : {description or gray('(无)')}")
    print()
    print(f"  {bold('Token（请复制到 Dify 环境变量 bridge_token）：')}")
    print(f"  {yellow(token)}")
    print()
    print(f"  Dify HTTP 节点 Body 示例：")
    print(f'  {gray("{")}"token":"{yellow(token)}","content":"{{{{#LLM节点ID.text#}}}}"{gray("}")}')
    print()
    print(f"  {bold('重启服务后生效：')}")
    print(f"  ./start.sh restart")
    print()
    print(bold("=" * 62))
    print()


# ── 命令：delete ──────────────────────────────────────────────
def cmd_delete(bot_id: str):
    cfg = load_config()
    bot = find_bot(cfg, bot_id)
    if not bot:
        print(red(f"\n  ❌ 未找到机器人 [{bot_id}]\n"))
        sys.exit(1)

    print()
    print(f"  将删除机器人: {cyan(bot_id)}  {gray(bot.get('description', ''))}")
    confirm = input(f"  确认删除？{red('[y/N]')}: ").strip().lower()
    if confirm != "y":
        print(yellow("  已取消"))
        return

    cfg["bots"] = [b for b in cfg["bots"] if b["id"] != bot_id]
    save_config(cfg)
    print(green(f"\n  ✅ 机器人 [{bot_id}] 已删除，重启服务后生效\n"))


# ── 命令：token ───────────────────────────────────────────────
def cmd_token(bot_id: str):
    cfg = load_config()
    bot = find_bot(cfg, bot_id)
    if not bot:
        print(red(f"\n  ❌ 未找到机器人 [{bot_id}]\n"))
        sys.exit(1)

    print()
    print(f"  机器人 [{cyan(bot_id)}] 当前 Token：")
    print(f"  {yellow(bot['token'])}")
    print()
    confirm = input(f"  是否重新生成 Token？{red('[y/N]')}: ").strip().lower()
    if confirm != "y":
        return

    new_token = gen_token()
    bot["token"] = new_token
    save_config(cfg)

    print()
    print(green("  ✅ Token 已更新！"))
    print(f"  新 Token：{yellow(new_token)}")
    print()
    print(yellow("  ⚠️  请同步更新 Dify 环境变量 bridge_token，并重启服务！"))
    print()


# ── 命令：show ────────────────────────────────────────────────
def cmd_show(bot_id: str):
    cfg = load_config()
    bot = find_bot(cfg, bot_id)
    if not bot:
        print(red(f"\n  ❌ 未找到机器人 [{bot_id}]\n"))
        sys.exit(1)

    print()
    print(bold(f"  ── [{bot_id}] 详情 ──────────────────────────"))
    print(f"  ID          : {cyan(bot['id'])}")
    print(f"  描述        : {bot.get('description') or gray('(无)')}")
    print(f"  Token       : {yellow(bot['token'])}")
    print()
    print(f"  企微 Bot ID : {bot['wecom']['bot_id']}")
    print(f"  企微 Secret : {bot['wecom']['secret'][:8]}{'*' * 20}")
    print()
    print(f"  Dify Base   : {bot['dify']['api_base']}")
    print(f"  Dify API Key: {bot['dify']['api_key']}")
    print(f"  输入变量    : {bot['dify']['input_variable']}")
    print(f"  输出变量    : {bot['dify']['output_variable']}")
    print(f"  超时        : {bot['dify'].get('timeout', 60)}s")
    print()
    print(f"  默认 chatid : {bot.get('default_chatid') or gray('(未设置)')}")
    print(f"  欢迎语      : {bot.get('welcome_message', '')}")
    print(f"  等待提示    : {bot.get('thinking_message', '')}")
    print()
    print(bold("  Dify HTTP 节点 Body："))
    token = bot['token']
    print(f'  {{"token":"{yellow(token)}","content":"{{#LLM节点ID.text#}}"}}')
    print()


# ── 帮助 ─────────────────────────────────────────────────────
def cmd_help():
    print(f"""
{bold('wework-dify-bridge 管理工具')}

{bold('用法：')}
  python manage.py list              查看所有机器人
  python manage.py add               添加机器人（交互式）
  python manage.py delete <id>       删除机器人
  python manage.py token <id>        查看 / 重新生成 token
  python manage.py show <id>         查看单个机器人详情

{bold('示例：')}
  python manage.py add
  python manage.py list
  python manage.py show bot-meeting
  python manage.py token bot-meeting
  python manage.py delete bot-hr
""")


# ── 入口 ─────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]

    if not args or args[0] in ("help", "--help", "-h"):
        cmd_help()
    elif args[0] == "list":
        cmd_list()
    elif args[0] == "add":
        cmd_add()
    elif args[0] == "delete":
        if len(args) < 2:
            print(red("\n  用法：python manage.py delete <id>\n"))
            sys.exit(1)
        cmd_delete(args[1])
    elif args[0] == "token":
        if len(args) < 2:
            print(red("\n  用法：python manage.py token <id>\n"))
            sys.exit(1)
        cmd_token(args[1])
    elif args[0] == "show":
        if len(args) < 2:
            print(red("\n  用法：python manage.py show <id>\n"))
            sys.exit(1)
        cmd_show(args[1])
    else:
        print(red(f"\n  未知命令：{args[0]}"))
        cmd_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
