// extraer_pptx.mjs — recorre la presentación (por omisión la versión 2, estilo PowerPoint)
// lámina por lámina y paso por paso, y describe cada paso como formas nativas para
// construir_pptx.py: cajas, textos con sus líneas, imágenes, regiones fotografiadas
// (SVG, lienzos, fórmulas), videos y enlaces entre láminas. Además graba en video:
//   - los bucles de las regiones que se animan sin fin (data-pptx-clip);
//   - las animaciones de cada paso (un lienzo que se dibuja, un elemento que se deforma, una
//     tabla que se marca de a un ítem): PowerPoint las reproduce una vez con el clic;
// y recorre los estados de los botones de los laboratorios (método pptx() de cada
// visualización), que PowerPoint vuelve diapositivas enlazadas o disparadores.
//
//   node herramientas/extraer_pptx.mjs [--html=Defensa_EduFEM_v2.html] [--trabajo=_trabajo/pptx]
//                                      [--solo=id1,id2] [--sin-bucles] [--sin-animaciones] [--sin-estados]
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
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
await page.goto(pathToFileURL(HTML).href + `?captura=1&nitidez=2&pptx=1&cuadros=${encodeURIComponent(cuadros)}`, { waitUntil: 'load', timeout: 180000 });
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
/** Como asentar, pero anota cuándo cambió por última vez cada región (firmas de contenido):
 *  { rasters: {sid: ms}, regiones: {vid: ms} }. */
async function asentarMidiendo(minimo) {
  const firmas = () => page.evaluate(() => window.__pptx.firmas());
  let base = await firmas();
  const ult = { rasters: {}, regiones: {} };
  let t = 0;
  const muestra = async () => {
    const f = await firmas();
    for (const tipo of ['rasters', 'regiones']) {
      for (const [id, h] of Object.entries(f[tipo])) if (id in base[tipo] && base[tipo][id] !== h) ult[tipo][id] = t;
    }
    base = f;
  };
  while (t < minimo) { await avanzar(100); t += 100; await muestra(); }
  for (let k = 0; k < 160; k++) { const r = await avanzar(100); t += 100; await muestra(); if (!r.tweens) break; }
  for (let k = 0; k < 4; k++) { await avanzar(100); t += 100; await muestra(); }
  return ult;
}
/** Avanza exactamente ms (una lámina puede pedir su instante: data-pptx-captura="paso:ms"). */
async function avanzarHasta(ms) { for (let t = 0; t < ms; t += 100) await avanzar(100); }
const ir = (id, p) => page.evaluate(({ id, p }) => window.__deck.ir(id, p), { id, p });
const sha = (buf) => crypto.createHash('sha1').update(buf).digest('hex').slice(0, 16);
const par = (v) => Math.max(2, Math.round(v / 2) * 2);

// ---------------------------------------------------------------- fotografiar un estado
const vistas = new Map();   // hash -> archivo
let nFotos = 0;
/** Describe el estado actual de la lámina y fotografía cada región (fondo transparente, 2x). */
async function capturarEstado() {
  const des = await page.evaluate(() => window.__pptx.extraer());
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
    const h = sha(buf);
    if (!vistas.has(h)) { const f = `${h}.png`; fs.writeFileSync(path.join(IMG, f), buf); vistas.set(h, f); nFotos++; }
    archivos[r.rid] = { archivo: vistas.get(h), x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
  }
  await page.evaluate(() => window.__pptx.limpiar());
  if (await page.evaluate(() => window.__pptx.redimensiones())) throw new Error('una captura redimensionó la ventana');
  return { des, archivos };
}
/** Completa las regiones con su archivo y las imágenes con su ruta local. */
function resolverItems(des, archivos) {
  for (const it of des.items) {
    if (it.t === 'raster') {
      const a = archivos[it.rid];
      if (!a) { it.t = 'omitido'; continue; }
      Object.assign(it, { archivo: a.archivo, x: a.x, y: a.y, w: a.w, h: a.h });
    }
    if (it.t === 'img' && it.src) {
      const u = new URL(it.src);
      it.ruta = decodeURIComponent(u.pathname.replace(/^\/([A-Za-z]:)/, '$1'));
      delete it.src;
    }
  }
  return des.items.filter((i) => i.t !== 'omitido');
}

