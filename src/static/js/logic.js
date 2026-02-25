document.addEventListener('DOMContentLoaded', () => {
  // 요소 존재 여부 확인을 위한 셀렉터
  const getEl = (id) => document.getElementById(id);
  
  const roiStart = getEl('roiStart');
  const roiLog = getEl('roiLog');
  const videoFeed = getEl('video-feed');
  const videoUploader = getEl('videoUploader');
  const uploadTrigger = getEl('uploadTrigger');

  // [사이드바 이동 로직]
  document.querySelectorAll('.sidebar a').forEach(a => {
    a.addEventListener('click', (e) => {
      const targetPage = a.dataset.page;
      if (targetPage === 'playback') {
        window.location.href = '/monitoring';
        return; 
      } else if (targetPage === 'overview') {
        window.location.href = '/';
        return;
      }
      // 기본 동작 (단일 페이지 앱인 경우만 작동)
      e.preventDefault();
      showPage(targetPage);
    });
  });

  // [방어적 코드] 요소가 있는 페이지(인덱스)에서만 실행
  if (roiStart && roiLog && videoFeed) {
      let roiMode = false;
      let roiPoints = [];

      roiStart.addEventListener('click', () => {
          roiMode = true;
          roiStart.textContent = 'ROI 설정 중...';
      });

      videoFeed.addEventListener('click', (e) => {
          if(!roiMode) return;
          const rect = videoFeed.getBoundingClientRect();
          const x = (e.clientX - rect.left) / rect.width;
          const y = (e.clientY - rect.top) / rect.height;
          roiPoints.push({ x, y });
          roiLog.textContent = roiPoints.map((p, i) => `#${i+1} x:${p.x.toFixed(2)}`).join('\n');
      });
  }

  if (videoUploader && uploadTrigger) {
      uploadTrigger.addEventListener('click', () => videoUploader.click());
  }

  // 초기 렌더링 상태 표시
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar a').forEach(link => {
      if (path === '/monitoring' && link.dataset.page === 'playback') link.classList.add('active');
      else if (path === '/' && link.dataset.page === 'overview') link.classList.add('active');
  });
});