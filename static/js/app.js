/* ============================================================
   BIBIUNION — app.js
   1.  Router
   2.  Upload fichiers
   3.  Onglets upload
   4.  Capture photo   (+ review avant envoi)
   5.  Enregistrement vidéo (+ review)
   6.  Enregistrement audio (+ review)
   7.  Galerie mixte + scroll infini + temps réel
   8.  Lightbox + Filmstrip + Swipe + Drag
   9.  Diaporama
   10. Administration
   ============================================================ */
'use strict';

const SWIPE_THRESHOLD   = 50;
const REALTIME_INTERVAL = 15000;

/* ── 1. ROUTER ── */
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('upload-form'))     initUploadPage();
  if (document.getElementById('gallery-grid'))    initGalleryPage();
  if (document.querySelector('.admin-container')) initAdminPage();
});

/* ══════════════════════════════════════════════════════════
   2. PAGE UPLOAD
   ══════════════════════════════════════════════════════════ */
function initUploadPage() {
  const form             = document.getElementById('upload-form');
  const dropzone         = document.getElementById('dropzone');
  const fileInput        = document.getElementById('file-input');
  const previewContainer = document.getElementById('preview-container');
  const submitBtn        = document.getElementById('submit-btn');
  const summary          = document.getElementById('upload-summary');
  const summaryText      = document.getElementById('summary-text');
  const addMoreBtn       = document.getElementById('add-more-btn');

  let selectedFiles = [];

  initUploadTabs();

  ['dragenter','dragover'].forEach(ev =>
    dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.add('dragover'); })
  );
  ['dragleave','drop'].forEach(ev =>
    dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.remove('dragover'); })
  );
  dropzone.addEventListener('drop', e => addFiles(Array.from(e.dataTransfer.files)));
  fileInput.addEventListener('change', () => { addFiles(Array.from(fileInput.files)); fileInput.value = ''; });

  /* Entrée depuis les modules capture */
  window._addCapturedFile = (file, type) => addFiles([file], type);

  function detectType(file) {
    if (file.type.startsWith('image/') || /\.heic$/i.test(file.name)) return 'photo';
    if (file.type.startsWith('video/')) return 'video';
    if (file.type.startsWith('audio/')) return 'audio';
    return 'photo';
  }

  function addFiles(files, forceType = null) {
    files.forEach(file => {
      const type  = forceType || detectType(file);
      const id    = 'f_' + Math.random().toString(36).slice(2, 9);
      const entry = { id, file, type, status: 'pending', thumbnail: null,
                      duration: file._duration || null };
      selectedFiles.push(entry);
      renderPreview(entry);
    });
    updateSubmitBtn();
  }

  function renderPreview(entry) {
    const { id, file, type } = entry;
    const item = document.createElement('div');
    item.className = 'preview-item'; item.dataset.id = id;

    if (type === 'photo') {
      const img = document.createElement('img'); img.alt = 'Aperçu';
      if (!file.name.toLowerCase().endsWith('.heic')) {
        const r = new FileReader();
        r.onload = e => { img.src = e.target.result; };
        r.readAsDataURL(file);
      } else {
        item.textContent = '📷';
        item.style.cssText = 'display:flex;align-items:center;justify-content:center;font-size:2rem;';
      }
      item.appendChild(img);

    } else if (type === 'video') {
      item.classList.add('preview-item--video');
      const badge = document.createElement('div');
      badge.className = 'media-type-badge'; badge.textContent = '🎬';
      item.appendChild(badge);
      snapVideoThumbnail(file).then(res => {
        if (!res) return;
        const img = document.createElement('img');
        img.src = res.dataUrl;
        img.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;object-fit:cover;';
        item.insertBefore(img, badge);
        entry.thumbnail = res.blob;
      });

    } else {
      item.classList.add('preview-item--audio');
      item.textContent = '🎵';
      item.style.cssText = 'display:flex;align-items:center;justify-content:center;font-size:2rem;';
    }

    const rm = document.createElement('button');
    rm.type = 'button'; rm.className = 'preview-remove'; rm.innerHTML = '&times;';
    rm.setAttribute('aria-label', 'Retirer');
    rm.addEventListener('click', () => {
      selectedFiles = selectedFiles.filter(f => f.id !== id);
      item.remove(); updateSubmitBtn();
    });
    item.appendChild(rm);

    const pw = document.createElement('div'); pw.className = 'preview-progress';
    const pb = document.createElement('div'); pb.className = 'preview-progress-bar';
    pw.appendChild(pb); item.appendChild(pw);
    previewContainer.appendChild(item);
  }

  function updateSubmitBtn() {
    const p = selectedFiles.filter(f => f.status === 'pending' || f.status === 'error');
    submitBtn.disabled    = p.length === 0;
    submitBtn.textContent = p.length
      ? `Envoyer ${p.length} souvenir${p.length > 1 ? 's' : ''}`
      : 'Envoyer';
  }

  form.addEventListener('submit', e => {
    e.preventDefault();
    const auteur   = document.getElementById('auteur').value.trim();
    const table    = document.getElementById('table').value;
    const csrf     = form.querySelector('[name=csrfmiddlewaretoken]').value;
    const toUpload = selectedFiles.filter(f => f.status === 'pending' || f.status === 'error');
    if (!toUpload.length) return;
    submitBtn.disabled = true; submitBtn.textContent = 'Envoi en cours…';
    let done = 0, ok = 0;
    toUpload.forEach(entry => {
      uploadOne(entry, auteur, table, csrf, () => {
        done++; if (entry.status === 'success') ok++;
        if (done === toUpload.length) onAllDone(ok, toUpload.length);
      });
    });
  });

  function uploadOne(entry, auteur, table, csrf, cb) {
    const item = previewContainer.querySelector(`[data-id="${entry.id}"]`);
    const pb   = item?.querySelector('.preview-progress-bar');
    const fd   = new FormData();
    fd.append('auteur', auteur); fd.append('table', table);
    let url;
    if (entry.type === 'photo') {
      fd.append('image', entry.file); url = window.UPLOAD_URL;
    } else {
      fd.append('file', entry.file);
      fd.append('media_type', entry.type);
      if (entry.duration)   fd.append('duration',  String(Math.round(entry.duration)));
      if (entry.thumbnail)  fd.append('thumbnail', entry.thumbnail, 'thumb.jpg');
      url = window.UPLOAD_MEDIA_URL;
    }
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('X-CSRFToken', csrf);
    xhr.upload.onprogress = e => {
      if (e.lengthComputable && pb) pb.style.width = (e.loaded/e.total*100)+'%';
    };
    xhr.onload = () => {
      try {
        const res = JSON.parse(xhr.responseText);
        if (xhr.status === 200 && res.success) { entry.status='success'; markStatus(item,'success','✓'); }
        else { entry.status='error'; markStatus(item,'error','✗',res.error); }
      } catch { entry.status='error'; markStatus(item,'error','✗','Erreur'); }
      cb();
    };
    xhr.onerror = () => { entry.status='error'; markStatus(item,'error','✗','Réseau'); cb(); };
    xhr.send(fd);
  }

  function markStatus(item, cls, icon, msg) {
    if (!item) return;
    const el = document.createElement('div');
    el.className = `preview-status ${cls}`; el.textContent = icon;
    if (msg) el.title = msg; item.appendChild(el);
  }

  function onAllDone(ok, total) {
    form.style.display = 'none'; summary.style.display = 'block';
    summaryText.textContent = ok === total
      ? `${ok} souvenir${ok>1?'s':''} envoyé${ok>1?'s':''} avec succès 💛`
      : `${ok}/${total} réussi${ok>1?'s':''} — relancez pour les erreurs.`;
  }

  addMoreBtn?.addEventListener('click', () => {
    selectedFiles = []; previewContainer.innerHTML = '';
    form.style.display='block'; summary.style.display='none';
    submitBtn.disabled=true; submitBtn.textContent='Envoyer';
  });
}

