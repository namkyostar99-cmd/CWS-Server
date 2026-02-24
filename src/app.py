import os
from flask import Flask, render_template, jsonify, request
from database import init_db, save_violation_to_db, get_all_violations

# 이미지에서 확인된 src 폴더 내 구조 반영
app = Flask(__name__)

# 서버 기동 시 DB 초기화 (테이블 생성 등)
with app.app_context():
    init_db()

# --- [ 페이지 라우팅 ] ---

@app.route('/')
def index():
    """홈 화면 (index.html)"""
    return render_template('content/index.html', active_page='overview')

@app.route('/monitoring')
def monitoring():
    """모니터링 화면 (monitoring.html)"""
    # 초기 페이지 렌더링 시 최신 위반 데이터를 함께 전달
    try:
        data = get_all_violations()
    except Exception as e:
        print(f"Error fetching violations: {e}")
        data = []
    return render_template('content/monitoring.html', active_page='live', violations=data)

# --- [ API 엔드포인트 ] ---

@app.route('/api/v1/update', methods=['POST'])
def update_violation():
    """Edge PC로부터 새로운 위반 데이터를 수신하여 DB 저장"""
    data = request.json
    if not data:
        return jsonify({"result": "fail", "reason": "No JSON data"}), 400
    
    try:
        save_violation_to_db(
            track_id=data.get('track_id'),
            timestamp=data.get('timestamp'),
            filename=data.get('filename', 'Unknown'),
            url=data.get('url')
        )
        return jsonify({"result": "success"}), 200
    except Exception as e:
        print(f"DB Save Error: {e}")
        return jsonify({"result": "error", "message": str(e)}), 500

@app.route('/api/violations')
@app.route('/get_status')
def api_get_violations():
    """logic.js에서 실시간 데이터 갱신을 위해 호출하는 통로"""
    try:
        rows = get_all_violations()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/roi', methods=['POST'])
def api_save_roi():
    """logic.js에서 보낸 ROI 좌표 수신"""
    roi_points = request.json
    print(f"[*] Received ROI Points: {roi_points}")
    # 필요 시 여기서 DB 저장 로직 추가
    return jsonify({"status": "success", "received": len(roi_points)})

# --- [ 서버 실행 ] ---

if __name__ == '__main__':
    # EC2 외부 접속을 위해 0.0.0.0 허용
    app.run(host='0.0.0.0', port=5000, debug=True)