# encoding:utf-8
"""
企业微信 -> Dify Webhook 桥接服务

功能：
1. 接收企业微信应用的消息推送
2. 将消息转发到 Dify Webhook 触发节点
3. 将 Dify 工作流的回复返回给企业微信

使用方法：
1. 修改下方的配置参数
2. 运行: python webhook_bridge.py
3. 在企业微信后台配置接收消息URL为: http://你的服务器IP:9899/wxcomapp/
"""

import json
import requests
from flask import Flask, request, jsonify
from wechatpy.enterprise import create_reply, parse_message
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException

app = Flask(__name__)

# ==================== 配置区域 ====================
# 企业微信配置
CORP_ID = "你的企业微信CorpID"
AGENT_ID = "你的应用AgentID"
SECRET = "你的应用Secret"
TOKEN = "你的应用Token"
AES_KEY = "你的应用EncodingAESKey"

# Dify Webhook 配置
DIFY_WEBHOOK_URL = "http://localhost/triggers/webhook/HjHPaSZsJcSJBHNLw4DrFcA8"

# 服务端口
PORT = 9899
# =================================================

crypto = WeChatCrypto(TOKEN, AES_KEY, CORP_ID)


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
        
        response = requests.post(
            DIFY_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            # 根据 Dify Webhook 返回格式提取回复
            # 假设工作流输出变量名为 'text'
            if isinstance(result, dict):
                return result.get("text", result.get("answer", str(result)))
            return str(result)
        else:
            return f"调用 Dify 失败: HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        return "调用 Dify 超时，请稍后重试"
    except Exception as e:
        return f"调用 Dify 出错: {str(e)}"


@app.route('/wxcomapp/', methods=['GET', 'POST'])
def wechat_callback():
    """企业微信消息回调接口"""
    signature = request.args.get('msg_signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    
    if request.method == 'GET':
        # 处理URL验证
        echostr = request.args.get('echostr', '')
        try:
            echostr = crypto.check_signature(signature, timestamp, nonce, echostr)
            return echostr
        except InvalidSignatureException:
            return "Invalid signature", 403
            
    elif request.method == 'POST':
        # 处理消息推送
        try:
            # 解密消息
            message = crypto.decrypt_message(
                request.data,
                signature,
                timestamp,
                nonce
            )
            msg = parse_message(message)
            
            print(f"[收到消息] 来自: {msg.source}, 内容: {msg.content}")
            
            # 处理文本消息
            if msg.type == "text":
                user_query = msg.content
                user_id = msg.source
                
                # 调用 Dify Webhook
                reply_text = call_dify_webhook(user_query, user_id)
                
                # 构造回复
                reply = create_reply(reply_text, msg)
                encrypted_reply = crypto.encrypt_message(
                    reply.render(),
                    nonce,
                    timestamp
                )
                return encrypted_reply
                
            else:
                # 非文本消息，返回默认回复
                reply = create_reply("暂不支持此类消息，请发送文本", msg)
                encrypted_reply = crypto.encrypt_message(
                    reply.render(),
                    nonce,
                    timestamp
                )
                return encrypted_reply
                
        except InvalidSignatureException:
            return "Invalid signature", 403
        except Exception as e:
            print(f"处理消息出错: {e}")
            return "success"  # 返回success避免企业微信重试


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    print("=" * 50)
    print("企业微信 -> Dify Webhook 桥接服务")
    print("=" * 50)
    print(f"服务端口: {PORT}")
    print(f"Dify Webhook: {DIFY_WEBHOOK_URL}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
