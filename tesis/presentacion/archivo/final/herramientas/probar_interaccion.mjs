// probar_interaccion.mjs — prueba automática de la presentación en modo vivo (reloj real).
// Recorre todas las láminas con el teclado, sigue un enlace y vuelve, abre el índice, cambia
// el tema, abre la vista del orador y fotografía cada lámina en el tema claro.
//   node herramientas/probar_interaccion.mjs [carpeta_fotos_tema_claro]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import puppeteer from 'puppeteer-core';
import { buscarChrome } from './foto.mjs';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
// --html=Defensa_EduFEM_v2.html trabaja sobre la versión 2 (aspecto PowerPoint)
const ARG_HTML = (process.argv.find((a) => a.startsWith('--html=')) || '').slice(7);
const HTML = path.resolve(AQUI, '..', ARG_HTML || 'Defensa_EduFEM.html');
const FOTOS = process.argv.slice(2).find((a) => !a.startsWith('--'));
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
const fallos = [];
const ok = (cond, msj) => { console.log((cond ? '  ok   ' : '  FALLA ') + msj); if (!cond) fallos.push(msj); };

const browser = await puppeteer.launch({ executablePath: buscarChrome(), headless: true, timeout: 180000, protocolTimeout: 600000, args: ['--autoplay-policy=no-user-gesture-required'], defaultViewport: { width: 1600, height: 900 } });
const page = await browser.newPage();
const errores = [];
page.on('pageerror', (e) => errores.push(e.message));
page.on('console', (m) => { if (m.type() === 'error') errores.push(m.text()); });
await page.goto(pathToFileURL(HTML).href, { waitUntil: 'load' });
await page.waitForFunction('window.__listo === true', { timeout: 60000 });
const estado = () => page.evaluate(() => ({ id: EF.Deck.laminas[EF.Deck.i].id, paso: EF.Deck.paso }));

// 1. recorrido completo con la flecha derecha
const lam = await page.evaluate(() => EF.Deck.laminas.filter((L) => !L.respaldo).map((L) => ({ id: L.id, pasos: L.pasos })));
const totalPasos = lam.reduce((s, l) => s + l.pasos + 1, 0);
for (let k = 0; k < totalPasos - 1; k++) { await page.keyboard.press('ArrowRight'); await esperar(60); }
await esperar(900);
let e = await estado();
ok(e.id === 'cierre', `recorrido con → llega al cierre (${totalPasos} pasos) — está en ${e.id}`);
await page.keyboard.press('ArrowRight'); await esperar(300);
e = await estado();
ok(e.id === 'cierre', 'no pasa del cierre al respaldo por accidente');

// 2. ir a una lámina por número y volver con Inicio
await page.keyboard.press('Home'); await esperar(600);
ok((await estado()).id === 'portada', 'Inicio vuelve a la carátula');
for (const c of '42') await page.keyboard.press(c);
await page.keyboard.press('Enter'); await esperar(900);
ok((await estado()).id === 'cook', 'número 42 + Intro lleva a la lámina 42 (Cook)');

// 3. enlace con botón y «Volver»
await page.evaluate(() => EF.Deck.irA('consistencia', { apilar: true })); await esperar(900);
await page.click('#consistencia tr.enlace[data-ir="mms"]'); await esperar(900);
e = await estado();
ok(e.id === 'mms', 'la fila de la matriz de consistencia lleva a su evidencia (MMS)');
ok(await page.$eval('#volver', (v) => v.classList.contains('visible')), 'aparece el botón «Volver»');
await page.click('#volver button'); await esperar(900);
ok((await estado()).id === 'consistencia', '«Volver» regresa a la matriz de consistencia');

// 4. índice
await page.keyboard.press('m'); await esperar(300);
ok(await page.$eval('#menu', (m) => m.classList.contains('visible')), 'M abre el índice');
await page.click('#menu button[data-id="veredicto"]'); await esperar(900);
ok((await estado()).id === 'veredicto', 'un clic en el índice lleva a la lámina');
await page.click('#veredicto .crit[data-ir="cook"]'); await esperar(900);
ok((await estado()).id === 'cook', 'un criterio del veredicto lleva a su evidencia');
await page.keyboard.press('Backspace'); await esperar(900);
ok((await estado()).id === 'veredicto', 'Retroceso vuelve al veredicto');

