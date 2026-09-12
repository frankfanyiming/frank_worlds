// Embedded by export-native-web.py. Keep startup errors visible before loading Godot.
const lang = new URLSearchParams(location.search).get('lang') || 'zh-CN';
const copy = {
  'zh-CN': ['正在下载世界…', '连接中断，请重试', '重新载入', '正在打开场景…', '正在加载引擎…'],
  'zh-TW': ['正在下載世界…', '連線中斷，請重試', '重新載入', '正在開啟場景…', '正在載入引擎…'],
  en: ['Downloading the world…', 'Connection interrupted. Please retry.', 'Retry', 'Opening the scene…', 'Loading the engine…'],
  ja: ['世界をダウンロードしています…', '接続が切れました。再試行してください。', '再試行', 'シーンを開いています…', 'エンジンを読み込んでいます…'],
  ko: ['세계를 내려받고 있어요…', '연결이 끊겼어요. 다시 시도해 주세요.', '다시 시도', '장면을 여는 중…', '엔진을 불러오는 중…'],
}[lang] || ['Downloading…', 'Unable to connect. Please retry.', 'Retry', 'Opening…', 'Loading engine…'];
document.documentElement.lang = lang;
const statusPanel = document.querySelector('#status');
const label = document.querySelector('#label');
const progressBar = document.querySelector('#progress');
const percent = document.querySelector('#percent');
const retryButton = document.querySelector('#retry');
retryButton.textContent = copy[2];
let progress = 0, lastPublished = 0, failed = false, ready = false;
let queuedSound = new URLSearchParams(location.search).get('sound') === '1';
const controllers = new Set();

