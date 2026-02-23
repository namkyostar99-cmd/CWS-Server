import sqlite3
import os

def get_db_connection():
    """데이터베이스 연결 객체 생성 및 반환"""
    # EC2 환경에서 경로 문제를 방지하기 위해 절대 경로 설정 권장
    db_path = os.path.join(os.path.dirname(__file__), '..', 'traffic_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 결과를 딕셔너리 형태로 반환받기 위함
    return conn

def init_db():
    """데이터베이스 테이블 초기화 (최초 1회 실행)"""
    conn = get_db_connection()
    c = conn.cursor()
    # url 컬럼은 Edge PC의 상세 페이지 주소를 저장합니다.
    c.execute('''CREATE TABLE IF NOT EXISTS violations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  track_id INTEGER, 
                  timestamp TEXT, 
                  filename TEXT, 
                  url TEXT)''')
    conn.commit()
    conn.close()
    print("[*] Database Initialized.")

def save_violation_to_db(track_id, timestamp, filename, url):
    """
    위반 내역 및 접근 URL 저장
    filename: 서버 저장 시 파일명 (현재 구조에선 'EXTERNAL_LINK' 등으로 기록 가능)
    url: Edge PC가 서빙하는 상세 페이지의 풀 주소 (http://edge-ip:5001/...)
    """
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO violations (track_id, timestamp, filename, url) VALUES (?, ?, ?, ?)",
                  (track_id, timestamp, filename, url))
        conn.commit()
    except Exception as e:
        print(f"[!] DB Save Error: {e}")
    finally:
        conn.close()

def get_all_violations():
    """웹 대시보드 조회를 위한 전체 기록 반환"""
    conn = get_db_connection()
    c = conn.cursor()
    rows = c.execute("SELECT * FROM violations ORDER BY id DESC").fetchall()
    conn.close()
    return rows