# encoding:utf-8
"""
企业微信智能机器人 + Dify 工作流 多机器人桥接服务

支持多个企微机器人同时运行，每个机器人对应独立的 Dify 工作流。
通过 config.json 的 bots 数组统一配置，token 实现路由认证。

依赖：
    pip install wecom-aibot-sdk-python aiohttp --break-system-packages

使用方法：
    1. 编辑 config.json，在 bots 数组中配置每个机器人
    2. 运行: python wework_smart_bot_final.py

Dify HTTP 节点主动通知接口：
    POST http://<host>:{notify_port}/notify
    Body: {"token": "your-bot-token", "content": "消息内容", "chatid": "可选"}
    Response: {"ok": true}
"""

import asyncio
import json
import logging
import os
import secrets
import signal
import aiohttp
from aiohttp import web
from dataclasses import dataclass, field
from typing import Optional
from wecom_aibot_sdk import WSClient, generate_req_id, DefaultLogger


# ──────────────────────────────────────────────────────────
# 配置加载
# ──────────────────────────────────────────────────────────
def get_config_file():
    """获取配置文件路径，固定使用项目目录下的 config/config.json"""
    # 从 core/bridge_server.py 向上两级到项目根目录
    return os.path.join(os.path.dirname(__file__), "..", "config", "config.json")

_CONFIG_FILE = os.path.abspath(get_config_file())

def load_config() -> dict:
    with open(_CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)

cfg = load_config()

SERVICE_CFG  = cfg.get("service", {})
NOTIFY_PORT  = SERVICE_CFG.get("notify_port", 8899)
LOG_LEVEL    = getattr(logging, SERVICE_CFG.get("log_level", "INFO").upper(), logging.INFO)

# 只加载启用的机器人
ALL_BOTS_CFG = cfg.get("bots", [])
BOTS_CFG = [b for b in ALL_BOTS_CFG if b.get("enabled", True)]

# 按 WeCom Bot ID 分组，支持一个 Bot ID 对应多个 Dify 工作流
from collections import defaultdict
BOTS_BY_WECOM = defaultdict(list)
for bot in BOTS_CFG:
    wecom_id = bot.get("wecom", {}).get("bot_id", "")
    if wecom_id:
        BOTS_BY_WECOM[wecom_id].append(bot)

if not BOTS_CFG:
    raise ValueError("config.json 中没有启用的机器人，请至少启用一个")


# ──────────────────────────────────────────────────────────
# Bot 上下文（每个机器人一个实例）
# ──────────────────────────────────────────────────────────
@dataclass
class BotContext:
    bot_id:         str
    token:          str
    ws_client:      Optional[WSClient] = field(default=None, repr=False)
    dify_api_base:  str = "http://127.0.0.1/v1"
    dify_api_key:   str = ""
    dify_input_var: str = "input"
    dify_output_var:str = "text"
    dify_timeout:   int = 60
    default_chatid: str = ""
    welcome_msg:    str = "你好！有什么可以帮你的吗？"
    thinking_msg:   str = "⏳ 思考中..."
    description:    str = ""

    @classmethod
    def from_cfg(cls, bot_cfg: dict) -> "BotContext":
        dify = bot_cfg.get("dify", {})
        return cls(
            bot_id         = bot_cfg["id"],
            token          = bot_cfg["token"],
            dify_api_base  = dify.get("api_base",        "http://127.0.0.1/v1"),
            dify_api_key   = dify.get("api_key",         ""),
            dify_input_var = dify.get("input_variable",  "input"),
            dify_output_var= dify.get("output_variable", "text"),
            dify_timeout   = dify.get("timeout",         60),
            default_chatid = bot_cfg.get("default_chatid", ""),
            welcome_msg    = bot_cfg.get("welcome_message", "你好！有什么可以帮你的吗？"),
            thinking_msg   = bot_cfg.get("thinking_message", "⏳ 思考中..."),
            description    = bot_cfg.get("description", ""),
        )


# token → BotContext 路由表
_token_router: dict[str, BotContext] = {}


