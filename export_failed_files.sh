#!/bin/bash

echo ""
echo "🎵 MusicMetaCleaner - 失败文件导出工具"
echo "================================================"
echo ""

python3 export_failed_files.py "$@"

echo ""
echo "按任意键退出..."
read -n 1 