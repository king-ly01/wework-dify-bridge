# encoding:utf-8
"""
企业微信机器人消息发送服务

功能：接收 HTTP 请求，转发消息到企业微信机器人

Dify 工作流配置：
1. 添加 HTTP 请求节点
2. 请求方法：POST
3. URL：http://127.0.0.1:9899/send
4. Body：{"message": "{{#start.text#}}"}

使用方法：
python wework_bot_sender.py
"""

import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ==================== 配置区域 ====================
# 企业微信机器人 Webhook 地址
# 格式：https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx
WECOM_BOT_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的机器人Key"

# 服务端口
PORT = 9899
# =================================================


def send_to_wework_bot(message: str, msg_type: str = "text") -> dict:
    """
    发送消息到企业微信机器人
    
    Args:
        message: 要发送的消息内容
        msg_type: 消息类型 (text/markdown)
        
    Returns:
        发送结果
    """
    try:
        if msg_type == "markdown":
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": message
                }
            }
        else:
            payload = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
        
        response = requests.post(
            WECOM_BOT_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        result = response.json()
        return {
            "success": result.get("errcode") == 0,
            "errcode": result.get("errcode"),
            "errmsg": result.get("errmsg")
        }
            
    except Exception as e:
        return {
            "success": False,
            "errcode": -1,
            "errmsg": str(e)
        }


@app.route('/send', methods=['POST'])
def send_message():
    """
    接收消息并发送到企业微信机器人
    
    请求格式：
    {
        "message": "消息内容",
        "type": "text"  // 可选，默认为 text，支持 markdown
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请求体为空"}), 400
        
        message = data.get("message", "")
        msg_type = data.get("type", "text")
        
        if not message:
            return jsonify({"success": False, "error": "message 不能为空"}), 400
        
        print(f"[接收消息] {message}")
        
        result = send_to_wework_bot(message, msg_type)
        
        if result["success"]:
            print(f"[发送成功]")
            return jsonify({"success": True, "data": result})
        else:
            print(f"[发送失败] {result}")
            return jsonify({"success": False, "error": result["errmsg"]}), 500
            
    except Exception as e:
        print(f"[错误] {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    print("=" * 60)
    print("企业微信机器人消息发送服务")
    print("=" * 60)
    print(f"服务地址: http://127.0.0.1:{PORT}")
    print(f"发送接口: POST http://127.0.0.1:{PORT}/send")
    print(f"健康检查: GET http://127.0.0.1:{PORT}/health")
    print("=" * 60)
    print("\n请修改配置：WECOM_BOT_WEBHOOK_URL = 你的机器人Webhook地址")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
