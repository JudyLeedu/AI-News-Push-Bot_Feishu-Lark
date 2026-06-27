#!/bin/bash
# ============================================================
# AI 资讯分频推送机器人 - 启动脚本
# ============================================================
set -e

cd "$(dirname "$0")"

# 创建日志目录
mkdir -p logs

# 检查配置文件
if [ ! -f config.yaml ] && [ -z "$FEISHU_APP_ID" ]; then
    echo "❌ 找不到 config.yaml 且未设置相关环境变量，请先配置"
    exit 1
fi

# 检查是否存在 python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 找不到 python3 命令，请先安装 Python 3.12+"
    exit 1
fi

# 自动创建并使用虚拟环境，避免污染全局
if [ ! -d ".venv" ]; then
    echo "📦 正在初始化虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖（不再忽略错误）
pip install -r requirements.txt -q

echo "🚀 启动 AI 资讯分频推送机器人..."
echo "   日报：每天 08:30（北京时间）"
echo "   周报：每周六 08:30（北京时间）"
echo "   月报：每月最后一天 08:30（北京时间）"
echo ""

# 启动
exec python -m src.main scheduler
