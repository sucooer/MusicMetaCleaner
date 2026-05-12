import os
import re
from datetime import datetime


def to_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def normalize_new_filename(new_name, original_ext=''):
    name = str(new_name or '').strip().strip('"').strip("'")
    name = os.path.basename(name)
    name = re.sub(r'[\\/:\*\?"<>\|\x00-\x1f]+', '_', name).strip()
    if not name:
        return None
    _, ext = os.path.splitext(name)
    if not ext and original_ext:
        return name + original_ext
    return name


def extract_ai_config(data):
    cfg = data.get('ai_config') if isinstance(data, dict) else None
    if not isinstance(cfg, dict):
        return None
    base_url = str(cfg.get('base_url', '')).strip().rstrip('/')
    model = str(cfg.get('model', '')).strip()
    api_key = str(cfg.get('api_key', '')).strip()
    timeout_raw = cfg.get('timeout', 6)
    try:
        timeout = float(timeout_raw)
    except (TypeError, ValueError):
        timeout = 6
    if timeout <= 0:
        timeout = 6
    if not (base_url and model and api_key):
        return None
    return {
        'base_url': base_url,
        'model': model,
        'api_key': api_key,
        'timeout': timeout,
    }


def normalize_filter_ext(filter_ext_raw):
    if not filter_ext_raw:
        return None
    if isinstance(filter_ext_raw, str):
        items = [item.strip().lower() for item in filter_ext_raw.split(',') if item.strip()]
    elif isinstance(filter_ext_raw, list):
        items = [str(item).strip().lower() for item in filter_ext_raw if str(item).strip()]
    else:
        return None

    normalized = []
    for ext in items:
        if not ext.startswith('.'):
            ext = '.' + ext
        normalized.append(ext)
    return sorted(set(normalized)) if normalized else None


def is_running_in_docker():
    if os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv'):
        return True

    cgroup_path = '/proc/1/cgroup'
    try:
        with open(cgroup_path, 'r', encoding='utf-8') as file_obj:
            cgroup_text = file_obj.read()
        return any(token in cgroup_text for token in ('docker', 'containerd', 'kubepods'))
    except OSError:
        return False


def get_effective_allowed_root():
    allowed_root = os.getenv('MUSIC_CLEANER_ALLOWED_PATH', '').strip()
    if allowed_root:
        return os.path.abspath(allowed_root)
    if is_running_in_docker():
        return '/media'
    return ''


def get_default_path_mode_path():
    return get_effective_allowed_root()


def build_runtime_config():
    default_path = get_default_path_mode_path()
    return {
        'in_docker': is_running_in_docker(),
        'default_path': default_path,
        'defaultPath': default_path,
    }


def build_asset_versions(static_root):
    asset_names = (
        'app.css',
        'app.js',
        os.path.join('js', 'state.js'),
        os.path.join('js', 'methods.js'),
        os.path.join('js', 'methods', 'common.js'),
        os.path.join('js', 'methods', 'settings.js'),
        os.path.join('js', 'methods', 'upload.js'),
        os.path.join('js', 'methods', 'path.js'),
        os.path.join('js', 'methods', 'files.js'),
    )
    versions = {}
    for asset_name in asset_names:
        asset_path = os.path.join(static_root, asset_name)
        try:
            versions[asset_name] = str(int(os.path.getmtime(asset_path)))
        except OSError:
            versions[asset_name] = '0'
    return versions


def serialize_keyword_settings(lyrics_processor):
    return {
        'keywords': lyrics_processor.get_header_keywords(),
        'default_keywords': lyrics_processor.get_default_keywords(),
        'saved_at': lyrics_processor.last_saved_at,
    }


def resolve_display_name(filename, mapped_original_path=None):
    if mapped_original_path:
        return os.path.basename(mapped_original_path)
    basename = os.path.basename(filename)
    if '_' in basename and len(basename.split('_')) >= 3:
        parts = basename.split('_', 2)
        if parts[0].isdigit() and parts[1].isdigit():
            return parts[2]
    return basename


def resolve_download_name(filename, mapped_original_path=None):
    if not filename.startswith('cleaned_'):
        return os.path.basename(filename)
    internal_filename = filename[8:]
    return resolve_display_name(internal_filename, mapped_original_path)


def resolve_archive_name(filename, mapped_original_path=None):
    if not filename.startswith('cleaned_'):
        return filename
    internal_filename = filename[8:]
    if mapped_original_path:
        return mapped_original_path
    path_parts = internal_filename.split(os.sep)
    if path_parts:
        path_parts[-1] = resolve_display_name(path_parts[-1])
        return os.sep.join(path_parts)
    return internal_filename


def export_failed_files_report(failed_files, output_path):
    with open(output_path, 'w', encoding='utf-8') as file_obj:
        file_obj.write('MusicMetaCleaner - 失败文件列表\n')
        file_obj.write('=' * 50 + '\n')
        file_obj.write(f'导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        file_obj.write(f'失败文件总数: {len(failed_files)}\n')
        file_obj.write('=' * 50 + '\n\n')
        for index, failed_file in enumerate(failed_files, 1):
            file_obj.write(f"{index}. {failed_file['filename']}: {failed_file['error']}\n")
        file_obj.write('\n' + '=' * 50 + '\n')
        file_obj.write('导出完成\n')