# ──────────────────────────────────────────────────────────
# Dify 工作流调用
# ──────────────────────────────────────────────────────────
async def call_dify_workflow(query: str, user_id: str, chatid: str, ctx: BotContext) -> str:
    url = f"{ctx.dify_api_base}/workflows/run"
    headers = {
        "Authorization": f"Bearer {ctx.dify_api_key}",
        "Content-Type":  "application/json",
    }
    payload = {
        "inputs": {
            ctx.dify_input_var: query,
            "chatid":           chatid,
        },
        "response_mode": "blocking",
        "user":          user_id,
    }
    try:
        timeout = aiohttp.ClientTimeout(total=ctx.dify_timeout)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=timeout) as resp:
                result = await resp.json()
                if resp.status == 200:
                    outputs = result.get("data", {}).get("outputs", {})
                    return outputs.get(ctx.dify_output_var, str(outputs))
                else:
                    msg = result.get("message", "未知错误")
                    print(f"[{ctx.bot_id}][Dify] 调用失败 {resp.status}: {msg}")
                    return f"Dify 调用失败: {msg}"
    except asyncio.TimeoutError:
        return "Dify 响应超时，请稍后重试"
    except Exception as e:
        return f"调用出错: {e}"


# ──────────────────────────────────────────────────────────
# Notify HTTP 服务（供 Dify HTTP 节点调用）
# ──────────────────────────────────────────────────────────
async def handle_notify(request: web.Request) -> web.Response:
    """
    POST /notify
    支持两种方式传递 token：
      1. URL 参数: /notify?token=xxx
      2. Body JSON: {"token": "xxx", "content": "..."}
    
    Body JSON:
      {
        "content": "消息内容",          ← 必填
        "chatid":  "可选，留空用 default_chatid"
      }

    兼容企微原生格式：
      {"msgtype": "text", "text": {"content": "..."}}
    """
    try:
        raw = await request.text()
        print(f"[Notify] 收到原始请求: {raw[:200]}")
        raw = "".join(c for c in raw if c >= " " or c == "\t")
        if not raw:
            return web.json_response({"ok": False, "error": "请求体为空"}, status=400)
        
        # 尝试解析 JSON，如果不是 JSON 则使用原始文本作为 content
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # 纯文本内容，包装成 JSON 格式
            data = {"content": raw}

        # 1. 获取 token（优先从 URL 参数，其次从 Body）
        token = str(request.query.get("token", "")).strip()
        if not token:
            token = str(data.get("token", "")).strip()
        if not token:
            return web.json_response({"ok": False, "error": "缺少 token 参数"}, status=400)

        ctx = _token_router.get(token)
        if ctx is None:
            return web.json_response({"ok": False, "error": "token 无效"}, status=401)

        if ctx.ws_client is None or not ctx.ws_client.is_connected:
            return web.json_response({"ok": False, "error": f"机器人 {ctx.bot_id} 未连接"}, status=503)

        # 2. 解析 chatid
        chatid = str(data.get("chatid", "")).strip() or ctx.default_chatid
        if not chatid:
            # 尝试从 URL 参数获取
            chatid = str(request.query.get("chatid", "")).strip() or ctx.default_chatid
        if not chatid:
            return web.json_response({"ok": False, "error": "chatid 不能为空且未配置 default_chatid"}, status=400)

        # 3. 解析消息内容（兼容多种格式）
        # 优先从 Body 原始文本获取（如果不是 JSON）
        content = ""
        try:
            # 尝试作为 JSON 解析 content 字段
            content = str(data.get("content", "")).strip()
            if not content:
                # 安全获取 text.content，防止 text 不是 dict
                text_field = data.get("text", {})
                if isinstance(text_field, dict):
                    content = str(text_field.get("content", "")).strip()
        except Exception as e:
            print(f"[Notify] 解析内容出错: {e}")
        
        # 如果 JSON 中没有 content，使用原始 body 作为内容
        if not content and raw:
            content = raw.strip()
        
        if not content:
            return web.json_response({"ok": False, "error": "content 不能为空"}, status=400)

        # 4. 发送到企微
        await ctx.ws_client.send_message(chatid, {
            "msgtype":  "markdown",
            "markdown": {"content": content},
        })
        print(f"[{ctx.bot_id}][Notify] → {chatid}: {content[:60]}")
        return web.json_response({"ok": True})

    except Exception as e:
        print(f"[Notify] 错误: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_health(request):
    """健康检查端点"""
    return web.json_response({
        "ok": True,
        "service": "bridge",
        "version": "1.0.0",
        "bots": len(_token_router),
        "connected_bots": sum(1 for ctx in _token_router.values() if ctx.ws_client and ctx.ws_client.is_connected)
    })


async def handle_options(request):
    """处理 CORS 预检请求"""
    return web.Response(status=200, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    })


