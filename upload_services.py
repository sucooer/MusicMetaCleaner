import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename

from lyrics_utils import clean_lyrics, get_lyrics_from_file, save_lyrics_to_file, is_audio_file
from services import export_failed_files_report, resolve_display_name
from storage import append_execution_log, get_execution_log_path, get_filename_mapping, get_keyword_settings_path, set_filename_mapping


def handle_upload_files(app, files):
    uploaded_files = []
    errors = []

    for file in files:
        if file and file.filename and is_audio_file(file.filename):
            try:
                original_filename = file.filename
                filename = secure_filename(original_filename)
                if not filename:
                    errors.append(f"文件名无效: {original_filename}")
                    continue

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                internal_filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], internal_filename)
                file.save(file_path)
                set_filename_mapping(app, internal_filename, original_filename)
                original_lyrics = get_lyrics_from_file(file_path)
                uploaded_files.append({
                    'filename': internal_filename,
                    'original_name': original_filename,
                    'has_lyrics': bool(original_lyrics),
                    'original_lyrics': original_lyrics
                })
            except Exception as exc:
                errors.append(f"处理文件 {file.filename} 失败: {str(exc)}")

    if not uploaded_files and not errors:
        return {'error': '没有有效的音频文件'}, 400

    result = {'files': uploaded_files}
    if errors:
        result['warnings'] = errors
    return result, 200


def handle_upload_folder(app, files):
    uploaded_files = []
    folder_structure = {}
    errors = []

    for file in files:
        if file and file.filename and is_audio_file(file.filename):
            try:
                original_path = file.filename
                original_basename = os.path.basename(original_path)
                filename = secure_filename(original_basename)
                folder_path = os.path.dirname(original_path)
                if not filename:
                    errors.append(f"文件名无效: {original_path}")
                    continue

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                internal_filename = timestamp + filename

                if folder_path:
                    path_parts = folder_path.replace('\\', '/').split('/')
                    safe_path_parts = []
                    for part in path_parts:
                        if part and part != '.' and part != '..':
                            safe_part = secure_filename(part)
                            if safe_part:
                                safe_path_parts.append(safe_part)
                    if safe_path_parts:
                        safe_folder_path = os.path.join(*safe_path_parts)
                        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], safe_folder_path)
                        os.makedirs(upload_dir, exist_ok=True)
                        file_path = os.path.join(upload_dir, internal_filename)
                        internal_relative_path = os.path.join(safe_folder_path, internal_filename)
                    else:
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], internal_filename)
                        internal_relative_path = internal_filename
                else:
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], internal_filename)
                    internal_relative_path = internal_filename

                file.save(file_path)
                set_filename_mapping(app, internal_relative_path, original_path)
                original_lyrics = get_lyrics_from_file(file_path)
                file_info = {
                    'filename': internal_relative_path,
                    'original_name': original_path,
                    'has_lyrics': bool(original_lyrics),
                    'original_lyrics': original_lyrics,
                    'folder': folder_path
                }
                uploaded_files.append(file_info)

                if folder_path not in folder_structure:
                    folder_structure[folder_path] = {'total': 0, 'with_lyrics': 0}
                folder_structure[folder_path]['total'] += 1
                if file_info['has_lyrics']:
                    folder_structure[folder_path]['with_lyrics'] += 1
            except Exception as exc:
                errors.append(f"处理文件 {file.filename} 失败: {str(exc)}")

    if not uploaded_files and not errors:
        return {'error': '没有有效的音频文件'}, 400

    result = {
        'files': uploaded_files,
        'folder_structure': folder_structure,
        'total_files': len(uploaded_files),
        'files_with_lyrics': len([f for f in uploaded_files if f['has_lyrics']])
    }
    if errors:
        result['warnings'] = errors
    return result, 200


def build_preview_payload(app, filename, use_ai, ai_config):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return {'error': '文件不存在'}, 404

    original_lyrics = get_lyrics_from_file(file_path)
    if not original_lyrics:
        return {'error': '文件中没有歌词'}, 400

    cleaned_lyrics, removed_lines = clean_lyrics(original_lyrics, use_ai=use_ai, ai_config=ai_config)
    return {
        'original_lyrics': original_lyrics,
        'cleaned_lyrics': cleaned_lyrics,
        'removed_lines': removed_lines,
        'removed_count': len(removed_lines)
    }, 200


def process_uploaded_files(app, filenames, use_ai, ai_config):
    processed_files = []
    failed_files = []
    ignored_files = []

    for filename in filenames:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            failed_files.append({'filename': filename, 'error': '文件不存在'})
            continue

        try:
            original_lyrics = get_lyrics_from_file(file_path)
            if not original_lyrics:
                ignored_files.append({'filename': filename, 'reason': '文件中没有歌词标签'})
                continue

            cleaned_lyrics, removed_lines = clean_lyrics(original_lyrics, use_ai=use_ai, ai_config=ai_config)
            if len(removed_lines) == 0:
                ignored_files.append({'filename': filename, 'reason': '歌词无需清理'})
                continue

            relative_path = os.path.relpath(file_path, app.config['UPLOAD_FOLDER'])
            processed_filename = f"cleaned_{relative_path}"
            processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
            processed_dir = os.path.dirname(processed_path)
            if processed_dir:
                os.makedirs(processed_dir, exist_ok=True)

            shutil.copy2(file_path, processed_path)
            if save_lyrics_to_file(processed_path, cleaned_lyrics):
                display_name = resolve_display_name(filename, get_filename_mapping(app, filename))
                processed_files.append({
                    'original_filename': filename,
                    'processed_filename': processed_filename,
                    'display_name': display_name,
                    'removed_count': len(removed_lines),
                    'folder': os.path.dirname(relative_path) if os.path.dirname(relative_path) else None
                })
            else:
                failed_files.append({'filename': filename, 'error': '保存歌词失败'})
        except Exception as exc:
            failed_files.append({'filename': filename, 'error': str(exc)})

    if failed_files:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"failed_files_{timestamp}.txt"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        try:
            export_failed_files_report(failed_files, output_path)
            app.logger.info('失败文件已导出到: %s', output_path)
        except Exception as exc:
            app.logger.exception('导出失败文件时出错: %s', exc)

    payload = {
        'processed_files': processed_files,
        'failed_files': failed_files,
        'ignored_files': ignored_files,
        'success_count': len(processed_files),
        'failed_count': len(failed_files),
        'ignored_count': len(ignored_files)
    }
    append_execution_log(app, 'upload', payload)
    return payload, 200


def cleanup_workspace(app):
    protected_upload_files = {
        os.path.abspath(get_keyword_settings_path(app)),
        os.path.abspath(get_execution_log_path(app))
    }

    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER'], topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.abspath(file_path) in protected_upload_files:
                continue
            try:
                os.remove(file_path)
            except Exception as exc:
                app.logger.warning('Failed to remove file %s: %s', file_path, exc)
        for directory in dirs:
            dir_path = os.path.join(root, directory)
            try:
                os.rmdir(dir_path)
            except Exception as exc:
                app.logger.warning('Failed to remove directory %s: %s', dir_path, exc)

    for root, dirs, files in os.walk(app.config['PROCESSED_FOLDER'], topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                os.remove(file_path)
            except Exception as exc:
                app.logger.warning('Failed to remove file %s: %s', file_path, exc)
        for directory in dirs:
            dir_path = os.path.join(root, directory)
            try:
                os.rmdir(dir_path)
            except Exception as exc:
                app.logger.warning('Failed to remove directory %s: %s', dir_path, exc)

    return {'message': '清理完成'}, 200
