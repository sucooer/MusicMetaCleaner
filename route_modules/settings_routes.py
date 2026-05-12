from datetime import datetime

from flask import current_app, render_template, request, jsonify, make_response

from lyrics_utils import lyrics_processor
from route_modules.base import bp
from services import build_asset_versions, build_runtime_config, serialize_keyword_settings
from storage import load_execution_logs


@bp.route('/')
def index():
    response = render_template(
        'index.html',
        runtime_config=build_runtime_config(),
        asset_versions=build_asset_versions(current_app.static_folder)
    )
    from flask import make_response
    resp = make_response(response)
    resp.headers['Cache-Control'] = 'no-store, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp
@bp.route('/settings/lyrics_keywords', methods=['GET', 'POST'])
def lyrics_keyword_settings():
    """获取或保存歌词清理关键词设置"""
    if request.method == 'GET':
        lyrics_processor.load_header_keywords()
        return jsonify(serialize_keyword_settings(lyrics_processor))

    data = request.get_json(silent=True) or {}
    keywords = data.get('keywords')
    if not isinstance(keywords, list):
        return jsonify({'error': 'keywords 必须是数组'}), 400

    saved_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        lyrics_processor.save_header_keywords(keywords, updated_at=saved_at)
    except (OSError, ValueError) as exc:
        return jsonify({'error': f'保存关键词失败: {str(exc)}'}), 500

    return jsonify(serialize_keyword_settings(lyrics_processor))
@bp.route('/execution_logs', methods=['GET'])
def execution_logs():
    """返回最近的执行日志"""
    limit_raw = request.args.get('limit', 20)
    try:
        limit = int(limit_raw)
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 100))

    entries = load_execution_logs(current_app)
    return jsonify({
        'logs': entries[:limit],
        'total': len(entries)
    })