function update(value, stage, force = false) {
  if (failed || ready) return;
  progress = Math.max(progress, Math.min(99, value));
  if (!force && Date.now() - lastPublished < 120) return;
  lastPublished = Date.now();
  progressBar.value = progress;
  document.querySelector('.aptx-capsule')?.style?.setProperty('--download', progress + '%');
  percent.textContent = Math.floor(progress) + '%';
  if (stage) label.textContent = stage;
  parent.postMessage({type: 'xlands-progress', progress, detail: label.textContent}, '*');
}
function fail(error) {
  if (failed || ready) return;
  failed = true;
  for (const controller of controllers) controller.abort();
  console.error(error);
  label.textContent = copy[1];
  retryButton.hidden = false;
  parent.postMessage({type: 'xlands-error'}, '*');
}
function deadline(promise, ms, onTimeout = () => {}) {
  let timer;
  return Promise.race([
    promise,
    new Promise((_, reject) => {
      timer = setTimeout(() => { onTimeout(); reject(Error('Download timed out')); }, ms);
    }),
  ]).finally(() => clearTimeout(timer));
}
window.addEventListener('error', e => fail(e.error || Error(e.message || 'Engine error')));
window.addEventListener('unhandledrejection', e => fail(e.reason));
window.addEventListener('pagehide', () => { for (const c of controllers) c.abort(); });
window.addEventListener('message', e => {
  if (e.source !== parent) return;
  if (e.data?.type === 'xlands-sound') {
    queuedSound = !!e.data.enabled;
    window.xlandsSound?.(queuedSound);
  }
});
// Each surface owns its pointer. Joystick, camera and action fingers are independent.
function installTouchControls() {
  const controls = {
    'zh-CN': ['移动','拖动画面转视角','跑步','互动','跳跃','视角'],
    'zh-TW': ['移動','拖動畫面轉視角','跑步','互動','跳躍','視角'],
    en: ['Move','Drag the scene to look','Run','Interact','Jump','View'],
    ja: ['移動','画面をドラッグして見回す','走る','調べる','ジャンプ','視点'],
    ko: ['이동','화면을 끌어 둘러보기','달리기','상호작용','점프','시점'],
  }[lang] || ['Move','Drag to look','Run','Interact','Jump','View'];
  const stick = document.querySelector('#touch-stick'), canvas = document.querySelector('#canvas');
  if (!stick?.addEventListener || !canvas?.addEventListener) return;
  const knob = stick.querySelector('.touch-stick-knob');
  let moveId = null, look = null, menuOpen = false, panelLocked = false;
  const blocked = () => menuOpen || panelLocked;
  const held = new Map();
  for (const el of document.querySelectorAll('[data-touch-copy]')) el.textContent = controls[Number(el.dataset.touchCopy)];
  stick.setAttribute('aria-label', controls[0]);
  const move = event => {
    if (event.pointerId !== moveId) return;
    const box = stick.getBoundingClientRect(), radius = box.width * .32;
    let x = (event.clientX - box.left - box.width / 2) / radius, y = (event.clientY - box.top - box.height / 2) / radius;
    const length = Math.hypot(x, y); if (length > 1) { x /= length; y /= length; }
    knob.style.transform = `translate(${x * radius}px, ${y * radius}px)`;
    window.xlandsMove?.(length < .13 ? 0 : x, length < .13 ? 0 : y);
  };
  const endMove = event => { if (event.pointerId !== moveId) return; moveId = null; knob.style.transform = ''; window.xlandsMove?.(0, 0); };
  stick.addEventListener('pointerdown', event => { if (blocked() || moveId !== null) return; event.preventDefault(); moveId = event.pointerId; stick.setPointerCapture(event.pointerId); move(event); });
  stick.addEventListener('pointermove', move);
  for (const type of ['pointerup','pointercancel','lostpointercapture']) stick.addEventListener(type, endMove);
  for (const button of document.querySelectorAll('[data-action]')) {
    const action = button.dataset.action, pointers = new Set(); held.set(button, pointers);
    if (action === 'jump') { button.textContent = controls[4]; button.setAttribute('aria-label', controls[4]); }
    button.addEventListener('pointerdown', event => {
      if (blocked()) return;
      event.preventDefault(); button.setPointerCapture(event.pointerId); pointers.add(event.pointerId); button.classList.add('held');
      window.xlandsInput?.(action, true);
    });
    const release = event => {
      if (!pointers.delete(event.pointerId) || pointers.size) return;
      button.classList.remove('held'); window.xlandsInput?.(action, false);
    };
    for (const type of ['pointerup','pointercancel','lostpointercapture']) button.addEventListener(type, release);
  }
  canvas.addEventListener('pointerdown', event => { if (blocked() || event.pointerType !== 'touch' || look) return; look = {id:event.pointerId, x:event.clientX, y:event.clientY}; canvas.setPointerCapture(event.pointerId); });
  canvas.addEventListener('pointermove', event => {
    if (blocked() || !look || look.id !== event.pointerId) return;
    const dx = event.clientX - look.x, dy = event.clientY - look.y; look.x = event.clientX; look.y = event.clientY;
    window.xlandsLook?.(dx, dy);
  });
  const endLook = event => { if (look?.id === event.pointerId) look = null; };
  for (const type of ['pointerup','pointercancel','lostpointercapture']) canvas.addEventListener(type, endLook);
  function reset() {
    moveId = null; look = null; knob.style.transform = ''; window.xlandsMove?.(0, 0);
    for (const [button, pointers] of held) { pointers.clear(); button.classList.remove('held'); window.xlandsInput?.(button.dataset.action, false); }
  }
  const sheet = document.createElement('div'); sheet.className = 'native-menu'; sheet.hidden = true;
  const card = document.createElement('section'); card.className = 'native-menu-card'; card.setAttribute('role','dialog'); card.setAttribute('aria-modal','true');
  const heading = document.createElement('header'), title = document.createElement('h2'), close = document.createElement('button');
  title.id = 'native-menu-title'; card.setAttribute('aria-labelledby',title.id); close.textContent = '×';
  close.setAttribute('aria-label', {'zh-CN':'关闭菜单','zh-TW':'關閉選單',ja:'メニューを閉じる',ko:'메뉴 닫기',en:'Close menu'}[lang] || 'Close menu');
  heading.append(title,close); const items = document.createElement('div'); items.className = 'native-menu-items'; card.append(heading,items); sheet.append(card); document.body.append(sheet);
  const cancelMenu = () => window.xlandsMenuAction?.(-1);
  close.addEventListener('click',cancelMenu); sheet.addEventListener('click',event=>{if(event.target===sheet)cancelMenu();});
  const syncLock = () => {document.body.classList.toggle('world-ui-open',blocked()); if(blocked())reset();};
  window.xlandsOverlayLocked = locked => {panelLocked=!!locked;syncLock();};
  window.xlandsMenu = data => {
    menuOpen=!!data; sheet.hidden=!menuOpen; syncLock();
    if(!data)return;
    title.textContent=data.title; items.replaceChildren(); items.scrollTop=0;
    for(const item of data.items){
      const row=document.createElement(item.separator?'div':'button'); row.textContent=item.text;
      if(item.separator)row.className='native-menu-section';
      else {row.disabled=!!item.disabled;row.addEventListener('click',()=>window.xlandsMenuAction?.(item.id));}
      items.append(row);
    }
    close.focus({preventScroll:true});
  };
  window.addEventListener('blur', reset); window.addEventListener('pagehide', reset); window.addEventListener('resize', reset);
  document.addEventListener('visibilitychange', () => { if (document.hidden) reset(); });
}
installTouchControls();
if (typeof location.pathname === 'string' && location.pathname.includes('/conan/')) document.body?.classList.add('conan');

