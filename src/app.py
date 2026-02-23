import os
import mimetypes
from flask import Flask, render_template, request, jsonify, send_from_directory
from database import init_db, save_violation_to_db

# 브라우저 MIME 타입 호환성 설정
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

app = Flask(__name__, 
            static_url_path='', 
            static_folder='static', 
            template_folder='templates')

# 데이터베이스 초기화 (최초 실행 시 테이블 생성)
init_db()

# 실시간 로그를 담을 메모리 저장소 (세션 동안 유지)
violation_logs = []

# --- [Middleware: MIME 타입 강제 지정] ---
@app.after_request
def add_header(response):
    if request.path.endswith('.css'):
        response.headers['Content-Type'] = 'text/css'
    elif request.path.endswith('.js'):
        response.headers['Content-Type'] = 'application/javascript'
    return response

# --- [View Routing: 페이지 이동] ---

@app.route('/')
def index():
    """메인 대시보드 (Overview)"""
    return render_template('content/index.html')

@app.route('/monitoring.html')
def monitoring_page():
    """실시간 관제 페이지"""
    return render_template('content/monitoring.html')

@app.route('/login.html')
def login_page():
    return render_template('content/login.html')

# --- [API Layer: 데이터 수신 및 전달] ---

@app.route('/api/v1/update', methods=['POST'])
def receive_edge_data():
    """
    Edge PC로부터 위반 정보를 수신하는 API.
    Edge는 사진 파일이 아닌, 본인이 호스팅하는 상세페이지 URL을 보냅니다.
    """
    try:
        data = request.json
        track_id = data.get('track_id')
        timestamp = data.get('timestamp')
        # Edge PC가 생성한 자체 상세페이지 URL (예: http://edge-ip:5001/evidence/...)
        edge_url = data.get('url') 

        # 1. DB 저장 (이전 database.py 구조 활용)
        # filename 자리에 'EXTERNAL_LINK'를 넣어 에지가 관리함을 표시
        save_violation_to_db(track_id, timestamp, "EXTERNAL_LINK", edge_url)

        # 2. 실시간 로그 갱신 (HTML 태그 포함)
        log_entry = f"[{timestamp[-8:]}] ID {track_id} 위반 " \
                    f"<a href='{edge_url}' target='_blank' style='color:#ff6b6b; margin-left:5px;'>[보기]</a>"
        violation_logs.append(log_entry)
        
        # 로그는 최신 15개만 유지하여 메모리 관리
        if len(violation_logs) > 15:
            violation_logs.pop(0)

        print(f"[*] New Violation Recorded: ID {track_id} -> {edge_url}")
        return jsonify({"status": "success", "message": "Data recorded on Server"}), 200

    except Exception as e:
        print(f"[!] API Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_status')
def get_status():
    """프론트엔드에서 1초마다 호출하여 신호와 로그를 가져가는 API"""
    # 실제 신호 제어 로직이 서버에 없다면 Edge가 보낸 마지막 신호를 저장해서 반환해야 함
    # 여기서는 예시로 'RED'를 기본값으로 반환
    return jsonify({
        "signal": "RED", 
        "logs": violation_logs
    })

# --- [Static & Utils] ---

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # t2.micro 환경을 고려하여 debug는 False로 설정
    # 외부 접속 허용을 위해 0.0.0.0 사용
    app.run(host='0.0.0.0', port=5000, debug=False)