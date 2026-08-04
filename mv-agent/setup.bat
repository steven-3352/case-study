@echo off
REM MV 导演助手 · Windows 一键安装脚本

echo 🚀 MV 导演助手 · 环境初始化
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% 已安装

REM 创建虚拟环境（可选）
if not exist "venv\" (
    echo 📦 创建虚拟环境 venv\
    python -m venv venv
    call venv\Scripts\activate
    pip install --upgrade pip
) else (
    echo 📦 使用已有虚拟环境 venv\
    call venv\Scripts\activate
)

REM 安装依赖
echo 📥 安装依赖...
pip install -r requirements.txt

REM 配置 .env
if not exist ".env" (
    echo 📝 复制 .env.example -^> .env
    copy .env.example .env
    echo ⚠️  请编辑 .env 文件，填入你的 API Key
) else (
    echo ✅ .env 已存在
)

REM 创建 projects 目录
if not exist "projects\" mkdir projects

echo.
echo 🎉 安装完成！
echo.
echo 下一步：
echo   1. 编辑 .env 文件，填入 API Key
echo   2. 激活虚拟环境：venv\Scripts\activate
echo   3. 开始对话：用 Codex 打开本目录
echo.
pause
