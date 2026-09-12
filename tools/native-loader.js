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
  window.xlandsOverlayLocked = locked => {panelLocked=!!locked;document.body.classList.toggle('world-ui-open',panelLocked);if(panelLocked)reset();};
  window.addEventListener('blur', reset); window.addEventListener('pagehide', reset); window.addEventListener('resize', reset);
  document.addEventListener('visibilitychange', () => { if (document.hidden) reset(); });
}
installTouchControls();
// Shared browser UI: one HUD and one accessible sheet, for mouse and touch.
function installWorldUI() {
  const words = {
    'zh-CN': ['散步手记','小世界','相册','行囊','朋友','探索与设置','关闭','拍一张照片','还没有旅行照片','把喜欢的一刻留在这里。照片与朋友的回忆会慢慢填满这本手记。','继续散步','三叶草','操作','行走','跑步','环视','跳跃','互动','视角','朋友日常','目的地','时间与视角'],
    'zh-TW': ['散步手記','小世界','相簿','行囊','朋友','探索與設定','關閉','拍一張照片','還沒有旅行照片','把喜歡的一刻留在這裡。照片與朋友的回憶會慢慢填滿這本手記。','繼續散步','三葉草','操作','行走','跑步','環視','跳躍','互動','視角','朋友日常','目的地','時間與視角'],
    en: ['Wander journal','Little world','Album','Bag','Friends','Explore & settings','Close','Take a photo','Your first memory awaits','Keep a moment you love. Your photos and days with friends will gradually fill these pages.','Keep wandering','Clovers','Controls','Walk','Run','Look','Jump','Interact','View','Days with friends','Places','Time & view'],
    ja: ['おさんぽ手帳','小さな世界','アルバム','旅じたく','友だち','探索と設定','閉じる','写真を撮る','はじめの一枚を待っています','好きな瞬間を残しましょう。写真と友だちとの思い出が、この手帳を少しずつ彩ります。','散歩を続ける','みつば','操作','歩く','走る','見回す','ジャンプ','調べる','視点','友だちとの日々','行き先','時間と視点'],
    ko: ['산책 수첩','작은 세계','앨범','가방','친구','탐험과 설정','닫기','사진 찍기','첫 추억을 기다려요','좋아하는 순간을 남겨 보세요. 사진과 친구들과의 추억이 이 수첩을 채워 갈 거예요.','계속 산책하기','클로버','조작','걷기','달리기','둘러보기','점프','상호작용','시점','친구와의 하루','목적지','시간과 시점'],
  }[lang] || [];
  const isFrog = location.pathname.includes('/frog/');
  const icons = {
    album:'<rect x="4" y="3" width="16" height="18" rx="3"/><path d="M8 3v18M11 14l3-3 4 5M12 8h.01"/>',
    bag:'<path d="M6 8h12l2 12H4L6 8Z"/><path d="M9 8V6a3 3 0 0 1 6 0v2M4 14h16"/>',
    friends:'<circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2M17 5a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 4v2"/>',
    menu:'<path d="M5 7h14M5 12h14M5 17h14"/>',
    close:'<path d="m6 6 12 12M18 6 6 18"/>',
    leaf:'<path d="M20 4C8 2 3 9 7 15c6 4 13-1 13-11ZM4 20l12-12"/>',
    camera:'<path d="M3 8h4l2-3h6l2 3h4v12H3V8Z"/><circle cx="12" cy="13" r="4"/>',
    arrow:'<path d="M5 12h14m-5-5 5 5-5 5"/>',
    compass:'<circle cx="12" cy="12" r="9"/><path d="m15 8-2 6-5 2 2-6 5-2Z"/>'
  };
  const svg = name => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name] || icons.compass}</svg>`;
  const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text)n.textContent=text;return n;};
  const action = (id, value) => window.xlandsUIAction?.(id,value ?? (id === 'friend' ? 'open' : ''));
  const button=(icon,title,id)=>{const b=el('button','world-icon');b.innerHTML=svg(icon);b.title=title;b.setAttribute('aria-label',title);b.dataset.uiAction=id;b.addEventListener('click',()=>action(id));return b;};
  const hud=el('div','world-hud'), top=el('div','world-hud-top'), locationChip=el('div','world-location');
  const mark=el('span','world-mark');mark.innerHTML=svg(isFrog?'leaf':'compass');
  const where=el('div'), place=el('strong'), time=el('span');where.append(place,time);locationChip.append(mark,where);
  const dock=el('nav','world-dock');dock.setAttribute('aria-label',words[5]);
  if(isFrog){dock.append(button('friends',words[4],'friend'),button('album',words[2],'album'),button('bag',words[3],'bag'));}
  dock.append(button('menu',words[5],'menu'));top.append(locationChip,dock);
  const counter=el('span','world-counter');counter.innerHTML=svg('leaf');const number=el('b');counter.append(number);counter.setAttribute('aria-label',words[11]);counter.hidden=!isFrog;
  const friend=el('button','world-friend-note');friend.addEventListener('click',()=>action('friend'));friend.hidden=true;
  const bottom=el('div','world-hud-bottom'), toast=el('div','world-toast');toast.setAttribute('role','status');toast.hidden=true;
  const prompt=el('button','world-prompt');const key=el('kbd','','E'),promptText=el('span'), arrow=el('span','prompt-arrow');arrow.innerHTML=svg('arrow');prompt.append(key,promptText,arrow);prompt.hidden=true;prompt.addEventListener('click',()=>{window.xlandsInput?.('interact',true);window.xlandsInput?.('interact',false);});
  const help=el('button','world-controls-help',`${words[12]}  ?`);help.addEventListener('click',()=>showHelp());
  bottom.append(friend,toast,prompt);hud.append(top,counter,bottom,help);document.body.append(hud);
  const sheet=el('div','native-menu');sheet.hidden=true;
  const card=el('section','native-menu-card');card.setAttribute('role','dialog');card.setAttribute('aria-modal','true');card.setAttribute('aria-labelledby','native-menu-title');card.tabIndex=-1;
  const head=el('header'), heading=el('div'), eyebrow=el('span','sheet-eyebrow',words[0]),title=el('h2');title.id='native-menu-title';heading.append(eyebrow,title);
  const close=button('close',words[6],'close');head.append(heading,close);
  const content=el('div','native-menu-items'),footer=el('footer','sheet-footer');card.append(head,content,footer);sheet.append(card);document.body.append(sheet);
  let current=null, signature='',lastFocus=null, helpOpen=false;
  const closeSheet=()=>{helpOpen=false;action('external-lock',false);action('close');renderSheet(null);};
  close.onclick=closeSheet;sheet.addEventListener('click',e=>{if(e.target===sheet)closeSheet();});
  function renderSheet(data) {
    const next=JSON.stringify(data);
    if(next===signature)return;signature=next;
    const wasOpen=!sheet.hidden;sheet.hidden=!data;
    document.body.classList.toggle('world-ui-open',!!data);
    window.xlandsOverlayLocked?.(!!data);
    if(!data){if(wasOpen)lastFocus?.focus?.({preventScroll:true});return;}
    if(!wasOpen)lastFocus=document.activeElement;
    card.dataset.kind=data.kind;title.textContent=data.title;content.replaceChildren();content.classList.remove('has-photos');footer.replaceChildren();content.scrollTop=0;
    if(data.kind==='menu'){
      for(const item of data.items){
        if(item.separator){content.append(el('h3','native-menu-section',item.text));continue;}
        const row=el('button','menu-row'),label=el('span','',item.text),arr=el('span','menu-arrow','↗');row.append(label,arr);row.disabled=!!item.disabled;
        row.addEventListener('click',()=>window.xlandsMenuAction?.(item.id));content.append(row);
      }
    } else if(data.kind==='album'&&!data.blocks?.some(b=>b.type==='image')){
      const empty=el('div','album-empty'),drawing=el('div','album-illustration');drawing.innerHTML=svg('camera');
      empty.append(drawing,el('h3','',words[8]),el('p','',words[9]));const photo=el('button','sheet-primary',words[7]);photo.addEventListener('click',()=>action('photo'));empty.append(photo);content.append(empty);
    } else {
      const images=data.blocks?.some(b=>b.type==='image');if(images)content.classList.add('has-photos');else content.classList.remove('has-photos');
      let lastPhoto=null;
      for(const block of data.blocks||[]){
        if(block.type==='image'){const frame=el('figure','album-photo'),image=el('img');image.src=block.src;image.alt=words[2];image.loading='lazy';frame.append(image);content.append(frame);lastPhoto=frame;}
        else if(lastPhoto&&images){lastPhoto.append(el('figcaption','',block.text));lastPhoto=null;}else content.append(el('p','sheet-copy',block.text));
      }
      for(const choice of data.actions||[]){const b=el('button','sheet-choice',choice.label);b.addEventListener('click',()=>action(data.kind==='friend'?'friend':'panel-button',choice.id));footer.append(b);}
    }
    if(!footer.children.length&&data.kind!=='menu'){const done=el('button','sheet-secondary',words[10]);done.addEventListener('click',closeSheet);footer.append(done);}
    if(!wasOpen)close.focus({preventScroll:true});
  }
  function showHelp(){helpOpen=true;action('external-lock',true);renderSheet({kind:'help',title:words[12],blocks:[{type:'text',text:`W A S D  ·  ${words[13]}\nShift  ·  ${words[14]}\n${words[15]}  ·  ◉ ↔\nE  ·  ${words[17]}\n${isFrog?'C':'V'}  ·  ${words[18]}${isFrog?'\nSpace  ·  '+words[16]:''}`} ]});}
  document.addEventListener('keydown',e=>{
    if(sheet.hidden)return;
    if(e.key==='Escape'){e.preventDefault();closeSheet();action('external-lock',false);}
    if(e.key==='Tab'){
      const buttons=[...card.querySelectorAll('button:not([disabled]),a,input,select,[tabindex="0"]')];
      if(!buttons.length)return;const first=buttons[0],last=buttons.at(-1);
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
    }
  });
  window.xlandsState=data=>{
    current=data;document.body.classList.toggle('world-capturing',!!data.busy);place.textContent=data.place||words[1];time.textContent=data.time||'';number.textContent=String(data.counter??0);
    counter.title=words[11]+' '+number.textContent;
    prompt.hidden=!data.prompt;promptText.textContent=data.prompt||'';toast.hidden=!data.toast;toast.textContent=data.toast||'';
    const f=data.friend;friend.hidden=!f?.summary;friend.textContent=f?.summary||'';
    if(helpOpen)return;
    renderSheet(data.menu?{kind:'menu',title:isFrog?words[5]:words[20],items:data.menu.items}:data.panel);
  };
  window.addEventListener('message',e=>{if(e.source===parent&&e.data?.type==='xlands-ui-lock')action('external-lock',!!e.data.locked);});
}
installWorldUI();

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
