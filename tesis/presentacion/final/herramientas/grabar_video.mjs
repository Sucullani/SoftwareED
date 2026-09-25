// grabar_video.mjs — graba el video completo de la defensa en varias partes a la vez.
//
//   node herramientas/grabar_video.mjs [--partes=2] [--tema=oscuro] [--fps=30]
//
// 1. Extrae con ffmpeg los cuadros de los videos del software (assets/video/*.mp4) a
//    _trabajo/cuadros: en la captura se muestran como imágenes, sin buscar en el MP4.
// 2. Reparte las láminas en partes contiguas de duración parecida (según la narración).
// 3. Lanza capturar_video.mjs para cada parte en paralelo, cada una con su Chrome.
// 4. Al terminar, se monta con:  python herramientas/montar_video.py --trabajo=<parte1>,<parte2>,...
import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const FINAL = path.resolve(AQUI, '..');
const flags = Object.fromEntries(process.argv.slice(2).filter((a) => a.startsWith('--')).map((a) => { const [k, v] = a.slice(2).split('='); return [k, v ?? true]; }));
const PARTES = Number(flags.partes || 2);
const TRABAJO = path.join(AQUI, '_trabajo');

// ---- 1. cuadros de los videos
const CUADROS = path.join(TRABAJO, 'cuadros');
for (const f of fs.readdirSync(path.join(FINAL, 'assets', 'video')).filter((x) => x.endsWith('.mp4'))) {
  const dir = path.join(CUADROS, f.replace(/\.mp4$/, ''));
  if (fs.existsSync(dir) && fs.readdirSync(dir).length > 10) continue;
  fs.mkdirSync(dir, { recursive: true });
  const r = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', path.join(FINAL, 'assets', 'video', f), '-q:v', '3', path.join(dir, 'f%04d.jpg')]);
  if (r.status !== 0) throw new Error('ffmpeg no pudo extraer los cuadros de ' + f);
  console.log(`cuadros de ${f}: ${fs.readdirSync(dir).length}`);
}

// ---- 2. reparto por duración de la narración
const js = fs.readFileSync(path.join(FINAL, 'assets', 'data', 'narracion.js'), 'utf8');
const N = JSON.parse(js.slice(js.indexOf('=') + 1).trim().replace(/;\s*$/, ''));
const pausa = Number(N.pausa_s || 0.6);
// las láminas con video se capturan más despacio: se las pondera algo más
const peso = (id) => (['elasticidad-plana', 'bloqueo', 'portada', 'isoparametrico', 'gauss'].includes(id) ? 1.6 : 1);
const lam = N.orden.map((id) => ({ id, dur: N.laminas[id].pasos.reduce((s, p) => s + p.dur + pausa, 0) }));
const total = lam.reduce((s, l) => s + l.dur * peso(l.id), 0);
const grupos = [];
let acum = 0, actual = [];
for (const l of lam) {
  actual.push(l);
  acum += l.dur * peso(l.id);
  if (acum >= (total / PARTES) * (grupos.length + 1) && grupos.length < PARTES - 1) { grupos.push(actual); actual = []; }
}
if (actual.length) grupos.push(actual);

// ---- 3. captura en paralelo
const rel = path.relative(FINAL, CUADROS).split(path.sep).join('/');
const t0 = Date.now();
const procesos = grupos.map((g, k) => new Promise((res, rej) => {
  const dir = path.join(TRABAJO, `parte${k + 1}`);
  fs.rmSync(dir, { recursive: true, force: true });
  const args = [path.join(AQUI, 'capturar_video.mjs'), `--desde=${g[0].id}`, `--hasta=${g[g.length - 1].id}`, `--trabajo=${dir}`, `--cuadros=${rel}`];
  if (flags.tema) args.push(`--tema=${flags.tema}`);
  if (flags.fps) args.push(`--fps=${flags.fps}`);
  console.log(`parte ${k + 1}: ${g[0].id} … ${g[g.length - 1].id}  (${(g.reduce((s, l) => s + l.dur, 0) / 60).toFixed(1)} min de voz)`);
  const p = spawn(process.execPath, args, { stdio: ['ignore', 'pipe', 'pipe'] });
  const log = fs.createWriteStream(path.join(TRABAJO, `parte${k + 1}.log`));
  p.stdout.pipe(log); p.stderr.pipe(log);
  p.stdout.on('data', (d) => { const s = String(d).trim(); if (s) console.log(`  [${k + 1}] ${s.split('\n').pop()}`); });
  p.on('close', (c) => (c === 0 ? res(dir) : rej(new Error(`la parte ${k + 1} terminó con código ${c} (ver ${path.join(TRABAJO, `parte${k + 1}.log`)})`))));
}));
const dirs = await Promise.all(procesos);
console.log(`\n[OK] captura en ${((Date.now() - t0) / 60000).toFixed(1)} min`);
console.log('Montar con:\n  .venv\\Scripts\\python.exe tesis\\presentacion\\final\\herramientas\\montar_video.py --trabajo=' + dirs.join(','));
