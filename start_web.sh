#!/bin/bash

echo "🎵 音频歌词清理工具 - Web版本"
echo "================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ 错误: 未找到Python，请先安装Python"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "✅ 找到Python: $($PYTHON_CMD --version)"

# 安装依赖
echo "📦 检查并安装依赖..."
$PYTHON_CMD -m pip install -r requirements.txt

# 启动Web应用
echo ""
echo "🚀 启动Web服务器..."
echo "📱 请在浏览器中访问: http://localhost:5000"
echo "🛑 按 Ctrl+C 停止服务器"
echo ""

$PYTHON_CMD app.py