/* Helper snapshot vidéo */
function snapVideoThumbnail(file) {
  return new Promise(resolve => {
    const url = URL.createObjectURL(file);
    const v   = document.createElement('video');
    v.muted = true; v.preload = 'metadata'; v.src = url;
    v.addEventListener('loadeddata', () => { v.currentTime = 0.5; });
    v.addEventListener('seeked', () => {
      const c = document.createElement('canvas');
      c.width  = 320;
      c.height = v.videoHeight ? Math.round(v.videoHeight/v.videoWidth*320) : 180;
      c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      c.toBlob(blob => resolve({ dataUrl: c.toDataURL('image/jpeg',.8), blob }), 'image/jpeg', .8);
    }, { once: true });
    v.addEventListener('error', () => { URL.revokeObjectURL(url); resolve(null); });
  });
}

/* ══════════════════════════════════════════════════════════
   3. ONGLETS UPLOAD
   ══════════════════════════════════════════════════════════ */
function initUploadTabs() {
  const tabs   = document.querySelectorAll('.upload-tab');
  const panels = document.querySelectorAll('.tab-panel');
  tabs.forEach(tab => tab.addEventListener('click', () => {
    tabs.forEach(t  => { t.classList.remove('active'); t.setAttribute('aria-selected','false'); });
    panels.forEach(p => p.classList.remove('active'));
    tab.classList.add('active'); tab.setAttribute('aria-selected','true');
    document.getElementById('tab-'+tab.dataset.tab)?.classList.add('active');
    if (tab.dataset.tab==='camera'    && !tab._init) { initCameraCapture();  tab._init=true; }
    if (tab.dataset.tab==='video-rec' && !tab._init) { initVideoCapture();   tab._init=true; }
    if (tab.dataset.tab==='audio-rec' && !tab._init) { initAudioCapture();   tab._init=true; }
  }));
}