// ---------------------------------------------------------------- videos
const CLIPS = path.join(TRABAJO, 'clips');
fs.mkdirSync(CLIPS, { recursive: true });
/** Codifica los cuadros PNG (transparentes, al doble) sobre su color de fondo, a la resolución de
 *  diseño, y deja al lado el primer cuadro como póster. Sin cuadros B: con ellos PowerPoint
 *  arranca 160 ms tarde y nunca muestra los últimos cuadros (probado); el póster es el cuadro 0
 *  del propio video (si no, el video exportado por PowerPoint lo mezcla con el primer cuadro). */
function codificar(dir, fps, fondo, w, h, mp4) {
  const png = fs.readFileSync(path.join(dir, 'f0000.png'));
  const W2 = png.readUInt32BE(16), H2 = png.readUInt32BE(20);
  const r = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(fps), '-start_number', '0', '-i', path.join(dir, 'f%04d.png'),
    '-f', 'lavfi', '-i', `color=c=0x${fondo.slice(1)}:s=${W2}x${H2}:r=${fps}`,
    '-filter_complex', `[1:v][0:v]overlay=0:0:shortest=1,scale=${par(w)}:${par(h)}:flags=lanczos,format=yuv420p`,
    '-c:v', 'libx264', '-preset', 'slow', '-tune', 'animation', '-crf', '20', '-bf', '0', '-g', String(fps),
    '-keyint_min', String(fps), '-sc_threshold', '0', '-movflags', '+faststart', mp4]);
  if (r.status !== 0) { console.log('  ffmpeg falló:', String(r.stderr).slice(0, 400)); return null; }
  const poster = mp4.replace(/\.mp4$/, '_poster.png');
  spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', mp4, '-frames:v', '1', poster]);
  return { mp4, poster };
}

// Bucles. Una región con data-pptx-clip="nombre:ms:modo" (la carátula, la malla de los
// separadores, los modos de Gauss...) se anima sin fin en la presentación HTML. Para PowerPoint se
// graba un ciclo, cuadro a cuadro con el reloj virtual, se compone sobre su color de fondo y se
// codifica en MP4: construir_pptx.py lo inserta como video que se reproduce solo y en bucle. modo
// «ciclo»: el período cierra solo; «idavuelta»: se agrega el recorrido inverso para que el bucle
// no salte. Los clips se identifican por el cuadro fijo que ya se fotografió (mismo cuadro, mismo
// clip). reponer() deja la lámina en el estado del cuadro (con los bucles ya liberados).
const clipsHechos = new Map();
const FPS_CLIP = 15;
async function grabarClip(etiqueta, it, a, clave, reponer) {
  const dir = path.join(CLIPS, clave);
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  const fondo = await page.evaluate((id) => window.__pptx.fondoDe(id), it.rid);
  await page.evaluate(() => { window.EF.congelarBucles = null; });
  await reponer();
  await asentar(1500);
  const n = Math.max(2, Math.round((it.clip.ms / 1000) * FPS_CLIP));
  const firmas = new Set();
  for (let k = 0; k < n; k++) {
    await page.evaluate((id) => window.__pptx.aislar(id), it.rid);
    const buf = await page.screenshot({ type: 'png', omitBackground: true, captureBeyondViewport: false, clip: { x: a.x, y: a.y, width: a.w, height: a.h } });
    await page.evaluate(() => window.__pptx.restaurar());
    firmas.add(sha(buf));
    fs.writeFileSync(path.join(dir, `f${String(k).padStart(4, '0')}.png`), buf);
    await avanzar(1000 / FPS_CLIP);
  }
  // se vuelve al estado congelado, que es el que siguen los pasos siguientes
  await page.evaluate(() => { window.EF.detenerBucles(); window.EF.congelarBucles = 4.5; });
  await reponer();
  await asentar(1200);
  if (firmas.size < 3) { fs.rmSync(dir, { recursive: true, force: true }); return null; }   // no se mueve
  let total = n;
  if (it.clip.modo === 'idavuelta') {
    for (let k = n - 2; k >= 1; k--) fs.copyFileSync(path.join(dir, `f${String(k).padStart(4, '0')}.png`), path.join(dir, `f${String(total++).padStart(4, '0')}.png`));
  }
  const res = codificar(dir, FPS_CLIP, fondo, a.w, a.h, path.join(CLIPS, `${clave}.mp4`));
  fs.rmSync(dir, { recursive: true, force: true });
  if (!res) return null;
  console.log(`   bucle ${it.clip.nombre} (${etiqueta}) · ${total} cuadros · ${(fs.statSync(res.mp4).size / 1e6).toFixed(2)} MB`);
  return res.mp4;
}
async function bucles(items, archivos, etiqueta, reponer) {
  if (flags['sin-bucles']) return;
  for (const it of items) {
    if (it.t !== 'raster' || !it.clip || !archivos[it.rid]) continue;
    const clave = archivos[it.rid].archivo.replace(/\.png$/, '');
    if (!clipsHechos.has(clave)) clipsHechos.set(clave, await grabarClip(etiqueta, it, archivos[it.rid], clave, reponer));
    const mp4 = clipsHechos.get(clave);
    if (mp4) it.clipVideo = mp4;
  }
}

