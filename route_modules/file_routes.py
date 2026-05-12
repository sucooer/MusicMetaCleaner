import os
import tempfile
import zipfile
from datetime import datetime

from flask import current_app, request, jsonify, send_file

from route_modules.base import bp, temp_files
from services import export_failed_files_report, normalize_new_filename, resolve_archive_name, resolve_download_name
from storage import get_filename_mapping


@bp.route('/rename_processed', methods=['POST'])
def rename_processed():
    """重命名上传模式处理后的文件（processed 目录内）"""
    try:
        data = request.get_json(silent=True) or {}
        processed_filename = str(data.get('processed_filename', '')).strip()
        new_name_input = data.get('new_name')

        if not processed_filename:
            return jsonify({'error': '文件名不能为空'}), 400

        src_path = os.path.abspath(os.path.join(current_app.config['PROCESSED_FOLDER'], processed_filename))
        processed_root = os.path.abspath(current_app.config['PROCESSED_FOLDER'])
        if os.path.commonpath([src_path, processed_root]) != processed_root:
            return jsonify({'error': '非法文件路径'}), 400
        if not os.path.isfile(src_path):
            return jsonify({'error': '文件不存在'}), 404

        rel_dir = os.path.dirname(processed_filename)
        src_ext = os.path.splitext(src_path)[1]
        new_name = normalize_new_filename(new_name_input, src_ext)
        if not new_name:
            return jsonify({'error': '新文件名无效'}), 400

        new_rel = os.path.join(rel_dir, new_name) if rel_dir else new_name
        dst_path = os.path.abspath(os.path.join(current_app.config['PROCESSED_FOLDER'], new_rel))
        if os.path.commonpath([dst_path, processed_root]) != processed_root:
            return jsonify({'error': '非法目标路径'}), 400
        if os.path.exists(dst_path):
            return jsonify({'error': '目标文件名已存在'}), 409

        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        os.rename(src_path, dst_path)

        return jsonify({
            'processed_filename': new_rel,
            'display_name': new_name
        })
    except Exception as e:
        return jsonify({'error': f'重命名失败: {str(e)}'}), 500
@bp.route('/download/<path:filename>')
def download_file(filename):
    """下载处理后的文件"""
    file_path = os.path.join(current_app.config['PROCESSED_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    # 获取原始文件名
    if filename.startswith('cleaned_'):
        internal_filename = filename[8:]  # 移除 'cleaned_' 前缀
        
        # 从映射表中获取原始文件名
        download_name = resolve_download_name(filename, get_filename_mapping(current_app, internal_filename))
    else:
        download_name = os.path.basename(filename)
    
    return send_file(file_path, as_attachment=True, download_name=download_name)
@bp.route('/download_all', methods=['POST'])
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
                file_path = os.path.join(current_app.config['PROCESSED_FOLDER'], filename)
                if os.path.exists(file_path):
                    # 恢复原始文件名和文件夹结构
                    if filename.startswith('cleaned_'):
                        internal_filename = filename[8:]  # 移除 'cleaned_' 前缀
                        
                        # 从映射表中获取原始文件路径
                        archive_name = resolve_archive_name(filename, get_filename_mapping(current_app, internal_filename))
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
@bp.route('/export_failed_files', methods=['POST'])
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
        export_failed_files_report(failed_files, output_path)

        return send_file(
            output_path, 
            as_attachment=True, 
            download_name=output_filename
        )
    
    except Exception as e:
        return jsonify({'error': f'导出失败文件时出错: {str(e)}'}), 500
