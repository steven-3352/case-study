#!/bin/bash
# MV 导演助手 · Linux/Mac 一键安装脚本

set -e

echo "🚀 MV 导演助手 · 环境初始化"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION 已安装"

# 创建虚拟环境（可选）
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境 venv/"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
else
    echo "📦 使用已有虚拟环境 venv/"
    source venv/bin/activate
fi

# 安装依赖
echo "📥 安装依赖..."
pip install -r requirements.txt

# 配置 .env
if [ ! -f ".env" ]; then
    echo "📝 复制 .env.example → .env"
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件，填入你的 API Key"
else
    echo "✅ .env 已存在"
fi

# 创建 projects 目录
mkdir -p projects

echo ""
echo "🎉 安装完成！"
echo ""
echo "下一步："
echo "  1. 编辑 .env 文件，填入 API Key"
echo "  2. 激活虚拟环境：source venv/bin/activate"
echo "  3. 开始对话：用 Codex 打开本目录"
echo ""
