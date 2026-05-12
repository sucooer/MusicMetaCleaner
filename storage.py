import contextlib
import json
import os

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - Unix
    msvcrt = None


def _config_path(app, key, default_name):
    return os.path.join(app.config['UPLOAD_FOLDER'], app.config.get(key, default_name))


def get_keyword_settings_path(app):
    return _config_path(app, 'KEYWORD_SETTINGS_FILENAME', '.lyrics-cleaner-keywords.json')


def get_execution_log_path(app):
    return _config_path(app, 'EXECUTION_LOG_FILENAME', '.execution-logs.json')


def get_filename_mapping_path(app):
    return _config_path(app, 'FILENAME_MAPPING_FILENAME', '.filename-mapping.json')


@contextlib.contextmanager
def _file_lock(lock_path, exclusive):
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    with open(lock_path, 'a+', encoding='utf-8') as lock_file:
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        elif msvcrt is not None:  # pragma: no cover - Windows
            mode = msvcrt.LK_LOCK if exclusive else msvcrt.LK_RLCK
            msvcrt.locking(lock_file.fileno(), mode, 1)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            elif msvcrt is not None:  # pragma: no cover - Windows
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)


def load_json_file(path, default):
    lock_path = f'{path}.lock'
    with _file_lock(lock_path, exclusive=False):
        if not os.path.exists(path):
            return default
        try:
            with open(path, 'r', encoding='utf-8') as file_obj:
                return json.load(file_obj)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return default


def save_json_file(path, payload):
    lock_path = f'{path}.lock'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with _file_lock(lock_path, exclusive=True):
        tmp_path = f'{path}.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as file_obj:
            json.dump(payload, file_obj, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)


def load_execution_logs(app):
    data = load_json_file(get_execution_log_path(app), [])
    return data if isinstance(data, list) else []


def append_execution_log(app, mode, result, context=None):
    failed_files = list((result or {}).get('failed_files') or [])
    ignored_files = list((result or {}).get('ignored_files') or [])
    if not failed_files and not ignored_files:
        return None

    from datetime import datetime

    context = context or {}
    entry = {
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'mode': mode,
        'success_count': int((result or {}).get('success_count', 0) or 0),
        'failed_count': int((result or {}).get('failed_count', len(failed_files)) or 0),
        'ignored_count': int((result or {}).get('ignored_count', len(ignored_files)) or 0),
        'target_path': str(context.get('target_path') or (result or {}).get('target_path') or ''),
        'dry_run': bool(context.get('dry_run', (result or {}).get('dry_run', False))),
        'failed_files': failed_files,
        'ignored_files': ignored_files,
    }

    entries = load_execution_logs(app)
    entries.insert(0, entry)
    save_json_file(get_execution_log_path(app), entries[:100])
    return entry


def load_filename_mapping(app):
    data = load_json_file(get_filename_mapping_path(app), {})
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items()}


def set_filename_mapping(app, internal_name, original_name):
    mapping = load_filename_mapping(app)
    mapping[str(internal_name)] = str(original_name)
    save_json_file(get_filename_mapping_path(app), mapping)


def get_filename_mapping(app, internal_name):
    return load_filename_mapping(app).get(str(internal_name))
