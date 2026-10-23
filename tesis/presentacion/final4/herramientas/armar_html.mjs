// armar_html.mjs — arma Defensa_EduFEM.html a partir de las láminas sueltas de laminas/.
//
//   node herramientas/armar_html.mjs                       -> ../Defensa_EduFEM.html (tema oscuro, versión 1)
//   node herramientas/armar_html.mjs --v2 --salida=_prueba_x.html   prueba privada con el aspecto PowerPoint
//   node herramientas/armar_html.mjs --solo=alcance,plano --v2 --salida=_prueba_x.html   solo esas láminas
//
// Orden: laminas/_cabeza.html + laminas/NN_<id>.html (orden alfabético del nombre) + laminas/_pie.html.
// Cada lámina vive en su propio archivo para que se pueda editar sin tocar las demás.
// La versión 2 oficial (Defensa_EduFEM_v2.html) la sigue armando generar_v2.mjs desde
// Defensa_EduFEM.html; --v2 aplica aquí las mismas cuatro sustituciones, solo para probar.
// La escritura es atómica (archivo temporal + renombrar): nadie lee un archivo a medio escribir.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const FINAL = path.resolve(AQUI, '..');
const LAM = path.join(FINAL, 'laminas');
const flags = Object.fromEntries(process.argv.slice(2).filter((a) => a.startsWith('--')).map((a) => { const [k, v] = a.slice(2).split('='); return [k, v ?? true]; }));

const cabeza = fs.readFileSync(path.join(LAM, '_cabeza.html'), 'utf8');
const pie = fs.readFileSync(path.join(LAM, '_pie.html'), 'utf8');
let archivos = fs.readdirSync(LAM).filter((f) => /^\d\d_.+\.html$/.test(f)).sort();
if (flags.solo) {
  const ids = String(flags.solo).split(',');
  archivos = archivos.filter((f) => ids.includes(f.replace(/^\d\d_/, '').replace(/\.html$/, '')));
}
const ids = new Set();
const cuerpo = archivos.map((f) => {
  const txt = fs.readFileSync(path.join(LAM, f), 'utf8');
  const m = txt.match(/<section[^>]*\sid="([^"]+)"/);
  if (!m) throw new Error(`${f}: no tiene <section ... id="...">`);
  if (ids.has(m[1])) throw new Error(`${f}: id repetido «${m[1]}»`);
  ids.add(m[1]);
  return `<!-- ${f} -->\n${txt.trim()}\n`;
}).join('\n');

let html = cabeza + '\n' + cuerpo + '\n' + pie;
if (flags.v2) {
  const cambios = [
    ['<html lang="es" data-tema="oscuro">', '<html lang="es" data-tema="claro" data-estilo="ppt">'],
    ['<title>Defensa EduFEM</title>', '<title>Defensa EduFEM · versión 2</title>'],
    ['<link rel="stylesheet" href="assets/terceros/inter.css">',
      '<link rel="stylesheet" href="assets/terceros/inter.css">\n<link rel="stylesheet" href="assets/terceros/carlito.css">'],
    ['<link rel="stylesheet" href="assets/css/laminas.css">',
      '<link rel="stylesheet" href="assets/css/laminas.css">\n<link rel="stylesheet" href="assets/css/estilo_ppt.css">'],
  ];
  for (const [a, b] of cambios) {
    if (html.split(a).length !== 2) throw new Error(`No se encontró una sola vez: ${a}`);
    html = html.replace(a, b);
  }
}
const destino = path.resolve(FINAL, flags.salida || 'Defensa_EduFEM.html');
const tmp = destino + '.' + process.pid + '.tmp';
fs.writeFileSync(tmp, html);
fs.renameSync(tmp, destino);
console.log(`[OK] ${path.relative(process.cwd(), destino)} · ${archivos.length} láminas`);