/* ══════════════════════════════════════════════════════════
   4. CAPTURE PHOTO + REVIEW
   ══════════════════════════════════════════════════════════ */
function initCameraCapture() {
  const preview      = document.getElementById('camera-preview');
  const canvas       = document.getElementById('camera-canvas');
  const btnStart     = document.getElementById('btn-start-camera');
  const btnSnap      = document.getElementById('btn-snap');
  const btnFlip      = document.getElementById('btn-flip-camera');
  const controls     = document.getElementById('camera-controls');
  const review       = document.getElementById('camera-review');
  const reviewImg    = document.getElementById('camera-review-img');
  const btnRetry     = document.getElementById('btn-camera-retry');
  const btnAccept    = document.getElementById('btn-camera-accept');
  if (!preview) return;

  let stream = null, facing = 'environment';
  let capturedBlob = null;

  async function startCam() {
    try {
      stream?.getTracks().forEach(t => t.stop());
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facing, width:{ideal:1280}, height:{ideal:720} }, audio: false,
      });
      preview.srcObject = stream;
      btnSnap.disabled = false; btnFlip.disabled = false;
      btnStart.textContent = 'Recadrer';
      showCapture();
    } catch (err) { alert(`Caméra inaccessible : ${err.message}`); }
  }

  function showCapture() {
    preview.style.display = 'block'; controls.style.display = 'flex';
    review.style.display = 'none';
  }

  function showReview(blob) {
    capturedBlob = blob;
    reviewImg.src = URL.createObjectURL(blob);
    review.style.display = 'flex';
    preview.style.display = 'none'; controls.style.display = 'none';
  }

  btnStart.addEventListener('click', startCam);
  btnFlip.addEventListener('click', () => {
    facing = facing === 'environment' ? 'user' : 'environment'; startCam();
  });

  btnSnap.addEventListener('click', () => {
    if (!stream) return;
    const w = preview.videoWidth||1280, h = preview.videoHeight||720;
    canvas.width=w; canvas.height=h;
    canvas.getContext('2d').drawImage(preview,0,0,w,h);
    canvas.toBlob(blob => {
      preview.style.filter='brightness(2)';
      setTimeout(()=>preview.style.filter='',120);
      showReview(blob);
    }, 'image/jpeg', 0.9);
  });

  btnRetry.addEventListener('click', () => {
    capturedBlob = null; showCapture();
  });

  btnAccept.addEventListener('click', () => {
    if (!capturedBlob) return;
    const file = new File([capturedBlob], `photo_${Date.now()}.jpg`, { type:'image/jpeg' });
    window._addCapturedFile(file, 'photo');
    capturedBlob = null; showCapture();
  });
}

/* ══════════════════════════════════════════════════════════
   5. ENREGISTREMENT VIDÉO + REVIEW
   ══════════════════════════════════════════════════════════ */