// Animaciones de paso. Mientras un paso se asienta se comparan las firmas del contenido: si un
// lienzo, un SVG o una fórmula cambia (rasters), o si cambian el texto o las clases de una
// visualización (regiones nativas: una tabla que se marca, un contador), el paso se vuelve a
// disparar y se graba cuadro a cuadro con el reloj virtual, con los ancestros a opacidad plena
// (PowerPoint pone su propio efecto de entrada). El video empieza en el estado del clic y
// termina en el estado final; construir_pptx.py lo reproduce una vez con ese clic.
const FPS_PASO = 25;
const MIN_ANIM = 150;   // ms: un cambio único en el primer cuadro no es una animación
async function dispararPaso(L, p, vecino) {
  if (p === 0) {
    await ir(vecino, 0);
    await asentar(300);
    await ir(L.id, 0);
  } else {
    await ir(L.id, p - 1);
    await asentar(600);
    await page.evaluate(() => window.__deck.siguiente());
  }
}
async function objetivosDe(med, des, archivos) {
  const objetivos = [];
  const cubiertos = new Set();
  for (const [vid, ms] of Object.entries(med.regiones)) {
    if (ms <= MIN_ANIM) continue;
    const r = await page.evaluate((v) => window.__pptx.region(v), vid);
    if (!r || r.w < 8 || r.h < 8) continue;
    const x0 = Math.max(0, Math.floor(r.x)), y0 = Math.max(0, Math.floor(r.y));
    const x1 = Math.min(1920, Math.ceil(r.x + r.w)), y1 = Math.min(1080, Math.ceil(r.y + r.h));
    r.dentro.forEach((rid) => cubiertos.add(rid));
    objetivos.push({ sel: { vid }, clip: { x: x0, y: y0, width: x1 - x0, height: y1 - y0 }, fondo: r.fondo, ms, tipo: 'region' });
  }
  const sids = Object.entries(med.rasters).filter(([, ms]) => ms > MIN_ANIM);
  if (sids.length) {
    const porRid = await page.evaluate((s) => window.__pptx.ridsDe(s), sids);   // rid -> ms
    for (const [rid, ms] of Object.entries(porRid)) {
      const a = archivos[rid];
      const it = des.items.find((i) => i.rid === rid);
      if (!a || !it || it.clip || cubiertos.has(rid)) continue;   // los bucles ya van en video
      const fondo = await page.evaluate((id) => window.__pptx.fondoDe(id), rid);
      objetivos.push({ sel: { rid }, clip: { x: a.x, y: a.y, width: a.w, height: a.h }, fondo, ms, tipo: 'raster', it });
    }
  }
  return objetivos;
}
async function grabarPaso(L, p, vecino, objetivos) {
  const T = Math.max(...objetivos.map((o) => o.ms)) + 240;
  const n = Math.ceil(T / (1000 / FPS_PASO)) + 1;
  for (const [j, o] of objetivos.entries()) {
    o.clave = `${L.id}_p${p}_${o.sel.rid || o.sel.vid}_${j}`;
    o.dir = path.join(CLIPS, o.clave);
    fs.rmSync(o.dir, { recursive: true, force: true });
    fs.mkdirSync(o.dir, { recursive: true });
    o.cuadros = [];
  }
  await dispararPaso(L, p, vecino);
  for (const o of objetivos) {
    await page.evaluate(() => window.__pptx.aislarNada());
    o.vacio = sha(await page.screenshot({ type: 'png', omitBackground: true, captureBeyondViewport: false, clip: o.clip }));
    await page.evaluate(() => window.__pptx.restaurar());
  }
  for (let k = 0; k < n; k++) {
    for (const o of objetivos) {
      if (k * (1000 / FPS_PASO) > o.ms + 240) continue;
      await page.evaluate((s) => window.__pptx.aislarGrabando(s), o.sel);
      const buf = await page.screenshot({ type: 'png', omitBackground: true, captureBeyondViewport: false, clip: o.clip });
      await page.evaluate(() => window.__pptx.restaurar());
      o.cuadros.push(buf);
    }
    await avanzar(1000 / FPS_PASO);
  }
  const hechos = [];
  for (const o of objetivos) {
    // fuera los cuadros en blanco del comienzo (la región todavía no se mostraba)
    let i0 = 0;
    while (i0 < o.cuadros.length && sha(o.cuadros[i0]) === o.vacio) i0++;
    const cuadros = o.cuadros.slice(i0);
    const distintos = new Set(cuadros.map(sha));
    if (cuadros.length < 4 || distintos.size < 3) { fs.rmSync(o.dir, { recursive: true, force: true }); continue; }
    cuadros.forEach((b, k) => fs.writeFileSync(path.join(o.dir, `f${String(k).padStart(4, '0')}.png`), b));
    const res = codificar(o.dir, FPS_PASO, o.fondo, o.clip.width, o.clip.height, path.join(CLIPS, `${o.clave}.mp4`));
    fs.rmSync(o.dir, { recursive: true, force: true });
    if (!res) continue;
    hechos.push({ ...o, res, ms: Math.round((cuadros.length * 1000) / FPS_PASO) });
  }
  return hechos;
}

