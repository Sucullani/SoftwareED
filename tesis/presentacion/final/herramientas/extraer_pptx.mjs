// extraer_pptx.mjs — recorre la presentación (por omisión la versión 2, estilo PowerPoint)
// lámina por lámina y paso por paso, y describe cada paso como formas nativas para
// construir_pptx.py: cajas, textos con sus líneas, imágenes, regiones fotografiadas
// (SVG, lienzos, fórmulas), videos y enlaces entre láminas.
//
//   node herramientas/extraer_pptx.mjs [--html=Defensa_EduFEM_v2.html] [--trabajo=_trabajo/pptx]
//                                      [--solo=id1,id2]
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';
import puppeteer from 'puppeteer-core';
import { buscarChrome } from './foto.mjs';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const FINAL = path.resolve(AQUI, '..');
const flags = Object.fromEntries(process.argv.slice(2).filter((a) => a.startsWith('--')).map((a) => { const [k, v] = a.slice(2).split('='); return [k, v ?? true]; }));
const HTML = path.resolve(FINAL, flags.html || 'Defensa_EduFEM_v2.html');
const TRABAJO = path.resolve(AQUI, flags.trabajo || '_trabajo/pptx');
const IMG = path.join(TRABAJO, 'img');
const SOLO = flags.solo ? String(flags.solo).split(',') : null;
fs.mkdirSync(IMG, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: buscarChrome(), headless: true, timeout: 180000, protocolTimeout: 900000,
  args: ['--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required', '--hide-scrollbars', '--font-render-hinting=none'],
  defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 2 },
});
const page = await browser.newPage();
page.setDefaultTimeout(600000);
const errores = [];
page.on('pageerror', (e) => errores.push('[pageerror] ' + e.message));
page.on('console', (m) => { if (m.type() === 'error') errores.push('[consola] ' + m.text()); });
// ?cuadros: los videos muestran un cuadro como imagen (sirve de portada del video)
const cuadros = path.relative(FINAL, path.join(AQUI, '_trabajo', 'cuadros')).split(path.sep).join('/');
await page.goto(pathToFileURL(HTML).href + `?captura=1&nitidez=2&pptx=1&cuadros=${encodeURIComponent(cuadros)}`, { waitUntil: 'load' });
await page.waitForFunction('window.__listo === true', { timeout: 120000 });
await page.addScriptTag({ path: path.join(AQUI, 'pptx_dom.js') });

const avanzar = async (ms) => page.evaluate((ms) => window.__deck.avanzar(ms), ms);
/** Avanza el reloj virtual hasta que no queden animaciones finitas (máximo 16 s). */
async function asentar(minimo) {
  let t = 0;
  for (; t < minimo; t += 100) await avanzar(100);
  for (let k = 0; k < 160; k++) { const r = await avanzar(100); if (!r.tweens) break; }
  for (let k = 0; k < 4; k++) await avanzar(100);
}
/** Avanza exactamente ms (una lámina puede pedir su instante: data-pptx-captura="paso:ms"). */
async function avanzarHasta(ms) { for (let t = 0; t < ms; t += 100) await avanzar(100); }

const laminas = await page.evaluate(() => window.__deck.laminas());
const escena = { html: path.basename(HTML), laminas: [] };
const vistas = new Map();   // hash -> archivo
let nFotos = 0;
const t0 = Date.now();
for (const L of laminas) {
  if (SOLO && !SOLO.includes(L.id)) continue;
  const meta = await page.evaluate((id) => {
    const el = document.getElementById(id);
    return { sinPie: el.hasAttribute('data-sin-pie'), titulo: el.getAttribute('data-titulo') || id, clases: el.className, captura: el.getAttribute('data-pptx-captura') || '' };
  }, L.id);
  // instante propio de captura para los pasos cuya animación vuelve al estado inicial
  const instante = Object.fromEntries(meta.captura.split(',').filter(Boolean).map((x) => x.split(':').map(Number)));
  delete meta.captura;
  const narr = await page.evaluate((id) => window.__pptx.narracion(id), L.id);
  const pasos = [];
  for (let p = 0; p <= L.pasos; p++) {
    if (p === 0) { await page.evaluate((id) => window.__deck.ir(id, 0), L.id); }
    else { await page.evaluate(() => window.__deck.siguiente()); }
    if (instante[p] != null) await avanzarHasta(instante[p]);
    else await asentar(p === 0 ? 1200 : 600);
    const est = await page.evaluate(() => window.__deck.estado());
    if (est.id !== L.id || est.paso !== p) throw new Error(`se esperaba ${L.id}:${p} y está ${est.id}:${est.paso}`);
    const des = await page.evaluate(() => window.__pptx.extraer());
    // fotografiar cada región aislada (fondo transparente, al doble de resolución)
    const archivos = {};
    for (const r of des.rasters) {
      const ok = await page.evaluate((id) => window.__pptx.aislar(id), r.rid);
      if (!ok) continue;
      const x0 = Math.max(0, Math.floor(r.x)), y0 = Math.max(0, Math.floor(r.y));
      const x1 = Math.min(1920, Math.ceil(r.x + r.w)), y1 = Math.min(1080, Math.ceil(r.y + r.h));
      let buf = null;
      if (x1 - x0 >= 1 && y1 - y0 >= 1) buf = await page.screenshot({ type: 'png', omitBackground: true, captureBeyondViewport: false, clip: { x: x0, y: y0, width: x1 - x0, height: y1 - y0 } });
      await page.evaluate(() => window.__pptx.restaurar());
      if (!buf) continue;
      const h = crypto.createHash('sha1').update(buf).digest('hex').slice(0, 16);
      if (!vistas.has(h)) { const f = `${h}.png`; fs.writeFileSync(path.join(IMG, f), buf); vistas.set(h, f); nFotos++; }
      archivos[r.rid] = { archivo: vistas.get(h), x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
    }
    await page.evaluate(() => window.__pptx.limpiar());
    if (await page.evaluate(() => window.__pptx.redimensiones())) throw new Error(`una captura redimensionó la ventana en ${L.id}:${p}`);
    for (const it of des.items) {
      if (it.t === 'raster') {
        const a = archivos[it.rid];
        if (!a) { it.t = 'omitido'; continue; }
        Object.assign(it, { archivo: a.archivo, x: a.x, y: a.y, w: a.w, h: a.h });
      }
      if (it.t === 'img') {
        // la imagen de archivo se referencia por su ruta local
        const u = new URL(it.src);
        it.ruta = decodeURIComponent(u.pathname.replace(/^\/([A-Za-z]:)/, '$1'));
        delete it.src;
      }
    }
    pasos.push({ fondo: des.fondo, items: des.items.filter((i) => i.t !== 'omitido') });
  }
  escena.laminas.push({ id: L.id, titulo: L.titulo, bloque: L.bloque, respaldo: L.respaldo, ...meta, narracion: narr, pasos });
  const seg = ((Date.now() - t0) / 1000).toFixed(0);
  console.log(`${String(escena.laminas.length).padStart(2)} ${L.id.padEnd(26)} ${pasos.length} pasos · ${pasos.reduce((s, p) => s + p.items.length, 0)} formas · ${nFotos} imágenes · ${seg} s`);
}
fs.writeFileSync(path.join(TRABAJO, 'escena.json'), JSON.stringify(escena));
console.log(`[OK] ${path.join(TRABAJO, 'escena.json')} · ${escena.laminas.length} láminas · ${nFotos} imágenes`);
if (errores.length) { console.log('--- errores ---'); for (const e of errores.slice(0, 30)) console.log(e); }
await browser.close();
