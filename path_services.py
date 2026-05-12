import os

from lyrics_utils import clean_lyrics, get_lyrics_from_file, is_audio_file, process_audio_file
from services import get_effective_allowed_root
from storage import append_execution_log


def ensure_allowed_target_path(target_path):
    abs_target_path = os.path.abspath(target_path)
    if not os.path.exists(abs_target_path):
        return None, ({'error': f'路径不存在: {abs_target_path}'}, 404)

    allowed_root = get_effective_allowed_root()
    if allowed_root:
        abs_allowed_root = os.path.abspath(allowed_root)
        try:
            in_allowed_root = os.path.commonpath([abs_target_path, abs_allowed_root]) == abs_allowed_root
        except ValueError:
            in_allowed_root = False

        if not in_allowed_root:
            return None, ({
                'error': '路径不在允许范围内',
                'allowed_root': abs_allowed_root
            }, 403)

    return abs_target_path, None


def browse_directory(requested_path):
    allowed_root = get_effective_allowed_root()
    abs_allowed_root = os.path.abspath(allowed_root) if allowed_root else None

    if requested_path:
        current_path = os.path.abspath(requested_path)
    elif abs_allowed_root:
        current_path = abs_allowed_root
    else:
        current_path = os.path.abspath('/')

    if not os.path.exists(current_path):
        return {'error': f'路径不存在: {current_path}'}, 404

    if not os.path.isdir(current_path):
        current_path = os.path.dirname(current_path)

    if abs_allowed_root:
        try:
            in_allowed_root = os.path.commonpath([current_path, abs_allowed_root]) == abs_allowed_root
        except ValueError:
            in_allowed_root = False
        if not in_allowed_root:
            return {
                'error': '路径不在允许范围内',
                'allowed_root': abs_allowed_root
            }, 403

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
        return {'error': f'无权限访问目录: {current_path}'}, 403

    directories.sort(key=lambda d: d['name'].lower())
    return {
        'current_path': current_path,
        'parent_path': parent_path,
        'directories': directories,
        'allowed_root': abs_allowed_root
    }, 200


def process_target_path(app, target_path, dry_run, backup, use_ai, ai_config, filter_ext):
    abs_target_path, error_result = ensure_allowed_target_path(target_path)
    if error_result:
        return error_result

    def should_process_file(file_path):
        if not is_audio_file(file_path):
            return False
        if filter_ext:
            return os.path.splitext(file_path)[1].lower() in filter_ext
        return True

    def get_removed_line_details(file_path):
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
            return {'error': '该文件不是可处理的音频格式，或不在扩展名过滤范围内'}, 400

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

        append_execution_log(app, 'path', result, context={
            'target_path': abs_target_path,
            'dry_run': dry_run
        })
        return result, 200

    for root, _, files in os.walk(abs_target_path):
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

    append_execution_log(app, 'path', result, context={
        'target_path': abs_target_path,
        'dry_run': dry_run
    })
    return result, 200
