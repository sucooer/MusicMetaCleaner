@echo off
chcp 65001 >nul 2>&1
title 音频歌词清理工具

cls
echo.
echo ==========================================
echo          音频歌词清理工具
echo ==========================================
echo.

REM 设置环境变量
set PYTHONIOENCODING=utf-8
set FLASK_ENV=production

REM 检查Python
echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python
    echo 请从 https://www.python.org 下载安装Python
    echo.
    pause
    exit /b 1
)
echo 完成

REM 安装依赖
echo [2/3] 安装依赖包...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet Flask mutagen Werkzeug
echo 完成

REM 启动服务
echo [3/3] 启动Web服务...
echo.
echo ==========================================
echo  服务器正在启动...
echo  
echo  请在浏览器中访问:
echo  http://localhost:5000
echo  
echo  按 Ctrl+C 停止服务器
echo ==========================================
echo.

REM 启动Web应用
python run.py

echo.
pause