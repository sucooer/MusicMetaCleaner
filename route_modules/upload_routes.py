import os
import shutil
from datetime import datetime

from flask import current_app, request, jsonify
from werkzeug.utils import secure_filename

from lyrics_utils import clean_lyrics, get_lyrics_from_file, save_lyrics_to_file, is_audio_file
from route_modules.base import bp
from services import export_failed_files_report, extract_ai_config, resolve_display_name, to_bool
from storage import append_execution_log, get_execution_log_path, get_filename_mapping, get_keyword_settings_path, set_filename_mapping


@bp.route('/upload', methods=['POST'])
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
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], internal_filename)
                    
                    # 保存文件
                    file.save(file_path)
                    
                    # 保存文件名映射
                    set_filename_mapping(current_app, internal_filename, original_filename)
                    
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
        current_app.logger.exception('Upload error: %s', e)
        return jsonify({'error': f'上传失败: {str(e)}'}), 500
@bp.route('/upload_folder', methods=['POST'])
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
                            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_folder_path)
                            os.makedirs(upload_dir, exist_ok=True)
                            file_path = os.path.join(upload_dir, internal_filename)
                            internal_relative_path = os.path.join(safe_folder_path, internal_filename)
                        else:
                            # 如果文件夹路径处理后为空，放在根目录
                            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], internal_filename)
                            internal_relative_path = internal_filename
                    else:
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], internal_filename)
                        internal_relative_path = internal_filename
                    
                    # 保存文件
                    file.save(file_path)
                    
                    # 保存文件名映射
                    set_filename_mapping(current_app, internal_relative_path, original_path)
                    
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
        current_app.logger.exception('Folder upload error: %s', e)
        return jsonify({'error': f'文件夹上传失败: {str(e)}'}), 500


@bp.route('/preview', methods=['POST'])
def preview_cleaning():
    """预览歌词清理效果"""
    data = request.get_json()
    filename = data.get('filename')
    use_ai = to_bool(data.get('ai_enabled'), default=True)
    ai_config = extract_ai_config(data)
    
    if not filename:
        return jsonify({'error': '文件名不能为空'}), 400
    
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    original_lyrics = get_lyrics_from_file(file_path)
    if not original_lyrics:
        return jsonify({'error': '文件中没有歌词'}), 400
    
    cleaned_lyrics, removed_lines = clean_lyrics(original_lyrics, use_ai=use_ai, ai_config=ai_config)
    
    return jsonify({
        'original_lyrics': original_lyrics,
        'cleaned_lyrics': cleaned_lyrics,
        'removed_lines': removed_lines,
        'removed_count': len(removed_lines)
    })
@bp.route('/process', methods=['POST'])
def process_files():
    """处理文件，清理歌词"""
    data = request.get_json()
    filenames = data.get('filenames', [])
    use_ai = to_bool(data.get('ai_enabled'), default=True)
    ai_config = extract_ai_config(data)
    
    if not filenames:
        return jsonify({'error': '没有选择要处理的文件'}), 400
    
    processed_files = []
    failed_files = []
    ignored_files = []
    
    for filename in filenames:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            failed_files.append({'filename': filename, 'error': '文件不存在'})
            continue
        
        try:
            original_lyrics = get_lyrics_from_file(file_path)
            if not original_lyrics:
                # 将没有歌词的文件标记为忽略，而不是失败
                ignored_files.append({'filename': filename, 'reason': '文件中没有歌词标签'})
                continue
            
            cleaned_lyrics, removed_lines = clean_lyrics(original_lyrics, use_ai=use_ai, ai_config=ai_config)
            
            # 无可移除行时，按忽略处理（无需清理）
            if len(removed_lines) == 0:
                ignored_files.append({'filename': filename, 'reason': '歌词无需清理'})
                continue

            # 保持文件夹结构
            relative_path = os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])
            processed_filename = f"cleaned_{relative_path}"
            processed_path = os.path.join(current_app.config['PROCESSED_FOLDER'], processed_filename)
            
            # 创建必要的文件夹
            processed_dir = os.path.dirname(processed_path)
            if processed_dir:
                os.makedirs(processed_dir, exist_ok=True)
            
            # 复制文件到处理文件夹
            shutil.copy2(file_path, processed_path)
            
            # 保存清理后的歌词
            if save_lyrics_to_file(processed_path, cleaned_lyrics):
                display_name = resolve_display_name(filename, get_filename_mapping(current_app, filename))
                
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
        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

        try:
            export_failed_files_report(failed_files, output_path)
            current_app.logger.info('失败文件已导出到: %s', output_path)
        except Exception as e:
            current_app.logger.exception('导出失败文件时出错: %s', e)
    
    response_payload = {
        'processed_files': processed_files,
        'failed_files': failed_files,
        'ignored_files': ignored_files,
        'success_count': len(processed_files),
        'failed_count': len(failed_files),
        'ignored_count': len(ignored_files)
    }
    append_execution_log(current_app, 'upload', response_payload)
    return jsonify(response_payload)
@bp.route('/cleanup', methods=['POST'])
def cleanup_files():
    """清理临时文件"""
    try:
        protected_upload_files = {
            os.path.abspath(get_keyword_settings_path(current_app)),
            os.path.abspath(get_execution_log_path(current_app))
        }

        # 清理上传文件夹
        for root, dirs, files in os.walk(current_app.config['UPLOAD_FOLDER'], topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.abspath(file_path) in protected_upload_files:
                    continue
                try:
                    os.remove(file_path)
                except Exception as e:
                    current_app.logger.warning('Failed to remove file %s: %s', file_path, e)
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    os.rmdir(dir_path)
                except Exception as e:
                    current_app.logger.warning('Failed to remove directory %s: %s', dir_path, e)
        
        # 清理处理文件夹
        for root, dirs, files in os.walk(current_app.config['PROCESSED_FOLDER'], topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    current_app.logger.warning('Failed to remove file %s: %s', file_path, e)
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    os.rmdir(dir_path)
                except Exception as e:
                    current_app.logger.warning('Failed to remove directory %s: %s', dir_path, e)
        
        return jsonify({'message': '清理完成'})
    
    except Exception as e:
        return jsonify({'error': f'清理失败: {str(e)}'}), 500
