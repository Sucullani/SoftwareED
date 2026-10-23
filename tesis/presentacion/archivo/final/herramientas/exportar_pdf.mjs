// exportar_pdf.mjs — respaldo estático de la presentación en PDF (una lámina por hoja,
// cada una en su último paso). Sirve si en la sala no se puede abrir el navegador, o para
// entregar las láminas impresas al tribunal.
//
//   node herramientas/exportar_pdf.mjs [--tema=claro|oscuro] [--salida=<archivo.pdf>]
//
// Por omisión: tema oscuro -> ../Defensa_EduFEM_final.pdf
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import puppeteer from 'puppeteer-core';
import { buscarChrome } from './foto.mjs';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
// --html=Defensa_EduFEM_v2.html trabaja sobre la versión 2 (aspecto PowerPoint)
const ARG_HTML = (process.argv.find((a) => a.startsWith('--html=')) || '').slice(7);
const HTML = path.resolve(AQUI, '..', ARG_HTML || 'Defensa_EduFEM.html');
const flags = Object.fromEntries(process.argv.slice(2).filter((a) => a.startsWith('--')).map((a) => { const [k, v] = a.slice(2).split('='); return [k, v ?? true]; }));
const TEMA = flags.tema || 'oscuro';
const SALIDA = path.resolve(flags.salida || path.join(AQUI, '..', ARG_HTML.includes('v2') ? 'Defensa_EduFEM_v2.pdf' : `Defensa_EduFEM_final${TEMA === 'claro' ? '_claro' : ''}.pdf`));

const browser = await puppeteer.launch({ executablePath: buscarChrome(), headless: true, timeout: 180000, protocolTimeout: 600000, args: ['--allow-file-access-from-files'], defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 1 } });
const page = await browser.newPage();
page.setDefaultTimeout(900000);
page.setDefaultNavigationTimeout(900000);
const errores = [];
page.on('pageerror', (e) => errores.push(e.message));
await page.goto(pathToFileURL(HTML).href + `?impresion=1&tema=${TEMA}`, { waitUntil: 'load' });
await page.waitForFunction('window.__listo === true', { timeout: 900000 });
await new Promise((r) => setTimeout(r, 2500));
await page.emulateMediaType('screen');
await page.pdf({ path: SALIDA, width: '1920px', height: '1080px', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 }, preferCSSPageSize: true });
const n = await page.evaluate(() => document.querySelectorAll('.lamina').length);
console.log(`[OK] ${SALIDA}  (${n} láminas, ${(fs.statSync(SALIDA).size / 1e6).toFixed(1)} MB)`);
if (errores.length) { console.log('--- errores ---'); errores.slice(0, 10).forEach((e) => console.log(e)); }
await browser.close();
