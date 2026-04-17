# wework-dify-bridge

企业微信智能机器人 + Dify 工作流 **多机器人多工作流桥接服务**。

通过一个 `config.json` 统一管理多个企微机器人，每个机器人对应一个独立的 Dify 工作流，实现一对一隔离路由。Dify HTTP 节点通过 `token` 认证，将消息精准回送到对应机器人。

---

## 目录

1. [架构说明](#1-架构说明)
2. [项目结构](#2-项目结构)
3. [安装依赖](#3-安装依赖)
4. [管理工具 manage.py](#4-管理工具-managepy)
5. [config.json 配置说明](#5-configjson-配置说明)
6. [启动与停止](#6-启动与停止)
7. [Dify 工作流配置要求](#7-dify-工作流配置要求)
8. [Dify HTTP 通知节点配置](#8-dify-http-通知节点配置)
9. [Dify Squid 代理白名单配置](#9-dify-squid-代理白名单配置)
10. [常见问题排查](#10-常见问题排查)

---

## 1. 架构说明

```
企微机器人A ──┐                           ┌── Dify 工作流A (api_key_A)
企微机器人B ──┤  wework-dify-bridge        ├── Dify 工作流B (api_key_B)
企微机器人C ──┘  (统一路由层, 单进程)      └── Dify 工作流C (api_key_C)
               ↑
         POST /notify  {"token":"xxx", "content":"..."}
         (Dify HTTP 节点回调，通过 token 路由到对应机器人)
```

**路由机制：**

| 方向 | 路由依据 |
|------|---------|
| 企微消息 → Dify | 哪个 WSClient 收到消息，就调用该 bot 绑定的 Dify api_key |
| Dify → 企微 | HTTP 节点 Body 中的 `token` 字段，找到对应机器人发送 |

---

## 2. 项目结构

```
wework-dify-bridge/
├── wework_smart_bot_final.py   # 主程序（一般不需要修改）
├── config.json                 # ⭐ 所有配置，唯一需要修改的文件
├── config.example.json         # 配置模板（脱敏，无密钥）
├── requirements.txt            # Python 依赖
├── install.sh                  # Linux 一键安装
├── start.sh                    # Linux 服务管理
├── start.bat                   # Windows 服务管理
├── wework-dify-bridge.service  # systemd 开机自启模板
├── README.md                   # 本文档
└── bridge.log                  # 运行日志（自动生成）
```

---

## 3. 安装依赖

> 安装完成后通过 `manage.py` 管理机器人，无需手动编辑 config.json。

### Linux / macOS

```bash
# 方法一：一键安装脚本（推荐）
sudo bash install.sh

# 方法二：手动安装
pip install wecom-aibot-sdk-python aiohttp --break-system-packages
```

### Windows

先安装 [Python 3.8+](https://www.python.org/downloads/)（安装时勾选 **Add Python to PATH**），然后：

```bat
start.bat install
```

---

## 4. 管理工具 manage.py

所有机器人的增删查改都通过 `manage.py` 完成，**无需手动编辑 config.json**。

### 命令一览

| 命令 | 说明 |
|------|------|
| `python manage.py list` | 查看所有机器人 |
| `python manage.py add` | 添加机器人（交互式引导，自动生成 token）|
| `python manage.py show <id>` | 查看某个机器人的完整信息 + Dify HTTP节点 Body 示例 |
| `python manage.py delete <id>` | 删除机器人 |
| `python manage.py token <id>` | 查看或重新生成 token |

### 典型流程

```bash
# 第一步：添加机器人
python manage.py add
# 按提示输入：机器人ID、描述、企微 bot_id、secret、Dify api_key 等
# 完成后自动生成 token 并显示在终端

# 第二步：把显示的 token 粘贴到 Dify 工作流的环境变量 bridge_token

# 第三步：重启服务
./start.sh restart

# 查看所有机器人
python manage.py list

# 查看某个机器人详情（包含 Dify HTTP节点 Body 示例）
python manage.py show bot-meeting

# 删除机器人
python manage.py delete bot-hr

# token 泄露了？重新生成
python manage.py token bot-meeting
```

### add 命令交互示例

```
$ python manage.py add

━━━ 添加新机器人 ━━━

  机器人 ID（唯一标识，如 bot-meeting）: bot-meeting
  描述（备注，可留空）: 会议室预订机器人

  ── 企业微信配置 ──
  企微机器人 Bot ID: aibpKUnDe2xfKl...
  企微机器人 Secret: KulVSMRhNcIp...

  ── Dify 配置 ──
  Dify API Base [http://127.0.0.1/v1]: 
  Dify API Key（app-xxx）: app-0qW0m8xPD3...
  工作流输入变量名 [input]: 
  工作流输出变量名 [text]: 
  超时秒数 [60]: 

  ── 其他配置 ──
  默认 chatid（可留空，后续从日志获取）: 
  欢迎语 [你好！有什么可以帮你的吗？]: 
  等待提示 [⏳ 思考中...]: 

══════════════════════════════════════════════════════════════
  ✅ 机器人 [bot-meeting] 添加成功！
══════════════════════════════════════════════════════════════

  Token（请复制到 Dify 环境变量 bridge_token）：
  a3f8c2d1e4b5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0

  Dify HTTP 节点 Body 示例：
  {"token":"a3f8c2...","content":"{{#LLM节点ID.text#}}"}

  重启服务后生效：
  ./start.sh restart
══════════════════════════════════════════════════════════════
```

---

## 5. config.json 配置说明

初次使用先复制模板：

```bash
cp config.example.json config.json
```

完整结构示例（2 个机器人）：

```json
{
  "service": {
    "notify_port": 8899,
    "log_level": "INFO"
  },
  "bots": [
    {
      "id": "bot-meeting",
      "description": "会议室预订机器人",
      "token": "your-secret-token-1",
      "wecom": {
        "bot_id": "企微机器人 Bot ID",
        "secret": "企微机器人 Secret"
      },
      "dify": {
        "api_base": "http://127.0.0.1/v1",
        "api_key": "app-xxx（Dify 工作流 API 密钥）",
        "input_variable": "input",
        "output_variable": "text",
        "timeout": 60
      },
      "default_chatid": "目标会话 chatid（可留空）",
      "welcome_message": "你好！我是会议室预订助手",
      "thinking_message": "⏳ 思考中..."
    },
    {
      "id": "bot-hr",
      "description": "HR 助手",
      "token": "your-secret-token-2",
      "wecom": { ... },
      "dify": { ... }
    }
  ]
}
```

### 字段说明

**service（全局）**

| 字段 | 说明 |
|------|------|
| `notify_port` | 本地 HTTP 通知服务端口，默认 8899 |
| `log_level` | 日志级别：DEBUG / INFO / WARNING |

**bots 数组（每个机器人）**

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 唯一标识，用于日志区分，不能重复 |
| `description` | 否 | 描述，仅作备注 |
| `token` | 是 | **路由认证凭据**，Dify HTTP 节点回调时必须携带，不能重复 |
| `wecom.bot_id` | 是 | 企业微信智能机器人 Bot ID |
| `wecom.secret` | 是 | 企业微信智能机器人 Secret |
| `dify.api_base` | 是 | Dify 服务地址，本机部署默认 `http://127.0.0.1/v1` |
| `dify.api_key` | 是 | 该工作流的 API 密钥，格式 `app-xxx` |
| `dify.input_variable` | 是 | 工作流开始节点的输入变量名，默认 `input` |
| `dify.output_variable` | 是 | 工作流结束节点的输出变量名，默认 `text` |
| `dify.timeout` | 否 | 等待 Dify 响应超时秒数，默认 60 |
| `default_chatid` | 否 | 默认发送目标，Dify HTTP 节点不传 chatid 时使用 |
| `welcome_message` | 否 | 用户进入会话时的欢迎语 |
| `thinking_message` | 否 | 调用 Dify 期间的等待提示 |

### 各配置项获取方式

**bot_id / secret**：企业微信管理后台 → 应用管理 → 智能机器人

**api_key**：Dify → 对应工作流 → 右上角「API 访问」→ 复制密钥（格式 `app-xxx`）

**token**：自行生成一串随机字符串，每个 bot 保持唯一即可，例如：
```bash
python3 -c "import secrets; print(secrets.token_hex(16))"
```

**default_chatid**：启动服务后，在企微中发一条消息，查看日志：
```
[bot-meeting] 收到消息 张三 (chatid=wreVEBEgAAdFURgpJ8RLuU7kZagJklxQ): 你好
```
将 `chatid=` 后面的值填入对应 bot 的 `default_chatid`。

---

## 6. 启动与停止

### Linux / macOS

```bash
chmod +x start.sh
./start.sh start     # 启动
./start.sh stop      # 停止
./start.sh restart   # 重启
./start.sh status    # 查看状态
./start.sh log       # 实时查看日志
```

正常启动后日志示例：

```
============================================================
  企业微信智能机器人 + Dify 多工作流桥接服务
============================================================
  加载机器人数量: 2
    - [bot-meeting] 会议室预订机器人  token=your-sec...
    - [bot-hr]      HR 助手          token=your-sec...
  Notify 端口: 8899
============================================================
[Notify] HTTP 服务已启动，端口 8899
[bot-meeting] WebSocket 已连接
[bot-meeting] 认证成功，开始接收消息
[bot-hr] WebSocket 已连接
[bot-hr] 认证成功，开始接收消息
```

### Windows

```bat
start.bat install    # 首次安装依赖
start.bat start      # 启动
start.bat stop       # 停止
start.bat restart    # 重启
start.bat log        # 查看最近日志
```

---

## 7. Dify 工作流配置要求

### 6.1 开始节点

必须有输入变量，变量名与 config.json 的 `input_variable` 一致（默认 `input`）：

```
变量名：input（类型：文本输入，必填）
```

### 6.2 结束节点（End Node）

输出变量名必须与 `output_variable` 一致（默认 `text`）：

```
输出变量名：text
引用来源：LLM节点 → 字段选 text（不是 message！）
```

> ⚠️ Dify LLM 节点的输出字段名是 `text`，不是 `message`。选错会导致机器人回复 `{}`。

### 6.3 Dify 环境变量（推荐）

在 Dify 工作流的「环境变量」中存储 token，避免硬编码：

```
变量名：bridge_token
值：your-secret-token-1（与 config.json 中该 bot 的 token 一致）
```

HTTP 节点 Body 中使用：
```json
{"token": "{{env.bridge_token}}", "content": "{{#LLM节点ID.text#}}"}
```

### 6.4 DSL 导入方式

修改 DSL 文件（.yml）后需重新导入：Dify → 工作流 → 右上角「...」→「导入 DSL」

---

## 8. Dify HTTP 通知节点配置

当工作流中间步骤需要主动推送消息到企微时，添加 HTTP 节点：

| 字段 | 值 |
|------|----|
| URL | `http://172.18.0.1:8899/notify` |
| Method | POST |
| Headers | `Content-Type:application/json` |
| Body 类型 | Raw Text |
| Body 内容 | `{"token":"{{env.bridge_token}}","content":"{{#LLM节点ID.text#}}"}` |

### Body 格式说明

```json
{
  "token":   "your-secret-token-1",  // 必填，路由到对应机器人
  "content": "要发送的消息内容",       // 必填
  "chatid":  "目标会话ID"             // 可选，留空用 default_chatid
}
```

**兼容企微原生格式（同样支持）：**
```json
{"token": "...", "msgtype": "text", "text": {"content": "消息内容"}}
```

消息以 **Markdown** 格式发送，支持加粗、换行等。

---

## 9. Dify Squid 代理白名单配置

Dify 的 HTTP 节点请求经过内置 squid 代理（SSRF 防护），必须将宿主机 IP 加入白名单。

### 配置文件位置

```
/path/to/dify/docker/ssrf_proxy/squid.conf.template
```

### 需要添加的内容

在 `http_access deny all` **之前**添加：

```
acl notify_host dst 172.18.0.1
acl notify_port port 8899
http_access allow notify_host notify_port
```

> 确认网桥 IP：`docker network inspect docker_default | grep Gateway`

### 使配置生效

```bash
cd /path/to/dify/docker
docker compose restart ssrf_proxy
```

### 验证方式

```bash
docker exec -it docker-ssrf_proxy-1 tail -f /var/log/squid/access.log
# TCP_MISS/200 → 正常
# TCP_DENIED   → 白名单未生效
```

---

## 10. 常见问题排查

### 机器人回复 `{}`

结束节点引用了 LLM 节点的 `.message`，应改为 `.text`，然后重新导入 DSL。

---

### `/notify` 返回 401

`token` 字段与 config.json 中的 token 不匹配。检查：
- Dify 环境变量 `bridge_token` 的值
- config.json 中该 bot 的 `token` 字段

---

### `/notify` 返回 503

对应机器人的 WSClient 未连接。查看日志确认该 bot 是否认证成功。

---

### 某个 bot 启动失败，其他 bot 仍正常

多 bot 并发启动，互不影响。查看日志中 `[bot-xxx]` 的错误信息，通常是 bot_id 或 secret 填写有误。

---

### HTTP 节点报 `Reached maximum retries`

Dify 容器无法访问宿主机 8899 端口，检查 squid 白名单配置。

---

### 修改 config.json 后不生效

config.json 在启动时读取一次，修改后需重启：
```bash
./start.sh restart
```

---

*项目地址：https://github.com/king-ly01/wework-dify-bridge*
