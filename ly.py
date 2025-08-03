import os
import sys
import argparse
from pathlib import Path
from lyrics_utils import LyricsProcessor
from datetime import datetime

# 创建歌词处理器实例
processor = LyricsProcessor()

def export_failed_files_to_txt(error_files, output_path="failed_files.txt"):
    """
    将失败文件列表导出到txt文件
    
    Args:
        error_files (list): 失败文件列表
        output_path (str): 输出文件路径
        
    Returns:
        bool: 导出是否成功
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("MusicMetaCleaner - 失败文件列表\n")
            f.write("=" * 50 + "\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"失败文件总数: {len(error_files)}\n")
            f.write("=" * 50 + "\n\n")
            
            for i, error_file in enumerate(error_files, 1):
                f.write(f"{i}. {error_file}\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("导出完成\n")
        
        print(f"✅ 失败文件已导出到: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ 导出失败文件时出错: {e}")
        return False

def batch_process_folder(folder_path, verbose=False, dry_run=False, backup=False, filter_ext=None):
    """批量处理文件夹中的所有音频文件"""
    processed_count = 0
    total_removed = 0
    total_files = 0
    skipped_files = 0
    error_files = []
    
    print(f"{'🔍 预览' if dry_run else '🎵 处理'}文件夹: {folder_path}")
    if backup and not dry_run:
        print("📦 备份模式已启用")
    if filter_ext:
        print(f"📁 只处理文件类型: {', '.join(filter_ext)}")
    print("-" * 60)
    
    for root, dirs, files in os.walk(folder_path):
        # 显示当前处理的文件夹
        relative_path = os.path.relpath(root, folder_path)
        if relative_path != ".":
            if verbose:
                print(f"\n📂 处理文件夹: {relative_path}")
        
        for file in files:
            if processor.is_audio_file(file):
                # 如果指定了文件类型过滤
                if filter_ext:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext not in filter_ext:
                        skipped_files += 1
                        continue
                
                file_path = os.path.join(root, file)
                total_files += 1
                
                try:
                    success, removed_lines = processor.process_audio_file(file_path, verbose, dry_run, backup)
                    if success:
                        processed_count += 1
                        total_removed += removed_lines
                        if not verbose and not dry_run:
                            print(f"✅ {os.path.relpath(file_path, folder_path)}")
                    else:
                        error_files.append(file_path)
                except Exception as e:
                    error_files.append(f"{file_path}: {str(e)}")
                    if verbose:
                        print(f"❌ 处理失败: {file_path} - {str(e)}")
    
    # 显示详细统计
    print("\n" + "="*60)
    print(f"📊 {'预览' if dry_run else '处理'}统计:")
    print(f"   🎵 音频文件总数: {total_files}")
    print(f"   ✅ {'预览' if dry_run else '处理'}成功: {processed_count}")
    if skipped_files > 0:
        print(f"   ⏭️  跳过文件: {skipped_files}")
    if error_files:
        print(f"   ❌ 失败文件: {len(error_files)}")
    print(f"   🧹 总移除行数: {total_removed}")
    
    if error_files and verbose:
        print(f"\n❌ 失败文件列表:")
        for error_file in error_files[:10]:  # 只显示前10个
            print(f"   - {error_file}")
        if len(error_files) > 10:
            print(f"   ... 还有 {len(error_files) - 10} 个文件")
    
    # 如果有失败文件，自动导出到txt文件
    if error_files:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"failed_files_{timestamp}.txt"
        export_failed_files_to_txt(error_files, output_filename)
    
    return processed_count, total_removed, error_files

def interactive_mode():
    """交互式命令行界面"""
    print("🎵 歌词清理工具 - 交互模式")
    print("="*60)
    print("此工具将删除歌词信息标头，保留带时间戳的纯歌词")
    print("💡 建议：复杂目录结构请先使用预览模式确认效果")
    
    while True:
        print("\n🎯 选择操作:")
        print("1. 🎵 处理单个文件")
        print("2. 📁 批量处理目录")
        print("3. 🔍 预览模式（不修改文件）")
        print("4. 📦 安全模式（自动备份）")
        print("5. 🎯 指定文件类型处理")
        print("6. 🌐 启动Web界面")
        print("7. ❓ 显示帮助")
        print("8. 🚪 退出")
        
        choice = input("\n请输入选择 (1-8): ").strip()
        
        if choice == "1":
            file_path = input("📂 请输入音频文件路径: ").strip().strip('"')
            if os.path.isfile(file_path):
                verbose = input("📋 是否显示详细信息? (y/n): ").lower() in ['y', 'yes', '是']
                backup = input("📦 是否创建备份? (y/n): ").lower() in ['y', 'yes', '是']
                processor.process_audio_file(file_path, verbose=verbose, backup=backup)
            else:
                print("❌ 文件不存在!")
        
        elif choice == "2":
            folder_path = input("📂 请输入音频文件夹路径: ").strip().strip('"')
            if os.path.isdir(folder_path):
                verbose = input("📋 是否显示详细信息? (y/n): ").lower() in ['y', 'yes', '是']
                backup = input("📦 是否创建备份? (y/n): ").lower() in ['y', 'yes', '是']
                processed, removed, errors = batch_process_folder(folder_path, verbose=verbose, backup=backup)
                if errors:
                    print(f"\n⚠️  有 {len(errors)} 个文件处理失败，建议检查文件权限或格式")
            else:
                print("❌ 目录不存在!")
        
        elif choice == "3":
            path = input("📂 请输入文件或文件夹路径: ").strip().strip('"')
            if os.path.isfile(path):
                processor.process_audio_file(path, verbose=True, dry_run=True)
            elif os.path.isdir(path):
                processed, removed, errors = batch_process_folder(path, verbose=True, dry_run=True)
                print(f"\n💡 预览完成！如果效果满意，可以去掉 --dry-run 参数正式处理")
            else:
                print("❌ 路径不存在!")
        
        elif choice == "4":
            path = input("📂 请输入文件或文件夹路径: ").strip().strip('"')
            if os.path.isfile(path):
                processor.process_audio_file(path, verbose=True, backup=True)
            elif os.path.isdir(path):
                processed, removed, errors = batch_process_folder(path, verbose=True, backup=True)
                print(f"\n📦 备份文件保存在原文件同目录下，文件名后缀为 .backup")
            else:
                print("❌ 路径不存在!")
        
        elif choice == "5":
            path = input("📂 请输入文件或文件夹路径: ").strip().strip('"')
            if os.path.exists(path):
                print("🎯 选择要处理的文件类型:")
                print("1. 只处理 MP3 文件")
                print("2. 只处理 FLAC 文件") 
                print("3. 只处理 M4A 文件")
                print("4. 自定义文件类型")
                
                type_choice = input("请选择 (1-4): ").strip()
                filter_ext = None
                
                if type_choice == "1":
                    filter_ext = ['.mp3']
                elif type_choice == "2":
                    filter_ext = ['.flac']
                elif type_choice == "3":
                    filter_ext = ['.m4a']
                elif type_choice == "4":
                    ext_input = input("请输入文件扩展名（如 .mp3,.flac）: ").strip()
                    filter_ext = [ext.strip() for ext in ext_input.split(',')]
                
                if filter_ext:
                    verbose = input("📋 是否显示详细信息? (y/n): ").lower() in ['y', 'yes', '是']
                    dry_run = input("🔍 是否预览模式? (y/n): ").lower() in ['y', 'yes', '是']
                    
                    if os.path.isfile(path):
                        processor.process_audio_file(path, verbose=verbose, dry_run=dry_run)
                    else:
                        processed, removed, errors = batch_process_folder(path, verbose=verbose, dry_run=dry_run, filter_ext=filter_ext)
            else:
                print("❌ 路径不存在!")
        
        elif choice == "6":
            try:
                print("🌐 启动Web界面...")
                print("📱 请在浏览器中访问: http://localhost:5000")
                os.system("python app.py")
            except KeyboardInterrupt:
                print("\n🌐 Web界面已关闭")
            except Exception as e:
                print(f"❌ 启动Web界面失败: {e}")
        
        elif choice == "7":
            show_help()
        
        elif choice == "8":
            print("👋 再见！")
            break
        
        else:
            print("❌ 无效的选择，请重试。")

def show_help():
    """显示帮助信息"""
    print("\n" + "="*60)
    print("📖 歌词清理工具使用帮助")
    print("="*60)
    print("🎯 功能说明:")
    print("   - 自动识别并移除歌词文件中的信息标头")
    print("   - 保留带时间戳的纯歌词内容")
    print("   - 支持 MP3、FLAC、M4A 格式")
    print("   - 保持原有文件夹结构不变")
    print()
    print("🔧 命令行用法:")
    print("   python ly.py [路径] [选项]")
    print()
    print("📋 常用选项:")
    print("   -v, --verbose     显示详细处理信息")
    print("   -d, --dry-run     预览模式，不修改文件")
    print("   -b, --backup      创建备份文件")
    print("   --filter-ext      只处理指定文件类型")
    print()
    print("💡 使用建议:")
    print("   1. 首次使用建议先用预览模式查看效果")
    print("   2. 重要文件建议开启备份模式")
    print("   3. 复杂目录结构建议使用命令行而非Web界面")
    print("   4. 处理大量文件时建议使用详细模式监控进度")
    print()
    print("🔍 示例命令:")
    print('   python ly.py "D:\\Music" --dry-run -v')
    print('   python ly.py "song.mp3" --backup')
    print('   python ly.py "D:\\Music" --filter-ext .flac,.mp3')
    print("="*60)

def main():
    parser = argparse.ArgumentParser(
        description='🎵 音频歌词清理工具 - 智能移除歌词信息标头',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🔍 使用示例:
  python ly.py                              # 启动交互模式
  python ly.py "D:\\Music" -v               # 详细模式处理文件夹
  python ly.py "song.mp3" --dry-run         # 预览单个文件
  python ly.py "D:\\Music" --backup -v      # 备份模式处理
  python ly.py "D:\\Music" --filter-ext .flac,.mp3  # 只处理指定格式
  python ly.py --web                        # 启动Web界面

💡 建议: 首次使用请先用 --dry-run 预览效果
        """
    )
    
    parser.add_argument('path', nargs='?', help='要处理的文件或文件夹路径')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细处理信息')
    parser.add_argument('-d', '--dry-run', action='store_true', help='预览模式，不修改文件')
    parser.add_argument('-b', '--backup', action='store_true', help='创建备份文件（.backup后缀）')
    parser.add_argument('-w', '--web', action='store_true', help='启动Web界面')
    parser.add_argument('--filter-ext', type=str, help='只处理指定文件类型，如: .mp3,.flac,.m4a')
    parser.add_argument('--stats', action='store_true', help='只显示统计信息，不处理文件')
    parser.add_argument('--version', action='version', version='歌词清理工具 v2.0')
    
    args = parser.parse_args()
    
    # 处理文件类型过滤
    filter_ext = None
    if args.filter_ext:
        filter_ext = [ext.strip().lower() for ext in args.filter_ext.split(',')]
        if not all(ext.startswith('.') for ext in filter_ext):
            print("❌ 错误: 文件扩展名必须以点开头，如: .mp3,.flac")
            sys.exit(1)
    
    if args.web:
        try:
            print("🌐 启动Web界面...")
            print("📱 请在浏览器中访问: http://localhost:5000")
            print("💡 提示: 复杂目录结构建议使用命令行模式")
            os.system("python app.py")
        except KeyboardInterrupt:
            print("\n🌐 Web界面已关闭")
        return
    
    if not args.path:
        interactive_mode()
        return
    
    path = Path(args.path)
    
    if not path.exists():
        print(f"❌ 错误: 路径不存在 - {path}")
        sys.exit(1)
    
    # 显示标题
    mode_text = ""
    if args.dry_run:
        mode_text += "🔍 预览模式"
    if args.backup:
        mode_text += " 📦 备份模式" if mode_text else "📦 备份模式"
    if filter_ext:
        mode_text += f" 🎯 过滤: {','.join(filter_ext)}" if mode_text else f"🎯 过滤: {','.join(filter_ext)}"
    
    print(f"🎵 音频歌词清理工具 {mode_text}")
    print("="*80)
    
    if args.stats:
        # 只显示统计信息
        if path.is_dir():
            total_files = 0
            audio_files = 0
            for root, dirs, files in os.walk(path):
                for file in files:
                    total_files += 1
                    if processor.is_audio_file(file):
                        audio_files += 1
            print(f"📊 目录统计: {path}")
            print(f"   📁 总文件数: {total_files}")
            print(f"   🎵 音频文件: {audio_files}")
            print(f"   📄 其他文件: {total_files - audio_files}")
        else:
            print(f"📊 文件信息: {path.name}")
            print(f"   🎵 音频文件: {'是' if processor.is_audio_file(str(path)) else '否'}")
        return
    
    if path.is_file():
        if processor.is_audio_file(str(path)):
            success, removed = processor.process_audio_file(str(path), args.verbose, args.dry_run, args.backup)
            if not success and not args.dry_run:
                print("❌ 处理失败")
                sys.exit(1)
            else:
                print(f"\n✅ {'预览' if args.dry_run else '处理'}完成!")
        else:
            print(f"❌ 错误: 不支持的文件格式 - {path.suffix}")
            print("💡 支持的格式: .mp3, .flac, .m4a")
            sys.exit(1)
    
    elif path.is_dir():
        processed, total_removed, errors = batch_process_folder(
            str(path), args.verbose, args.dry_run, args.backup, filter_ext
        )
        
        if processed == 0:
            print("⚠️  没有找到可处理的音频文件")
            if filter_ext:
                print(f"💡 当前过滤器: {','.join(filter_ext)}")
            sys.exit(1)
        else:
            print(f"\n🎉 {'预览' if args.dry_run else '处理'}完成!")
            if args.dry_run:
                print("💡 如果效果满意，去掉 --dry-run 参数即可正式处理")
            if errors:
                print(f"⚠️  注意: 有 {len(errors)} 个文件处理失败")
    
    if args.backup and not args.dry_run:
        print("📦 备份文件已创建，原文件已更新")

if __name__ == "__main__":
    main()