function initVideoCapture() {
  const preview        = document.getElementById('video-rec-preview');
  const timerEl        = document.getElementById('video-rec-timer');
  const btnStart       = document.getElementById('btn-start-video');
  const btnRecord      = document.getElementById('btn-record-video');
  const btnStop        = document.getElementById('btn-stop-video');
  const btnRecadrer    = document.getElementById('btn-recadrer-video');
  const btnFlip        = document.getElementById('btn-flip-video');
  const controls       = document.getElementById('video-controls');
  const review         = document.getElementById('video-review');
  const reviewPlayer   = document.getElementById('video-review-player');
  const btnRetry       = document.getElementById('btn-video-retry');
  const btnAccept      = document.getElementById('btn-video-accept');
  if (!preview) return;

  let stream=null, recorder=null, chunks=[], elapsed=0, timerInt=null;
  let capturedFile=null, capturedThumb=null;
  let facing='user';   // selfie par défaut

  function showCapture() {
    preview.style.display='block'; controls.style.display='flex';
    review.style.display='none'; reviewPlayer.pause(); reviewPlayer.src='';
  }

  function showReview(file, thumb) {
    capturedFile=file; capturedThumb=thumb;
    reviewPlayer.src=URL.createObjectURL(file);
    review.style.display='flex';
    preview.style.display='none'; controls.style.display='none';
  }

  async function startCam() {
    try {
      stream?.getTracks().forEach(t=>t.stop());
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facing, width:{ideal:1280}, height:{ideal:720} },
        audio: true,
      });
      preview.srcObject=stream;
      btnRecord.disabled=false; btnRecadrer.disabled=false; btnFlip.disabled=false;
      btnStart.textContent='Caméra active';
    } catch(err) { alert(`Caméra inaccessible : ${err.message}`); }
  }

  btnStart.addEventListener('click', startCam);

  /* Recadrer = relance la caméra (stoppe l'enregistrement en cours si besoin) */
  btnRecadrer.addEventListener('click', ()=>{
    if (recorder && recorder.state==='recording') {
      recorder.stop();
      clearInterval(timerInt);
      if(timerEl) timerEl.textContent='00:00';
      btnRecord.disabled=false; btnStop.disabled=true;
    }
    startCam();
  });

  /* Flip = bascule selfie ↔ caméra arrière */
  btnFlip.addEventListener('click', ()=>{
    facing = facing==='user'?'environment':'user';
    startCam();
  });

  btnRecord.addEventListener('click', () => {
    if (!stream) return;
    chunks=[]; elapsed=0;
    const mime = bestMime(['video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/webm','video/mp4']);
    recorder = new MediaRecorder(stream, mime?{mimeType:mime}:{});
    recorder.ondataavailable = e => { if(e.data.size>0) chunks.push(e.data); };

    recorder.onstop = () => {
      clearInterval(timerInt);
      const bMime = recorder.mimeType;
      const ext   = bMime.includes('webm')?'webm':'mp4';
      const blob  = new Blob(chunks,{type:bMime});
      const file  = Object.assign(new File([blob],`video_${Date.now()}.${ext}`,{type:bMime}),{_duration:elapsed});

      /* Snapshot miniature depuis la préview */
      const c=document.createElement('canvas'); c.width=320; c.height=180;
      c.getContext('2d').drawImage(preview,0,0,320,180);
      c.toBlob(thumb => showReview(file,thumb), 'image/jpeg',.8);

      btnRecord.disabled=false; btnStop.disabled=true;
      if(timerEl) timerEl.textContent='00:00';
    };
    recorder.start(500);
    btnRecord.disabled=true; btnStop.disabled=false;
    timerInt=setInterval(()=>{ elapsed++; if(timerEl) timerEl.textContent=formatTime(elapsed); },1000);
  });

  btnStop.addEventListener('click', () => recorder?.stop());

  btnRetry.addEventListener('click', () => {
    capturedFile=null; capturedThumb=null; showCapture();
  });

  btnAccept.addEventListener('click', () => {
    if (!capturedFile) return;
    const f = Object.assign(capturedFile, {_thumbBlob: capturedThumb});
    window._addCapturedFile(f, 'video');
    capturedFile=null; capturedThumb=null; showCapture();
  });
}

/* ══════════════════════════════════════════════════════════
   6. ENREGISTREMENT AUDIO + REVIEW
   ══════════════════════════════════════════════════════════ */
