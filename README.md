# 🎵 音频歌词清理工具 v2.0

一个智能的音频文件歌词清理工具，自动移除歌词中的信息标头，保留纯净的带时间戳歌词。支持现代化Web界面和强大的命令行两种使用方式。

## 🚀 快速开始

### 🖥️ Windows用户（一键启动）
**双击 `启动Web界面.bat` 文件**
- ✅ 自动检查Python环境
- ✅ 自动安装依赖包
- ✅ 自动启动Web服务
- ✅ 自动打开浏览器

### 🐧 其他系统用户
```bash
python run.py
```
然后在浏览器中打开：http://localhost:5000

### ⚡ 命令行使用（推荐复杂目录）
```bash
# 🎯 交互式模式（新手友好）
python ly.py

# 🔍 预览模式（安全第一）
python ly.py "D:\Music" --dry-run -v

# 📦 备份模式（双重保险）
python ly.py "D:\Music" --backup -v

# 🎵 处理单个文件
python ly.py "song.mp3" --backup

# 🎯 只处理特定格式
python ly.py "D:\Music" --filter-ext .flac,.mp3 -v
```

## 🎯 使用方式选择

### 📱 Web界面（适合简单需求）
**3步完成处理：**
1. **📂 上传文件** - 拖拽或选择音频文件
2. **👀 预览效果** - 查看清理前后对比
3. **💾 下载结果** - 获取处理后的文件

### 💻 命令行（适合复杂目录）
**推荐用于：**
- 🗂️ 复杂的文件夹结构
- 📁 包含图片、说明文件的音乐目录
- 🔄 批量处理大量文件
- 🔒 需要保持完整目录结构

## ✨ 功能特点

### 🧹 歌词清理功能
自动识别并移除以下类型的信息标头：
- 作词、作曲、编曲信息
- 制作人、录音师、混音师信息
- 发行、出品、策划信息
- 其他制作相关信息

### 🎵 文件支持
- **音频格式**：MP3、FLAC、M4A
- **文件大小**：无限制（取决于服务器配置）
- **批量处理**：支持文件夹上传，保持目录结构
- **预览模式**：查看清理效果而不修改文件

### 🌐 现代化界面
- 响应式设计，支持移动设备
- 拖拽上传，操作简便
- 实时预览清理效果
- 批量下载处理结果

## 🔧 命令行选项（全新升级）

```bash
python ly.py [路径] [选项]

🎯 核心选项:
  -v, --verbose      显示详细处理信息
  -d, --dry-run      预览模式，不修改文件
  -b, --backup       创建备份文件（.backup后缀）
  -w, --web          启动Web界面

🎵 高级选项:
  --filter-ext       只处理指定文件类型（如: .mp3,.flac,.m4a）
  --stats            只显示统计信息，不处理文件
  --version          显示版本信息
  -h, --help         显示详细帮助

🔍 交互模式选项:
  1. 🎵 处理单个文件
  2. 📁 批量处理目录  
  3. 🔍 预览模式
  4. 📦 安全模式（自动备份）
  5. 🎯 指定文件类型处理
  6. 🌐 启动Web界面
  7. ❓ 显示帮助
```

## 📁 项目结构

```
├── app.py                 # Flask Web应用
├── ly.py                  # 命令行脚本
├── run.py                 # 启动脚本
├── 启动Web界面.bat        # Windows一键启动
├── requirements.txt       # Python依赖
├── templates/
│   └── index.html        # Web界面模板
├── uploads/              # 上传文件临时目录（自动创建）
└── processed/            # 处理后文件目录（自动创建）
```

## 💡 使用示例

### 🔰 新手推荐流程
```bash
# 1. 启动交互模式（最简单）
python ly.py

# 2. 预览效果（安全第一）
python ly.py "D:\Music" --dry-run -v

# 3. 备份处理（双重保险）
python ly.py "D:\Music" --backup -v
```

### 🚀 高级用法示例
```bash
# 📊 查看目录统计
python ly.py "D:\Music" --stats

# 🎯 只处理FLAC文件
python ly.py "D:\Music" --filter-ext .flac --backup -v

# 🔍 预览特定格式
python ly.py "D:\Music" --filter-ext .mp3,.flac --dry-run

# 📦 安全处理单个文件
python ly.py "song.mp3" --backup -v

# 🌐 启动Web界面
python ly.py --web
```

### 📁 复杂目录处理示例
```bash
# 处理包含图片、说明文件的音乐收藏
python ly.py "D:\Music Collection" --backup --filter-ext .flac -v

# 预览整个音乐库的清理效果
python ly.py "E:\Music Library" --dry-run --verbose

# 只处理MP3，保持其他文件不变
python ly.py "F:\Mixed Media" --filter-ext .mp3 --backup
```

## ⚠️ 注意事项

### 🔒 安全建议
- 💾 **重要文件请先备份**：使用 `--backup` 参数或手动备份
- 🔍 **首次使用先预览**：使用 `--dry-run` 查看效果
- 📁 **复杂目录用命令行**：Web界面适合简单需求

