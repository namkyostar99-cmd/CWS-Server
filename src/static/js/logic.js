// Flask에서는 템플릿에서 url_for('static', filename='...') 형태로 경로 처리됨
// # 직접 참조가 필요한 경우: static 폴더의 상대 경로 사용
document.addEventListener('DOMContentLoaded', () => {
  const roiControls = document.getElementById('roiControls');
  const roiStart = document.getElementById('roiStart');
  const roiReset = document.getElementById('roiReset');
  const roiDone = document.getElementById('roiDone');
  const roiLog = document.getElementById('roiLog');
  const roiInfo = document.getElementById('roiInfo');
  const videoFeed = document.getElementById('video-feed');
  const videoUploader = document.getElementById('videoUploader');
  const uploadTrigger = document.getElementById('uploadTrigger');

  let roiMode = false;
  let roiPoints = [];

  function setActiveNav(page){
    document.querySelectorAll('.sidebar a').forEach(x => x.classList.remove('active'));
    const link = document.querySelector(`.sidebar a[data-page="${page}"]`);
    if(link) link.classList.add('active');
  }

  // [수정/추가됨] navigation: 기존 원본 구조를 유지하되 페이지 이동 로직 추가
  document.querySelectorAll('.sidebar a').forEach(a => {
    a.addEventListener('click', (e) => {
      // 1. 위반기록 조회(playback)나 Live Feeds(overview) 클릭 시 실제 페이지 이동
      const targetPage = a.dataset.page;
      
      if (targetPage === 'playback') {
        // e.preventDefault()를 무시하고 강제 이동
        window.location.href = '/monitoring';
        return; 
      } else if (targetPage === 'overview') {
        window.location.href = '/';
        return;
      }

      // 2. 그 외 기존 logic.js 동작 (단일 페이지 내 전환용)
      e.preventDefault();
      document.querySelectorAll('.sidebar a').forEach(x => x.classList.remove('active'));
      a.classList.add('active');
      showPage(targetPage);
    });
  });

  function showPage(page){
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    const el = document.getElementById(page);
    if(el) el.classList.remove('hidden');
    if(page === 'live'){
      document.querySelector('.status')?.classList.remove('hidden');
    } else {
      document.querySelector('.status')?.classList.add('hidden');
    }
  }

  function setRoiLog(){
    if(roiPoints.length === 0){
      roiLog.textContent = '(클릭 좌표가 여기에 표시됩니다)';
      return;
    }
    roiLog.textContent = roiPoints.map((p, i) => `#${i+1}  x:${p.x.toFixed(3)}  y:${p.y.toFixed(3)}  (px ${p.px}, ${p.py})`).join('\n');
  }

  roiStart.addEventListener('click', () => {
    roiMode = true;
    roiStart.textContent = 'ROI 설정 중...';
  });

  roiReset.addEventListener('click', () => {
    roiPoints = [];
    roiMode = false;
    roiStart.textContent = 'ROI 설정 시작';
    setRoiLog();
  });

  roiDone.addEventListener('click', () => {
    roiMode = false;
    roiStart.textContent = 'ROI 설정 시작';
    // TODO: Flask API로 ROI 좌표 전송
    alert(`좌표 ${roiPoints.length}개 저장됨`);
  });

  // videoFeed가 존재할 때만 리스너 등록 (에러 방지)
  if(videoFeed) {
    videoFeed.addEventListener('click', (e) => {
      if(!roiMode) return;
      const rect = videoFeed.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      roiPoints.push({ x, y, px: Math.round(e.clientX - rect.left), py: Math.round(e.clientY - rect.top) });
      setRoiLog();
    });
  }

  let currentObjectUrl = null;

  if(videoUploader) {
    videoUploader.addEventListener('change', (e) => {
      const file = e.target.files?.[0];
      if(!file) return;
      if(currentObjectUrl){
        URL.revokeObjectURL(currentObjectUrl);
        currentObjectUrl = null;
      }
      const url = URL.createObjectURL(file);
      currentObjectUrl = url;
      if(videoFeed) videoFeed.src = url;
    });
  }

  if(uploadTrigger) {
    uploadTrigger.addEventListener('click', () => {
      videoUploader.value = '';
      videoUploader.click();
    });
  }

  // Playback: Add new violation card dynamically
  window.addViolationCard = function(data) {
    const grid = document.getElementById('playbackGrid');
    if(!grid) return;
    
    const card = document.createElement('div');
    card.className = 'playback-card';
    card.innerHTML = `
      <div class="playback-img">${data.image || '차량 이미지'}</div>
      <div class="playback-info">
        <div class="playback-title">${data.title || '위반 종류'}</div>
        <div class="playback-meta">차량번호: ${data.plateNumber || '-'}</div>
        <div class="playback-meta">시간: ${data.time || '-'}</div>
        <div class="playback-meta">위치: ${data.location || '-'}</div>
      </div>
    `;
    grid.appendChild(card);
  };

  // initial render
  // 현재 URL 경로를 확인하여 페이지 초기 상태 설정
  const path = window.location.pathname;
  if(path === '/monitoring') {
    setActiveNav('playback');
    showPage('playback');
  } else {
    showPage('live');
    setRoiLog();
  }
});