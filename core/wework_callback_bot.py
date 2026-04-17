# encoding:utf-8
"""
企业微信智能机器人（回调模式）+ Dify 桥接服务

功能：
1. 接收企业微信智能机器人的消息推送（回调模式）
2. 将消息转发到 Dify Webhook
3. 将 Dify 回复通过企业微信 API 发送给用户

企业微信智能机器人文档：
https://developer.work.weixin.qq.com/document/path/99198

使用方法：
1. 修改下方的配置
2. 运行: python wework_callback_bot.py
3. 在企业微信后台配置回调 URL: http://你的IP:9899/callback
"""

import json
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==================== 配置区域 ====================
# 企业微信配置
CORP_ID = "你的企业微信CorpID"  # 我的企业页面获取
BOT_ID = "aibpKUnDe2xfKlubp5Wt1LMpKl7se0fJvTd"
SECRET = "KulVSMRhNcIpAjYHHlGS7viWIs35PkAMdgcuHfMeOvk"
TOKEN = "你的Token"  # 在机器人后台随机生成
AES_KEY = "你的EncodingAESKey"  # 在机器人后台随机生成

# Dify Webhook 配置
DIFY_WEBHOOK_URL = "http://127.0.0.1/triggers/webhook/HjHPaSZsJcSJBHNLw4DrFcA8"

# 服务端口
PORT = 9899
# =================================================

# 全局变量
access_token = None
token_expire_time = 0


def get_access_token():
    """获取企业微信访问令牌"""
    global access_token, token_expire_time
    
    if access_token and time.time() < token_expire_time:
        return access_token
    
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORP_ID}&corpsecret={SECRET}"
    
    try:
        response = requests.get(url, timeout=30)
        result = response.json()
        
        if result.get("errcode") == 0:
            access_token = result["access_token"]
            token_expire_time = time.time() + result["expires_in"] - 300
            print(f"[Token] 获取成功")
            return access_token
        else:
            print(f"[Token] 获取失败: {result}")
            return None
            
    except Exception as e:
        print(f"[Token] 异常: {e}")
        return None


def send_message(user_id: str, message: str) -> bool:
    """发送消息给用户"""
    token = get_access_token()
    if not token:
        return False
    
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
    
    payload = {
        "touser": user_id,
        "msgtype": "text",
        "agentid": BOT_ID,
        "text": {
            "content": message
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        if result.get("errcode") == 0:
            print(f"[发送成功] -> {user_id}")
            return True
        else:
            print(f"[发送失败] {result}")
            return False
            
    except Exception as e:
        print(f"[发送异常] {e}")
        return False


def call_dify(query: str, user_id: str) -> str:
    """调用 Dify"""
    try:
        payload = {
            "query": query,
            "user_id": user_id
        }
        
        print(f"[Dify] 调用: {query[:50]}...")
        
        response = requests.post(
            DIFY_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict):
                return result.get("text", result.get("answer", str(result)))
            return str(result)
        else:
            return f"服务暂时不可用 (HTTP {response.status_code})"
            
    except Exception as e:
        return f"调用出错: {str(e)}"


@app.route('/callback', methods=['GET', 'POST'])
def callback():
    """企业微信回调接口"""
    if request.method == 'GET':
        # URL 验证
        msg_signature = request.args.get('msg_signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        print(f"[验证] signature={msg_signature}, timestamp={timestamp}, nonce={nonce}")
        
        # TODO: 实现消息签名验证
        # 参考: https://developer.work.weixin.qq.com/document/path/99198#%E6%B6%88%E6%81%AF%E7%9A%84%E5%8A%A0%E8%A7%A3%E5%AF%86
        
        return echostr
        
    elif request.method == 'POST':
        # 接收消息
        try:
            data = request.get_data()
            print(f"[收到消息] {data}")
            
            # TODO: 解密消息
            # 解析出 user_id 和 message
            
            # 临时：假设直接收到 JSON
            msg_data = request.get_json() or {}
            user_id = msg_data.get('FromUserName', 'unknown')
            message = msg_data.get('Content', '')
            
            if message:
                # 调用 Dify
                reply = call_dify(message, user_id)
                # 发送回复
                send_message(user_id, reply)
            
            return "success"
            
        except Exception as e:
            print(f"[处理错误] {e}")
            return "success"


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "bot_id": BOT_ID[:10] + "...",
        "corp_id": CORP_ID[:10] + "..." if CORP_ID != "你的企业微信CorpID" else "未配置"
    })


if __name__ == '__main__':
    print("=" * 60)
    print("企业微信智能机器人（回调模式）+ Dify 桥接服务")
    print("=" * 60)
    print(f"Bot ID: {BOT_ID[:20]}...")
    print(f"Dify: {DIFY_WEBHOOK_URL}")
    print(f"端口: {PORT}")
    print("=" * 60)
    print("\n⚠️  请配置 CORP_ID、TOKEN 和 AES_KEY")
    print("📖 文档: https://developer.work.weixin.qq.com/document/path/99198")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
