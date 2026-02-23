from flask import Flask, jsonify, request
# 파일명이 database.py이므로 아래와 같이 임포트합니다.
from database import init_db, save_violation_to_db, get_all_violations

app = Flask(__name__)

# 1. 서버 시작 시 DB 테이블 초기화 (데이터베이스 이니셜라이제이션 출력 확인용)
init_db()

# --- [HTML UI: DB 데이터를 4열로 출력하는 인덱스 페이지] ---
def get_dashboard_html():
    return """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>CWS 중앙 관제 시스템</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #0b0b0b; color: #f0f0f0; padding: 20px; font-family: 'Malgun Gothic', sans-serif; }
            .header-bar { background: #dc3545; color: white; padding: 15px; font-weight: bold; border-radius: 8px; margin-bottom: 30px; text-align: center; border: 1px solid #ff4d4d; }
            .violation-card { background: #1a1a1a; border: 1px solid #333; border-radius: 12px; transition: 0.3s; height: 100%; }
            .violation-card:hover { border-color: #dc3545; transform: translateY(-5px); box-shadow: 0 4px 20px rgba(220, 53, 69, 0.2); }
            .btn-evidence { background-color: #dc3545; border: none; color: white; width: 100%; margin-top: 15px; font-weight: bold; }
            .btn-evidence:hover { background-color: #a71d2a; }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="header-bar">🚨 CWS 2026 REAL-TIME TRAFFIC VIOLATION MONITORING</div>
            
            <div id="log-grid" class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4">
                <div class="col-12 text-center text-muted py-5">데이터 로딩 중...</div>
            </div>
        </div>

        <script>
            function fetchLogs() {
                fetch('/get_status')
                .then(res => res.json())
                .then(data => {
                    const grid = document.getElementById('log-grid');
                    if (data.length === 0) {
                        grid.innerHTML = '<div class="col-12 text-center text-muted py-5"><h3>수신된 위반 데이터가 없습니다.</h3></div>';
                        return;
                    }

                    grid.innerHTML = data.map(item => `
                        <div class="col">
                            <div class="violation-card p-3 shadow">
                                <h6 class="text-danger fw-bold mb-3">TRAFFIC VIOLATION</h6>
                                <p class="small mb-1"><span class="text-secondary">TRACK ID:</span> <strong>${item.track_id}</strong></p>
                                <p class="small mb-3"><span class="text-secondary">TIME:</span> ${item.timestamp}</p>
                                <a href="${item.url}" target="_blank" class="btn btn-sm btn-evidence">증거 확인</a>
                            </div>
                        </div>
                    `).join('');
                });
            }
            // 2초마다 DB 내용을 새로고침
            setInterval(fetchLogs, 2000);
            fetchLogs();
        </script>
    </body>
    </html>
    """

# --- [서버 라우팅 로직] ---

@app.route('/')
def index():
    # 이제 'Hello World' 대신 실제 대시보드 화면을 반환합니다.
    return get_dashboard_html()

@app.route('/api/v1/update', methods=['POST'])
def update():
    data = request.json
    if data:
        # 2. 수신된 데이터를 database.py의 함수를 통해 저장
        save_violation_to_db(
            track_id=data.get('track_id'),
            timestamp=data.get('timestamp'),
            filename=data.get('filename', 'EXTERNAL_LINK'),
            url=data.get('url')
        )
        print(f"[*] 데이터 수신 및 DB 저장 완료: ID {data.get('track_id')}")
    return jsonify({"status": "success"}), 200

@app.route('/get_status')
def get_status():
    # 3. database.py에서 전체 기록 조회
    rows = get_all_violations()
    # sqlite3.Row 객체들을 JSON으로 보낼 수 있게 딕셔너리로 변환
    return jsonify([dict(row) for row in rows])

if __name__ == '__main__':
    # 5000번 포트로 실행
    app.run(host='0.0.0.0', port=5000)