### 💻 系统要求
- 🐍 Python 3.7+ （推荐 3.9+）
- 🌐 首次使用需要网络连接（安装依赖）
- 💾 足够的磁盘空间（备份模式需要额外空间）

### 📂 文件支持
- 🎵 **音频格式**：MP3、FLAC、M4A
- 📁 **目录结构**：完全保持原有结构
- 🖼️ **其他文件**：图片、文档等保持不变

## 🆘 常见问题

### 🚀 启动问题
**启动失败？**
1. 确保已安装Python（从 https://python.org 下载）
2. 以管理员身份运行 `启动Web界面.bat`
3. 或手动运行：`python run.py`
4. 检查是否有杀毒软件阻止

**无法访问网页？**
- 检查地址：http://localhost:5000
- 确保防火墙允许访问
- 尝试：http://127.0.0.1:5000
- 检查端口5000是否被占用

### 📁 文件处理问题
**命令行处理失败？**
```bash
# 检查文件权限
python ly.py "文件路径" --stats

# 使用详细模式查看错误
python ly.py "文件路径" --dry-run -v

# 尝试备份模式
python ly.py "文件路径" --backup -v
```

**Web界面上传失败？**
- 检查文件格式（仅支持MP3、FLAC、M4A）
- 大文件夹建议使用命令行模式
- 确保网络连接稳定
- 尝试单个文件上传测试

**如何只预览而不修改文件？**
```bash
# 命令行预览
python ly.py "路径" --dry-run -v

# 或使用Web界面的预览功能
```

### 🔧 高级问题
**如何恢复备份文件？**
```bash
# 备份文件通常以 .backup 结尾
# 手动重命名即可恢复
mv "song.mp3.backup" "song.mp3"
```

**如何批量处理特定格式？**
```bash
# 只处理FLAC文件
python ly.py "D:\Music" --filter-ext .flac

# 处理多种格式
python ly.py "D:\Music" --filter-ext .mp3,.flac,.m4a
```

## 🔧 技术栈

- **核心**：Python 3.7+ 
- **音频处理**：Mutagen（支持MP3/FLAC/M4A）
- **Web后端**：Flask + Werkzeug
- **Web前端**：Bootstrap 5 + 原生JavaScript
- **命令行**：argparse + 彩色输出

## 🔄 开发说明

### 📝 自定义清理规则
编辑 `lyrics_utils.py` 中的 `header_keywords` 列表：
```python
self.header_keywords = [
    '作词', '作曲', '编曲', '演唱', '制作',
    # 添加你的自定义关键词
    '你的关键词'
]
```

### 🎯 扩展支持格式
在 `lyrics_utils.py` 中添加新格式支持：
```python
self.supported_formats = {'.mp3', '.flac', '.m4a', '.新格式'}
```

### 🔧 调试模式
```bash
# 启用详细日志
python ly.py "路径" -v

# 查看统计信息
python ly.py "路径" --stats

# 测试单个文件
python ly.py "test.mp3" --dry-run -v
```

## 📞 技术支持

### 🔍 问题诊断步骤
1. **检查Python版本**：`python --version`（建议3.7+）
2. **检查依赖安装**：`pip list | grep mutagen`
3. **测试单个文件**：`python ly.py "test.mp3" --dry-run -v`
4. **检查文件权限**：确保有读写权限

### 🐛 报告问题时请提供
- 操作系统版本
- Python版本
- 错误信息截图
- 使用的命令
- 文件格式和大小

## 🎉 更新日志

### v2.0 (最新版本)
- 🆕 **全新命令行界面**：美化界面，emoji图标
- 📦 **备份功能**：自动创建备份文件
- 🎯 **文件类型过滤**：只处理指定格式
- 📊 **统计模式**：快速查看目录信息
- 🔍 **增强预览**：更详细的预览信息
- 🎨 **交互模式升级**：8种操作选项
- 🛡️ **安全性提升**：多重保护机制

### v1.0
- ✅ 基础歌词清理功能
- 🌐 Web界面支持
- 📁 文件夹批量处理

## 💝 贡献

欢迎提交Issue和Pull Request！

### 🤝 如何贡献
1. Fork 本项目
2. 创建功能分支：`git checkout -b feature/新功能`
3. 提交更改：`git commit -m '添加新功能'`
4. 推送分支：`git push origin feature/新功能`
5. 提交Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢所有使用和贡献这个项目的朋友们！

---

💡 **提示**：
- 🔰 **新手**：建议从交互模式开始 `python ly.py`
- 🏆 **进阶**：使用命令行参数提高效率
- 🛡️ **安全**：重要文件请先用 `--dry-run` 预览
- 📦 **备份**：使用 `--backup` 参数双重保险

**首次使用会自动下载安装依赖包，请保持网络连接。安装完成后即可离线使用。**