@web.middleware
async def cors_middleware(request, handler):
    """CORS 中间件"""
    if request.method == "OPTIONS":
        return await handle_options(request)
    
    response = await handler(request)
    
    # 添加 CORS 头
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response


async def start_notify_server():
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get("/health", handle_health)
    app.router.add_post("/notify", handle_notify)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", NOTIFY_PORT)
    await site.start()
    print(f"[Notify] HTTP 服务已启动，端口 {NOTIFY_PORT}")
    print(f"[Notify] 健康检查: http://0.0.0.0:{NOTIFY_PORT}/health")


# ──────────────────────────────────────────────────────────
# 启动一组共享同一个 WeCom Bot ID 的机器人
# 一个 WeCom 连接，多个 Dify 工作流并行触发
# ──────────────────────────────────────────────────────────
async def start_bot_group(wecom_bot_id: str, bot_configs: list):
    """启动一组共享同一个 WeCom Bot ID 的机器人"""
    if not bot_configs:
        return
    
    # 使用第一个配置获取 WeCom 凭证
    primary_cfg = bot_configs[0]
    wecom_cfg = primary_cfg.get("wecom", {})
    
    # 为每个配置创建上下文
    contexts = []
    for cfg in bot_configs:
        ctx = BotContext.from_cfg(cfg)
        _token_router[ctx.token] = ctx
        contexts.append(ctx)
    
    logger = DefaultLogger(level=LOG_LEVEL)
    client = WSClient({
        "bot_id": wecom_cfg["bot_id"],
        "secret": wecom_cfg["secret"],
        "logger": logger,
    })
    
    # 给每个上下文设置 ws_client
    for ctx in contexts:
        ctx.ws_client = client
    
    tag = f"[{wecom_bot_id}]"
    bot_names = ", ".join([ctx.bot_id for ctx in contexts])

    async def on_connected(*args):
        print(f"{tag} WebSocket 已连接")

    async def on_authenticated(*args):
        print(f"{tag} 认证成功，管理机器人: {bot_names}")

    async def on_disconnected(reason):
        print(f"{tag} 断开连接: {reason}")

    async def on_reconnecting(attempt):
        print(f"{tag} 第 {attempt} 次重连...")

    async def on_enter(frame):
        # 发送第一个机器人的欢迎消息
        if contexts:
            await client.reply_welcome(frame, {
                "msgtype": "text",
                "text":    {"content": contexts[0].welcome_msg},
            })

    async def on_text(frame):
        """消息处理：同时触发所有启用的 Dify 工作流"""
        content = frame.body.get("text", {}).get("content", "").strip()
        sender  = (frame.body.get("from", {}).get("userid", "")
                   or frame.body.get("from", {}).get("id", "unknown"))
        chatid  = frame.body.get("chatid", sender)

        if not content:
            return

        print(f"\n{tag} 收到消息 {sender} (chatid={chatid}): {content}")
        print(f"{tag} 将并行触发 {len(contexts)} 个工作流...")

        # 先发送"思考中"提示
        stream_id = generate_req_id("stream")
        await client.reply_stream(frame, stream_id, contexts[0].thinking_msg, finish=False)

        # 并行调用所有 Dify 工作流
        async def call_workflow_with_ctx(ctx: BotContext):
            try:
                reply = await call_dify_workflow(content, sender, chatid, ctx)
                print(f"  [{ctx.bot_id}] 回复: {reply[:60]}{'...' if len(reply) > 60 else ''}")
                return reply
            except Exception as e:
                print(f"  [{ctx.bot_id}] 调用失败: {e}")
                return None

        # 并发执行所有工作流
        results = await asyncio.gather(*[call_workflow_with_ctx(ctx) for ctx in contexts])
        
        # 合并所有成功的工作流回复
        successful_replies = [r for r in results if r]
        if successful_replies:
            # 用分隔符合并多个回复
            if len(successful_replies) == 1:
                final_reply = successful_replies[0]
            else:
                final_reply = "\n\n---\n\n".join(successful_replies)
            await client.reply_stream(frame, stream_id, final_reply, finish=True)
        else:
            await client.reply_stream(frame, stream_id, "所有工作流调用失败", finish=True)

    client.on("connected",        on_connected)
    client.on("authenticated",    on_authenticated)
    client.on("disconnected",     on_disconnected)
    client.on("reconnecting",     on_reconnecting)
    client.on("event.enter_chat", on_enter)
    client.on("message.text",     on_text)

    print(f"{tag} 正在连接企业微信服务器... (管理 {len(contexts)} 个机器人)")
    await client.connect_async()

    # 保持连接
    while client.is_connected:
        await asyncio.sleep(1)


