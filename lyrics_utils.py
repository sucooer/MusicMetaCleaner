#!/usr/bin/env python3
"""
歌词处理工具模块
提供歌词清理和音频文件处理的公共函数
"""

import os
import re
from mutagen.flac import FLAC
from mutagen.id3 import ID3, USLT
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4


class LyricsProcessor:
    """歌词处理器类"""
    
    def __init__(self):
        # 扩展所有常见杂项关键词
        self.header_keywords = [
            '作词', '作曲', '编曲', '演唱', '制作', '作品', '提供', '制作人', 'Produced by',
            '和声', '配唱', '录音', '录音师', '混音', '混音师', '母带', '母带工程师',
            '文案', '制片', '监制', 'OP', 'SP', '发行', '出品', '出品人', '策划', '统筹', '推广', '鸣谢', '詞：', '編曲', '詩曲', 
            '词', '曲', '作詞' , '制作人'# 添加单字关键词
            'Lyrics by', 'Composed by',  # 添加英文关键词
            'Lyrics by:', 'Composed by:'  # 添加带冒号的英文关键词
        ]
        
        # 支持的音频格式
        self.supported_formats = {'.mp3', '.flac', '.m4a'}
    
    def clean_lyrics(self, lyrics_text, verbose=False):
        """
        删除歌词中的信息标头，但保留带方括号的时间戳格式
        
        Args:
            lyrics_text (str): 原始歌词文本
            verbose (bool): 是否显示详细信息
            
        Returns:
            tuple: (清理后的歌词, 被移除的行列表)
        """
        if not lyrics_text:
            return "", []
        
        lines = lyrics_text.split('\n')
        pure_lyrics_lines = []
        removed_lines = []
        
        for line in lines:
            # 检查是否包含时间戳 [xx:xx.xx]
            has_timestamp = re.search(r'\[\d+:\d+\.\d+\]', line) is not None
            # 提取时间戳后的内容
            content_after_timestamp = re.sub(r'^\[\d+:\d+\.\d+\]', '', line).strip()
            # 检查是否以杂项关键词开头
            has_header_keyword = any(content_after_timestamp.startswith(keyword) for keyword in self.header_keywords)
            
            # 如果有时间戳且有杂项关键词，则跳过
            if has_timestamp and has_header_keyword:
                removed_lines.append(line)
                if verbose:
                    print(f"移除行: {line}")
                continue
            pure_lyrics_lines.append(line)
        
        return '\n'.join(pure_lyrics_lines), removed_lines
    
    def is_audio_file(self, filename):
        """检查文件是否为支持的音频格式"""
        return os.path.splitext(filename.lower())[1] in self.supported_formats
    
    def get_lyrics_from_file(self, file_path):
        """
        从音频文件中提取歌词
        
        Args:
            file_path (str): 音频文件路径
            
        Returns:
            str: 歌词文本，如果没有歌词则返回空字符串
        """
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.flac':
                audio = FLAC(file_path)
                return audio.get('lyrics', [''])[0] if 'lyrics' in audio else ""
                
            elif file_ext == '.mp3':
                audio = ID3(file_path)
                return audio.get('USLT', USLT()).text if 'USLT' in audio else ""
                
            elif file_ext == '.m4a':
                audio = MP4(file_path)
                return audio.get('©lyr', [''])[0] if '©lyr' in audio else ""
                
        except Exception as e:
            print(f"读取歌词时出错 {file_path}: {e}")
            return ""
        
        return ""
    
    def save_lyrics_to_file(self, file_path, lyrics_text):
        """
        将清理后的歌词保存到音频文件
        
        Args:
            file_path (str): 音频文件路径
            lyrics_text (str): 要保存的歌词文本
            
        Returns:
            bool: 保存是否成功
        """
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.flac':
                audio = FLAC(file_path)
                audio['lyrics'] = [lyrics_text]
                audio.save()
                
            elif file_ext == '.mp3':
                audio = ID3(file_path)
                if 'USLT' not in audio:
                    audio['USLT'] = USLT(encoding=3, lang='chi', desc='', text=lyrics_text)
                else:
                    audio['USLT'].text = lyrics_text
                audio.save()
                
            elif file_ext == '.m4a':
                audio = MP4(file_path)
                audio['©lyr'] = [lyrics_text]
                audio.save()
                
            return True
            
        except Exception as e:
            print(f"保存歌词时出错 {file_path}: {e}")
            return False
    
    def process_audio_file(self, file_path, verbose=False, dry_run=False, backup=False):
        """
        处理单个音频文件以清理歌词
        
        Args:
            file_path (str): 音频文件路径
            verbose (bool): 是否显示详细信息
            dry_run (bool): 是否为预览模式（不修改文件）
            backup (bool): 是否创建备份文件
            
        Returns:
            tuple: (处理状态, 移除的行数)
            处理状态: True=成功, False=失败, None=忽略（无歌词标签）
        """
        try:
            if not self.is_audio_file(file_path):
                if verbose:
                    print(f"❌ 不支持的文件类型: {file_path}")
                return False, 0
            
            original_lyrics = self.get_lyrics_from_file(file_path)
            if not original_lyrics:
                if verbose:
                    print(f"⏭️  无歌词标签: {os.path.basename(file_path)}")
                return None, 0
            
            if verbose:
                print(f"📄 处理文件: {os.path.basename(file_path)}")
                print(f"   原歌词长度: {len(original_lyrics)} 字符")
            
            clean_lyrics_text, removed_lines = self.clean_lyrics(original_lyrics, verbose)
            
            if len(removed_lines) == 0:
                if verbose:
                    print(f"   ✨ 无需清理（没有找到信息标头）")
                return True, 0
            
            if not dry_run:
                # 创建备份
                if backup:
                    backup_success = self.create_backup(file_path)
                    if not backup_success:
                        print(f"❌ 备份失败: {file_path}")
                        return False, 0
                    if verbose:
                        print(f"   📦 已创建备份")
                
                # 保存清理后的歌词
                success = self.save_lyrics_to_file(file_path, clean_lyrics_text)
                if not success:
                    return False, 0
                
                if verbose:
                    print(f"   ✅ 已更新歌词 (移除 {len(removed_lines)} 行)")
                else:
                    print(f"✅ {os.path.basename(file_path)} (移除 {len(removed_lines)} 行)")
            else:
                if verbose:
                    print(f"   🔍 预览: 将移除 {len(removed_lines)} 行信息标头")
                else:
                    print(f"🔍 {os.path.basename(file_path)} (将移除 {len(removed_lines)} 行)")
            
            return True, len(removed_lines)
            
        except Exception as e:
            print(f"❌ 处理文件时出错 {file_path}: {e}")
            return False, 0
    
    def create_backup(self, file_path):
        """
        创建文件备份
        
        Args:
            file_path (str): 原文件路径
            
        Returns:
            bool: 备份是否成功
        """
        try:
            import shutil
            backup_path = file_path + '.backup'
            
            # 如果备份文件已存在，添加数字后缀
            counter = 1
            while os.path.exists(backup_path):
                backup_path = f"{file_path}.backup.{counter}"
                counter += 1
            
            shutil.copy2(file_path, backup_path)
            return True
            
        except Exception as e:
            print(f"创建备份失败 {file_path}: {e}")
            return False


# 创建全局实例供其他模块使用
lyrics_processor = LyricsProcessor()

# 导出常用函数
clean_lyrics = lyrics_processor.clean_lyrics
get_lyrics_from_file = lyrics_processor.get_lyrics_from_file
save_lyrics_to_file = lyrics_processor.save_lyrics_to_file
is_audio_file = lyrics_processor.is_audio_file
process_audio_file = lyrics_processor.process_audio_file