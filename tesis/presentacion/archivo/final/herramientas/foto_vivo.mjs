// foto_vivo.mjs — fotografía láminas en modo vivo (con controles y botón «Volver» visibles).
//   node herramientas/foto_vivo.mjs <salida_dir> id [id ...]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import puppeteer from 'puppeteer-core';
import { buscarChrome } from './foto.mjs';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
// --html=Defensa_EduFEM_v2.html trabaja sobre la versión 2 (aspecto PowerPoint)
const ARG_HTML = (process.argv.find((a) => a.startsWith('--html=')) || '').slice(7);
const HTML = path.resolve(AQUI, '..', ARG_HTML || 'Defensa_EduFEM.html');
const [salida, ...ids] = process.argv.slice(2);
fs.mkdirSync(salida, { recursive: true });
const b = await puppeteer.launch({ executablePath: buscarChrome(), headless: true, timeout: 180000, protocolTimeout: 600000, defaultViewport: { width: 1920, height: 1080 } });
const pg = await b.newPage();
await pg.goto(pathToFileURL(HTML).href, { waitUntil: 'load' });
await pg.waitForFunction('window.__listo === true');
for (const id of ids) {
  await pg.evaluate((id) => { EF.Deck.irA('consistencia', { apilar: true }); EF.Deck.irA(id, { apilar: true }); }, id);
  await new Promise((r) => setTimeout(r, 2500));
  await pg.screenshot({ path: path.join(salida, `vivo_${id}.png`) });
  console.log('foto', id);
}
await b.close();
