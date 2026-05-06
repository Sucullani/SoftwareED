// Graba la animación HTML como frames JPG usando Chrome headless via CDP.
// Usa solo built-ins de Node 24+ (WebSocket, fetch, fs, child_process).
// Después ffmpeg compone los frames en MP4.

import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';
import { join } from 'node:path';

const HERE = import.meta.dirname;
const FRAMES_DIR = join(HERE, 'frames');
const URL = `http://localhost:${process.env.PORT || 8765}/Q4-Q9.html`;
const DURATION_S = parseFloat(process.env.DURATION_S || '7.5');
const FPS = parseInt(process.env.FPS || '30');
const TOTAL_FRAMES = Math.round(DURATION_S * FPS);
const VIEWPORT_W = 1200;
const VIEWPORT_H = 800;
const CHROME_PATH = process.env.CHROME_PATH
  || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const CDP_PORT = 9222;

try {
  if (existsSync(FRAMES_DIR)) rmSync(FRAMES_DIR, { recursive: true, force: true, maxRetries: 3 });
} catch {}
mkdirSync(FRAMES_DIR, { recursive: true });

console.log(`→ Lanzando Chrome headless...`);
const userDataDir = join(HERE, '.chrome-profile');
const chrome = spawn(CHROME_PATH, [
  '--headless=new',
  `--remote-debugging-port=${CDP_PORT}`,
  `--user-data-dir=${userDataDir}`,
  '--disable-extensions',
  '--no-first-run',
  '--no-default-browser-check',
  '--disable-features=Translate',
  `--window-size=${VIEWPORT_W},${VIEWPORT_H}`,
  '--hide-scrollbars',
  'about:blank',
], { stdio: 'ignore', detached: false });

const cleanup = () => { try { chrome.kill('SIGKILL'); } catch {} };
process.on('exit', cleanup);
process.on('SIGINT', () => { cleanup(); process.exit(1); });

// Esperar que CDP esté listo
let targets;
for (let i = 0; i < 40; i++) {
  await sleep(150);
  try {
    const r = await fetch(`http://127.0.0.1:${CDP_PORT}/json`);
    targets = await r.json();
    if (targets.length) break;
  } catch {}
}
if (!targets) { console.error('Chrome no respondió'); cleanup(); process.exit(1); }

const tgt = targets.find(t => t.type === 'page') || targets[0];
console.log(`→ Conectando a ${tgt.id}`);
const ws = new WebSocket(tgt.webSocketDebuggerUrl);
await new Promise((res, rej) => {
  ws.addEventListener('open', res, { once: true });
  ws.addEventListener('error', rej, { once: true });
});

let nextId = 1;
const pending = new Map();
ws.addEventListener('message', (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) {
    const { res, rej } = pending.get(msg.id);
    pending.delete(msg.id);
    if (msg.error) rej(new Error(JSON.stringify(msg.error)));
    else res(msg.result);
  } else if (msg.method === 'Page.screencastFrame') {
    const { data, sessionId } = msg.params;
    frames.push(data);
    send('Page.screencastFrameAck', { sessionId });
  }
});
function send(method, params = {}) {
  const id = nextId++;
  return new Promise((res, rej) => {
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
}

const frames = [];

await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', {
  width: VIEWPORT_W, height: VIEWPORT_H, deviceScaleFactor: 1, mobile: false,
});

// Inyectar pre-navegación: limpia localStorage (playhead a 0) y normaliza body.
await send('Page.addScriptToEvaluateOnNewDocument', {
  source: `
    try { localStorage.clear(); } catch (e) {}
    const css = \`
      html, body, #root { margin: 0 !important; padding: 0 !important;
                           overflow: hidden !important; background: #222233 !important; }
      #root > * { width: 100vw !important; height: 100vh !important; }
    \`;
    const inject = () => {
      if (!document.head) return setTimeout(inject, 10);
      const s = document.createElement('style');
      s.textContent = css;
      document.head.appendChild(s);
    };
    inject();
  `,
});

console.log(`→ Navegando a ${URL}`);
await send('Page.navigate', { url: URL });
await new Promise((res) => {
  const handler = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.method === 'Page.loadEventFired') {
      ws.removeEventListener('message', handler);
      res();
    }
  };
  ws.addEventListener('message', handler);
});

console.log('→ Esperando que React+JSX se compile e inicie animación...');
await sleep(2500);

// Ocultar la barra de controles: encontrar el div cuyo texto matchea
// el patrón "M:SS.XXM:SS.XX" del playback bar y ocultarlo.
console.log('→ Ocultando PlaybackBar...');
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const re = /^\\d:\\d\\d\\.\\d\\d.*\\d:\\d\\d\\.\\d\\d$/;
      let hidden = 0;
      for (const d of document.querySelectorAll('div')) {
        if (re.test((d.textContent || '').trim())) {
          d.style.display = 'none';
          hidden++;
        }
      }
      return hidden;
    })()
  `,
});

// Esperar a que el playhead vuelva a 0 (loop wrap-around) para empezar el
// screencast alineado a t=0. Polleamos localStorage cada 30 ms.
console.log('→ Esperando wrap-around del loop (t→0)...');
let prevT = -1;
const waitForZero = async () => {
  for (let i = 0; i < 400; i++) {  // máx ~12 s
    const r = await send('Runtime.evaluate', {
      expression: 'parseFloat(localStorage.getItem("animstage:t") || "0")',
      returnByValue: true,
    });
    const t = r.result.value;
    if (prevT > 6.5 && t < 0.15) return t;
    prevT = t;
    await sleep(30);
  }
  return null;
};
const aligned = await waitForZero();
console.log(`  alineado a t≈${aligned?.toFixed(3)}s`);

console.log(`→ Iniciando screencast (${TOTAL_FRAMES} frames @ ${FPS} fps)`);
const startTime = Date.now();
await send('Page.startScreencast', {
  format: 'jpeg', quality: 92,
  maxWidth: VIEWPORT_W, maxHeight: VIEWPORT_H,
  everyNthFrame: 1,
});

await sleep(DURATION_S * 1000 + 500);

await send('Page.stopScreencast');
console.log(`→ Capturados ${frames.length} frames en ${((Date.now() - startTime) / 1000).toFixed(2)}s`);

// Re-muestrear a FPS exactos: tomamos solo TOTAL_FRAMES distribuidos
// uniformemente sobre los frames recibidos.
const N = frames.length;
const wanted = Math.min(TOTAL_FRAMES, N);
for (let i = 0; i < wanted; i++) {
  const srcIdx = Math.round((i / wanted) * N);
  const buf = Buffer.from(frames[Math.min(srcIdx, N - 1)], 'base64');
  writeFileSync(join(FRAMES_DIR, `frame_${String(i).padStart(5, '0')}.jpg`), buf);
}
console.log(`→ ${wanted} frames JPG escritos a ${FRAMES_DIR}`);

ws.close();
cleanup();
process.exit(0);
