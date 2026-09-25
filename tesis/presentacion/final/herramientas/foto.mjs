// foto.mjs — fotografía láminas de la presentación con el Chrome instalado (sin pantalla).
// Sirve para revisar el diseño sin abrir el navegador.
//
//   node herramientas/foto.mjs <salida_dir> [id[:paso] ...] [--tema=claro] [--todas] [--escala=0.5]
//
// Sin ids fotografía la primera lámina. --todas recorre todas en su último paso.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import puppeteer from 'puppeteer-core';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
// --html=Defensa_EduFEM_v2.html trabaja sobre la versión 2 (aspecto PowerPoint)
const ARG_HTML = (process.argv.find((a) => a.startsWith('--html=')) || '').slice(7);
const HTML = path.resolve(AQUI, '..', ARG_HTML || 'Defensa_EduFEM.html');

export function buscarChrome() {
  const cands = [
    process.env.CHROME,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    path.join(process.env.LOCALAPPDATA || '', 'Google/Chrome/Application/chrome.exe'),
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  ].filter(Boolean);
  for (const c of cands) if (fs.existsSync(c)) return c;
  throw new Error('No se encontró Chrome ni Edge. Definí la variable CHROME con la ruta del ejecutable.');
}

async function main() {
  const args = process.argv.slice(2);
  const flags = Object.fromEntries(args.filter((a) => a.startsWith('--')).map((a) => { const [k, v] = a.slice(2).split('='); return [k, v ?? true]; }));
  const pos = args.filter((a) => !a.startsWith('--'));
  const salida = path.resolve(pos[0] || 'fotos');
  fs.mkdirSync(salida, { recursive: true });
  const escala = Number(flags.escala || 0.5);
  const browser = await puppeteer.launch({
    executablePath: buscarChrome(), headless: true, timeout: 180000, protocolTimeout: 600000,
    args: ['--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required', '--hide-scrollbars'],
    defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  const errores = [];
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) errores.push(`[${m.type()}] ${m.text()}`); });
  page.on('pageerror', (e) => errores.push('[pageerror] ' + e.message));
  // --pptx: los mismos parámetros que usa extraer_pptx.mjs (bucles congelados, cuadros de video)
  const cuadros = path.relative(path.resolve(AQUI, '..'), path.join(AQUI, '_trabajo', 'cuadros')).split(path.sep).join('/');
  const url = pathToFileURL(HTML).href + `?captura=1${flags.tema ? '&tema=' + flags.tema : ''}${flags.pptx ? '&pptx=1&cuadros=' + encodeURIComponent(cuadros) : ''}`;
  await page.goto(url, { waitUntil: 'load' });
  await page.waitForFunction('window.__listo === true', { timeout: 60000 });
  let objetivos = pos.slice(1);
  if (flags.todas) {
    const lam = await page.evaluate(() => window.__deck.laminas());
    objetivos = lam.map((l) => `${l.id}:${l.pasos}`);
  }
  if (flags.pasos) {
    // todas las láminas en todos sus pasos, en orden (para comparar con construir_pptx.py --pasos-separados)
    const lam = await page.evaluate(() => window.__deck.laminas());
    let k = 0;
    for (const l of lam) {
      for (let p = 0; p <= l.pasos; p++) {
        if (p === 0) await page.evaluate((id) => window.__deck.ir(id, 0), l.id);
        else await page.evaluate(() => window.__deck.siguiente());
        // el mismo instante que usa extraer_pptx.mjs: data-pptx-captura o el final de las animaciones
        const cap = await page.evaluate((id) => document.getElementById(id).getAttribute('data-pptx-captura') || '', l.id);
        const inst = Object.fromEntries(cap.split(',').filter(Boolean).map((x) => x.split(':').map(Number)));
        const av = (ms) => page.evaluate((ms) => window.__deck.avanzar(ms), ms);
        if (inst[p] != null) { for (let t = 0; t < inst[p]; t += 100) await av(100); }
        else {
          for (let t = 0; t < (p === 0 ? 1200 : 600); t += 100) await av(100);
          for (let k = 0; k < 160; k++) { const r = await av(100); if (!r.tweens) break; }
          for (let k = 0; k < 4; k++) await av(100);
        }
        const buf = await page.screenshot({ type: 'png' });
        fs.writeFileSync(path.join(salida, `${String(++k).padStart(3, '0')}_${l.id}_${p}.png`), buf);
      }
    }
    console.log('fotos', k);
    await browser.close();
    return;
  }
  if (!objetivos.length) objetivos = [(await page.evaluate(() => window.__deck.estado())).id + ':0'];
  let k = 0;
  for (const obj of objetivos) {
    const [id, pasoTxt] = obj.split(':');
    const paso = pasoTxt === undefined ? 0 : Number(pasoTxt);
    await page.evaluate((id) => window.__deck.ir(id, 0), id);
    for (let t = 0; t < 40; t++) await page.evaluate(() => window.__deck.avanzar(100));
    for (let p = 1; p <= paso; p++) {
      await page.evaluate(() => window.__deck.siguiente());
      for (let t = 0; t < 30; t++) await page.evaluate(() => window.__deck.avanzar(100));
    }
    for (let t = 0; t < 20; t++) await page.evaluate(() => window.__deck.avanzar(100));
    const nombre = `${String(++k).padStart(2, '0')}_${id}_${paso}.png`;
    const buf = await page.screenshot({ type: 'png' });
    if (escala !== 1) {
      // reducción simple con un canvas de la propia página
      const b64 = buf.toString('base64');
      const red = await page.evaluate(async (b64, escala) => {
        const img = new Image(); img.src = 'data:image/png;base64,' + b64; await img.decode();
        const c = document.createElement('canvas'); c.width = img.width * escala; c.height = img.height * escala;
        const x = c.getContext('2d'); x.imageSmoothingQuality = 'high'; x.drawImage(img, 0, 0, c.width, c.height);
        return c.toDataURL('image/png').split(',')[1];
      }, b64, escala);
      fs.writeFileSync(path.join(salida, nombre), Buffer.from(red, 'base64'));
    } else fs.writeFileSync(path.join(salida, nombre), buf);
    console.log('foto', nombre);
  }
  if (errores.length) { console.log('--- consola ---'); for (const e of errores.slice(0, 40)) console.log(e); }
  await browser.close();
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  main().catch((e) => { console.error(e); process.exit(1); });
}
