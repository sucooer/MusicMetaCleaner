from flask import current_app, request, jsonify

from route_modules.base import bp
from services import extract_ai_config, normalize_filter_ext, normalize_new_filename, to_bool
from path_services import browse_directory, process_target_path


@bp.route('/process_path', methods=['POST'])
def process_path():
    data = request.get_json(silent=True) or {}
    target_path = str(data.get('path', '')).strip().strip('"')
    dry_run = bool(data.get('dry_run', False))
    backup = bool(data.get('backup', False))
    use_ai = to_bool(data.get('ai_enabled'), default=True)
    ai_config = extract_ai_config(data)
    filter_ext = normalize_filter_ext(data.get('filter_ext'))

    if not target_path:
        return jsonify({'error': '路径不能为空'}), 400

    payload, status = process_target_path(
        current_app,
        target_path=target_path,
        dry_run=dry_run,
        backup=backup,
        use_ai=use_ai,
        ai_config=ai_config,
        filter_ext=filter_ext
    )
    return jsonify(payload), status


@bp.route('/browse_path', methods=['POST'])
def browse_path():
    data = request.get_json(silent=True) or {}
    requested_path = str(data.get('path', '')).strip().strip('"')
    payload, status = browse_directory(requested_path)
    return jsonify(payload), status


@bp.route('/rename_path_file', methods=['POST'])
def rename_path_file():
    try:
        data = request.get_json(silent=True) or {}
        file_path = str(data.get('path', '')).strip().strip('"')
        new_name_input = data.get('new_name')

        if not file_path:
            return jsonify({'error': '路径不能为空'}), 400

        import os
        abs_file_path = os.path.abspath(file_path)
        if not os.path.isfile(abs_file_path):
            return jsonify({'error': '文件不存在'}), 404

        from services import get_effective_allowed_root
        allowed_root = get_effective_allowed_root()
        if allowed_root:
            abs_allowed_root = os.path.abspath(allowed_root)
            try:
                in_allowed_root = os.path.commonpath([abs_file_path, abs_allowed_root]) == abs_allowed_root
            except ValueError:
                in_allowed_root = False
            if not in_allowed_root:
                return jsonify({'error': '路径不在允许范围内', 'allowed_root': abs_allowed_root}), 403

        src_ext = os.path.splitext(abs_file_path)[1]
        new_name = normalize_new_filename(new_name_input, src_ext)
        if not new_name:
            return jsonify({'error': '新文件名无效'}), 400

        dst_path = os.path.join(os.path.dirname(abs_file_path), new_name)
        if os.path.abspath(dst_path) == abs_file_path:
            return jsonify({'error': '新文件名与原文件相同'}), 400
        if os.path.exists(dst_path):
            return jsonify({'error': '目标文件名已存在'}), 409

        os.rename(abs_file_path, dst_path)
        return jsonify({
            'path': os.path.abspath(dst_path),
            'display_name': os.path.basename(dst_path)
        })
    except Exception as e:
        return jsonify({'error': f'重命名失败: {str(e)}'}), 500