function initAudioCapture() {
  const timerEl      = document.getElementById('audio-rec-timer');
  const waveform     = document.getElementById('audio-waveform');
  const btnRecord    = document.getElementById('btn-record-audio');
  const btnStop      = document.getElementById('btn-stop-audio');
  const controls     = document.getElementById('audio-controls');
  const review       = document.getElementById('audio-review');
  const reviewPlayer = document.getElementById('audio-review-player');
  const btnRetry     = document.getElementById('btn-audio-retry');
  const btnAccept    = document.getElementById('btn-audio-accept');
  const bars         = waveform ? Array.from(waveform.querySelectorAll('.waveform-bar')) : [];
  if (!btnRecord) return;

  let stream=null, recorder=null, chunks=[], elapsed=0, timerInt=null;
  let analyser=null, animFrame=null;
  let capturedFile=null;

  function showCapture() {
    controls.style.display='flex';
    review.style.display='none'; reviewPlayer.pause(); reviewPlayer.src='';
    waveform?.classList.remove('recording');
    bars.forEach(b=>b.style.height='8px');
  }

  function showReview(file) {
    capturedFile=file;
    reviewPlayer.src=URL.createObjectURL(file);
    review.style.display='flex'; controls.style.display='none';
  }

  btnRecord.addEventListener('click', async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({audio:true});
      const actx = new (window.AudioContext||window.webkitAudioContext)();
      const src  = actx.createMediaStreamSource(stream);
      analyser   = actx.createAnalyser(); analyser.fftSize=64;
      src.connect(analyser); animateWave();

      chunks=[]; elapsed=0;
      const mime = bestMime(['audio/webm;codecs=opus','audio/ogg;codecs=opus','audio/mp4']);
      recorder = new MediaRecorder(stream, mime?{mimeType:mime}:{});
      recorder.ondataavailable = e => { if(e.data.size>0) chunks.push(e.data); };

      recorder.onstop = () => {
        clearInterval(timerInt); cancelAnimationFrame(animFrame);
        stream.getTracks().forEach(t=>t.stop());
        const bMime = recorder.mimeType;
        const ext   = bMime.includes('webm')?'webm':bMime.includes('mp4')?'m4a':'ogg';
        const file  = Object.assign(
          new File([new Blob(chunks,{type:bMime})],`vocal_${Date.now()}.${ext}`,{type:bMime}),
          {_duration:elapsed}
        );
        showReview(file);
        btnRecord.disabled=false; btnStop.disabled=true;
        if(timerEl) timerEl.textContent='00:00';
      };

      recorder.start(500);
      waveform?.classList.add('recording');
      btnRecord.disabled=true; btnStop.disabled=false;
      timerInt=setInterval(()=>{ elapsed++; if(timerEl) timerEl.textContent=formatTime(elapsed); },1000);
    } catch(err) { alert(`Microphone inaccessible : ${err.message}`); }
  });

  btnStop.addEventListener('click', () => recorder?.stop());

  btnRetry.addEventListener('click', () => { capturedFile=null; showCapture(); });
  btnAccept.addEventListener('click', () => {
    if (!capturedFile) return;
    window._addCapturedFile(capturedFile, 'audio');
    capturedFile=null; showCapture();
  });

  function animateWave() {
    if (!analyser||!bars.length) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    function draw() {
      analyser.getByteFrequencyData(data);
      bars.forEach((b,i)=>{ b.style.height=Math.max(4,(data[i%data.length]||0)*56/255)+'px'; });
      animFrame=requestAnimationFrame(draw);
    }
    draw();
  }
}

