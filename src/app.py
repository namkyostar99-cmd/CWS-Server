from flask import Flask, render_template, jsonify, request
from database import init_db, save_violation_to_db, get_all_violations

app = Flask(__name__, 
            static_folder='../static', 
            template_folder='../templates')

# 서버 시작 시 DB 초기화 (MySQL)
init_db()

# --- [페이지 렌더링 경로] ---

@app.route('/')
def index():
    """홈 화면 (index.html)"""
    return render_template('index.html', active_page='overview')

@app.route('/monitoring')
def monitoring():
    """실시간 모니터링 화면 (monitoring.html)"""
    # 초기 렌더링 시 DB에서 최신 위반 내역을 가져와 전달할 수 있습니다.
    violations = get_all_violations()
    return render_template('monitoring.html', active_page='live', violations=violations)

# --- [API 엔드포인트: logic.js 및 Edge와 통신] ---

@app.route('/api/v1/update', methods=['POST'])
def receive_edge_data():
    """Edge PC로부터 위반 데이터를 수신하여 DB에 저장"""
    data = request.json
    if data:
        save_violation_to_db(
            track_id=data.get('track_id'),
            timestamp=data.get('timestamp'),
            filename=data.get('filename', 'EXTERNAL_LINK'),
            url=data.get('url')
        )
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "fail"}), 400

@app.route('/get_status')
@app.route('/api/violations')
def get_violations():
    """DB에 저장된 위반 내역을 JSON으로 반환 (logic.js에서 사용)"""
    rows = get_all_violations()
    # MySQL DictCursor 결과는 이미 리스트-딕셔너리 형태입니다.
    return jsonify(rows)

@app.route('/api/roi', methods=['POST'])
def save_roi():
    """logic.js에서 전송한 ROI 좌표 저장"""
    roi_data = request.json
    print(f"[*] 수신된 ROI 좌표: {roi_data}")
    # TODO: DB에 ROI 좌표를 저장하는 로직을 추가할 수 있습니다.
    return jsonify({"status": "success", "message": "ROI saved"})

if __name__ == '__main__':
    # 시스템 서비스 등록을 고려하여 host와 port 설정
    app.run(host='0.0.0.0', port=5000, debug=False)