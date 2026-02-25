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

  // navigation
  document.querySelectorAll('.sidebar a').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      document.querySelectorAll('.sidebar a').forEach(x => x.classList.remove('active'));
      a.classList.add('active');
      showPage(a.dataset.page);
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
    // fetch('/api/roi', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(roiPoints) })
    alert(`좌표 ${roiPoints.length}개 저장됨`);
  });

  videoFeed.addEventListener('click', (e) => {
    if(!roiMode) return;
    const rect = videoFeed.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    roiPoints.push({ x, y, px: Math.round(e.clientX - rect.left), py: Math.round(e.clientY - rect.top) });
    setRoiLog();
  });

  let currentObjectUrl = null;

  videoUploader.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if(!file) return;
    if(currentObjectUrl){
      URL.revokeObjectURL(currentObjectUrl);
      currentObjectUrl = null;
    }
    const url = URL.createObjectURL(file);
    currentObjectUrl = url;
    videoFeed.src = url;
  });

  uploadTrigger.addEventListener('click', () => {
    // allow re-uploading the same file by resetting input value
    videoUploader.value = '';
    videoUploader.click();
  });

  // Playback: Add new violation card dynamically
  // TODO: Flask에서는 서버에서 위반 데이터를 받아와서 동적으로 추가
  // fetch('/api/violations').then(res => res.json()).then(data => { ... })
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
  showPage('live');
  setRoiLog();

  document.addEventListener('DOMContentLoaded', function() {
    // 위반기록 조회 버튼(data-page="playback")을 찾아 클릭 이벤트 추가
    const dbMenuBtn = document.querySelector('a[data-page="playback"]');
    
    if (dbMenuBtn) {
        dbMenuBtn.addEventListener('click', function(e) {
            // 기존 logic.js의 기본 동작(e.preventDefault 등)이 있다면 무시하고 강제 이동
            e.preventDefault(); 
            window.location.href = '/monitoring';
        });
    }

    // 추가로 Live Feeds(data-page="overview") 클릭 시 홈으로 이동 보장
    const liveMenuBtn = document.querySelector('a[data-page="overview"]');
    if (liveMenuBtn) {
        liveMenuBtn.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/';
        });
    }
 });

});

