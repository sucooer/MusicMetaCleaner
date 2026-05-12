from flask import current_app, request, jsonify

from route_modules.base import bp
from services import extract_ai_config, to_bool
from upload_services import (
    build_preview_payload,
    cleanup_workspace,
    handle_upload_files,
    handle_upload_folder,
    process_uploaded_files,
)


@bp.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'files' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': '没有选择文件'}), 400
        payload, status = handle_upload_files(current_app, files)
        return jsonify(payload), status
    except Exception as exc:
        current_app.logger.exception('Upload error: %s', exc)
        return jsonify({'error': f'上传失败: {str(exc)}'}), 500


@bp.route('/upload_folder', methods=['POST'])
def upload_folder():
    try:
        if 'files' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': '没有选择文件'}), 400
        payload, status = handle_upload_folder(current_app, files)
        return jsonify(payload), status
    except Exception as exc:
        current_app.logger.exception('Folder upload error: %s', exc)
        return jsonify({'error': f'文件夹上传失败: {str(exc)}'}), 500


@bp.route('/preview', methods=['POST'])
def preview_cleaning():
    data = request.get_json() or {}
    filename = data.get('filename')
    use_ai = to_bool(data.get('ai_enabled'), default=True)
    ai_config = extract_ai_config(data)

    if not filename:
        return jsonify({'error': '文件名不能为空'}), 400

    payload, status = build_preview_payload(current_app, filename, use_ai, ai_config)
    return jsonify(payload), status


@bp.route('/process', methods=['POST'])
def process_files():
    data = request.get_json() or {}
    filenames = data.get('filenames', [])
    use_ai = to_bool(data.get('ai_enabled'), default=True)
    ai_config = extract_ai_config(data)

    if not filenames:
        return jsonify({'error': '没有选择要处理的文件'}), 400

    payload, status = process_uploaded_files(current_app, filenames, use_ai, ai_config)
    return jsonify(payload), status


@bp.route('/cleanup', methods=['POST'])
def cleanup_files():
    try:
        payload, status = cleanup_workspace(current_app)
        return jsonify(payload), status
    except Exception as exc:
        return jsonify({'error': f'清理失败: {str(exc)}'}), 500
