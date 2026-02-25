import os
from flask import Flask, render_template, jsonify, request
from database import init_db, save_violation_to_db, get_all_violations, get_table_data_from_db, get_all_stream_configs

app = Flask(__name__)

# 전역 변수
streaming_url = "http://210.99.70.120:1935/live/cctv006.stream/playlist.m3u8"

with app.app_context():
    init_db()

@app.route('/')
def index():
    global streaming_url
    violations = get_all_violations()
    # 인덱스 페이지의 목록 박스용 URL 리스트
    configs = get_all_stream_configs()
    return render_template('content/index.html', 
                           active_page='overview', 
                           violations=violations,
                           current_stream=streaming_url,
                           url_list=configs)

@app.route('/monitoring')
def monitoring():
    global streaming_url
    violations = get_all_violations()
    return render_template('content/monitoring.html', 
                           active_page='live', 
                           violations=violations,
                           current_stream=streaming_url)

# --- 신규 추가: 모니터링 페이지 동적 테이블 API ---
@app.route('/api/get_table_data')
def api_get_table_data():
    table_type = request.args.get('type') # '1' 또는 '2'
    table_name = 'stream_config' if table_type == '1' else 'violations'
    data = get_table_data_from_db(table_name)
    return jsonify({
        "table_name": table_name,
        "data": data
    })

# --- 신규 추가: 엣지로부터 위반 데이터 수신 API ---
@app.route('/api/sync/violations', methods=['POST'])
def sync_violations():
    data = request.json # 엣지에서 전송한 리스트
    if not data: return jsonify({"status": "fail"}), 400
    for item in data:
        save_violation_to_db(
            item.get('title', '위반'),
            item.get('plate_number', '-'),
            item.get('timestamp'),
            item.get('location', '-'),
            item.get('evidence_url')
        )
    return jsonify({"status": "success"})

@app.route('/api/set_stream', methods=['POST'])
def set_stream():
    global streaming_url
    data = request.json
    if data and 'url' in data:
        streaming_url = data['url']
        return jsonify({"status": "success", "url": streaming_url})
    return jsonify({"status": "fail"}), 400

@app.route('/api/violations')
def api_get_violations():
    return jsonify(get_all_violations())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)