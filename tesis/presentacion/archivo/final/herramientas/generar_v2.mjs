// generar_v2.mjs — arma Defensa_EduFEM_v2.html (versión 2, aspecto PowerPoint) a partir de
// Defensa_EduFEM.html. Las láminas, los datos, la voz y el motor son los mismos: la v2 solo
// agrega data-estilo="ppt" (que activa assets/css/estilo_ppt.css) y la fuente Carlito.
// Después de cambiar una lámina en Defensa_EduFEM.html, correr de nuevo:
//
//   node herramientas/generar_v2.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const FINAL = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const origen = path.join(FINAL, 'Defensa_EduFEM.html');
const destino = path.join(FINAL, 'Defensa_EduFEM_v2.html');
let html = fs.readFileSync(origen, 'utf8');

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
html = html.replace('<!doctype html>\n', '<!doctype html>\n<!-- Generado por herramientas/generar_v2.mjs a partir de Defensa_EduFEM.html: no editar a mano. -->\n');
fs.writeFileSync(destino, html);
console.log('[OK]', path.relative(process.cwd(), destino));