async function loadEngineScript() {
  if (typeof Engine !== 'undefined') return;
  const script = document.createElement('script');
  script.src = 'index.js';
  await deadline(new Promise((resolve, reject) => {
    script.onload = resolve;
    script.onerror = () => reject(Error('Engine script unavailable'));
    document.head.appendChild(script);
  }), 45000, () => script.remove());
}

// Preserve bytes already received on a broken connection. A 200 response to a
// resumed request means Range is unsupported, so restart that chunk safely.
async function downloadChunk(chunk, onProgress) {
  const encoded = new Uint8Array(chunk.bytes);
  let received = 0;
  const url = chunk.file + '?v=' + chunk.sha256;
  for (let attempt = 0; attempt < 3; attempt++) {
    const controller = new AbortController();
    controllers.add(controller);
    try {
      const response = await deadline(fetch(url, {
        signal: controller.signal,
        headers: received ? { Range: 'bytes=' + received + '-' } : {},
      }), 30000, () => controller.abort());
      if (!response.ok || !response.body) throw Error('Download failed: ' + response.status);
      if (response.status === 206) {
        const range = /^bytes (\d+)-(\d+)\/(\d+)$/.exec(response.headers.get('Content-Range') || '');
        if (!range || Number(range[1]) !== received || Number(range[3]) !== chunk.bytes)
          throw Error('Invalid download range');
      } else {
        received = 0;
        onProgress(0);
      }
      const reader = response.body.getReader();
      while (true) {
        const {done, value} = await deadline(reader.read(), 30000, () => controller.abort());
        if (done) break;
        if (received + value.length > encoded.length) { received = 0; throw Error('Unexpected chunk size'); }
        encoded.set(value, received);
        received += value.length;
        onProgress(received);
      }
      if (received !== chunk.bytes) throw Error('Incomplete chunk');
      const raw = new Uint8Array(await new Response(
        new Response(encoded).body.pipeThrough(new DecompressionStream('gzip')),
      ).arrayBuffer());
      const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', raw)))
        .map(b => b.toString(16).padStart(2, '0')).join('');
      if (raw.length !== chunk.rawBytes || digest !== chunk.sha256) throw Error('Corrupt chunk');
      return raw;
    } catch (error) {
      controller.abort();
      if (received === chunk.bytes) received = 0; // Full but invalid: re-download.
      if (attempt === 2 || failed) throw error;
    } finally {
      controllers.delete(controller);
    }
  }
  throw Error('Download failed');
}

async function load() {
  update(1, copy[4], true);
  await loadEngineScript();
  if (Engine.getMissingFeatures({threads: false}).length) throw Error('WebGL2 unavailable');
  const controller = new AbortController();
  controllers.add(controller);
  let descriptor;
  try {
    descriptor = await deadline(fetch('world-pack.json', {signal: controller.signal, cache: 'no-store'}).then(r => {
      if (!r.ok) throw Error('World manifest unavailable');
      return r.json();
    }), 20000, () => controller.abort());
  } finally { controllers.delete(controller); }
  const bytes = new Uint8Array(descriptor.totalBytes);
  const downloaded = descriptor.chunks.map(() => 0);
  const totalDownload = descriptor.chunks.reduce((sum, chunk) => sum + chunk.bytes, 0);
  let cursor = 0, engineProgress = 0;
  function report() {
    const complete = downloaded.reduce((sum, size) => sum + size, 0);
    update(3 + engineProgress * 10 + complete / totalDownload * 80,
      copy[0] + ' ' + (complete / 1048576).toFixed(1) + ' / ' + (totalDownload / 1048576).toFixed(1) + ' MB');
  }
  const engine = new Engine({...config, canvas: document.querySelector('#canvas'), locale: lang,
    canvasResizePolicy: 2,
    onProgress: (loaded, total) => { engineProgress = total ? Math.min(1, loaded / total) : 0; report(); },
    onPrint: text => {
      console.log(text);
      if (text.includes('_READY')) {
        ready = true;
        document.body.classList.add('world-ready');
        statusPanel.remove();
        window.xlandsSound?.(queuedSound);
        parent.postMessage({type: 'xlands-ready'}, '*');
      }
    },
    onPrintError: text => console.warn(text),
    onExit: code => { if (code !== 0) fail(Error('Engine exited: ' + code)); },
  });
  async function next() {
    while (cursor < descriptor.chunks.length && !failed) {
      const index = cursor++, chunk = descriptor.chunks[index];
      const data = await downloadChunk(chunk, size => { downloaded[index] = size; report(); });
      bytes.set(data, chunk.offset);
    }
  }
  await Promise.all([
    deadline(engine.init('index'), 180000), next(), next(), next(),
  ]);
  if (failed) return;
  update(94, copy[3], true);
  await engine.preloadFile(bytes.buffer, 'index.pck');
  update(96, copy[3], true);
  await deadline(engine.start({args: ['--main-pack', 'index.pck']}), 90000);
}
load().catch(fail);
