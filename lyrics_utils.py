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
            # 中文常见元信息关键词
            '作词', '作词：', '词', '词：', '填词', '填词：', '歌词', '歌词：',
            '作曲', '作曲：', '曲', '曲：', '谱曲', '谱曲：', '词曲', '词曲：',
            '编曲', '编曲：', '配器', '配器：', '和声', '和声：', '和音', '和音：', '配唱', '配唱：',
            '演唱', '演唱：', '歌手', '歌手：', '主唱', '主唱：', '合唱', '合唱：',
            '制作', '制作：', '制作人', '制作人：', '监制', '监制：', '制片', '制片：',
            '录音', '录音：', '录音师', '录音师：', '录音棚', '录音棚：', '录音室', '录音室：',
            '混音', '混音：', '缩混', '缩混：', '混音师', '混音师：', '后期', '后期：',
            '母带', '母带：', '母带工程师', '母带工程师：', '母带处理', '母带处理：',
            '文案', '文案：', '策划', '策划：', '统筹', '统筹：', '推广', '推广：', '宣传', '宣传：', '企划', '企划：',
            '发行', '发行：', '发行方', '发行方：', '发行公司', '发行公司：',
            '出品', '出品：', '出品人', '出品人：', '出品公司', '出品公司：', '唱片公司', '唱片公司：',
            '版权', '版权：', '版权所有', '版权归', '授权', '授权：', '未经许可', '禁止转载',
            '鸣谢', '鸣谢：', '特别鸣谢', '特别鸣谢：', '提供', '提供：', '作品', '作品：',
            '词作者', '词作者：', '曲作者', '曲作者：', '编者', '编者：',
            '翻译', '翻译：', '译者', '译者：', '歌词翻译', '歌词翻译：', '音译', '音译：',
            'LRC', 'LRC：', 'lrc', 'lrc：', '歌词制作', '歌词制作：', '歌词编辑', '歌词编辑：',
            'OP', 'SP', '詞：', '詞', '作詞', '作詞：', '編曲', '編曲：', '詩曲',

            # 英文常见元信息关键词
            'Produced by', 'Lyrics by', 'Composed by', 'Lyrics by:', 'Composed by:',
            'Lyricist', 'Composer', 'Arranger', 'Arrangement', 'Written by', 'Music by', 'Words by',
            'Artist', 'Singer', 'Vocal', 'Vocals', 'Performed by', 'Feat.', 'Featuring',
            'Producer', 'Executive Producer', 'Co-Producer', 'Production',
            'Recording', 'Recorded by', 'Tracking', 'Engineered by', 'Audio Engineer',
            'Mixed by', 'Mixing', 'Mix Engineer', 'Mastered by', 'Mastering', 'Remastered by',
            'Chorus', 'Background Vocal', 'Backing Vocal', 'Harmony',
            'Album', 'Title', 'Song', 'Track', 'Disc', 'Version', 'Original', 'Remix',
            'Publisher', 'Publishing', 'Label', 'Distributed by', 'Distribution',
            'Copyright', 'All Rights Reserved', 'Licensed by', 'ISRC',
            'Transcribed by', 'Translated by', 'Subtitle', 'Subtitles', 'Source'
        ]
        self.header_keywords_lower = [kw.lower() for kw in self.header_keywords]        
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
        
        # 兼容 \n / \r\n / \r 各种换行
        lines = lyrics_text.splitlines()
        pure_lyrics_lines = []
        removed_lines = []
        
        for line in lines:
            line_for_match = line.lstrip('\ufeff')  # 兼容部分歌词开头 BOM
            timestamp_match = re.match(
                r'^\s*\[(\d{1,2}):(\d{1,2})(?:[.:](\d{1,3}))?\]\s*(.*)$',
                line_for_match
            )

            # 移除 00:00.xx 的标题元信息行，例如 [00:00.10]不如这样 - 陈奕迅
            if timestamp_match:
                minute = int(timestamp_match.group(1))
                second = int(timestamp_match.group(2))
                content = timestamp_match.group(4).strip()

                if minute == 0 and second == 0:
                    is_title_artist = re.search(r'.+\s*[-—–－]\s*.+', content) is not None
                    if content == "" or is_title_artist:
                        removed_lines.append(line)
                        if verbose:
                            print(f"移除行: {line}")
                        continue

            timestamp_prefix_pattern = r'^(?:\s*\[\d{1,2}:\d{1,2}(?:[.:]\d{1,3})?\])+\s*'
            # 检查是否包含时间戳 [xx:xx.xx] / [xx:xx]
            has_timestamp = re.search(r'\[\d{1,2}:\d{1,2}(?:[.:]\d{1,3})?\]', line_for_match) is not None
            # 提取一个或多个前置时间戳后的内容
            content_after_timestamp = re.sub(timestamp_prefix_pattern, '', line_for_match).strip()
            # 检查是否以杂项关键词开头（英文大小写不敏感）
            content_after_timestamp_lower = content_after_timestamp.lower()
            has_header_keyword = any(
                content_after_timestamp_lower.startswith(keyword)
                for keyword in self.header_keywords_lower
            )
            
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