function bestMime(types) { return types.find(t=>MediaRecorder.isTypeSupported(t))||''; }
function formatTime(s)   { return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`; }

/* ══════════════════════════════════════════════════════════
   7. PAGE GALERIE
   ══════════════════════════════════════════════════════════ */
function initGalleryPage() {
  const grid        = document.getElementById('gallery-grid');
  const loader      = document.getElementById('gallery-loader');
  const empty       = document.getElementById('gallery-empty');
  const filterTable = document.getElementById('filter-table');
  const filterDate  = document.getElementById('filter-date');
  const resetBtn    = document.getElementById('reset-filters');
  const toggleSlide = document.getElementById('toggle-slideshow');
  const typeBtns    = document.querySelectorAll('.filter-type-btn');

  let allItems=[], currentPage=1, hasNext=true, loading=false, lastId=0, activeType='all';

  loadItems();

  window.addEventListener('scroll', () => {
    if (loading||!hasNext) return;
    if (window.innerHeight+window.scrollY>=document.body.offsetHeight-400) { currentPage++; loadItems(); }
  });

  typeBtns.forEach(btn=>btn.addEventListener('click',()=>{
    typeBtns.forEach(b=>b.classList.remove('active'));
    btn.classList.add('active'); activeType=btn.dataset.type; resetAndReload();
  }));
  filterTable.addEventListener('change', resetAndReload);
  filterDate.addEventListener('change',  resetAndReload);
  resetBtn.addEventListener('click', ()=>{
    filterTable.value=''; filterDate.value='';
    typeBtns.forEach(b=>b.classList.remove('active'));
    typeBtns[0]?.classList.add('active'); activeType='all'; resetAndReload();
  });

  function resetAndReload() {
    currentPage=1; hasNext=true; allItems=[]; lastId=0;
    grid.innerHTML=''; empty.style.display='none'; loadItems();
  }

  function apiParams(extra={}) {
    return new URLSearchParams({
      page: currentPage, table: filterTable.value, date: filterDate.value,
      types: activeType==='all'?'photo,video,audio':activeType, ...extra,
    }).toString();
  }

  function loadItems() {
    if (loading) return;
    loading=true; loader.style.display='flex';
    fetch(`${window.GALLERY_DATA_URL}?${apiParams()}`)
      .then(r=>r.json())
      .then(data=>{
        loader.style.display='none'; loading=false; hasNext=data.has_next;
        if (!data.photos.length&&!allItems.length){ empty.style.display='block'; return; }
        data.photos.forEach(item=>{ allItems.push(item); if(item.id>lastId) lastId=item.id; renderItem(item); });
      })
      .catch(()=>{ loader.style.display='none'; loading=false; });
  }

  /* Temps réel */
  setInterval(()=>{
    if (!lastId) return;
    fetch(`${window.GALLERY_DATA_URL}?${apiParams({since_id:lastId})}`)
      .then(r=>r.json())
      .then(data=>{
        if (!data.photos?.length) return;
        data.photos.slice().reverse().forEach(item=>{
          if (item.id<=lastId) return;
          lastId=item.id; allItems.unshift(item);
          renderItem(item,true); empty.style.display='none';
        });
      }).catch(()=>{});
  }, REALTIME_INTERVAL);

  /* ── Rendu item ── */
  function renderItem(item, prepend=false) {
    const el = document.createElement('div');
    el.className='gallery-item'; el.dataset.id=item.id; el.dataset.type=item.type;
    el.setAttribute('role','listitem'); el.setAttribute('tabindex','0');

    if      (item.type==='photo') buildPhotoItem(el,item);
    else if (item.type==='video') buildVideoItem(el,item);
    else                          buildAudioItem(el,item);

    /* Badge type */
    const badge = document.createElement('span');
    badge.className='gallery-media-badge';
    badge.textContent = item.type==='photo'?'IMG':item.type==='video'?'VID':'AUD';
    el.appendChild(badge);

    /* Légende hover */
    const cap=document.createElement('div');
    cap.className='gallery-item-caption';
    cap.textContent=`${item.auteur}${item.table?' · '+item.table:''}`;
    el.appendChild(cap);

    el.addEventListener('click',   ()=>openLightbox(item.id));
    el.addEventListener('keydown', e=>{ if(e.key==='Enter'||e.key===' ') openLightbox(item.id); });

    prepend?grid.insertBefore(el,grid.firstChild):grid.appendChild(el);
  }

  function buildPhotoItem(el,item) {
    const img=document.createElement('img');
    img.src=item.thumbnail_url; img.loading='lazy'; img.alt='';
    img.className='gallery-thumb-img'; el.appendChild(img);
  }

  function buildVideoItem(el,item) {
    const img=document.createElement('img');
    img.className='gallery-thumb-img'; img.loading='lazy'; img.alt='';
    if (item.thumbnail_url) { img.src=item.thumbnail_url; }
    else { img.style.display='none'; el.style.background='linear-gradient(135deg,#3d2b1f,#6b4f3a)'; }
    el.appendChild(img);

    /* Vidéo hover 5s muet */
    const hv=document.createElement('video');
    hv.className='hover-video'; hv.src=item.file_url;
    hv.muted=true; hv.loop=false; hv.preload='none'; hv.playsInline=true;
    el.appendChild(hv);
    el.addEventListener('mouseenter',()=>{ hv.currentTime=0; hv.play().catch(()=>{}); hv._t=setTimeout(()=>hv.pause(),5000); });
    el.addEventListener('mouseleave',()=>{ clearTimeout(hv._t); hv.pause(); hv.currentTime=0; });
  }

  function buildAudioItem(el,item) {
    el.classList.add('gallery-item--audio');
    const icon=document.createElement('div'); icon.className='audio-gallery-icon'; icon.textContent='🎵';
    const barsWrap=document.createElement('div'); barsWrap.className='audio-gallery-bars';
    for(let i=0;i<8;i++){
      const b=document.createElement('span'); b.style.height=(4+Math.random()*18)+'px'; barsWrap.appendChild(b);
    }
    el.append(icon,barsWrap);
  }


  /* ════════════════════════════════════════════════════════
     8. LIGHTBOX + FILMSTRIP + SWIPE + DRAG
     ════════════════════════════════════════════════════════ */
  const lightbox      = document.getElementById('lightbox');
  const mediaWrap     = document.getElementById('lightbox-media-wrap');
  const captionEl     = document.getElementById('lightbox-caption');
  const btnClose      = document.getElementById('lightbox-close');
  const btnPrev       = document.getElementById('lightbox-prev');
  const btnNext       = document.getElementById('lightbox-next');
  const filmstripTrack= document.getElementById('filmstrip-track');

  let currentIndex=0;

  function openLightbox(itemId) {
    currentIndex=allItems.findIndex(i=>i.id===itemId);
    if (currentIndex===-1) return;
    buildFilmstrip();
    showCurrent();
    lightbox.style.display='flex';
    document.body.style.overflow='hidden';
    btnClose.focus();
  }

  function closeLightbox() {
    mediaWrap.querySelector('video')?.pause();
    mediaWrap.querySelector('audio')?.pause();
    lightbox.style.display='none';
    document.body.style.overflow='';
    stopSlideshow();
  }

  /* ── Filmstrip ── */
  function buildFilmstrip() {
    filmstripTrack.innerHTML='';
    allItems.forEach((item,idx)=>{
      const thumb=document.createElement('div');
      thumb.className='filmstrip-thumb';
      if (idx===currentIndex) thumb.classList.add('active');
      thumb.dataset.idx=idx;

      if (item.type==='photo') {
        const img=document.createElement('img'); img.src=item.thumbnail_url; img.alt='';
        thumb.appendChild(img);
      } else if (item.type==='video') {
        if (item.thumbnail_url) {
          const img=document.createElement('img'); img.src=item.thumbnail_url; img.alt='';
          thumb.appendChild(img);
        } else {
          /* mini préview vidéo au survol */
          const v=document.createElement('video');
          v.src=item.file_url; v.muted=true; v.preload='none'; v.playsInline=true;
          thumb.appendChild(v);
          thumb.addEventListener('mouseenter',()=>{ v.currentTime=0; v.play().catch(()=>{}); });
          thumb.addEventListener('mouseleave',()=>{ v.pause(); v.currentTime=0; });
        }
        const icon=document.createElement('span'); icon.className='fs-icon'; icon.textContent='🎬';
        thumb.appendChild(icon);
      } else {
        const icon=document.createElement('span'); icon.className='fs-icon'; icon.textContent='🎵';
        thumb.appendChild(icon);
      }

      /* Badge type */
      const badge=document.createElement('span'); badge.className='fs-badge';
      badge.textContent=item.type==='photo'?'IMG':item.type==='video'?'VID':'AUD';
      thumb.appendChild(badge);

      thumb.addEventListener('click',()=>{ currentIndex=idx; showCurrent(); updateFilmstripActive(); });
      filmstripTrack.appendChild(thumb);
    });
    scrollFilmstripToActive();
  }

  function updateFilmstripActive() {
    filmstripTrack.querySelectorAll('.filmstrip-thumb').forEach((t,i)=>{
      t.classList.toggle('active', i===currentIndex);
    });
    scrollFilmstripToActive();
  }

  function scrollFilmstripToActive() {
    const active=filmstripTrack.querySelector('.filmstrip-thumb.active');
    if (active) active.scrollIntoView({ behavior:'smooth', block:'nearest', inline:'center' });
  }

  /* ── Affiche l'item courant ── */
  function showCurrent() {
    const item=allItems[currentIndex]; if (!item) return;
    mediaWrap.querySelector('video')?.pause();
    mediaWrap.querySelector('audio')?.pause();
    mediaWrap.innerHTML='';

    if (item.type==='photo') {
      const img=document.createElement('img'); img.src=item.full_url; img.alt=`Photo de ${item.auteur}`;
      mediaWrap.appendChild(img);
    } else if (item.type==='video') {
      const v=document.createElement('video');
      v.src=item.file_url; v.controls=true; v.autoplay=true; v.playsInline=true;
      v.style.cssText='max-width:92vw;max-height:72vh;';
      mediaWrap.appendChild(v);
    } else {
      const wrap=document.createElement('div'); wrap.className='lightbox-audio-wrapper';
      const icon=document.createElement('div'); icon.className='lightbox-audio-icon'; icon.textContent='🎵';
      const name=document.createElement('p'); name.style.cssText='color:white;font-size:.9rem;'; name.textContent=item.auteur;
      const a=document.createElement('audio'); a.src=item.file_url; a.controls=true; a.autoplay=true;
      a.style.width='min(380px,88vw)';
      wrap.append(icon,name,a); mediaWrap.appendChild(wrap);
    }

    captionEl.textContent=`${item.auteur}${item.table?' · '+item.table:''} — ${item.date_upload}`;
    updateFilmstripActive();
  }

  const goPrev=()=>{ currentIndex=(currentIndex-1+allItems.length)%allItems.length; showCurrent(); };
  const goNext=()=>{ currentIndex=(currentIndex+1)%allItems.length; showCurrent(); };

  btnClose.addEventListener('click', closeLightbox);
  btnPrev.addEventListener('click',  goPrev);
  btnNext.addEventListener('click',  goNext);
  lightbox.addEventListener('click', e=>{ if(e.target===lightbox) closeLightbox(); });

  document.addEventListener('keydown', e=>{
    if (lightbox.style.display!=='flex') return;
    if (e.key==='Escape')    closeLightbox();
    if (e.key==='ArrowLeft') goPrev();
    if (e.key==='ArrowRight')goNext();
  });

  /* ── Swipe tactile ── */
  let tx0=0, ty0=0;
  lightbox.addEventListener('touchstart', e=>{ tx0=e.touches[0].clientX; ty0=e.touches[0].clientY; },{passive:true});
  lightbox.addEventListener('touchend',   e=>{
    const dx=e.changedTouches[0].clientX-tx0, dy=e.changedTouches[0].clientY-ty0;
    if (Math.abs(dx)<SWIPE_THRESHOLD||Math.abs(dy)>Math.abs(dx)) return;
    slideAnim(dx>0?'right':'left'); dx>0?goPrev():goNext();
  },{passive:true});

  /* ── Drag souris ── */
  let mx0=0, dragging=false;
  mediaWrap.addEventListener('mousedown', e=>{ mx0=e.clientX; dragging=true; mediaWrap.style.cursor='grabbing'; e.preventDefault(); });
  window.addEventListener('mousemove', e=>{ if(!dragging) return; mediaWrap.style.transform=`translateX(${(e.clientX-mx0)*.3}px)`; });
  window.addEventListener('mouseup',   e=>{
    if (!dragging) return; dragging=false; mediaWrap.style.cursor='';
    const dx=e.clientX-mx0;
    if (Math.abs(dx)>=SWIPE_THRESHOLD) { slideAnim(dx>0?'right':'left'); dx>0?goPrev():goNext(); }
    else {
      mediaWrap.style.transition='transform .2s ease';
      mediaWrap.style.transform='translateX(0)';
      setTimeout(()=>mediaWrap.style.transition='',200);
    }
  });

  function slideAnim(dir) {
    const out=dir==='left'?'-70px':'70px';
    mediaWrap.style.transition='transform .22s ease, opacity .22s';
    mediaWrap.style.transform=`translateX(${out})`; mediaWrap.style.opacity='0';
    setTimeout(()=>{
      mediaWrap.style.transition='';
      mediaWrap.style.transform=`translateX(${dir==='left'?'70px':'-70px'})`;
      requestAnimationFrame(()=>{
        mediaWrap.style.transition='transform .22s ease, opacity .22s';
        mediaWrap.style.transform='translateX(0)'; mediaWrap.style.opacity='1';
        setTimeout(()=>mediaWrap.style.transition='',240);
      });
    },220);
  }

  /* ════════════════════════════════════════════════════════
     9. DIAPORAMA
     ════════════════════════════════════════════════════════ */
  let slideshowTimer=null;

  toggleSlide?.addEventListener('change',()=>{
    toggleSlide.checked?startSlideshow():stopSlideshow();
  });

  function startSlideshow() {
    if (!allItems.length) return;
    currentIndex=0; buildFilmstrip(); showCurrent();
    lightbox.style.display='flex'; document.body.style.overflow='hidden';
    slideshowTimer=setInterval(goNext,4500);
  }

  function stopSlideshow() {
    clearInterval(slideshowTimer); slideshowTimer=null;
    if (toggleSlide) toggleSlide.checked=false;
  }
}

/* ══════════════════════════════════════════════════════════
   10. ADMINISTRATION
   ══════════════════════════════════════════════════════════ */
function initAdminPage() {
  document.querySelectorAll('.delete-btn').forEach(btn=>{
    btn.addEventListener('click', function(){
      if (!confirm('Supprimer définitivement ce fichier ?')) return;
      const id=this.dataset.id, type=this.dataset.type;
      const url=type==='photo'?`${window.DELETE_PHOTO_URL}${id}/`:`${window.DELETE_MEDIA_URL}${id}/`;
      fetch(url,{method:'POST',headers:{'X-CSRFToken':window.CSRF_TOKEN}})
        .then(r=>r.json())
        .then(data=>{
          if (data.success) document.querySelector(`.admin-card[data-id="${id}"]`)?.remove();
          else alert('Suppression échouée.');
        }).catch(()=>alert('Erreur réseau.'));
    });
  });
}
