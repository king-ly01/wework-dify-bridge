"""企业微信连接模块"""

import asyncio


def test_wecom_connection(bot_id: str, secret: str) -> tuple[bool, str]:
    """
    测试企业微信智能机器人连接 - 使用 WebSocket 长连接验证
    
    Args:
        bot_id: 机器人 ID
        secret: 机器人 Secret
    
    Returns:
        (是否成功, 消息)
    """
    try:
        from wecom_aibot_sdk import WSClient, DefaultLogger
        
        logger = DefaultLogger(level=30)  # WARNING，减少输出
        client = WSClient({
            "bot_id": bot_id,
            "secret": secret,
            "logger": logger,
        })
        
        async def check():
            try:
                # 尝试连接（5秒超时）
                await asyncio.wait_for(client.connect_async(), timeout=5)
                
                # 等待认证结果（再等待3秒）
                for _ in range(30):  # 3秒，每0.1秒检查一次
                    if client.is_authenticated:
                        await client.disconnect()
                        return True, "连接成功"
                    await asyncio.sleep(0.1)
                
                # 连接成功但认证失败
                await client.disconnect()
                return False, "连接成功但认证失败，请检查 Bot ID 和 Secret 是否正确"
                
            except asyncio.TimeoutError:
                return False, "连接超时，请检查网络或 Bot ID/Secret 是否正确"
            except Exception as e:
                return False, f"连接失败: {e}"
        
        # 运行异步检查
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(check())
        loop.close()
        return result
        
    except ImportError:
        return None, "缺少 wecom-aibot-sdk，无法测试"
    except Exception as e:
        return False, f"测试失败: {e}"


def wait_for_chatid(bot_id: str, secret: str, timeout: int = 60) -> tuple[bool, str]:
    """
    等待用户发送消息，捕获 chatid
    
    Args:
        bot_id: 机器人 ID
        secret: 机器人 Secret
        timeout: 超时时间（秒）
    
    Returns:
        (是否成功, chatid 或错误信息)
    """
    try:
        from wecom_aibot_sdk import WSClient, DefaultLogger
        
        logger = DefaultLogger(level=30)
        client = WSClient({
            "bot_id": bot_id,
            "secret": secret,
            "logger": logger,
        })
        
        chatid_received = None
        
        # 定义消息处理器
        async def on_text(frame):
            nonlocal chatid_received
            # 从 frame.body 中提取 chatid（参考 bridge_server.py 的实现）
            body = getattr(frame, 'body', {})
            if isinstance(body, dict):
                sender = body.get("from", {}).get("userid") or body.get("from", {}).get("id", "unknown")
                chatid = body.get("chatid", sender)
                if chatid and chatid != "unknown":
                    chatid_received = chatid
        
        # 注册消息处理器
        client.on("message.text", on_text)
        
        async def wait():
            try:
                await asyncio.wait_for(client.connect_async(), timeout=5)
                # 等待认证
                for _ in range(30):
                    if client.is_authenticated:
                        break
                    await asyncio.sleep(0.1)
                
                if not client.is_authenticated:
                    return False, "认证失败"
                
                # 等待用户发送消息（获取 chatid）
                for _ in range(timeout * 10):  # 每 0.1 秒检查一次
                    if chatid_received:
                        await client.disconnect()
                        return True, chatid_received
                    await asyncio.sleep(0.1)
                
                await client.disconnect()
                return False, "等待超时，未收到消息"
                
            except asyncio.TimeoutError:
                return False, "连接超时"
            except Exception as e:
                return False, f"错误: {e}"
        
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(wait())
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        return result
        
    except ImportError:
        return False, "缺少 wecom-aibot-sdk"
    except Exception as e:
        return False, f"失败: {e}"


def send_welcome_message(bot_id: str, secret: str, chatid: str, owner: str, bot_id_display: str) -> bool:
    """
    发送欢迎消息到企业微信机器人
    
    Args:
        bot_id: 机器人 ID
        secret: 机器人 Secret
        chatid: 聊天 ID
        owner: 配置人姓名
        bot_id_display: 显示的机器人 ID
    
    Returns:
        是否发送成功
    """
    try:
        from wecom_aibot_sdk import WSClient, DefaultLogger
        
        logger = DefaultLogger(level=30)
        client = WSClient({
            "bot_id": bot_id,
            "secret": secret,
            "logger": logger,
        })
        
        async def send():
            try:
                await asyncio.wait_for(client.connect_async(), timeout=5)
                for _ in range(30):
                    if client.is_authenticated:
                        break
                    await asyncio.sleep(0.1)
                
                if client.is_authenticated:
                    welcome_msg = f"""🎉 恭喜您！Bridge 连接成功！ 🎉

👋 {owner}，您好
🤖 机器人「{bot_id_display}」已成功 Bridge！

✨ Bridge 功能强大：
• 无缝连接企业微信与 Dify AI！
• 支持多个机器人同时运行！
• 智能消息路由，自动回复！
• 实时连接，秒级响应！

🚀 您的 AI 助手已就绪，随时可以为您服务！

💡 下一步： Dify 中配置 HTTP 节点，开始吧！"""
                    
                    try:
                        await client.send_message(
                            chatid=chatid,
                            body={
                                "msgtype": "markdown",
                                "markdown": {"content": welcome_msg}
                            }
                        )
                        await asyncio.sleep(0.5)
                        await client.disconnect()
                        await asyncio.sleep(0.2)
                        return True
                    except Exception as e:
                        print(f"发送消息错误: {e}")
                        return False
            except Exception:
                pass
            return False
        
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(send())
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        return result
    except Exception:
        return False
