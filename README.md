# CWS-Server
**중앙 관제 서버**

---

## 1. 프로젝트 개요

CWS-Server는 CWS-Edge로부터 신호위반 데이터를 수신하여 DB에 저장하고,  
관제 요원이 실시간 영상 및 위반 기록을 웹 브라우저에서 확인할 수 있는 중앙 대시보드 서버입니다.

| 항목 | 내용 |
|------|------|
| 실행 포트 | `5000` |
| 배포 환경 | AWS EC2 |
| 주요 역할 | 위반 데이터 수신·저장, 대시보드 제공, 이미지 프록시 |
| 프레임워크 | Flask + Jinja2 Templates |
| DB | `cws_data.db` (SQLite) |
| 연동 서버 | CWS-Edge (ngrok 주소 또는 엣지 IP) |

---

## 2. 시스템 아키텍처

```
  [CCTV/HLS 스트림] ──────────────────────────────────┐
                                                       ↓
  [CWS-Edge :5001]                           [브라우저 (관제 요원)]
    ↓  POST /api/sync/violations                      ↑
    ↓  위반 데이터 전송                     HLS 스트림 + 대시보드
  [CWS-Server :5000]  ←────────────────────────────────┘
    - SQLite DB 저장
    - 이미지 프록시 (GET /view_evidence/<filename>)
    ↓  GET /api/get_evidence_file/<filename>
  [CWS-Edge :5001]
    - 증거 이미지 반환
```

---

## 3. 파일 구조

```
CWS-Server/
└── src/
    ├── app.py                     # Flask 라우트 (핵심)
    ├── database.py                # SQLite CRUD
    ├── static/
    │   ├── css/styles.css
    │   ├── js/logic.js            # 사이드바·ROI 설정 JS
    │   └── images/
    └── templates/
        ├── layout.html            # 공통 레이아웃
        ├── common/
        │   ├── header.html
        │   ├── nav.html
        │   └── footer.html
        └── content/
            ├── index.html         # Live Feeds 페이지
            └── monitoring.html    # 위반기록 조회 페이지
```

---

## 4. 설치 및 실행

### 4-1. 의존성 설치

```bash
pip install flask requests
```

### 4-2. 설정 변경

`src/app.py` 상단의 두 값을 환경에 맞게 수정하세요.

```python
# 엣지 서버 주소 — ngrok 주소 또는 엣지 IP:5001
EDGE_SERVER_URL = "https://xxxx.ngrok-free.dev"

# 기본 스트리밍 URL (DB에 없을 때 사용)
DEFAULT_STREAM_URL = "http://210.99.70.120:1935/live/cctv006.stream/playlist.m3u8"
```

### 4-3. 서버 실행

```bash
cd src
python app.py
# → http://0.0.0.0:5000 에서 실행됨
```

---

## 5. ngrok 주소 갱신 방법

> ⚠️ 엣지 PC에서 ngrok을 재시작하면 Forwarding 주소가 바뀝니다. 아래 절차에 따라 갱신하세요.

**① 엣지 PC의 ngrok 화면에서 새 주소 확인**

```
Forwarding  https://새주소.ngrok-free.dev -> http://localhost:5001
```

**② EC2에서 `app.py` 수정**

```python
EDGE_SERVER_URL = "https://새주소.ngrok-free.dev"
```

**③ Flask 재시작**

```bash
python app.py
```

---

## 6. API 엔드포인트

| Method | Endpoint | 호출자 | 설명 |
|--------|----------|--------|------|
| GET | `/` | 브라우저 | Live Feeds 대시보드 (HLS 플레이어 + 통계) |
| GET | `/monitoring` | 브라우저 | 위반기록 조회 페이지 |
| POST | `/api/sync/violations` | CWS-Edge | 위반 데이터 수신 및 DB 저장 |
| GET | `/api/get_table_data?type=` | 브라우저 | DB 테이블 동적 조회 (1: stream_config, 2: violations) |
| GET | `/view_evidence/<filename>` | 브라우저 | 엣지 이미지를 프록시하여 모달로 표시 |
| POST | `/api/set_stream` | 브라우저 | 스트리밍 URL 변경 (DB에 영속 저장) |
| GET | `/api/violations` | 브라우저 | 모든 위반 기록 JSON 반환 |
| POST | `/api/remote_set_roi` | 브라우저 | 중앙 서버에서 엣지 ROI 원격 설정 |

---

## 7. DB 스키마

### stream_config

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER (PK) | 자동 증가 |
| stream_url | TEXT UNIQUE | 스트리밍 URL |
| roi_points | TEXT | ROI 좌표 (JSON) |

### violations

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER (PK) | 자동 증가 |
| title | TEXT | 위반 유형 (예: 신호위반 감지) |
| plate_number | TEXT | 번호판 (현재 `ID-{obj_id}` 임시값) |
| timestamp | TEXT | 위반 발생 시각 |
| location | TEXT | 위반 발생 위치 |
| evidence_url | TEXT | 증거 이미지 파일명 |

---

## 8. 주요 수정 이력

| 항목 | 내용 |
|------|------|
| `streaming_url` 영속화 | 전역 변수 → DB 저장/로드 방식으로 변경 (재시작 후에도 유지) |
| 증거 이미지 팝업 → 모달 | `window.open()` 제거 → 페이지 내 모달로 교체 (팝업 차단 해결) |
| timeout 단축 | 이미지 프록시 timeout 60초 → 5초로 단축 |
| 에러 메시지 구체화 | `ConnectTimeout` / `ConnectionError` 별도 처리 |
| 원격 ROI API 추가 | `POST /api/remote_set_roi` — 중앙에서 엣지 ROI 원격 설정 가능 |
| ngrok 헤더 추가 | 이미지 프록시 요청에 `ngrok-skip-browser-warning` 헤더 추가 |

---

## 9. 실행 체크리스트

- [ ] `EDGE_SERVER_URL`을 엣지의 ngrok 주소로 변경
- [ ] `pip install flask requests` 완료 확인
- [ ] `python app.py` 실행
- [ ] 브라우저에서 `http://<EC2-IP>:5000` 접속 확인
- [ ] EC2 보안 그룹에서 5000 포트 인바운드 허용 확인
- [ ] 엣지에서 위반 발생 시 `/monitoring` 페이지에 데이터 수신 확인
