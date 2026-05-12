import atexit
import logging
import os
import shutil

from flask import Flask, jsonify

from lyrics_utils import (
    clean_lyrics,
    get_lyrics_from_file,
    save_lyrics_to_file,
    is_audio_file,
    process_audio_file,
    lyrics_processor,
)
from routes import bp, temp_files
from services import build_runtime_config as _services_build_runtime_config
from services import get_effective_allowed_root as _services_get_effective_allowed_root
from services import is_running_in_docker as _services_is_running_in_docker
from storage import get_app_db_path as _storage_get_app_db_path
from storage import get_execution_log_path as _storage_get_execution_log_path
from storage import get_filename_mapping_path as _storage_get_filename_mapping_path
from storage import get_keyword_settings_path as _storage_get_keyword_settings_path
from storage import initialize_storage as _initialize_storage

app = Flask(__name__)
app.jinja_env.variable_start_string = '(('
app.jinja_env.variable_end_string = '))'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['KEYWORD_SETTINGS_FILENAME'] = '.lyrics-cleaner-keywords.json'
app.config['EXECUTION_LOG_FILENAME'] = '.execution-logs.json'
app.config['FILENAME_MAPPING_FILENAME'] = '.filename-mapping.json'
app.config['APP_DB_FILENAME'] = '.music-meta-cleaner.db'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000


def get_keyword_settings_path():
    return _storage_get_keyword_settings_path(app)


def get_execution_log_path():
    return _storage_get_execution_log_path(app)


def get_filename_mapping_path():
    return _storage_get_filename_mapping_path(app)


def get_app_db_path():
    return _storage_get_app_db_path(app)


def configure_keyword_settings_storage():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    lyrics_processor.configure_settings_path(get_keyword_settings_path())
    _initialize_storage(app)


def _is_running_in_docker():
    return _services_is_running_in_docker()


def _get_effective_allowed_root():
    return _services_get_effective_allowed_root()


def _build_runtime_config():
    return _services_build_runtime_config()


def cleanup_temp_files():
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                if os.path.isfile(temp_file):
                    os.remove(temp_file)
                elif os.path.isdir(temp_file):
                    shutil.rmtree(temp_file)
        except Exception as exc:
            app.logger.warning('清理临时文件失败 %s: %s', temp_file, exc)


configure_keyword_settings_storage()
atexit.register(cleanup_temp_files)


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': '上传文件过大，请检查服务器配置或减少文件数量'}), 413


app.register_blueprint(bp)
app.logger.setLevel(logging.INFO)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
