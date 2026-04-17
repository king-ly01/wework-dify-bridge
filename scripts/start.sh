#!/bin/bash
# wework-dify-bridge 服务管理脚本
# 用法：./start.sh [start|stop|restart|status|log]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MAIN="$PROJECT_DIR/core/bridge_server.py"
LOG="$PROJECT_DIR/bridge.log"
PID_FILE="$PROJECT_DIR/bridge.pid"
PYTHON=$(command -v python3 || command -v python)

# ── 颜色 ────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

get_pid() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return
        fi
    fi
    # 从进程列表查找
    pgrep -f "core/bridge_server.py" | head -1
}

do_start() {
    local pid=$(get_pid)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}服务已在运行中（PID: $pid）${NC}"
        return
    fi
    echo -n "正在启动桥接服务..."
    nohup env PYTHONUNBUFFERED=1 "$PYTHON" "$MAIN" >> "$LOG" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    pid=$(get_pid)
    if [ -n "$pid" ]; then
        echo -e " ${GREEN}✅ 启动成功（PID: $pid）${NC}"
        echo "日志：tail -f $LOG"
    else
        echo -e " ${RED}❌ 启动失败，请查看日志：$LOG${NC}"
    fi
}

do_stop() {
    local pid=$(get_pid)
    if [ -z "$pid" ]; then
        echo -e "${YELLOW}服务未运行${NC}"
        return
    fi
    echo -n "正在停止服务（PID: $pid）..."
    kill "$pid" 2>/dev/null
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null
    fi
    rm -f "$PID_FILE"
    echo -e " ${GREEN}✅ 已停止${NC}"
}

do_status() {
    local pid=$(get_pid)
    if [ -n "$pid" ]; then
        echo -e "${GREEN}● 服务运行中（PID: $pid）${NC}"
        echo "  日志文件：$LOG"
        echo "  最近5条日志："
        tail -5 "$LOG" 2>/dev/null | sed 's/^/    /'
    else
        echo -e "${RED}● 服务未运行${NC}"
    fi
}

do_log() {
    echo "实时查看日志（Ctrl+C 退出）："
    tail -f "$LOG"
}

case "${1:-start}" in
    start)   do_start ;;
    stop)    do_stop ;;
    restart) do_stop; sleep 1; do_start ;;
    status)  do_status ;;
    log)     do_log ;;
    *)
        echo "用法：$0 {start|stop|restart|status|log}"
        echo ""
        echo "  start    启动服务"
        echo "  stop     停止服务"
        echo "  restart  重启服务"
        echo "  status   查看运行状态"
        echo "  log      实时查看日志"
        exit 1
        ;;
esac
