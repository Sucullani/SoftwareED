/* =====================================================================
   viz/l4_alcance.js — visualizaciones del grupo «alcance» (final4).

   Lámina 04 · alcance  (viz «alc-embudo», data-pasos="3")
     0  objeto de estudio y campo de acción (tarjetas; aquí solo se animan sus ilustraciones)
     1  el embudo del alcance: cada nivel se angosta y lo que queda fuera sale de escena
        hacia la columna «Fuera del alcance», donde se tacha
     2  dentro del dominio, las dos idealizaciones (video y ejemplos; el embudo resalta el dominio)
     3  delimitación en cuatro planos (el embudo resalta el objeto de estudio: el plano disciplinar)
   Lámina 05 · plano  (viz «alc-plano», data-pasos="2")
     0  barra · plano · sólido frente a los conceptos de la formulación
     1  las matrices a escala: D, B y kₑ del Q4 frente a las del hexaedro de ocho nodos,
        que crecen hasta desbordar el tamaño del Q4
     2  el puente: la misma formulación rige el caso tridimensional

   Los textos de lectura están en el HTML de cada lámina (el motor los muestra por paso);
   aquí se dibuja lo gráfico (SVG) y se mueve lo que la lámina anima. Toda animación pasa por
   EF.tween (reloj virtual del video) y todo color es una variable CSS del tema.
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
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
  function circulo(g, x, y, r, relleno, trazo, ancho) {
    return est(S('circle', { cx: x, cy: y, r }, g), { relleno: relleno || 'none', trazo: trazo || 'none', estilo: `stroke-width:${ancho || 0}` });
  }
  function texto(g, x, y, t, estilo, color, ancla) {
    return est(S('text', { x, y, 'text-anchor': ancla || 'middle', text: t }, g), { relleno: color, estilo });
  }
  function punta(g, x2, y2, ux, uy, p, color) {
    const bx = x2 - ux * p, by = y2 - uy * p;
    return forma(g, `M${x2},${y2} L${bx - uy * p * 0.55},${by + ux * p * 0.55} L${bx + uy * p * 0.55},${by - ux * p * 0.55} Z`, color);
  }
  function flecha(g, x1, y1, x2, y2, color, ancho, p) {
    p = p || ancho * 3;
    const L = Math.hypot(x2 - x1, y2 - y1), ux = (x2 - x1) / L, uy = (y2 - y1) / L;
    const gg = S('g', {}, g);
    linea(gg, `M${x1},${y1} L${x2 - ux * p * 0.8},${y2 - uy * p * 0.8}`, color, ancho);
    punta(gg, x2, y2, ux, uy, p, color);
    return gg;
  }
  const poli = (pts) => 'M' + pts.map((p) => `${p[0]},${p[1]}`).join(' L') + ' Z';
  /** Interpolación bilineal en un cuadrilátero Q = [sup-izq, sup-der, inf-der, inf-izq]. */
  function bil(Q, s, t) {
    const a = [Q[0][0] + (Q[1][0] - Q[0][0]) * s, Q[0][1] + (Q[1][1] - Q[0][1]) * s];
    const b = [Q[3][0] + (Q[2][0] - Q[3][0]) * s, Q[3][1] + (Q[2][1] - Q[3][1]) * s];
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  }
  /** Placa con un campo de tensiones esquemático (rojo en el empotramiento, azul en el extremo libre). */
  function contorno(g, Q, nx, ny) {
    const campo = (s, t) => Math.pow(1 - s, 1.15) * (0.32 + 0.68 * Math.abs(1 - 2 * t));
    for (let i = 0; i < nx; i++) {
      for (let j = 0; j < ny; j++) {
        const s0 = i / nx, s1 = (i + 1) / nx, t0 = j / ny, t1 = (j + 1) / ny;
        const c = EF.jetCss(0.06 + 0.9 * campo((s0 + s1) / 2, (t0 + t1) / 2));
        forma(g, poli([bil(Q, s0, t0), bil(Q, s1, t0), bil(Q, s1, t1), bil(Q, s0, t1)]), c, c, 0.9);
      }
    }
  }
  function mallaQ(g, Q, nx, ny, color, ancho) {
    const out = [];
    for (let i = 0; i <= nx; i++) { const a = bil(Q, i / nx, 0), b = bil(Q, i / nx, 1); out.push(linea(g, `M${a[0]},${a[1]} L${b[0]},${b[1]}`, color, ancho)); }
    for (let j = 0; j <= ny; j++) { const a = bil(Q, 0, j / ny), b = bil(Q, 1, j / ny); out.push(linea(g, `M${a[0]},${a[1]} L${b[0]},${b[1]}`, color, ancho)); }
    return out;
  }

  // ------------------------------------------------------------------ íconos
  // Cada ícono dibuja en su propio viewBox (120 × 80 si no se indica otro). Grises los de lo que
  // queda fuera; con el azul del objeto de estudio los ejemplos que quedan dentro; naranja los de
  // la delimitación.
  const GR = 'var(--texto-3)', GRF = 'var(--superficie-3)', TX2 = 'var(--texto-2)';
  const AZ = 'var(--h-neutro)', AZF = 'var(--h-neutro-suave)', NA = 'var(--acento)';
  const VB = { objeto: '0 0 760 250', campo: '0 0 760 250', prohibido: '0 0 32 32', disciplinar: '0 0 100 100', institucional: '0 0 100 100', espacial: '0 0 100 100', temporal: '0 0 100 100' };
  const ICONOS = {
    prohibido(g) {
      circulo(g, 16, 16, 12.5, 'none', 'var(--mal)', 3.6);
      linea(g, 'M7.5,24.5 L24.5,7.5', 'var(--mal)', 3.6);
    },
    portico(g) {
      linea(g, 'M12,68 V20 H54 V68', GR, 5);
      for (const x of [12, 54]) {
        linea(g, `M${x - 9},70 H${x + 9}`, GR, 3);
        linea(g, `M${x - 7},77 l5,-6 M${x - 1},77 l5,-6 M${x + 5},77 l5,-6`, GR, 1.6);
      }
      linea(g, 'M64,60 H116 M77,32 H103 M64,60 L77,32 L90,60 L103,32 L116,60', GR, 3);
      forma(g, 'M64,60 l-6,9 h12 z', 'none', GR, 2.4);
      circulo(g, 116, 65, 4.4, 'none', GR, 2.4);
    },
    placa(g) {
      forma(g, 'M4,58 L38,72 L62,58 L28,44 Z', GRF, GR, 2.6);
      forma(g, 'M64,70 Q82,26 100,70 L116,58 Q98,14 80,58 Z', GRF, GR, 2.6);
      linea(g, 'M82,48 L98,36', GR, 1.6);
    },
    solido(g) {
      const f = [[30, 72], [80, 72], [80, 26], [30, 26]];
      const b = f.map(([x, y]) => [x + 24, y - 18]);
      forma(g, poli(f), GRF, GR, 2.6);
      forma(g, poli([f[3], f[2], b[2], b[3]]), GRF, GR, 2.6);
      forma(g, poli([f[1], b[1], b[2], f[2]]), GRF, GR, 2.6);
      linea(g, `M${b[0][0]},${b[0][1]} L${b[1][0]},${b[1][1]} M${b[0][0]},${b[0][1]} L${b[3][0]},${b[3][1]} M${b[0][0]},${b[0][1]} L${f[0][0]},${f[0][1]}`, GR, 2, 'stroke-dasharray:4 4');
    },
    nolineal(g) {
      linea(g, 'M16,72 V8 M16,72 H112', GR, 2.6);
      linea(g, 'M16,72 L60,16', GR, 2, 'stroke-dasharray:5 5');
      linea(g, 'M16,72 C34,46 50,30 110,24', GR, 4.4);
    },
    dinamica(g) {
      linea(g, 'M6,40 H116', GR, 2);
      linea(g, 'M6,40 C14,2 24,2 32,40 S50,74 58,40 S72,14 80,40 S92,58 98,40 S108,32 114,40', GR, 4);
    },
    triq8(g) {
      const T = [[8, 70], [50, 70], [26, 22]];
      forma(g, poli(T), GRF, GR, 2.6);
      for (const p of T) circulo(g, p[0], p[1], 4.2, 'var(--fondo)', GR, 2.2);
      const Q = [[64, 70], [114, 66], [110, 18], [68, 14]];
      forma(g, poli(Q), GRF, GR, 2.6);
      const medios = Q.map((p, i) => [(p[0] + Q[(i + 1) % 4][0]) / 2, (p[1] + Q[(i + 1) % 4][1]) / 2]);
      for (const p of Q.concat(medios)) circulo(g, p[0], p[1], 4.2, 'var(--fondo)', GR, 2.2);
    },
    mallado(g) {
      forma(g, 'M12,60 C6,36 26,12 56,14 C88,16 112,30 106,54 C100,74 30,80 12,60 Z', GRF, GR, 2.6);
      const P = [[22, 54], [36, 30], [58, 24], [82, 26], [98, 46], [86, 64], [60, 68], [36, 68], [54, 46], [76, 46]];
      const T = [[0, 1, 8], [1, 2, 8], [2, 3, 9], [2, 9, 8], [3, 4, 9], [4, 5, 9], [5, 6, 9], [6, 8, 9], [6, 7, 8], [7, 0, 8]];
      for (const t of T) linea(g, poli(t.map((i) => P[i])), GR, 1.4);
      forma(g, 'M106,0 L109,8 L117,11 L109,14 L106,22 L103,14 L95,11 L103,8 Z', GR);
    },
    ensayo(g) {
      // prensa de ensayo con una probeta cilíndrica (la validación no se hace contra ensayos)
      linea(g, 'M18,76 V6 M102,76 V6', GR, 3.2);
      linea(g, 'M12,6 H108 M12,77 H108', GR, 4.4);
      forma(g, 'M50,6 H70 V15 H50 Z', GR);
      forma(g, 'M38,15 H82 V20 H38 Z', GR);
      forma(g, 'M38,71 H82 V76 H38 Z', GR);
      forma(g, 'M46,23 V68 A14,3.5 0 0 0 74,68 V23 Z', GRF, GR, 2.4);
      est(S('ellipse', { cx: 60, cy: 23, rx: 14, ry: 3.5 }, g), { relleno: GRF, trazo: GR, estilo: 'stroke-width:2.4' });
      linea(g, 'M57,31 L63,41 L56,50 L62,61', GR, 1.8);
    },
    // --- dentro del dominio: ejemplos de ingeniería civil
    viga(g) {
      linea(g, 'M14,4 H106', 'var(--carga)', 2.4);
      for (let k = 0; k < 6; k++) flecha(g, 18 + k * 16.8, 4, 18 + k * 16.8, 17, 'var(--carga)', 2.4, 6);
      forma(g, 'M10,19 H110 V61 H10 Z', AZF, AZ, 2.6);
      forma(g, 'M22,61 l-8,12 h16 z', 'none', 'var(--apoyo)', 2.6);
      forma(g, 'M98,61 l-8,12 h16 z', 'none', 'var(--apoyo)', 2.6);
    },
    muro(g) {
      forma(g, 'M46,8 H80 V66 H46 Z', AZF, AZ, 2.6);
      linea(g, 'M26,66 H100', TX2, 3);
      for (let x = 30; x <= 96; x += 9) linea(g, `M${x},66 l-6,8`, TX2, 1.6);
      flecha(g, 6, 15, 44, 15, 'var(--carga)', 3, 9);
    },
    presa(g) {
      forma(g, 'M2,26 H46 V68 H2 Z', 'var(--cian)', 'none', 0, 'fill-opacity:.28');
      linea(g, 'M2,26 q5.5,-4 11,0 t11,0 t11,0 t11,0', 'var(--cian)', 2.2);
      forma(g, 'M46,68 V10 H60 L110,68 Z', AZF, AZ, 2.6);
      linea(g, 'M0,68 H118', TX2, 3);
    },
    contencion(g) {
      forma(g, 'M68,16 H118 V68 H96 V58 H68 Z', GRF, 'none');
      for (let x = 74; x <= 114; x += 9) for (let y = 22; y <= 52; y += 9) circulo(g, x + ((y / 9) % 2) * 3, y, 1.4, GR);
      linea(g, 'M68,16 H118', TX2, 2);
      forma(g, 'M56,6 H68 V56 H98 V68 H28 V56 H56 Z', AZF, AZ, 2.6);
      linea(g, 'M0,68 H28', TX2, 3);
    },
    tunel(g) {
      forma(g, 'M6,10 H114 V76 H6 Z', GRF);
      linea(g, 'M6,10 H114', TX2, 2.4);
      for (const [x, y] of [[18, 24], [100, 22], [16, 58], [102, 60], [30, 40], [90, 40]]) circulo(g, x, y, 1.6, GR);
      forma(g, 'M38,76 V48 A22,22 0 0 1 82,48 V76 Z', AZF, AZ, 3);
      forma(g, 'M46,76 V49 A14,14 0 0 1 74,49 V76 Z', 'var(--fondo)', AZ, 2);
    },
    // --- delimitación (100 × 100)
    disciplinar(g) {
      const q4 = [[12, 80], [46, 84], [44, 30], [16, 26]];
      forma(g, poli(q4), 'var(--fondo)', NA, 3);
      for (const p of q4) circulo(g, p[0], p[1], 4.5, NA);
      const q9 = [[54, 84], [90, 80], [86, 26], [56, 30]];
      forma(g, poli(q9), 'var(--fondo)', NA, 3);
      for (let i = 0; i <= 2; i++) for (let j = 0; j <= 2; j++) {
        const p = bil([q9[3], q9[2], q9[1], q9[0]], i / 2, j / 2);
        circulo(g, p[0], p[1], 4.2, (i === 1 || j === 1) ? 'var(--fondo)' : NA, NA, 2.4);
      }
    },
    institucional(g) {
      forma(g, 'M10,34 L50,10 L90,34 Z', NA);
      for (const x of [18, 35, 57, 74]) forma(g, `M${x},40 h9 v36 h-9 z`, NA);
      forma(g, 'M12,80 H88 V86 H12 Z', NA);
      forma(g, 'M6,89 H94 V95 H6 Z', NA);
    },
    espacial(g) {
      forma(g, 'M18,20 H82 V64 H18 Z', 'var(--fondo)', NA, 4);
      forma(g, 'M6,74 H94 L86,66 H14 Z', NA);
      forma(g, poli([[34, 56], [64, 54], [62, 30], [38, 33]]), 'none', NA, 2.6);
      for (const p of [[34, 56], [64, 54], [62, 30], [38, 33]]) circulo(g, p[0], p[1], 3, NA);
    },
    temporal(g) {
      forma(g, 'M14,20 H86 V90 H14 Z', 'var(--fondo)', NA, 4);
      forma(g, 'M14,20 H86 V38 H14 Z', NA);
      linea(g, 'M32,10 V26 M68,10 V26', NA, 5);
      texto(g, 50, 75, '2026', 'font:800 25px var(--fuente)', NA);
    },
    // --- paso 0: objeto de estudio (medio continuo → malla → tensiones)
    objeto(g, ref) {
      const capt = ['medio continuo', 'malla de elementos', 'tensiones'];
      ref.paneles = [];
      [0, 268, 536].forEach((x, k) => {
        const gp = S('g', {}, g);
        ref.paneles.push(gp);
        const Q = [[x + 36, 26], [x + 196, 72], [x + 196, 132], [x + 36, 168]];
        linea(gp, `M${x + 30},20 V174`, TX2, 3.4);
        for (let y = 28; y <= 166; y += 14) linea(gp, `M${x + 30},${y} l-11,9`, TX2, 1.8);
        if (k === 2) {
          const gc = S('g', {}, gp);
          contorno(gc, Q, 16, 10);
          mallaQ(gc, Q, 4, 3, 'var(--alc-malla-sobre-campo)', 1.4);
          forma(gp, poli(Q), 'none', TX2, 2.4);
          ref.contorno = gc;
        } else {
          forma(gp, poli(Q), AZF, AZ, 2.8);
          if (k === 1) {
            const gm = S('g', {}, gp);
            mallaQ(gm, Q, 4, 3, 'var(--malla)', 2.2);
            for (let i = 0; i <= 4; i++) for (let j = 0; j <= 3; j++) { const p = bil(Q, i / 4, j / 3); circulo(gm, p[0], p[1], 4.2, 'var(--nodo)'); }
            ref.malla = gm;
          }
        }
        flecha(gp, x + 214, 66, x + 214, 126, 'var(--carga)', 3.4, 11);
        texto(gp, x + 116, 222, capt[k], 'font:650 25px var(--fuente)', TX2);
        if (k < 2) flecha(g, x + 228, 98, x + 270, 98, GR, 3.4, 12);
      });
    },
    // --- paso 0: campo de acción (software educativo + memoria de cálculo)
    campo(g, ref) {
      // computadora portátil con un modelo resuelto en el lienzo
      forma(g, 'M70,12 H378 a12,12 0 0 1 12,12 V178 H58 V24 a12,12 0 0 1 12,-12 Z', 'var(--lienzo)', TX2, 5);
      forma(g, 'M28,198 H420 L396,180 H52 Z', GRF, TX2, 3);
      forma(g, 'M72,30 H136 V166 H72 Z', GRF);
      for (let k = 0; k < 5; k++) linea(g, `M84,${50 + k * 24} H${126 - (k % 2) * 18}`, 'var(--linea-2)', 5);
      const gp = S('g', {}, g);
      const Q = [[166, 44], [362, 82], [362, 128], [166, 158]];
      contorno(gp, Q, 14, 8);
      mallaQ(gp, Q, 4, 2, 'var(--alc-malla-sobre-campo)', 1.3);
      forma(gp, poli(Q), 'none', TX2, 2);
      ref.pantalla = gp;
      texto(g, 224, 236, 'software educativo', 'font:650 25px var(--fuente)', TX2);
      texto(g, 448, 110, '+', 'font:700 46px var(--fuente)', GR);
      // memoria de cálculo: hojas con el desarrollo y una matriz
      const gd = S('g', {}, g);
      forma(gd, 'M506,30 H690 V214 H506 Z', GRF, 'var(--linea-2)', 2);
      forma(gd, 'M478,14 H632 L664,46 V200 H478 Z', 'var(--superficie)', TX2, 3);
      linea(gd, 'M632,14 V46 H664', TX2, 2.4);
      linea(gd, 'M496,40 H600', TX2, 6);
      linea(gd, 'M496,64 H640 M496,80 H618', 'var(--linea-2)', 4);
      linea(gd, 'M504,96 h-8 v58 h8 M612,96 h8 v58 h-8', TX2, 3);
      for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
        est(S('rect', { x: 506 + j * 26, y: 101 + i * 13, width: 22, height: 9, rx: 2 }, gd), { relleno: AZ, estilo: `fill-opacity:${i === j ? 0.85 : 0.4}` });
      }
      linea(gd, 'M496,172 H646 M496,186 H604', 'var(--linea-2)', 4);
      ref.memoria = gd;
      texto(g, 584, 236, 'memoria de cálculo', 'font:650 25px var(--fuente)', TX2);
    },
  };

  /** Dibuja los íconos de una lámina en sus marcadores [data-ico]. */
  function dibujarIconos(raiz) {
    for (const span of raiz.querySelectorAll('[data-ico]')) {
      if (span._ico) continue;
      const nombre = span.getAttribute('data-ico');
      const f = ICONOS[nombre];
      if (!f) { console.warn('Ícono desconocido:', nombre); continue; }
      const svg = S('svg', { viewBox: VB[nombre] || '0 0 120 80', preserveAspectRatio: 'xMidYMid meet' }, span);
      const ref = {};
      f(S('g', {}, svg), ref);
      span._ico = ref;
    }
  }

  /** Registro de las animaciones en curso de una visualización, para cancelarlas al saltar. */
  function animador() {
    const activos = [];
    return {
      tw(o) { const t = EF.tween(o); activos.push(t); return t; },
      trazar(p, o) { const t = EF.trazar(p, o); activos.push(t); return t; },
      cancelar() { for (const t of activos.splice(0)) t.cancelar(false); },
    };
  }
  function limpiarTrazo(p) { p.style.strokeDasharray = ''; p.style.strokeDashoffset = ''; }

  // ===================================================================== 04 · el embudo del alcance
  EF.registrarViz('alc-embudo', function (cont, L) {
    dibujarIconos(L.el);
    const A = animador();
    const W = 1720, H = 772;
    const svg = S('svg', { class: 'viz', width: W, height: H, viewBox: `0 0 ${W} ${H}` });
    cont.insertBefore(svg, cont.firstChild);

    // geometría: un cono de cinco niveles que se angosta de 800 a 400 px, y el pico (EduFEM)
    const CX = 444, Y0 = 16, HB = 104, GB = 12, M0 = 400, M1 = 200;
    const YF = Y0 + 5 * HB + 4 * GB;
    const med = (y) => M0 - ((y - Y0) * (M0 - M1)) / (YF - Y0);
    const PICO = { y0: YF + GB, y1: YF + GB + 120, m: 180 };

    const gRes = S('g', {}, svg);
    const gNiv = S('g', {}, svg);
    const gCon = S('g', {}, svg);
    const rotulos = Array.from(cont.querySelectorAll('.alc-nivel'));
    const niveles = [];
    for (let i = 0; i < 5; i++) {
      const y0 = Y0 + i * (HB + GB), y1 = y0 + HB, a0 = med(y0), a1 = med(y1);
      const g = S('g', {}, gNiv);
      const color = i === 0 ? 'var(--texto-3)' : AZ;
      const p = forma(g, `M${CX - a0},${y0} L${CX + a0},${y0} L${CX + a1},${y1} L${CX - a1},${y1} Z`, color, color, 2.5);
      p.style.fillOpacity = i === 0 ? '0.12' : String(0.1 + 0.055 * (i - 1));
      p.style.strokeOpacity = '0.6';
      const r = rotulos[i];
      const a = Math.min(a0, a1) - 20;
      Object.assign(r.style, { left: `${CX - a}px`, width: `${2 * a}px`, top: `${y0}px`, height: `${HB}px` });
      niveles.push({ g, y0, y1, a0, a1, rot: r });
    }
    {
      const g = S('g', {}, gNiv);
      est(S('rect', { x: CX - PICO.m, y: PICO.y0, width: 2 * PICO.m, height: PICO.y1 - PICO.y0, rx: 22 }, g), { relleno: NA });
      const r = rotulos[5];
      Object.assign(r.style, { left: `${CX - PICO.m + 16}px`, width: `${2 * PICO.m - 32}px`, top: `${PICO.y0}px`, height: `${PICO.y1 - PICO.y0}px` });
      niveles.push({ g, y0: PICO.y0, y1: PICO.y1, a0: PICO.m, a1: PICO.m, rot: r });
    }
    const leyenda = cont.querySelector('.alc-leyenda');

    // lo que sale: cada ítem nace en la pared del embudo, en la unión del nivel que lo contenía
    // (data-desde) con el siguiente, más angosto; lo que deja afuera EduFEM sale de su costado
    const X_FUERA = 880;
    const elsSale = Array.from(cont.querySelectorAll('.alc-sale'));
    const salidas = elsSale.map((el, k) => {
      const top = 62 + k * 80;
      el.style.top = `${top}px`;
      el.style.transformOrigin = 'left center';
      const desde = Number(el.getAttribute('data-desde'));
      const hermanos = elsSale.filter((x) => x.getAttribute('data-desde') === String(desde));
      const j = hermanos.indexOf(el), n = hermanos.length;
      const yb = desde === 5 ? (PICO.y0 + PICO.y1) / 2 : niveles[desde].y1 + GB / 2;
      const yo = yb + (j - (n - 1) / 2) * (n === 2 ? 50 : 34);
      const xo = CX + (desde === 5 ? PICO.m : med(yo)) + 16;
      return { el, cuando: Number(el.getAttribute('data-cuando')), dx: xo - X_FUERA, dy: yo - (top + 38), tacha: el.querySelector('.alc-tacha'), b: el.querySelector('b') };
    });

    // resaltes del dominio (paso 2) y del objeto de estudio (paso 3), con su conector a la escena
    function contornoNiveles(i0, i1, pad) {
      const a = niveles[i0], b = niveles[i1];
      return `M${CX - a.a0 - pad},${a.y0 - pad} L${CX + a.a0 + pad},${a.y0 - pad} L${CX + b.a1 + pad},${b.y1 + pad} L${CX - b.a1 - pad},${b.y1 + pad} Z`;
    }
    function conector(i, yDestino) {
      const nv = niveles[i], y = (nv.y0 + nv.y1) / 2, x = CX + med(y) + 14;
      const g = S('g', {}, gCon);
      circulo(g, x, y, 6, AZ);
      const p = linea(g, `M${x},${y} C${x + 60},${y} ${X_FUERA - 70},${yDestino} ${X_FUERA - 14},${yDestino}`, AZ, 3.5);
      const pt = punta(g, X_FUERA - 4, yDestino, 1, 0, 14, AZ);
      return { g, p, pt };
    }
    const res2 = linea(gRes, contornoNiveles(1, 2, 9), AZ, 3.5, 'stroke-dasharray:12 8');
    const res3 = linea(gRes, contornoNiveles(1, 4, 9), AZ, 3.5, 'stroke-dasharray:12 8');
    const con2 = conector(1, 22);
    const con3 = conector(2, 56 + 82);

    function verConector(c, v) { op(c.g, v); op(c.pt, v); limpiarTrazo(c.p); }
    function estado(p) {
      A.cancelar();
      const v = p >= 1 ? 1 : 0;
      for (const nv of niveles) { op(nv.g, v); nv.g.removeAttribute('transform'); op(nv.rot, v); }
      for (const s of salidas) { s.el.style.transform = ''; op(s.el, v); s.tacha.style.transform = `scaleX(${v})`; s.b.style.color = ''; }
      op(leyenda, v);
      op(res2, p === 2 ? 1 : 0); verConector(con2, p === 2 ? 1 : 0);
      op(res3, p === 3 ? 1 : 0); verConector(con3, p === 3 ? 1 : 0);
    }

    // ---- paso 1: el embudo se arma de arriba abajo y lo que queda fuera sale de escena
    function aparecerNivel(nv, t) {
      const yc = (nv.y0 + nv.y1) / 2;
      A.tw({ dur: 380, retraso: t, cada: (e) => {
        op(nv.g, e);
        nv.g.setAttribute('transform', `translate(${CX},${yc}) scale(${0.55 + 0.45 * e},1) translate(${-CX},${-yc})`);
      }, fin: () => nv.g.removeAttribute('transform') });
      A.tw({ dur: 320, retraso: t + 120, cada: (e) => op(nv.rot, e) });
    }
    function volar(s, t) {
      const el = s.el;
      op(el, 0);
      s.tacha.style.transform = 'scaleX(0)';
      s.b.style.color = 'var(--texto)';
      A.tw({ dur: 160, retraso: t, cada: (e) => { op(el, e); el.style.transform = `translate(${s.dx}px,${s.dy}px) scale(${0.8 + 0.05 * e})`; } });
      A.tw({ dur: 450, retraso: t + 160, curva: 'ambos', cada: (e) => {
        const x = s.dx * (1 - e), y = s.dy * (1 - e) - 26 * Math.sin(Math.PI * e);
        el.style.transform = `translate(${x}px,${y}px) scale(${0.85 + 0.15 * e})`;
      }, fin: () => { el.style.transform = ''; s.b.style.color = ''; } });
      A.tw({ dur: 200, retraso: t + 640, cada: (e) => { s.tacha.style.transform = `scaleX(${e})`; } });
    }
    function construir() {
      estado(1);
      for (const nv of niveles) { op(nv.g, 0); op(nv.rot, 0); }
      for (const s of salidas) op(s.el, 0);
      op(leyenda, 0);
      const t0 = 220, dt = 440;   // 220 ms: el tiempo en que se van las tarjetas del paso 0
      niveles.forEach((nv, i) => aparecerNivel(nv, t0 + i * dt));
      const orden = {};
      for (const s of salidas) {
        const k = (orden[s.cuando] = (orden[s.cuando] || 0) + 1) - 1;
        volar(s, t0 + s.cuando * dt + 40 + k * 150);
      }
      A.tw({ dur: 380, retraso: t0 + 5 * dt + 480, cada: (e) => op(leyenda, e) });
    }
    function resaltar(res, con, t) {
      A.tw({ dur: 400, retraso: t, cada: (e) => op(res, e) });
      op(con.g, 1); op(con.pt, 0);
      A.trazar(con.p, { dur: 650, retraso: t + 150 });
      A.tw({ dur: 200, retraso: t + 760, cada: (e) => op(con.pt, e) });
    }

    // ---- paso 0: las ilustraciones de las tarjetas se arman al entrar
    function ilustraciones() {
      const o = L.el.querySelector('[data-ico="objeto"]')._ico || {};
      const c = L.el.querySelector('[data-ico="campo"]')._ico || {};
      if (o.paneles) o.paneles.forEach((gp, k) => { op(gp, 0); A.tw({ dur: 420, retraso: 350 + k * 380, cada: (e) => op(gp, e) }); });
      if (o.malla) { op(o.malla, 0); A.tw({ dur: 380, retraso: 900, cada: (e) => op(o.malla, e) }); }
      if (c.pantalla) { op(c.pantalla, 0); A.tw({ dur: 500, retraso: 800, cada: (e) => op(c.pantalla, e) }); }
      if (c.memoria) { op(c.memoria, 0); A.tw({ dur: 450, retraso: 1150, cada: (e) => op(c.memoria, e) }); }
    }

    return {
      entrar(p, o) {
        estado(p);
        if (p === 0 && !o.instantaneo && !o.impresion) ilustraciones();
      },
      paso(k, o) {
        if (o.adelante && k === 1) { construir(); return; }
        if (o.adelante && k === 2) { estado(1); resaltar(res2, con2, 260); return; }
        if (o.adelante && k === 3) {
          estado(2);
          A.tw({ dur: 220, cada: (e) => { op(res2, 1 - e); op(con2.g, 1 - e); op(con2.pt, 1 - e); } });
          resaltar(res3, con3, 260);
          return;
        }
        estado(k);
      },
      salir() { A.cancelar(); },
    };
  });

  // ===================================================================== 05 · ¿por qué el plano?
  EF.registrarViz('alc-plano', function (cont, L) {
    dibujarIconos(L.el);
    const A = animador();
    const W = 1720, H = 772;
    const svg = S('svg', { class: 'viz', width: W, height: H, viewBox: `0 0 ${W} ${H}` });
    cont.insertBefore(svg, cont.firstChild);

    // ---------------------------------------------------------------- paso 0 · los tres elementos
    // barra (1D): dos nodos, carga axial, una sola dirección
    const gBarra = S('g', {}, svg);
    const BY = 284;
    forma(gBarra, `M566,${BY - 10} H774 V${BY + 10} H566 Z`, AZF, AZ, 3);
    circulo(gBarra, 566, BY, 11, 'var(--fondo)', 'var(--nodo)', 4);
    circulo(gBarra, 774, BY, 11, 'var(--fondo)', 'var(--nodo)', 4);
    flecha(gBarra, 550, BY, 494, BY, 'var(--carga)', 4.5, 15);
    flecha(gBarra, 790, BY, 846, BY, 'var(--carga)', 4.5, 15);
    flecha(gBarra, 566, 344, 792, 344, GR, 2.6, 11);
    texto(gBarra, 808, 352, 'x', 'font:italic 600 26px var(--fuente)', GR, 'start');

    // plano (2D): el cuadrado natural se transforma en el elemento real (E3 del ejemplo guía)
    const gPlano = S('g', {}, svg);
    const gRef = S('g', {}, gPlano);
    const RQ = [[938, 360], [1022, 360], [1022, 276], [938, 276]];          // (ξ, η) = (−1,−1), (1,−1), (1,1), (−1,1)
    const E3 = [[2, 3], [7, 4], [7, 8], [5, 8]];
    const PQ = E3.map(([x, y]) => [1090 + (x - 2) * 36, 404 - (y - 3) * 36]);
    const XI = [-1, 1, 1, -1], ETA = [-1, -1, 1, 1];
    const mapa = (Q, xi, eta) => {
      let x = 0, y = 0;
      for (let i = 0; i < 4; i++) { const N = 0.25 * (1 + xi * XI[i]) * (1 + eta * ETA[i]); x += N * Q[i][0]; y += N * Q[i][1]; }
      return [x, y];
    };
    function dibujarQ(g, Q, conLineas) {
      if (conLineas) {
        for (const c of [-0.5, 0, 0.5]) {
          const a = mapa(Q, c, -1), b = mapa(Q, c, 1);
          linea(g, `M${a[0]},${a[1]} L${b[0]},${b[1]}`, 'var(--ejeX)', 1.8, 'stroke-opacity:.75');
          const d = mapa(Q, -1, c), f = mapa(Q, 1, c);
          linea(g, `M${d[0]},${d[1]} L${f[0]},${f[1]}`, 'var(--ejeY)', 1.8, 'stroke-opacity:.75');
        }
        const gp = 1 / Math.sqrt(3);
        for (const [a, b] of [[-gp, -gp], [gp, -gp], [gp, gp], [-gp, gp]]) { const p = mapa(Q, a, b); circulo(g, p[0], p[1], 6, NA); }
      }
    }
    forma(gRef, poli(RQ), 'var(--superficie)', TX2, 2.6);
    dibujarQ(gRef, RQ, true);
    for (const p of RQ) circulo(gRef, p[0], p[1], 6, 'var(--fondo)', 'var(--nodo)', 3);
    texto(gRef, 980, 394, 'ξ', 'font:italic 700 26px var(--fuente)', 'var(--ejeX)');
    texto(gRef, 922, 326, 'η', 'font:italic 700 26px var(--fuente)', 'var(--ejeY)');
    flecha(gRef, 1030, 318, 1080, 318, TX2, 3.4, 13);
    texto(gRef, 1055, 302, 'x(ξ, η)', 'font:italic 600 23px var(--fuente)', TX2);
    // el elemento real viaja al título del paso 1
    const gQ4mov = S('g', {}, gPlano);
    const gQ4det = S('g', {}, gQ4mov);
    const gQ4base = S('g', {}, gQ4mov);
    forma(gQ4det, poli(PQ), AZF, 'none');
    dibujarQ(gQ4det, PQ, true);
    forma(gQ4base, poli(PQ), 'none', AZ, 3.6);
    for (const p of PQ) circulo(gQ4base, p[0], p[1], 7.5, 'var(--fondo)', 'var(--nodo)', 3.4);

    // sólido (3D): hexaedro de ocho nodos con sus 2 × 2 × 2 puntos de Gauss
    const gSol = S('g', {}, svg);
    const gHexMov = S('g', {}, gSol);
    const gHexDet = S('g', {}, gHexMov);
    const gHex = S('g', {}, gHexMov);
    const F = [[1415, 410], [1575, 410], [1575, 250], [1415, 250]];
    const B = [[1487, 352], [1647, 352], [1652, 186], [1487, 192]];
    forma(gHex, poli([F[3], F[2], B[2], B[3]]), 'var(--texto-3)', 'none', 0, 'fill-opacity:.16');
    forma(gHex, poli([F[1], B[1], B[2], F[2]]), 'var(--texto-3)', 'none', 0, 'fill-opacity:.24');
    forma(gHex, poli(F), 'var(--texto-3)', 'none', 0, 'fill-opacity:.09');
    linea(gHex, `M${B[0][0]},${B[0][1]} L${B[1][0]},${B[1][1]} M${B[0][0]},${B[0][1]} L${B[3][0]},${B[3][1]} M${B[0][0]},${B[0][1]} L${F[0][0]},${F[0][1]}`, TX2, 2.4, 'stroke-dasharray:7 6');
    linea(gHex, poli(F) + ` M${F[3][0]},${F[3][1]} L${B[3][0]},${B[3][1]} L${B[2][0]},${B[2][1]} L${F[2][0]},${F[2][1]} M${F[1][0]},${F[1][1]} L${B[1][0]},${B[1][1]} L${B[2][0]},${B[2][1]}`, TX2, 3.4);
    // puntos de Gauss: interpolación trilineal en las ocho esquinas (ξ izq→der, η abajo→arriba, ζ frente→fondo)
    const V8 = [[F[0], -1, -1, -1], [F[1], 1, -1, -1], [F[2], 1, 1, -1], [F[3], -1, 1, -1], [B[0], -1, -1, 1], [B[1], 1, -1, 1], [B[2], 1, 1, 1], [B[3], -1, 1, 1]];
    const g3 = 1 / Math.sqrt(3);
    for (const z of [g3, -g3]) for (const yv of [-g3, g3]) for (const xv of [-g3, g3]) {
      let x = 0, y = 0;
      for (const [P, a, b, c] of V8) { const N = 0.125 * (1 + xv * a) * (1 + yv * b) * (1 + z * c); x += N * P[0]; y += N * P[1]; }
      circulo(gHexDet, x, y, 5.5, NA).style.opacity = z > 0 ? '0.5' : '1';
    }
    for (const [P] of V8) circulo(gHex, P[0], P[1], 7, 'var(--fondo)', 'var(--nodo)', 3.2).style.opacity = (P === B[0]) ? '0.55' : '1';

    // a dónde viajan los dos elementos en el paso 1 (íconos junto al título de cada bloque)
    const kq = 68 / 180;
    const T_Q4 = { k: kq, tx: 2 - 1090 * kq, ty: -2 - 224 * kq };
    const kh = 66 / 224;
    const T_HEX = { k: kh, tx: 604 - 1415 * kh, ty: -1 - 186 * kh };
    function mover(g, T, e) {
      g.setAttribute('transform', e ? `translate(${T.tx * e},${T.ty * e}) scale(${1 + (T.k - 1) * e})` : '');
    }

    // ---------------------------------------------------------------- paso 1 · las matrices a escala
    const s = 18;   // una celda = un término; la misma escala para las seis matrices
    const gMat = S('g', {}, svg);
    const PAT = {
      D2: (i, j) => (i < 2 && j < 2) || (i === 2 && j === 2),
      B2: (i, j) => (i === 0 ? j % 2 === 0 : i === 1 ? j % 2 === 1 : true),
      D3: (i, j) => (i < 3 && j < 3) || i === j,
      B3: (i, j) => { const d = j % 3; return [d === 0, d === 1, d === 2, d !== 2, d !== 0, d !== 1][i]; },
      K: () => true,
    };
    function rejilla(clave, x0, y0, nf, nc, patron, color) {
      const g = S('g', {}, gMat);
      const cuadrada = nf === nc;
      const celdas = [];
      for (let i = 0; i < nf; i++) {
        for (let j = 0; j < nc; j++) {
          const nz = patron(i, j);
          const r = S('rect', { x: x0 + j * s + 1.5, y: y0 + i * s + 1.5, width: s - 3, height: s - 3, rx: 2.5 }, g);
          est(r, { relleno: nz ? color : 'var(--superficie-3)', estilo: nz ? `fill-opacity:${cuadrada && i === j ? 1 : cuadrada ? 0.58 : 0.78}` : '' });
          celdas.push({ r, i, j });
        }
      }
      const cor = linea(g, '', TX2, 3);
      const etq = cont.querySelector(`.pla-mat[data-m="${clave}"] span`);
      const R = {
        g, nf, nc, celdas, etq, final: etq ? etq.textContent : '',
        mostrar(mf, mc, ff, fc) {
          ff = ff == null ? mf : ff; fc = fc == null ? mc : fc;
          for (const c of celdas) c.r.style.display = c.i < mf && c.j < mc ? '' : 'none';
          const w = fc * s, h = ff * s;
          cor.setAttribute('d', `M${x0 + 6},${y0 - 5} H${x0 - 5} V${y0 + h + 5} H${x0 + 6} M${x0 + w - 6},${y0 - 5} H${x0 + w + 5} V${y0 + h + 5} H${x0 + w - 6}`);
        },
        revelarHasta(k) { celdas.forEach((c, n) => { c.r.style.display = n < k ? '' : 'none'; }); },
      };
      R.mostrar(nf, nc);
      return R;
    }
    const M = {
      qD: rejilla('qD', 0, 136, 3, 3, PAT.D2, NA),
      qB: rejilla('qB', 130, 136, 3, 8, PAT.B2, NA),
      qK: rejilla('qK', 310, 136, 8, 8, PAT.K, NA),
      sD: rejilla('sD', 600, 136, 6, 6, PAT.D3, TX2),
      sB: rejilla('sB', 730, 136, 6, 24, PAT.B3, TX2),
      sK: rejilla('sK', 1212, 136, 24, 24, PAT.K, TX2),
    };
    // el tamaño del Q4 (8 × 8) dibujado sobre la rigidez del hexaedro: lo que sobra, desborda
    const fantasma = est(S('rect', { x: 1209, y: 133, width: 8 * s + 6, height: 8 * s + 6, rx: 4 }, svg), { relleno: 'none', trazo: NA, estilo: 'stroke-width:4;stroke-dasharray:10 7' });
    const flechaMal = flecha(svg, 1150, 343, 1202, 343, 'var(--mal)', 4, 15);

    // ---------------------------------------------------------------- paso 2 · el puente
    const gPuente = S('g', {}, svg);
    const arco = linea(gPuente, 'M548,764 Q860,616 1172,764', TX2, 5);
    const montantes = [];
    for (let x = 600; x <= 1120; x += 65) {
      const t = (x - 548) / 624, y = 764 - 296 * t * (1 - t);
      montantes.push(linea(gPuente, `M${x},678 V${y}`, GR, 3));
    }
    const tablero = linea(gPuente, 'M520,676 H1200', NA, 8);

    // ---------------------------------------------------------------- estados
    function restaurarEtiquetas() { for (const R of Object.values(M)) if (R.etq) R.etq.textContent = R.final; }
    function estado(p) {
      A.cancelar();
      const v0 = p === 0 ? 1 : 0, v1 = p >= 1 ? 1 : 0;
      op(gBarra, v0); op(gRef, v0); op(gQ4det, v0); op(gHexDet, v0);
      op(gQ4mov, 1); op(gHexMov, 1);
      mover(gQ4mov, T_Q4, v1); mover(gHexMov, T_HEX, v1);
      for (const R of Object.values(M)) { op(R.g, v1); R.mostrar(R.nf, R.nc); }
      restaurarEtiquetas();
      op(fantasma, v1); op(flechaMal, v1);
      op(gPuente, p >= 2 ? 1 : 0);
      limpiarTrazo(arco); limpiarTrazo(tablero);
      for (const m of montantes) op(m, 1);
    }

    // paso 0 al entrar: los elementos aparecen y después las marcas, columna por columna
    function entrada0() {
      estado(0);
      const grupos = [[gBarra, 250], [gRef, 520], [gQ4mov, 820], [gHexMov, 1120]];
      for (const [g, t] of grupos) { op(g, 0); A.tw({ dur: 420, retraso: t, cada: (e) => op(g, e) }); }
      const marcas = Array.from(cont.querySelectorAll('.pla-marca:not(.chica)'));
      marcas.forEach((m, k) => {
        op(m, 0);
        A.tw({ dur: 260, retraso: 1500 + k * 85, curva: 'rebote', cada: (e) => {
          m.style.opacity = String(Math.min(1, e * 1.6));
          m.style.transform = `scale(${0.4 + 0.6 * e})`;
        }, fin: () => { m.style.transform = ''; } });
      });
    }

    // paso 1: los elementos viajan a los títulos; las matrices del Q4 se llenan y las del hexaedro
    // crecen desde el tamaño de las del Q4 hasta el suyo
    function aPaso1() {
      estado(0);
      for (const R of Object.values(M)) op(R.g, 0);
      op(fantasma, 0); op(flechaMal, 0);
      A.tw({ dur: 260, cada: (e) => { op(gBarra, 1 - e); op(gRef, 1 - e); op(gQ4det, 1 - e); op(gHexDet, 1 - e); } });
      A.tw({ dur: 700, retraso: 80, curva: 'ambos', cada: (e) => { mover(gQ4mov, T_Q4, e); mover(gHexMov, T_HEX, e); } });
      const llenar = (R, t, dur) => {
        R.revelarHasta(0);
        A.tw({ dur: 10, retraso: t, fin: () => op(R.g, 1) });
        A.tw({ dur, retraso: t, curva: 'lineal', cada: (e) => R.revelarHasta(Math.ceil(e * R.celdas.length)) });
      };
      llenar(M.qD, 650, 200); llenar(M.qB, 850, 240); llenar(M.qK, 1050, 340);
      const crecer = (R, f0, c0, t, dur) => {
        R.mostrar(f0, c0);
        if (R.etq) R.etq.textContent = `${f0} × ${c0}`;
        A.tw({ dur: 10, retraso: t, fin: () => op(R.g, 1) });
        A.tw({ dur, retraso: t + 60, curva: 'ambos', cada: (e) => {
          const ff = f0 + (R.nf - f0) * e, fc = c0 + (R.nc - c0) * e;
          const mf = Math.round(ff), mc = Math.round(fc);
          R.mostrar(mf, mc, ff, fc);
          if (R.etq) R.etq.textContent = `${mf} × ${mc}`;
        }, fin: () => { if (R.etq) R.etq.textContent = R.final; } });
      };
      crecer(M.sD, 3, 3, 1350, 1380); crecer(M.sB, 3, 8, 1350, 1380); crecer(M.sK, 8, 8, 1350, 1380);
      A.tw({ dur: 300, retraso: 1350, cada: (e) => op(fantasma, e) });
      A.tw({ dur: 300, retraso: 2800, cada: (e) => op(flechaMal, e) });
    }

    // paso 2: se tiende el puente
    function aPaso2() {
      estado(1);
      op(gPuente, 1);
      for (const m of montantes) op(m, 0);
      A.trazar(arco, { dur: 900, retraso: 150 });
      montantes.forEach((m, k) => A.tw({ dur: 220, retraso: 700 + k * 60, cada: (e) => op(m, e) }));
      A.trazar(tablero, { dur: 700, retraso: 400 });
    }

    return {
      entrar(p, o) {
        if (p === 0 && !o.instantaneo && !o.impresion) entrada0();
        else estado(p);
      },
      paso(k, o) {
        if (o.adelante && k === 1) { aPaso1(); return; }
        if (o.adelante && k === 2) { aPaso2(); return; }
        estado(k);
      },
      salir() { A.cancelar(); },
    };
  });
})();
