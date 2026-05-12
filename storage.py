import json
import os
import sqlite3
from datetime import datetime


def _config_path(app, key, default_name):
    return os.path.join(app.config['UPLOAD_FOLDER'], app.config.get(key, default_name))


def get_keyword_settings_path(app):
    return _config_path(app, 'KEYWORD_SETTINGS_FILENAME', '.lyrics-cleaner-keywords.json')


def get_execution_log_path(app):
    return get_app_db_path(app)


def get_filename_mapping_path(app):
    return get_app_db_path(app)


def get_app_db_path(app):
    return _config_path(app, 'APP_DB_FILENAME', '.music-meta-cleaner.db')


def initialize_storage(app):
    db_path = get_app_db_path(app)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                mode TEXT NOT NULL,
                success_count INTEGER NOT NULL,
                failed_count INTEGER NOT NULL,
                ignored_count INTEGER NOT NULL,
                target_path TEXT NOT NULL,
                dry_run INTEGER NOT NULL,
                failed_files_json TEXT NOT NULL,
                ignored_files_json TEXT NOT NULL
            )
            '''
        )
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS filename_mappings (
                internal_name TEXT PRIMARY KEY,
                original_name TEXT NOT NULL
            )
            '''
        )
        conn.commit()


def load_execution_logs(app):
    initialize_storage(app)
    with sqlite3.connect(get_app_db_path(app)) as conn:
        rows = conn.execute(
            '''
            SELECT created_at, mode, success_count, failed_count, ignored_count,
                   target_path, dry_run, failed_files_json, ignored_files_json
            FROM execution_logs
            ORDER BY id DESC
            LIMIT 100
            '''
        ).fetchall()

    entries = []
    for row in rows:
        entries.append({
            'created_at': row[0],
            'mode': row[1],
            'success_count': row[2],
            'failed_count': row[3],
            'ignored_count': row[4],
            'target_path': row[5],
            'dry_run': bool(row[6]),
            'failed_files': json.loads(row[7]),
            'ignored_files': json.loads(row[8]),
        })
    return entries


def append_execution_log(app, mode, result, context=None):
    failed_files = list((result or {}).get('failed_files') or [])
    ignored_files = list((result or {}).get('ignored_files') or [])
    if not failed_files and not ignored_files:
        return None

    initialize_storage(app)
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

    with sqlite3.connect(get_app_db_path(app)) as conn:
        conn.execute(
            '''
            INSERT INTO execution_logs (
                created_at, mode, success_count, failed_count, ignored_count,
                target_path, dry_run, failed_files_json, ignored_files_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                entry['created_at'],
                entry['mode'],
                entry['success_count'],
                entry['failed_count'],
                entry['ignored_count'],
                entry['target_path'],
                int(entry['dry_run']),
                json.dumps(entry['failed_files'], ensure_ascii=False),
                json.dumps(entry['ignored_files'], ensure_ascii=False),
            )
        )
        conn.execute(
            '''
            DELETE FROM execution_logs
            WHERE id NOT IN (
                SELECT id FROM execution_logs ORDER BY id DESC LIMIT 100
            )
            '''
        )
        conn.commit()
    return entry


def set_filename_mapping(app, internal_name, original_name):
    initialize_storage(app)
    with sqlite3.connect(get_app_db_path(app)) as conn:
        conn.execute(
            '''
            INSERT OR REPLACE INTO filename_mappings (internal_name, original_name)
            VALUES (?, ?)
            ''',
            (str(internal_name), str(original_name))
        )
        conn.commit()


def get_filename_mapping(app, internal_name):
    initialize_storage(app)
    with sqlite3.connect(get_app_db_path(app)) as conn:
        row = conn.execute(
            'SELECT original_name FROM filename_mappings WHERE internal_name = ?',
            (str(internal_name),)
        ).fetchone()
    return row[0] if row else None