// ---------------------------------------------------------------- recorrido
const laminas = await page.evaluate(() => window.__deck.laminas());
const escena = { html: path.basename(HTML), laminas: [] };
const claveEstado = (s) => JSON.stringify(Object.fromEntries(Object.keys(s).sort().map((k) => [k, s[k]])));
const t0 = Date.now();
let nAnim = 0, nEstados = 0;
for (const [iL, L] of laminas.entries()) {
  if (SOLO && !SOLO.includes(L.id)) continue;
  const vecino = laminas[iL > 0 ? iL - 1 : iL + 1].id;
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
    if (p === 0) await ir(L.id, 0);
    else await page.evaluate(() => window.__deck.siguiente());
    let med = null;
    if (instante[p] != null) await avanzarHasta(instante[p]);
    else med = await asentarMidiendo(p === 0 ? 1200 : 600);
    const est = await page.evaluate(() => window.__deck.estado());
    if (est.id !== L.id || est.paso !== p) throw new Error(`se esperaba ${L.id}:${p} y está ${est.id}:${est.paso}`);
    const { des, archivos } = await capturarEstado();
    await bucles(des.items, archivos, `${L.id}:${p}`, async () => { await ir(L.id, p); });
    if (!flags['sin-animaciones']) {
      if (!med) {   // el cuadro se tomó a mitad de la animación: se mide aparte, entera
        await dispararPaso(L, p, vecino);
        med = await asentarMidiendo(0);
      }
      const objetivos = await objetivosDe(med, des, archivos);
      if (objetivos.length) {
        const hechos = await grabarPaso(L, p, vecino, objetivos);
        for (const o of hechos) {
          const clip = { mp4: o.res.mp4, poster: o.res.poster, ms: o.ms };
          if (o.tipo === 'raster') o.it.clipPaso = clip;
          else des.items.push({ t: 'region', x: o.clip.x, y: o.clip.y, w: o.clip.width, h: o.clip.height, orden: 5e5 + nAnim, entrada: null, z: 50, clipPaso: clip });
          nAnim++;
          console.log(`   animación ${L.id}:${p} ${o.tipo} ${o.sel.rid || o.sel.vid} · ${(o.ms / 1000).toFixed(1)} s · ${(fs.statSync(o.res.mp4).size / 1e6).toFixed(2)} MB`);
        }
      }
      // de vuelta al paso, asentado, para seguir
      await ir(L.id, p);
      await asentar(1200);
    }
    pasos.push({ fondo: des.fondo, items: resolverItems(des, archivos) });
  }
  // estados de los botones de los laboratorios, desde el último paso
  const estados = [];
  if (!flags['sin-estados']) {
    const apis = await page.evaluate((id) => window.__pptx.estadosInfo(id), L.id);
    for (const api of apis) {
      const nodos = {};
      const cola = [api.base];
      while (cola.length && Object.keys(nodos).length < 60) {
        const s = cola.shift();
        const cl = claveEstado(s);
        if (nodos[cl]) continue;
        const fijar = () => page.evaluate(({ k, s }) => window.__pptx.fijarEstado(k, s), { k: api.k, s });
        await fijar();
        await asentar(300);
        const { des, archivos } = await capturarEstado();
        await bucles(des.items, archivos, `${L.id}·${cl}`, async () => { await ir(L.id, L.pasos); await asentar(600); await fijar(); });
        const controles = await page.evaluate(({ k, s }) => window.__pptx.controlesEstado(k, s), { k: api.k, s });
        nodos[cl] = { estado: s, fondo: des.fondo, items: resolverItems(des, archivos),
          controles: controles.map((c) => ({ ...c, destino: claveEstado(c.destino) })) };
        for (const c of controles) if (!nodos[claveEstado(c.destino)]) cola.push(c.destino);
        nEstados++;
      }
      estados.push({ via: api.via, regiones: api.regiones, base: claveEstado(api.base), nodos });
      console.log(`   estados ${L.id}: ${Object.keys(nodos).length} (${api.via})`);
    }
    if (apis.length) { await ir(L.id, L.pasos); await asentar(1200); }
  }
  escena.laminas.push({ id: L.id, titulo: L.titulo, bloque: L.bloque, respaldo: L.respaldo, ...meta, narracion: narr, pasos, ...(estados.length ? { estados } : {}) });
  const seg = ((Date.now() - t0) / 1000).toFixed(0);
  console.log(`${String(escena.laminas.length).padStart(2)} ${L.id.padEnd(26)} ${pasos.length} pasos · ${pasos.reduce((s, p) => s + p.items.length, 0)} formas · ${nFotos} imágenes · ${nAnim} animaciones · ${seg} s`);
}
fs.writeFileSync(path.join(TRABAJO, 'escena.json'), JSON.stringify(escena));
console.log(`[OK] ${path.join(TRABAJO, 'escena.json')} · ${escena.laminas.length} láminas · ${nFotos} imágenes · ${nAnim} animaciones · ${nEstados} estados`);
if (errores.length) { console.log('--- errores ---'); for (const e of errores.slice(0, 30)) console.log(e); }
await browser.close();
