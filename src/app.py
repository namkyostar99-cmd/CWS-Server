import os
import requests
import io
from flask import Flask, render_template, jsonify, request, send_file
from database import init_db, save_violation_to_db, get_all_violations, get_table_data_from_db, get_all_stream_configs

app = Flask(__name__)

# [중요 설정] 엣지 서버의 주소 (본인의 엣지 PC 공인 IP 또는 내부 IP로 수정)
EDGE_SERVER_URL = "http://119.194.93.220:5001"
# 전역 변수
streaming_url = "http://210.99.70.120:1935/live/cctv006.stream/playlist.m3u8"

with app.app_context():
    init_db()

@app.route('/')
def index():
    global streaming_url
    violations = get_all_violations()
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

# --- [신규 추가] 엣지 서버 이미지 프록시 로직 ---
# EDGE_SERVER_URL은 엣지 서버의 공인 IP와 포트여야 합니다.

@app.route('/view_evidence/<filename>')
def view_evidence(filename):
    """
    중앙 서버가 엣지 서버의 /evidence/ 경로에서 이미지를 가져와 사용자에게 전달
    """
    try:
        # 1. 실제 이미지가 서빙되는 경로로 수정 (/api/get_evidence_file/ -> /evidence/)
        edge_api_url = f"{EDGE_SERVER_URL}/evidence/{filename}"
        
        # 2. 엣지 서버에 요청 (timeout은 연결 5초, 응답 대기 10초 정도로 설정 권장)
        response = requests.get(edge_api_url, timeout=(5, 10))
        
        if response.status_code == 200:
            # 엣지로부터 받은 바이너리 데이터를 메모리 버퍼에 담아 전송
            return send_file(
                io.BytesIO(response.content),
                mimetype='image/jpeg' # jpg의 정식 mimetype은 image/jpeg입니다.
            )
        else:
            return f"<h3>파일을 찾을 수 없습니다. (엣지 응답 코드: {response.status_code})</h3>", 404
            
    except requests.exceptions.ConnectTimeout:
        return "<h3>엣지 서버 연결 시간 초과: 서버가 꺼져있거나 방화벽/공유기 설정을 확인하세요.</h3>", 504
    except requests.exceptions.ConnectionError:
        return "<h3>엣지 서버 연결 거부: 주소가 틀렸거나 포트 포워딩이 안 되어 있습니다.</h3>", 502
    except Exception as e:
        return f"<h3>기타 오류 발생: {str(e)}</h3>", 500

# --- 모니터링 페이지 동적 테이블 API ---
@app.route('/api/get_table_data')
def api_get_table_data():
    table_type = request.args.get('type') # '1' 또는 '2'
    table_name = 'stream_config' if table_type == '1' else 'violations'
    data = get_table_data_from_db(table_name)
    return jsonify({
        "table_name": table_name,
        "data": data
    })

# --- 엣지로부터 위반 데이터 수신 API ---
@app.route('/api/sync/violations', methods=['POST'])
def sync_violations():
    data = request.json 
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
    