# 保持旧函数名兼容
async def start_bot(bot_raw_cfg: dict):
    """兼容旧接口，单个机器人启动"""
    wecom_id = bot_raw_cfg.get("wecom", {}).get("bot_id", "")
    await start_bot_group(wecom_id, [bot_raw_cfg])


# ──────────────────────────────────────────────────────────
# PID 文件管理
# ──────────────────────────────────────────────────────────
PID_FILE = os.path.join(os.path.dirname(__file__), "..", "bridge.pid")
PID_FILE = os.path.abspath(PID_FILE)

def write_pid():
    """写入 PID 文件"""
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

def remove_pid():
    """删除 PID 文件"""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

def check_existing_process():
    """检查是否已有进程在运行，如果是则自动重启"""
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            try:
                old_pid = int(f.read().strip())
                if os.path.exists(f"/proc/{old_pid}"):
                    print(f"[信息] 检测到已有服务在运行 (PID: {old_pid})")
                    print(f"[信息] 正在自动重启...")
                    # 发送终止信号给旧进程
                    try:
                        os.kill(old_pid, signal.SIGTERM)
                        # 等待旧进程结束
                        for _ in range(20):  # 最多等待 10 秒
                            if not os.path.exists(f"/proc/{old_pid}"):
                                break
                            import time
                            time.sleep(0.5)
                        else:
                            # 强制终止
                            os.kill(old_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # 进程已经结束了
                    print(f"[信息] 旧服务已停止")
            except (ValueError, OSError):
                pass
        # 删除旧 PID 文件
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    return True

# ──────────────────────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────────────────────
async def main():
    # 忽略 SIGHUP 信号（防止终端关闭时退出）
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    
    # 检查是否已有进程运行
    if not check_existing_process():
        return
    
    # 写入 PID 文件
    write_pid()
    
    print("=" * 60)
    print("  企业微信智能机器人 + Dify 多工作流桥接服务")
    print("=" * 60)
    print(f"  加载机器人数量: {len(BOTS_CFG)} (按 WeCom Bot 分组: {len(BOTS_BY_WECOM)} 组)")
    for wecom_id, bots in BOTS_BY_WECOM.items():
        if len(bots) == 1:
            print(f"    - [{bots[0]['id']}] {bots[0].get('description', '')}")
        else:
            print(f"    - [{wecom_id}] 包含 {len(bots)} 个工作流:")
            for b in bots:
                print(f"        • {b['id']}: {b.get('description', '')}")
    print(f"  Notify 端口: {NOTIFY_PORT}")
    print("=" * 60)
    print()

    # 启动 HTTP 通知服务
    await start_notify_server()

    # 按 WeCom Bot ID 分组启动，每组共享一个 WebSocket 连接
    try:
        await asyncio.gather(*[
            start_bot_group(wecom_id, bots) 
            for wecom_id, bots in BOTS_BY_WECOM.items()
        ])
    except KeyboardInterrupt:
        print("\n[停止] 服务已停止")
    finally:
        remove_pid()


if __name__ == "__main__":
    asyncio.run(main())
