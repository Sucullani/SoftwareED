/* =====================================================================
   viz/diseno.js — animaciones del bloque «Diseño y desarrollo del modelo».
   Todo número que aparece sale de EDUFEM_DATOS (motor de EduFEM).
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const DAT = () => window.EDUFEM_DATOS;
  const est = (e, o) => EF.estiloSvg(e, o);
  const S = EF.svg;

  // ------------------------------------------------------------------ utilidades del ejemplo canónico
  function canonico() {
    const C = DAT().canonico;
    const P = C.nodos.map((n) => [n.x, n.y]);
    const idx = Object.fromEntries(C.nodos.map((n, i) => [n.id, i]));
    const elems = Object.entries(C.elementos_conect).map(([k, con]) => ({ id: Number(k), con: con.map((n) => idx[n]) }));
    const u = C.nodos.map((n, i) => [C.u[2 * i], C.u[2 * i + 1]]);
    return { C, P, idx, elems, u };
  }
  EF.canonico = canonico;
  const mat = (M, dec) => '\\begin{bmatrix}' + M.map((f) => (Array.isArray(f) ? f : [f]).map((v) => EF.tex(v, dec)).join('&')).join('\\\\') + '\\end{bmatrix}';
  const vecT = (v, dec) => '\\begin{bmatrix}' + v.map((x) => EF.tex(x, dec)).join('&') + '\\end{bmatrix}^{T}';
  EF.texMat = mat;

  /** Invariantes a partir de las componentes (como el motor: se recalculan, no se extrapolan). */
  function invariantes(sx, sy, txy) {
    const c = 0.5 * (sx + sy), r = Math.hypot(0.5 * (sx - sy), txy);
    const s1 = c + r, s2 = c - r;
    return { c, r, s1, s2, vm: Math.sqrt(s1 * s1 - s1 * s2 + s2 * s2), tp: 0.5 * Math.atan2(2 * txy, sx - sy) };
  }
  EF.invariantes = invariantes;

  // ================================================================== casos de estudio (mallas reales)
  EF.registrarViz('casos', function (cont) {
    const D = DAT();
    const fila = EF.el('div', { class: 'rejilla-4', style: 'gap:22px' });
    cont.appendChild(fila);
    const tarjetas = [
      {
        t: 'Soluciones manufacturadas', s: '4 configuraciones · N = 2 … 32 · Q4 y Q9',
        ej: 'Fuerza de volumen, restricciones no homogéneas y mapeo distorsionado, en tensión y en deformación plana',
        ref: 'Solución exacta construida', dib: (lz) => {
          const c = D.mms.campos.Q4['8'];
          lz.encuadrar(-0.05, 1.05, -0.05, 1.05, 18);
          lz.inicio(EF.css('--lienzo'));
          lz.rellenoElementos(c.nodos, c.elems, c.err, { log: true, min: Math.min(...c.err), max: Math.max(...c.err) });
          lz.malla(c.nodos, c.elems, { color: 'rgba(255,255,255,.45)', ancho: 1 });
        },
      },
      {
        t: 'Viga de Timoshenko', s: 'Q9 56 × 8 · 1921 nodos · 3842 GDL',
        ej: 'Carga superficial uniforme y apoyos; tensión plana',
        ref: 'Analítica de Timoshenko y Goodier [13] y SAP2000 [19]', dib: (lz) => {
          const T = D.timoshenko;
          lz.encuadrar(-7.2, 7.2, -2.2, 2.0, { s: 20, d: 12, i: 20, iz: 12 });
          lz.inicio(EF.css('--lienzo'));
          const u = T.u.map((p) => [p[0] / 100, p[1] / 100]);
          lz.campo(T.nodos, T.elems, T.sx, { u, escala: 40, sub: 2 });
          lz.malla(T.nodos, T.elems.filter((_, k) => k % 1 === 0), { color: 'rgba(0,0,0,.25)', ancho: 0.6, u, escala: 40 });
          lz.apoyo(-7, 0, { tam: 9 }); lz.apoyo(7, 0, { tam: 9, movil: true });
          for (let x = -6.5; x <= 6.6; x += 1.3) lz.flecha(x, 0.62, 0, -1, { largo: 22, ancho: 2 });
        },
      },
      {
        t: 'Membrana de Cook', s: 'Q4 y Q9 · N = 2 … 32',
        ej: 'Distorsión trapezoidal bajo cortante y flexión: el caso que bloquea al Q4',
        ref: '23,96; publicado 23,965 [26, p. 28]', dib: (lz) => {
          const c = D.cook.casos.Q9['8'];
          lz.encuadrar(-2, 52, -3, 64, 16);
          lz.inicio(EF.css('--lienzo'));
          lz.campo(c.nodos, c.elems, c.vm, { max: EF.percentil(c.vm, 96), u: c.u, escala: 0.4, sub: 3 });
          lz.malla(c.nodos, c.elems, { color: 'rgba(0,0,0,.35)', ancho: 0.8, u: c.u, escala: 0.4 });
          lz.empotramiento(0, 0, 44, {});
        },
      },
      {
        t: 'Ejemplo canónico', s: '9 nodos · 4 elementos Q4 · P = 1000',
        ej: 'No mide exactitud: demuestra que la memoria se rehace a mano',
        ref: 'Anexo G', dib: (lz) => {
          const { C, P, idx, elems } = canonico();
          lz.encuadrar(-0.8, 11.8, -1.4, 9.4, 16);
          lz.inicio(EF.css('--lienzo'));
          lz.malla(P, elems.map((e) => e.con), { color: EF.css('--malla'), ancho: 2.2 });
          lz.nodos(P, P.map((_, i) => i), { radio: 5 });
          for (const a of C.apoyos) lz.apoyo(P[idx[a]][0], P[idx[a]][1], { tam: 11 });
          lz.flecha(P[idx[7]][0], P[idx[7]][1], 0, -1, { largo: 44, ancho: 3 });
          elems.forEach((e) => { const cx = e.con.reduce((s, i) => s + P[i][0], 0) / 4, cy = e.con.reduce((s, i) => s + P[i][1], 0) / 4; lz.etiqueta(cx, cy, 'E' + e.id, { ancla: 'center', tam: 18, color: EF.css('--texto-3') }); });
        },
      },
    ];
    const lienzos = [];
    tarjetas.forEach((t, k) => {
      const card = EF.el('div', { class: 'tarjeta', style: 'padding:0;overflow:hidden', 'data-entrada': String(k + 1) });
      const caja = EF.el('div', { style: 'height:250px;background:var(--lienzo)' });
      card.appendChild(caja);
      const lz = new EF.LienzoMEF(caja, 395, 250);
      lienzos.push([lz, t.dib]);
      card.appendChild(EF.el('div', { style: 'padding:18px 22px 22px' }, [
        EF.el('h3', { style: 'font-size:32px;margin:0 0 4px', text: t.t }),
        EF.el('div', { class: 'mini', style: 'margin-bottom:12px', text: t.s }),
        EF.el('p', { style: 'font-size:23px;color:var(--texto);margin:0 0 12px', html: '<b style="color:var(--acento)">Ejercita:</b> ' + t.ej }),
        EF.el('p', { style: 'font-size:21px;margin:0', html: '<b>Referencia:</b> ' + t.ref }),
      ]));
      fila.appendChild(card);
    });
    const dibujar = () => lienzos.forEach(([lz, f]) => { lz.redimensionar(); f(lz); });
    return { entrar: dibujar, redimensionar: dibujar, tema: dibujar };
  });

  // ================================================================== criterios (umbral) y veredicto
  const CRIT = [
    { cl: 'a', c: 'Etapas con módulo educativo', p: 'Exhaustividad', u: '7 de 7', o: '7 de 7', r: 'Una etapa sin módulo', ir: 'cobertura-procedimiento' },
    { cl: 'a', c: 'Etapas con desarrollo en la memoria', p: 'Exhaustividad', u: '9 de 9', o: '9 de 9', r: 'Una etapa sin desarrollo', ir: 'memoria' },
    { cl: 'a', c: 'Solución y tensiones en el post-proceso', p: 'Modo crudo y suavizado', u: 'Ambas', o: 'Ambas', r: 'Una sin exposición', ir: 'postproceso' },
    { cl: 'a', c: 'Fases sobre el mismo lienzo', p: 'Exhaustividad', u: '3 de 3', o: '3 de 3', r: 'Una fase en otra vista', ir: 'cobertura-procedimiento' },
    { cl: 'a', c: 'Ítems de contenido con instrumento', p: 'Consenso de 67 expertos [3]', u: '18 de 18', o: '18 de 18', r: 'Un ítem sin instrumento', ir: 'cobertura-contenido' },
    { cl: 'a', c: 'Intercambio CSV / DXF; memoria Q4 y Q9', p: 'Ida y vuelta e importación repetible', u: 'Sin pérdida y sin error', o: 'Sin pérdida y sin error', r: 'Una entidad perdida o un error', ir: 'consistencia-interna' },
    { cl: 'b', c: 'Tasa L² del desplazamiento', p: '4 configuraciones · medio orden', u: 'teórica ± 0,5', o: '2,00 · 3,00', r: 'Una tasa fuera de margen', ir: 'mms' },
    { cl: 'b', c: 'Tasa H¹ del desplazamiento', p: '4 configuraciones · medio orden', u: 'teórica ± 0,5', o: '1,00 · 2,00', r: 'Una tasa fuera de margen', ir: 'mms' },
    { cl: 'b', c: 'Flecha frente a la analítica', p: 'Timoshenko · tolerancia del autor', u: '< 3 %', o: '0,2633 %', r: 'Un error mayor', ir: 'timoshenko' },
    { cl: 'b', c: 'σx frente a la analítica, 3 puntos', p: 'Timoshenko · tolerancia del autor', u: '< 1 %', o: 'máx. 0,04 %', r: 'Un valor mayor', ir: 'timoshenko' },
    { cl: 'b', c: 'σx frente a SAP2000, 3 puntos', p: 'Diferencia, no error', u: '< 1 %', o: 'máx. 0,21 %', r: 'Un valor mayor', ir: 'timoshenko' },
    { cl: 'b', c: 'Residuo del equilibrio de reacciones', p: 'Cero numérico del motor', u: '< 10⁻⁸', o: '1,7 × 10⁻¹³', r: 'Un residuo mayor', ir: 'timoshenko' },
    { cl: 'b', c: 'Error con Q9 y N = 8 (Cook)', p: 'Tolerancia del autor', u: '< 1,5 %', o: '0,144 %', r: 'Un error mayor', ir: 'cook' },
    { cl: 'b', c: 'Flecha Q4 < Q9, misma malla', p: 'Predicción: bloqueo por cortante', u: 'Se observa', o: '22,079 < 23,925', r: 'Que no se observe', ir: 'cook' },
    { cl: 'b', c: 'Memoria: etapas remitidas a su ecuación', p: 'Ejemplo canónico · Anexo G', u: 'Todas', o: 'Todas', r: 'Una etapa sin desarrollo cotejable', ir: 'memoria' },
  ];
  EF.registrarViz('criterios', function (cont) {
    const modo = cont.getAttribute('data-modo') || 'umbral';
    const cols = EF.el('div', { class: 'criterios ' + modo });
    cont.appendChild(cols);
    const colA = EF.el('div'), colB = EF.el('div');
    const hA = EF.el('h4', { style: 'color:var(--acento)' }), hB = EF.el('h4', { style: 'color:var(--primario)' });
    colA.appendChild(hA); colB.appendChild(hB);
    const filas = CRIT.map((k) => {
      const f = EF.el('div', { class: 'crit' + (modo === 'veredicto' ? ' enlace' : '') });
      const o = EF.el('div', { class: modo === 'umbral' ? 'o refuta' : 'o', text: modo === 'umbral' ? k.r : '·' });
      f.append(EF.el('div', { class: 'c', html: `${k.c}<small>${k.p}</small>` }), EF.el('div', { class: 'u', text: k.u }), o);
      if (modo === 'veredicto') { f.setAttribute('data-ir', k.ir); f.title = 'Ver la evidencia'; }
      (k.cl === 'a' ? colA : colB).appendChild(f);
      return { f, o, k };
    });
    cols.append(colA, colB);
    if (modo === 'umbral') colB.setAttribute('data-paso', '1');
    const encabezados = (na, nb) => {
      hA.innerHTML = `(a) Trazabilidad${na != null ? ` · <span style="color:var(--ok)">${na} de 6</span>` : ''}`;
      hB.innerHTML = `(b) Verificabilidad${nb != null ? ` · <span style="color:var(--ok)">${nb} de 9</span>` : ''}`;
    };
    encabezados();
    const banner = EF.el('div', { class: 'explica', style: 'margin-top:26px;background:var(--ok-suave);font-size:31px;font-weight:650', 'data-paso': '2', html: '<b style="color:var(--ok)">15 de 15.</b> La hipótesis queda comprobada en sus dos cláusulas, dentro del alcance declarado.' });
    if (modo === 'veredicto') colA.appendChild(banner);
    function marcar(i, v) { if (modo === 'umbral') return; const F = filas[i]; F.o.textContent = v ? F.k.o : '·'; F.o.classList.toggle('medido', v); }
    function estado(p) {
      filas.forEach((F, i) => marcar(i, modo === 'veredicto' && ((F.k.cl === 'a' && p >= 1) || (F.k.cl === 'b' && p >= 2))));
      if (modo === 'veredicto') encabezados(p >= 1 ? 6 : null, p >= 2 ? 9 : null);
    }
    function animar(cl) {
      const sel = filas.map((F, i) => [F, i]).filter(([F]) => F.k.cl === cl);
      sel.forEach(([F, i], j) => EF.tween({ dur: 380, retraso: 250 + j * 420, curva: 'rebote', cada: (t) => { if (t > 0.05 && !F.o.classList.contains('medido')) marcar(i, true); F.o.style.transform = `scale(${0.6 + 0.4 * t})`; }, fin: () => { F.o.style.transform = ''; encabezados(cl === 'a' ? j + 1 : 6, cl === 'b' ? j + 1 : null); } }));
    }
    return {
      entrar(p, op) { estado(p); if (modo === 'veredicto' && !op.instantaneo && !op.impresion && p >= 1) { if (p === 1) { filas.forEach((F, i) => marcar(i, false)); encabezados(); animar('a'); } } },
      paso(k, op) {
        if (modo !== 'veredicto') return;
        if (op.adelante && k === 1) { estado(0); animar('a'); }
        else if (op.adelante && k === 2) { estado(1); animar('b'); }
        else estado(k);
      },
    };
  });

  // ================================================================== arquitectura
  EF.registrarViz('arquitectura', function (cont) {
    const W = 1720, H = 700;
    const s = S('svg', { class: 'viz', width: W, height: H, viewBox: `0 0 ${W} ${H}` }, cont);
    const cx = 860, cy = 232;
    const capas = [
      { n: 'gui/', d: ['Interfaz: pre-proceso,', 'lienzo y post-proceso'], a: -150 },
      { n: 'fem/', d: ['Motor del MEF', '(NumPy / SciPy puros)'], a: -90, clave: true },
      { n: 'education/', d: ['Módulos educativos', 'M0 a M7'], a: -30 },
      { n: 'file_io/', d: ['Proyecto, CSV, DXF', 'y memoria PDF'], a: 30 },
      { n: 'config/', d: ['Constantes, unidades', 'y paletas de color'], a: 90 },
      { n: 'models/', d: ['Modelo, comprobador de', 'salud, deshacer / rehacer'], a: 150 },
    ];
    const lineas = S('g', {}, s);
    const gNod = S('g', {}, s);
    const pos = capas.map((c) => [cx + 600 * Math.cos((c.a * Math.PI) / 180), cy + 168 * Math.sin((c.a * Math.PI) / 180)]);
    const ls = pos.map((p) => { const l = S('line', { x1: cx, y1: cy, x2: p[0], y2: p[1] }, lineas); est(l, { trazo: 'var(--linea-2)', estilo: 'stroke-width:3;stroke-dasharray:10 10' }); return l; });
    const centro = S('g', {}, gNod);
    est(S('rect', { x: cx - 230, y: cy - 78, width: 460, height: 156, rx: 26 }, centro), { relleno: 'var(--acento-suave)', trazo: 'var(--acento)', estilo: 'stroke-width:3' });
    est(S('text', { x: cx, y: cy - 16, 'text-anchor': 'middle', text: 'ProjectModel' }, centro), { relleno: 'var(--acento)', estilo: 'font:800 40px var(--mono)' });
    est(S('text', { x: cx, y: cy + 24, 'text-anchor': 'middle', text: 'el estado completo del análisis,' }, centro), { relleno: 'var(--texto)', estilo: 'font:600 23px var(--fuente)' });
    est(S('text', { x: cx, y: cy + 54, 'text-anchor': 'middle', text: 'una sola copia compartida' }, centro), { relleno: 'var(--texto)', estilo: 'font:600 23px var(--fuente)' });
    const nodos = capas.map((c, k) => {
      const [x, y] = pos[k];
      const g = S('g', { transform: `translate(${x - 165},${y - 58})` }, gNod);
      est(S('rect', { x: 0, y: 0, width: 330, height: 116, rx: 20 }, g), { relleno: 'var(--superficie-2)', trazo: c.clave ? 'var(--primario)' : 'var(--linea-2)', estilo: `stroke-width:${c.clave ? 3 : 1.5}` });
      est(S('text', { x: 24, y: 42, text: c.n }, g), { relleno: c.clave ? 'var(--primario)' : 'var(--texto)', estilo: 'font:800 30px var(--mono)' });
      c.d.forEach((t, j) => est(S('text', { x: 24, y: 74 + j * 26, text: t }, g), { relleno: 'var(--texto-2)', estilo: 'font:600 20px var(--fuente)' }));
      if (c.clave) {
        const b = S('g', { transform: 'translate(150,16)' }, g);
        est(S('rect', { x: 0, y: 0, width: 166, height: 32, rx: 16 }, b), { relleno: 'var(--primario)' });
        est(S('text', { x: 83, y: 22, 'text-anchor': 'middle', text: 'sin interfaz gráfica' }, b), { relleno: '#fff', estilo: 'font:750 16px var(--fuente)' });
      }
      g.style.opacity = '0';
      return g;
    });
    const pulso = S('circle', { r: 9 }, s); est(pulso, { relleno: 'var(--ok)' }); pulso.style.opacity = '0';
    // tecnologías (paso 1)
    const techs = EF.el('div', { 'data-paso': '1', style: 'position:absolute;left:0;top:548px;width:1720px' });
    techs.appendChild(EF.el('div', { style: 'font:800 20px var(--fuente);letter-spacing:.12em;text-transform:uppercase;color:var(--texto-3);margin-bottom:10px', text: 'Tecnologías empleadas (Tabla 2.5)' }));
    const chips = ['Python', 'NumPy · SciPy', 'tkinter + ttkbootstrap', 'pylatex + TeX Live', 'PyMuPDF', 'ezdxf', 'Pillow', 'manim (videos)', 'PyInstaller + Inno Setup'];
    techs.appendChild(EF.el('div', { style: 'display:flex;gap:10px;flex-wrap:wrap' }, chips.map((t) => EF.el('span', { class: 'ficha', style: 'font-size:21px;padding:8px 14px;color:var(--texto)', text: t }))));
    techs.appendChild(EF.el('div', { class: 'mini', style: 'margin-top:12px', html: 'Todas de código abierto. Salvo manim, con la que los videos se generan antes de empaquetar, todas van dentro del instalador, incluido el TeX Live que compila la memoria. PyMuPDF se distribuye bajo AGPL-3.0 (nota de la Tabla 2.5).' }));
    cont.appendChild(techs);
    const nota = EF.el('div', { class: 'explica', 'data-paso': '2', style: 'position:absolute;left:0;top:474px;width:1720px;margin:0;font-size:27px;padding:10px 24px', html: 'Módulos, memoria y guiones de verificación llaman a <b>las mismas funciones del motor</b>: lo expuesto es lo que se calculó.' });
    cont.appendChild(nota);
    let bucle = null;
    function pulsos() {
      if (bucle) bucle.detener();
      const destinos = [2, 3];
      bucle = EF.bucle((t) => {
        const k = destinos[Math.floor(t / 1.2) % 2];
        const f = (t % 1.2) / 1.2;
        const a = pos[1], b = pos[k];
        const x = f < 0.5 ? a[0] + (cx - a[0]) * f * 2 : cx + (b[0] - cx) * (f - 0.5) * 2;
        const y = f < 0.5 ? a[1] + (cy - a[1]) * f * 2 : cy + (b[1] - cy) * (f - 0.5) * 2;
        pulso.setAttribute('cx', x); pulso.setAttribute('cy', y); pulso.style.opacity = '1';
      });
    }
    return {
      entrar(p, op) {
        if (op.instantaneo || op.impresion) { nodos.forEach((g) => (g.style.opacity = '1')); }
        else nodos.forEach((g, k) => { g.style.opacity = '0'; EF.tween({ dur: 450, retraso: 300 + k * 160, cada: (t) => { g.style.opacity = String(t); } }); });
        ls.forEach((l, k) => { if (!op.instantaneo && !op.impresion) EF.trazar(l, { dur: 500, retraso: 200 + k * 160, conservar: false }); });
        if (p >= 2 && !op.impresion) pulsos(); else pulso.style.opacity = '0';
      },
      paso(k) { if (k >= 2) pulsos(); else { if (bucle) { bucle.detener(); bucle = null; } pulso.style.opacity = '0'; } },
      salir() { if (bucle) { bucle.detener(); bucle = null; } },
    };
  });

  // ================================================================== motor: identidad vs índice + matriz dispersa
  EF.registrarViz('motor', function (cont) {
    const W = 1720, H = 700;
    // --- izquierda: identidad del nodo -> índice -> GDL
    const s = S('svg', { class: 'viz', width: 820, height: 640, viewBox: '0 0 820 640', style: 'position:absolute;left:0;top:0' }, cont);
    est(S('text', { x: 0, y: 28, text: 'Lo que ve el usuario → lo que usa el sistema' }, s), { relleno: 'var(--texto-2)', estilo: 'font:750 27px var(--fuente)' });
    const ids = [1, 5, 50, 99];
    const g = S('g', { transform: 'translate(0,70)' }, s);
    const filas = [];
    ids.forEach((id, k) => {
      const y = k * 96;
      const r1 = S('g', { transform: `translate(0,${y})` }, g);
      est(S('rect', { x: 0, y: 0, width: 150, height: 70, rx: 14 }, r1), { relleno: 'var(--superficie-2)', trazo: 'var(--nodo)', estilo: 'stroke-width:2' });
      est(S('text', { x: 75, y: 46, 'text-anchor': 'middle', text: 'nodo ' + id }, r1), { relleno: 'var(--texto)', estilo: 'font:750 26px var(--fuente)' });
      const fl = S('path', { d: `M160,${y + 35} L290,${y + 35}` }, g); est(fl, { trazo: 'var(--texto-3)', estilo: 'stroke-width:3;stroke-dasharray:6 6' });
      const r2 = S('g', { transform: `translate(300,${y})` }, g);
      est(S('rect', { x: 0, y: 0, width: 110, height: 70, rx: 14 }, r2), { relleno: 'var(--acento-suave)', trazo: 'var(--acento)', estilo: 'stroke-width:2' });
      est(S('text', { x: 55, y: 46, 'text-anchor': 'middle', text: 'i = ' + k }, r2), { relleno: 'var(--acento)', estilo: 'font:800 26px var(--fuente)' });
      const fl2 = S('path', { d: `M420,${y + 35} L520,${y + 35}` }, g); est(fl2, { trazo: 'var(--texto-3)', estilo: 'stroke-width:3;stroke-dasharray:6 6' });
      const r3 = S('g', { transform: `translate(530,${y})` }, g);
      est(S('rect', { x: 0, y: 0, width: 250, height: 70, rx: 14 }, r3), { relleno: 'var(--primario-suave)', trazo: 'var(--primario)', estilo: 'stroke-width:2' });
      est(S('text', { x: 125, y: 46, 'text-anchor': 'middle', text: `GDL ${2 * k} y ${2 * k + 1}` }, r3), { relleno: 'var(--primario)', estilo: 'font:800 26px var(--fuente)' });
      filas.push([r1, fl, r2, fl2, r3]);
    });
    est(S('text', { x: 160, y: 58, text: 'node_index_map' }, s), { relleno: 'var(--texto-3)', estilo: 'font:600 19px var(--mono)' });
    const pie = EF.el('div', { style: 'position:absolute;left:0;top:470px;width:800px' });
    pie.innerHTML = '<div class="tarjeta plana" style="padding:18px 22px"><div style="font-size:28px;line-height:1.3"><b>K</b> se dimensiona 2N = 8, no 2 · máx(id) = 198. Mismo problema con {1, 2, 3, 4}: diferencia <b style="color:var(--ok)">&lt; 10⁻⁹</b> (§ 3.3).</div></div>';
    cont.appendChild(pie);
    // --- derecha: patrón de dispersión de K (Cook Q9, N = 8)
    const der = EF.el('div', { 'data-paso': '1', style: 'position:absolute;left:880px;top:0;width:840px;height:640px' });
    cont.appendChild(der);
    der.appendChild(EF.el('div', { style: 'font:750 27px var(--fuente);color:var(--texto-2);margin-bottom:12px', text: 'Patrón de K: membrana de Cook, Q9, N = 8 (578 GDL)' }));
    const caja = EF.el('div', { style: 'position:absolute;left:0;top:50px;width:430px;height:430px;border-radius:12px;overflow:hidden;border:1px solid var(--linea-2);background:var(--lienzo)' });
    der.appendChild(caja);
    const cv = EF.el('canvas', { style: 'width:430px;height:430px' });
    caja.appendChild(cv);
    const info = EF.el('div', { style: 'position:absolute;left:460px;top:50px;width:380px' });
    der.appendChild(info);
    const c8 = DAT().cook.casos.Q9['8'];
    const n = c8.gdl;
    let nnz = 0;
    function pintar() {
      const r = EF.escalaRender();
      cv.width = 430 * r; cv.height = 430 * r;
      const ctx = cv.getContext('2d');
      ctx.fillStyle = EF.css('--lienzo'); ctx.fillRect(0, 0, cv.width, cv.height);
      const esc = cv.width / n;
      const marca = new Uint8Array(n * n);
      nnz = 0;
      for (const con of c8.elems) {
        const dofs = con.flatMap((i) => [2 * i, 2 * i + 1]);
        for (const a of dofs) for (const b of dofs) { const k = a * n + b; if (!marca[k]) { marca[k] = 1; nnz++; } }
      }
      ctx.fillStyle = EF.css('--acento');
      for (let a = 0; a < n; a++) for (let b = 0; b < n; b++) if (marca[a * n + b]) ctx.fillRect(b * esc, a * esc, Math.max(1, esc), Math.max(1, esc));
      info.innerHTML = `<div class="etq" style="margin-bottom:10px;font:750 19px/1.2 var(--fuente);letter-spacing:.1em;text-transform:uppercase;color:var(--texto-3)">Memoria de K (Tabla 3.9)</div><div class="kpi acento"><div class="valor" style="font-size:74px">0,21<small>MB</small></div><div class="etq">dispersa, frente a <b>3 MB</b> densa</div></div>
        <div class="mini" style="margin-top:18px">El patrón dibujado: ${EF.fmt(nnz, 0)} coeficientes no nulos de ${EF.fmt(n * n, 0)} (${EF.fmt((100 * nnz) / (n * n), 1)} %).</div>`;
    }
    const sol = EF.el('div', { 'data-paso': '2', class: 'tarjeta', style: 'position:absolute;left:880px;top:500px;width:840px;padding:18px 24px' });
    sol.innerHTML = '<div class="etq">Solución directa (§ 2.2.5)</div><p style="font-size:25px;color:var(--texto);line-height:1.35">Factorización LU dispersa (SuperLU) con reordenamiento de mínimo grado sobre Kᵀ + K. Junto al motor por lotes se conserva la <b>versión legible</b> elemento a elemento: es el patrón de comparación de las pruebas de regresión.</p>';
    cont.appendChild(sol);
    return {
      entrar(p, op) {
        pintar();
        if (!op.instantaneo && !op.impresion) filas.forEach((f, k) => f.forEach((e, j) => { e.style.opacity = '0'; EF.tween({ dur: 350, retraso: 200 + k * 380 + j * 110, cada: (t) => { e.style.opacity = String(t); } }); }));
        else filas.forEach((f) => f.forEach((e) => (e.style.opacity = '1')));
      },
      redimensionar: pintar, tema: pintar,
    };
  });

  // ================================================================== ensamblaje (K 18 x 18 real)
  EF.registrarViz('ensamblaje', function (cont) {
    const { C, P, idx, elems, u } = canonico();
    const caja = EF.el('div', { style: 'position:absolute;left:0;top:0;width:740px;height:640px;border-radius:18px;overflow:hidden;border:1px solid var(--linea-2)' });
    cont.appendChild(caja);
    const lz = new EF.LienzoMEF(caja, 740, 640);
    const n = 18, cel = 30, x0 = 830, y0 = 34;
    const s = S('svg', { class: 'viz', width: 890, height: 640, viewBox: `0 0 890 640`, style: 'position:absolute;left:800px;top:0' }, cont);
    const g = S('g', {}, s);
    const celdas = [];
    for (let i = 0; i < n; i++) { celdas.push([]); for (let j = 0; j < n; j++) { const r = S('rect', { x: 40 + j * cel, y: y0 + i * cel, width: cel - 2, height: cel - 2, rx: 3 }, g); est(r, { relleno: 'var(--superficie-3)' }); celdas[i].push(r); } }
    for (let i = 0; i < n; i++) {
      est(S('text', { x: 40 + i * cel + cel / 2 - 1, y: y0 - 8, 'text-anchor': 'middle', text: String(i) }, g), { relleno: 'var(--texto-3)', estilo: 'font:600 13px var(--fuente)' });
      est(S('text', { x: 32, y: y0 + i * cel + cel / 2 + 4, 'text-anchor': 'end', text: String(i) }, g), { relleno: 'var(--texto-3)', estilo: 'font:600 13px var(--fuente)' });
    }
    // vector F y u a la derecha
    const colF = [], colU = [];
    const xF = 40 + n * cel + 26, xU = xF + 70;
    est(S('text', { x: xF + 22, y: y0 - 8, 'text-anchor': 'middle', text: 'F' }, g), { relleno: 'var(--texto-2)', estilo: 'font:800 18px var(--fuente)' });
    est(S('text', { x: xU + 44, y: y0 - 8, 'text-anchor': 'middle', text: 'u' }, g), { relleno: 'var(--texto-2)', estilo: 'font:800 18px var(--fuente)' });
    for (let i = 0; i < n; i++) {
      const r = S('rect', { x: xF, y: y0 + i * cel, width: 44, height: cel - 2, rx: 3 }, g); est(r, { relleno: 'var(--superficie-3)' }); colF.push(r);
      const ru = S('text', { x: xU + 88, y: y0 + i * cel + 20, 'text-anchor': 'end', text: '' }, g); est(ru, { relleno: 'var(--texto)', estilo: 'font:650 15px var(--fuente);font-variant-numeric:tabular-nums' }); colU.push(ru);
    }
    const etq = EF.el('div', { style: 'position:absolute;left:800px;top:596px;width:900px;font:650 24px var(--fuente);color:var(--texto-2)' });
    cont.appendChild(etq);
    const K = C.K;
    let vmax = 0; for (const f of K) for (const v of f) vmax = Math.max(vmax, Math.abs(v));
    const restr = new Set(C.restringidos);
    let acum = null, fase = { elem: -1, deform: 0, restr: false, sol: false };
    function reiniciar() { acum = K.map((f) => f.map(() => 0)); }
    function sumarElemento(e) {
      const E = C.elementos[String(e.id)];
      E.dofs.forEach((a, i) => E.dofs.forEach((b, j) => { acum[a][b] += E.ke[i][j]; }));
    }
    function pintarK(activo) {
      const dofsAct = activo ? new Set(C.elementos[String(activo.id)].dofs) : null;
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
        const v = acum[i][j];
        const t = Math.min(1, Math.abs(v) / vmax);
        const r = celdas[i][j];
        let col = v === 0 ? 'var(--superficie-3)' : EF.rgba(v > 0 ? EF.css('--acento') : EF.css('--primario'), 0.18 + 0.82 * Math.sqrt(t));
        if (fase.restr && (restr.has(i) || restr.has(j))) col = 'var(--superficie)';
        r.style.fill = col;
        r.style.stroke = dofsAct && dofsAct.has(i) && dofsAct.has(j) ? 'var(--texto)' : 'none';
        r.style.strokeWidth = '1.5';
      }
      colF.forEach((r, i) => { r.style.fill = C.F[i] !== 0 ? 'var(--carga)' : (fase.restr && restr.has(i) ? 'var(--superficie)' : 'var(--superficie-3)'); });
      colU.forEach((t, i) => { t.textContent = fase.sol ? (restr.has(i) ? '0' : EF.fmtCient(C.u[i], 2)) : ''; t.style.fill = restr.has(i) ? 'var(--texto-3)' : 'var(--texto)'; });
    }
    function dibujarMalla(activo) {
      lz.redimensionar();
      lz.encuadrar(-0.8, 11.8, -1.2, 9.4, 28);
      lz.inicio(EF.css('--lienzo'));
      const esc = 90 * fase.deform;
      if (fase.deform > 0) lz.malla(P, elems.map((e) => e.con), { color: EF.css('--texto-3'), discontinua: [6, 6], ancho: 1.2 });
      lz.malla(P, elems.map((e) => e.con), { color: EF.css('--malla'), ancho: 2.2, u, escala: esc });
      if (activo) lz.elemento(P, activo.con, { color: EF.css('--acento'), ancho: 4, relleno: EF.css('--acento'), alfaRelleno: 0.22, u, escala: esc });
      lz.nodos(P, P.map((_, i) => i), { radio: 6, u, escala: esc });
      C.nodos.forEach((nd, i) => {
        const p = EF.LienzoMEF.pos(P, u, esc, i);
        lz.etiqueta(p[0], p[1], `${nd.id}`, { dx: -14, dy: -16, tam: 19, color: EF.css('--texto'), ancla: 'right' });
        lz.etiqueta(p[0], p[1], `${2 * i}·${2 * i + 1}`, { dx: 12, dy: 18, tam: 16, color: EF.css('--acento') });
      });
      for (const a of C.apoyos) { const p = P[idx[a]]; lz.apoyo(p[0], p[1], { tam: 12 }); }
      const p7 = EF.LienzoMEF.pos(P, u, esc, idx[7]);
      lz.flecha(p7[0], p7[1], 0, -1, { largo: 50, ancho: 3.5, texto: 'P = 1000', dxTexto: 0 });
      if (fase.sol) {
        for (const a of C.apoyos) {
          const i = idx[a], p = P[i];
          const rx = C.R[2 * i], ry = C.R[2 * i + 1];
          lz.etiqueta(p[0], p[1], `R = (${EF.fmt(rx, 1)}; ${EF.fmt(ry, 1)})`, { dy: 48, ancla: 'center', tam: 17, color: '#111', fondo: '#ffa62b', alfaFondo: 0.92 });
        }
      }
      elems.forEach((e) => { const cx = e.con.reduce((s2, i) => s2 + P[i][0], 0) / 4, cy = e.con.reduce((s2, i) => s2 + P[i][1], 0) / 4; lz.etiqueta(cx, cy, 'E' + e.id, { ancla: 'center', tam: 20, color: activo && activo.id === e.id ? EF.css('--acento') : EF.css('--texto-3') }); });
    }
    // el nodo 5 lo comparten los cuatro elementos: K[8][8] acumula cuatro aportes
    function detalleNodo5() {
      const partes = elems.map((e) => { const E = C.elementos[String(e.id)]; const l = E.dofs.indexOf(8); return E.ke[l][l]; });
      return `K<sub>8,8</sub> (nodo 5, compartido): ${partes.map((v) => EF.fmt(v, 0)).join(' + ')} = <b>${EF.fmt(K[8][8], 0)}</b>`;
    }
    let anim = [];
    function cancelar() { anim.forEach((a) => a.cancelar()); anim = []; }
    function ensamblar() {
      cancelar(); reiniciar(); fase = { elem: -1, deform: 0, restr: false, sol: false };
      pintarK(null); dibujarMalla(null);
      elems.forEach((e, k) => anim.push(EF.tween({ dur: 10, retraso: 400 + k * 1500, fin: () => { sumarElemento(e); pintarK(e); dibujarMalla(e); etq.innerHTML = `Ensamblando E${e.id}: sus 8 GDL (${C.elementos[String(e.id)].dofs.join(', ')}) reciben su k<sub>e</sub>`; } })));
      anim.push(EF.tween({ dur: 10, retraso: 400 + 4 * 1500, fin: () => { pintarK(null); dibujarMalla(null); etq.innerHTML = detalleNodo5(); } }));
    }
    function completo() { reiniciar(); elems.forEach(sumarElemento); }
    function estado(p, animar) {
      cancelar();
      if (p === 0) { reiniciar(); fase = { elem: -1, deform: 0, restr: false, sol: false }; pintarK(null); dibujarMalla(null); etq.innerHTML = 'Numeración de GDL: el nodo de índice i ocupa las posiciones 2i y 2i + 1'; return; }
      if (p === 1) { if (animar) { ensamblar(); return; } completo(); fase = { elem: -1, deform: 0, restr: false, sol: false }; pintarK(null); dibujarMalla(null); etq.innerHTML = detalleNodo5(); return; }
      completo();
      fase.restr = true; fase.sol = p >= 3;
      if (p === 2) { fase.deform = 0; pintarK(null); dibujarMalla(null); etq.innerHTML = `Restricciones en los nodos ${C.apoyos.join(', ')}: quedan ${C.libres.length} incógnitas · K<sub>ff</sub> u<sub>f</sub> = F<sub>f</sub>`; return; }
      pintarK(null);
      const sumRy = C.apoyos.reduce((s2, a) => s2 + C.R[2 * idx[a] + 1], 0);
      etq.innerHTML = `Solución: u en los 12 GDL libres · reacciones: ΣR<sub>y</sub> = ${EF.fmt(sumRy, 2)} = P`;
      if (animar) anim.push(EF.tween({ dur: 1600, curva: 'ambos', cada: (t) => { fase.deform = t; dibujarMalla(null); } }));
      else { fase.deform = 1; dibujarMalla(null); }
    }
    return {
      entrar(p, op) { estado(p, !op.instantaneo && !op.impresion); },
      paso(k, op) { estado(k, op.adelante); },
      salir: cancelar,
      redimensionar() { dibujarMalla(null); }, tema() { pintarK(null); dibujarMalla(null); },
    };
  });

  // ================================================================== post-proceso: contorno, sonda y Mohr
  EF.registrarViz('postproceso', function (cont) {
    const { C, P, idx, elems, u } = canonico();
    const caja = EF.el('div', { style: 'position:absolute;left:0;top:0;width:980px;height:650px;border-radius:18px;overflow:hidden;border:1px solid var(--linea-2)' });
    cont.appendChild(caja);
    const lz = new EF.LienzoMEF(caja, 980, 650);
    const barra = EF.el('div', { style: 'position:absolute;left:850px;top:20px' });
    caja.appendChild(barra);
    const bc = EF.barraColor(barra, { titulo: 'von Mises', alto: 380, ancho: 120 });
    const panel = EF.el('div', { class: 'tarjeta', 'data-paso': '1', style: 'position:absolute;left:1020px;top:0;width:700px;padding:22px 26px' });
    cont.appendChild(panel);
    const seg = EF.el('div', { class: 'segmentado solo-vivo', style: 'position:absolute;right:0;top:-174px' });
    const botones = [['vm', 'von Mises'], ['sx', 'σx'], ['sy', 'σy'], ['txy', 'τxy']].map(([k, t]) => { const b = EF.el('button', { class: k === 'vm' ? 'sel' : '', text: t }); b.onclick = () => { comp = k; botones.forEach((x) => x.classList.toggle('sel', x === b)); dibujar(); }; seg.appendChild(b); return b; });
    cont.appendChild(seg);
    let comp = 'vm', esc = 60, sonda = 7, crudo = false, paso = 0, anguloMohr = 0;
    const valorNodal = (id, k) => C.nodal[String(id)][k];
    const comps = { vm: 'von Mises', sx: 'σx', sy: 'σy', txy: 'τxy' };
    function valoresCrudos(e) {
      const E = C.elementos[String(e.id)];
      return E.sigma_nodal.map((s) => (comp === 'vm' ? s[3] : comp === 'sx' ? s[0] : comp === 'sy' ? s[1] : s[2]));
    }
    function dibujar() {
      lz.redimensionar();
      lz.encuadrar(-0.8, 11.8, -0.9, 9.3, { s: 40, d: 170, i: 40, iz: 40 });
      lz.inicio(EF.css('--lienzo'));
      const vals = C.nodos.map((nd) => valorNodal(nd.id, comp));
      let vmin = Math.min(...vals), vmax = Math.max(...vals);
      if (crudo) for (const e of elems) for (const v of valoresCrudos(e)) { vmin = Math.min(vmin, v); vmax = Math.max(vmax, v); }
      lz.malla(P, elems.map((e) => e.con), { color: EF.css('--texto-3'), ancho: 1.2, discontinua: [6, 6], alfa: 0.6 });
      if (crudo) {
        for (const e of elems) lz.campo(e.con.map((i) => P[i]), [[0, 1, 2, 3]], valoresCrudos(e), { min: vmin, max: vmax, u: e.con.map((i) => u[i]), escala: esc, sub: 6 });
      } else lz.campo(P, elems.map((e) => e.con), vals, { min: vmin, max: vmax, u, escala: esc, sub: 6 });
      lz.malla(P, elems.map((e) => e.con), { color: 'rgba(255,255,255,.7)', ancho: 1.6, u, escala: esc });
      bc.actualizar(vmin, vmax, 1);
      C.nodos.forEach((nd, i) => {
        const p = EF.LienzoMEF.pos(P, u, esc, i);
        lz.nodos([p], [0], { radio: nd.id === sonda && paso >= 1 ? 9 : 5, color: nd.id === sonda && paso >= 1 ? '#ffd23f' : EF.css('--nodo') });
        lz.etiqueta(p[0], p[1], `${nd.id}: ${EF.fmt(valorNodal(nd.id, comp), 2)}`, { dx: 10, dy: -16, tam: 18, color: '#fff', fondo: 'rgba(10,16,30,.72)', alfaFondo: 0.8 });
      });
      const p7 = EF.LienzoMEF.pos(P, u, esc, idx[7]);
      lz.flecha(p7[0], p7[1], 0, -1, { largo: 50, ancho: 3.5 });
      for (const a of C.apoyos) {
        const i = idx[a], p = P[i];
        lz.apoyo(p[0], p[1], { tam: 11 });
        if (paso >= 2) {
          const rx = C.R[2 * i], ry = C.R[2 * i + 1];
          lz.flecha(p[0], p[1], Math.sign(rx) || 1, 0, { largo: 46, ancho: 3, color: '#ffa62b' });
          lz.flecha(p[0], p[1], 0, Math.sign(ry) || 1, { largo: 46, ancho: 3, color: '#ffa62b' });
          lz.etiqueta(p[0], p[1], `Rx = ${EF.fmt(rx, 2)} · Ry = ${EF.fmt(ry, 2)}`, { dy: 66, ancla: 'center', tam: 17, color: '#111', fondo: '#ffa62b', alfaFondo: 0.95 });
        }
      }
      lz.etiqueta(-0.5, 9.0, crudo ? 'Crudo: cada elemento con sus propios valores nodales' : 'Suavizado: promedio en los nodos compartidos', { tam: 21, color: EF.css('--texto-2') });
    }
    function escribirPanel() {
      const nd = C.nodal[String(sonda)];
      const i = idx[sonda];
      const inv = invariantes(nd.sx, nd.sy, nd.txy);
      const R = inv.r, c0 = inv.c;
      const fila = (a, b) => `<tr><td style="color:var(--texto-3);padding-right:18px">${a}</td><td class="num-tab" style="font-weight:700;text-align:right">${b}</td></tr>`;
      panel.innerHTML = `<div class="etq">Sonda · nodo ${sonda} · (${EF.fmt(P[i][0], 1)}; ${EF.fmt(P[i][1], 1)})</div>
        <div style="display:flex;gap:24px;align-items:flex-start">
        <table style="font-size:25px;border-collapse:collapse;line-height:1.5">${fila('ux', EF.fmt(u[i][0], 5))}${fila('uy', EF.fmt(u[i][1], 5))}${fila('σx', EF.fmt(nd.sx, 2))}${fila('σy', EF.fmt(nd.sy, 2))}${fila('τxy', EF.fmt(nd.txy, 2))}${fila('σ₁', EF.fmt(nd.s1, 2))}${fila('σ₂', EF.fmt(nd.s2, 2))}${fila('<b style="color:var(--acento)">VM</b>', '<span style="color:var(--acento)">' + EF.fmt(nd.vm, 2) + '</span>')}</table>
        <div id="mohr-caja"></div></div>
        <div class="mini" style="margin-top:6px">Círculo de Mohr: centro ${EF.fmt(c0, 1)}, radio ${EF.fmt(R, 1)}; θp = ${EF.fmt((inv.tp * 180) / Math.PI, 1)}°. Valores del motor, idénticos a los de la interfaz.</div>`;
      dibujarMohr(inv, nd);
    }
    let svgM = null;
    function dibujarMohr(inv, nd) {
      const caja2 = panel.querySelector('#mohr-caja');
      caja2.innerHTML = '';
      const W = 330, H = 330;
      svgM = S('svg', { class: 'viz', width: W, height: H, viewBox: `0 0 ${W} ${H}` }, caja2);
      const lim = Math.max(Math.abs(inv.s1), Math.abs(inv.s2), inv.r) * 1.12;
      const sx = (v) => W / 2 + ((v - inv.c) / (2 * lim)) * W * 0.95;
      const sy = (v) => H / 2 - (v / (2 * lim)) * H * 0.95;
      est(S('line', { x1: 0, x2: W, y1: sy(0), y2: sy(0) }, svgM), { trazo: 'var(--linea-2)', estilo: 'stroke-width:1.5' });
      est(S('line', { x1: sx(0), x2: sx(0), y1: 0, y2: H }, svgM), { trazo: 'var(--linea-2)', estilo: 'stroke-width:1.5' });
      est(S('circle', { cx: sx(inv.c), cy: sy(0), r: (inv.r / (2 * lim)) * W * 0.95 }, svgM), { relleno: 'none', trazo: 'var(--primario)', estilo: 'stroke-width:3' });
      const p1 = S('circle', { cx: sx(inv.s1), cy: sy(0), r: 8 }, svgM); est(p1, { relleno: 'var(--mal)' });
      const p2 = S('circle', { cx: sx(inv.s2), cy: sy(0), r: 8 }, svgM); est(p2, { relleno: 'var(--mal)' });
      est(S('text', { x: sx(inv.s1) + 6, y: sy(0) - 12, text: 'σ₁' }, svgM), { relleno: 'var(--mal)', estilo: 'font:800 18px var(--fuente)' });
      est(S('text', { x: sx(inv.s2) - 26, y: sy(0) - 12, text: 'σ₂' }, svgM), { relleno: 'var(--mal)', estilo: 'font:800 18px var(--fuente)' });
      const dia = S('line', {}, svgM); est(dia, { trazo: 'var(--aviso)', estilo: 'stroke-width:2;stroke-dasharray:5 5' });
      const pa = S('circle', { r: 8 }, svgM); est(pa, { relleno: 'var(--aviso)' });
      const pb = S('circle', { r: 6 }, svgM); est(pb, { relleno: 'var(--aviso)', estilo: 'opacity:.6' });
      svgM.__actualizar = (ang) => {
        // punto (σx, τxy) girando hacia el eje principal al animar
        const a0 = Math.atan2(nd.txy, nd.sx - inv.c);
        const a = a0 * (1 - ang);
        const X = inv.c + inv.r * Math.cos(a), Y = inv.r * Math.sin(a);
        pa.setAttribute('cx', sx(X)); pa.setAttribute('cy', sy(Y));
        pb.setAttribute('cx', sx(2 * inv.c - X)); pb.setAttribute('cy', sy(-Y));
        dia.setAttribute('x1', sx(X)); dia.setAttribute('y1', sy(Y)); dia.setAttribute('x2', sx(2 * inv.c - X)); dia.setAttribute('y2', sy(-Y));
      };
      svgM.__actualizar(anguloMohr);
    }
    // sonda con clic sobre un nodo (en vivo)
    lz.canvas.addEventListener('click', (ev) => {
      const q = EF.aLocal(lz.canvas, ev.clientX, ev.clientY);
      let mejor = null, dmin = 30;
      C.nodos.forEach((nd, i) => { const p = EF.LienzoMEF.pos(P, u, esc, i); const d = Math.hypot(lz.X(p[0]) - q.x, lz.Y(p[1]) - q.y); if (d < dmin) { dmin = d; mejor = nd.id; } });
      if (mejor != null) { sonda = mejor; anguloMohr = 0; dibujar(); escribirPanel(); }
    });
    let bucle = null;
    function animarMohr() {
      anguloMohr = 0;
      return EF.tween({ dur: 2400, retraso: 600, curva: 'ambos', cada: (t) => { anguloMohr = t; if (svgM) svgM.__actualizar(t); } });
    }
    return {
      entrar(p, op) {
        paso = p; crudo = false; sonda = 7;
        if (!op.instantaneo && !op.impresion && p === 0) { esc = 0; EF.tween({ dur: 1600, retraso: 400, curva: 'ambos', cada: (t) => { esc = 60 * t; dibujar(); } }); }
        else esc = 60;
        dibujar(); escribirPanel();
        if (p === 3 && !op.instantaneo && !op.impresion) alternar();
      },
      paso(k, op) {
        paso = k; crudo = false;
        dibujar(); escribirPanel();
        if (k === 1 && op.adelante) animarMohr();
        if (k === 3 && op.adelante) alternar();
      },
      salir() { if (bucle) { bucle.detener(); bucle = null; } },
      redimensionar: dibujar, tema() { dibujar(); escribirPanel(); },
    };
    function alternar() {
      crudo = true; dibujar();
      EF.tween({ dur: 2800, fin: () => { crudo = false; dibujar(); } });
    }
  });

  // ================================================================== memoria de cálculo (hojas reales del Anexo G)
  EF.registrarViz('memoria', function (cont) {
    const paginas = EF.rango(8).map((k) => `assets/img/anexoG_${k + 1}.png`);
    const marcas = {
      4: [{ x: 0.2865, y: 0.0886, w: 0.0571, h: 0.0142, c: 'acento' }, { x: 0.5606, y: 0.0886, w: 0.0571, h: 0.0142, c: 'acento' }, { x: 0.2199, y: 0.117, w: 0.0571, h: 0.0142, c: 'acento' }, { x: 0.6869, y: 0.1772, w: 0.0547, h: 0.0142, c: 'ok' }, { x: 0.5228, y: 0.565, w: 0.0547, h: 0.0142, c: 'ok' }],
      6: [{ x: 0.5459, y: 0.2556, w: 0.0645, h: 0.0142, c: 'ok' }, { x: 0.271, y: 0.2871, w: 0.0645, h: 0.0142, c: 'ok' }],
      7: [{ x: 0.7651, y: 0.8481, w: 0.0547, h: 0.0142, c: 'ok' }, { x: 0.8148, y: 0.3695, w: 0.0465, h: 0.0118, c: 'ok' }],
    };
    // pila de hojas
    const pila = EF.el('div', { style: 'position:absolute;left:0;top:24px;width:560px;height:640px' });
    cont.appendChild(pila);
    const hojas = paginas.map((src, k) => {
      const h = EF.el('div', { style: `position:absolute;left:${60 + k * 6}px;top:${k * 5}px;width:460px;height:630px;background:#fff;border-radius:6px;box-shadow:0 12px 30px rgba(0,0,0,.45);overflow:hidden;transform-origin:left center` });
      const img = EF.el('img', { src, alt: `Anexo G, hoja ${k + 1}`, class: 'zoomable', style: 'width:100%;height:100%;object-fit:cover;object-position:top' });
      h.appendChild(img);
      const capa = EF.el('div', { style: 'position:absolute;inset:0;pointer-events:none' });
      h.appendChild(capa);
      pila.appendChild(h);
      return { h, capa };
    });
    // lista de capítulos
    const der = EF.el('div', { style: 'position:absolute;left:620px;top:0;width:1100px' });
    cont.appendChild(der);
    const caps = ['Planteo del problema', 'Discretización', 'Calidad de la malla', 'Formulación elemental', 'Ensamblaje', 'Restricciones y solución', 'Post-proceso', 'Diagnóstico y validación', 'Resumen e interpretación'];
    der.innerHTML = `<div class="etq" style="font-size:22px;margin-bottom:12px">Nueve capítulos, el mismo procedimiento que el motor</div>
      <div class="caps-mem">${caps.map((c, k) => `<div class="cap-mem" data-entrada="${k + 1}"><b>${k + 1}</b>${c}</div>`).join('')}</div>
      <div class="rejilla-2" style="margin-top:26px;gap:20px">
        <div class="tarjeta plana"><div class="etq">Dos estilos</div><p style="font-size:24px">Educativo (infografías y glosario) y directo; las fórmulas y matrices se emiten siempre.</p></div>
        <div class="tarjeta plana"><div class="etq">Sin instalar nada más</div><p style="font-size:24px">pylatex + TeX Live embebido: compila sin internet y sin MiKTeX.</p></div>
      </div>`;
    const nota = EF.el('div', { class: 'explica', 'data-paso': '1', style: 'position:absolute;left:620px;top:560px;width:1100px;margin:0;font-size:28px;padding:16px 24px' });
    cont.appendChild(nota);
    let actual = 0, anim = null;
    function mostrar(k, marcasDe) {
      actual = k;
      hojas.forEach((H, j) => {
        const delante = j === k;
        H.h.style.zIndex = String(delante ? 20 : j < k ? j : 10 - j);
        H.h.style.transform = delante ? 'translateX(-40px) rotate(-1.2deg) scale(1.02)' : j < k ? `translateX(${-60 - (k - j) * 4}px) rotate(${-1.5 - (k - j) * 0.45}deg) scale(.96)` : `translateX(0) rotate(${(j - k) * 1.2}deg) scale(.97)`;
        H.h.style.filter = delante ? '' : 'brightness(.72)';
        H.capa.innerHTML = '';
      });
      if (marcasDe) for (const m of marcas[k + 1] || []) {
        hojas[k].capa.appendChild(EF.el('div', { style: `position:absolute;left:${(m.x - 0.006) * 100}%;top:${(m.y - 0.004) * 100}%;width:${(m.w + 0.012) * 100}%;height:${(m.h + 0.008) * 100}%;border:3px solid var(--${m.c});border-radius:4px;background:${m.c === 'ok' ? 'rgba(52,211,153,.18)' : 'rgba(255,138,61,.16)'};box-shadow:0 0 0 4px ${m.c === 'ok' ? 'rgba(52,211,153,.25)' : 'rgba(255,138,61,.22)'}` }));
      }
    }
    function hojear() {
      if (anim) anim.cancelar();
      let k = -1;
      anim = EF.tween({ dur: 8 * 700, curva: 'lineal', cada: (t) => { const j = Math.min(7, Math.floor(t * 8)); if (j !== k) { k = j; mostrar(j, false); } }, fin: () => mostrar(0, false) });
    }
    function estado(p, animar) {
      if (anim) { anim.cancelar(); anim = null; }
      if (p === 0) { if (animar) hojear(); else mostrar(0, false); nota.innerHTML = ''; }
      if (p === 1) { mostrar(3, true); nota.innerHTML = 'Hoja 4 (p. 167): el Jacobiano de E3 remite a las <b style="color:var(--acento)">Ecuaciones 1.9 a 1.11</b> y da <b style="color:var(--ok)">det J = 4,7604</b>: cada valor, con la ecuación de la que sale.'; }
      if (p === 2) {
        if (animar) { mostrar(5, true); anim = EF.tween({ dur: 3000, fin: () => mostrar(6, true) }); } else mostrar(6, true);
        nota.innerHTML = 'Hojas 6 y 7 (pp. 169–170): las reacciones suman <b style="color:var(--ok)">1000,00</b> contra la carga aplicada y el máximo de von Mises es <b style="color:var(--ok)">864,70</b> en el nodo 7.';
      }
    }
    return {
      entrar(p, op) { estado(p, !op.instantaneo && !op.impresion); },
      paso(k, op) { estado(k, op.adelante); },
      salir() { if (anim) { anim.cancelar(); anim = null; } },
    };
  });

  // ================================================================== trazabilidad en acción
  EF.registrarViz('trazar', function (cont) {
    const { C, P, idx, elems, u } = canonico();
    const E3 = C.elementos[String(C.showcase)];
    const nodo = 7;
    const kLoc = E3.nodos.indexOf(nodo);          // 3: el nodo 7 es el 4.º de E3
    const Erow = C.E_extrap[kLoc];                 // fila de la extrapolación
    const gpCerca = Erow.indexOf(Math.max(...Erow)); // el punto de Gauss más próximo (peso a)
    const G = E3.gauss[gpCerca];
    const nd = C.nodal[String(nodo)];
    // barra de etapas (se recorre de 9 hacia 1)
    const barra = EF.el('div', { class: 'traza-barra' });
    EF.ETAPAS.forEach((et) => barra.appendChild(EF.el('div', { class: 'tb', 'data-n': String(et.n), html: `<b>${et.n}</b><span>${et.c}</span>` })));
    barra.appendChild(EF.el('div', { class: 'tb datos', 'data-n': '0', html: '<b>◉</b><span>Datos</span>' }));
    cont.appendChild(barra);
    const caja = EF.el('div', { style: 'position:absolute;left:0;top:96px;width:700px;height:600px;border-radius:18px;overflow:hidden;border:1px solid var(--linea-2)' });
    cont.appendChild(caja);
    const lz = new EF.LienzoMEF(caja, 700, 600);
    const panel = EF.el('div', { class: 'panel-mat traza-panel', style: 'position:absolute;left:740px;top:96px;width:980px;height:600px;overflow:hidden' });
    cont.appendChild(panel);
    const DDf = C.D_factor;
    const Dn = C.D.map((f) => f.map((v) => v / DDf));
    const pasos = [
      {
        etapas: [], titulo: 'Un resultado del post-proceso',
        tex: [`\\sigma_{\\mathrm{VM}}(\\text{nodo }7)=${EF.tex(nd.vm, 2)}`],
        txt: '¿De dónde sale este número? La trazabilidad responde siguiéndolo hacia atrás, etapa por etapa, hasta los datos del modelo.',
        dib: 'contorno',
      },
      {
        etapas: [9], titulo: 'Etapa 9 · extrapolación y promedio',
        tex: [
          `\\boldsymbol{\\sigma}_{7}=\\mathbf{E}_{4\\bullet}\\,\\boldsymbol{\\sigma}_{\\text{Gauss}},\\;\\;\\mathbf{E}_{4\\bullet}=${vecT(Erow, 3).replace('^{T}', '')}`,
          `\\begin{aligned}\\sigma_y(7)&=${Erow.slice(0, 2).map((w, g) => `(${EF.tex(w, 3)})(${EF.tex(E3.sigma_gauss[g][1], 1)})`).join('+')}\\\\&\\quad+${Erow.slice(2).map((w, g) => `(${EF.tex(w, 3)})(${EF.tex(E3.sigma_gauss[g + 2][1], 1)})`).join('+')}=${EF.tex(nd.sy, 2)}\\end{aligned}`,
          `(\\sigma_x,\\sigma_y,\\tau_{xy})_7=(${EF.tex(nd.sx, 2)};\\;${EF.tex(nd.sy, 2)};\\;${EF.tex(nd.txy, 2)})\\Rightarrow\\sigma_{\\mathrm{VM}}=${EF.tex(nd.vm, 2)}`,
        ],
        txt: `El nodo 7 pertenece solo a E${C.showcase}: su tensión es la extrapolada desde los cuatro puntos de Gauss del elemento, y von Mises se recalcula con las componentes.`,
        dib: 'gauss',
      },
      {
        etapas: [3, 4], titulo: `Etapas 3 y 4 · tensión en el punto de Gauss ${gpCerca + 1}`,
        tex: [
          `\\boldsymbol{\\varepsilon}_g=\\mathbf{B}_g\\,\\mathbf{u}_e=${mat(G.eps.map((v) => [v]), 7).replace(/\\begin\{bmatrix\}/, '\\begin{bmatrix}')}`,
          `\\boldsymbol{\\sigma}_g=\\mathbf{D}\\,\\boldsymbol{\\varepsilon}_g=${EF.tex(DDf, 0)}${mat(Dn, 3)}\\boldsymbol{\\varepsilon}_g=${mat(G.sigma.map((v) => [v]), 2)}`,
        ],
        txt: 'La tensión en el punto de Gauss sale de multiplicar la matriz constitutiva por la deformación, y la deformación, de B por los desplazamientos del elemento.',
        dib: 'gauss',
      },
      {
        etapas: [8], titulo: 'Etapa 8 · restricciones y solución',
        tex: [
          `\\mathbf{u}_e^{(E${C.showcase})}=${vecT(E3.ue, 5)}`,
          `\\mathbf{K}_{ff}\\,\\mathbf{u}_f=\\mathbf{F}_f\\quad(${C.libres.length}\\text{ incógnitas; }${C.restringidos.length}\\text{ GDL restringidos})`,
        ],
        txt: `Los ocho desplazamientos del elemento son una parte del vector u, que resuelve el sistema reducido una vez impuestos los apoyos en los nodos ${C.apoyos.join(', ')}.`,
        dib: 'apoyos',
      },
      {
        etapas: [6], titulo: 'Etapa 6 · el vector de cargas',
        tex: [`F_{13}=-1000\\;(\\text{carga }P\\text{ en el GDL vertical del nodo }7);\\;\\text{los demás }F_i=0`],
        txt: 'En este ejemplo la única carga es nodal: entra directo en F. Una carga distribuida pasaría antes por las fuerzas nodales equivalentes (módulo M6).',
        dib: 'carga',
      },
      {
        etapas: [7], titulo: 'Etapa 7 · ensamblaje',
        tex: [`\\mathbf{K}=\\mathop{\\mathsf{A}}_{e=1}^{4}\\mathbf{k}_e\\qquad K_{8,8}=${C.elementos ? elems.map((e) => { const Ee = C.elementos[String(e.id)]; const l = Ee.dofs.indexOf(8); return EF.tex(Ee.ke[l][l], 0); }).join('+') : ''}=${EF.tex(C.K[8][8], 0)}`],
        txt: 'Cada matriz elemental se suma en las filas y columnas de sus GDL; el nodo 5, compartido por los cuatro elementos, acumula cuatro aportes.',
        dib: 'todos',
      },
      {
        etapas: [5], titulo: 'Etapa 5 · rigidez por cuadratura de Gauss',
        tex: [
          `\\mathbf{k}_e=\\sum_{g=1}^{4}w_g\\,\\mathbf{B}_g^T\\mathbf{D}\\,\\mathbf{B}_g\\,t\\,|\\det\\mathbf{J}_g|,\\quad t=${EF.tex(C.t, 1)},\\;w_g=1`,
          `\\det\\mathbf{J}_g=${E3.gauss.map((g) => EF.tex(g.detJ, 4)).join(';\\;')}`,
          `k_{e,11}=${EF.tex(E3.ke[0][0], 1)}`,
        ],
        txt: 'La rigidez del elemento es la suma de cuatro aportes, uno por punto de Gauss, cada uno ponderado por el determinante del Jacobiano.',
        dib: 'gauss',
      },
      {
        etapas: [3], titulo: `Etapa 3 · matriz B en el punto de Gauss ${gpCerca + 1}`,
        tex: [`\\mathbf{B}_g=${mat(G.B, 3)}`],
        txt: 'B reúne las derivadas físicas de las funciones de forma, obtenidas con la inversa del Jacobiano.',
        dib: 'gauss',
      },
      {
        etapas: [1, 2], titulo: 'Etapas 1 y 2 · mapeo isoparamétrico y Jacobiano',
        tex: [
          `\\mathbf{J}_g=\\frac{\\partial\\mathbf{N}}{\\partial(\\xi,\\eta)}\\,\\mathbf{X}_e=${mat(G.J, 4)},\\quad\\det\\mathbf{J}_g=${EF.tex(G.detJ, 4)}`,
          `\\mathbf{X}_e=${mat(E3.X, 1)}\\;(\\text{nodos }${E3.nodos.join(',\\,')})`,
        ],
        txt: 'Todo empieza en las coordenadas de los nodos del elemento y en las funciones de forma evaluadas en el punto de Gauss.',
        dib: 'coords',
      },
      {
        etapas: [0], titulo: 'Los datos del modelo',
        tex: [
          `E=${EF.tex(C.E, 0)},\\;\\nu=${EF.tex(C.nu, 1)},\\;t=${EF.tex(C.t, 1)},\\;P=${EF.tex(C.P, 0)}\\;\\text{en el nodo 7},\\;\\text{apoyos en }1,3,6`,
          `\\begin{aligned}\\sigma_{\\mathrm{VM}}=${EF.tex(nd.vm, 2)}&\\leftarrow\\boldsymbol{\\sigma}_7=\\mathbf{E}\\,\\boldsymbol{\\sigma}_{\\text{Gauss}}\\leftarrow\\boldsymbol{\\sigma}_g=\\mathbf{D}\\mathbf{B}_g\\mathbf{u}_e\\leftarrow\\mathbf{K}_{ff}\\mathbf{u}_f=\\mathbf{F}_f\\\\&\\leftarrow\\mathbf{K}=\\mathsf{A}\\,\\mathbf{k}_e\\leftarrow\\mathbf{k}_e=\\textstyle\\sum w_g\\mathbf{B}^T\\mathbf{D}\\mathbf{B}\\,t|\\det\\mathbf{J}|\\leftarrow\\mathbf{J}\\leftarrow\\mathbf{X}_e,\\,E,\\,\\nu,\\,t,\\,P\\end{aligned}`,
        ],
        txt: 'Desde el resultado hasta los datos, sin una sola caja negra: esa es la trazabilidad que mide la hipótesis. La memoria de cálculo la deja por escrito (Anexo G).',
        dib: 'datos',
      },
    ];
    function marcarBarra(etapas, recorridas) {
      for (const b of barra.children) {
        const n = Number(b.getAttribute('data-n'));
        b.classList.toggle('actual', etapas.includes(n));
        b.classList.toggle('hecha', recorridas.has(n) && !etapas.includes(n));
      }
    }
    function dibujar(tipo) {
      lz.redimensionar();
      lz.encuadrar(-0.8, 11.8, -1.0, 9.4, 30);
      lz.inicio(EF.css('--lienzo'));
      const esc = tipo === 'contorno' ? 60 : 0;
      const vm = C.nodos.map((n) => C.nodal[String(n.id)].vm);
      if (tipo === 'contorno') {
        lz.malla(P, elems.map((e) => e.con), { color: EF.css('--texto-3'), ancho: 1.2, discontinua: [6, 6], alfa: 0.6 });
        lz.campo(P, elems.map((e) => e.con), vm, { u, escala: esc, sub: 6 });
      }
      lz.malla(P, elems.map((e) => e.con), { color: tipo === 'contorno' ? 'rgba(255,255,255,.7)' : EF.css('--malla'), ancho: 2, u, escala: esc });
      const e3 = elems.find((e) => e.id === C.showcase);
      if (['gauss', 'coords'].includes(tipo)) lz.elemento(P, e3.con, { color: EF.css('--acento'), ancho: 4, relleno: EF.css('--acento'), alfaRelleno: 0.18 });
      if (tipo === 'todos') elems.forEach((e, k) => lz.elemento(P, e.con, { color: ['#5b9bff', '#34d399', '#ff8a3d', '#b794ff'][k], ancho: 3, relleno: ['#5b9bff', '#34d399', '#ff8a3d', '#b794ff'][k], alfaRelleno: 0.16 }));
      lz.nodos(P, P.map((_, i) => i), { radio: 6, u, escala: esc });
      C.nodos.forEach((n2, i) => { const p = EF.LienzoMEF.pos(P, u, esc, i); lz.etiqueta(p[0], p[1], String(n2.id), { dx: -12, dy: -16, ancla: 'right', tam: 19, color: EF.css('--texto') }); });
      const p7 = EF.LienzoMEF.pos(P, u, esc, idx[7]);
      const c = lz.ctx;
      c.save(); c.beginPath(); c.arc(lz.X(p7[0]), lz.Y(p7[1]), 16, 0, 2 * Math.PI); c.lineWidth = 4; c.strokeStyle = '#ffd23f'; c.stroke(); c.restore();
      if (tipo === 'gauss') E3.gauss.forEach((g, k) => {
        c.beginPath(); c.arc(lz.X(g.x[0]), lz.Y(g.x[1]), k === gpCerca ? 11 : 7, 0, 2 * Math.PI);
        c.fillStyle = k === gpCerca ? '#ffd23f' : 'rgba(255,210,63,.55)'; c.fill(); c.lineWidth = 2; c.strokeStyle = '#111'; c.stroke();
        if (k === gpCerca) lz.etiqueta(g.x[0], g.x[1], `PG${k + 1}`, { dx: 14, dy: 0, tam: 19, color: '#ffd23f' });
      });
      if (['apoyos', 'datos'].includes(tipo)) for (const a of C.apoyos) lz.apoyo(P[idx[a]][0], P[idx[a]][1], { tam: 13 });
      if (['carga', 'datos', 'contorno'].includes(tipo)) lz.flecha(p7[0], p7[1], 0, -1, { largo: 56, ancho: 4, texto: tipo === 'contorno' ? '' : 'P = 1000' });
      if (tipo === 'coords' || tipo === 'datos') E3.X.forEach((q, k) => lz.etiqueta(q[0], q[1], `(${EF.fmt(q[0], 0)}; ${EF.fmt(q[1], 0)})`, { dx: k === 0 || k === 3 ? -14 : 14, dy: 22, ancla: k === 0 || k === 3 ? 'right' : 'left', tam: 17, color: EF.css('--acento') }));
    }
    function mostrar(k, animar) {
      const p = pasos[k];
      const recorridas = new Set();
      for (let j = 0; j <= k; j++) pasos[j].etapas.forEach((n) => recorridas.add(n));
      marcarBarra(p.etapas, recorridas);
      panel.innerHTML = `<div class="etq" style="color:var(--acento);font-size:21px">${p.titulo}</div>` +
        p.tex.map((t) => `<div class="k" data-t="${encodeURIComponent(t)}" style="margin:14px 0"></div>`).join('') +
        `<p style="font-size:26px;line-height:1.35;color:var(--texto-2);margin-top:18px">${p.txt}</p>`;
      for (const el of panel.querySelectorAll('.k')) EF.katex(el, decodeURIComponent(el.getAttribute('data-t')), true);
      dibujar(p.dib);
      if (animar) { panel.style.opacity = '0'; EF.tween({ dur: 450, cada: (t) => { panel.style.opacity = String(t); panel.style.transform = `translateX(${24 * (1 - t)}px)`; } }); }
    }
    return {
      entrar(p, op) { mostrar(p, !op.instantaneo && !op.impresion); },
      paso(k, op) { mostrar(k, op.adelante); },
      redimensionar() { dibujar(pasos[EF.Deck.paso] ? pasos[EF.Deck.paso].dib : 'contorno'); },
      tema() { mostrar(EF.Deck.paso || 0, false); },
    };
  });
})();
