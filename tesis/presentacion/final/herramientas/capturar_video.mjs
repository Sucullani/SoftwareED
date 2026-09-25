// capturar_video.mjs — graba la presentación, cuadro a cuadro, sincronizada con la narración.
//
// Abre Defensa_EduFEM.html en el Chrome instalado (sin pantalla) en modo captura: el reloj
// de las animaciones es virtual y solo avanza cuando este guion lo pide, así que cada cuadro
// sale igual en cada corrida y el video no depende de la velocidad del equipo. Cada paso de
// cada lámina dura lo que su pista de voz (assets/data/narracion.js) más la pausa; si una
// animación todavía no terminó, el paso se alarga hasta que termine.
//
// Los cuadros van directo a ffmpeg por una tubería (no se guardan en disco).
//
//   node herramientas/capturar_video.mjs [--tema=oscuro] [--fps=30] [--calidad=90]
//        [--trabajo=<carpeta>] [--desde=<id>] [--hasta=<id>]
//
// Salida en <trabajo> (por omisión herramientas/_trabajo): video_mudo.mp4 y segmentos.json.
// Después: python herramientas/montar_video.py
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { fileURLToPath, pathToFileURL } from 'node:url';
import puppeteer from 'puppeteer-core';
import { buscarChrome } from './foto.mjs';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
// --html=Defensa_EduFEM_v2.html trabaja sobre la versión 2 (aspecto PowerPoint)
const ARG_HTML = (process.argv.find((a) => a.startsWith('--html=')) || '').slice(7);
const HTML = path.resolve(AQUI, '..', ARG_HTML || 'Defensa_EduFEM.html');
const flags = Object.fromEntries(process.argv.slice(2).filter((a) => a.startsWith('--')).map((a) => { const [k, v] = a.slice(2).split('='); return [k, v ?? true]; }));
const FPS = Number(flags.fps || 30);
const CALIDAD = Number(flags.calidad || 90);
const TEMA = flags.tema || 'oscuro';
const TRABAJO = path.resolve(flags.trabajo || path.join(AQUI, '_trabajo'));
const EXTRA_MAX = 8; // s: lo más que se alarga un paso esperando a que termine su animación
fs.mkdirSync(TRABAJO, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: buscarChrome(), headless: true,
  args: ['--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required', '--hide-scrollbars', '--force-device-scale-factor=1'],
  defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 1 },
  protocolTimeout: 600000,
});
const page = await browser.newPage();
const errores = [];
page.on('pageerror', (e) => errores.push('[pageerror] ' + e.message));
page.on('console', (m) => { if (m.type() === 'error') errores.push('[consola] ' + m.text()); });
const paramCuadros = flags.cuadros ? `&cuadros=${encodeURIComponent(flags.cuadros)}` : "";
await page.goto(pathToFileURL(HTML).href + `?captura=1&tema=${TEMA}${paramCuadros}`, { waitUntil: 'load' });
await page.waitForFunction('window.__listo === true', { timeout: 120000 });

const laminas = (await page.evaluate(() => window.__deck.laminas())).filter((l) => !l.respaldo);
const narr = await page.evaluate(() => window.EDUFEM_NARRACION);
if (!narr) throw new Error('Falta assets/data/narracion.js: corré antes herramientas/sintetizar_voz.py');
const pausa = Number(narr.pausa_s || 0.6);

// segmentos: un paso de una lámina, con su pista
const segs = [];
let activo = !flags.desde;
for (const l of laminas) {
  if (flags.desde && l.id === flags.desde) activo = true;
  if (!activo) continue;
  const pasosN = (narr.laminas[l.id] || { pasos: [] }).pasos;
  if (pasosN.length !== l.pasos + 1) console.warn(`! ${l.id}: la lámina tiene ${l.pasos + 1} pasos y la narración ${pasosN.length}`);
  for (let k = 0; k <= l.pasos; k++) {
    const p = pasosN[k];
    segs.push({ id: l.id, bloque: l.bloque, titulo: l.titulo, paso: k, audio: p ? p.audio : null, voz: p ? p.dur : 0, dur: p ? p.dur + pausa : 2.0, texto: p ? p.texto : '', subtitulos: p ? p.subtitulos : [] });
  }
  if (flags.hasta && l.id === flags.hasta) break;
}
const totalPrev = segs.reduce((s, x) => s + x.dur, 0);
console.log(`${segs.length} pasos · ${(totalPrev / 60).toFixed(1)} min previstos · ${FPS} cps · tema ${TEMA}`);

const salida = path.join(TRABAJO, 'video_mudo.mp4');
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
  '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'animation', '-g', '300', '-crf', '24', '-pix_fmt', 'yuv420p', '-r', String(FPS), '-movflags', '+faststart', salida],
{ stdio: ['pipe', 'inherit', 'inherit'] });
const escribir = async (buf) => { if (!ff.stdin.write(buf)) await once(ff.stdin, 'drain'); };

const cdp = await page.createCDPSession();
async function foto() {
  await page.evaluate(() => Promise.all(Array.from(document.images).filter((i) => !i.complete).map((i) => new Promise((r) => { i.onload = i.onerror = r; }))));
  const r = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: CALIDAD, optimizeForSpeed: true });
  return Buffer.from(r.data, 'base64');
}

const manifiesto = [];
let t = 0, ultimo = null, fotos = 0, cuadros = 0;
const t0real = Date.now();
for (const [i, s] of segs.entries()) {
  if (s.paso === 0) await page.evaluate((id) => window.__deck.ir(id, 0), s.id);
  else await page.evaluate(() => window.__deck.siguiente());
  const n0 = Math.round(s.dur * FPS);
  let f = 0;
  for (;;) {
    const r = await page.evaluate((ms) => window.__deck.avanzar(ms), 1000 / FPS);
    if (r.sucio || f < 2 || !ultimo) { ultimo = await foto(); fotos++; }
    await escribir(ultimo); f++; cuadros++;
    if (f >= n0 && (r.tweens === 0 || f >= n0 + EXTRA_MAX * FPS)) break;
  }
  manifiesto.push({ ...s, t0: +t.toFixed(3), dur: +(f / FPS).toFixed(3) });
  t += f / FPS;
  if (i % 5 === 0 || i === segs.length - 1) {
    const vel = (t / ((Date.now() - t0real) / 1000)).toFixed(2);
    console.log(`  ${String(i + 1).padStart(3)}/${segs.length}  ${s.id}:${s.paso}  video ${(t / 60).toFixed(1)} min  (${fotos} fotos, ${vel}× tiempo real)`);
  }
}
ff.stdin.end();
await once(ff, 'close');
fs.writeFileSync(path.join(TRABAJO, 'segmentos.json'), JSON.stringify({ fps: FPS, tema: TEMA, pausa, segmentos: manifiesto }, null, 1));
console.log(`\n[OK] ${salida}  ${(t / 60).toFixed(2)} min, ${cuadros} cuadros, ${fotos} capturas`);
if (errores.length) { console.log('--- errores de la página ---'); for (const e of errores.slice(0, 30)) console.log(e); }
await browser.close();
