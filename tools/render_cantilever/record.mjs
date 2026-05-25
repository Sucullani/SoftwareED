// Captura DETERMINISTICA frame-by-frame de la animacion del cantilever.
// El bundle expone window.__stage.setTime tras el primer mount; este
// script avanza t manualmente cada 1/FPS y captura screenshot via CDP.
// Ventaja sobre Page.startScreencast: no depende del FPS interno del
// headless (que puede colapsar a 8-10 fps), garantiza N frames exactos.

import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync, existsSync, readFileSync, statSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';
import { join, extname, resolve, normalize } from 'node:path';
import { createServer } from 'node:http';

const HERE = import.meta.dirname;
const FRAMES_DIR = join(HERE, 'frames');
const SERVE_ROOT = join(HERE, 'q4-q9', 'project');
const PORT = parseInt(process.env.PORT || '8766');
const URL = `http://127.0.0.1:${PORT}/index.html`;
const DURATION_S = parseFloat(process.env.DURATION_S || '4.0');
const FPS = parseInt(process.env.FPS || '30');
const TOTAL_FRAMES = Math.round(DURATION_S * FPS);
const VIEWPORT_W = 900;
const VIEWPORT_H = 600;
const CHROME_PATH = process.env.CHROME_PATH
  || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const CDP_PORT = parseInt(process.env.CDP_PORT || '9223');

// Servidor estatico minimo — sirve q4-q9/project/ en 127.0.0.1:PORT.
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.jsx':  'text/javascript; charset=utf-8',
  '.js':   'text/javascript; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.png':  'image/png',
  '.json': 'application/json',
};
const server = createServer((req, res) => {
  try {
    const reqPath = decodeURIComponent((req.url || '/').split('?')[0]);
    const safe = normalize(reqPath).replace(/^([\\\/])+/, '');
    const full = resolve(SERVE_ROOT, safe || 'index.html');
    if (!full.startsWith(resolve(SERVE_ROOT))) { res.writeHead(403).end(); return; }
    const st = statSync(full);
    const target = st.isDirectory() ? join(full, 'index.html') : full;
    const body = readFileSync(target);
    res.writeHead(200, { 'Content-Type': MIME[extname(target).toLowerCase()] || 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404, { 'Content-Type': 'text/plain' }).end('Not found');
  }
});
await new Promise((r, j) => { server.listen(PORT, '127.0.0.1', r); server.once('error', j); });
console.log(`-> Servidor estatico en ${URL}`);

try {
  if (existsSync(FRAMES_DIR)) rmSync(FRAMES_DIR, { recursive: true, force: true, maxRetries: 3 });
} catch {}
mkdirSync(FRAMES_DIR, { recursive: true });

console.log(`-> Lanzando Chrome headless (CDP ${CDP_PORT})...`);
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

let targets;
for (let i = 0; i < 40; i++) {
  await sleep(150);
  try {
    const r = await fetch(`http://127.0.0.1:${CDP_PORT}/json`);
    targets = await r.json();
    if (targets.length) break;
  } catch {}
}
if (!targets) { console.error('Chrome no respondio'); cleanup(); process.exit(1); }

const tgt = targets.find(t => t.type === 'page') || targets[0];
console.log(`-> Conectando a ${tgt.id}`);
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
  }
});
function send(method, params = {}) {
  const id = nextId++;
  return new Promise((res, rej) => {
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
}

await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', {
  width: VIEWPORT_W, height: VIEWPORT_H, deviceScaleFactor: 1, mobile: false,
});

// Pre-navigation: limpiar localStorage y forzar layout sin margenes/scroll.
await send('Page.addScriptToEvaluateOnNewDocument', {
  source: `
    try { localStorage.clear(); } catch (e) {}
    const css = \`
      html, body, #root { margin: 0 !important; padding: 0 !important;
                           overflow: hidden !important; background: #1c1e22 !important; }
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

console.log(`-> Navegando a ${URL}`);
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

console.log('-> Esperando que Babel compile JSX e inicie React...');
// Espera a que window.__stage este disponible (montaje del Stage component).
for (let i = 0; i < 100; i++) {
  await sleep(100);
  const r = await send('Runtime.evaluate', {
    expression: 'typeof window.__stage',
    returnByValue: true,
  });
  if (r.result.value === 'object') {
    console.log(`   window.__stage disponible tras ~${(i * 100)} ms`);
    break;
  }
}

// Ocultar la PlaybackBar (Stage scrubber + play/pause).
console.log('-> Ocultando PlaybackBar...');
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

// Pausar la animacion y poner playhead en 0.
await send('Runtime.evaluate', {
  expression: 'window.__stage.setPlaying(false); window.__stage.setTime(0);',
});
await sleep(120);

console.log(`-> Capturando ${TOTAL_FRAMES} frames @ ${FPS} fps (frame-by-frame)`);
const startTime = Date.now();

// Frame 0 == Frame TOTAL_FRAMES para loop seamless: solo capturamos 0..TOTAL_FRAMES-1.
for (let i = 0; i < TOTAL_FRAMES; i++) {
  const t = (i / TOTAL_FRAMES) * DURATION_S;
  // Set time exactly via React setter; aceptamos un round-trip por frame.
  await send('Runtime.evaluate', {
    expression: `window.__stage.setTime(${t.toFixed(5)})`,
  });
  // Wait one RAF para que React commit los cambios a SVG.
  await send('Runtime.evaluate', {
    expression: 'new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))',
    awaitPromise: true,
  });
  const shot = await send('Page.captureScreenshot', {
    format: 'jpeg', quality: 92, captureBeyondViewport: false,
  });
  const buf = Buffer.from(shot.data, 'base64');
  writeFileSync(join(FRAMES_DIR, `frame_${String(i).padStart(5, '0')}.jpg`), buf);
  if ((i + 1) % 30 === 0 || i === TOTAL_FRAMES - 1) {
    console.log(`   ${i + 1}/${TOTAL_FRAMES}  (t=${t.toFixed(2)}s)`);
  }
}

console.log(`-> ${TOTAL_FRAMES} frames JPG en ${((Date.now() - startTime) / 1000).toFixed(2)}s`);

ws.close();
cleanup();
try { server.close(); } catch {}
process.exit(0);
