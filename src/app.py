import os
import requests
import io
from flask import Flask, render_template, jsonify, request, send_file
from database import init_db, save_violation_to_db, get_all_violations, get_table_data_from_db, get_all_stream_configs, save_stream_url, get_latest_stream_url

app = Flask(__name__)

# [중요 설정] 엣지 서버의 주소 (본인의 엣지 PC 공인 IP 또는 내부 IP로 수정)
EDGE_SERVER_URL = "https://stacey-unjeweled-mindi.ngrok-free.dev"
# 기본 스트리밍 URL (DB에 저장된 값이 없을 때만 사용)
DEFAULT_STREAM_URL = "http://210.99.70.120:1935/live/cctv006.stream/playlist.m3u8"

with app.app_context():
    init_db()
    # [수정] 서버 시작 시 DB에서 마지막으로 저장된 URL 로드 (재시작 후에도 유지)
    streaming_url = get_latest_stream_url(DEFAULT_STREAM_URL)

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
@app.route('/view_evidence/<filename>')
def view_evidence(filename):
    """
    사용자가 증거보기를 누르면 호출됨.
    중앙 서버가 엣지 서버에 직접 접속하여 이미지를 가져온 뒤 사용자에게 전달.
    """
    try:
        # 엣지 서버의 이미지 파일 전송 엔드포인트 호출
        # ngrok 무료 플랜 경고 페이지 우회 헤더
        NGROK_HEADERS = {"ngrok-skip-browser-warning": "true"}
        edge_api_url = f"{EDGE_SERVER_URL}/api/get_evidence_file/{filename}"
        response = requests.get(edge_api_url, headers=NGROK_HEADERS, timeout=5)
        
        if response.status_code == 200:
            # 엣지로부터 받은 바이너리 데이터를 메모리에서 파일 객체로 변환하여 전송
            return send_file(
                io.BytesIO(response.content),
                mimetype='image/jpg'
            )
        else:
            return f"<h3>엣지 서버 응답 오류 (상태코드: {response.status_code})</h3>", 404
            
    except requests.exceptions.ConnectTimeout:
        return "<h3>엣지 서버 연결 타임아웃 — 방화벽/포트포워딩을 확인하세요 (port 5001)</h3>", 504
    except requests.exceptions.ConnectionError:
        return "<h3>엣지 서버에 연결할 수 없습니다 — 엣지 서버가 실행 중인지 확인하세요</h3>", 502
    except Exception as e:
        return f"<h3>오류: {e}</h3>", 500

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
        save_stream_url(streaming_url)  # [수정] DB에도 저장하여 재시작 후에도 유지
        return jsonify({"status": "success", "url": streaming_url})
    return jsonify({"status": "fail"}), 400

@app.route('/api/violations')
def api_get_violations():
    return jsonify(get_all_violations())

# [추가] 중앙 서버에서 Edge ROI를 원격으로 설정
@app.route('/api/remote_set_roi', methods=['POST'])
def remote_set_roi():
    """
    중앙 서버 UI에서 Edge의 ROI를 원격 제어.
    Body: { "points": [{px, py}, ...] }  — 4개 이상의 점 필요
    """
    data = request.json
    points = data.get('points') if data else None

    if not points or len(points) < 4:
        return jsonify({"status": "fail", "msg": "4개 이상의 점이 필요합니다."}), 400
    try:
        resp = requests.post(
            f"{EDGE_SERVER_URL}/api/set_roi",
            json={"points": points},
            timeout=5
        )
        return jsonify({"status": "success", "edge_response": resp.json()})
    except Exception as e:
        return jsonify({"status": "fail", "msg": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
