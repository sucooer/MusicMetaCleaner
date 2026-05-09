#!/usr/bin/env python3
"""
音频歌词清理工具 - Web版本启动脚本
"""

import sys
import os
import subprocess

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import flask
        import mutagen
        import werkzeug
        print("✓ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        return False

def install_dependencies():
    """安装依赖"""
    print("正在安装依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ 依赖安装完成")
        return True
    except subprocess.CalledProcessError:
        print("✗ 依赖安装失败")
        return False

def main():
    print("=" * 60)
    print("🎵 音频歌词清理工具 - Web版本")
    print("=" * 60)
    print()
    
    # 检查依赖
    if not check_dependencies():
        print("是否要自动安装依赖? (y/n): ", end="")
        if input().lower() in ['y', 'yes', '是']:
            if not install_dependencies():
                print("请手动安装依赖: pip install -r requirements.txt")
                return
        else:
            print("请手动安装依赖: pip install -r requirements.txt")
            return
    
    print()
    print("🚀 启动Web服务器...")
    print("📱 本机访问: http://localhost:5000")
    print("🌐 局域网/服务器访问: http://<服务器IP>:5000")
    print("🛑 按 Ctrl+C 停止服务器")
    print()
    
    # 启动Flask应用
    try:
        from app import app
        # 监听所有网卡，允许通过服务器IP访问
        app.run(
            debug=False, 
            host='0.0.0.0', 
            port=5000, 
            threaded=True,
            use_reloader=False,
            processes=1
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("可能的解决方案:")
        print("1. 确保端口5000未被占用")
        print("2. 尝试以管理员身份运行")
        print("3. 检查防火墙设置")

if __name__ == "__main__":
    main()
