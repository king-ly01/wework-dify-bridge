#!/bin/bash
# wework-dify-bridge 一键安装脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="wework-dify-bridge"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PYTHON=$(command -v python3 || command -v python)

echo "========================================"
echo "  wework-dify-bridge 安装程序"
echo "========================================"
echo ""

# ── 1. 检查 Python ──────────────────────────
echo "[1/5] 检查 Python 环境..."
if [ -z "$PYTHON" ]; then
    echo "  ❌ 未找到 Python3，请先安装: sudo apt install python3"
    exit 1
fi
PY_VER=$($PYTHON --version 2>&1)
echo "  ✅ $PY_VER"

# ── 2. 安装依赖 ──────────────────────────────
echo "[2/5] 安装 Python 依赖..."
$PYTHON -m pip install -q --break-system-packages -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null \
    || $PYTHON -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
echo "  ✅ 依赖安装完成"

# ── 3. 初始化配置文件 ────────────────────────
echo "[3/5] 初始化配置文件..."
if [ ! -f "$SCRIPT_DIR/config.json" ]; then
    cp "$SCRIPT_DIR/config.example.json" "$SCRIPT_DIR/config.json"
    echo "  ✅ 已生成 config.json（请编辑填入真实配置）"
else
    echo "  ℹ️  config.json 已存在，跳过"
fi

# ── 4. 安装 systemd 服务（可选） ─────────────
echo "[4/5] 安装 systemd 开机自启服务..."
if command -v systemctl &>/dev/null && [ "$EUID" -eq 0 ]; then
    EXEC_USER=${SUDO_USER:-$(whoami)}
    EXEC_PATH="$SCRIPT_DIR/wework_smart_bot_final.py"
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=WeWork Dify Bridge Service
After=network.target

[Service]
Type=simple
User=${EXEC_USER}
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${PYTHON} ${EXEC_PATH}
Restart=always
RestartSec=5
StandardOutput=append:${SCRIPT_DIR}/bridge.log
StandardError=append:${SCRIPT_DIR}/bridge.log

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    echo "  ✅ systemd 服务已安装并设为开机自启"
    echo "     启动：sudo systemctl start $SERVICE_NAME"
    echo "     查看：sudo systemctl status $SERVICE_NAME"
else
    if [ "$EUID" -ne 0 ]; then
        echo "  ℹ️  非 root 运行，跳过 systemd 安装（如需自启动请用 sudo 重新运行）"
    else
        echo "  ℹ️  systemd 不可用，跳过"
    fi
fi

# ── 5. 完成 ──────────────────────────────────
echo "[5/5] 安装完成！"
echo ""
echo "========================================"
echo "  下一步操作："
echo "========================================"
echo ""
echo "  1. 编辑配置文件："
echo "     nano $SCRIPT_DIR/config.json"
echo ""
echo "  2. 启动服务："
echo "     $SCRIPT_DIR/start.sh start"
echo ""
echo "  3. 查看日志："
echo "     tail -f $SCRIPT_DIR/bridge.log"
echo ""
echo "  详细说明请查看 README.md"
echo "========================================"
