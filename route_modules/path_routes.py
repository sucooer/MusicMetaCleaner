import os

from flask import current_app, request, jsonify

from lyrics_utils import clean_lyrics, get_lyrics_from_file, is_audio_file, process_audio_file
from route_modules.base import bp
from services import extract_ai_config, get_effective_allowed_root, normalize_filter_ext, normalize_new_filename, to_bool
from storage import append_execution_log


@bp.route('/process_path', methods=['POST'])
def process_path():
    """按服务器路径直接处理文件或文件夹"""
    try:
        data = request.get_json(silent=True) or {}
        target_path = str(data.get('path', '')).strip().strip('"')
        dry_run = bool(data.get('dry_run', False))
        backup = bool(data.get('backup', False))
        use_ai = to_bool(data.get('ai_enabled'), default=True)
        ai_config = extract_ai_config(data)
        filter_ext = normalize_filter_ext(data.get('filter_ext'))

        if not target_path:
            return jsonify({'error': '路径不能为空'}), 400

        abs_target_path = os.path.abspath(target_path)

        if not os.path.exists(abs_target_path):
            return jsonify({'error': f'路径不存在: {abs_target_path}'}), 404

        # 可选的路径白名单（用于生产环境安全控制）
        allowed_root = get_effective_allowed_root()
        if allowed_root:
            abs_allowed_root = os.path.abspath(allowed_root)
            try:
                in_allowed_root = os.path.commonpath([abs_target_path, abs_allowed_root]) == abs_allowed_root
            except ValueError:
                in_allowed_root = False

            if not in_allowed_root:
                return jsonify({
                    'error': '路径不在允许范围内',
                    'allowed_root': abs_allowed_root
                }), 403

        def should_process_file(file_path):
            if not is_audio_file(file_path):
                return False
            if filter_ext:
                return os.path.splitext(file_path)[1].lower() in filter_ext
            return True

        def get_removed_line_details(file_path):
            """仅用于预览模式：返回将被移除的具体歌词行"""
            if not dry_run:
                return []
            original_lyrics = get_lyrics_from_file(file_path)
            if not original_lyrics:
                return []
            _, removed_line_items = clean_lyrics(original_lyrics, use_ai=use_ai, ai_config=ai_config)
            return removed_line_items

        result = {
            'target_path': abs_target_path,
            'dry_run': dry_run,
            'backup': backup,
            'filter_ext': filter_ext,
            'total_audio_files': 0,
            'success_count': 0,
            'failed_count': 0,
            'ignored_count': 0,
            'total_removed': 0,
            'processed_files': [],
            'failed_files': [],
            'ignored_files': []
        }

        if os.path.isfile(abs_target_path):
            if not should_process_file(abs_target_path):
                return jsonify({'error': '该文件不是可处理的音频格式，或不在扩展名过滤范围内'}), 400

            result['total_audio_files'] = 1
            state, removed_lines = process_audio_file(abs_target_path, verbose=False, dry_run=dry_run, backup=backup, use_ai=use_ai, ai_config=ai_config)
            display_name = os.path.basename(abs_target_path)

            if state is True and removed_lines > 0:
                removed_line_items = get_removed_line_details(abs_target_path)
                result['success_count'] = 1
                result['total_removed'] = removed_lines
                result['processed_files'].append({
                    'path': abs_target_path,
                    'display_name': display_name,
                    'removed_count': removed_lines,
                    'removed_lines': removed_line_items
                })
            elif state is None:
                result['ignored_count'] = 1
                result['ignored_files'].append({
                    'filename': abs_target_path,
                    'reason': '文件中没有歌词标签'
                })
            elif state is True and removed_lines == 0:
                result['ignored_count'] = 1
                result['ignored_files'].append({
                    'filename': abs_target_path,
                    'reason': '歌词无需清理'
                })
            else:
                result['failed_count'] = 1
                result['failed_files'].append({
                    'filename': abs_target_path,
                    'error': '处理失败'
                })

            append_execution_log(current_app, 'path', result, context={
                'target_path': abs_target_path,
                'dry_run': dry_run
            })
            return jsonify(result)

        # 文件夹模式
        for root, dirs, files in os.walk(abs_target_path):
            for file in files:
                file_path = os.path.join(root, file)
                if not should_process_file(file_path):
                    continue

                result['total_audio_files'] += 1
                state, removed_lines = process_audio_file(file_path, verbose=False, dry_run=dry_run, backup=backup, use_ai=use_ai, ai_config=ai_config)
                rel_path = os.path.relpath(file_path, abs_target_path)

                if state is True and removed_lines > 0:
                    removed_line_items = get_removed_line_details(file_path)
                    result['success_count'] += 1
                    result['total_removed'] += removed_lines
                    result['processed_files'].append({
                        'path': file_path,
                        'display_name': rel_path,
                        'removed_count': removed_lines,
                        'removed_lines': removed_line_items
                    })
                elif state is None:
                    result['ignored_count'] += 1
                    result['ignored_files'].append({
                        'filename': rel_path,
                        'reason': '文件中没有歌词标签'
                    })
                elif state is True and removed_lines == 0:
                    result['ignored_count'] += 1
                    result['ignored_files'].append({
                        'filename': rel_path,
                        'reason': '歌词无需清理'
                    })
                else:
                    result['failed_count'] += 1
                    result['failed_files'].append({
                        'filename': rel_path,
                        'error': '处理失败'
                    })

        append_execution_log(current_app, 'path', result, context={
            'target_path': abs_target_path,
            'dry_run': dry_run
        })
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'路径处理失败: {str(e)}'}), 500
@bp.route('/browse_path', methods=['POST'])
def browse_path():
    """浏览服务器目录，用于路径模式手动选择"""
    try:
        data = request.get_json(silent=True) or {}
        requested_path = str(data.get('path', '')).strip().strip('"')

        allowed_root = get_effective_allowed_root()
        abs_allowed_root = os.path.abspath(allowed_root) if allowed_root else None

        if requested_path:
            current_path = os.path.abspath(requested_path)
        elif abs_allowed_root:
            current_path = abs_allowed_root
        else:
            current_path = os.path.abspath('/')

        if not os.path.exists(current_path):
            return jsonify({'error': f'路径不存在: {current_path}'}), 404

        if not os.path.isdir(current_path):
            current_path = os.path.dirname(current_path)

        if abs_allowed_root:
            try:
                in_allowed_root = os.path.commonpath([current_path, abs_allowed_root]) == abs_allowed_root
            except ValueError:
                in_allowed_root = False
            if not in_allowed_root:
                return jsonify({
                    'error': '路径不在允许范围内',
                    'allowed_root': abs_allowed_root
                }), 403

        parent_path = None
        try:
            parent_candidate = os.path.abspath(os.path.join(current_path, '..'))
            if parent_candidate != current_path:
                if abs_allowed_root:
                    in_root = os.path.commonpath([parent_candidate, abs_allowed_root]) == abs_allowed_root
                    if in_root:
                        parent_path = parent_candidate
                else:
                    parent_path = parent_candidate
        except Exception:
            parent_path = None

        directories = []
        try:
            with os.scandir(current_path) as entries:
                for entry in entries:
                    if not entry.is_dir(follow_symlinks=False):
                        continue
                    full_path = os.path.abspath(entry.path)
                    if abs_allowed_root:
                        try:
                            in_root = os.path.commonpath([full_path, abs_allowed_root]) == abs_allowed_root
                        except ValueError:
                            in_root = False
                        if not in_root:
                            continue
                    directories.append({
                        'name': entry.name,
                        'path': full_path
                    })
        except PermissionError:
            return jsonify({'error': f'无权限访问目录: {current_path}'}), 403

        directories.sort(key=lambda d: d['name'].lower())

        return jsonify({
            'current_path': current_path,
            'parent_path': parent_path,
            'directories': directories,
            'allowed_root': abs_allowed_root
        })
    except Exception as e:
        return jsonify({'error': f'目录浏览失败: {str(e)}'}), 500
@bp.route('/rename_path_file', methods=['POST'])
def rename_path_file():
    """重命名路径模式中的服务器文件"""
    try:
        data = request.get_json(silent=True) or {}
        file_path = str(data.get('path', '')).strip().strip('"')
        new_name_input = data.get('new_name')

        if not file_path:
            return jsonify({'error': '路径不能为空'}), 400

        abs_file_path = os.path.abspath(file_path)
        if not os.path.isfile(abs_file_path):
            return jsonify({'error': '文件不存在'}), 404

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
