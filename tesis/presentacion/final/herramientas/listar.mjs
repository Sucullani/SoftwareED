// listar.mjs — imprime las láminas de la presentación con su número de pasos (JSON).
//   node herramientas/listar.mjs            -> tabla legible
//   node herramientas/listar.mjs --json     -> JSON en la salida estándar
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import puppeteer from 'puppeteer-core';
import { buscarChrome } from './foto.mjs';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
// --html=Defensa_EduFEM_v2.html trabaja sobre la versión 2 (aspecto PowerPoint)
const ARG_HTML = (process.argv.find((a) => a.startsWith('--html=')) || '').slice(7);
const HTML = path.resolve(AQUI, '..', ARG_HTML || 'Defensa_EduFEM.html');

const browser = await puppeteer.launch({ executablePath: buscarChrome(), headless: true, timeout: 180000, protocolTimeout: 600000, args: ['--allow-file-access-from-files'], defaultViewport: { width: 1920, height: 1080 } });
const page = await browser.newPage();
const errores = [];
page.on('pageerror', (e) => errores.push(e.message));
page.on('console', (m) => { if (m.type() === 'error') errores.push(m.text()); });
await page.goto(pathToFileURL(HTML).href + '?captura=1', { waitUntil: 'load' });
await page.waitForFunction('window.__listo === true', { timeout: 60000 });
const lam = await page.evaluate(() => window.__deck.laminas());
if (process.argv.includes('--json')) console.log(JSON.stringify(lam));
else {
  let n = 0;
  for (const l of lam) console.log(`${l.respaldo ? '  R' : String(++n).padStart(3)}  ${l.id.padEnd(26)} pasos=${l.pasos}  ${l.titulo}`);
  if (errores.length) { console.log('--- errores ---'); errores.forEach((e) => console.log(e)); }
}
await browser.close();
