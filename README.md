# WEDBRIDGE

**WEDBRIDGE** - 企业微信 + Dify 智能桥接平台

企业微信智能机器人与 Dify AI 工作流的无缝连接桥梁，支持多机器人、多工作流并行处理，专为高并发场景设计（支持 600+ 机器人）。

---

## 目录

1. [项目简介](#1-项目简介)
2. [系统架构](#2-系统架构)
3. [功能特性](#3-功能特性)
4. [快速开始](#4-快速开始)
5. [详细配置](#5-详细配置)
6. [Dify 配置指南](#6-dify-配置指南)
7. [高并发优化](#7-高并发优化)
8. [API 接口](#8-api-接口)
9. [常见问题](#9-常见问题)
10. [更新日志](#10-更新日志)

---

## 1. 项目简介

WEDBRIDGE 是一个企业微信（WeCom）与 Dify AI 工作流之间的智能桥接平台。它解决了以下问题：

- **多工作流并行**：一个 WeCom 机器人可以同时触发多个 Dify 工作流
- **高并发支持**：支持 600+ 机器人同时在线，Redis 队列保证消息不丢失
- **实时状态监控**：Web 界面实时显示机器人连接状态、消息数量、运行时间
- **独立控制**：每个机器人可独立启用/禁用，互不影响

### 1.1 核心概念

| 概念 | 说明 |
|------|------|
| **WeCom Bot ID** | 企业微信机器人的唯一标识，多个机器人可共享同一个 WeCom Bot ID |
| **机器人 ID** | WEDBRIDGE 内部标识，每个 Dify 工作流对应一个机器人 |
| **主连接** | 实际建立 WebSocket 连接的机器人 |
| **订阅者** | 共享主连接 WebSocket，但使用不同 Dify 配置的机器人 |

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         企业微信用户                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │ WebSocket
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      WEDBRIDGE 平台                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │    Web      │  │    API      │  │   Worker    │  │  Redis  │ │
│  │   (Nginx)   │  │  (FastAPI)  │  │(WebSocket)  │  │ (Queue) │ │
│  │   Port 80   │  │  Port 8899  │  │  Port 8898  │  │ Port 6379││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬────┘ │
│         └─────────────────┴─────────────────┘              │    │
│                           │                                │    │
│                    ┌──────┴──────┐                         │    │
│                    │  Connection │◄────────────────────────┘    │
│                    │    Pool     │   消息队列/状态管理            │
│                    └──────┬──────┘                              │
│                           │ 消息分发                             │
│           ┌───────────────┼───────────────┐                     │
│           ▼               ▼               ▼                     │
│      ┌─────────┐    ┌─────────┐    ┌─────────┐                  │
│      │ Dify    │    │ Dify    │    │ Dify    │                  │
│      │ 工作流A  │    │ 工作流B  │    │ 工作流C  │                  │
│      └────┬────┘    └────┬────┘    └────┬────┘                  │
│           │              │              │                       │
│           └──────────────┼──────────────┘                       │
│                          ▼                                      │
│                 ┌─────────────────┐                             │
│                 │   结果合并发送    │                             │
│                 │    到企业微信     │                             │
│                 └─────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 组件说明

| 组件 | 功能 | 端口 |
|------|------|------|
| **Web** | Vue3 前端界面，机器人管理、状态监控 | 80 |
| **API** | FastAPI 后端，RESTful API、数据库操作 | 8899 |
| **Worker** | WebSocket 连接池，消息收发、Dify 调用 | 8898 |
| **Redis** | 消息队列、状态缓存 | 6379 |
| **PostgreSQL** | 机器人配置、消息记录持久化 | 5432 |

### 2.3 消息流转

1. **用户发送消息** → WeCom 服务器
2. **Worker 接收消息** → 通过 WebSocket 连接
3. **查找关联工作流** → 根据 WeCom Bot ID 找到所有订阅的 Dify 配置
4. **并行触发工作流** → 所有关联的 Dify 工作流同时执行（HTTP 调用）
5. **收集工作流输出** → 等待所有工作流完成（带超时控制）
6. **按序发送回复** → 工作流结果按完成顺序一条条发送给用户（不合并）

---

## 3. 功能特性

### 3.1 核心功能

- ✅ **多机器人管理**：支持 600+ 机器人同时运行
- ✅ **1:N 架构**：一个 WeCom 机器人可同时触发多个 Dify 工作流
- ✅ **实时状态监控**：Web 界面显示连接状态（灰色/蓝色/绿色/红色）
- ✅ **独立启停控制**：每个机器人可独立启用/禁用，立即生效
- ✅ **消息统计**：今日消息数、累计消息数、错误数实时统计
- ✅ **高可用设计**：Redis 持久化队列，消息不丢失
- ✅ **连接池管理**：HTTP 连接池、熔断器、自动重连

### 3.2 状态指示器

| 颜色 | 状态 | 说明 |
|------|------|------|
| 🔘 灰色 | 未启动 | 机器人已禁用 |
| 🔵 蓝色闪烁 | 正在连接 | 已启用，正在建立连接 |
| 🟢 绿色 | 连接成功 | 已启用，WebSocket 连接正常 |
| 🔴 红色 | 连接失败 | 已启用，但认证失败或连接异常 |

---

## 4. 快速开始

### 4.1 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ 内存（高并发场景建议 8GB+）

### 4.2 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/king-ly01/wedbridge.git
cd wedbridge/docker

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，修改必要配置（见下方 4.2.1）

# 3. 拉取预构建镜像
docker compose pull

# 4. 启动服务
docker compose up -d

# 5. 查看状态
docker compose ps

# 6. 查看日志
docker compose logs -f
```

#### 4.2.1 环境变量配置说明

编辑 `docker/.env` 文件：

```bash
# ==================== 服务端口 ====================
API_PORT=8899          # API 服务端口
WEB_PORT=80            # Web 前端端口
DB_PORT=5432           # PostgreSQL 端口（如与其他服务冲突请修改）

# ==================== 数据库配置 ====================
DATABASE_URL=postgresql://wedbridge:wedbridge@db:5432/wedbridge
REDIS_URL=redis://redis:6379/0

# ==================== 安全密钥 ====================
# 生产环境请修改此密钥
SECRET_KEY=your-secret-key-change-in-production

# ==================== Dify 网络集成 ====================
# 如果服务器上运行了 Dify，需要配置 Dify 的 Docker 网络名称
# 查看方法：docker network ls | grep dify
# 常见值：docker_default / dify_default
DIFY_NETWORK=docker_default
```

> **重要**：`DIFY_NETWORK` 必须与 Dify 实际使用的 Docker 网络名一致，否则启动会报错。
> 查看方法：`docker network ls | grep dify`

#### 4.2.2 前端构建（首次部署需要）

Web 前端通过 Nginx 挂载静态文件，首次部署需要构建：

```bash
# 安装 Node.js 18+（如未安装）
cd wedbridge/web
npm install
npm run build     # 生成 dist/ 目录
```

构建完成后 `docker compose up -d` 即可，Nginx 会自动挂载 `web/dist` 目录。

### 4.3 访问系统

- **Web 界面**：http://localhost
- **默认账户**：`admin` / `admin`
- **API 文档**：http://localhost/api/docs

### 4.4 常用命令

```bash
# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看特定服务日志
docker compose logs -f worker
docker compose logs -f api

# 更新到最新版本
cd wedbridge && git pull
cd docker
docker compose pull
docker compose up -d
```

### 4.5 镜像说明

| 镜像 | 来源 | 说明 |
|------|------|------|
| `ghcr.io/king-ly01/wedbridge-api` | GHCR（公开） | API 服务，FastAPI 后端 |
| `ghcr.io/king-ly01/wedbridge-worker` | GHCR（公开） | Worker 服务，WebSocket 连接池 |
| `nginx:alpine` | Docker Hub | Web 前端，挂载本地 dist 目录 |
| `postgres:15-alpine` | Docker Hub | 数据库 |
| `redis:7-alpine` | Docker Hub | 消息队列 |

> API 和 Worker 镜像托管在 GitHub Container Registry（ghcr.io），已设为 Public，无需登录即可拉取。

---

## 5. 详细配置

### 5.1 环境变量配置（.env）

```bash
# 数据库配置
DATABASE_URL=postgresql://wedbridge:wedbridge@db:5432/wedbridge
DB_PORT=5432

# Redis 配置
REDIS_URL=redis://redis:6379/0

# API 服务配置
API_PORT=8899
SECRET_KEY=your-secret-key-here-change-in-production

# Web 服务端口
WEB_PORT=80

# Worker 配置（可选）
WORKER_SYNC_INTERVAL=5
```

### 5.2 机器人配置

通过 Web 界面或 API 配置机器人：

| 字段 | 必填 | 说明 |
|------|------|------|
| **机器人 ID** | 是 | 唯一标识，只能包含字母、数字、下划线 |
| **描述** | 否 | 机器人用途说明 |
| **WeCom Bot ID** | 是 | 企业微信机器人 ID |
| **WeCom Secret** | 是 | 企业微信机器人 Secret |
| **Dify API Base** | 是 | Dify API 地址，如 `http://your-dify:5001/v1` |
| **Dify API Key** | 是 | Dify 工作流 API Key |
| **Dify Workflow ID** | 否 | 工作流 ID（如使用特定工作流）|
| **输入变量** | 否 | 默认为 `input` |
| **输出变量** | 否 | 默认为 `text` |
| **超时时间** | 否 | 工作流执行超时，默认 60 秒 |

### 5.3 1:N 配置示例

**场景**：一个 WeCom 机器人触发多个 Dify 工作流

**配置步骤**：

1. 创建第一个机器人（主连接）：
   - 机器人 ID: `bot-main`
   - WeCom Bot ID: `aibpKUnDe2xfKlubp5Wt1LMpKl7se0fJvTd`
   - Dify API Key: `workflow-a-key`

2. 创建第二个机器人（订阅者）：
   - 机器人 ID: `bot-sub-1`
   - WeCom Bot ID: `aibpKUnDe2xfKlubp5Wt1LMpKl7se0fJvTd`（相同）
   - Dify API Key: `workflow-b-key`

3. 两个机器人共享同一个 WebSocket 连接，但触发不同的工作流

---

## 6. Dify 配置指南

### 6.1 工作流开始节点

必须有输入变量：
- **变量名**：`input`（与 WEDBRIDGE 配置中的 `input_variable` 一致）
- **类型**：文本输入
- **必填**：是

### 6.2 工作流结束节点

输出变量名：
- **变量名**：`text`（与 WEDBRIDGE 配置中的 `output_variable` 一致）
- **引用来源**：LLM 节点的 `text` 字段

### 6.3 HTTP 节点配置（关键）

当工作流需要主动发送消息到企微时，添加 HTTP 节点：

| 配置项 | 值 |
|--------|-----|
| **URL** | `http://your-wedbridge/notify?token=ROBOT_TOKEN` |
| **Method** | POST |
| **Headers** | `Content-Type: application/json` |
| **Body 类型** | Raw Text |
| **Body 内容** | `{"content": "{{#llm.text#}}"}` |

**获取 Token**：
- 在 WEDBRIDGE Web 界面，点击机器人「详情」
- 复制「回调 URL」中的 token 参数

### 6.4 关闭 SSRF 代理（必须）

Dify 默认开启 SSRF 代理保护，会拦截 HTTP 节点对内网地址的请求。如果 Dify 和 WEDBRIDGE 在同一服务器，**必须关闭 SSRF 代理**，否则 Dify 工作流无法回调 WEDBRIDGE。

#### 方法一：注释 SSRF 代理配置（推荐）

编辑 Dify 的 `.env` 文件：

```bash
cd /path/to/dify/docker
vim .env
```

找到以下行并**注释掉**：

```bash
# 注释掉这两行，关闭 SSRF 代理
#HTTP_PROXY=http://ssrf_proxy:3128
#HTTPS_PROXY=http://ssrf_proxy:3128

# 同时注释掉 Sandbox 的代理配置
#SANDBOX_HTTP_PROXY=http://ssrf_proxy:3128
#SANDBOX_HTTPS_PROXY=http://ssrf_proxy:3128
```

然后重启 Dify：

```bash
cd /path/to/dify/docker
docker compose down
docker compose up -d
```

#### 方法二：配置 SSRF 白名单

如果不想完全关闭 SSRF 代理，可以将 WEDBRIDGE 的 IP 加入白名单：

**步骤 1：查看 WEDBRIDGE 容器 IP**

```bash
docker inspect wedbridge-api | grep IPAddress
```

**步骤 2：编辑 Squid 配置**

```bash
vim /path/to/dify/docker/ssrf_proxy/squid.conf.template
```

在 `http_access deny all` **之前**添加：

```conf
# WEDBRIDGE 服务（根据实际 IP 修改）
acl wedbridge_net dst 172.16.0.0/12
http_access allow wedbridge_net
```

**步骤 3：重启 SSRF Proxy**

```bash
cd /path/to/dify/docker
docker compose restart ssrf_proxy
```

**步骤 4：验证**

```bash
# 查看 Squid 日志
docker exec dify-ssrf_proxy-1 tail -f /var/log/squid/access.log
# 正常：TCP_MISS/200
# 被拦截：TCP_DENIED
```

#### 验证 SSRF 是否已关闭

在 Dify 工作流中添加一个 HTTP 节点，请求 `http://wedbridge-api:8899/api/health`。如果返回成功，说明 SSRF 配置正确。

---

## 7. 高并发优化

### 7.1 系统调优

**Linux 系统参数**：

```bash
# 编辑 /etc/sysctl.conf
fs.file-max = 100000
net.ipv4.tcp_max_syn_backlog = 65536
net.core.somaxconn = 65535
net.ipv4.ip_local_port_range = 1024 65535

# 应用配置
sysctl -p
```

**Docker 资源限制**：

```yaml
# docker-compose.yml 中添加
services:
  worker:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
```

### 7.2 连接池配置

Worker 自动管理以下连接池：

| 连接池 | 默认大小 | 说明 |
|--------|----------|------|
| WebSocket 连接 | 无限制 | 每个 WeCom Bot ID 一个连接 |
| HTTP 连接 | 100 | 连接 Dify API |
| Redis 连接 | 50 | 消息队列操作 |

### 7.3 监控指标

Worker 提供 `/worker/stats` 接口返回实时指标：

```json
{
  "total_bots": 600,
  "connected": 580,
  "authenticated": 580,
  "total_messages": 12500,
  "queue_stats": {
    "total_queue_depth": 120,
    "overloaded_bots": 0
  }
}
```

---

## 8. API 接口

### 8.1 机器人管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/bots` | GET | 获取机器人列表 |
| `/api/bots` | POST | 创建机器人 |
| `/api/bots/{id}` | PUT | 更新机器人 |
| `/api/bots/{id}` | DELETE | 删除机器人 |
| `/api/bots/{id}/start` | POST | 启动机器人 |
| `/api/bots/{id}/stop` | POST | 停止机器人 |

### 8.2 Worker 状态

| 接口 | 方法 | 说明 |
|------|------|------|
| `/worker/stats` | GET | 获取所有机器人状态 |
| `/worker/sync` | POST | 强制同步机器人配置 |

### 8.3 消息回调

| 接口 | 方法 | 说明 |
|------|------|------|
| `/notify?token=xxx` | POST | Dify 工作流回调发送消息 |

---

## 9. 常见问题

### 9.1 状态显示"正在连接"但已连接成功

**原因**：Worker 的 `/stats` 接口只返回主连接，订阅者不显示。

**解决**：已修复，更新到最新版本。

### 9.2 HTTP 节点报错 "Reached maximum retries"

**原因**：
1. WEDBRIDGE 未运行
2. SSRF 代理未配置白名单
3. 防火墙阻挡

**解决**：
1. 检查 `docker compose ps`
2. 配置 Squid 白名单（见 6.4）
3. 检查防火墙规则

### 9.3 消息丢失

**原因**：Redis 未持久化或 Worker 重启。

**解决**：
1. 确保 Redis 配置正确
2. 检查 Worker 日志：`docker compose logs -f worker`
3. 开启 Redis 持久化

### 9.4 多个工作流只触发了一个

**原因**：
1. 部分机器人被禁用
2. Dify API Key 无效

**解决**：
1. 检查机器人启用状态
2. 在 Dify 重新发布工作流获取新 API Key

### 9.5 机器人回复 `{}` 或空消息

**原因**：结束节点引用了错误的字段。

**解决**：结束节点应引用 LLM 节点的 `text` 字段。

---

## 10. 更新日志

### v2.0.0 (2026-04-19)

- ✅ **全新架构**：API + Worker 分离，支持高并发
- ✅ **Web 界面**：Vue3 + Element Plus，实时状态监控
- ✅ **Redis 队列**：消息持久化，不丢失
- ✅ **连接池优化**：HTTP 连接池、熔断器
- ✅ **1:N 架构完善**：支持 600+ 机器人共享连接
- ✅ **今日消息统计**：按天统计消息数
- ✅ **强制同步 API**：启停机器人立即生效

### v1.2.0 (2026-04-18)

- ✅ 添加 Docker 支持
- ✅ 支持通过 Docker Compose 一键部署
- ✅ 添加健康检查端点

### v1.1.0 (2026-04-18)

- ✅ 支持一个 WeCom Bot 触发多个 Dify 工作流
- ✅ 添加机器人启用/禁用控制
- ✅ 完善 CLI 菜单

### v1.0.0 (2026-04-17)

- ✅ 初始版本
- ✅ 支持多机器人管理
- ✅ 支持 Dify HTTP 回调

---

## 许可证

MIT License

## 项目地址

https://github.com/king-ly01/wedbridge

## 技术支持

如有问题，请提交 Issue 或联系技术支持。
