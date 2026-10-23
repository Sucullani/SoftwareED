/* =====================================================================
   viz/l4_resultados.js — visualizaciones del grupo «resultados» (final4), Capítulo 3.

   r31-mms        lámina 31. Paso 0: la solución exacta fabricada y las mallas que se refinan.
                  Pasos 1 a 3: alrededor de la Figura 3.1 de la tesis (la dibuja «figdoc», tal
                  cual), los triángulos «h ÷ 2 → error ÷ 4 / ÷ 8» en su propio sistema de
                  coordenadas, sin tapar datos.
   r32-viga       lámina 32. La viga de Timoshenko con los datos del motor (el campo σx de la
                  Figura 3.3), los puntos A, B y C, la tabla con barras frente al umbral, la flecha
                  y el equilibrio de las reacciones.
   r33-cook       lámina 33. La membrana de Cook con los datos del motor, sincronizada con el
                  trazo de la Figura 3.4 (figdoc): cada punto que aparece es su malla. En el paso 3
                  vuelve a empezar el video del bloqueo (viz heredada «video») y marca el contraste
                  con Štembera y Füssl.
   r34-cobertura  lámina 34. Los seis contadores de la trazabilidad y los 49 contenidos del
                  consenso que se separan hasta dejar los 18 del universo, marcados uno a uno.
   r35-leccion    lámina 35. La numeración equivocada de los puntos de Gauss, el cierre que
                  falla en la memoria y la corrección.

   Todo lo que se mueve pasa por EF.tween (reloj virtual del video). Los colores son variables
   CSS: la versión oscura y la clara se leen igual. Las cifras son las de final4 (§ 3.2 a § 3.7).
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const S = EF.svg;
  const est = (e, o) => EF.estiloSvg(e, o);
  const DAT = () => window.EDUFEM_DATOS;
  const PPT = () => EF.estilo === 'ppt';

  // ------------------------------------------------------------------ utilidades
  /** Junta las animaciones de una lámina para cortarlas al cambiar de paso. */
  function animador() {
    let lista = [];
    return {
      t(op) { const tw = EF.tween(op); lista.push(tw); return tw; },
      parar() { const l = lista; lista = []; for (const tw of l) tw.cancelar(false); },
    };
  }
  const op = (el, v) => { if (el) el.style.opacity = String(v); };
  const limpiar = (el) => { if (el) { el.style.opacity = ''; el.style.transform = ''; } };
  function largo(p) { try { return p.getTotalLength() || 1; } catch (e) { return 1000; } }
  function trazoParcial(p, f) {
    const L = largo(p);
    p.style.strokeDasharray = `${L} ${L}`;
    p.style.strokeDashoffset = String(L * (1 - EF.clamp(f, 0, 1)));
  }
  function trazoEntero(p) { p.style.strokeDasharray = ''; p.style.strokeDashoffset = ''; }
  /** Números de un atributo «d» de un trazo SVG, de a pares. */
  function puntosD(d) {
    const n = (d.match(/-?\d+(?:\.\d+)?(?:e-?\d+)?/gi) || []).map(Number);
    const out = [];
    for (let i = 0; i + 1 < n.length; i += 2) out.push([n[i], n[i + 1]]);
    return out;
  }
  /** Puntos de una serie de la figura de la tesis (los del trazo de datos, en orden de malla). */
  function puntosSerie(svg, clave, gid) {
    const g = svg && svg.getElementById(clave + '__' + gid);
    const p = g && g.querySelector('path:not(defs path)');
    return p ? puntosD(p.getAttribute('d')) : [];
  }
  /** «figdoc» muestra cada serie borrando su stroke-dasharray: las rectas de referencia de la
   *  tesis son discontinuas, y aquí se les devuelve su trazo original, el del documento. */
  function guardarDiscontinuas(svg, clave, gids) {
    const mapa = new Map();
    for (const gid of gids) {
      const g = svg && svg.getElementById(clave + '__' + gid);
      if (!g) continue;
      for (const p of g.querySelectorAll('path')) {
        const m = (p.getAttribute('style') || '').match(/stroke-dasharray:\s*([^;]+)/);
        if (m) mapa.set(p, m[1].trim());
      }
    }
    return () => { for (const [p, d] of mapa) p.style.strokeDasharray = d; };
  }
  function linea(g, d, color, ancho, extra) {
    return est(S('path', { d }, g), { trazo: color, relleno: 'none', estilo: `stroke-width:${ancho};stroke-linecap:round;stroke-linejoin:round${extra ? ';' + extra : ''}` });
  }
  function texto(g, x, y, t, estilo, color, ancla) {
    return est(S('text', { x, y, 'text-anchor': ancla || 'middle', text: t }, g), { relleno: color || 'var(--texto)', estilo });
  }
  /** Aparición con rebote (sellos, marcas): escala desde k0 hasta 1. */
  function rebote(an, el, retraso, k0, dur) {
    op(el, 0);
    an.t({ dur: dur || 460, retraso, curva: 'rebote',
      cada: (e) => { op(el, Math.min(1, 2.4 * e)); el.style.transform = `scale(${k0 + (1 - k0) * e})`; },
      fin: () => limpiar(el) });
  }

  // ------------------------------------------------------------------ íconos (58 × 58)
  const ICONOS = {
    malla(g) {   // una malla gruesa y una fina
      const cuad = (x0, y0, t, n, col) => {
        est(S('rect', { x: x0, y: y0, width: t, height: t, rx: 2 }, g), { relleno: 'var(--superficie)', trazo: col, estilo: 'stroke-width:2' });
        for (let k = 1; k < n; k++) {
          linea(g, `M ${x0 + (t * k) / n} ${y0} V ${y0 + t}`, col, 1.2);
          linea(g, `M ${x0} ${y0 + (t * k) / n} H ${x0 + t}`, col, 1.2);
        }
      };
      cuad(4, 18, 26, 6, 'var(--malla)');
      cuad(34, 8, 22, 2, 'var(--malla)');
    },
    ejes(g) {    // ← mallas más finas · ↓ menos error
      linea(g, 'M 50 14 H 10', 'var(--acento)', 4);
      linea(g, 'M 18 6 L 8 14 L 18 22', 'var(--acento)', 4);
      linea(g, 'M 30 26 V 52', 'var(--h-ok)', 4);
      linea(g, 'M 22 44 L 30 54 L 38 44', 'var(--h-ok)', 4);
    },
    pendiente(g) {   // triángulo de pendiente
      linea(g, 'M 6 12 L 52 48', 'var(--primario)', 4);
      linea(g, 'M 6 48 H 52 V 48', 'var(--texto-3)', 3, 'stroke-dasharray:5 4');
      linea(g, 'M 52 48 V 12', 'var(--texto-3)', 3, 'stroke-dasharray:5 4');
      linea(g, 'M 6 12 V 48 H 52', 'var(--acento)', 3.5);
    },
    escudo(g) {      // una prueba que vigila: escudo con una marca
      est(S('path', { d: 'M 29 4 L 50 12 V 28 C 50 41 41 50 29 55 C 17 50 8 41 8 28 V 12 Z' }, g), { relleno: 'var(--h-ok)', trazo: 'none' });
      linea(g, 'M 19 30 L 27 38 L 40 22', 'var(--fondo)', 5.5);
    },
    modulos(g) {     // una malla con un elemento iluminado por la capa del módulo
      est(S('rect', { x: 4, y: 14, width: 40, height: 40, rx: 3 }, g), { relleno: 'var(--superficie)', trazo: 'var(--texto-3)', estilo: 'stroke-width:2.5' });
      linea(g, 'M 24 14 V 54 M 4 34 H 44', 'var(--texto-3)', 2.5);
      est(S('rect', { x: 24, y: 14, width: 20, height: 20 }, g), { relleno: 'var(--acento)', trazo: 'none' });
      est(S('rect', { x: 30, y: 4, width: 24, height: 20, rx: 3 }, g), { relleno: 'var(--superficie)', trazo: 'var(--acento)', estilo: 'stroke-width:2.5' });
      linea(g, 'M 35 11 H 49 M 35 17 H 45', 'var(--acento)', 2.5);
    },
    memoria(g) {     // una hoja con el cálculo escrito
      est(S('path', { d: 'M 10 4 H 36 L 48 16 V 54 H 10 Z' }, g), { relleno: 'var(--superficie)', trazo: 'var(--texto-2)', estilo: 'stroke-width:2.6;stroke-linejoin:round' });
      linea(g, 'M 36 4 V 16 H 48', 'var(--texto-2)', 2.6);
      linea(g, 'M 17 25 H 41 M 17 33 H 36 M 17 41 H 41', 'var(--h-vd)', 3);
      linea(g, 'M 17 48 H 29', 'var(--h-vd)', 3);
    },
    post(g) {        // un contorno de tensiones, en franjas
      const franjas = ['var(--h-mal)', 'var(--acento)', 'var(--h-ok)', 'var(--h-vi)'];
      franjas.forEach((c, k) => est(S('rect', { x: 6, y: 6 + 11.5 * k, width: 46, height: 11.5 }, g), { relleno: c, trazo: 'none' }));
      est(S('rect', { x: 6, y: 6, width: 46, height: 46, rx: 3 }, g), { relleno: 'none', trazo: 'var(--texto-2)', estilo: 'stroke-width:2.6' });
      est(S('circle', { cx: 38, cy: 22, r: 5.5 }, g), { relleno: 'var(--superficie)', trazo: 'var(--texto)', estilo: 'stroke-width:2.6' });
    },
    lienzo(g) {      // un lienzo con sus tres fases
      est(S('rect', { x: 3, y: 9, width: 52, height: 40, rx: 4 }, g), { relleno: 'var(--superficie)', trazo: 'var(--texto-2)', estilo: 'stroke-width:2.6' });
      ['var(--h-vi)', 'var(--acento)', 'var(--h-ok)'].forEach((c, k) => est(S('rect', { x: 8 + 15.5 * k, y: 15, width: 12, height: 28, rx: 2 }, g), { relleno: c, trazo: 'none' }));
    },
    expertos(g) {    // tres personas
      [[29, 0], [13, 6], [45, 6]].forEach(([x, dy]) => {
        est(S('circle', { cx: x, cy: 17 + dy, r: 7 }, g), { relleno: 'var(--texto-3)', trazo: 'none' });
        est(S('path', { d: `M ${x - 11} ${46 + dy} Q ${x - 11} ${28 + dy} ${x} ${28 + dy} Q ${x + 11} ${28 + dy} ${x + 11} ${46 + dy} Z` }, g), { relleno: 'var(--texto-3)', trazo: 'none' });
      });
    },
    intercambio(g) { // el modelo sale y vuelve: dos flechas opuestas entre dos hojas
      est(S('rect', { x: 3, y: 12, width: 16, height: 34, rx: 2 }, g), { relleno: 'var(--superficie)', trazo: 'var(--texto-2)', estilo: 'stroke-width:2.4' });
      est(S('rect', { x: 39, y: 12, width: 16, height: 34, rx: 2 }, g), { relleno: 'var(--superficie)', trazo: 'var(--texto-2)', estilo: 'stroke-width:2.4' });
      linea(g, 'M 23 23 H 34 M 30 19 L 35 23 L 30 27', 'var(--h-vd)', 3);
      linea(g, 'M 35 36 H 24 M 28 32 L 23 36 L 28 40', 'var(--h-vd)', 3);
    },
  };
  function ponerIconos(raiz) {
    for (const i of raiz.querySelectorAll('[data-ico]')) {
      if (i.firstChild) continue;
      const f = ICONOS[i.getAttribute('data-ico')];
      if (!f) continue;
      const s = S('svg', { viewBox: '0 0 58 58', 'aria-hidden': 'true' }, i);
      f(S('g', {}, s));
    }
  }

  /** Malla cuadrada de N × N en un SVG de lado t (las líneas interiores se pueden trazar). */
  function mallaSvg(cont, N, t) {
    const s = S('svg', { viewBox: `0 0 ${t} ${t}`, 'aria-hidden': 'true' }, cont);
    est(S('rect', { x: 0, y: 0, width: t, height: t }, s), { relleno: 'var(--superficie)', trazo: 'none' });
    const g = S('g', {}, s);
    // trazo según la densidad: la malla de 32 × 32 sigue leyéndose como malla y no como mancha
    const celda = t / N;
    const ancho = celda < 3 ? 0.5 : celda < 6 ? 0.8 : celda < 12 ? 1.2 : 1.8;
    const lineas = [];
    for (let k = 1; k < N; k++) {
      lineas.push(linea(g, `M ${(t * k) / N} 0 V ${t}`, 'var(--malla)', ancho));
      lineas.push(linea(g, `M 0 ${(t * k) / N} H ${t}`, 'var(--malla)', ancho));
    }
    est(S('rect', { x: 0, y: 0, width: t, height: t }, s), { relleno: 'none', trazo: 'var(--malla)', estilo: 'stroke-width:3' });
    return { svg: s, lineas };
  }

  // ==================================================================== 31 · mms
  EF.registrarViz('r31-mms', function (cont, L) {
    const raiz = L.el;
    const an = animador();
    ponerIconos(raiz);

    // ---------- paso 0: la solución exacta, pintada píxel a píxel con la paleta jet
    const cu = raiz.querySelector('.r31-cu'), cv = raiz.querySelector('.r31-cv');
    function pintar(canvas, f, vmin, vmax) {
      const r = EF.escalaRender();
      const n = Math.round(230 * r);
      if (canvas.width !== n) { canvas.width = n; canvas.height = n; }
      const ctx = canvas.getContext('2d');
      const img = ctx.createImageData(n, n);
      for (let j = 0; j < n; j++) {
        const y = 1 - (j + 0.5) / n;
        for (let i = 0; i < n; i++) {
          const x = (i + 0.5) / n;
          const t = (f(x, y) - vmin) / (vmax - vmin);
          const k = Math.max(0, Math.min(255, Math.round(t * 255))) * 3;
          const o = (j * n + i) * 4;
          img.data[o] = EF.jetLUT[k]; img.data[o + 1] = EF.jetLUT[k + 1]; img.data[o + 2] = EF.jetLUT[k + 2]; img.data[o + 3] = 255;
        }
      }
      ctx.putImageData(img, 0, 0);
    }
    function pintarCampos() {
      pintar(cu, (x, y) => Math.sin(Math.PI * x) * Math.sin(Math.PI * y), 0, 1);
      pintar(cv, (x, y) => Math.cos(Math.PI * x) * Math.cos(Math.PI * y), -1, 1);
    }
    pintarCampos();

    // mallas N = 2 … 32 (paso 0) y la fila de la lectura (de la más fina a la más gruesa, como el eje h)
    const NS = [2, 4, 8, 16, 32];
    const mallas = NS.map((N) => {
      const m = EF.el('div', { class: 'r31-m' });
      raiz.querySelector('.r31-mallas').appendChild(m);
      const ms = mallaSvg(m, N, 108);
      m.appendChild(EF.el('span', { text: `N = ${N}` }));
      return { el: m, ...ms };
    });
    const mini = raiz.querySelector('.r31-mini');
    for (const N of NS.slice().reverse()) {
      const m = EF.el('div', { class: 'r31-m' });
      mini.appendChild(m);
      mallaSvg(m, N, 62);
      m.appendChild(EF.el('span', { text: String(N) }));
    }
    mini.appendChild(EF.el('span', { class: 'r31-flecha', html: '← N = 32 … 2' }));

    // íconos de las cuatro configuraciones (Tabla D.3): cuadrado y cuadrilátero distorsionado
    for (const c of raiz.querySelectorAll('.r31-cfg')) {
      const s = S('svg', { viewBox: '0 0 52 52', 'aria-hidden': 'true' }, c);
      const P = c.getAttribute('data-cfg') === 'dist' ? [[0, 0], [1, 0.15], [0.85, 1], [0.1, 0.8]] : [[0, 0], [1, 0], [1, 1], [0, 1]];
      const d = P.map(([x, y], k) => `${k ? 'L' : 'M'} ${4 + 44 * x} ${48 - 44 * y}`).join(' ') + ' Z';
      est(S('path', { d }, s), { relleno: 'var(--superficie)', trazo: 'var(--h-ok)', estilo: 'stroke-width:3;stroke-linejoin:round' });
    }

    // ---------- pasos 1 y 2: triángulos de pendiente sobre la Figura 3.1 (a), en sus coordenadas
    const svgA = raiz.querySelector('.r31-fa .figdoc svg');
    const svgB = raiz.querySelector('.r31-fb .figdoc svg');
    const sobre = raiz.querySelector('.r31-sobre');
    const devolverA = guardarDiscontinuas(svgA, 'mms_l2', ['pend_q4', 'pend_q9']);
    const devolverB = guardarDiscontinuas(svgB, 'mms_h1', ['pend_q4', 'pend_q9']);
    /** Triángulo entre dos mallas sucesivas: A, la más fina (abajo a la izquierda); B, la más gruesa. */
    function triangulo(A, B, color, tinta, txH, txE) {
      const g = S('g', {}, sobre);
      const C = [B[0], A[1]];
      const h = linea(g, `M ${A[0]} ${A[1]} L ${C[0]} ${C[1]}`, color, 2.1);
      const v = linea(g, `M ${C[0]} ${C[1]} L ${B[0]} ${B[1]}`, color, 2.1);
      const halo = 'paint-order:stroke;stroke:var(--r-papel);stroke-width:4.5px;stroke-linejoin:round';
      const tH = texto(g, (A[0] + C[0]) / 2, A[1] + 17.5, txH, `font:700 15px var(--fuente);${halo}`, tinta);
      const tE = texto(g, C[0] + 6, (C[1] + B[1]) / 2 + 5.5, txE, `font:700 15px var(--fuente);${halo}`, tinta, 'start');
      return { g, h, v, tH, tE };
    }
    const p4 = puntosSerie(svgA, 'mms_l2', 'serie_q4');
    const p9 = puntosSerie(svgA, 'mms_l2', 'serie_q9');
    // orden de los puntos: N = 2, 4, 8, 16, 32 (de derecha a izquierda en el eje h)
    const tri4 = p4.length === 5 ? triangulo(p4[4], p4[3], 'var(--r-fq4)', 'var(--r-fq4-tinta)', 'h ÷ 2', 'error ÷ 4') : null;
    const tri9 = p9.length === 5 ? triangulo(p9[3], p9[2], 'var(--r-fq9)', 'var(--r-fq9-tinta)', 'h ÷ 2', 'error ÷ 8') : null;

    function ponerTri(t, visible, animar, retraso) {
      if (!t) return;
      for (const p of [t.h, t.v]) trazoEntero(p);
      if (!visible) { op(t.g, 0); return; }
      op(t.g, 1);
      for (const e of [t.tH, t.tE]) op(e, 1);
      if (!animar) return;
      trazoParcial(t.h, 0); trazoParcial(t.v, 0); op(t.tH, 0); op(t.tE, 0);
      an.t({ dur: 420, retraso, curva: 'sale', cada: (e) => trazoParcial(t.h, e), fin: () => trazoEntero(t.h) });
      an.t({ dur: 320, retraso: retraso + 180, cada: (e) => op(t.tH, e) });
      an.t({ dur: 420, retraso: retraso + 420, curva: 'sale', cada: (e) => trazoParcial(t.v, e), fin: () => trazoEntero(t.v) });
      an.t({ dur: 320, retraso: retraso + 640, cada: (e) => op(t.tE, e) });
    }
    function mallasCompletas() { for (const m of mallas) { limpiar(m.el); for (const l of m.lineas) trazoEntero(l); } }
    /** Paso 0: cada malla aparece y se subdivide, de la más gruesa a la más fina. */
    function animarMallas() {
      mallas.forEach((m, k) => {
        const r = 650 + k * 230;
        op(m.el, 0);
        for (const l of m.lineas) trazoParcial(l, 0);
        an.t({ dur: 260, retraso: r, cada: (e) => op(m.el, e), fin: () => limpiar(m.el) });
        an.t({ dur: 420, retraso: r + 120, curva: 'ambos', cada: (e) => { for (const l of m.lineas) trazoParcial(l, e); }, fin: () => { for (const l of m.lineas) trazoEntero(l); } });
      });
    }
    function estado(p, animar) {
      an.parar();
      devolverA(); devolverB();
      // la serie del Q4 termina de trazarse ≈ 1,85 s después del paso; la del Q9 cruza N = 8 → 16 hacia 1,3 s
      ponerTri(tri4, p >= 1, animar && p === 1, 1900);
      ponerTri(tri9, p >= 2, animar && p === 2, 1650);
      if (p === 0 && animar) animarMallas(); else mallasCompletas();
    }
    return {
      entrar(p, o) { estado(p, !o.instantaneo && !o.impresion); },
      paso(k, o) { estado(k, !!o.adelante && !o.salto); },
      salir() { an.parar(); },
      redimensionar() { pintarCampos(); },
      tema() { pintarCampos(); },
    };
  });

  // ==================================================================== 32 · timoshenko
  EF.registrarViz('r32-viga', function (cont, L) {
    const raiz = L.el;
    const T = DAT().timoshenko;
    const an = animador();
    const caja = raiz.querySelector('.r32-viga');
    const W = (PPT() ? 1742 : 1720) - 2, H = 278;
    const lz = new EF.LienzoMEF(caja, W, H);
    const u = T.u.map((p) => [p[0] / 100, p[1] / 100]);   // cm -> m, como la malla
    const ESC = 20;
    let sxMin = Infinity, sxMax = -Infinity;
    for (const v of T.sx) { if (v < sxMin) sxMin = v; if (v > sxMax) sxMax = v; }
    raiz.querySelector('.r32-barra').style.background =
      `linear-gradient(90deg,${EF.rango(11).map((k) => EF.jetCss(k / 10)).join(',')})`;

    const cerca = (x, y) => T.nodos.reduce((b, p, k) => (Math.hypot(p[0] - x, p[1] - y) < Math.hypot(T.nodos[b][0] - x, T.nodos[b][1] - y) ? k : b), 0);
    // puntos de control (Tabla 3.2): marco de Timoshenko-Goodier, y hacia la fibra traccionada;
    // en la malla, y hacia arriba (y_MEF = −y_ref)
    const PTS = { A: [0, -0.6], B: [-4.5, 0.3], C: [-3.5, 0.2] };
    const iPts = Object.fromEntries(Object.entries(PTS).map(([n, [x, y]]) => [n, cerca(x, y)]));
    const fila = (yy) => T.nodos.map((p, i) => [p, i]).filter(([p]) => Math.abs(p[1] - yy) < 1e-6).sort((a, b) => a[0][0] - b[0][0]).map(([, i]) => i);
    const sup = fila(0.6), eje = fila(0);
    const cargas = sup.filter((_, k) => k % 4 === 2);
    const iM = cerca(0, 0);
    const pos = (i, esc) => EF.LienzoMEF.pos(T.nodos, u, esc, i);
    /** Posición deformada de un punto de control (su desplazamiento, el del nodo más cercano). */
    const posPto = (n, esc) => { const [x, y] = PTS[n], d = u[iPts[n]]; return [x + esc * d[0], y + esc * d[1]]; };

    const st = { esc: ESC, marcas: 1, pulso: { A: 0, B: 0, C: 0 }, eje: 0, reac: 0 };
    function dibujar() {
      lz.redimensionar();
      lz.encuadrar(-8.7, 8.7, -1.5, 1.2, { s: 12, d: 12, i: 10, iz: 12 });
      const c = lz.inicio(EF.css('--lienzo'));
      const tx = EF.css('--texto'), tx3 = EF.css('--texto-3');
      lz.campo(T.nodos, T.elems, T.sx, { min: sxMin, max: sxMax, u, escala: st.esc, sub: 2 });
      lz.malla(T.nodos, T.elems, { color: EF.css('--r-malla-campo'), ancho: 0.6, u, escala: st.esc });
      // paso 2: la viga sin deformar y el eje deformado, con la flecha en el centro
      if (st.eje > 0) {
        c.save();
        c.globalAlpha = st.eje;
        c.setLineDash([9, 7]); c.lineWidth = 2; c.strokeStyle = tx3;
        c.strokeRect(lz.X(-7), lz.Y(0.6), lz.X(7) - lz.X(-7), lz.Y(-0.6) - lz.Y(0.6));
        c.beginPath(); c.moveTo(lz.X(-7), lz.Y(0)); c.lineTo(lz.X(7), lz.Y(0)); c.stroke();
        c.setLineDash([]); c.lineWidth = 3; c.strokeStyle = tx;
        c.beginPath();
        eje.forEach((i, k) => { const p = pos(i, st.esc); if (k) c.lineTo(lz.X(p[0]), lz.Y(p[1])); else c.moveTo(lz.X(p[0]), lz.Y(p[1])); });
        c.stroke();
        const pm = pos(iM, st.esc), x0 = lz.X(0), y0 = lz.Y(0), y1 = lz.Y(pm[1]);
        c.lineWidth = 3.5; c.strokeStyle = EF.css('--acento'); c.fillStyle = EF.css('--acento');
        c.beginPath(); c.moveTo(x0, y0 + 2); c.lineTo(x0, y1 - 9); c.stroke();
        c.beginPath(); c.moveTo(x0, y1); c.lineTo(x0 - 7, y1 - 12); c.lineTo(x0 + 7, y1 - 12); c.closePath(); c.fill();
        c.restore();
        if (st.eje > 0.6) lz.etiqueta(0.18, (pm[1] + 0) / 2, 'flecha: 2,03460 cm', { tam: 24, peso: 800, color: tx, fondo: EF.css('--lienzo'), alfaFondo: 0.92 });
      }
      for (const a of T.apoyos) { const p = pos(a.i, st.esc); lz.apoyo(p[0], p[1], { tam: 13, movil: a.tipo === 'movil' }); }
      for (const i of cargas) { const q = pos(i, st.esc); lz.flecha(q[0], q[1] + 0.02, 0, -1, { largo: 30, ancho: 2.4 }); }
      lz.etiqueta(0, 1.04, 'q = 5000 kgf/m', { tam: 25, peso: 800, ancla: 'center', color: EF.css('--carga') });
      // cotas: la luz y el peralte
      c.save();
      c.strokeStyle = tx3; c.lineWidth = 1.8;
      const yL = lz.Y(-1.33);
      c.beginPath(); c.moveTo(lz.X(-7), yL); c.lineTo(lz.X(7), yL); c.stroke();
      for (const x of [-7, 7]) { c.beginPath(); c.moveTo(lz.X(x), yL - 9); c.lineTo(lz.X(x), yL + 9); c.stroke(); }
      const xH = lz.X(-7.28);
      c.beginPath(); c.moveTo(xH, lz.Y(0.6)); c.lineTo(xH, lz.Y(-0.6)); c.stroke();
      for (const y of [0.6, -0.6]) { c.beginPath(); c.moveTo(xH - 8, lz.Y(y)); c.lineTo(xH + 8, lz.Y(y)); c.stroke(); }
      c.restore();
      lz.etiqueta(0, -1.33, 'L = 14 m', { tam: 24, peso: 750, ancla: 'center', color: tx, fondo: EF.css('--lienzo'), alfaFondo: 1 });
      lz.etiqueta(-7.4, 0.02, 'H = 1,20 m', { tam: 24, peso: 750, ancla: 'right', color: tx });
      // paso 2: las reacciones, de 35 000 kgf cada una
      if (st.reac > 0) {
        for (const a of T.apoyos) {
          const p = pos(a.i, st.esc);
          const yTope = p[1] - 0.17, yBase = yTope - 0.95 * st.reac;
          c.save();
          c.strokeStyle = EF.css('--apoyo'); c.fillStyle = EF.css('--apoyo'); c.lineWidth = 4;
          c.beginPath(); c.moveTo(lz.X(p[0]), lz.Y(yBase)); c.lineTo(lz.X(p[0]), lz.Y(yTope) + 12); c.stroke();
          c.beginPath(); c.moveTo(lz.X(p[0]), lz.Y(yTope)); c.lineTo(lz.X(p[0]) - 8, lz.Y(yTope) + 15); c.lineTo(lz.X(p[0]) + 8, lz.Y(yTope) + 15); c.closePath(); c.fill();
          c.restore();
          if (st.reac > 0.7) {
            // el rótulo, hacia el centro del vano: afuera no cabe en la versión 1
            const der = p[0] > 0;
            lz.etiqueta(p[0] + (der ? -0.24 : 0.24), -1.03, 'R = 35 000 kgf', { tam: 24, peso: 800, ancla: der ? 'right' : 'left', color: EF.css('--apoyo') });
          }
        }
      }
      // los tres puntos de control
      if (st.marcas > 0) {
        const off = { A: [16, 2, 'left'], B: [-16, -4, 'right'], C: [16, -4, 'left'] };
        for (const n of ['A', 'B', 'C']) {
          const [x, y] = posPto(n, st.esc), X = lz.X(x), Y = lz.Y(y), k = st.pulso[n];
          c.save();
          c.globalAlpha = st.marcas;
          if (k > 0) { c.beginPath(); c.arc(X, Y, 12 + 16 * k, 0, 2 * Math.PI); c.lineWidth = 4; c.strokeStyle = EF.rgba(EF.css('--acento'), 1 - k * 0.7); c.stroke(); }
          c.beginPath(); c.arc(X, Y, 10, 0, 2 * Math.PI); c.fillStyle = EF.css('--r-papel'); c.fill(); c.lineWidth = 3.5; c.strokeStyle = EF.css('--r-tinta'); c.stroke();
          c.restore();
          if (st.marcas > 0.5) lz.etiqueta(x, y, n, { dx: off[n][0], dy: off[n][1], ancla: off[n][2], tam: 27, peso: 850, color: EF.css('--r-tinta'), fondo: EF.css('--r-papel'), alfaFondo: 0.92, borde: EF.css('--r-tinta') });
        }
      }
    }

    // ---------- tablas con barras: lo coloreado es la parte del umbral que se usó
    const pistas = Array.from(raiz.querySelectorAll('.r32-pct')).map((td) => ({ i: td.querySelector('.r32-pista > i'), f: Number(td.getAttribute('data-v')) / 1, fila: td.closest('tr').getAttribute('data-fila') }));
    const pistasF = Array.from(raiz.querySelectorAll('.r32-fl .r32-pista > i')).map((i) => ({ i, f: Number(i.getAttribute('data-v')) / Number(i.getAttribute('data-u')) }));
    const ancho = (b, e) => { b.i.style.width = `${Math.max(0.6, 100 * b.f * e)}%`; };

    function estado(p, animar) {
      an.parar();
      st.pulso = { A: 0, B: 0, C: 0 };
      st.eje = p >= 2 ? 1 : 0; st.reac = p >= 2 ? 1 : 0;
      st.esc = ESC; st.marcas = 1;
      for (const b of pistas) ancho(b, p >= 1 ? 1 : 0);
      for (const b of pistasF) ancho(b, p >= 2 ? 1 : 0);
      if (animar && p === 0) {
        // la carga deforma la viga; después aparecen los puntos de control
        st.esc = 0; st.marcas = 0;
        an.t({ dur: 1500, retraso: 200, curva: 'ambos', cada: (e) => { st.esc = ESC * e; dibujar(); } });
        an.t({ dur: 500, retraso: 1550, cada: (e) => { st.marcas = e; dibujar(); } });
      }
      if (animar && p === 1) {
        // cada fila de la tabla se enciende con su punto en la viga
        ['A', 'B', 'C'].forEach((n, k) => {
          const r = 450 + k * 520;
          an.t({ dur: 900, retraso: r, curva: 'lineal', cada: (e) => { st.pulso[n] = e < 1 ? e : 0; dibujar(); }, fin: () => { st.pulso[n] = 0; dibujar(); } });
          for (const b of pistas.filter((x) => x.fila === n)) { ancho(b, 0); an.t({ dur: 700, retraso: r + 150, curva: 'sale', cada: (e) => ancho(b, e) }); }
        });
      }
      if (animar && p === 2) {
        st.eje = 0; st.reac = 0;
        for (const b of pistasF) ancho(b, 0);
        an.t({ dur: 700, retraso: 250, cada: (e) => { st.eje = e; dibujar(); } });
        pistasF.forEach((b, k) => an.t({ dur: 800, retraso: 700 + k * 350, curva: 'sale', cada: (e) => ancho(b, e) }));
        an.t({ dur: 800, retraso: 1700, curva: 'sale', cada: (e) => { st.reac = e; dibujar(); } });
      }
      dibujar();
    }
    return {
      entrar(p, o) { estado(p, !o.instantaneo && !o.impresion); },
      paso(k, o) { estado(k, !!o.adelante && !o.salto); },
      salir() { an.parar(); },
      redimensionar() { dibujar(); },
      tema() { dibujar(); },
    };
  });

  // ==================================================================== 33 · cook
  /** Fracción del trazo de una poligonal en que se alcanza cada uno de sus vértices
   *  (la misma regla con que «figdoc» suelta cada marcador al trazar la serie). */
  function fracciones(pts) {
    const acum = [0];
    for (let i = 1; i < pts.length; i++) acum.push(acum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    const L = acum[acum.length - 1] || 1;
    return acum.map((a) => a / L);
  }
  /** Anillo (o recuadro) de resalte sobre la figura de la tesis, en sus coordenadas. */
  function anillo(g, x, y, r, color) {
    return est(S('circle', { cx: x, cy: y, r }, g), { relleno: 'none', trazo: color, estilo: 'stroke-width:2.4' });
  }
  const HALO = 'paint-order:stroke;stroke:var(--r-papel);stroke-width:4.5px;stroke-linejoin:round';

  EF.registrarViz('r33-cook', function (cont, L) {
    const raiz = L.el;
    const CK = DAT().cook;
    const an = animador();
    const Ns = [2, 4, 8, 16, 32];
    const W = (PPT() ? 720 : 708) - 2, H = (PPT() ? 640 : 630) - 2;
    const lz = new EF.LienzoMEF(raiz.querySelector('.r33-lienzo'), W, H);
    const ESC = 0.5;
    const info = raiz.querySelector('.r33-info');
    const svg = raiz.querySelector('.r33-fig .figdoc svg');
    const sobre = raiz.querySelector('.r33-sobre');
    const p4 = puntosSerie(svg, 'cook', 'serie_q4');
    const p9 = puntosSerie(svg, 'cook', 'serie_q9');
    const fr4 = fracciones(p4), fr9 = fracciones(p9);

    let modo = 'caso', el = 'Q9', N = 8, fase = 1;
    const borde = (c) => c.nodos.map((p, i) => [p, i]).filter(([p]) => Math.abs(p[0] - 48) < 1e-6);
    function cargas(c) {
      const b = borde(c);
      return [46, 50, 54, 58].map((yy) => b.reduce((m, [p, i]) => (Math.abs(p[1] - yy) < Math.abs(c.nodos[m][1] - yy) ? i : m), b[0][1]));
    }
    // en la versión 1 (letra Inter, más ancha) el encuadre deja más margen para los rótulos
    const VX = PPT() ? [-9, 84] : [-15, 92], TAM = PPT() ? 24 : 22;
    function dibujar() {
      lz.redimensionar();
      lz.encuadrar(VX[0], VX[1], -6, 79, { s: 10, d: 10, i: 10, iz: 10 });
      const ctx = lz.inicio(EF.css('--lienzo'));
      const tx = EF.css('--texto'), tx2 = EF.css('--texto-2'), tx3 = EF.css('--texto-3');
      const c = CK.casos[el][String(N)];
      const esc = ESC * (modo === 'caso' ? fase : 1);
      // la membrana sin deformar (trazo discontinuo)
      ctx.save();
      ctx.setLineDash([8, 6]); ctx.lineWidth = 2; ctx.strokeStyle = tx3;
      ctx.beginPath();
      CK.esquinas.forEach(([x, y], k) => (k ? ctx.lineTo(lz.X(x), lz.Y(y)) : ctx.moveTo(lz.X(x), lz.Y(y))));
      ctx.closePath(); ctx.stroke();
      ctx.restore();
      // la deformada con su malla: en el paso 0, neutra; en los pasos 1 y 2, del color de su elemento
      const colEl = modo === 'caso' ? EF.css('--malla') : EF.css(el === 'Q4' ? '--r-q4' : '--r-q9');
      lz.malla(c.nodos, c.elems, { color: colEl, ancho: N >= 16 ? 0.9 : 1.6, u: c.u, escala: esc, relleno: colEl, alfaRelleno: 0.13 });
      lz.empotramiento(0, 0, 44, {});
      for (const i of cargas(c)) { const q = EF.LienzoMEF.pos(c.nodos, c.u, esc, i); lz.flecha(q[0] + 2.6, q[1] + 1.4, 0, 1, { largo: 30, ancho: 3 }); }
      // el punto de control (48; 52)
      const iS = c.nodos.findIndex((p) => Math.abs(p[0] - 48) < 1e-6 && Math.abs(p[1] - 52) < 1e-6);
      const q = EF.LienzoMEF.pos(c.nodos, c.u, esc, iS);
      if (modo === 'caso') {
        CK.esquinas.forEach(([x, y], k) => {
          const d = [[-0.6, -3.2, 'right'], [1.8, -0.6, 'left'], [1.8, 1.6, 'left'], [-1.6, 0.6, 'right']][k];
          lz.etiqueta(x + d[0], y + d[1], `(${x}; ${y})`, { tam: TAM, peso: 700, ancla: d[2], color: tx2 });
        });
        if (fase > 0.15) {
          ctx.save();
          ctx.strokeStyle = EF.css('--acento'); ctx.fillStyle = EF.css('--acento'); ctx.lineWidth = 3;
          const X0 = lz.X(48), Y0 = lz.Y(52), X1 = lz.X(q[0]), Y1 = lz.Y(q[1]);
          const a = Math.atan2(Y1 - Y0, X1 - X0);
          ctx.beginPath(); ctx.moveTo(X0, Y0); ctx.lineTo(X1 - 12 * Math.cos(a), Y1 - 12 * Math.sin(a)); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(X1, Y1); ctx.lineTo(X1 - 14 * Math.cos(a) + 7 * Math.sin(a), Y1 - 14 * Math.sin(a) - 7 * Math.cos(a));
          ctx.lineTo(X1 - 14 * Math.cos(a) - 7 * Math.sin(a), Y1 - 14 * Math.sin(a) + 7 * Math.cos(a)); ctx.closePath(); ctx.fill();
          ctx.restore();
        }
        lz.etiqueta(50.5, 52, 'se mide u_y en (48; 52)', { tam: TAM + 1, peso: 800, ancla: 'left', color: EF.css('--acento') });
        lz.etiqueta(51.5, 71, 'carga tangencial unitaria', { tam: TAM, peso: 750, ancla: 'left', color: EF.css('--carga') });
      } else {
        // la referencia, 23,96, a la misma escala: lo que le falta al punto para llegar
        const yR = 52 + ESC * CK.ref;
        ctx.save();
        ctx.setLineDash([7, 6]); ctx.lineWidth = 2.5; ctx.strokeStyle = EF.css('--h-ok');
        ctx.beginPath(); ctx.moveTo(lz.X(36), lz.Y(yR)); ctx.lineTo(lz.X(56), lz.Y(yR)); ctx.stroke();
        ctx.restore();
        lz.etiqueta(57, yR, 'referencia 23,96', { tam: TAM, peso: 800, ancla: 'left', color: EF.css('--h-ok') });
      }
      ctx.save();
      ctx.beginPath(); ctx.arc(lz.X(q[0]), lz.Y(q[1]), 9, 0, 2 * Math.PI);
      ctx.fillStyle = EF.css('--r-papel'); ctx.fill(); ctx.lineWidth = 3.5; ctx.strokeStyle = tx; ctx.stroke();
      ctx.restore();
      // rótulos de la malla en curso (HTML)
      info.className = 'r33-info ' + (el === 'Q4' ? 'q4' : 'q9');
      info.children[0].textContent = `${el} · N = ${N}`;
      info.children[1].textContent = `${EF.fmt(c.gdl, 0)} GDL`;
      info.children[2].innerHTML = `u<sub>y</sub> = ${EF.fmt(c.uy, 3)}`;
      info.children[3].textContent = `error ${EF.fmt(c.error, 3, { signo: true })} %`;
    }
    /** La membrana sigue al trazo de la serie: cada punto que aparece en la figura es su malla. */
    function seguir(elem, fr, retraso, dur, alFinal) {
      an.t({ dur, retraso, curva: 'ambos', cada: (v) => {
        let k = 0;
        for (let j = 0; j < fr.length; j++) if (v + 1e-9 >= fr[j]) k = j;
        if (modo !== 'malla' || el !== elem || N !== Ns[k]) { modo = 'malla'; el = elem; N = Ns[k]; dibujar(); }
      }, fin: alFinal });
    }

    // ---------- llamadas sobre la Figura 3.4 (en sus coordenadas, sin tapar datos)
    const tinta = 'var(--r-tinta)';
    const g1 = S('g', {}, sobre), g2 = S('g', {}, sobre), g3 = S('g', {}, sobre);
    if (p4.length === 5) {
      // paso 1: la malla más gruesa y la más fina del Q4
      anillo(g1, p4[0][0], p4[0][1], 9, 'var(--r-anillo)');
      anillo(g1, p4[4][0], p4[4][1], 9, 'var(--r-anillo)');
      texto(g1, p4[0][0] + 13, p4[0][1] + 5, 'N = 2', `font:700 14.5px var(--fuente);${HALO}`, 'var(--r-fq4-tinta)', 'start');
      texto(g1, p4[4][0] + 4, p4[4][1] + 24, 'N = 32', `font:700 14.5px var(--fuente);${HALO}`, 'var(--r-fq4-tinta)', 'middle');
    }
    if (p4.length === 5 && p9.length === 5) {
      const x = p4[3][0];
      est(S('rect', { x: x - 9, y: p9[2][1] - 9, width: 18, height: p4[3][1] - p9[2][1] + 18, rx: 9 }, g2), { relleno: 'none', trazo: 'var(--r-anillo)', estilo: 'stroke-width:2.4' });
      texto(g2, x + 14, p4[3][1] + 19, 'mismos GDL: 578', `font:700 14.5px var(--fuente);${HALO}`, tinta, 'start');
    }
    const a3 = p4.map((p) => anillo(g3, p[0], p[1], 9, 'var(--r-anillo)'));

    // ---------- tabla de Štembera y Füssl: las celdas iguales se encienden de a una
    const filas = raiz.querySelectorAll('.r33-tab tbody tr');
    const celdas = [1, 2, 3, 4, 5].map((k) => [filas[0].children[k], filas[1].children[k]]);
    function marcarCelda(k, si) { for (const td of celdas[k]) td.classList.toggle('igual', si); }

    // ---------- el video del bloqueo (viz heredada «video», que corre desde que se entra a la
    // lámina): se lo vuelve a empezar cuando aparece, en el paso 3, para que se vea desde el principio
    function reiniciarVideo() {
      const v = (L.viz || []).find((x) => x.nombre === 'video');
      if (v && v.inst && v.inst.entrar) { try { v.inst.entrar(3, {}); } catch (e) { console.error(e); } }
    }

    function estado(p, animar) {
      an.parar();
      op(g1, p === 1 ? 1 : 0); op(g2, p === 2 ? 1 : 0); op(g3, p === 3 ? 1 : 0);
      for (let k = 0; k < 5; k++) { marcarCelda(k, p >= 3); op(a3[k], 1); }
      if (p === 0) {
        modo = 'caso'; el = 'Q9'; N = 8; fase = 1;
        if (animar) { fase = 0; an.t({ dur: 1300, retraso: 350, curva: 'ambos', cada: (e) => { fase = e; dibujar(); } }); }
      } else if (p === 1) {
        modo = 'malla'; el = 'Q4'; N = 32;
        if (animar) {
          N = 2; seguir('Q4', fr4, 250, 1600);
          op(g1, 0); an.t({ dur: 450, retraso: 1900, cada: (e) => op(g1, e) });
        }
      } else if (p === 2) {
        modo = 'malla'; el = 'Q9'; N = 8;
        if (animar) {
          N = 2; seguir('Q9', fr9, 250, 1600, () => { N = 8; dibujar(); });
          op(g2, 0); an.t({ dur: 450, retraso: 1950, cada: (e) => op(g2, e) });
        }
      } else if (animar) {
        // paso 3: cada valor del Q4, en la figura y en la tabla, junto al de la fuente publicada
        reiniciarVideo();
        for (let k = 0; k < 5; k++) {
          marcarCelda(k, false); op(a3[k], 0);
          an.t({ dur: 300, retraso: 1250 + k * 280, cada: (e) => op(a3[k], e), fin: () => marcarCelda(k, true) });
        }
      }
      if (p <= 2) dibujar();
    }
    return {
      entrar(p, o) { estado(p, !o.instantaneo && !o.impresion); },
      paso(k, o) { estado(k, !!o.adelante && !o.salto); },
      salir() { an.parar(); },
      redimensionar() { dibujar(); },
      tema() { dibujar(); },
    };
  });

  // ==================================================================== 34 · cobertura
  // Tabla 3.7 de final4 y su nota: el universo (18), lo que queda fuera del alcance disciplinar
  // (18), lo anterior al procedimiento de cálculo (12) y lo no expuesto (1). Los nombres son los
  // de la Tabla 3.7 (se ven al pasar el puntero en la versión en vivo).
  const UNIVERSO = {
    FEA13: 'Selección del tipo de elemento', FEA14: 'Definición del tamaño de elemento',
    FEA15: 'Efecto de la relación de aspecto y la distorsión en la exactitud', FEA16: 'Efecto del orden del elemento en la exactitud',
    FEA17: 'Refinamiento y convergencia de la malla', FEA18: 'Refinar en zonas de concentración de tensiones',
    FEA26: 'Presentar resultados de desplazamiento y tensión', FEA27: 'Diferencia entre tensiones nodales y elementales',
    FEA28: 'Deformada escalada', FEA29: 'Visualizar el efecto de las cargas y compararlo con los resultados',
    FEA30: 'Prueba de convergencia refinando hasta una diferencia dada', FEA31: 'Definición de la tensión de von Mises',
    FEA32: 'Revisar las tensiones para decidir el refinamiento', FEA33: 'Comparar las reacciones con las cargas aplicadas',
    FEA34: 'Correlacionar los resultados con referencias externas', FEM2: 'Ensamblar las rigideces, aplicar restricciones y resolver',
    FEM8: 'Formulación isoparamétrica de elementos bidimensionales', FEM9: 'Integración numérica de Gauss',
  };
  const FUERA = ['FEM1', 'FEM4', 'FEM5', 'FEM6', 'FEM7', 'FEM10', 'FEM11', 'FEM12', 'FEM13', 'FEM14', 'FEM15', 'FEA6', 'FEA7', 'FEA8', 'FEA9', 'FEA21', 'FEA22', 'FEA23'];
  const ANTES = ['FEA1', 'FEA2', 'FEA3', 'FEA4', 'FEA5', 'FEA10', 'FEA11', 'FEA12', 'FEA19', 'FEA20', 'FEA24', 'FEA25'];
  const NOEXP = ['FEM3'];

  EF.registrarViz('r34-cobertura', function (cont, L) {
    const raiz = L.el;
    const an = animador();
    ponerIconos(raiz);
    const caja = raiz.querySelector('.r34-items');
    const W = PPT() ? 1742 : 1720;
    const n18 = raiz.querySelector('.r34-n18');
    const f18 = raiz.querySelector('.r34-f18');
    const ok18 = f18.querySelector('.r34-ok');
    const tIni = Array.from(raiz.querySelectorAll('.r34-tit.t-ini'));
    const tGru = Array.from(raiz.querySelectorAll('.r34-tit.t-gru'));   // universo, fuera, anteriores, no expuesto
    const subs = Array.from(raiz.querySelectorAll('.r34-sub'));
    const ids = [...EF.rango(15).map((k) => 'FEM' + (k + 1)), ...EF.rango(34).map((k) => 'FEA' + (k + 1))];
    const grupo = (id) => (UNIVERSO[id] ? 'u' : FUERA.includes(id) ? 'f' : ANTES.includes(id) ? 'a' : 'x');
    const items = Object.fromEntries(ids.map((id) => {
      const e = EF.el('div', { class: 'r34-it', text: id, title: UNIVERSO[id] ? `${id} · ${UNIVERSO[id]}` : id });
      caja.appendChild(e);
      return [id, { e, g: grupo(id) }];
    }));
    const pos = (e, x, y) => { e.style.left = `${x}px`; e.style.top = `${y}px`; };

    // ---------- tamaños de ítem [ancho, alto, letra]: de partida, del universo y de los que quedan fuera
    const T0 = [100, 58, 25], TU = [112, 64, 27], TO = [80, 46, 22];
    const ancho = (cols, t, g) => cols * t[0] + (cols - 1) * g;
    // de partida: los dos bloques del consenso, conceptos (FEM) y destrezas (FEA)
    const wC = ancho(5, T0, 12), wD = ancho(9, T0, 12), h0 = 80;
    const x0 = Math.round((W - (wC + h0 + wD)) / 2);
    const ini = {};
    ids.forEach((id) => {
      const fem = id.startsWith('FEM'), k = Number(id.slice(3)) - 1, cols = fem ? 5 : 9;
      ini[id] = { x: (fem ? x0 : x0 + wC + h0) + (k % cols) * (T0[0] + 12), y: 50 + Math.floor(k / cols) * (T0[1] + 12), t: T0 };
    });
    pos(tIni[0], x0, 0); pos(tIni[1], x0 + wC + h0, 0);
    // final: el universo a la izquierda, grande; lo que queda fuera a la derecha, chico
    const fin = {};
    const ubicar = (lista, cols, x, y, t, g) => lista.forEach((id, k) => { fin[id] = { x: x + (k % cols) * (t[0] + g), y: y + Math.floor(k / cols) * (t[1] + g), t }; });
    const univ = Object.keys(UNIVERSO);
    const wU = ancho(6, TU, 12), xR = wU + 70, wA = ancho(6, TO, 10), xX = xR + wA + (PPT() ? 70 : 50);
    ubicar(univ, 6, 0, 50, TU, 12);
    ubicar(FUERA, 9, xR, 50, TO, 10);
    ubicar(ANTES, 6, xR, 262, TO, 10);
    ubicar(NOEXP, 1, xX, 262, TO, 10);
    pos(tGru[0], 0, 0); pos(tGru[1], xR, 0); pos(tGru[2], xR, 212); pos(tGru[3], xX, 212);
    pos(subs[0], 0, 286); subs[0].style.width = `${wU}px`;
    pos(subs[1], xR, 160); pos(subs[2], xR, 372); pos(subs[3], xX, 318);

    function colocar(id, f) {
      const a = ini[id], b = fin[id], s = items[id].e.style;
      s.left = `${EF.lerp(a.x, b.x, f).toFixed(1)}px`;
      s.top = `${EF.lerp(a.y, b.y, f).toFixed(1)}px`;
      s.width = `${EF.lerp(a.t[0], b.t[0], f).toFixed(1)}px`;
      s.height = `${EF.lerp(a.t[1], b.t[1], f).toFixed(1)}px`;
      s.fontSize = `${EF.lerp(a.t[2], b.t[2], f).toFixed(1)}px`;
    }
    const teñir = (id, si) => { const it = items[id]; it.e.className = 'r34-it' + (si ? ' ' + it.g : ''); };
    function marcar(n) {
      univ.forEach((id, k) => items[id].e.classList.toggle('ok', k < n));
      n18.textContent = n ? String(n) : '…';
    }
    function fijar(p) {
      const f = p >= 1 ? 1 : 0;
      for (const id of ids) { colocar(id, f); teñir(id, p >= 1); }
      marcar(p >= 1 ? 18 : 0);
      for (const t of tIni) op(t, p >= 1 ? 0 : 1);
      for (const t of [...tGru, ...subs]) op(t, p >= 1 ? 1 : 0);
      f18.classList.toggle('listo', p >= 1);
      op(ok18, p >= 1 ? 1 : 0);
    }
    /** Paso 1: los 49 se separan en sus cuatro grupos y los 18 del universo se marcan uno a uno. */
    function animar() {
      fijar(0);
      f18.classList.remove('listo');
      an.t({ dur: 300, retraso: 650, cada: (e) => { for (const t of tIni) op(t, 1 - e); } });
      const retrasoDe = { f: 700, a: 830, x: 960, u: 1000 };
      const enGrupo = { u: 0, f: 0, a: 0, x: 0 };
      ids.forEach((id) => {
        const g = items[id].g, r = retrasoDe[g] + 14 * enGrupo[g]++;
        an.t({ dur: 10, retraso: r, fin: () => teñir(id, true) });
        an.t({ dur: 720, retraso: r, curva: 'ambos', cada: (e) => colocar(id, e) });
      });
      an.t({ dur: 380, retraso: 1480, cada: (e) => { for (const t of [...tGru, ...subs]) op(t, e); } });
      univ.forEach((id, k) => an.t({ dur: 10, retraso: 1950 + k * 56, fin: () => marcar(k + 1) }));
      an.t({ dur: 10, retraso: 1950 + 18 * 56, fin: () => f18.classList.add('listo') });
      rebote(an, ok18, 1950 + 18 * 56 + 20, 0.3);
    }
    function estado(p, animarlo) {
      an.parar();
      if (p === 1 && animarlo) animar(); else fijar(p);
    }
    fijar(0);
    return {
      entrar(p, o) { estado(p, !o.instantaneo && !o.impresion); },
      paso(k, o) { estado(k, !!o.adelante && !o.salto); },
      salir() { an.parar(); },
    };
  });
  // ==================================================================== 35 · leccion
  // El elemento E3 del ejemplo guía, con los datos del motor: sus cuatro puntos de Gauss en el
  // orden en que el motor los numera, (−,−), (−,+), (+,−), (+,+) (Anexo G), y adónde lleva el
  // valor de cada uno la matriz de extrapolación: la que estaba escrita para otra numeración
  // (columnas 3 y 4 intercambiadas: E_extrap_mal, la de la versión con el defecto) y la corregida
  // (E_extrap, la inversa de la de interpolación). El cierre: volver a interpolar en los puntos de
  // Gauss los valores nodales (M_interp). Con la matriz corregida, cada valor vuelve igual.
  EF.registrarViz('r35-leccion', function (cont, L) {
    const raiz = L.el;
    const an = animador();
    ponerIconos(raiz);
    const C = DAT().canonico;
    const E3 = C.elementos[String(C.showcase)];
    const M = C.M_interp;
    // nodo que más recibe de cada punto de Gauss (filas de la matriz: nodos; columnas: puntos)
    const destino = (E) => [0, 1, 2, 3].map((k) => [0, 1, 2, 3].reduce((b, i) => (E[i][k] > E[b][k] ? i : b), 0));
    const dMal = destino(C.E_extrap_mal), dBien = destino(C.E_extrap);
    // punto de Gauss que más recibe de cada nodo al volver a interpolar (filas de M: puntos)
    const vuelta = [0, 1, 2, 3].map((i) => [0, 1, 2, 3].reduce((b, k) => (M[k][i] > M[b][i] ? k : b), 0));
    // el punto al que regresa el valor de cada punto de Gauss, con cada matriz
    const regresaMal = dMal.map((i) => vuelta[i]), regresaBien = dBien.map((i) => vuelta[i]);

    // ---------- dibujo (coordenadas físicas del ejemplo guía; y hacia arriba)
    const VB = [700, 516], s = 90, cx = 350, cy = 258;
    const P = (q) => [cx + s * (q[0] - 4.5), cy - s * (q[1] - 5.5)];
    const pn = E3.X.map(P), pg = E3.gauss.map((g) => P(g.x));
    const svg = S('svg', { viewBox: `0 0 ${VB[0]} ${VB[1]}`, preserveAspectRatio: 'xMidYMid meet', 'aria-hidden': 'true' }, raiz.querySelector('.r35-dibujo'));
    const gEl = S('g', {}, svg), gFl = S('g', {}, svg), gN = S('g', {}, svg), gP = S('g', {}, svg), gT = S('g', {}, svg);
    est(S('path', { d: pn.map((p, k) => `${k ? 'L' : 'M'} ${p[0]} ${p[1]}`).join(' ') + ' Z' }, gEl),
      { relleno: 'var(--primario-suave)', trazo: 'var(--texto-2)', estilo: 'stroke-width:3;stroke-linejoin:round' });
    E3.nodos.forEach((id, i) => {
      const [x, y] = pn[i];
      est(S('circle', { cx: x, cy: y, r: 21 }, gN), { relleno: 'var(--superficie)', trazo: 'var(--texto)', estilo: 'stroke-width:3' });
      texto(gN, x, y + 8.5, String(id), 'font:800 24px var(--fuente)', 'var(--texto)');
    });
    const aros = pg.map(([x, y], k) => {
      const aro = est(S('circle', { cx: x, cy: y, r: 28 }, gP), { relleno: 'none', trazo: 'var(--h-mal)', estilo: 'stroke-width:3.5' });
      est(S('circle', { cx: x, cy: y, r: 19 }, gP), { relleno: 'var(--primario)', trazo: 'none' });
      texto(gP, x, y + 8.5, String(k + 1), 'font:800 24px var(--fuente)', 'var(--fondo)');
      op(aro, 0);
      return aro;
    });
    // flechas: de cada punto de Gauss al nodo que más recibe de él
    const flechas = pg.map(() => {
      const g = S('g', {}, gFl);
      const p = linea(g, 'M 0 0', 'var(--texto-3)', 3.5);
      const h = est(S('path', { d: 'M 0 0' }, g), { relleno: 'var(--texto-3)', trazo: 'none' });
      return { g, p, h };
    });
    function ponerFlecha(f, a, b, color) {
      const dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
      const x0 = a[0] + ux * 23, y0 = a[1] + uy * 23;
      const x1 = b[0] - ux * 25, y1 = b[1] - uy * 25;
      const xb = x1 - ux * 15, yb = y1 - uy * 15;
      f.p.setAttribute('d', `M ${x0.toFixed(1)} ${y0.toFixed(1)} L ${xb.toFixed(1)} ${yb.toFixed(1)}`);
      f.h.setAttribute('d', `M ${x1.toFixed(1)} ${y1.toFixed(1)} L ${(xb - uy * 8).toFixed(1)} ${(yb + ux * 8).toFixed(1)} L ${(xb + uy * 8).toFixed(1)} ${(yb - ux * 8).toFixed(1)} Z`);
      f.p.style.stroke = color; f.h.style.fill = color;
    }
    const COL = { neutro: 'var(--texto-3)', mal: 'var(--h-mal)', ok: 'var(--h-ok)' };
    const malo = (k) => dMal[k] !== dBien[k];
    // fichas: el valor de cada punto de Gauss, que va al nodo y vuelve. La que vuelve a un punto
    // ajeno queda junto a él, en rojo; la que vuelve al suyo se funde con él y deja una marca.
    const centro = P([4.5, 5.5]);
    const hacia = (q, d) => { const dx = centro[0] - q[0], dy = centro[1] - q[1], n = Math.hypot(dx, dy); return [q[0] + (d * dx) / n, q[1] + (d * dy) / n]; };
    const dock = pg.map((q) => hacia(q, 38));
    // la marca va del lado contrario a la flecha corregida, para no taparla
    const marcaEn = pg.map((q, k) => {
      const dx = pn[dBien[k]][0] - q[0];
      return dx > 20 ? [q[0] - 34, q[1] + 10] : [q[0] + 34, q[1] + 10];
    });
    const marcaMal = pg.map((q) => hacia(q, 70));
    const fichas = pg.map((_, k) => {
      const g = S('g', {}, gT);
      const c = est(S('circle', { cx: 0, cy: 0, r: 17 }, g), { relleno: 'var(--superficie)', trazo: 'var(--texto-2)', estilo: 'stroke-width:2.5' });
      const t = texto(g, 0, 8.3, String(k + 1), 'font:800 23.5px var(--fuente)', 'var(--texto)');
      op(g, 0);
      return { g, c, t };
    });
    const marcas = pg.map(() => { const t = texto(gT, 0, 0, '', 'font:900 30px var(--fuente)', 'var(--h-ok)'); op(t, 0); return t; });
    const mover = (f, q) => f.g.setAttribute('transform', `translate(${q[0].toFixed(1)} ${q[1].toFixed(1)})`);
    /** La ficha k en su estado de llegada al punto r. */
    function atracar(k, r) {
      const f = fichas[k], ok = r === k, m = marcas[r];
      m.textContent = ok ? '✓' : '✗';
      m.style.fill = ok ? 'var(--h-ok)' : 'var(--h-mal)';
      const q = ok ? marcaEn[r] : [marcaMal[r][0], marcaMal[r][1] + 10];
      m.setAttribute('x', q[0].toFixed(1)); m.setAttribute('y', q[1].toFixed(1));
      op(m, 1);
      if (ok) { op(f.g, 0); return; }
      mover(f, dock[r]); op(f.g, 1);
      f.c.style.fill = 'var(--h-mal)'; f.c.style.stroke = 'none';
      f.t.style.fill = 'var(--fondo)';
    }
    function soltar(k) {
      const f = fichas[k];
      op(f.g, 0); f.c.style.fill = 'var(--superficie)'; f.c.style.stroke = 'var(--texto-2)'; f.t.style.fill = 'var(--texto)';
    }
    /** Recorrido por una poligonal, con fracción e en [0, 1] (tramos proporcionales a su largo). */
    function enRuta(pts, e) {
      const lg = [];
      let tot = 0;
      for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); lg.push(l); tot += l; }
      let d = e * tot;
      for (let i = 1; i < pts.length; i++) {
        if (d <= lg[i - 1] || i === pts.length - 1) { const t = lg[i - 1] ? Math.min(1, d / lg[i - 1]) : 1; return [EF.lerp(pts[i - 1][0], pts[i][0], t), EF.lerp(pts[i - 1][1], pts[i][1], t)]; }
        d -= lg[i - 1];
      }
      return pts[pts.length - 1];
    }

    // ---------- la tabla del cierre: σx de los puntos de Gauss (Tabla G.5) y su vuelta desde los nodos
    const filas = Array.from(raiz.querySelectorAll('.r35-tab tbody tr'));
    const sg = E3.sigma_gauss.map((v) => v[0]);
    const cMal = E3.cierre_mal.map((v) => v[0]), cBien = E3.cierre_bien.map((v) => v[0]);
    filas.forEach((tr, k) => {
      tr.querySelector('.r35-g').textContent = EF.fmt(sg[k], 2);
      tr.querySelector('td.r35-col-b').innerHTML = `${EF.fmt(cBien[k], 2)}<span class="marca">✓</span>`;
    });
    function celdaVuelta(k, visible) {
      const td = filas[k].querySelector('.r35-v');
      const ok = Math.abs(cMal[k] - sg[k]) < 1e-6;
      td.className = 'der r35-v' + (visible ? (ok ? ' ok' : ' mal') : '');
      td.innerHTML = visible ? `${EF.fmt(cMal[k], 2)}<span class="marca">${ok ? '✓' : '✗'}</span>` : '';
    }

    function estado(p, animar) {
      an.parar();
      // flechas
      pg.forEach((a, k) => {
        const b = pn[p >= 2 ? dBien[k] : dMal[k]];
        ponerFlecha(flechas[k], a, b, p >= 2 ? COL.ok : malo(k) ? COL.mal : COL.neutro);
        trazoEntero(flechas[k].p); op(flechas[k].h, 1); op(flechas[k].g, 1);
      });
      aros.forEach((a, k) => op(a, p <= 1 && malo(k) ? 1 : 0));
      // fichas y marcas
      fichas.forEach((_, k) => soltar(k));
      marcas.forEach((m) => op(m, 0));
      if (p >= 1) fichas.forEach((_, k) => atracar(k, p >= 2 ? regresaBien[k] : regresaMal[k]));
      filas.forEach((_, k) => celdaVuelta(k, p >= 1));
      if (!animar) return;

      if (p === 0) {
        // las cuatro flechas se dibujan: primero las que llegan a su nodo, después las cruzadas
        const orden = [0, 1, 2, 3].sort((a, b) => Number(malo(a)) - Number(malo(b)));
        aros.forEach((a) => op(a, 0));
        orden.forEach((k, j) => {
          const f = flechas[k], r = 450 + j * 330;
          trazoParcial(f.p, 0); op(f.h, 0);
          an.t({ dur: 480, retraso: r, curva: 'sale', cada: (e) => trazoParcial(f.p, e), fin: () => trazoEntero(f.p) });
          an.t({ dur: 200, retraso: r + 400, cada: (e) => op(f.h, e) });
        });
        aros.forEach((a, k) => { if (malo(k)) rebote(an, a, 1900, 0.4, 520); });
      } else if (p === 1) {
        // ida y vuelta: cada valor va al nodo que más recibe de él y regresa al punto más cercano a ese nodo
        filas.forEach((_, k) => celdaVuelta(k, false));
        fichas.forEach((f, k) => {
          soltar(k);
          const rr = regresaMal[k];
          const ruta = rr === k ? [pg[k], pn[dMal[k]], pg[rr]] : [pg[k], pn[dMal[k]], pg[rr], dock[rr]];
          const r = 250 + k * 90;
          mover(f, pg[k]);
          an.t({ dur: 200, retraso: r, cada: (e) => op(f.g, e) });
          an.t({ dur: 1500, retraso: r + 150, curva: 'ambos', cada: (e) => mover(f, enRuta(ruta, e)), fin: () => atracar(k, regresaMal[k]) });
        });
        marcas.forEach((m) => op(m, 0));
        an.t({ dur: 10, retraso: 2050, fin: () => filas.forEach((_, k) => celdaVuelta(k, true)) });
      } else {
        // la matriz corregida: las flechas cruzadas van a su nodo y los valores vuelven a su punto
        pg.forEach((a, k) => {
          ponerFlecha(flechas[k], a, pn[dMal[k]], malo(k) ? COL.mal : COL.neutro);
          if (!malo(k)) { an.t({ dur: 500, retraso: 200, cada: (e) => { flechas[k].p.style.stroke = e > 0.5 ? COL.ok : COL.neutro; flechas[k].h.style.fill = e > 0.5 ? COL.ok : COL.neutro; } }); return; }
          const A = pn[dMal[k]], B = pn[dBien[k]];
          an.t({ dur: 800, retraso: 150, curva: 'ambos', cada: (e) => ponerFlecha(flechas[k], a, [EF.lerp(A[0], B[0], e), EF.lerp(A[1], B[1], e)], e < 0.5 ? COL.mal : COL.ok) });
        });
        aros.forEach((a, k) => { if (malo(k)) { op(a, 1); an.t({ dur: 400, retraso: 150, cada: (e) => op(a, 1 - e) }); } });
        fichas.forEach((f, k) => {
          if (regresaMal[k] === regresaBien[k]) { atracar(k, regresaBien[k]); return; }
          atracar(k, regresaMal[k]);
          const de = dock[regresaMal[k]], a = pg[regresaBien[k]];
          const m = marcas[regresaMal[k]];
          an.t({ dur: 200, retraso: 950, cada: (e) => op(m, 1 - e) });
          an.t({ dur: 700, retraso: 1000, curva: 'ambos',
            cada: (e) => { mover(f, [EF.lerp(de[0], a[0], e), EF.lerp(de[1], a[1], e)]); if (e > 0.5) f.c.style.fill = 'var(--h-ok)'; op(f.g, e > 0.8 ? (1 - e) / 0.2 : 1); },
            fin: () => atracar(k, regresaBien[k]) });
        });
      }
    }
    return {
      entrar(p, o) { estado(p, !o.instantaneo && !o.impresion); },
      paso(k, o) { estado(k, !!o.adelante && !o.salto); },
      salir() { an.parar(); },
    };
  });
})();
