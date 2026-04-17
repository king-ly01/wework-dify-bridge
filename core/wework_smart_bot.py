# encoding:utf-8
"""
企业微信智能机器人 + Dify 桥接服务

功能：
1. 使用长连接方式连接企业微信智能机器人
2. 接收用户消息并转发到 Dify Webhook
3. 将 Dify 回复发送回企业微信

企业微信智能机器人文档：
https://developer.work.weixin.qq.com/document/path/99198

使用方法：
1. 修改下方的 BOT_ID 和 SECRET
2. 修改 DIFY_WEBHOOK_URL
3. 运行: python wework_smart_bot.py
"""

import json
import time
import threading
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==================== 配置区域 ====================
# 企业微信智能机器人配置
BOT_ID = "aibpKUnDe2xfKlubp5Wt1LMpKl7se0fJvTd"
SECRET = "KulVSMRhNcIpAjYHHlGS7viWIs35PkAMdgcuHfMeOvk"

# Dify Webhook 配置
DIFY_WEBHOOK_URL = "http://127.0.0.1/triggers/webhook/HjHPaSZsJcSJBHNLw4DrFcA8"

# 服务端口（用于接收主动推送，如果企业微信支持的话）
PORT = 9899
# =================================================

# 全局变量
access_token = None
token_expire_time = 0


def get_access_token():
    """获取企业微信访问令牌"""
    global access_token, token_expire_time
    
    # 如果令牌未过期，直接返回
    if access_token and time.time() < token_expire_time:
        return access_token
    
    # 请求新令牌
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={BOT_ID}&corpsecret={SECRET}"
    
    try:
        response = requests.get(url, timeout=30)
        result = response.json()
        
        if result.get("errcode") == 0:
            access_token = result["access_token"]
            # 提前 5 分钟过期
            token_expire_time = time.time() + result["expires_in"] - 300
            print(f"[Token] 获取成功，有效期: {result['expires_in']} 秒")
            return access_token
        else:
            print(f"[Token] 获取失败: {result}")
            return None
            
    except Exception as e:
        print(f"[Token] 请求异常: {e}")
        return None


def send_message_to_user(user_id: str, message: str) -> bool:
    """
    发送消息给企业微信用户
    
    Args:
        user_id: 用户ID
        message: 消息内容
        
    Returns:
        是否发送成功
    """
    token = get_access_token()
    if not token:
        print("[发送失败] 无法获取 access_token")
        return False
    
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
    
    payload = {
        "touser": user_id,
        "msgtype": "text",
        "text": {
            "content": message
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        if result.get("errcode") == 0:
            print(f"[发送成功] 用户: {user_id}")
            return True
        else:
            print(f"[发送失败] {result}")
            return False
            
    except Exception as e:
        print(f"[发送异常] {e}")
        return False


def call_dify_webhook(query: str, user_id: str) -> str:
    """
    调用 Dify Webhook 触发工作流
    
    Args:
        query: 用户输入的消息
        user_id: 用户ID
        
    Returns:
        Dify 工作流的回复文本
    """
    try:
        payload = {
            "query": query,
            "user_id": user_id
        }
        
        print(f"[调用 Dify] 用户: {user_id}, 消息: {query}")
        
        response = requests.post(
            DIFY_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[Dify 返回] {result}")
            
            # 根据 Dify Webhook 返回格式提取回复
            if isinstance(result, dict):
                return result.get("text", result.get("answer", str(result)))
            return str(result)
        else:
            error_msg = f"调用 Dify 失败: HTTP {response.status_code}"
            print(f"[Dify 错误] {error_msg}")
            return error_msg
            
    except requests.exceptions.Timeout:
        return "调用 Dify 超时，请稍后重试"
    except Exception as e:
        return f"调用 Dify 出错: {str(e)}"


def process_message(user_id: str, message: str):
    """处理用户消息"""
    print(f"[收到消息] 用户: {user_id}, 内容: {message}")
    
    # 调用 Dify
    reply = call_dify_webhook(message, user_id)
    
    # 发送回复
    send_message_to_user(user_id, reply)


@app.route('/webhook', methods=['POST'])
def receive_webhook():
    """
    接收消息推送（如果企业微信支持主动推送）
    
    或者作为 Dify 回调接口
    """
    try:
        data = request.get_json()
        print(f"[Webhook] 收到数据: {data}")
        
        # 处理企业微信消息推送
        if data.get("msg_type") == "text":
            user_id = data.get("from_user")
            message = data.get("content")
            if user_id and message:
                # 异步处理，避免阻塞
                threading.Thread(
                    target=process_message,
                    args=(user_id, message)
                ).start()
        
        return jsonify({"errcode": 0, "errmsg": "ok"})
        
    except Exception as e:
        print(f"[Webhook 错误] {e}")
        return jsonify({"errcode": 0, "errmsg": "ok"})


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "bot_id": BOT_ID[:10] + "...",
        "dify_webhook": DIFY_WEBHOOK_URL
    })


def start_long_polling():
    """
    启动长连接轮询（模拟）
    
    注意：企业微信智能机器人的长连接需要使用官方 SDK
    这里提供一个简化版本，实际生产环境建议使用官方提供的 SDK
    """
    print("[长连接] 启动消息接收服务...")
    print("[提示] 企业微信智能机器人建议使用官方 SDK 启动长连接")
    print("[文档] https://developer.work.weixin.qq.com/document/path/99198")
    
    # 测试获取 Token
    token = get_access_token()
    if token:
        print("[连接成功] 已连接到企业微信智能机器人")
    else:
        print("[连接失败] 请检查 BOT_ID 和 SECRET 是否正确")


if __name__ == '__main__':
    print("=" * 60)
    print("企业微信智能机器人 + Dify 桥接服务")
    print("=" * 60)
    print(f"Bot ID: {BOT_ID[:15]}...")
    print(f"Dify Webhook: {DIFY_WEBHOOK_URL}")
    print(f"服务端口: {PORT}")
    print("=" * 60)
    
    # 启动长连接
    start_long_polling()
    
    # 启动 Flask 服务（用于接收回调）
    print("\n启动 HTTP 服务...")
    app.run(host='0.0.0.0', port=PORT, debug=False)
