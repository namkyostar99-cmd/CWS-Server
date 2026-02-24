import os
from flask import Flask, render_template, jsonify, request
from database import init_db, save_violation_to_db, get_all_violations

app = Flask(__name__)

# 전역 변수로 스트리밍 주소 관리 (초기값은 플레이스홀더)
streaming_url = "http://210.99.70.120:1935/live/cctv006.stream/playlist.m3u8"

with app.app_context():
    init_db()

@app.route('/')
def index():
    """홈 화면: 이제 여기서도 스트리밍 화면을 보여줍니다."""
    global streaming_url
    return render_template('content/index.html', 
                           active_page='overview', 
                           current_stream=streaming_url)

@app.route('/monitoring')
def monitoring():
    """모니터링 화면"""
    global streaming_url
    violations = get_all_violations()
    return render_template('content/monitoring.html', 
                           active_page='live', 
                           violations=violations,
                           current_stream=streaming_url)

@app.route('/api/set_stream', methods=['POST'])
def set_stream():
    """설정창에서 입력한 URL을 서버에 저장하고 반환"""
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