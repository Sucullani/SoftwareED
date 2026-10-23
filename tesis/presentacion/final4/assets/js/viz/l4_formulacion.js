/* =====================================================================
   viz/l4_formulacion.js — visualizaciones del grupo «formulacion» (final4).

   Lámina 11 · estado-arte   (viz «ea-matriz», data-pasos="3")
     0  la matriz de la Tabla 1.1 se arma columna por columna (ocho atributos × cinco recursos)
     1  entra la columna EduFEM (la anima el motor: data-paso="1")
     2  el vacío: se atenúan las demás filas y se marcan la 6 y la 8
     3  la matriz se repliega; salen los cinco requisitos y los cuatro principios
   Lámina 12 · formulacion   (viz «f12-formulacion», data-pasos="3")
     0  del pórtico a la chapa: las dos terminan en K u = F
     1  la forma fuerte: equilibrio punto por punto (pide derivadas segundas)
     2  el desplazamiento virtual: trabajo interno = trabajo externo, para todo δu admisible
     3  la cadena N → B → D → kₑ → ensamblaje → K u = F
   Lámina 13 · procedimiento (viz «f13-etapas», data-pasos="3")
     0  etapas 1–3 (geometría) · 1 etapas 4–5 (material y rigidez)
     2  etapas 6–8 (del elemento a la estructura) · 3 etapa 9 (tensiones)

   Los textos de lectura están en el HTML de cada lámina (el motor los muestra por paso);
   aquí se dibuja lo gráfico (SVG) y se mueve lo que la lámina anima. Toda animación pasa por
   EF.tween / EF.bucle (reloj virtual del video) y todo color es una variable CSS del tema,
   salvo la paleta jet de los campos de tensión (la del post-proceso de EduFEM).
   Los números salen de EDUFEM_DATOS (motor de EduFEM, ejemplo guía).
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const DAT = () => window.EDUFEM_DATOS;
  const S = (tag, at, padre) => EF.svg(tag, at, padre);
  const est = (e, o) => EF.estiloSvg(e, o);
  const op = (el, v) => { el.style.opacity = String(v); };

  // ------------------------------------------------------------------ trazos con variables CSS
  function linea(g, d, color, ancho, extra) {
    return est(S('path', { d }, g), { trazo: color, relleno: 'none', estilo: `stroke-width:${ancho};stroke-linecap:round;stroke-linejoin:round${extra ? ';' + extra : ''}` });
  }
  function forma(g, d, relleno, trazo, ancho, extra) {
    return est(S('path', { d }, g), { relleno: relleno || 'none', trazo: trazo || 'none', estilo: `stroke-width:${ancho || 0};stroke-linejoin:round${extra ? ';' + extra : ''}` });
  }
  function circulo(g, x, y, r, relleno, trazo, ancho, extra) {
    return est(S('circle', { cx: x, cy: y, r }, g), { relleno: relleno || 'none', trazo: trazo || 'none', estilo: `stroke-width:${ancho || 0}${extra ? ';' + extra : ''}` });
  }
  function rect(g, x, y, w, h, rx, relleno, trazo, ancho, extra) {
    return est(S('rect', { x, y, width: w, height: h, rx: rx || 0 }, g), { relleno: relleno || 'none', trazo: trazo || 'none', estilo: `stroke-width:${ancho || 0}${extra ? ';' + extra : ''}` });
  }
  /** Texto SVG; «σ_x» o «σ_{xy}» se escriben con subíndice. estilo: «font:…» o solo la fuente. */
  function texto(g, x, y, t, estilo, color, ancla) {
    if (!/^\s*[a-z-]+\s*:/.test(estilo)) estilo = 'font:' + estilo;
    const e = S('text', { x, y, 'text-anchor': ancla || 'middle' }, g);
    for (const p of EF.partesSub(String(t))) {
      const ts = S('tspan', { text: p.t }, e);
      if (p.sub) { ts.setAttribute('baseline-shift', 'sub'); ts.setAttribute('font-size', '70%'); }
    }
    return est(e, { relleno: color, estilo });
  }
  function punta(g, x2, y2, ux, uy, p, color) {
    const bx = x2 - ux * p, by = y2 - uy * p;
    return forma(g, `M${x2},${y2} L${bx - uy * p * 0.55},${by + ux * p * 0.55} L${bx + uy * p * 0.55},${by - ux * p * 0.55} Z`, color);
  }
  /** Flecha de (x1,y1) a (x2,y2): devuelve {g, l, pt} (el trazo y la punta por separado). */
  function flecha(g, x1, y1, x2, y2, color, ancho, p) {
    p = p || ancho * 3;
    const L = Math.hypot(x2 - x1, y2 - y1) || 1, ux = (x2 - x1) / L, uy = (y2 - y1) / L;
    const gg = S('g', {}, g);
    const l = linea(gg, `M${x1},${y1} L${x2 - ux * p * 0.8},${y2 - uy * p * 0.8}`, color, ancho);
    const pt = punta(gg, x2, y2, ux, uy, p, color);
    return { g: gg, l, pt };
  }
  const poli = (pts) => 'M' + pts.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' L') + ' Z';
  const abierta = (pts) => 'M' + pts.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' L');

  /** Registro de las animaciones en curso de una visualización, para cancelarlas al saltar. */
  function animador() {
    const activos = [];
    return {
      tw(o) { const t = EF.tween(o); activos.push(t); return t; },
      /** Dibuja un trazo de 0 a 100 %; la longitud se mide en el primer cuadro (el contenedor
       *  puede estar todavía oculto cuando se programa). */
      trazar(p, o) {
        o = o || {};
        let L = null;
        p.style.strokeDasharray = '1 100000'; p.style.strokeDashoffset = '0';
        const t = EF.tween({
          dur: o.dur || 700, retraso: o.retraso || 0, curva: o.curva || 'ambos',
          cada(e) {
            if (L == null) { try { L = p.getTotalLength() || 1; } catch (er) { L = 1000; } }
            p.style.strokeDasharray = `${L} ${L}`; p.style.strokeDashoffset = String(L * (1 - e));
          },
          fin() { p.style.strokeDasharray = ''; p.style.strokeDashoffset = ''; },
        });
        activos.push(t);
        return t;
      },
      cancelar() { for (const t of activos.splice(0)) t.cancelar(false); },
    };
  }
  const limpiarTrazo = (p) => { p.style.strokeDasharray = ''; p.style.strokeDashoffset = ''; };

  // ------------------------------------------------------------------ íconos pequeños (HTML [data-ico])
  // Se dibujan en currentColor o con variables del tema, dentro de un viewBox de 100 × 100.
  const ICONOS = {
    traza(g) {   // dos eslabones de cadena
      const c = 'currentColor';
      forma(g, 'M14,58 a16,16 0 0 1 0,-22 l14,-14 a16,16 0 0 1 22,0 l4,4', 'none', c, 9, 'stroke-linecap:round');
      forma(g, 'M86,42 a16,16 0 0 1 0,22 l-14,14 a16,16 0 0 1 -22,0 l-4,-4', 'none', c, 9, 'stroke-linecap:round');
      linea(g, 'M36,64 L64,36', c, 9);
    },
    verif(g) {   // un valor dentro de la banda de tolerancia
      const c = 'currentColor';
      rect(g, 6, 34, 88, 32, 6, 'currentColor', 'none', 0, 'fill-opacity:.22');
      linea(g, 'M6,50 H94', c, 4, 'stroke-dasharray:8 7');
      linea(g, 'M26,52 L42,68 L74,30', c, 10);
    },
    ambas(g) { ICONOS.traza(S('g', { transform: 'translate(-6,-6) scale(.62)' }, g)); ICONOS.verif(S('g', { transform: 'translate(40,40) scale(.62)' }, g)); },
    alcance(g) { // una persona
      const c = 'currentColor';
      circulo(g, 50, 30, 17, c);
      forma(g, 'M18,92 a32,32 0 0 1 64,0 Z', c);
    },
    // los cuatro principios (§ 1.2) se dibujan en el neutro: el azul queda para la variable independiente
    ojo(g) {
      const c = 'var(--h-neutro)';
      forma(g, 'M4,50 C24,18 76,18 96,50 C76,82 24,82 4,50 Z', 'var(--fondo)', c, 6);
      circulo(g, 50, 50, 17, c);
      circulo(g, 56, 44, 5, 'var(--fondo)');
    },
    mano(g) {    // cursor que toca un nodo de la malla
      const c = 'var(--h-neutro)';
      forma(g, 'M6,10 H62 V62 H6 Z', 'var(--fondo)', 'var(--malla)', 4);
      linea(g, 'M34,10 V62 M6,36 H62', 'var(--malla)', 3);
      circulo(g, 34, 36, 7, c);
      forma(g, 'M44,46 L92,64 L72,70 L84,92 L74,96 L62,74 L48,88 Z', c, 'var(--fondo)', 3);
    },
    escalera(g) {
      const c = 'var(--h-neutro)';
      forma(g, 'M6,92 V74 H28 V56 H50 V38 H72 V20 H94 V92 Z', 'var(--h-neutro-suave)', c, 5);
      forma(g, 'M22,64 l8,-9 l8,9 M44,46 l8,-9 l8,9 M66,28 l8,-9 l8,9', 'none', c, 4, 'stroke-linecap:round');
    },
    puente(g) {
      const c = 'var(--h-neutro)';
      linea(g, 'M2,46 H98', c, 7);
      forma(g, 'M14,46 Q50,4 86,46', 'none', c, 5);
      for (const x of [26, 38, 50, 62, 74]) linea(g, `M${x},46 V${46 - (26 - Math.abs(x - 50) * 0.75)}`, c, 3);
      forma(g, 'M10,46 H22 V92 H10 Z M78,46 H90 V92 H78 Z', c);
      forma(g, 'M0,92 H100', 'none', 'var(--texto-3)', 3);
    },
  };
  function dibujarIconos(raiz) {
    for (const span of raiz.querySelectorAll('[data-ico]')) {
      if (span._ico) continue;
      const f = ICONOS[span.getAttribute('data-ico')];
      if (!f) continue;
      const svg = S('svg', { viewBox: '0 0 100 100', preserveAspectRatio: 'xMidYMid meet' }, span);
      f(S('g', {}, svg));
      span._ico = true;
    }
  }

  // ===================================================================== 11 · estado del arte
  EF.registrarViz('ea-matriz', function (cont, L) {
    dibujarIconos(L.el);
    const A = animador();
    const mat = cont.querySelector('.ea-mat');
    const filas = Array.from(mat.querySelectorAll('.ea-fila'));
    // columnas de los cinco recursos (la de EduFEM la revela el motor en el paso 1)
    const columnas = [0, 1, 2, 3, 4].map((c) => filas.map((f) => f.children[c + 1]));
    const rotulosFila = filas.map((f) => f.children[0]);
    const vacias = filas.filter((f) => f.hasAttribute('data-clase-paso'));
    const otras = filas.slice(1).filter((f) => !f.hasAttribute('data-clase-paso'));

    function limpiar() {
      A.cancelar();
      for (const col of columnas) for (const c of col) { c.style.opacity = ''; c.style.transform = ''; }
      for (const r of rotulosFila) { r.style.opacity = ''; r.style.transform = ''; }
      for (const f of filas) f.style.opacity = '';
      for (const f of vacias) for (const c of f.children) c.style.boxShadow = '';
      mat.style.opacity = ''; mat.style.transform = ''; mat.style.visibility = '';
    }
    function estado(p) {
      limpiar();
      if (p === 2) for (const f of otras) f.style.opacity = '0.3';
      if (p >= 3) { mat.style.visibility = 'hidden'; mat.style.opacity = '0'; }
    }
    // paso 0: los rótulos de fila y después cada columna, de arriba abajo
    function armar() {
      estado(0);
      rotulosFila.forEach((r, k) => {
        op(r, 0);
        A.tw({ dur: 320, retraso: 150 + k * 45, cada: (e) => { op(r, e); r.style.transform = `translateX(${-18 * (1 - e)}px)`; }, fin: () => { r.style.transform = ''; } });
      });
      columnas.forEach((col, c) => col.forEach((cel, k) => {
        op(cel, 0);
        A.tw({ dur: 340, retraso: 520 + c * 400 + k * 42, cada: (e) => { op(cel, e); cel.style.transform = `translateY(${12 * (1 - e)}px)`; }, fin: () => { cel.style.transform = ''; } });
      }));
    }
    // paso 2: se atenúan las demás filas y el contorno del vacío se dibuja
    function vacio() {
      estado(1);
      for (const f of otras) A.tw({ dur: 520, retraso: 200, cada: (e) => op(f, 1 - 0.7 * e) });
      for (const f of vacias) {
        const celdas = Array.from(f.children).filter((c) => c.classList.contains('ea-c') && !c.classList.contains('edu'));
        celdas.forEach((c, k) => A.tw({
          dur: 380, retraso: 380 + k * 90,
          cada: (e) => { c.style.boxShadow = `inset 0 0 0 ${(3 * e).toFixed(2)}px var(--acento)`; },
          fin: () => { c.style.boxShadow = ''; },
        }));
      }
    }
    // paso 3: la matriz se repliega hacia arriba; los requisitos salen de ella (los revela el motor)
    function replegar() {
      estado(2);
      A.tw({
        dur: 460, curva: 'entra',
        cada: (e) => { op(mat, 1 - e); mat.style.transform = `translateY(${-30 * e}px) scaleY(${1 - 0.75 * e})`; },
        fin: () => { mat.style.visibility = 'hidden'; },
      });
    }
    return {
      entrar(p, o) {
        if (p === 0 && !o.instantaneo && !o.impresion) armar();
        else estado(p);
      },
      paso(k, o) {
        if (o.adelante && k === 2) { vacio(); return; }
        if (o.adelante && k === 3) { replegar(); return; }
        estado(k);
      },
      salir() { A.cancelar(); },
    };
  });

  // ===================================================================== datos del ejemplo guía
  /** Malla del ejemplo guía (nueve nodos, cuatro Q4) tal como la exporta el motor. */
  function ejemploGuia() {
    const C = DAT().canonico;
    const P = C.nodos.map((n) => [n.x, n.y]);
    const idx = Object.fromEntries(C.nodos.map((n, i) => [n.id, i]));
    const elems = Object.keys(C.elementos_conect).map(Number).sort((a, b) => a - b)
      .map((k) => ({ id: k, con: C.elementos_conect[String(k)].map((id) => idx[id]), dofs: C.elementos[String(k)].dofs }));
    const borde = [1, 2, 3, 6, 9, 8, 7, 4].map((id) => idx[id]);   // contorno, en orden
    return { C, P, idx, elems, borde, apoyos: C.apoyos.map((id) => idx[id]), nc: idx[C.carga.nodo] };
  }
  const G1 = 1 / Math.sqrt(3);
  const PG = [[-G1, -G1], [-G1, G1], [G1, -G1], [G1, G1]];   // orden del motor
  /** Punto físico de un Q4 en (ξ, η). */
  function mapear(X, xi, eta) {
    const N = EF.Q4.N(xi, eta);
    return [EF.interp(N, X.map((p) => p[0])), EF.interp(N, X.map((p) => p[1]))];
  }
  /** Vista mundo → lámina (y hacia arriba). */
  function vista(ox, oy, s) { return { X: (x) => ox + s * x, Y: (y) => oy - s * y, s, P: (p) => [ox + s * p[0], oy - s * p[1]] }; }
  /** Apoyo fijo: triángulo bajo el punto y suelo rayado. */
  function apoyo(g, x, y, t) {
    const c = 'var(--apoyo)';
    forma(g, `M${x},${y} L${x - t},${y + 1.5 * t} L${x + t},${y + 1.5 * t} Z`, c, c, 2.5, 'fill-opacity:.28');
    linea(g, `M${x - 1.5 * t},${y + 1.5 * t + 3} H${x + 1.5 * t}`, c, 3);
    for (let k = 0; k < 4; k++) linea(g, `M${x - 1.2 * t + k * 0.75 * t},${y + 1.5 * t + 4} l${-0.45 * t},${0.55 * t}`, c, 1.8);
  }
  /** Rejilla de una matriz (n × n) que se pinta por bloques; devuelve {pintar(dofs, anim), limpiar()}. */
  function rejillaK(g, x0, y0, n, cel, color) {
    const celdas = [];
    for (let i = 0; i < n; i++) {
      celdas.push([]);
      for (let j = 0; j < n; j++) {
        const r = rect(g, x0 + j * cel, y0 + i * cel, cel - 1.5, cel - 1.5, Math.min(3, cel / 5), 'var(--superficie-3)');
        r.__n = 0;
        celdas[i].push(r);
      }
    }
    const alfa = (k) => (k <= 0 ? 0.12 : Math.min(1, 0.32 + 0.26 * (k - 1)));
    return {
      celdas,
      /** Suma el bloque de esos GDL (con A2, animado: el conteo sube cuando le toca). */
      pintar(dofs, A2, retraso) {
        const blq = [];
        for (const a of dofs) for (const b of dofs) blq.push(celdas[a][b]);
        let sumado = false;
        const aplicar = (e) => {
          if (!sumado) { for (const r of blq) { r.__prev = r.__n; r.__n += 1; } sumado = true; }
          for (const r of blq) { const a0 = alfa(r.__prev), a1 = alfa(r.__n); r.style.fill = color; r.style.fillOpacity = String(a0 + (a1 - a0) * e); }
        };
        if (A2) A2.tw({ dur: 260, retraso: retraso || 0, cada: aplicar }); else aplicar(1);
      },
      limpiar() { for (const f of celdas) for (const r of f) { r.__n = 0; r.style.fill = 'var(--superficie-3)'; r.style.fillOpacity = '1'; } },
    };
  }

  // ===================================================================== 12 · formulación variacional
  EF.registrarViz('f12-formulacion', function (cont) {
    const A = animador();
    const EG = ejemploGuia();
    const { C, P, elems, borde, apoyos, nc } = EG;
    const esc = [0, 1, 2, 3].map((k) => cont.querySelector('.f12-esc.e' + k));
    function svgEn(padre, w, h, alFinal) {
      const s = S('svg', { class: 'viz f12-svg', width: w, height: h, viewBox: `0 0 ${w} ${h}` });
      if (alFinal) padre.appendChild(s); else padre.insertBefore(s, padre.firstChild);
      return s;
    }
    const FMAT = "italic 600 30px 'KaTeX_Math','Times New Roman',serif";

    // ------------------------------------------------------------ escena 0 · del pórtico a la chapa
    const s0 = svgEn(esc[0], 1720, 716);
    const gPort = S('g', {}, s0), gChapa = S('g', {}, s0), gFl0 = S('g', {}, s0);
    const NP = [[70, 476], [70, 200], [390, 200], [390, 476]];
    for (const k of [0, 3]) {
      const [x, y] = NP[k];
      linea(gPort, `M${x - 40},${y + 2} H${x + 40}`, 'var(--apoyo)', 4);
      for (let j = 0; j < 6; j++) linea(gPort, `M${x - 34 + j * 13},${y + 4} l-11,13`, 'var(--apoyo)', 2.2);
    }
    const barras = [[0, 1], [1, 2], [2, 3]].map(([a, b]) => linea(gPort, `M${NP[a][0]},${NP[a][1]} L${NP[b][0]},${NP[b][1]}`, 'var(--primario)', 12));
    const juntas = NP.map(([x, y]) => circulo(gPort, x, y, 9, 'var(--fondo)', 'var(--nodo)', 4));
    texto(gPort, 230, 186, 'barra', 'font:650 24px var(--fuente)', 'var(--texto-3)');
    const KP = rejillaK(S('g', {}, s0), 520, 360, 12, 15, 'var(--primario)');
    const dofsBarra = [[0, 1, 2, 3, 4, 5], [3, 4, 5, 6, 7, 8], [6, 7, 8, 9, 10, 11]];
    // chapa: el ejemplo guía, dividido en sus cuatro elementos
    const v0 = vista(950, 506, 40);
    const polys0 = elems.map((e) => forma(gChapa, poli(e.con.map((i) => v0.P(P[i]))), 'var(--acento-suave)', 'var(--malla)', 3));
    for (const i of apoyos) { const [x, y] = v0.P(P[i]); apoyo(gChapa, x, y, 11); }
    { const [x, y] = v0.P(P[nc]); flecha(gChapa, x, y - 62, x, y - 5, 'var(--carga)', 5, 14); }
    for (const [x, y] of P.map((p) => v0.P(p))) circulo(gChapa, x, y, 6, 'var(--fondo)', 'var(--nodo)', 3);
    const gauss0 = elems.map((e) => {
      const X = e.con.map((i) => P[i]);
      return PG.map(([xi, eta]) => { const [x, y] = v0.P(mapear(X, xi, eta)); return circulo(gChapa, x, y, 6, 'var(--aviso)', 'var(--fondo)', 1.5); });
    });
    const KC = rejillaK(S('g', {}, s0), 1480, 360, 18, 10, 'var(--acento)');
    const fl0 = [flecha(gFl0, 0, 0, 0, 0, 'var(--texto-3)', 3.5, 14), flecha(gFl0, 0, 0, 0, 0, 'var(--texto-3)', 3.5, 14)];
    fl0[0].l.setAttribute('d', 'M712,452 C770,452 790,520 792,588'); fl0[0].pt.setAttribute('d', 'M792,598 L784,582 L800,582 Z');
    // la de la chapa la rodea por debajo de la línea de apoyos y entra por el lado derecho de la caja
    fl0[1].l.setAttribute('d', 'M1472,486 C1420,486 1416,654 1300,654 L1078,654'); fl0[1].pt.setAttribute('d', 'M1064,654 L1080,646 L1080,662 Z');

    function estado0(final) {
      for (const b of barras) { limpiarTrazo(b); op(b, final ? 1 : 0); }
      KP.limpiar(); KC.limpiar();
      polys0.forEach((p) => { p.style.fill = 'var(--acento-suave)'; });
      for (const gs of gauss0) for (const c of gs) op(c, final ? 1 : 0);
      for (const f of fl0) { limpiarTrazo(f.l); op(f.g, final ? 1 : 0); }
      if (final) { dofsBarra.forEach((d) => KP.pintar(d)); elems.forEach((e) => KC.pintar(e.dofs)); }
    }
    function animar0() {
      estado0(false);
      const t0 = 260;
      barras.forEach((b, k) => {
        A.tw({ dur: 1, retraso: t0 + k * 380, fin: () => op(b, 1) });
        A.trazar(b, { dur: 330, retraso: t0 + k * 380 });
        KP.pintar(dofsBarra[k], A, t0 + k * 380 + 280);
      });
      elems.forEach((e, k) => {
        const t = t0 + 120 + k * 400;
        A.tw({ dur: 380, retraso: t, cada: (x) => { polys0[k].style.fill = x < 1 ? 'var(--acento)' : 'var(--acento-suave)'; polys0[k].style.fillOpacity = x < 1 ? String(0.25 + 0.3 * Math.sin(Math.PI * x)) : ''; } });
        gauss0[k].forEach((c, j) => A.tw({ dur: 160, retraso: t + 60 + j * 50, cada: (x) => op(c, x) }));
        KC.pintar(e.dofs, A, t + 260);
      });
      fl0.forEach((f, k) => { A.tw({ dur: 1, retraso: 1950, fin: () => op(f.g, 1) }); op(f.pt, 0); A.trazar(f.l, { dur: 420, retraso: 1950 + k * 80 }); A.tw({ dur: 160, retraso: 2330 + k * 80, cada: (x) => op(f.pt, x) }); });
    }

    // ------------------------------------------------------------ escena 1 · la forma fuerte
    const s1 = svgEn(esc[1], 1720, 540);
    const v1 = vista(40, 440, 40);
    const gPl1 = S('g', {}, s1);
    forma(gPl1, poli(borde.map((i) => v1.P(P[i]))), 'var(--primario-suave)', 'var(--primario)', 3);
    for (const i of apoyos) { const [x, y] = v1.P(P[i]); apoyo(gPl1, x, y, 10); }
    { const [x, y] = v1.P(P[nc]); flecha(gPl1, x, y - 58, x, y - 5, 'var(--carga)', 5, 14); }
    const Q = v1.P([6.3, 5.2]);
    const lupa = circulo(s1, Q[0], Q[1], 34, 'none', 'var(--texto)', 3);
    const punto = circulo(s1, Q[0], Q[1], 6, 'var(--texto)');
    const con1 = [linea(s1, `M${Q[0] + 26},${Q[1] - 22} L716,150`, 'var(--texto-3)', 2, 'stroke-dasharray:7 6'),
      linea(s1, `M${Q[0] + 26},${Q[1] + 22} L716,330`, 'var(--texto-3)', 2, 'stroke-dasharray:7 6')];
    const gDif = S('g', {}, s1);
    rect(gDif, 720, 150, 180, 180, 4, 'var(--fondo)', 'var(--texto)', 3);
    const pares1 = [];
    const parFlecha = (lista, etqs) => { const g = S('g', {}, gDif); const fl = lista.map(([a, b, c, d, col]) => flecha(g, a, b, c, d, col, 4.5, 15)); const et = etqs.map(([x, y, t, an, col]) => texto(g, x, y, t, FMAT, col, an)); pares1.push({ g, fl, et }); };
    parFlecha([[720, 240, 642, 240, 'var(--primario)'], [900, 240, 980, 240, 'var(--primario)']], [[640, 226, 'σ_x', 'end', 'var(--primario)'], [988, 232, 'σ_x + dσ_x', 'start', 'var(--primario)']]);
    parFlecha([[810, 330, 810, 404, 'var(--primario)'], [810, 150, 810, 76, 'var(--primario)']], [[826, 410, 'σ_y', 'start', 'var(--primario)'], [826, 82, 'σ_y + dσ_y', 'start', 'var(--primario)']]);
    // tangenciales (Ecuación 1.1): τxy + dτxy en las caras positivas (derecha y superior), τxy en las negativas
    parFlecha([[914, 290, 914, 190, 'var(--texto-2)'], [706, 190, 706, 290, 'var(--texto-2)'], [760, 136, 860, 136, 'var(--texto-2)'], [860, 344, 760, 344, 'var(--texto-2)']],
      [[928, 300, 'τ_{xy} + dτ_{xy}', 'start', 'var(--texto-2)'], [870, 129, 'τ_{xy} + dτ_{xy}', 'start', 'var(--texto-2)'],
        [688, 292, 'τ_{xy}', 'end', 'var(--texto-2)'], [870, 356, 'τ_{xy}', 'start', 'var(--texto-2)']]);
    parFlecha([[810, 212, 810, 268, 'var(--carga)']], [[826, 262, 'b', 'start', 'var(--carga)']]);
    // el desplazamiento por trozos (dentro de la nota)
    const sN = svgEn(esc[1].querySelector('.e1-nota'), 700, 172);
    // la curva se aplana (0,74) para dejar más de 8 px bajo el rótulo «… por trozos», aun en el pulso
    const xU = (t) => 50 + t * 150, yU = (u) => 124 - 0.74 * u;
    const uEx = (t) => 18 + 62 * Math.sin(0.78 * t) + 4 * t;
    const exacta = linea(sN, abierta(EF.rango(41).map((k) => [xU(k / 10), yU(uEx(k / 10))])), 'var(--texto-3)', 2.5, 'stroke-dasharray:8 7');
    const trozos = linea(sN, abierta([0, 1, 2, 3, 4].map((t) => [xU(t), yU(uEx(t))])), 'var(--primario)', 5);
    const nodosU = [0, 1, 2, 3, 4].map((t) => circulo(sN, xU(t), yU(uEx(t)), 6, 'var(--fondo)', 'var(--primario)', 3));
    const quiebres = [1, 2, 3].map((t) => circulo(sN, xU(t), yU(uEx(t)), 15, 'none', 'var(--mal)', 3.5));
    linea(sN, `M${xU(0) - 10},124 H${xU(4) + 20}`, 'var(--linea-2)', 2);

    function estado1(final) {
      for (const e of [lupa, punto, gDif]) op(e, final ? 1 : 0);
      lupa.setAttribute('r', 34);
      for (const l of con1) { limpiarTrazo(l); op(l, final ? 1 : 0); }
      for (const p of pares1) { op(p.g, final ? 1 : 0); for (const f of p.fl) limpiarTrazo(f.l); }
      for (const e of [exacta, trozos]) { limpiarTrazo(e); op(e, final ? 1 : 0); }
      for (const n of nodosU) op(n, final ? 1 : 0);
      for (const q of quiebres) { op(q, final ? 1 : 0); q.setAttribute('r', 15); }
    }
    function animar1() {
      estado1(false);
      op(punto, 0);
      A.tw({ dur: 220, retraso: 260, cada: (e) => op(punto, e) });
      A.tw({ dur: 380, retraso: 420, curva: 'salePlus', cada: (e) => { op(lupa, 1); lupa.setAttribute('r', (34 * e).toFixed(1)); } });
      con1.forEach((l, k) => { A.tw({ dur: 1, retraso: 700, fin: () => op(l, 1) }); A.trazar(l, { dur: 320, retraso: 700 + k * 60 }); });
      A.tw({ dur: 260, retraso: 960, cada: (e) => op(gDif, e) });
      pares1.forEach((p, k) => {
        const t = 1120 + k * 260;
        A.tw({ dur: 1, retraso: t, fin: () => op(p.g, 1) });
        for (const f of p.fl) { op(f.pt, 0); A.trazar(f.l, { dur: 260, retraso: t }); A.tw({ dur: 120, retraso: t + 220, cada: (e) => op(f.pt, e) }); }
        for (const et of p.et) { op(et, 0); A.tw({ dur: 260, retraso: t + 180, cada: (e) => op(et, e) }); }
      });
      // la nota (la revela el motor a los 1,5 s): curva exacta, la aproximación por trozos, los quiebres
      A.tw({ dur: 1, retraso: 1750, fin: () => op(exacta, 1) });
      A.trazar(exacta, { dur: 420, retraso: 1750 });
      A.tw({ dur: 1, retraso: 2100, fin: () => op(trozos, 1) });
      A.trazar(trozos, { dur: 420, retraso: 2100 });
      nodosU.forEach((n, k) => A.tw({ dur: 140, retraso: 2100 + k * 90, cada: (e) => op(n, e) }));
      quiebres.forEach((q, k) => A.tw({
        dur: 520, retraso: 2440 + k * 140, curva: 'lineal',
        cada: (e) => { op(q, Math.min(1, e * 3)); q.setAttribute('r', (15 + 6 * Math.sin(Math.PI * e)).toFixed(1)); },
        fin: () => q.setAttribute('r', 15),
      }));
    }

    // ------------------------------------------------------------ escena 2 · el desplazamiento virtual
    const anim2 = esc[2].querySelector('.e2-anim');
    const s2 = svgEn(anim2, 1720, 520, true);
    const v2 = vista(150, 440, 45);
    const HALO2 = 'paint-order:stroke;stroke:var(--fondo);stroke-width:6px;stroke-linejoin:round';
    const gPl2 = S('g', {}, s2);
    // tensiones reales (von Mises), en tono suave: son las del ejemplo guía resuelto
    {
      const vm = C.nodos.map((n) => C.nodal[String(n.id)].vm);
      const vmin = Math.min(...vm), vmax = Math.max(...vm);
      const gC = S('g', { style: 'opacity:.26' }, gPl2);
      const n = 8;
      for (const e of elems) {
        const X = e.con.map((i) => P[i]), V = e.con.map((i) => vm[i]);
        for (let a = 0; a < n; a++) for (let b = 0; b < n; b++) {
          const xi0 = -1 + (2 * b) / n, xi1 = -1 + (2 * (b + 1)) / n, et0 = -1 + (2 * a) / n, et1 = -1 + (2 * (a + 1)) / n;
          const v = EF.interp(EF.Q4.N((xi0 + xi1) / 2, (et0 + et1) / 2), V);
          const col = EF.jetCss((v - vmin) / (vmax - vmin));
          forma(gC, poli([[xi0, et0], [xi1, et0], [xi1, et1], [xi0, et1]].map(([x, y]) => v2.P(mapear(X, x, y)))), col, col, 0.8);
        }
      }
    }
    for (const e of elems) forma(gPl2, poli(e.con.map((i) => v2.P(P[i]))), 'none', 'var(--malla)', 2, 'stroke-opacity:.75');
    forma(gPl2, poli(borde.map((i) => v2.P(P[i]))), 'none', 'var(--texto-2)', 3);
    for (const i of apoyos) { const [x, y] = v2.P(P[i]); apoyo(gPl2, x, y, 11); }
    {
      const [x1, y1] = v2.P(P[apoyos[0]]); texto(gPl2, x1 - 22, y1 + 8, 'δu = 0', 'font:650 22px var(--fuente)', 'var(--texto-3)', 'end');
      const [x3, y3] = v2.P(P[apoyos[2]]); texto(gPl2, x3 + 26, y3 + 8, 'δu = 0', 'font:650 22px var(--fuente)', 'var(--texto-3)', 'start');
    }
    { const [x, y] = v2.P(P[nc]); flecha(gPl2, x, y - 70, x, y - 5, 'var(--carga)', 5.5, 16); texto(gPl2, x - 20, y - 40, 'P', FMAT, 'var(--carga)', 'end'); }
    const gVir = S('g', {}, s2);
    const virInt = elems.map(() => linea(gVir, 'M0,0', 'var(--texto)', 1.6, 'stroke-dasharray:5 6;stroke-opacity:.7'));
    const virBorde = forma(gVir, 'M0,0', 'none', 'var(--texto)', 3.5, 'stroke-dasharray:12 8');
    const virNodos = P.map(() => circulo(gVir, 0, 0, 5, 'var(--texto)'));
    // δu del nodo cargado: la flecha va del nodo a su posición desplazada, sobre un halo del fondo para
    // que se lea encima del contorno punteado; el símbolo queda fijo arriba y a la derecha del nodo,
    // fuera del contorno, y no sigue al nodo
    const flDuHalo = linea(gVir, 'M0,0', 'var(--fondo)', 10);
    const flDu = flecha(gVir, 0, 0, 0, 0, 'var(--texto)', 3.5, 13);
    { const [x, y] = v2.P(P[nc]); texto(gVir, x + 22, y - 20, 'δu', 'font:' + FMAT + ';' + HALO2, 'var(--texto)', 'start'); }
    // modos virtuales (valores nodales; nulos en los apoyos 1, 3 y 6)
    const libre = (i) => !apoyos.includes(i);
    const modo = (f) => P.map((p, i) => (libre(i) ? f(p[0], p[1], i) : [0, 0]));
    const id = (n) => EG.idx[n];
    const especial = { [id(2)]: [0, -0.15], [id(4)]: [0.15, -0.35], [id(5)]: [0, -0.25], [id(7)]: [0, -1.2], [id(8)]: [-0.1, -0.55], [id(9)]: [0, -0.1] };
    const MODOS = [
      modo((x, y) => [0, -y / 8]),
      modo((x, y) => [0.9 * (y / 8), -0.6 * (y / 8) * (x / 9)]),
      modo((x, y, i) => especial[i] || [0, 0]),
    ];
    // trabajo interno δUᵀ(K u) y externo δUᵀF, cada uno por su lado (K, u y F del motor)
    const Ku = C.K.map((f) => f.reduce((s, v, j) => s + v * C.u[j], 0));
    const plano = (m) => m.flatMap((d) => d);
    const W = MODOS.map((m) => { const d = plano(m); return { int: d.reduce((s, v, j) => s + v * Ku[j], 0) / 1000, ext: d.reduce((s, v, j) => s + v * C.F[j], 0) / 1000 }; });
    // balanza con sus dos medidores
    const gBal = S('g', {}, s2);
    const FX = 1290, FY = 410;
    forma(gBal, `M${FX},${FY} L${FX - 40},${FY + 60} L${FX + 40},${FY + 60} Z`, 'var(--superficie-3)', 'var(--texto-2)', 3);
    linea(gBal, `M${FX - 80},${FY + 62} H${FX + 80}`, 'var(--texto-2)', 4);
    const gBrazo = S('g', {}, gBal);
    linea(gBrazo, `M900,${FY - 4} H1680`, 'var(--texto-2)', 9);
    const VMAX = 1.3, HMAX = 260, Y0M = FY - 22;
    const medidores = [[1040, 'var(--cian)'], [1540, 'var(--carga)']].map(([cx, col]) => {
      const g = S('g', {}, gBrazo);
      linea(g, `M${cx},${FY - 8} V${Y0M + 6}`, 'var(--texto-2)', 5);
      rect(g, cx - 95, Y0M, 190, 10, 4, 'var(--texto-2)');
      rect(g, cx - 46, Y0M - HMAX, 92, HMAX, 6, 'var(--superficie-2)', 'var(--linea-2)', 2);
      for (let k = 1; k < 6; k++) linea(g, `M${cx - 46},${Y0M - (k * HMAX) / 6} h14 M${cx + 46},${Y0M - (k * HMAX) / 6} h-14`, 'var(--linea-2)', 2);
      const barra = rect(g, cx - 40, Y0M - 6, 80, 6, 4, col);
      return { cx, barra };
    });
    const gNivel = S('g', {}, gBal);
    circulo(gNivel, FX, FY - 60, 26, 'var(--ok-suave)', 'var(--ok)', 3);
    texto(gNivel, FX, FY - 49, '=', 'font:800 34px var(--fuente)', 'var(--ok)');
    linea(gNivel, `M${FX},${FY - 34} V${FY - 4}`, 'var(--ok)', 4);
    // palanca (analogía): P₁ a = P₂ b; giro virtual δθ: δ₁ = a δθ, δ₂ = b δθ
    const palDiv = EF.el('div', { class: 'e2-pal-svg', 'data-pptx-clip': 'f12-palanca:9600:ciclo', style: 'position:absolute;left:0;top:30px;width:224px;height:96px' });
    esc[2].querySelector('.e2-palanca').appendChild(palDiv);
    const sPal = S('svg', { class: 'viz', width: 224, height: 96, viewBox: '0 0 224 96', style: 'overflow:visible' }, palDiv);
    const PX = 100, PY = 70;
    forma(sPal, `M${PX},${PY} L${PX - 16},${PY + 24} L${PX + 16},${PY + 24} Z`, 'var(--superficie-3)', 'var(--texto-2)', 2.5);
    const gPal = S('g', {}, sPal);
    linea(gPal, `M${PX - 66},${PY - 2} H${PX + 110}`, 'var(--texto-2)', 6);
    rect(gPal, PX - 66 - 15, PY - 36, 30, 30, 4, 'var(--primario)');
    rect(gPal, PX + 110 - 10, PY - 25, 20, 20, 3, 'var(--primario)');
    // rótulos 12 px por encima de cada bloque: el subíndice no queda detrás
    texto(gPal, PX - 66, PY - 56, 'P_1', "italic 600 24px 'KaTeX_Math','Times New Roman',serif", 'var(--texto)');
    texto(gPal, PX + 110, PY - 45, 'P_2', "italic 600 24px 'KaTeX_Math','Times New Roman',serif", 'var(--texto)');

    let bucle2 = null;
    const K_DIB = 0.92;   // ampliación del desplazamiento virtual en el dibujo (la flecha δu mide más de 30 px)
    function dibujarVirtual(s) {
      const T = 3.2;
      const m = Math.floor(s / T) % 3, tau = (s % T) / T;
      const a = Math.pow(Math.sin(Math.PI * tau), 2);
      const d = MODOS[m];
      const Pd = P.map((p, i) => v2.P([p[0] + K_DIB * a * d[i][0], p[1] + K_DIB * a * d[i][1]]));
      virBorde.setAttribute('d', poli(borde.map((i) => Pd[i])));
      elems.forEach((e, k) => virInt[k].setAttribute('d', poli(e.con.map((i) => Pd[i]))));
      Pd.forEach((p, i) => { virNodos[i].setAttribute('cx', p[0].toFixed(1)); virNodos[i].setAttribute('cy', p[1].toFixed(1)); });
      const [x0, y0] = v2.P(P[nc]), [x1, y1] = Pd[nc];
      const lon = Math.hypot(x1 - x0, y1 - y0);
      // la flecha aparece cuando ya mide lo suficiente para leerse (a amplitud plena, de 40 a 50 px)
      const alfa = EF.clamp((lon - 18) / 12, 0, 1);
      op(flDu.g, alfa); op(flDuHalo, alfa);
      if (lon > 1) {
        const ux = (x1 - x0) / lon, uy = (y1 - y0) / lon, f = (v) => v.toFixed(1);
        const xa = x0 + 2 * ux, ya = y0 + 2 * uy;        // nace en el nodo
        const xt = x1 - 5 * ux, yt = y1 - 5 * uy;        // la punta toca el borde del nodo desplazado
        flDu.l.setAttribute('d', `M${f(xa)},${f(ya)} L${f(xt - 11 * ux)},${f(yt - 11 * uy)}`);
        flDu.pt.setAttribute('d', `M${f(xt)},${f(yt)} L${f(xt - 13 * ux - 7 * uy)},${f(yt - 13 * uy + 7 * ux)} L${f(xt - 13 * ux + 7 * uy)},${f(yt - 13 * uy - 7 * ux)} Z`);
        flDuHalo.setAttribute('d', `M${f(xa)},${f(ya)} L${f(xt - 5 * ux)},${f(yt - 5 * uy)}`);   // con el remate redondo llega a la punta
      }
      // cada medidor marca su propio cálculo (sin cifras en pantalla: la amplitud del δu es arbitraria)
      const vi = a * W[m].int, ve = a * W[m].ext;
      [vi, ve].forEach((v, k) => {
        const h = Math.max(6, (Math.min(v, VMAX) / VMAX) * (HMAX - 8));
        medidores[k].barra.setAttribute('y', (Y0M - 4 - h).toFixed(1));
        medidores[k].barra.setAttribute('height', h.toFixed(1));
      });
      // la balanza se inclinaría con la diferencia entre los dos trabajos (aquí, nula)
      const giro = Math.atan(40 * (vi - ve)) * 180 / Math.PI;
      gBrazo.setAttribute('transform', `rotate(${giro.toFixed(3)} ${FX} ${FY})`);
      gPal.setAttribute('transform', `rotate(${(-7 * a).toFixed(2)} ${PX} ${PY - 2})`);
    }
    /** Con vivo, el desplazamiento virtual oscila sin fin (tres modos); si no, queda el cuadro
     *  representativo: el primer modo a amplitud plena. */
    function estado2(vivo) {
      if (bucle2) { bucle2.detener(); bucle2 = null; }
      if (vivo) { dibujarVirtual(0); bucle2 = EF.bucle((s) => dibujarVirtual(s), { fps: 25 }); }
      else dibujarVirtual(1.6);
    }

    // ------------------------------------------------------------ escena 3 · la cadena hasta K u = F
    const s3 = svgEn(esc[3], 1720, 716);
    const gOk = S('g', {}, s3);
    const xV = (t) => 30 + t * 88, yV = (u) => 92 - 0.85 * u;
    linea(gOk, abierta([0, 1, 2, 3, 4].map((t) => [xV(t), yV(uEx(t))])), 'var(--ok)', 5);
    for (const t of [0, 1, 2, 3, 4]) circulo(gOk, xV(t), yV(uEx(t)), 5.5, 'var(--fondo)', 'var(--ok)', 3);
    circulo(gOk, 418, 46, 22, 'var(--ok)');
    linea(gOk, 'M407,46 L415,55 L430,37', 'var(--fondo)', 5);
    const COL = [[0, 250], [278, 250], [556, 250], [834, 330], [1192, 250], [1470, 250]];
    const minis = COL.map(() => S('g', {}, s3));
    const flechas3 = COL.slice(0, 5).map(([x, w], k) => flecha(s3, x + w + 3, 506, COL[k + 1][0] - 3, 506, 'var(--texto-3)', 4, 12));
    // 1 · funciones de forma: desplazamientos nodales de E3 y su interpolación en el interior
    const e3 = C.elementos[String(C.showcase)];
    const X3 = e3.X;
    const vE = (x0, y0, s) => vista(x0 - s * 2, y0 + s * 3, s);   // E3 ocupa x 2–7, y 3–8
    {
      const g = minis[0], v = vE(30, 400, 38);
      forma(g, poli(X3.map((p) => v.P(p))), 'var(--acento-suave)', 'var(--malla)', 3);
      const ue = [0, 1, 2, 3].map((k) => [e3.ue[2 * k], e3.ue[2 * k + 1]]);
      const um = Math.max(...ue.map((u) => Math.hypot(u[0], u[1])));
      const fl = (p, u, col, an) => { const [x, y] = v.P(p); const k = 46 / um; flecha(g, x, y, x + k * u[0], y - k * u[1], col, an, an * 3.2); };
      for (const [xi, eta] of [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5], [0, 0]]) {
        const N = EF.Q4.N(xi, eta);
        fl(mapear(X3, xi, eta), [EF.interp(N, ue.map((u) => u[0])), EF.interp(N, ue.map((u) => u[1]))], 'var(--primario)', 2.6);
      }
      X3.forEach((p, k) => fl(p, ue[k], 'var(--primario)', 4.5));
      for (const p of X3) { const [x, y] = v.P(p); circulo(g, x, y, 6, 'var(--fondo)', 'var(--nodo)', 3); }
    }
    // 2 · matriz B: el elemento sin deformar y deformado (ampliado)
    {
      const g = minis[1], v = vE(308, 400, 38);
      forma(g, poli(X3.map((p) => v.P(p))), 'none', 'var(--texto-3)', 2.5, 'stroke-dasharray:7 6');
      const k = 0.85 / Math.max(...e3.ue.map(Math.abs));   // el mayor desplazamiento, dibujado de 0,85 unidades
      const Xd = X3.map((p, i) => [p[0] + k * e3.ue[2 * i], p[1] + k * e3.ue[2 * i + 1]]);
      forma(g, poli(Xd.map((p) => v.P(p))), 'var(--primario-suave)', 'var(--primario)', 3.5);
      for (const p of Xd) { const [x, y] = v.P(p); circulo(g, x, y, 5, 'var(--fondo)', 'var(--nodo)', 3); }
      texto(g, 433, 330, 'ε', "italic 700 40px 'KaTeX_Math','Times New Roman',serif", 'var(--primario)');
    }
    // 3 · matriz D: un cuadrado con sus tensiones
    {
      const g = minis[2], cx = 681, cy = 285;
      rect(g, cx - 56, cy - 56, 112, 112, 4, 'var(--fondo)', 'var(--texto)', 3);
      for (const [a, b, c, d] of [[cx + 56, cy, cx + 108, cy], [cx - 56, cy, cx - 108, cy], [cx, cy - 56, cx, cy - 108], [cx, cy + 56, cx, cy + 108]]) flecha(g, a, b, c, d, 'var(--primario)', 4, 13);
      texto(g, cx, cy + 10, 'E, ν', "italic 700 30px 'KaTeX_Math','Times New Roman',serif", 'var(--texto)');
      texto(g, cx + 100, cy - 22, 'σ', "italic 700 32px 'KaTeX_Math','Times New Roman',serif", 'var(--primario)');
    }
    // 4 · rigidez del elemento: puntos de Gauss y la matriz 8 × 8 de E3
    {
      const g = minis[3], v = vE(846, 392, 32);
      forma(g, poli(X3.map((p) => v.P(p))), 'var(--acento-suave)', 'var(--malla)', 3);
      for (const [xi, eta] of PG) { const [x, y] = v.P(mapear(X3, xi, eta)); circulo(g, x, y, 7, 'var(--aviso)', 'var(--fondo)', 1.5); }
      let km = 0; for (const f of e3.ke) for (const x of f) km = Math.max(km, Math.abs(x));
      const c = 15;
      e3.ke.forEach((f, i) => f.forEach((x, j) => rect(g, 1022 + j * c, 212 + i * c, c - 1.5, c - 1.5, 2, Math.abs(x) < 1e-9 ? 'var(--superficie-3)' : 'var(--acento)', 'none', 0, `fill-opacity:${(0.18 + 0.82 * Math.sqrt(Math.abs(x) / km)).toFixed(2)}`)));
      texto(g, 1082, 366, '8 × 8', 'font:700 24px var(--fuente)', 'var(--texto-3)');
    }
    // 5 · ensamblaje: la malla y la matriz global 18 × 18
    {
      const g = minis[4], v = vista(1200, 262, 11);
      elems.forEach((e) => forma(g, poli(e.con.map((i) => v.P(P[i]))), 'var(--acento-suave)', 'var(--malla)', 2));
      // el rótulo va encima de la malla (no sobre la rejilla) y la flecha lleva de la malla a K
      texto(g, 1260, 160, 'cuatro elementos', 'font:650 22px var(--fuente)', 'var(--texto-3)');
      flecha(g, 1262, 272, 1314, 326, 'var(--texto-3)', 2.5, 9);
      const KK = rejillaK(S('g', {}, g), 1322, 286, 18, 6.6, 'var(--acento)');
      elems.forEach((e) => KK.pintar(e.dofs));
      texto(g, 1381, 274, 'K', "italic 700 26px 'KaTeX_Main','Times New Roman',serif", 'var(--texto-2)');
    }
    // 6 · el mismo sistema que el del pórtico
    {
      const g = minis[5];
      const NPm = [[1500, 340], [1500, 250], [1572, 250], [1572, 340]];
      linea(g, abierta(NPm), 'var(--primario)', 7);
      for (const [x, y] of [NPm[0], NPm[3]]) linea(g, `M${x - 14},${y + 2} H${x + 14}`, 'var(--apoyo)', 3);
      texto(g, 1604, 306, '+', 'font:800 34px var(--fuente)', 'var(--texto-3)');
      const v = vista(1622, 340, 8.4);
      const esc6 = 60;
      const Pd = P.map((p, i) => [p[0] + esc6 * C.u[2 * i], p[1] + esc6 * C.u[2 * i + 1]]);
      elems.forEach((e) => forma(g, poli(e.con.map((i) => v.P(P[i]))), 'none', 'var(--texto-3)', 1.4, 'stroke-dasharray:4 4'));
      elems.forEach((e) => forma(g, poli(e.con.map((i) => v.P(Pd[i]))), 'var(--acento-suave)', 'var(--malla)', 2));
      for (const i of apoyos) { const [x, y] = v.P(P[i]); apoyo(g, x, y, 6); }
      { const [x, y] = v.P(Pd[nc]); flecha(g, x, y - 34, x, y - 3, 'var(--carga)', 3.5, 10); }
      flecha(g, 1536, 362, 1580, 412, 'var(--acento)', 3.5, 12);
      flecha(g, 1668, 362, 1624, 412, 'var(--acento)', 3.5, 12);
    }
    const RET3 = [300, 720, 1140, 1560, 1980, 2400];
    function estado3(final) {
      op(gOk, final ? 1 : 0);
      minis.forEach((m) => { op(m, final ? 1 : 0); m.removeAttribute('transform'); });
      flechas3.forEach((f) => { limpiarTrazo(f.l); op(f.g, final ? 1 : 0); });
    }
    function animar3() {
      estado3(false);
      A.tw({ dur: 380, retraso: 220, cada: (e) => op(gOk, e) });
      minis.forEach((m, k) => A.tw({ dur: 420, retraso: RET3[k], cada: (e) => { op(m, e); m.setAttribute('transform', `translate(0,${(14 * (1 - e)).toFixed(1)})`); }, fin: () => m.removeAttribute('transform') }));
      flechas3.forEach((f, k) => { A.tw({ dur: 1, retraso: RET3[k] + 260, fin: () => op(f.g, 1) }); op(f.pt, 0); A.trazar(f.l, { dur: 200, retraso: RET3[k] + 260 }); A.tw({ dur: 120, retraso: RET3[k] + 420, cada: (e) => op(f.pt, e) }); });
    }

    // ------------------------------------------------------------ pasos
    function fijar(p, vivo) {
      A.cancelar();
      estado0(true); estado1(true); estado3(true);
      estado2(vivo && p === 2);
    }
    return {
      entrar(p, o) {
        fijar(p, !o.impresion);
        if (o.instantaneo || o.impresion) return;
        if (p === 0) animar0();
        else if (p === 1) animar1();
        else if (p === 3) animar3();
      },
      paso(k, o) {
        fijar(k, true);
        if (!o.adelante) return;
        if (k === 1) animar1();
        else if (k === 3) animar3();
      },
      salir() { A.cancelar(); if (bucle2) { bucle2.detener(); bucle2 = null; } },
    };
  });

  // ===================================================================== 13 · las nueve etapas
  EF.registrarViz('f13-etapas', function (cont) {
    const A = animador();
    const EG = ejemploGuia();
    const { C, P, elems, apoyos, nc } = EG;
    const e3 = C.elementos[String(C.showcase)];
    const X3 = e3.X;                                    // nodos 4, 5, 8, 7
    const esc = Array.from(cont.querySelectorAll('.f13-esc'));
    const svgEn = (padre, w, h) => { const s = S('svg', { class: 'viz f13-svg', width: w, height: h, viewBox: `0 0 ${w} ${h}` }); padre.insertBefore(s, padre.firstChild); return s; };
    const HALO = 'paint-order:stroke;stroke:var(--fondo);stroke-width:6px;stroke-linejoin:round';
    const FM = (px) => `font:italic 700 ${px}px 'KaTeX_Math','Times New Roman',serif`;
    const NUM = (px) => `font:750 ${px}px var(--fuente);font-variant-numeric:tabular-nums;${HALO}`;
    /** Color de una celda con signo: naranja positivo, azul negativo, intensidad por |v|. */
    const celda = (r, v, vmax) => {
      const t = Math.abs(v) / vmax;
      r.style.fill = t < 1e-6 ? 'var(--superficie-3)' : (v > 0 ? 'var(--acento)' : 'var(--primario)');
      r.style.fillOpacity = t < 1e-6 ? '1' : (0.16 + 0.8 * Math.sqrt(t)).toFixed(3);
    };
    const memBarra = cont.querySelector('.f13-mem-barra');
    const contador = cont.querySelector('.e1-cont');

    // ------------------------------------------------------------ paso 0 · etapas 1 a 3 (geometría)
    const s0 = svgEn(esc[0], 1720, 410);
    // 1 · mapeo: el cuadrado natural se transforma en E3
    const g1 = S('g', {}, s0);
    const SQ = { x: 20, y: 140, t: 170 };
    const aSq = (xi, eta) => [SQ.x + ((xi + 1) / 2) * SQ.t, SQ.y + ((1 - eta) / 2) * SQ.t];
    const vM = vista(300 - 46 * 2, 340 + 46 * 3, 46);
    const aE = (xi, eta) => vM.P(mapear(X3, xi, eta));
    rect(g1, SQ.x, SQ.y, SQ.t, SQ.t, 0, 'var(--primario-suave)', 'var(--linea-2)', 2);
    flecha(g1, SQ.x + SQ.t / 2, SQ.y + SQ.t / 2, SQ.x + SQ.t + 22, SQ.y + SQ.t / 2, 'var(--ejeX)', 2.5, 10);
    flecha(g1, SQ.x + SQ.t / 2, SQ.y + SQ.t / 2, SQ.x + SQ.t / 2, SQ.y - 24, 'var(--ejeY)', 2.5, 10);
    texto(g1, SQ.x + SQ.t + 26, SQ.y + SQ.t / 2 - 10, 'ξ', FM(26), 'var(--ejeX)', 'start');
    texto(g1, SQ.x + SQ.t / 2 + 12, SQ.y - 14, 'η', FM(26), 'var(--ejeY)', 'start');
    [[-1, -1, '1'], [1, -1, '2'], [1, 1, '3'], [-1, 1, '4']].forEach(([xi, eta, t]) => { const [x, y] = aSq(xi, eta); texto(g1, x + (xi < 0 ? -12 : 12), y + (eta < 0 ? 28 : -12), t, 'font:700 22px var(--fuente)', 'var(--texto-3)', xi < 0 ? 'end' : 'start'); });
    flecha(g1, 210, 180, 318, 180, 'var(--texto-3)', 3, 12);   // el mapeo: 48 px por encima del eje ξ, para no leerse con él
    const familia = [];
    for (const v of [-1, -0.5, 0, 0.5, 1]) for (const dir of [0, 1]) {
      familia.push({ v, dir, p: linea(g1, 'M0,0', dir ? 'var(--ejeY)' : 'var(--ejeX)', Math.abs(v) === 1 ? 3 : 1.6, Math.abs(v) === 1 ? '' : 'stroke-opacity:.65') });
    }
    const nodos1 = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(() => circulo(g1, 0, 0, 7, 'var(--fondo)', 'var(--nodo)', 3));
    const etq1 = S('g', {}, g1);
    ['4', '5', '8', '7'].forEach((t, k) => { const [x, y] = vM.P(X3[k]); texto(etq1, x + (k === 0 || k === 3 ? -14 : 14), y + (k < 2 ? 26 : -12), 'nodo ' + t, 'font:700 22px var(--fuente)', 'var(--texto-2)', k === 0 || k === 3 ? 'end' : 'start'); });
    function morph(m) {
      for (const f of familia) {
        const pts = EF.rango(13).map((k) => {
          const u = -1 + k / 6;
          const [xi, eta] = f.dir ? [f.v, u] : [u, f.v];
          const a = aSq(xi, eta), b = aE(xi, eta);
          return [a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m];
        });
        f.p.setAttribute('d', abierta(pts));
      }
      [[-1, -1], [1, -1], [1, 1], [-1, 1]].forEach(([xi, eta], k) => {
        const a = aSq(xi, eta), b = aE(xi, eta);
        nodos1[k].setAttribute('cx', (a[0] + (b[0] - a[0]) * m).toFixed(1));
        nodos1[k].setAttribute('cy', (a[1] + (b[1] - a[1]) * m).toFixed(1));
      });
    }
    // 2 · Jacobiano: det J sobre E3 y su valor en cada punto de Gauss (Anexo G)
    const g2 = S('g', {}, s0);
    const vJ = vista(610 - 50 * 2, 350 + 50 * 3, 50);
    {
      const n = 10, cel = [];
      let dlo = Infinity, dhi = -Infinity;
      for (let a = 0; a < n; a++) for (let b = 0; b < n; b++) {
        const xi0 = -1 + (2 * b) / n, xi1 = xi0 + 2 / n, et0 = -1 + (2 * a) / n, et1 = et0 + 2 / n;
        const d = EF.jacobiano(EF.Q4.dN((xi0 + xi1) / 2, (et0 + et1) / 2), X3).det;
        dlo = Math.min(dlo, d); dhi = Math.max(dhi, d);
        cel.push({ d, pts: [[xi0, et0], [xi1, et0], [xi1, et1], [xi0, et1]] });
      }
      for (const c of cel) forma(g2, poli(c.pts.map(([x, y]) => vJ.P(mapear(X3, x, y)))), 'var(--primario)', 'var(--primario)', 0.6, `fill-opacity:${(0.1 + 0.55 * (c.d - dlo) / (dhi - dlo)).toFixed(3)};stroke-opacity:${(0.1 + 0.55 * (c.d - dlo) / (dhi - dlo)).toFixed(3)}`);
    }
    forma(g2, poli(X3.map((p) => vJ.P(p))), 'none', 'var(--malla)', 3);
    const pg2 = e3.gauss.map((g, k) => {
      const [x, y] = vJ.P(g.x);
      const gg = S('g', {}, g2);
      circulo(gg, x, y, 8, 'var(--aviso)', 'var(--fondo)', 2);
      const dx = g.x[0] < 5 ? -14 : 14;
      texto(gg, x + dx, y + 8, EF.fmt(g.detJ, 4), NUM(22), 'var(--texto)', dx < 0 ? 'end' : 'start');
      return gg;
    });
    // el área de un cuadradito del espacio natural, en el punto de Gauss 1 (a escala)
    const gdA = S('g', {}, g2);
    {
      const J = e3.gauss[0].J;
      const o = [1002, 330];
      rect(gdA, 902, 290, 40, 40, 2, 'var(--primario-suave)', 'var(--primario)', 2.5);
      texto(gdA, 922, 368, 'dξ dη', FM(22), 'var(--texto-2)');
      flecha(gdA, 952, 310, 990, 310, 'var(--texto-3)', 2.5, 10);
      const e1 = [J[0][0] * 40, -J[0][1] * 40], e2 = [J[1][0] * 40, -J[1][1] * 40];
      forma(gdA, poli([o, [o[0] + e1[0], o[1] + e1[1]], [o[0] + e1[0] + e2[0], o[1] + e1[1] + e2[1]], [o[0] + e2[0], o[1] + e2[1]]]), 'var(--primario-suave)', 'var(--primario)', 2.5);
      // dA en el centro del paralelogramo; el factor, debajo de su borde inferior y con halo
      texto(gdA, o[0] + (e1[0] + e2[0]) / 2, o[1] + (e1[1] + e2[1]) / 2 + 8, 'dA', FM(24), 'var(--primario)');
      texto(gdA, o[0] + e1[0] / 2, 368, '× ' + EF.fmt(e3.gauss[0].detJ, 4), NUM(23), 'var(--primario)', 'middle');
    }
    // 3 · matriz B en el punto de Gauss 1: 8 desplazamientos → 3 deformaciones
    const g3 = S('g', {}, s0);
    const B0 = e3.gauss[0].B, eps0 = e3.gauss[0].eps;
    const umax = Math.max(...e3.ue.map(Math.abs)), bmax = Math.max(...B0.flat().map(Math.abs)), emax = Math.max(...eps0.map(Math.abs));
    const cU = e3.ue.map((v, k) => { const r = rect(g3, 1180, 100 + 30 * k, 28, 28, 4); celda(r, v, umax); return r; });
    const cB = B0.map((f, i) => f.map((v, j) => { const r = rect(g3, 1250 + 30 * j, 175 + 30 * i, 28, 28, 4); celda(r, v, bmax); return r; }));
    const cE = eps0.map((v, i) => { const r = rect(g3, 1532, 175 + 30 * i, 28, 28, 4); celda(r, v, emax); return r; });
    texto(g3, 1194, 88, 'u_e', FM(28), 'var(--texto)');
    texto(g3, 1369, 160, 'B', FM(28), 'var(--texto)');
    texto(g3, 1546, 160, 'ε', FM(28), 'var(--texto)');
    const fl3 = [flecha(g3, 1214, 220, 1244, 220, 'var(--texto-3)', 3, 10), flecha(g3, 1494, 220, 1526, 220, 'var(--texto-3)', 3, 10)];
    texto(g3, 1194, 370, '8 valores', 'font:650 22px var(--fuente)', 'var(--texto-3)');
    texto(g3, 1369, 300, '3 × 8', 'font:700 22px var(--fuente)', 'var(--texto-3)');
    texto(g3, 1369, 330, 'en el punto de Gauss 1', 'font:600 22px var(--fuente)', 'var(--texto-3)');
    texto(g3, 1546, 300, '3 valores', 'font:650 22px var(--fuente)', 'var(--texto-3)');
    const pintarB = (fU, fB, fE) => {
      cU.forEach((r, k) => { celda(r, k < fU ? e3.ue[k] : 0, umax); });
      cB.forEach((f, i) => f.forEach((r, j) => celda(r, i < fB ? B0[i][j] : 0, bmax)));
      cE.forEach((r, i) => celda(r, i < fE ? eps0[i] : 0, emax));
    };
    function estado0(final) {
      morph(final ? 1 : 0); op(etq1, final ? 1 : 0);
      op(g2, final ? 1 : 0); for (const p of pg2) op(p, 1); op(gdA, 1);
      pintarB(final ? 8 : 0, final ? 3 : 0, final ? 3 : 0);
      for (const f of fl3) op(f.g, final ? 1 : 0);
    }
    function animar0() {
      estado0(false);
      A.tw({ dur: 1400, retraso: 300, curva: 'ambos', cada: (e) => morph(e) });
      A.tw({ dur: 300, retraso: 1600, cada: (e) => op(etq1, e) });
      A.tw({ dur: 420, retraso: 900, cada: (e) => op(g2, e) });
      for (const p of pg2) op(p, 0);
      pg2.forEach((p, k) => A.tw({ dur: 240, retraso: 1250 + k * 120, cada: (e) => op(p, e) }));
      op(gdA, 0); A.tw({ dur: 400, retraso: 1750, cada: (e) => op(gdA, e) });
      for (let k = 1; k <= 8; k++) A.tw({ dur: 1, retraso: 1900 + k * 55, fin: () => pintarB(k, 0, 0) });
      A.tw({ dur: 1, retraso: 2380, fin: () => op(fl3[0].g, 1) });
      for (let i = 1; i <= 3; i++) A.tw({ dur: 1, retraso: 2400 + i * 150, fin: () => pintarB(8, i, 0) });
      A.tw({ dur: 1, retraso: 2920, fin: () => op(fl3[1].g, 1) });
      for (let i = 1; i <= 3; i++) A.tw({ dur: 1, retraso: 2950 + i * 90, fin: () => pintarB(8, 3, i) });
    }

    // ------------------------------------------------------------ paso 1 · etapas 4 y 5
    const s1 = svgEn(esc[1], 1720, 410);
    const vR = vista(660 - 48 * 2, 350 + 48 * 3, 48);
    forma(s1, poli(X3.map((p) => vR.P(p))), 'var(--acento-suave)', 'var(--malla)', 3);
    for (const p of X3) { const [x, y] = vR.P(p); circulo(s1, x, y, 6, 'var(--fondo)', 'var(--nodo)', 3); }
    const pg5 = e3.gauss.map((g, k) => {
      const [x, y] = vR.P(g.x);
      const gg = S('g', {}, s1);
      const halo = circulo(gg, x, y, 18, 'var(--aviso)', 'none', 0, 'fill-opacity:.25');
      circulo(gg, x, y, 9, 'var(--aviso)', 'var(--fondo)', 2);
      texto(gg, x, y - 16, String(k + 1), NUM(22), 'var(--texto-2)');
      return { gg, halo };
    });
    flecha(s1, 914, 222, 950, 222, 'var(--texto-3)', 3, 11);
    const KE = e3.ke;
    let kmax = 0; for (const f of KE) for (const v of f) kmax = Math.max(kmax, Math.abs(v));
    const cK = KE.map((f, i) => f.map((v, j) => rect(s1, 960 + 32 * j, 90 + 32 * i, 30, 30, 4)));
    const aportes = e3.gauss.map((g) => g.aporte);
    function pintarKe(n, frac) {
      for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) {
        let v = 0;
        for (let g = 0; g < 4; g++) v += aportes[g][i][j] * (g < n ? 1 : g === n ? frac : 0);
        celda(cK[i][j], v, kmax);
      }
    }
    // reglas 2 × 2 (Q4) y 3 × 3 (Q9): el tamaño del punto sigue a su peso
    const gReglas = S('g', {}, s1);
    const r9 = Math.sqrt(0.6), w9 = [5 / 9, 8 / 9, 5 / 9], x9 = [-r9, 0, r9];
    [[1277, [[-G1, -G1, 1], [-G1, G1, 1], [G1, -G1, 1], [G1, G1, 1]]],
      [1493, x9.flatMap((a, i) => x9.map((b, j) => [a, b, w9[i] * w9[j]]))]].forEach(([x0, pts]) => {
      rect(gReglas, x0, 180, 140, 140, 4, 'var(--primario-suave)', 'var(--linea-2)', 2);
      for (const [a, b, w] of pts) circulo(gReglas, x0 + ((a + 1) / 2) * 140, 180 + ((1 - b) / 2) * 140, 5 + 7 * Math.sqrt(w), 'var(--aviso)', 'var(--fondo)', 1.5);
    });
    function estado1(final) {
      pintarKe(final ? 4 : 0, 0);
      pg5.forEach((p) => { op(p.gg, 1); op(p.halo, 0); });
      contador.textContent = final ? 'suma de los 4 aportes' : '';
      op(gReglas, 1);
    }
    function animar1() {
      estado1(false);
      op(gReglas, 0);
      A.tw({ dur: 400, retraso: 300, cada: (e) => op(gReglas, e) });
      for (let g = 0; g < 4; g++) {
        const t = 560 + g * 640;
        A.tw({ dur: 1, retraso: t, fin: () => { contador.textContent = `aporte del punto ${g + 1} de 4`; pg5.forEach((p, k) => op(p.halo, k === g ? 1 : 0)); } });
        A.tw({ dur: 460, retraso: t + 60, curva: 'ambos', cada: (e) => pintarKe(g, e) });
      }
      A.tw({ dur: 1, retraso: 560 + 4 * 640, fin: () => { pintarKe(4, 0); contador.textContent = 'suma de los 4 aportes'; pg5.forEach((p) => op(p.halo, 0)); } });
    }

    // ------------------------------------------------------------ paso 2 · etapas 6 a 8
    const s2 = svgEn(esc[2], 1720, 410);
    // 6 · una carga repartida uniforme q sobre una arista: q L / 2 en cada nodo [2, p. 113]
    const g6 = S('g', {}, s2);
    linea(g6, 'M60,300 H380', 'var(--texto-2)', 6);
    for (const x of [60, 380]) circulo(g6, x, 300, 8, 'var(--fondo)', 'var(--nodo)', 3);
    const gRep = S('g', {}, g6);
    linea(gRep, 'M60,196 H380', 'var(--carga)', 3);
    const repartidas = EF.rango(9).map((k) => { const x = 60 + k * 40; const f = flecha(gRep, x, 198, x, 290, 'var(--carga)', 3, 10); f.x = x; return f; });
    texto(gRep, 40, 206, 'q', FM(30), 'var(--carga)', 'end');
    const nodales = [60, 380].map((x) => { const f = flecha(g6, x, 150, x, 290, 'var(--carga)', 6, 18); const t = texto(f.g, x, 136, 'qL/2', FM(28), 'var(--carga)'); return f; });
    linea(g6, 'M60,340 H380 M60,330 V350 M380,330 V350', 'var(--texto-3)', 2);
    texto(g6, 220, 372, 'L', FM(26), 'var(--texto-3)');
    // 7 · ensamblaje y 8 · restricciones y solución, sobre la malla del ejemplo guía
    const g7 = S('g', {}, s2);
    const vE2 = vista(560, 384, 36);
    const polys7 = elems.map((e) => forma(g7, poli(e.con.map((i) => vE2.P(P[i]))), 'var(--acento-suave)', 'var(--malla)', 3));
    elems.forEach((e) => { const c = e.con.reduce((s, i) => [s[0] + P[i][0] / 4, s[1] + P[i][1] / 4], [0, 0]); const [x, y] = vE2.P(c); texto(g7, x, y + 8, 'E' + e.id, 'font:700 22px var(--fuente)', 'var(--texto-3)'); });
    for (const p of P) { const [x, y] = vE2.P(p); circulo(g7, x, y, 6, 'var(--fondo)', 'var(--nodo)', 3); }
    { const [x, y] = vE2.P(P[nc]); flecha(g7, x, y - 40, x, y - 5, 'var(--carga)', 4.5, 13); }
    const gApo = S('g', {}, g7);
    for (const i of apoyos) { const [x, y] = vE2.P(P[i]); apoyo(gApo, x, y, 10); }
    const KG = rejillaK(S('g', {}, s2), 1040, 66, 18, 17, 'var(--acento)');
    const gRestr = S('g', {}, s2);
    for (const d of C.restringidos) {
      rect(gRestr, 1040, 66 + 17 * d - 0.5, 17 * 18 - 1.5, 17, 0, 'var(--fondo)', 'none', 0, 'fill-opacity:.78');
      rect(gRestr, 1040 + 17 * d - 0.5, 66, 17, 17 * 18 - 1.5, 0, 'var(--fondo)', 'none', 0, 'fill-opacity:.78');
    }
    const escU = 1.1 / Math.max(...C.u.map(Math.abs));
    const Pd = P.map((p, i) => [p[0] + escU * C.u[2 * i], p[1] + escU * C.u[2 * i + 1]]);
    const gDef = S('g', {}, s2);
    elems.forEach((e) => forma(gDef, poli(e.con.map((i) => vE2.P(Pd[i]))), 'var(--acento)', 'var(--acento)', 3, 'fill-opacity:.16'));
    function estado2(final) {
      KG.limpiar();
      if (final) elems.forEach((e) => KG.pintar(e.dofs));
      polys7.forEach((p) => { p.style.fill = 'var(--acento-suave)'; p.style.fillOpacity = ''; });
      op(gRep, final ? 0.14 : 1);
      repartidas.forEach((f) => f.g.removeAttribute('transform'));
      for (const f of nodales) { op(f.g, final ? 1 : 0); }
      op(gApo, final ? 1 : 0); op(gRestr, final ? 1 : 0); op(gDef, final ? 1 : 0);
    }
    function animar2() {
      estado2(false);
      A.tw({
        dur: 800, retraso: 450, curva: 'ambos',
        cada: (e) => {
          op(gRep, 1 - 0.86 * e);
          repartidas.forEach((f) => { const dest = f.x < 220 ? 60 : 380; f.g.setAttribute('transform', `translate(${((dest - f.x) * 0.85 * e).toFixed(1)},0)`); });
          for (const f of nodales) { op(f.g, e); }
        },
      });
      elems.forEach((e, k) => {
        const t = 650 + k * 380;
        A.tw({ dur: 360, retraso: t, cada: (x) => { polys7[k].style.fill = x < 1 ? 'var(--acento)' : 'var(--acento-suave)'; polys7[k].style.fillOpacity = x < 1 ? String(0.25 + 0.35 * Math.sin(Math.PI * x)) : ''; } });
        KG.pintar(e.dofs, A, t + 120);
      });
      A.tw({ dur: 380, retraso: 2150, cada: (e) => { op(gApo, e); op(gRestr, e); } });
      A.tw({ dur: 520, retraso: 2500, cada: (e) => op(gDef, e) });
    }

    // ------------------------------------------------------------ paso 3 · etapa 9
    const s3 = svgEn(esc[3], 1720, 410);
    const sy = (k) => k[1];
    // (a) E3: puntos de Gauss (Tabla G.5) → nodos (Tabla G.6)
    const ga = S('g', {}, s3);
    const vA = vista(110 - 50 * 2, 350 + 50 * 3, 50);   // E3: x 110–360, y 100–350
    forma(ga, poli(X3.map((p) => vA.P(p))), 'var(--acento-suave)', 'var(--malla)', 3);
    const cercano = [0, 2, 3, 1];   // nodo 4 ↔ PG1, nodo 5 ↔ PG3, nodo 8 ↔ PG4, nodo 7 ↔ PG2
    const gPGa = S('g', {}, ga), gFla = S('g', {}, ga), gNoda = S('g', {}, ga);
    // rótulos de los puntos 1 a 4 [dx, dy, ancla]: los de la izquierda, hacia el interior (no sobre el
    // borde izquierdo); el del punto 4, afuera a la derecha (adentro no cabe junto al del punto 2)
    const despPG = [[14, 8, 'start'], [16, 32, 'middle'], [-6, -16, 'middle'], [42, 10, 'start']];
    e3.gauss.forEach((g, k) => {
      const [x, y] = vA.P(g.x);
      circulo(gPGa, x, y, 8, 'var(--aviso)', 'var(--fondo)', 2);
      texto(gPGa, x + despPG[k][0], y + despPG[k][1], EF.fmt(sy(e3.sigma_gauss[k]), 2), NUM(22), 'var(--texto)', despPG[k][2]);
    });
    const flA = X3.map((p, k) => {
      const [x0, y0] = vA.P(e3.gauss[cercano[k]].x), [x1, y1] = vA.P(p);
      const L2 = Math.hypot(x1 - x0, y1 - y0), ux = (x1 - x0) / L2, uy = (y1 - y0) / L2;
      return flecha(gFla, x0 + 12 * ux, y0 + 12 * uy, x1 - 8 * ux, y1 - 8 * uy, 'var(--acento)', 2.5, 10);
    });
    X3.forEach((p, k) => {
      const [x, y] = vA.P(p);
      const der = k === 1 || k === 2;
      const t = texto(gNoda, x + (der ? 16 : -16), y + (k < 2 ? 34 : -16), EF.fmt(sy(e3.sigma_nodal[k]), 2), 'font:800 23px var(--fuente);font-variant-numeric:tabular-nums', 'var(--acento)', der ? 'start' : 'end');
      t.setAttribute('style', t.getAttribute('style') + ';' + HALO);
      circulo(gNoda, x, y, 6, 'var(--acento)', 'var(--fondo)', 2);
    });
    // (b) el nodo 5 recibe un valor desde cada uno de sus cuatro elementos y los promedia (Tabla G.7)
    const gb = S('g', {}, s3);
    const vB = vista(610, 360, 36);
    elems.forEach((e) => forma(gb, poli(e.con.map((i) => vB.P(P[i]))), 'var(--superficie-2)', 'var(--malla)', 2.5));
    const i5 = EG.idx[5];
    const [n5x, n5y] = vB.P(P[i5]);
    const gTags = S('g', {}, gb);
    // de cada elemento llega un valor; la tesis tabula el de E3 (Tabla G.6) y el promedio (Tabla G.7)
    const tags = elems.map((e) => {
      const El = C.elementos[String(e.id)];
      const v = El.sigma_nodal[El.nodos.indexOf(5)][1];
      const c = e.con.reduce((s, i) => [s[0] + P[i][0] / 4, s[1] + P[i][1] / 4], [0, 0]);
      const [cx, cy] = vB.P(c);
      const esE3 = e.id === C.showcase;
      // cada rótulo donde su elemento tiene lugar, lejos del contorno también con Inter (versión
      // oscura): E1 y E2 en su centroide; E3, que lleva además su valor, apenas más allá; E4, angosto
      // arriba, en su parte baja. La flecha nace por debajo del rótulo (ini: fracción hacia el nodo 5)
      let x = cx, y = cy, ini = 0.25;
      if (esE3) { x = cx + (cx - n5x) * 0.1; y = cy + (cy - n5y) * 0.1; ini = 0.4; }
      else if (e.id === 4) { x = cx + 6; y = cy + 34; ini = 0.45; }
      const g = S('g', {}, gTags);
      const fl = flecha(g, x + (n5x - x) * ini, y + (n5y - y) * ini, n5x + (x - n5x) * 0.12, n5y + (y - n5y) * 0.12, 'var(--texto-3)', 2, 8);
      texto(g, x, esE3 ? y - 6 : y + 8, esE3 ? 'E' + e.id : 'desde E' + e.id, 'font:700 22px var(--fuente)', 'var(--texto-3)');
      if (esE3) texto(g, x, y + 20, EF.fmt(v, 2), NUM(22), 'var(--texto)');
      return { g, fl };
    });
    circulo(gb, n5x, n5y, 9, 'var(--ok)', 'var(--fondo)', 2.5);
    // abajo y a la derecha del nodo, dentro de E2: entre la flecha que sube de E2, la que va al
    // promedio y la arista 5–6, sin que lo cruce ninguna línea
    texto(gb, n5x + 24, n5y + 36, 'nodo 5', `font:700 22px var(--fuente);${HALO}`, 'var(--texto-2)', 'start');
    const gProm = S('g', {}, gb);
    rect(gProm, 1018, 196, 116, 70, 10, 'var(--ok-suave)', 'var(--ok)', 2.5);
    texto(gProm, 1076, 222, 'promedio', 'font:700 22px var(--fuente)', 'var(--ok)');
    texto(gProm, 1076, 252, EF.fmt(C.nodal['5'].sy, 2), 'font:800 24px var(--fuente);font-variant-numeric:tabular-nums', 'var(--ok)');
    flecha(gProm, n5x + 14, n5y, 1014, 231, 'var(--ok)', 2.5, 9);
    // (c) el campo de σy promediado, en el post-proceso de EduFEM (paleta jet)
    const gc = S('g', {}, s3);
    const vC = vista(1190, 362, 36);
    const syN = C.nodos.map((n) => C.nodal[String(n.id)].sy);
    const smin = Math.min(...syN), smax = Math.max(...syN);
    for (const e of elems) {
      const X = e.con.map((i) => P[i]), V = e.con.map((i) => syN[i]);
      const n = 10;
      for (let a = 0; a < n; a++) for (let b = 0; b < n; b++) {
        const xi0 = -1 + (2 * b) / n, xi1 = xi0 + 2 / n, et0 = -1 + (2 * a) / n, et1 = et0 + 2 / n;
        const v = EF.interp(EF.Q4.N((xi0 + xi1) / 2, (et0 + et1) / 2), V);
        const col = EF.jetCss((v - smin) / (smax - smin));
        forma(gc, poli([[xi0, et0], [xi1, et0], [xi1, et1], [xi0, et1]].map(([x, y]) => vC.P(mapear(X, x, y)))), col, col, 0.8);
      }
    }
    elems.forEach((e) => forma(gc, poli(e.con.map((i) => vC.P(P[i]))), 'none', 'var(--fondo)', 1.6, 'stroke-opacity:.7'));
    for (let k = 0; k < 28; k++) { const t = k / 27; rect(gc, 1606, 350 - t * 270 - 10, 26, 10.5, 0, EF.jetCss(t)); }
    rect(gc, 1606, 80, 26, 270, 3, 'none', 'var(--linea-2)', 1.5);
    // extremos de la escala: los valores de σy de los nodos 9 y 7 en la Tabla G.7
    [[smax, 86], [smin, 356]].forEach(([v, y]) => texto(gc, 1638, y, EF.fmt(v, 2), 'font:650 22px var(--fuente);font-variant-numeric:tabular-nums', 'var(--texto-2)', 'start'));
    function estado3(final) {
      for (const g of [gPGa, gNoda, gTags, gProm, gc]) op(g, final ? 1 : 0);
      op(gFla, final ? 1 : 0);
      for (const f of flA) limpiarTrazo(f.l);
      memBarra.style.transform = '';
    }
    function animar3() {
      estado3(false);
      A.tw({ dur: 320, retraso: 300, cada: (e) => op(gPGa, e) });
      A.tw({ dur: 1, retraso: 760, fin: () => op(gFla, 1) });
      flA.forEach((f) => { op(f.pt, 0); A.trazar(f.l, { dur: 420, retraso: 760 }); A.tw({ dur: 140, retraso: 1120, cada: (e) => op(f.pt, e) }); });
      A.tw({ dur: 320, retraso: 1250, cada: (e) => op(gNoda, e) });
      A.tw({ dur: 1, retraso: 1550, fin: () => op(gTags, 1) });
      tags.forEach((t, k) => { op(t.g, 0); A.tw({ dur: 260, retraso: 1550 + k * 110, cada: (e) => op(t.g, e) }); });
      A.tw({ dur: 320, retraso: 2050, cada: (e) => op(gProm, e) });
      A.tw({ dur: 520, retraso: 2350, cada: (e) => op(gc, e) });
      memBarra.style.transform = 'scaleX(0)';
      A.tw({ dur: 900, retraso: 2400, curva: 'ambos', cada: (e) => { memBarra.style.transform = `scaleX(${e.toFixed(4)})`; }, fin: () => { memBarra.style.transform = ''; } });
    }

    // ------------------------------------------------------------ pasos
    function fijar() { A.cancelar(); estado0(true); estado1(true); estado2(true); estado3(true); }
    const animar = [animar0, animar1, animar2, animar3];
    return {
      entrar(p, o) {
        fijar();
        if (p === 0 && !o.instantaneo && !o.impresion) animar0();
      },
      paso(k, o) {
        fijar();
        if (o.adelante) animar[k]();
      },
      salir() { A.cancelar(); },
    };
  });
})();