// 5. controles de laboratorio
await page.evaluate(() => EF.Deck.irA('cook')); await esperar(1200);
await page.evaluate(() => { const b = Array.from(document.querySelectorAll('#cook .segmentado button')).find((x) => x.textContent === 'N = 16'); b.click(); });
await esperar(400);
const rotulo = await page.evaluate(() => Array.from(document.querySelectorAll('#cook .segmentado button.sel')).map((b) => b.textContent));
ok(rotulo.includes('N = 16'), 'Cook: el botón N = 16 queda seleccionado');

// 6. tema claro, láser, apagón
await page.keyboard.press('t'); await esperar(300);
const v2 = await page.evaluate(() => EF.estilo === 'ppt');
ok((await page.evaluate(() => document.documentElement.getAttribute('data-tema'))) === 'claro', v2 ? 'T avisa que la versión 2 tiene un solo tema (claro)' : 'T cambia al tema claro');
await page.keyboard.press('b'); await esperar(200);
ok(await page.$eval('#apagon', (a) => a.classList.contains('visible')), 'B apaga la pantalla');
await page.keyboard.press('b'); await esperar(200);

// 7. vista del orador
const popup = new Promise((res) => browser.once('targetcreated', async (t) => res(await t.page())));
await page.keyboard.press('s');
const orador = await Promise.race([popup, esperar(4000).then(() => null)]);
if (orador) {
  await esperar(800);
  const txt = await orador.evaluate(() => document.getElementById('tit') && document.getElementById('tit').textContent);
  ok(!!txt, `la vista del orador se abre y muestra la lámina actual («${txt}»)`);
  const notas = await orador.evaluate(() => document.getElementById('notas').textContent.slice(0, 60));
  ok(notas.length > 20, 'la vista del orador muestra el guion del paso');
  await orador.evaluate(() => document.getElementById('sigB').click()); await esperar(700);
  ok((await estado()).paso === 1, 'el botón › de la vista del orador avanza la presentación');
} else ok(false, 'la vista del orador se abre');

// 8. presentación narrada: en un separador (narración corta) avanza sola al terminar el audio
await page.bringToFront();
await page.evaluate(() => EF.Deck.irA('sep-teoria')); await esperar(800);
await page.keyboard.press('a');
const durSep = await page.evaluate(() => EDUFEM_NARRACION.laminas['sep-teoria'].pasos[0].dur);
let avanzo = false;
for (let k = 0; k < durSep + 12 && !avanzo; k++) { await esperar(1000); avanzo = (await estado()).id === 'estado-arte'; }
ok(avanzo, `la narración automática reproduce el audio y avanza sola (${durSep.toFixed(1)} s)`);
await page.keyboard.press('a'); await esperar(300);

// 9. fotos en el tema claro
if (FOTOS) {
  fs.mkdirSync(FOTOS, { recursive: true });
  const ids = ['portada', 'caja-negra', 'procedimiento', 'isoparametrico', 'gauss', 'ensamblaje', 'trazabilidad', 'mms', 'timoshenko', 'cook', 'veredicto', 'cierre'];
  for (const [k, id] of ids.entries()) {
    await page.evaluate((id) => { const L = EF.Deck.porId[id]; EF.Deck.irA(id, { paso: L.pasos }); }, id);
    await esperar(2600);
    await page.screenshot({ path: path.join(FOTOS, `${String(k + 1).padStart(2, '0')}_${id}.png`) });
  }
}
ok(errores.length === 0, `sin errores de JavaScript (${errores.length})`);
if (errores.length) errores.slice(0, 10).forEach((x) => console.log('     ' + x));
await browser.close();
console.log(fallos.length ? `\n${fallos.length} fallas` : '\nTodo en orden');
process.exit(fallos.length ? 1 : 0);
