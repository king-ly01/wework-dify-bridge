# WEDBRIDGE

**WEDBRIDGE** - 企业微信 + Dify 智能桥接平台

企业微信智能机器人与 Dify AI 工作流的无缝连接桥梁，支持多机器人、多工作流并行处理。

支持一个 WeCom 机器人同时触发多个 Dify 工作流，实现工作流并行处理和结果合并。

---

## 目录

1. [架构说明](#1-架构说明)
2. [功能特性](#2-功能特性)
3. [安装部署](#3-安装部署)
4. [CLI 命令](#4-cli-命令)
5. [配置说明](#5-配置说明)
6. [Dify 配置要求](#6-dify-配置要求)
7. [Squid 代理配置](#7-squid-代理配置)
8. [常见问题](#8-常见问题)
9. [更新日志](#9-更新日志)

---

## 1. 架构说明

### 1.1 系统架构

```
┌───────────────────────────────────────────────────────────┐
│                      企业微信用户                           │
└──────────────────────┬────────────────────────────────────┘
                       │ WebSocket
                       ▼
┌───────────────────────────────────────────────────────────┐
│                   wework-dify-bridge                      │
│  ┌────────────────────────────────────────────────────┐   │
│  │  WeCom Bot (aibpKUnDe2xfKlubp5Wt1LMpKl7se0fJvTd)   │   │
│  │  WebSocket 连接（唯一）                              │   │
│  └────────────────────┬───────────────────────────────┘   │
│                       │ 消息分发                           │
│           ┌───────────┼───────────┐                       │
│           ▼           ▼           ▼                       │
│      ┌─────────┐ ┌─────────┐ ┌─────────┐                  │
│      │ Dify    │ │ Dify    │ │ Dify    │                  │
│      │ 工作流A  │ │ 工作流B  │ │ 工作流C  │                  │
│      └────┬────┘ └────┬────┘ └────┬────┘                  │
│           │           │           │                       │
│           └───────────┼───────────┘                       │
│                       ▼                                   │
│              ┌─────────────────┐                          │
│              │   结果合并发送    │             
│              │    到企业微信     │                          │
│              └─────────────────┘                          │
└───────────────────────────────────────────────────────────┘
```

### 1.2 消息流转

1. **用户发送消息** → WeCom Bot
2. **Bridge 接收消息** → 通过 WebSocket
3. **并行触发工作流** → 所有关联的 Dify 工作流同时执行
4. **收集工作流输出** → 等待所有工作流完成
5. **合并发送回复** → 将多个工作流结果合并后发送给用户

---

## 2. 功能特性

- ✅ **多机器人管理**：支持多个 WeCom 机器人同时运行
- ✅ **多工作流并行**：一个机器人可同时触发多个 Dify 工作流
- ✅ **工作流启停控制**：可单独启用/禁用某个工作流
- ✅ **自动 IP 检测**：自动获取本机 IP 生成回调 URL
- ✅ **进程守护**：支持后台运行，终端关闭不退出
- ✅ **防重复启动**：自动检测并防止重复启动
- ✅ **智能重启**：自动停止旧进程，启动新进程
- ✅ **健康检查**：HTTP 健康检查端点
- ✅ **日志管理**：支持查看和实时跟踪日志

---

## 3. 安装部署

### 3.1 环境要求

- Python 3.8+
- pip
- Linux/macOS/Windows

### 3.2 安装步骤

```bash
# 1. 克隆项目
cd /home/linyang/wework-dify-bridge

# 2. 安装依赖
pip install -e . --break-system-packages

# 3. 验证安装
bridge --help
```

### 3.3 启动服务

```bash
# 启动
wedbridge start
# 或简写
wb start

# 查看状态
wedbridge status

# 查看日志
wedbridge logs
wedbridge logs -f  # 实时跟踪

# 重启
wedbridge restart

# 停止
wedbridge stop
```

---

## 4. CLI 命令

### 4.1 服务管理

| 命令 | 说明 |
|------|------|
| `bridge start` | 启动服务 |
| `bridge stop` | 停止服务 |
| `bridge restart` | 重启服务（自动防重复）|
| `bridge status` | 查看服务状态 |
| `bridge logs [行数]` | 查看日志 |
| `bridge logs -f` | 实时跟踪日志 |

### 4.2 机器人管理

```bash
# 进入配置菜单
wedbridge config
# 或
wb config
```

菜单选项：
1. **新增机器人连接** - 添加新的机器人配置
2. **修改机器人连接** - 修改现有机器人配置
3. **管控机器人连接** - 启用/禁用机器人
4. **查询机器人连接** - 查看机器人详情和 URL
5. **删除机器人连接** - 删除机器人

### 4.3 查看机器人

```bash
# 查看所有机器人
wedbridge id
# 或
wb id

# 查看指定机器人
wedbridge id <机器人ID>
```

---

## 5. 配置说明

### 5.1 配置文件位置

```
/home/linyang/wework-dify-bridge/config/config.json
```

### 5.2 配置示例

```json
{
  "service": {
    "notify_port": 8899,
    "log_level": "INFO"
  },
  "bots": [
    {
      "id": "bot-meeting",
      "enabled": true,
      "description": "机器人",
      "token": "meeting-bridge-token-2024",
      "wecom": {
        "bot_id": "",
        "secret": ""
      },
      "dify": {
        "api_base": "",
        "api_key": "",
        "input_variable": "input",
        "output_variable": "text",
        "timeout": 60
      },
      "default_chatid": "w ",
      "welcome_message": "你好！我是会议室预订机器人",
      "thinking_message": "⏳ 思考中...",
      "owner": "admin"
    }
  ]
}
```

### 5.3 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 机器人唯一标识 |
| `enabled` | 否 | 是否启用（默认 true）|
| `token` | 是 | Dify HTTP 回调认证令牌 |
| `wecom.bot_id` | 是 | 企业微信机器人 ID |
| `wecom.secret` | 是 | 企业微信机器人 Secret |
| `dify.api_key` | 是 | Dify 工作流 API Key |
| `default_chatid` | 否 | 默认会话 ID |

---

## 6. Dify 配置要求

### 6.1 工作流开始节点

必须有输入变量：
- **变量名**：`input`（与 config.json 中的 `input_variable` 一致）
- **类型**：文本输入
- **必填**：是

### 6.2 工作流结束节点

输出变量名：
- **变量名**：`text`（与 config.json 中的 `output_variable` 一致）
- **引用来源**：LLM 节点的 `text` 字段

### 6.3 HTTP 节点配置（关键）

当工作流需要主动发送消息到企微时，添加 HTTP 节点：

| 配置项 | 值 |
|--------|-----|
| **URL** | `http://192.168.1.9:8899/notify?token=YOUR_TOKEN` |
| **Method** | POST |
| **Headers** | `Content-Type: application/json` |
| **Body 类型** | Raw Text |
| **Body 内容** | `{"content": "{{#LLM节点ID.text#}}"}` |

**注意**：
- `192.168.1.9` 是 Bridge 所在机器的 IP，会自动检测
- `YOUR_TOKEN` 是对应机器人的 token
- 可通过 `bridge config` → `查询机器人连接` 查看完整 URL

### 6.4 多个工作流配置

同一个 WeCom Bot 可以配置多个 Dify 工作流：

1. 在 Bridge 中添加多个机器人配置
2. 所有机器人使用相同的 `wecom.bot_id` 和 `wecom.secret`
3. 每个机器人使用不同的 `dify.api_key`
4. 在 Dify 每个工作流的 HTTP 节点中使用对应的 token

**效果**：用户发送一条消息，会同时触发所有工作流，结果合并后返回。

---

## 7. Squid 代理配置

### 7.1 问题说明

Dify 的 HTTP 节点请求经过内置 Squid 代理（SSRF 防护），必须将 Bridge 所在 IP 加入白名单。

### 7.2 配置步骤

**1. 找到配置文件**

```bash
/path/to/dify/docker/ssrf_proxy/squid.conf.template
```

**2. 添加白名单**

在 `http_access deny all` **之前**添加：

```conf
# Bridge 所在机器 IP（根据实际情况修改）
acl notify_host dst 192.168.1.9
acl notify_port port 8899
http_access allow notify_host notify_port
```

**3. 重启 SSRF Proxy**

```bash
cd /path/to/dify/docker
docker compose restart ssrf_proxy
```

**4. 验证配置**

```bash
# 查看 Squid 访问日志
docker exec dify-ssrf_proxy-1 tail -f /var/log/squid/access.log

# 正常应显示：TCP_MISS/200
# 失败显示：TCP_DENIED
```

---

## 8. 常见问题

### 8.1 HTTP 节点报错 "Reached maximum retries"

**原因**：Dify 无法连接到 Bridge

**解决**：
1. 检查 Bridge 是否运行：`bridge status`
2. 检查 Squid 白名单配置
3. 检查防火墙是否放行 8899 端口

### 8.2 机器人回复 `{}`

**原因**：结束节点引用了错误的字段

**解决**：结束节点应引用 LLM 节点的 `text` 字段，不是 `message`

### 8.3 修改配置后不生效

**原因**：配置只在启动时读取

**解决**：执行 `bridge restart` 重启服务

### 8.4 同一个 Bot 的多个工作流没有都触发

**原因**：部分工作流被禁用

**解决**：使用 `bridge config` → `管控机器人连接` 检查启用状态

### 8.5 终端关闭后 Bridge 停止

**原因**：未使用后台模式

**解决**：使用 `bridge start` 启动（已内置 SIGHUP 忽略）

---

## 9. 更新日志

### v1.1.0 (2026-04-18)

- ✅ 支持一个 WeCom Bot 触发多个 Dify 工作流
- ✅ 添加机器人启用/禁用控制
- ✅ 添加 `enabled` 字段到配置
- ✅ 修复 'int' object has no attribute 'get' 错误
- ✅ 添加 SIGHUP 信号处理，支持后台运行
- ✅ 完善 PID 文件管理，防止重复启动
- ✅ 优化 CLI 菜单，添加"管控"功能

### v1.0.0 (2026-04-17)

- ✅ 初始版本
- ✅ 支持多机器人管理
- ✅ 支持 Dify HTTP 回调
- ✅ CLI 配置工具
- ✅ 自动 IP 检测

---

## 许可证

MIT License

## 项目地址

https://github.com/king-ly01/wedbridge
