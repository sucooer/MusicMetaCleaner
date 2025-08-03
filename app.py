import os
import json
import zipfile
import tempfile
import shutil
import atexit
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from lyrics_utils import clean_lyrics, get_lyrics_from_file, save_lyrics_to_file, is_audio_file

app = Flask(__name__)
# app.config['MAX_CONTENT_LENGTH'] = None  # 不限制上传大小
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'

# 确保上传和处理文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# 临时文件清理列表
temp_files = []

# 文件名映射表：存储内部文件名到原始文件名的映射
filename_mapping = {}

def cleanup_temp_files():
    """清理临时文件"""
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                if os.path.isfile(temp_file):
                    os.remove(temp_file)
                elif os.path.isdir(temp_file):
                    shutil.rmtree(temp_file)
        except Exception as e:
            print(f"清理临时文件失败 {temp_file}: {e}")

# 注册程序退出时的清理函数
atexit.register(cleanup_temp_files)

# 错误处理器（保留以防其他413错误）
@app.errorhandler(413)
def request_entity_too_large(error):
    """处理文件过大错误"""
    return jsonify({
        'error': '上传文件过大，请检查服务器配置或减少文件数量'
    }), 413

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """处理文件上传"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': '没有选择文件'}), 400
        
        uploaded_files = []
        errors = []
        
        for file in files:
            if file and file.filename and is_audio_file(file.filename):
                try:
                    # 保存原始文件名
                    original_filename = file.filename
                    filename = secure_filename(original_filename)
                    
                    # 检查文件名是否有效
                    if not filename:
                        errors.append(f"文件名无效: {original_filename}")
                        continue
                    
                    # 添加时间戳避免文件名冲突
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    internal_filename = timestamp + filename
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], internal_filename)
                    
                    # 保存文件
                    file.save(file_path)
                    
                    # 保存文件名映射
                    filename_mapping[internal_filename] = original_filename
                    
                    # 提取原始歌词
                    original_lyrics = get_lyrics_from_file(file_path)
                    
                    uploaded_files.append({
                        'filename': internal_filename,
                        'original_name': original_filename,
                        'has_lyrics': bool(original_lyrics),
                        'original_lyrics': original_lyrics
                    })
                    
                except Exception as e:
                    errors.append(f"处理文件 {file.filename} 失败: {str(e)}")
                    continue
        
        if not uploaded_files and not errors:
            return jsonify({'error': '没有有效的音频文件'}), 400
        
        result = {'files': uploaded_files}
        if errors:
            result['warnings'] = errors
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/upload_folder', methods=['POST'])
def upload_folder():
    """处理文件夹上传"""
    try:
        # 不限制上传大小
        
        if 'files' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': '没有选择文件'}), 400
        
        uploaded_files = []
        folder_structure = {}
        errors = []
        
        for file in files:
            if file and file.filename and is_audio_file(file.filename):
                try:
                    # 保持文件夹结构
                    original_path = file.filename
                    original_basename = os.path.basename(original_path)
                    filename = secure_filename(original_basename)
                    folder_path = os.path.dirname(original_path)
                    
                    # 检查文件名是否有效
                    if not filename:
                        errors.append(f"文件名无效: {original_path}")
                        continue
                    
                    # 添加时间戳避免文件名冲突
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    internal_filename = timestamp + filename
                    
                    # 创建文件夹结构
                    if folder_path:
                        # 安全地处理文件夹路径，保持目录结构
                        # 将路径分隔符统一为系统分隔符，并清理每个路径组件
                        path_parts = folder_path.replace('\\', '/').split('/')
                        safe_path_parts = []
                        for part in path_parts:
                            if part and part != '.' and part != '..':  # 过滤危险路径
                                safe_part = secure_filename(part)
                                if safe_part:  # 确保处理后的路径组件不为空
                                    safe_path_parts.append(safe_part)
                        
                        if safe_path_parts:
                            safe_folder_path = os.path.join(*safe_path_parts)
                            upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], safe_folder_path)
                            os.makedirs(upload_dir, exist_ok=True)
                            file_path = os.path.join(upload_dir, internal_filename)
                            internal_relative_path = os.path.join(safe_folder_path, internal_filename)
                        else:
                            # 如果文件夹路径处理后为空，放在根目录
                            file_path = os.path.join(app.config['UPLOAD_FOLDER'], internal_filename)
                            internal_relative_path = internal_filename
                    else:
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], internal_filename)
                        internal_relative_path = internal_filename
                    
                    # 保存文件
                    file.save(file_path)
                    
                    # 保存文件名映射
                    filename_mapping[internal_relative_path] = original_path
                    
                    # 提取原始歌词
                    original_lyrics = get_lyrics_from_file(file_path)
                    
                    file_info = {
                        'filename': internal_relative_path,
                        'original_name': original_path,
                        'has_lyrics': bool(original_lyrics),
                        'original_lyrics': original_lyrics,
                        'folder': folder_path
                    }
                    
                    uploaded_files.append(file_info)
                    
                    # 构建文件夹结构统计
                    if folder_path not in folder_structure:
                        folder_structure[folder_path] = {'total': 0, 'with_lyrics': 0}
                    folder_structure[folder_path]['total'] += 1
                    if file_info['has_lyrics']:
                        folder_structure[folder_path]['with_lyrics'] += 1
                        
                except Exception as e:
                    errors.append(f"处理文件 {file.filename} 失败: {str(e)}")
                    continue
        
        if not uploaded_files and not errors:
            return jsonify({'error': '没有有效的音频文件'}), 400
        
        result = {
            'files': uploaded_files,
            'folder_structure': folder_structure,
            'total_files': len(uploaded_files),
            'files_with_lyrics': len([f for f in uploaded_files if f['has_lyrics']])
        }
        
        if errors:
            result['warnings'] = errors
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Folder upload error: {e}")
        print(f"Error details: {error_details}")
        return jsonify({'error': f'文件夹上传失败: {str(e)}'}), 500

@app.route('/preview', methods=['POST'])
def preview_cleaning():
    """预览歌词清理效果"""
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': '文件名不能为空'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    original_lyrics = get_lyrics_from_file(file_path)
    if not original_lyrics:
        return jsonify({'error': '文件中没有歌词'}), 400
    
    cleaned_lyrics, removed_lines = clean_lyrics(original_lyrics)
    
    return jsonify({
        'original_lyrics': original_lyrics,
        'cleaned_lyrics': cleaned_lyrics,
        'removed_lines': removed_lines,
        'removed_count': len(removed_lines)
    })

@app.route('/process', methods=['POST'])
def process_files():
    """处理文件，清理歌词"""
    data = request.get_json()
    filenames = data.get('filenames', [])
    
    if not filenames:
        return jsonify({'error': '没有选择要处理的文件'}), 400
    
    processed_files = []
    failed_files = []
    
    for filename in filenames:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            failed_files.append({'filename': filename, 'error': '文件不存在'})
            continue
        
        try:
            original_lyrics = get_lyrics_from_file(file_path)
            if not original_lyrics:
                failed_files.append({'filename': filename, 'error': '文件中没有歌词'})
                continue
            
            cleaned_lyrics, removed_lines = clean_lyrics(original_lyrics)
            
            # 保持文件夹结构
            relative_path = os.path.relpath(file_path, app.config['UPLOAD_FOLDER'])
            processed_filename = f"cleaned_{relative_path}"
            processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
            
            # 创建必要的文件夹
            processed_dir = os.path.dirname(processed_path)
            if processed_dir:
                os.makedirs(processed_dir, exist_ok=True)
            
            # 复制文件到处理文件夹
            shutil.copy2(file_path, processed_path)
            
            # 保存清理后的歌词
            if save_lyrics_to_file(processed_path, cleaned_lyrics):
                # 从映射表获取原始文件名
                print(f"Debug: 查找文件名映射 - filename: {filename}")
                print(f"Debug: 映射表键: {list(filename_mapping.keys())}")
                
                if filename in filename_mapping:
                    original_path = filename_mapping[filename]
                    display_name = os.path.basename(original_path)
                    print(f"Debug: 从映射表找到 - original_path: {original_path}, display_name: {display_name}")
                else:
                    print(f"Debug: 映射表中未找到，尝试解析文件名")
                    # 如果映射表中没有，尝试从文件名解析
                    basename = os.path.basename(filename)
                    print(f"Debug: basename: {basename}")
                    if '_' in basename and len(basename.split('_')) >= 3:
                        parts = basename.split('_', 2)
                        print(f"Debug: 分割结果: {parts}")
                        if parts[0].isdigit() and parts[1].isdigit():
                            display_name = parts[2]
                            print(f"Debug: 解析成功 - display_name: {display_name}")
                        else:
                            display_name = basename
                            print(f"Debug: 时间戳格式不正确，使用basename: {display_name}")
                    else:
                        display_name = basename
                        print(f"Debug: 无法解析，使用basename: {display_name}")
                
                processed_files.append({
                    'original_filename': filename,
                    'processed_filename': processed_filename,
                    'display_name': display_name,  # 用于显示的原始文件名
                    'removed_count': len(removed_lines),
                    'folder': os.path.dirname(relative_path) if os.path.dirname(relative_path) else None
                })
            else:
                failed_files.append({'filename': filename, 'error': '保存歌词失败'})
                
        except Exception as e:
            failed_files.append({'filename': filename, 'error': str(e)})
    
    # 如果有失败文件，自动导出到txt文件
    if failed_files:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"failed_files_{timestamp}.txt"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("MusicMetaCleaner - 失败文件列表\n")
                f.write("=" * 50 + "\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"失败文件总数: {len(failed_files)}\n")
                f.write("=" * 50 + "\n\n")
                
                for i, failed_file in enumerate(failed_files, 1):
                    f.write(f"{i}. {failed_file['filename']}: {failed_file['error']}\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("导出完成\n")
            
            print(f"✅ 失败文件已导出到: {output_path}")
        except Exception as e:
            print(f"❌ 导出失败文件时出错: {e}")
    
    return jsonify({
        'processed_files': processed_files,
        'failed_files': failed_files,
        'success_count': len(processed_files),
        'failed_count': len(failed_files)
    })

@app.route('/download/<path:filename>')
def download_file(filename):
    """下载处理后的文件"""
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    # 获取原始文件名
    if filename.startswith('cleaned_'):
        internal_filename = filename[8:]  # 移除 'cleaned_' 前缀
        
        # 从映射表中获取原始文件名
        if internal_filename in filename_mapping:
            original_path = filename_mapping[internal_filename]
            download_name = os.path.basename(original_path)
        else:
            # 如果映射表中没有，尝试从文件名解析
            basename = os.path.basename(internal_filename)
            if '_' in basename and len(basename.split('_')) >= 3:
                parts = basename.split('_', 2)
                if parts[0].isdigit() and parts[1].isdigit():
                    download_name = parts[2]  # 使用原始文件名部分
                else:
                    download_name = basename
            else:
                download_name = basename
    else:
        download_name = os.path.basename(filename)
    
    return send_file(file_path, as_attachment=True, download_name=download_name)

@app.route('/download_all', methods=['POST'])
def download_all():
    """打包下载所有处理后的文件"""
    data = request.get_json()
    filenames = data.get('filenames', [])
    
    if not filenames:
        return jsonify({'error': '没有文件可下载'}), 400
    
    # 创建临时zip文件
    temp_dir = tempfile.mkdtemp()
    temp_files.append(temp_dir)  # 添加到清理列表
    zip_path = os.path.join(temp_dir, 'cleaned_audio_files.zip')
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            added_files = 0
            for filename in filenames:
                file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
                if os.path.exists(file_path):
                    # 恢复原始文件名和文件夹结构
                    if filename.startswith('cleaned_'):
                        internal_filename = filename[8:]  # 移除 'cleaned_' 前缀
                        
                        # 从映射表中获取原始文件路径
                        if internal_filename in filename_mapping:
                            archive_name = filename_mapping[internal_filename]
                        else:
                            # 如果映射表中没有，尝试从文件名解析
                            path_parts = internal_filename.split(os.sep)
                            if path_parts:
                                basename = path_parts[-1]
                                if '_' in basename and len(basename.split('_')) >= 3:
                                    parts = basename.split('_', 2)
                                    if parts[0].isdigit() and parts[1].isdigit():
                                        path_parts[-1] = parts[2]  # 使用原始文件名部分
                                        archive_name = os.sep.join(path_parts)
                                    else:
                                        archive_name = internal_filename
                                else:
                                    archive_name = internal_filename
                            else:
                                archive_name = internal_filename
                    else:
                        archive_name = filename
                    
                    zipf.write(file_path, archive_name)
                    added_files += 1
        
        if added_files == 0:
            return jsonify({'error': '没有找到可下载的文件'}), 404
        
        return send_file(
            zip_path, 
            as_attachment=True, 
            download_name=f'cleaned_audio_files_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        )
    
    except Exception as e:
        return jsonify({'error': f'创建压缩包失败: {str(e)}'}), 500

@app.route('/export_failed_files', methods=['POST'])
def export_failed_files():
    """导出失败文件列表到txt文件"""
    data = request.get_json()
    failed_files = data.get('failed_files', [])
    
    if not failed_files:
        return jsonify({'error': '没有失败文件可导出'}), 400
    
    # 创建临时txt文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"failed_files_{timestamp}.txt"
    output_path = os.path.join(tempfile.gettempdir(), output_filename)
    temp_files.append(output_path)  # 添加到清理列表
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("MusicMetaCleaner - 失败文件列表\n")
            f.write("=" * 50 + "\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"失败文件总数: {len(failed_files)}\n")
            f.write("=" * 50 + "\n\n")
            
            for i, failed_file in enumerate(failed_files, 1):
                f.write(f"{i}. {failed_file['filename']}: {failed_file['error']}\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("导出完成\n")
        
        return send_file(
            output_path, 
            as_attachment=True, 
            download_name=output_filename
        )
    
    except Exception as e:
        return jsonify({'error': f'导出失败文件时出错: {str(e)}'}), 500

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """清理临时文件"""
    try:
        # 清理上传文件夹
        for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER'], topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Failed to remove file {file_path}: {e}")
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    os.rmdir(dir_path)
                except Exception as e:
                    print(f"Failed to remove directory {dir_path}: {e}")
        
        # 清理处理文件夹
        for root, dirs, files in os.walk(app.config['PROCESSED_FOLDER'], topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Failed to remove file {file_path}: {e}")
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    os.rmdir(dir_path)
                except Exception as e:
                    print(f"Failed to remove directory {dir_path}: {e}")
        
        # 清理文件名映射
        filename_mapping.clear()
        
        return jsonify({'message': '清理完成'})
    
    except Exception as e:
        return jsonify({'error': f'清理失败: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)