import sqlite3

def get_db_connection():
    conn = sqlite3.connect('cws_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 테이블 1: 스트리밍 URL 및 ROI 설정 (설정용)
    cursor.execute('''CREATE TABLE IF NOT EXISTS stream_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stream_url TEXT NOT NULL UNIQUE,
                        roi_points TEXT
                    )''')
    # 테이블 2: 위반 기록 (기록용)
    cursor.execute('''CREATE TABLE IF NOT EXISTS violations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        plate_number TEXT,
                        timestamp TEXT,
                        location TEXT,
                        evidence_url TEXT
                    )''')
    conn.commit()
    conn.close()

# 위반 기록 저장 (기존 함수 유지)
def save_violation_to_db(title, plate, time, loc, img_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO violations (title, plate_number, timestamp, location, evidence_url)
                      VALUES (?, ?, ?, ?, ?)''', (title, plate, time, loc, img_url))
    conn.commit()
    conn.close()

# 테이블 데이터 동적 조회를 위한 함수
def get_table_data_from_db(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    # 보안상 허용된 테이블만 조회
    if table_name not in ['stream_config', 'violations']:
        return []
    cursor.execute(f'SELECT * FROM {table_name} ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# 인덱스 페이지 통계 및 목록용
def get_all_violations():
    return get_table_data_from_db('violations')

def get_all_stream_configs():
    return get_table_data_from_db('stream_config')