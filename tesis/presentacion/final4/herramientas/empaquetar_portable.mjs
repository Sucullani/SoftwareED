// empaquetar_portable.mjs — arma una sola HTML que funciona sin la carpeta assets/, en cualquier
// equipo y navegador: hojas de estilo, letras, scripts, imágenes, videos, datos y la voz del modo
// narrado van dentro del archivo (como data: URI). Se comparte ese archivo solo.
//
//   node herramientas/empaquetar_portable.mjs [--html=Defensa_EduFEM_v2.html] [--salida=<archivo>] [--sin-audio]
//
// Por omisión: Defensa_EduFEM_v2.html -> Defensa_EduFEM_v2_portable.html (≈ 25 MB con la voz).
// Termina con error si queda alguna referencia a assets/ sin resolver.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const FINAL = path.resolve(AQUI, '..');
const flags = Object.fromEntries(process.argv.slice(2).filter((a) => a.startsWith('--')).map((a) => { const [k, v] = a.slice(2).split('='); return [k, v ?? true]; }));
const ENTRADA = path.resolve(FINAL, flags.html || 'Defensa_EduFEM_v2.html');
const SALIDA = path.resolve(FINAL, flags.salida || ENTRADA.replace(/\.html$/i, '_portable.html'));
const CON_AUDIO = !flags['sin-audio'];

const MIME = {
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.gif': 'image/gif',
  '.webp': 'image/webp', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.mp3': 'audio/mpeg',
  '.mp4': 'video/mp4', '.json': 'application/json',
};
const cache = new Map();
function datos(f) {
  if (!cache.has(f)) cache.set(f, `data:${MIME[path.extname(f).toLowerCase()] || 'application/octet-stream'};base64,${fs.readFileSync(f).toString('base64')}`);
  return cache.get(f);
}
const faltan = [];

/** Divide una lista CSS por las comas que no están dentro de paréntesis ni de comillas. */
function dividir(valor) {
  const partes = [];
  let prof = 0, comilla = '', actual = '';
  for (const c of valor) {
    if (comilla) { if (c === comilla) comilla = ''; actual += c; continue; }
    if (c === '"' || c === "'") { comilla = c; actual += c; continue; }
    if (c === '(') prof++;
    if (c === ')') prof--;
    if (c === ',' && prof === 0) { partes.push(actual); actual = ''; continue; }
    actual += c;
  }
  if (actual.trim()) partes.push(actual);
  return partes;
}
const urlDe = (s) => { const m = /url\((['"]?)([^'")]+)\1\)/.exec(s); return m ? m[2] : null; };

/** CSS con sus url() en línea; de las fuentes alternativas (woff, ttf) quedan solo las que existen. */
function cssEnLinea(css, dir) {
  css = css.replace(/src:([^;}]*)/g, (m, valor) => {
    const vivas = dividir(valor).filter((p) => {
      const u = urlDe(p);
      return !u || u.startsWith('data:') || fs.existsSync(path.resolve(dir, u));
    });
    return 'src:' + vivas.join(',');
  });
  return css.replace(/url\((['"]?)([^'")]+)\1\)/g, (m, q, u) => {
    if (u.startsWith('data:') || u.startsWith('#') || /^[a-z]+:/i.test(u)) return m;
    const f = path.resolve(dir, u);
    if (!fs.existsSync(f)) { faltan.push(u); return m; }
    return `url("${datos(f)}")`;
  });
}

let html = fs.readFileSync(ENTRADA, 'utf8');

// 1. hojas de estilo
html = html.replace(/<link\s+rel="stylesheet"\s+href="([^"]+)"\s*\/?>/g, (m, href) => {
  if (/^[a-z]+:/i.test(href)) return m;
  const f = path.resolve(FINAL, href);
  if (!fs.existsSync(f)) { faltan.push(href); return m; }
  return `<style data-origen="${href}">\n${cssEnLinea(fs.readFileSync(f, 'utf8'), path.dirname(f))}\n</style>`;
});

// 2. scripts (la voz del modo narrado se pide por su ruta: pasa por EF_ACTIVO)
const PARCHES = {
  'assets/js/deck.js': [["new Audio('assets/audio/' + d.audio)", "new Audio(EF_ACTIVO('assets/audio/' + d.audio))"]],
};
html = html.replace(/<script\s+src="([^"]+)"([^>]*)><\/script>/g, (m, src, resto) => {
  if (/^[a-z]+:/i.test(src)) return m;
  const f = path.resolve(FINAL, src);
  if (!fs.existsSync(f)) { faltan.push(src); return m; }
  let js = fs.readFileSync(f, 'utf8');
  for (const [viejo, nuevo] of PARCHES[src] || []) {
    if (!js.includes(viejo)) throw new Error(`${src}: no está «${viejo}»; revisar el parche de empaquetar_portable.mjs`);
    js = js.split(viejo).join(nuevo);
  }
  return `<script data-origen="${src}"${resto}>\n${js.replace(/<\/script/gi, '<\\/script')}\n</script>`;
});

// 3. imágenes, videos, icono y lupa
html = html.replace(/\b(src|href|poster|data-grande)="(assets\/[^"]+)"/g, (m, attr, ruta) => {
  const f = path.resolve(FINAL, ruta);
  if (!fs.existsSync(f)) { faltan.push(ruta); return m; }
  return `${attr}="${datos(f)}"`;
});

// 4. la voz del modo narrado, en un mapa que consulta EF_ACTIVO (antes de cualquier otro script)
const pistas = {};
if (CON_AUDIO) {
  const dirA = path.join(FINAL, 'assets', 'audio');
  for (const n of fs.readdirSync(dirA).filter((x) => x.endsWith('.mp3')).sort()) pistas['assets/audio/' + n] = datos(path.join(dirA, n));
}
const mapa = `<script data-origen="empaquetar_portable.mjs">\n` +
  `window.EF_ACTIVOS = ${JSON.stringify(pistas)};\n` +
  `window.EF_ACTIVO = function (r) { return (window.EF_ACTIVOS && window.EF_ACTIVOS[r]) || r; };\n</script>\n`;
const primerScript = html.indexOf('<script');
if (primerScript < 0) throw new Error('la HTML no tiene scripts');
html = html.slice(0, primerScript) + mapa + html.slice(primerScript);

// 5. control: no debe quedar ninguna referencia a assets/ fuera de los nombres del mapa y de los comentarios
const restos = [...html.matchAll(/(?:src|href|poster|data-grande)="assets\/[^"]*"|url\((['"]?)assets\/[^)]*\)/g)].map((x) => x[0]);
fs.writeFileSync(SALIDA, html, 'utf8');
const mb = (fs.statSync(SALIDA).size / 1e6).toFixed(1);
console.log(`[OK] ${path.relative(FINAL, SALIDA)} · ${mb} MB · ${cache.size} archivos en línea · ${Object.keys(pistas).length} pistas de voz`);
if (faltan.length) console.log('  faltan (quedan como referencia externa):', [...new Set(faltan)].join(', '));
if (restos.length) { console.log('  referencias sin resolver:', [...new Set(restos)].slice(0, 20).join(' | ')); process.exit(1); }
