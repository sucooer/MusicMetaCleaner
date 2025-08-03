#!/usr/bin/env python3
"""
失败文件导出工具
用于将MusicMetaCleaner处理过程中的失败文件导出到txt文件
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

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

def read_failed_files_from_log(log_file):
    """
    从日志文件中读取失败文件列表
    
    Args:
        log_file (str): 日志文件路径
        
    Returns:
        list: 失败文件列表
    """
    failed_files = []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if line.startswith('❌') and '处理失败' in line:
                # 提取文件路径和错误信息
                parts = line.split(' - ', 1)
                if len(parts) == 2:
                    file_path = parts[0].replace('❌ 处理失败: ', '').strip()
                    error_msg = parts[1].strip()
                    failed_files.append(f"{file_path}: {error_msg}")
                else:
                    failed_files.append(line)
            elif line.startswith('❌') and '失败文件' in line:
                # 直接包含失败信息的行
                failed_files.append(line)
                
    except Exception as e:
        print(f"❌ 读取日志文件时出错: {e}")
    
    return failed_files

def main():
    parser = argparse.ArgumentParser(description='导出MusicMetaCleaner失败文件列表')
    parser.add_argument('--input', '-i', help='输入文件路径（日志文件或失败文件列表）')
    parser.add_argument('--output', '-o', default='failed_files.txt', help='输出文件路径')
    parser.add_argument('--files', '-f', nargs='+', help='直接指定失败文件列表')
    
    args = parser.parse_args()
    
    failed_files = []
    
    if args.files:
        # 直接指定失败文件列表
        failed_files = args.files
    elif args.input:
        # 从输入文件读取
        if os.path.exists(args.input):
            failed_files = read_failed_files_from_log(args.input)
        else:
            print(f"❌ 输入文件不存在: {args.input}")
            return 1
    else:
        # 交互模式
        print("🎵 MusicMetaCleaner - 失败文件导出工具")
        print("=" * 50)
        
        while True:
            print("\n请选择输入方式:")
            print("1. 📄 从日志文件读取")
            print("2. 📝 手动输入失败文件")
            print("3. 🚪 退出")
            
            choice = input("\n请输入选择 (1-3): ").strip()
            
            if choice == "1":
                log_file = input("📂 请输入日志文件路径: ").strip().strip('"')
                if os.path.exists(log_file):
                    failed_files = read_failed_files_from_log(log_file)
                    break
                else:
                    print("❌ 文件不存在!")
                    
            elif choice == "2":
                print("📝 请输入失败文件列表（每行一个，输入空行结束）:")
                while True:
                    line = input().strip()
                    if not line:
                        break
                    failed_files.append(line)
                break
                
            elif choice == "3":
                print("👋 再见!")
                return 0
                
            else:
                print("❌ 无效选择!")
    
    if not failed_files:
        print("❌ 没有找到失败文件!")
        return 1
    
    # 导出失败文件
    success = export_failed_files_to_txt(failed_files, args.output)
    
    if success:
        print(f"\n📊 导出统计:")
        print(f"   失败文件总数: {len(failed_files)}")
        print(f"   输出文件: {args.output}")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main()) 