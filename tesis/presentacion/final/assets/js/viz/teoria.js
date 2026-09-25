/* =====================================================================
   viz/teoria.js — animaciones del bloque «Base teórica».
   Los números salen de EDUFEM_DATOS (motor de EduFEM); lo que se calcula
   en vivo al arrastrar un nodo usa las mismas fórmulas (se rotula así).
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const DAT = () => window.EDUFEM_DATOS;
  const est = (e, o) => EF.estiloSvg(e, o);
  const S = EF.svg;

  // Elemento E3 del ejemplo canónico (el de mayor energía, el del Anexo G)
  function elementoE3() {
    const C = DAT().canonico;
    const e = C.elementos[String(C.showcase)];
    return { C, e, id: C.showcase, X: e.X, nodos: e.nodos };
  }

  // ================================================================== pórtico -> continuo
  EF.registrarViz('portico', function (cont) {
    const W = 1720, H = 500;
    const s = S('svg', { class: 'viz', width: W, height: H, viewBox: `0 0 ${W} ${H}` }, cont);
    // --- panel izquierdo: pórtico
    const gP = S('g', {}, s);
    est(S('text', { x: 0, y: 34, text: 'Pórtico: rigidez de cada barra en forma cerrada' }, gP), { relleno: 'var(--texto-2)', estilo: 'font:750 28px var(--fuente)' });
    const N = [[80, 440], [80, 150], [470, 150], [470, 440]];
    const barras = [[0, 1], [1, 2], [2, 3]];
    const bEls = barras.map(([a, b]) => { const l = S('line', { x1: N[a][0], y1: N[a][1], x2: N[b][0], y2: N[b][1] }, gP); est(l, { trazo: 'var(--primario)', estilo: 'stroke-width:12;stroke-linecap:round' }); return l; });
    const etqB = ['k₁', 'k₂', 'k₃'].map((t, k) => { const [a, b] = barras[k]; const tx = S('text', { x: (N[a][0] + N[b][0]) / 2 + (k === 1 ? 0 : k === 0 ? -44 : 26), y: (N[a][1] + N[b][1]) / 2 + (k === 1 ? -22 : 8), 'text-anchor': 'middle', text: t }, gP); est(tx, { relleno: 'var(--primario)', estilo: 'font:800 30px var(--fuente)' }); return tx; });
    for (const n of N) est(S('circle', { cx: n[0], cy: n[1], r: 10 }, gP), { relleno: 'var(--fondo)', trazo: 'var(--nodo)', estilo: 'stroke-width:4' });
    for (const n of [N[0], N[3]]) est(S('path', { d: `M${n[0]},${n[1]} l-22,30 h44 z` }, gP), { relleno: 'none', trazo: 'var(--apoyo)', estilo: 'stroke-width:4' });
    // matriz global 12x12
    function grilla(g, x0, y0, n, c) {
      const celdas = [];
      for (let i = 0; i < n; i++) { celdas.push([]); for (let j = 0; j < n; j++) { const r = S('rect', { x: x0 + j * c, y: y0 + i * c, width: c - 1.5, height: c - 1.5, rx: 2 }, g); est(r, { relleno: 'var(--superficie-3)' }); celdas[i].push(r); } }
      return celdas;
    }
    est(S('text', { x: 600, y: 118, text: 'K del pórtico' }, gP), { relleno: 'var(--texto-3)', estilo: 'font:700 22px var(--fuente)' });
    const KP = grilla(gP, 560, 136, 12, 17);
    // --- panel derecho: chapa
    const gC = S('g', { transform: 'translate(900,0)' }, s);
    est(S('text', { x: 0, y: 34, text: 'Chapa: la rigidez sale de integrar sobre el área' }, gC), { relleno: 'var(--texto-2)', estilo: 'font:750 28px var(--fuente)' });
    const P = (i, j) => { // malla 3x2 sobre un trapecio
      const t = i / 3, v = j / 2;
      const xb = 20 + t * 420, xt = 60 + t * 330;
      const x = xb + (xt - xb) * v, y = 440 - v * (290 - 40 * t);
      return [x, y];
    };
    const elemsC = [];
    for (let j = 0; j < 2; j++) for (let i = 0; i < 3; i++) elemsC.push([[i, j], [i + 1, j], [i + 1, j + 1], [i, j + 1]]);
    const polys = elemsC.map((q) => { const p = S('path', { d: 'M' + q.map(([i, j]) => P(i, j).join(',')).join('L') + 'Z' }, gC); est(p, { relleno: 'var(--acento-suave)', trazo: 'var(--malla)', estilo: 'stroke-width:3' }); return p; });
    const gpC = S('g', {}, gC);
    est(S('text', { x: 590, y: 118, text: 'K de la chapa' }, gC), { relleno: 'var(--texto-3)', estilo: 'font:700 22px var(--fuente)' });
    const KC = grilla(gC, 560, 136, 24, 8.5);
    const formula = EF.el('div', { class: 'ec-chica', style: 'position:absolute;left:900px;top:452px;width:540px;text-align:left;color:var(--texto)' });
    EF.katex(formula, '\\mathbf{k}_e=\\int_{\\Omega_e}\\mathbf{B}^T\\mathbf{D}\\,\\mathbf{B}\\,t\\,dA', false);
    cont.appendChild(formula);
    formula.style.opacity = '0';

    function limpiarK(K) { for (const f of K) for (const r of f) { r.style.fill = 'var(--superficie-3)'; r.style.opacity = '1'; } }
    function pintarBloque(K, dofs, color, alfa) {
      for (const a of dofs) for (const b of dofs) { const r = K[a][b]; r.style.fill = color; r.__n = (r.__n || 0) + 1; r.style.opacity = String(Math.min(1, 0.35 + 0.28 * r.__n) * alfa); }
    }
    const dofsBarra = [[0, 1, 2, 3, 4, 5], [3, 4, 5, 6, 7, 8], [6, 7, 8, 9, 10, 11]];
    const idN = (i, j) => j * 4 + i;
    const dofsElemC = elemsC.map((q) => q.flatMap(([i, j]) => [2 * idN(i, j), 2 * idN(i, j) + 1]));
    function estadoPortico(completo) {
      limpiarK(KP); for (const f of KP) for (const r of f) r.__n = 0;
      bEls.forEach((b) => { b.style.opacity = '1'; b.style.strokeDasharray = ''; });
      if (completo) dofsBarra.forEach((d) => pintarBloque(KP, d, 'var(--primario)', 1));
    }
    function estadoChapa(completo) {
      limpiarK(KC); for (const f of KC) for (const r of f) r.__n = 0;
      gC.style.opacity = completo === null ? '0.18' : '1';
      formula.style.opacity = completo ? '1' : '0';
      gpC.innerHTML = '';
      if (completo) dofsElemC.forEach((d) => pintarBloque(KC, d, 'var(--acento)', 1));
    }
    function animarPortico() {
      estadoPortico(false);
      bEls.forEach((b, k) => EF.trazar(b, { dur: 600, retraso: k * 350 }));
      dofsBarra.forEach((d, k) => EF.tween({ dur: 450, retraso: 1300 + k * 650, cada: () => {}, fin: () => { pintarBloque(KP, d, 'var(--primario)', 1); bEls.forEach((b, j) => est(b, { trazo: j === k ? 'var(--acento)' : 'var(--primario)', estilo: 'stroke-width:12;stroke-linecap:round' })); } }));
      EF.tween({ dur: 10, retraso: 3400, fin: () => bEls.forEach((b) => est(b, { trazo: 'var(--primario)', estilo: 'stroke-width:12;stroke-linecap:round' })) });
    }
    function animarChapa() {
      estadoChapa(false);
      gC.style.opacity = '1';
      EF.tween({ dur: 600, cada: (e) => { formula.style.opacity = String(e); } });
      elemsC.forEach((q, k) => {
        EF.tween({ dur: 400, retraso: 500 + k * 520, fin: () => {
          polys.forEach((p, j) => est(p, { relleno: j === k ? 'var(--acento)' : 'var(--acento-suave)', trazo: 'var(--malla)', estilo: `stroke-width:3;fill-opacity:${j === k ? 0.55 : 1}` }));
          gpC.innerHTML = '';
          const g = 1 / Math.sqrt(3);
          for (const [xi, eta] of [[-g, -g], [g, -g], [g, g], [-g, g]]) {
            const Nv = EF.Q4.N(xi, eta);
            const pts = q.map(([i, j]) => P(i, j));
            const x = EF.interp(Nv, pts.map((p) => p[0])), y = EF.interp(Nv, pts.map((p) => p[1]));
            est(S('circle', { cx: x, cy: y, r: 6 }, gpC), { relleno: 'var(--aviso)' });
          }
          pintarBloque(KC, dofsElemC[k], 'var(--acento)', 1);
        } });
      });
      EF.tween({ dur: 10, retraso: 500 + elemsC.length * 520 + 300, fin: () => { polys.forEach((p) => est(p, { relleno: 'var(--acento-suave)', trazo: 'var(--malla)', estilo: 'stroke-width:3' })); gpC.innerHTML = ''; } });
    }
    return {
      entrar(p, op) {
        if (op.instantaneo || op.impresion) { estadoPortico(true); estadoChapa(p >= 1 ? true : null); return; }
        animarPortico();
        estadoChapa(p >= 1 ? true : null);
      },
      paso(k, op) {
        if (k === 1 && op.adelante) animarChapa();
        else if (k === 0) estadoChapa(null);
        else estadoChapa(true);
      },
    };
  });

  // ================================================================== nueve etapas
  EF.registrarViz('procedimiento', function (cont, L) {
    const E = EF.ETAPAS;
    const simbolos = ['N', 'J', 'B', 'D', 'k<sub>e</sub>', 'f', 'K', 'u', 'σ'];
    const capturas = ['fig_modulo_m1', 'fig_modulo_m2', 'fig_modulo_m3', 'fig_modulo_m4', 'fig_modulo_m5', 'fig_modulo_m6', 'fig_modulo_m7', 'fig_postproceso', 'fig_postproceso'];
    const fila = EF.el('div', { class: 'proc9' });
    const tarjetas = E.map((et, k) => {
      const t = EF.el('div', { class: 'etapa', 'data-entrada': String(k + 1), 'data-retraso': String(120 + k * 90) }, [
        EF.el('div', { class: 'n', text: String(et.n) }),
        EF.el('div', { class: 's', html: `<b style="font-family:KaTeX_Math,serif;font-style:italic;font-size:40px">${simbolos[k]}</b>` }),
        EF.el('div', { class: 't', text: et.t }),
        EF.el('div', { class: 'inst', 'data-paso': '1', 'data-retraso': String(k * 70) }, [
          et.mod ? EF.el('span', { class: 'm', text: 'Módulo ' + et.mod }) : EF.el('span', { class: 'po', text: 'Post-proceso' }),
          EF.el('span', { class: 'me', text: 'Memoria' }),
        ]),
      ]);
      t.addEventListener('click', () => seleccionar(k, true));
      fila.appendChild(t);
      return t;
    });
    cont.appendChild(fila);
    const det = EF.el('div', { class: 'detalle-etapa', style: 'margin-top:30px', 'data-paso': '2' });
    const izq = EF.el('div', { class: 'tarjeta', style: 'min-height:390px' });
    const tit = EF.el('h3', { style: 'font-size:40px;margin:0 0 6px' });
    const sec = EF.el('div', { class: 'etq', style: 'color:var(--acento);margin-bottom:18px' });
    const ec = EF.el('div', { class: 'ec', style: 'margin:12px 0 18px;font-size:44px' });
    const donde = EF.el('div', { class: 'aux' });
    izq.append(sec, tit, ec, donde);
    const der = EF.el('div', { class: 'figura zoomable', style: 'height:390px;background:#212529' });
    const img = EF.el('img', { class: 'zoomable', alt: '', style: 'width:100%;height:100%;object-fit:contain' });
    der.appendChild(img);
    det.append(izq, der);
    cont.appendChild(det);
    let sel = -1, recorrido = null;
    function seleccionar(k, usuario) {
      if (usuario && recorrido) { recorrido.cancelar(); recorrido = null; }
      sel = k;
      tarjetas.forEach((t, j) => t.classList.toggle('sel', j === k));
      const et = E[k];
      sec.textContent = `Etapa ${et.n} · marco teórico ${et.sec}`;
      tit.textContent = et.t;
      EF.katex(ec, et.tex, true);
      donde.innerHTML = et.mod
        ? `<b>Módulo educativo ${et.mod}</b> sobre el elemento que el usuario selecciona · <b>memoria</b>: capítulo «${et.mem}».`
        : `Sin módulo propio: <b>post-proceso</b> (sonda cruda y suavizada, vista 3D, tabla) y <b>memoria</b>: capítulo «${et.mem}».`;
      img.src = `assets/img/${capturas[k]}.png`;
      img.alt = et.mod ? `Módulo ${et.mod} de EduFEM (captura de la aplicación)` : 'Post-proceso de EduFEM (captura de la aplicación)';
    }
    function recorrer() {
      if (recorrido) recorrido.cancelar();
      let k = 0;
      seleccionar(0);
      recorrido = EF.tween({ dur: 9 * 1400, curva: 'lineal', cada: (e) => { const j = Math.min(8, Math.floor(e * 9)); if (j !== k) { k = j; seleccionar(j); } } });
    }
    return {
      entrar(p, op) {
        if (p >= 2) { if (op.instantaneo || op.impresion) seleccionar(8); else recorrer(); }
        else tarjetas.forEach((t) => t.classList.remove('sel'));
      },
      paso(k, op) { if (k === 2 && op.adelante) recorrer(); else if (k < 2) { if (recorrido) recorrido.cancelar(); tarjetas.forEach((t) => t.classList.remove('sel')); } else seleccionar(sel < 0 ? 8 : sel); },
      salir() { if (recorrido) { recorrido.cancelar(); recorrido = null; } },
    };
  });

  // ================================================================== superficie 3D de una función de forma
  function superficie3D(lz, fn, op) {
    const c = lz.ctx;
    const n = op.n || 22;
    const th = op.giro;
    const cx = lz.W / 2, cy = op.centroY || lz.H * 0.66, esc = op.escala || 130, escZ = op.escalaZ || 170;
    // vista axonométrica: giro alrededor del eje vertical y base inclinada
    const proy = (x, y, z) => {
      const xr = x * Math.cos(th) - y * Math.sin(th);
      const yr = x * Math.sin(th) + y * Math.cos(th);
      return [cx + esc * xr, cy - escZ * z - esc * yr * 0.5, yr];
    };
    const quads = [];
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      const x0 = -1 + (2 * i) / n, x1 = -1 + (2 * (i + 1)) / n, y0 = -1 + (2 * j) / n, y1 = -1 + (2 * (j + 1)) / n;
      const zs = [fn(x0, y0), fn(x1, y0), fn(x1, y1), fn(x0, y1)];
      const pts = [proy(x0, y0, zs[0]), proy(x1, y0, zs[1]), proy(x1, y1, zs[2]), proy(x0, y1, zs[3])];
      const prof = (pts[0][2] + pts[1][2] + pts[2][2] + pts[3][2]) / 4;
      // normal aproximada para sombrear
      const dzx = (zs[1] - zs[0] + zs[2] - zs[3]) / 2, dzy = (zs[3] - zs[0] + zs[2] - zs[1]) / 2;
      const luz = EF.clamp(0.72 + 0.9 * (-dzx * 0.5 + dzy * 0.35), 0.45, 1.15);
      quads.push({ pts, prof, z: (zs[0] + zs[1] + zs[2] + zs[3]) / 4, luz });
    }
    // pintor: primero lo más lejano (yr grande = más al fondo)
    quads.sort((a, b) => b.prof - a.prof);
    // base
    c.save();
    c.strokeStyle = EF.css('--linea-2'); c.lineWidth = 1.5; c.setLineDash([6, 6]);
    const base = [proy(-1, -1, 0), proy(1, -1, 0), proy(1, 1, 0), proy(-1, 1, 0)];
    c.beginPath(); base.forEach((p, k) => (k ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]))); c.closePath(); c.stroke();
    c.setLineDash([]);
    for (const q of quads) {
      const t = EF.clamp((q.z - (op.zmin || 0)) / ((op.zmax || 1) - (op.zmin || 0)), 0, 1);
      const col = EF.jet(t).map((v) => Math.round(EF.clamp(v * q.luz, 0, 255)));
      c.fillStyle = `rgb(${col[0]},${col[1]},${col[2]})`;
      c.strokeStyle = 'rgba(0,0,0,.28)'; c.lineWidth = 0.7;
      c.beginPath(); q.pts.forEach((p, k) => (k ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]))); c.closePath(); c.fill(); c.stroke();
    }
    // nodos de la base
    for (const [k, [a, b]] of (op.nodosNat || []).entries()) {
      const p = proy(a, b, fn(a, b));
      const q = proy(a, b, 0);
      c.strokeStyle = EF.css('--texto-3'); c.lineWidth = 1.2; c.setLineDash([3, 4]);
      c.beginPath(); c.moveTo(q[0], q[1]); c.lineTo(p[0], p[1]); c.stroke(); c.setLineDash([]);
      c.beginPath(); c.arc(q[0], q[1], k === op.activo ? 9 : 6, 0, 2 * Math.PI);
      c.fillStyle = k === op.activo ? EF.css('--acento') : EF.css('--nodo'); c.fill();
    }
    c.restore();
  }

  // ================================================================== mapeo isoparamétrico
  EF.registrarViz('iso', function (cont) {
    const { X } = elementoE3();
    const W = 1720, H = 640;
    const cv = EF.el('div', { style: `position:absolute;left:0;top:0;width:${W}px;height:560px` });
    cont.appendChild(cv);
    const lz = new EF.LienzoMEF(cv, W, 560);
    const lzF = new EF.LienzoMEF(EF.el('div', { style: 'position:absolute;left:1250px;top:0;width:470px;height:560px' }), 470, 560);
    cont.appendChild(lzF.canvas.parentNode);
    lzF.canvas.parentNode.setAttribute('data-paso', '1');
    // controles
    const barra = EF.el('div', { class: 'grupo-botones solo-vivo', style: 'position:absolute;left:0;top:578px' });
    const segTipo = EF.el('div', { class: 'segmentado' });
    const bQ4 = EF.el('button', { class: 'sel', text: 'Q4' }), bQ9 = EF.el('button', { text: 'Q9' });
    segTipo.append(bQ4, bQ9);
    const segN = EF.el('div', { class: 'segmentado naranja' });
    const bRest = EF.el('button', { class: 'boton fantasma', text: '↺ Restablecer', style: 'padding:12px 20px;font-size:24px' });
    barra.append(segTipo, segN, bRest, EF.el('span', { class: 'mini', text: 'Arrastre los nodos del elemento real' }));
    cont.appendChild(barra);
    const leyendas = EF.el('div', { style: 'position:absolute;left:0;top:500px;width:1250px;display:flex;justify-content:space-around;font:650 24px var(--fuente);color:var(--texto-3)' },
      [EF.el('span', { text: 'Cuadrado natural (ξ, η) ∈ [−1, 1]²' }), EF.el('span', { text: 'Elemento real: E3 del ejemplo canónico' })]);
    cont.appendChild(leyendas);
    const flechaTxt = EF.el('div', { class: 'ec-chica', style: 'position:absolute;left:470px;top:196px;width:300px;text-align:center' });
    EF.katex(flechaTxt, 'x=\\sum_i N_i(\\xi,\\eta)\\,x_i', true);
    cont.appendChild(flechaTxt);
    const props = EF.el('div', { 'data-paso': '2', style: 'position:absolute;left:1250px;top:578px;width:470px;display:flex;gap:12px;flex-wrap:wrap' });
    const p1 = EF.el('span', { class: 'ficha ok', style: 'font-size:22px' }); EF.katex(p1, 'N_i(\\xi_j,\\eta_j)=\\delta_{ij}');
    const p2 = EF.el('span', { class: 'ficha ok', style: 'font-size:22px' }); EF.katex(p2, '\\textstyle\\sum_i N_i=1');
    props.append(p1, p2);
    cont.appendChild(props);

    let tipo = 4, activo = 0, giro = 0.6, morph = 1, bucle = null;
    let Xe = X.map((p) => p.slice());
    const X9 = () => {
      // Q9 recto: nodos medios en el punto medio y centro en el baricentro (orden del motor)
      const m = (a, b) => [(Xe[a][0] + Xe[b][0]) / 2, (Xe[a][1] + Xe[b][1]) / 2];
      const c = [(Xe[0][0] + Xe[1][0] + Xe[2][0] + Xe[3][0]) / 4, (Xe[0][1] + Xe[1][1] + Xe[2][1] + Xe[3][1]) / 4];
      return [...Xe, m(0, 1), m(1, 2), m(2, 3), m(3, 0), c];
    };
    let medios = null; // desplazamientos de nodos medios (Q9) al arrastrar
    function coords() {
      if (tipo === 4) return Xe;
      const b = X9();
      if (medios) for (let k = 4; k < 9; k++) { b[k][0] += medios[k][0]; b[k][1] += medios[k][1]; }
      return b;
    }
    // vistas: cuadrado a la izquierda, elemento a la derecha
    const VA = { x0: 70, y0: 70, t: 380 };  // cuadrado natural: 380 px de lado
    const aA = (xi, eta) => [VA.x0 + ((xi + 1) / 2) * VA.t, VA.y0 + ((1 - eta) / 2) * VA.t];
    function vistaElemento() { lz.encuadrar(1.2, 7.8, 2.4, 8.6, { s: 50, d: 520 + 0, i: 90, iz: 780 }); }
    const aC = (x, y) => [lz.X(x), lz.Y(y)];
    function mapeo(xi, eta) {
      const fam = EF.formas(tipo);
      const Nv = fam.N(xi, eta);
      const P = coords();
      let x = 0, y = 0;
      for (let k = 0; k < Nv.length; k++) { x += Nv[k] * P[k][0]; y += Nv[k] * P[k][1]; }
      return [x, y];
    }
    function dibujar() {
      vistaElemento();
      const c = lz.inicio(null);
      const nG = 8;
      const colX = EF.css('--ejeX'), colY = EF.css('--ejeY');
      // cuadrado natural
      c.save();
      c.fillStyle = EF.rgba(EF.css('--primario'), 0.06);
      c.fillRect(VA.x0, VA.y0, VA.t, VA.t);
      c.strokeStyle = EF.css('--linea-2'); c.lineWidth = 2; c.strokeRect(VA.x0, VA.y0, VA.t, VA.t);
      c.restore();
      // líneas coordenadas: interpolación entre cuadrado y elemento según morph
      const lerpP = (xi, eta, m) => {
        const a = aA(xi, eta), b = aC(...mapeo(xi, eta));
        return [a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m];
      };
      const familia = (m, alfa) => {
        for (let k = 0; k <= nG; k++) {
          const v = -1 + (2 * k) / nG;
          for (const [col, dir] of [[colX, 0], [colY, 1]]) {
            c.beginPath();
            for (let s = 0; s <= 24; s++) {
              const u = -1 + (2 * s) / 24;
              const [xi, eta] = dir === 0 ? [u, v] : [v, u];
              const p = lerpP(xi, eta, m);
              s ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]);
            }
            c.strokeStyle = col; c.globalAlpha = alfa * (k === 0 || k === nG ? 1 : 0.55); c.lineWidth = k === 0 || k === nG ? 3 : 1.6; c.stroke();
          }
        }
        c.globalAlpha = 1;
      };
      familia(0, 1);
      if (morph > 0) familia(morph, 1);
      // nodos
      const fam = EF.formas(tipo);
      fam.nat.forEach(([xi, eta], k) => {
        const a = aA(xi, eta);
        c.beginPath(); c.arc(a[0], a[1], k === activo ? 12 : 9, 0, 2 * Math.PI);
        c.fillStyle = k === activo ? EF.css('--acento') : EF.css('--lienzo'); c.fill();
        c.lineWidth = 3; c.strokeStyle = k === activo ? EF.css('--acento') : EF.css('--nodo'); c.stroke();
        c.font = `700 22px ${EF.fuente()}`; c.fillStyle = EF.css('--texto-2'); c.textAlign = 'center';
        c.fillText(String(k + 1), a[0] + (xi < 0 ? -26 : xi > 0 ? 26 : 0), a[1] + (eta < 0 ? 34 : eta > 0 ? -18 : 6));
      });
      if (morph >= 1) {
        const P = coords();
        const nombres = [4, 5, 8, 7];
        P.forEach((p, k) => {
          const q = aC(p[0], p[1]);
          c.beginPath(); c.arc(q[0], q[1], k === activo ? 12 : 9, 0, 2 * Math.PI);
          c.fillStyle = k === activo ? EF.css('--acento') : EF.css('--lienzo'); c.fill();
          c.lineWidth = 3; c.strokeStyle = k === activo ? EF.css('--acento') : EF.css('--nodo'); c.stroke();
          if (k < 4) { c.font = `700 22px ${EF.fuente()}`; c.fillStyle = EF.css('--texto-2'); c.textAlign = 'left'; c.fillText(`${k + 1} (nodo ${nombres[k]})`, q[0] + 14, q[1] - 14); }
        });
      }
      // ejes ξ, η
      c.font = `800 26px ${EF.fuente()}`; c.fillStyle = colX; c.textAlign = 'left'; c.fillText('ξ', VA.x0 + VA.t + 14, VA.y0 + VA.t / 2 + 8);
      c.fillStyle = colY; c.fillText('η', VA.x0 + VA.t / 2 - 8, VA.y0 - 16);
      // flecha central
      c.strokeStyle = EF.css('--texto-3'); c.lineWidth = 3;
      c.beginPath(); c.moveTo(500, 300); c.lineTo(720, 300); c.stroke();
      c.beginPath(); c.moveTo(720, 300); c.lineTo(704, 290); c.lineTo(704, 310); c.closePath(); c.fillStyle = EF.css('--texto-3'); c.fill();
    }
    function dibujarForma() {
      lzF.redimensionar();
      const c = lzF.inicio(null);
      const fam = EF.formas(tipo);
      superficie3D(lzF, (x, y) => fam.N(x, y)[activo], { giro, escala: 118, escalaZ: 190, centroY: 430, zmin: tipo === 9 ? -0.15 : 0, zmax: 1, nodosNat: fam.nat, activo });
      c.font = `750 32px ${EF.fuente()}`; c.fillStyle = EF.css('--texto'); c.textAlign = 'center';
      c.fillText(`N${activo + 1}(ξ, η)`, 235, 40);
      c.font = `600 20px ${EF.fuente()}`; c.fillStyle = EF.css('--texto-3');
      c.fillText(tipo === 4 ? 'vale 1 en su nodo y 0 en los demás' : 'bicuadrática (Lagrange 3 × 3)', 235, 72);
    }
    function botonesN() {
      segN.innerHTML = '';
      for (let k = 0; k < tipo; k++) {
        const b = EF.el('button', { class: k === activo ? 'sel' : '', text: 'N' + (k + 1) });
        b.onclick = () => { activo = k; botonesN(); dibujar(); dibujarForma(); };
        segN.appendChild(b);
      }
    }
    bQ4.onclick = () => { tipo = 4; activo = Math.min(activo, 3); bQ4.classList.add('sel'); bQ9.classList.remove('sel'); botonesN(); dibujar(); dibujarForma(); };
    bQ9.onclick = () => { tipo = 9; medios = null; bQ9.classList.add('sel'); bQ4.classList.remove('sel'); botonesN(); dibujar(); dibujarForma(); };
    bRest.onclick = () => { Xe = X.map((p) => p.slice()); medios = null; dibujar(); };
    // arrastre de nodos del elemento real (en vivo)
    let arrastre = -1;
    lz.canvas.addEventListener('pointerdown', (ev) => {
      const q = EF.aLocal(lz.canvas, ev.clientX, ev.clientY);
      const P = coords();
      let mejor = -1, dmin = 26;
      P.forEach((p, k) => { const s = aC(p[0], p[1]); const d = Math.hypot(s[0] - q.x, s[1] - q.y); if (d < dmin) { dmin = d; mejor = k; } });
      if (mejor >= 0) { arrastre = mejor; activo = mejor < tipo ? mejor : activo; lz.canvas.setPointerCapture(ev.pointerId); botonesN(); }
    });
    lz.canvas.addEventListener('pointermove', (ev) => {
      if (arrastre < 0) return;
      const q = EF.aLocal(lz.canvas, ev.clientX, ev.clientY);
      const [x, y] = lz.aMundo(q.x, q.y);
      if (arrastre < 4) Xe[arrastre] = [x, y];
      else { const b = X9(); medios = medios || b.map(() => [0, 0]); medios[arrastre] = [x - b[arrastre][0], y - b[arrastre][1]]; }
      dibujar(); dibujarForma();
    });
    lz.canvas.addEventListener('pointerup', () => { arrastre = -1; });
    botonesN();
    return {
      entrar(p, op) {
        lz.redimensionar();
        Xe = X.map((q) => q.slice());
        if (op.instantaneo || op.impresion) { morph = 1; dibujar(); dibujarForma(); }
        else { morph = 0; dibujar(); EF.tween({ dur: 1800, retraso: 500, curva: 'ambos', cada: (e) => { morph = e; dibujar(); } }); }
        dibujarForma();
        if (bucle) bucle.detener();
        if (!op.impresion && p >= 1) bucle = EF.bucle((s) => { giro = 0.6 + 0.35 * Math.sin(s * 0.7); dibujarForma(); });
      },
      paso(k) {
        if (k >= 1 && !bucle) bucle = EF.bucle((s) => { giro = 0.6 + 0.35 * Math.sin(s * 0.7); dibujarForma(); });
        if (k === 1) {
          // recorrido por las cuatro funciones de forma
          EF.tween({ dur: 4 * 1500, curva: 'lineal', cada: (e) => { const j = Math.min(3, Math.floor(e * 4)); if (j !== activo) { activo = j; botonesN(); dibujar(); dibujarForma(); } } });
        }
      },
      salir() { if (bucle) { bucle.detener(); bucle = null; } },
      redimensionar() { if (lz.redimensionar()) dibujar(); dibujarForma(); },
      tema() { dibujar(); dibujarForma(); },
    };
  });

  // ================================================================== Jacobiano y B con números reales
  EF.registrarViz('jacobiano', function (cont) {
    const { e, id, X } = elementoE3();
    const W = 1720, H = 660;
    const caja = EF.el('div', { style: 'position:absolute;left:0;top:0;width:700px;height:620px;border-radius:18px;overflow:hidden;border:1px solid var(--linea-2);background:var(--lienzo)' });
    cont.appendChild(caja);
    const lz = new EF.LienzoMEF(caja, 700, 620);
    const panel = EF.el('div', { class: 'panel-mat', style: 'position:absolute;left:740px;top:0;width:980px;height:620px;overflow:hidden' });
    cont.appendChild(panel);
    const barra = EF.el('div', { class: 'segmentado solo-vivo', style: 'position:absolute;right:0;top:-174px' });
    const bF = EF.el('button', { text: 'ƒ Fórmula' }), bV = EF.el('button', { class: 'sel', text: '123 Valores' });
    barra.append(bF, bV);
    cont.appendChild(barra);
    let modo = 'valores', paso = 0, Xa = X.map((p) => p.slice()), anim = null;
    const g0 = e.gauss[0];
    function calcular(Xv) {
      const pts = DAT().canonico.gauss_pts;
      return pts.map(([xi, eta]) => { const dN = EF.Q4.dN(xi, eta); const j = EF.jacobiano(dN, Xv); return { xi, eta, dN, ...j, B: EF.matB(dN, j.inv) }; });
    }
    const mat = (M, dec) => '\\begin{bmatrix}' + M.map((f) => f.map((v) => EF.tex(v, dec)).join('&')).join('\\\\') + '\\end{bmatrix}';
    function escribirPanel(vivo) {
      const r = vivo ? calcular(Xa)[0] : { dN: g0.dN, J: g0.J, det: g0.detJ, inv: g0.invJ, B: g0.B };
      const dNf = vivo ? [[0, 0, 0, 0], [0, 0, 0, 0]].map((f, a) => f.map((_, i) => r.inv[a][0] * r.dN[0][i] + r.inv[a][1] * r.dN[1][i])) : g0.dNf;
      const Xv = vivo ? Xa : X;
      let h = '';
      const bloque = (tex, etq) => `<div style="margin:6px 0 14px"><div class="etq" style="margin-bottom:4px">${etq}</div><div class="k" data-t="${encodeURIComponent(tex)}"></div></div>`;
      if (modo === 'formula' || paso === 0) {
        h += bloque('\\mathbf{J}=\\frac{\\partial\\mathbf{N}}{\\partial(\\xi,\\eta)}\\,\\mathbf{X}_e=\\begin{bmatrix}\\partial x/\\partial\\xi&\\partial y/\\partial\\xi\\\\\\partial x/\\partial\\eta&\\partial y/\\partial\\eta\\end{bmatrix}', 'Jacobiano (convención de Bathe, la del motor)');
        h += bloque('\\det\\mathbf{J}=J_{11}J_{22}-J_{12}J_{21}\\qquad dx\\,dy=|\\det\\mathbf{J}|\\,d\\xi\\,d\\eta', 'Factor local de cambio de área');
        h += bloque('\\begin{bmatrix}\\partial N_i/\\partial x\\\\\\partial N_i/\\partial y\\end{bmatrix}=\\mathbf{J}^{-1}\\begin{bmatrix}\\partial N_i/\\partial\\xi\\\\\\partial N_i/\\partial\\eta\\end{bmatrix}\\;\\Rightarrow\\;\\boldsymbol{\\varepsilon}=\\mathbf{B}\\,\\mathbf{u}_e', 'Regla de la cadena y matriz B');
      } else {
        const et = vivo ? 'cálculo en vivo con las mismas fórmulas' : `E${id}, punto de Gauss 1 (−1/√3, −1/√3) · valores del motor`;
        h += `<div class="etq" style="color:var(--acento)">${et}</div>`;
        if (paso === 1 || paso === 3) {
          h += bloque(`\\frac{\\partial\\mathbf{N}}{\\partial(\\xi,\\eta)}=${mat(r.dN, 4)}\\quad\\mathbf{X}_e=${mat(Xv, 2)}`, 'Derivadas naturales y coordenadas (nodos 4, 5, 8, 7)');
          h += bloque(`\\mathbf{J}=${mat(r.J, 4)}\\qquad\\det\\mathbf{J}=${EF.tex(r.det, 4)}`, r.det > 0 ? 'Jacobiano y su determinante' : '<span style="color:var(--mal)">det J ≤ 0: elemento inválido, el motor lo rechaza</span>');
        } else {
          h += bloque(`\\mathbf{J}^{-1}=\\frac{1}{\\det\\mathbf{J}}\\begin{bmatrix}J_{22}&-J_{12}\\\\-J_{21}&J_{11}\\end{bmatrix}=${mat(r.inv, 4)}`, 'Inversa por cofactores');
          h += bloque(`\\frac{\\partial\\mathbf{N}}{\\partial(x,y)}=\\mathbf{J}^{-1}\\frac{\\partial\\mathbf{N}}{\\partial(\\xi,\\eta)}=${mat(dNf, 4)}`, 'Derivadas físicas (regla de la cadena)');
          h += `<div class="etq" style="margin-bottom:4px">Matriz B (3 × 8) en el punto de Gauss 1</div><div class="k chica" data-t="${encodeURIComponent('\\mathbf{B}=' + mat(r.B, 3))}"></div>`;
        }
      }
      panel.innerHTML = h;
      for (const k of panel.querySelectorAll('.k')) EF.katex(k, decodeURIComponent(k.getAttribute('data-t')), true);
      const formula = modo === 'formula' || paso === 0;
      bF.classList.toggle('sel', formula); bV.classList.toggle('sel', !formula);
    }
    function dibujar(vivo) {
      lz.redimensionar();
      const Xv = vivo ? Xa : X;
      lz.encuadrar(1.2, 8.2, 2.2, 8.9, 50);
      lz.inicio(EF.css('--lienzo'));
      // campo de det J sobre una submalla 12x12 del elemento
      const n = 12, nod = [], val = [], el = [];
      for (let a = 0; a <= n; a++) for (let b = 0; b <= n; b++) {
        const xi = -1 + (2 * b) / n, eta = -1 + (2 * a) / n;
        const Nv = EF.Q4.N(xi, eta);
        nod.push([EF.interp(Nv, Xv.map((p) => p[0])), EF.interp(Nv, Xv.map((p) => p[1]))]);
        val.push(EF.jacobiano(EF.Q4.dN(xi, eta), Xv).det);
      }
      for (let a = 0; a < n; a++) for (let b = 0; b < n; b++) { const k = a * (n + 1) + b; el.push([k, k + 1, k + n + 2, k + n + 1]); }
      const vmax = 7;
      lz.campo(nod, el, val.map((v) => Math.max(v, 0)), { min: 0, max: vmax, sub: 1 });
      // zonas con det J <= 0 en rojo sólido
      const neg = el.filter((q) => q.some((k) => val[k] <= 0));
      if (neg.length) lz.rellenoElementos(nod, neg, neg.map(() => 0), { color: () => 'rgba(255,40,40,.85)' });
      lz.elemento(Xv, [0, 1, 2, 3], { color: EF.css('--texto'), ancho: 3 });
      const nombres = [4, 5, 8, 7];
      Xv.forEach((p, k) => { lz.nodos([p], [0], { radio: 8 }); lz.etiqueta(p[0], p[1], 'nodo ' + nombres[k], { dx: k === 0 || k === 3 ? -14 : 14, dy: k < 2 ? 26 : -24, ancla: k === 0 || k === 3 ? 'right' : 'left', tam: 21, color: EF.css('--texto-2') }); });
      // puntos de Gauss
      calcular(Xv).forEach((g, k) => {
        const Nv = EF.Q4.N(g.xi, g.eta);
        const x = EF.interp(Nv, Xv.map((p) => p[0])), y = EF.interp(Nv, Xv.map((p) => p[1]));
        const c = lz.ctx;
        c.beginPath(); c.arc(lz.X(x), lz.Y(y), k === 0 ? 11 : 8, 0, 2 * Math.PI);
        c.fillStyle = g.det > 0 ? '#ffd23f' : '#ff2d2d'; c.fill(); c.lineWidth = 3; c.strokeStyle = '#1a1a1a'; c.stroke();
        lz.etiqueta(x, y, `PG${k + 1}: ${EF.fmt(g.det, 3)}`, { dx: 0, dy: k === 0 ? 30 : -24, ancla: 'center', tam: 20, color: '#111', fondo: '#fff', alfaFondo: 0.85 });
      });
      lz.etiqueta(1.4, 8.75, 'det J sobre el elemento E3', { tam: 22, color: EF.css('--texto-2') });
    }
    function distorsion() {
      if (anim) anim.cancelar();
      const orig = X[2].slice(), dest = [3.0, 3.6];
      anim = EF.tween({
        dur: 7000, curva: 'lineal',
        cada: (e) => {
          const t = e < 0.45 ? EF.suave.ambos(e / 0.45) : e < 0.7 ? 1 : EF.suave.ambos(1 - (e - 0.7) / 0.3);
          Xa = X.map((p) => p.slice());
          Xa[2] = [orig[0] + (dest[0] - orig[0]) * t, orig[1] + (dest[1] - orig[1]) * t];
          dibujar(true); escribirPanel(true);
        },
        fin: () => { Xa = X.map((p) => p.slice()); dibujar(false); escribirPanel(false); },
      });
    }
    bF.onclick = () => { modo = 'formula'; bF.classList.add('sel'); bV.classList.remove('sel'); escribirPanel(false); };
    bV.onclick = () => { modo = 'valores'; bV.classList.add('sel'); bF.classList.remove('sel'); escribirPanel(false); };
    return {
      entrar(p, op) { paso = p; modo = 'valores'; dibujar(false); escribirPanel(false); if (p === 3 && !op.impresion && !op.instantaneo) distorsion(); },
      paso(k, op) { paso = k; if (anim && k !== 3) { anim.cancelar(); anim = null; Xa = X.map((q) => q.slice()); } dibujar(false); escribirPanel(false); if (k === 3 && op.adelante) distorsion(); },
      salir() { if (anim) { anim.cancelar(); anim = null; } },
      redimensionar() { dibujar(false); },
      tema() { dibujar(false); },
    };
  });

  // ================================================================== cuadratura de Gauss y modos espurios
  EF.registrarViz('gauss', function (cont) {
    const { e, id } = elementoE3();
    const G = DAT().gauss;
    const ec = EF.el('div', { class: 'ec-chica', style: 'position:absolute;left:0;top:0;width:1720px' });
    EF.katex(ec, '\\mathbf{k}_e=\\int_{-1}^{1}\\!\\!\\int_{-1}^{1}\\mathbf{B}^T\\mathbf{D}\\,\\mathbf{B}\\,t\\,|\\det\\mathbf{J}|\\,d\\xi\\,d\\eta\\;\\;\\approx\\;\\;\\sum_{g=1}^{n_g} w_g\\,\\mathbf{B}_g^T\\mathbf{D}\\,\\mathbf{B}_g\\,t\\,|\\det\\mathbf{J}_g|', true);
    cont.appendChild(ec);
    const nota = EF.el('div', { class: 'aux', style: 'position:absolute;left:0;top:128px;width:1720px;text-align:center;font-size:24px', html: 'El integrando es racional en (ξ, η): no tiene primitiva practicable. La regla de <i>m</i> puntos integra exacto un polinomio de grado 2<i>m</i> − 1 [14, pp. 141–142].' });
    cont.appendChild(nota);
    // panel izquierdo: cuadrado con los puntos
    const cvA = EF.el('div', { style: 'position:absolute;left:0;top:196px;width:430px;height:430px' });
    cont.appendChild(cvA);
    const lzA = new EF.LienzoMEF(cvA, 430, 430);
    const selReg = EF.el('div', { class: 'segmentado solo-vivo', style: 'position:absolute;left:40px;top:630px' });
    const bR = [1, 2, 3].map((n) => { const b = EF.el('button', { text: `${n} × ${n}` }); b.onclick = () => { regla = n; actualizarBotones(); dibujarA(); modos(); }; selReg.appendChild(b); return b; });
    cont.appendChild(selReg);
    // panel central: k_e acumulándose (valores del motor, E3)
    const gK = EF.el('div', { style: 'position:absolute;left:470px;top:190px;width:560px;height:470px' });
    cont.appendChild(gK);
    const sK = S('svg', { class: 'viz', width: 560, height: 470, viewBox: '0 0 560 470' }, gK);
    const etqK = EF.el('div', { class: 'aux', style: 'position:absolute;left:470px;top:640px;width:560px;text-align:center;font-size:23px' });
    cont.appendChild(etqK);
    // panel derecho: modos de energía nula
    const der = EF.el('div', { 'data-paso': '2', style: 'position:absolute;left:1070px;top:196px;width:650px;height:480px' });
    cont.appendChild(der);
    const cvM = EF.el('div', { style: 'position:absolute;left:0;top:0;width:300px;height:300px' });
    der.appendChild(cvM);
    const lzM = new EF.LienzoMEF(cvM, 300, 300);
    const sE = S('svg', { class: 'viz', width: 330, height: 300, viewBox: '0 0 330 300', style: 'position:absolute;left:320px;top:0' }, der);
    const txtM = EF.el('div', { style: 'position:absolute;left:0;top:318px;width:650px' });
    der.appendChild(txtM);

    let regla = 2, bucle = null, acum = 4;
    function actualizarBotones() { bR.forEach((b, k) => b.classList.toggle('sel', k + 1 === regla)); }
    function dibujarA() {
      lzA.redimensionar();
      const c = lzA.inicio(null);
      const x0 = 45, y0 = 25, t = 360;
      c.fillStyle = EF.rgba(EF.css('--primario'), 0.07); c.fillRect(x0, y0, t, t);
      c.strokeStyle = EF.css('--linea-2'); c.lineWidth = 2; c.strokeRect(x0, y0, t, t);
      c.strokeStyle = EF.css('--ejeX'); c.beginPath(); c.moveTo(x0, y0 + t / 2); c.lineTo(x0 + t, y0 + t / 2); c.stroke();
      c.strokeStyle = EF.css('--ejeY'); c.beginPath(); c.moveTo(x0 + t / 2, y0); c.lineTo(x0 + t / 2, y0 + t); c.stroke();
      const R = G.reglas[String(regla)];
      R.puntos.forEach(([xi, eta], k) => {
        const px = x0 + ((xi + 1) / 2) * t, py = y0 + ((1 - eta) / 2) * t;
        const w = R.pesos[k];
        const on = regla !== 2 || k < acum;
        const rad = 10 + 14 * Math.sqrt(w);
        c.beginPath(); c.arc(px, py, rad, 0, 2 * Math.PI);
        c.fillStyle = on ? 'rgba(255,210,63,.95)' : 'rgba(255,210,63,.25)'; c.fill();
        c.lineWidth = 3; c.strokeStyle = '#1a1a1a'; c.stroke();
        c.font = `700 18px ${EF.fuente()}`; c.fillStyle = EF.css('--texto-2'); c.textAlign = 'center';
        c.fillText('w = ' + EF.fmt(w, w % 1 ? 3 : 0), px, py + rad + 24);
      });
      c.font = `650 21px ${EF.fuente()}`; c.fillStyle = EF.css('--texto-3'); c.textAlign = 'center';
      c.fillText('Puntos de Gauss en (ξ, η)', x0 + t / 2, y0 + t + 34);
    }
    const aportes = e.gauss.map((g) => g.aporte);
    const keFinal = e.ke;
    let vmaxK = 0; for (const f of keFinal) for (const v of f) vmaxK = Math.max(vmaxK, Math.abs(v));
    const celdas = [];
    const c0 = 40, tam = 55;
    for (let i = 0; i < 8; i++) { celdas.push([]); for (let j = 0; j < 8; j++) {
      const r = S('rect', { x: c0 + j * tam, y: 20 + i * tam, width: tam - 3, height: tam - 3, rx: 6 }, sK);
      const tx = S('text', { x: c0 + j * tam + (tam - 3) / 2, y: 20 + i * tam + tam / 2 + 5, 'text-anchor': 'middle' }, sK);
      est(tx, { estilo: 'font:700 15.5px var(--fuente);font-variant-numeric:tabular-nums' });
      celdas[i].push([r, tx]);
    } }
    ['u₁', 'v₁', 'u₂', 'v₂', 'u₃', 'v₃', 'u₄', 'v₄'].forEach((t, k) => {
      est(S('text', { x: c0 + k * tam + 28, y: 14, 'text-anchor': 'middle', text: t }, sK), { relleno: 'var(--texto-3)', estilo: 'font:650 15px var(--fuente)' });
      est(S('text', { x: 18, y: 20 + k * tam + 34, 'text-anchor': 'middle', text: t }, sK), { relleno: 'var(--texto-3)', estilo: 'font:650 15px var(--fuente)' });
    });
    function pintarK(n, frac) {
      for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) {
        let v = 0;
        for (let g = 0; g < 4; g++) v += aportes[g][i][j] * (g < n ? 1 : g === n ? (frac || 0) : 0);
        const t = EF.clamp(Math.abs(v) / vmaxK, 0, 1);
        const [r, tx] = celdas[i][j];
        r.style.fill = v >= 0 ? EF.rgba(EF.css('--acento'), 0.08 + 0.8 * t) : EF.rgba(EF.css('--primario'), 0.08 + 0.8 * t);
        tx.textContent = Math.abs(v) < 0.5 ? '0' : EF.fmt(v / 1000, 1);
        tx.style.fill = t > 0.55 ? '#0b1222' : 'var(--texto)';
      }
      etqK.innerHTML = n >= 4 ? `<b>k<sub>e</sub></b> de E${id} (valores ÷ 10³): suma de los 4 aportes = la matriz del Anexo G` : `Aporte de ${Math.min(n + 1, 4)} de 4 puntos de Gauss (valores ÷ 10³)`;
    }
    function acumular() {
      pintarK(0, 0); acum = 0; dibujarA();
      for (let g = 0; g < 4; g++) EF.tween({ dur: 900, retraso: 300 + g * 1050, curva: 'ambos', cada: (t) => { acum = g + 1; pintarK(g, t); dibujarA(); } });
      EF.tween({ dur: 10, retraso: 300 + 4 * 1050 + 50, fin: () => pintarK(4) });
    }
    // modos de energía nula
    const MOD = G.modos;
    function modos() {
      const R = G.reglas[String(regla)];
      sE.innerHTML = '';
      const lam = R.autovalores, lmax = Math.max(...lam);
      est(S('text', { x: 0, y: 24, text: 'Autovalores de la rigidez' }, sE), { relleno: 'var(--texto-2)', estilo: 'font:700 22px var(--fuente)' });
      lam.forEach((l, k) => {
        const h = l <= 1e-9 * lmax ? 3 : 20 + 200 * Math.pow(l / lmax, 0.5);
        const x = 12 + k * 38;
        const r = S('rect', { x, y: 260 - h, width: 28, height: h, rx: 4 }, sE);
        est(r, { relleno: l <= 1e-9 * lmax ? (k < 3 ? 'var(--texto-3)' : 'var(--mal)') : 'var(--primario)' });
      });
      est(S('text', { x: 0, y: 292, text: `${R.ceros} nulos · rango ${R.rango}` }, sE), { relleno: R.ceros > 3 ? 'var(--mal)' : 'var(--ok)', estilo: 'font:800 24px var(--fuente)' });
      const esp = R.ceros - 3;
      const caja = (fondo, color, html) => `<div style="padding:16px 22px;border-radius:16px;background:${fondo};color:${color};font:650 26px/1.32 var(--fuente)">${html}</div>`;
      txtM.innerHTML = (regla === 1
        ? caja('var(--mal-suave)', 'var(--mal)', `<b>Regla 1 × 1:</b> ${R.ceros} modos de energía nula = 3 de cuerpo rígido + ${esp} <b>modos espurios (hourglass)</b>`)
        : caja('var(--ok-suave)', 'var(--ok)', `<b>Regla ${regla} × ${regla}:</b> solo los 3 modos de cuerpo rígido. EduFEM integra completo: 2 × 2 en Q4 y 3 × 3 en Q9.`))
        + '<div class="mini" style="margin-top:10px">Elemento cuadrado de prueba (E = 1, ν = 0,3) calculado con las funciones del motor.</div>';
    }
    function dibujarModo(tiempo) {
      lzM.redimensionar();
      const c = lzM.inicio(null);
      lzM.encuadrar(-1.6, 1.6, -1.6, 1.6, 20);
      const v = regla === 1 ? MOD['Reloj de arena x'] : MOD['Estiramiento x'];
      const a = 0.32 * Math.sin(tiempo * 2.4);
      const P = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map((p, k) => [p[0] + a * v[2 * k], p[1] + a * v[2 * k + 1]]);
      lzM.elemento([[-1, -1], [1, -1], [1, 1], [-1, 1]], [0, 1, 2, 3], { color: EF.css('--texto-3'), ancho: 1.5 });
      lzM.elemento(P, [0, 1, 2, 3], { color: regla === 1 ? EF.css('--mal') : EF.css('--ok'), ancho: 4, relleno: regla === 1 ? EF.css('--mal') : EF.css('--ok'), alfaRelleno: 0.18 });
      lzM.nodos(P, [0, 1, 2, 3], { radio: 7 });
      c.beginPath(); c.arc(lzM.X(0), lzM.Y(0), 8, 0, 2 * Math.PI); c.fillStyle = '#ffd23f'; c.fill();
      lzM.etiqueta(0, -1.45, regla === 1 ? 'reloj de arena: energía nula' : 'modo con energía', { ancla: 'center', tam: 19, color: EF.css('--texto-2') });
    }
    return {
      entrar(p, op) {
        regla = p === 2 ? 1 : 2; actualizarBotones();
        if (p === 1 && !op.instantaneo && !op.impresion) acumular(); else { acum = 4; pintarK(4); }
        dibujarA(); modos(); dibujarModo(0.6);
        if (bucle) bucle.detener();
        if (p >= 2 && !op.impresion) bucle = EF.bucle((s) => dibujarModo(s));
      },
      paso(k, op) {
        if (k === 1 && op.adelante) { regla = 2; actualizarBotones(); acumular(); }
        if (k === 2) {
          regla = 1; actualizarBotones(); dibujarA(); modos();
          if (!bucle) bucle = EF.bucle((s) => dibujarModo(s));
        }
        if (k === 3) { regla = 2; actualizarBotones(); dibujarA(); modos(); }
        if (k < 2) { if (bucle) { bucle.detener(); bucle = null; } regla = 2; actualizarBotones(); dibujarA(); if (k === 0) { acum = 4; pintarK(4); } }
      },
      salir() { if (bucle) { bucle.detener(); bucle = null; } },
      redimensionar() { dibujarA(); dibujarModo(0.6); },
      tema() { dibujarA(); pintarK(acum); dibujarModo(0.6); },
    };
  });

  // ================================================================== recuperación de tensiones
  EF.registrarViz('recuperacion', function (cont) {
    const C = DAT().canonico;
    const { e, id } = elementoE3();
    const nodosId = C.nodos.map((n) => n.id);
    const P = C.nodos.map((n) => [n.x, n.y]);
    const idx = Object.fromEntries(C.nodos.map((n, i) => [n.id, i]));
    const elems = Object.entries(C.elementos_conect).map(([k, con]) => ({ id: Number(k), con: con.map((n) => idx[n]) }));
    const caja = EF.el('div', { style: 'position:absolute;left:0;top:0;width:900px;height:640px;border-radius:18px;overflow:hidden;border:1px solid var(--linea-2)' });
    cont.appendChild(caja);
    const lz = new EF.LienzoMEF(caja, 900, 640);
    const der = EF.el('div', { style: 'position:absolute;left:940px;top:0;width:780px' });
    cont.appendChild(der);
    const f0 = EF.el('div', { class: 'tarjeta', style: 'padding:22px 26px' });
    const e1 = EF.el('div', { class: 'ec-chica' }); EF.katex(e1, '\\boldsymbol{\\sigma}_g=\\mathbf{D}\\,\\mathbf{B}_g\\,\\mathbf{u}_e', true);
    f0.append(EF.el('div', { class: 'etq', text: '1 · En los puntos de Gauss' }), e1);
    const f1 = EF.el('div', { class: 'tarjeta', style: 'padding:22px 26px;margin-top:18px', 'data-paso': '1' });
    const e2 = EF.el('div', { class: 'ec-chica' }); EF.katex(e2, '\\boldsymbol{\\sigma}_{\\text{nodos}}=\\mathbf{E}\\,\\boldsymbol{\\sigma}_{\\text{Gauss}},\\quad \\mathbf{E}=\\mathbf{M}^{-1}=\\begin{bmatrix}a&b&b&c\\\\b&c&a&b\\\\c&b&b&a\\\\b&a&c&b\\end{bmatrix}', true);
    const e2b = EF.el('div', { class: 'mini', html: 'a = 1 + √3/2 ≈ 1,866 · b = −0,5 · c = 1 − √3/2 ≈ 0,134. <b>E</b> en negrita es la matriz de extrapolación, no el módulo de elasticidad.' });
    f1.append(EF.el('div', { class: 'etq', text: '2 · Extrapolación a los nodos' }), e2, e2b);
    const f2 = EF.el('div', { class: 'tarjeta', style: 'padding:22px 26px;margin-top:18px', 'data-paso': '2' });
    const e3 = EF.el('div', { class: 'ec-chica' }); EF.katex(e3, '\\boldsymbol{\\sigma}_{\\text{nodo}}=\\frac{1}{n_e}\\sum_{e=1}^{n_e}\\boldsymbol{\\sigma}^{(e)}_{\\text{nodo}}', true);
    f2.append(EF.el('div', { class: 'etq', text: '3 · Promedio en el nodo compartido' }), e3, EF.el('div', { class: 'mini', text: 'El salto entre los valores sin promediar indica el error de discretización [1, pp. 476–477].' }));
    der.append(f0, f1, f2);
    const seg = EF.el('div', { class: 'segmentado solo-vivo', 'data-paso': '3', style: 'position:absolute;right:0;top:-174px' });
    const bCrudo = EF.el('button', { text: 'Crudo' }), bSuave = EF.el('button', { class: 'sel', text: 'Suavizado' });
    seg.append(bCrudo, bSuave);
    cont.appendChild(seg);
    const comp = 1; // sigma_y: la componente dominante en E3
    let paso = 0, vista = 'suave', prog = 1;
    const sGauss = e.sigma_gauss.map((s) => s[comp]);
    const sNod = e.sigma_nodal.map((s) => s[comp]);
    const conE3 = e.nodos.map((n) => idx[n]);
    function puntoGauss(k) {
      const [xi, eta] = C.gauss_pts[k];
      const Nv = EF.Q4.N(xi, eta);
      return [EF.interp(Nv, e.X.map((p) => p[0])), EF.interp(Nv, e.X.map((p) => p[1]))];
    }
    function dibujar() {
      lz.redimensionar();
      lz.encuadrar(-0.6, 11.6, -0.6, 8.8, { s: 40, d: 40, i: 40, iz: 40 });
      lz.inicio(EF.css('--lienzo'));
      const todos = [];
      for (const el of elems) for (const s of C.elementos[String(el.id)].sigma_nodal) todos.push(s[comp]);
      const vmin = Math.min(...todos), vmax = Math.max(...todos);
      if (paso >= 3) {
        if (vista === 'crudo') {
          for (const el of elems) {
            const v = C.elementos[String(el.id)].sigma_nodal.map((s) => s[comp]);
            const nod = el.con.map((i) => P[i]);
            lz.campo(nod, [[0, 1, 2, 3]], v, { min: vmin, max: vmax, sub: 6 });
          }
        } else {
          const v = nodosId.map((n) => C.nodal[String(n)].sy);
          lz.campo(P, elems.map((x) => x.con), v, { min: vmin, max: vmax, sub: 6 });
        }
      }
      lz.malla(P, elems.map((x) => x.con), { color: paso >= 3 ? 'rgba(255,255,255,.6)' : EF.css('--malla'), ancho: 2 });
      lz.elemento(P, conE3, { color: EF.css('--acento'), ancho: 4, relleno: paso < 3 ? EF.css('--acento') : null, alfaRelleno: 0.1 });
      lz.nodos(P, P.map((_, i) => i), { radio: 7 });
      C.nodos.forEach((n, i) => lz.etiqueta(P[i][0], P[i][1], String(n.id), { dx: 12, dy: -14, tam: 19, color: EF.css('--texto-3') }));
      if (paso < 2) {
        const c = lz.ctx;
        // puntos de Gauss con sigma_y
        sGauss.forEach((v, k) => {
          const [x, y] = puntoGauss(k);
          c.beginPath(); c.arc(lz.X(x), lz.Y(y), 12, 0, 2 * Math.PI); c.fillStyle = EF.jetCss((v - vmin) / (vmax - vmin)); c.fill();
          c.lineWidth = 3; c.strokeStyle = '#111'; c.stroke();
          lz.etiqueta(x, y, EF.fmt(v, 1), { dy: 28, ancla: 'center', tam: 19, color: '#111', fondo: '#fff', alfaFondo: 0.88 });
        });
        if (paso >= 1) {
          // pesos hacia el nodo 4 (esquina (-1,-1) de E3)
          const destino = P[conE3[0]];
          const pesos = e.gauss.map((_, k) => DAT().canonico.E_extrap[0][k]);
          sGauss.forEach((v, k) => {
            const [x, y] = puntoGauss(k);
            const t = EF.clamp(prog * 1.2 - k * 0.15, 0, 1);
            const xa = x + (destino[0] - x) * t, ya = y + (destino[1] - y) * t;
            c.save(); c.setLineDash([6, 6]); c.strokeStyle = EF.css('--acento'); c.lineWidth = 2.5;
            c.beginPath(); c.moveTo(lz.X(x), lz.Y(y)); c.lineTo(lz.X(xa), lz.Y(ya)); c.stroke(); c.restore();
            if (t > 0.5) lz.etiqueta((x + destino[0]) / 2, (y + destino[1]) / 2, '×' + EF.fmt(pesos[k], 3), { ancla: 'center', tam: 18, color: EF.css('--acento'), fondo: EF.css('--lienzo'), alfaFondo: 0.9 });
          });
          if (prog >= 1) {
            conE3.forEach((i, k) => lz.etiqueta(P[i][0], P[i][1], EF.fmt(sNod[k], 1), { dx: k === 0 || k === 3 ? -18 : 18, dy: k < 2 ? 30 : -34, ancla: k === 0 || k === 3 ? 'right' : 'left', tam: 21, color: '#111', fondo: '#ffd23f', alfaFondo: 0.95 }));
          }
        }
      }
      if (paso === 2) {
        // nodo 5: el valor que le llega desde cada uno de sus cuatro elementos, y su promedio
        const i5 = idx[5];
        const vals = C.nodal['5'].elementos.map((ide) => { const el = C.elementos[String(ide)]; const k = el.nodos.indexOf(5); return { ide, v: el.sigma_nodal[k][comp] }; });
        const off = { 1: [-2.0, -1.3], 2: [2.0, -1.3], 3: [-2.0, 1.4], 4: [2.0, 1.4] };
        const c = lz.ctx;
        vals.forEach((o) => {
          const [dx, dy] = off[o.ide];
          c.save(); c.strokeStyle = EF.css('--texto-3'); c.lineWidth = 1.5; c.setLineDash([4, 5]);
          c.beginPath(); c.moveTo(lz.X(P[i5][0]), lz.Y(P[i5][1])); c.lineTo(lz.X(P[i5][0] + dx * 0.8), lz.Y(P[i5][1] + dy * 0.8)); c.stroke(); c.restore();
          lz.etiqueta(P[i5][0] + dx, P[i5][1] + dy, `E${o.ide}: ${EF.fmt(o.v, 1)}`, { ancla: 'center', tam: 21, color: EF.css('--texto'), fondo: EF.css('--superficie-3'), alfaFondo: 0.96, borde: EF.css('--linea-2') });
        });
        lz.etiqueta(9.4, 1.4, `nodo 5 → promedio ${EF.fmt(C.nodal['5'].sy, 1)}`, { ancla: 'center', tam: 22, color: '#0b1222', fondo: '#34d399', alfaFondo: 0.96 });
      }
      lz.etiqueta(-0.3, -0.35, paso >= 3 ? `σy ${vista === 'crudo' ? 'crudo: discontinuo entre elementos' : 'suavizado: promedio nodal'}` : (paso === 2 ? 'σy en el nodo 5, desde sus cuatro elementos' : 'σy en E3: puntos de Gauss → nodos'), { tam: 21, color: EF.css('--texto-2') });
    }
    bCrudo.onclick = () => { vista = 'crudo'; bCrudo.classList.add('sel'); bSuave.classList.remove('sel'); dibujar(); };
    bSuave.onclick = () => { vista = 'suave'; bSuave.classList.add('sel'); bCrudo.classList.remove('sel'); dibujar(); };
    let alt = null;
    return {
      entrar(p, op) { paso = p; prog = 1; vista = 'suave'; dibujar(); if (p === 3 && !op.impresion && !op.instantaneo) alternar(); },
      paso(k, op) {
        paso = k;
        if (alt) { alt.cancelar(); alt = null; }
        if (k === 1 && op.adelante) { prog = 0; EF.tween({ dur: 1600, curva: 'ambos', cada: (t) => { prog = t; dibujar(); } }); }
        else { prog = 1; dibujar(); }
        if (k === 3 && op.adelante) alternar();
      },
      salir() { if (alt) { alt.cancelar(); alt = null; } },
      redimensionar() { dibujar(); },
      tema() { dibujar(); },
    };
    function alternar() {
      vista = 'crudo'; dibujar();
      alt = EF.tween({ dur: 2600, fin: () => { vista = 'suave'; bSuave.classList.add('sel'); bCrudo.classList.remove('sel'); dibujar(); alt = null; } });
    }
  });

  // ================================================================== idea de convergencia (errores reales del MMS)
  EF.registrarViz('convergencia-idea', function (cont) {
    const T = DAT().mms.tablas.unif_tp;
    const W = 1720, H = 390;
    const s = S('svg', { class: 'viz', width: W, height: H, viewBox: `0 0 ${W} ${H}` }, cont);
    const grupos = [];
    const filas = [['Q4', 'var(--q4)', 'Q4 (p = 1): error L² ∝ h² → cada mitad de h lo divide por 4'], ['Q9', 'var(--q9)', 'Q9 (p = 2): error L² ∝ h³ → cada mitad de h lo divide por 8']];
    filas.forEach(([el, col, tit], r) => {
      const g = S('g', { transform: `translate(${r * 870},0)` }, s);
      est(S('text', { x: 0, y: 28, text: tit }, g), { relleno: col, estilo: 'font:750 25px var(--fuente)' });
      const datos = T[el].slice(0, 4);
      const maxE = datos[0].L2;
      const barras = [];
      datos.forEach((d, k) => {
        const x = k * 205;
        // malla N x N
        const gm = S('g', { transform: `translate(${x + 10},52)` }, g);
        const t = 120;
        est(S('rect', { x: 0, y: 0, width: t, height: t }, gm), { relleno: 'var(--superficie-2)', trazo: col, estilo: 'stroke-width:2' });
        for (let i = 1; i < d.N; i++) {
          est(S('line', { x1: (i * t) / d.N, y1: 0, x2: (i * t) / d.N, y2: t }, gm), { trazo: col, estilo: 'stroke-width:1;opacity:.6' });
          est(S('line', { x1: 0, y1: (i * t) / d.N, x2: t, y2: (i * t) / d.N }, gm), { trazo: col, estilo: 'stroke-width:1;opacity:.6' });
        }
        est(S('text', { x: t / 2, y: t + 30, 'text-anchor': 'middle', text: `N = ${d.N}` }, gm), { relleno: 'var(--texto-3)', estilo: 'font:650 20px var(--fuente)' });
        // barra del error (escala log)
        const hmax = 150;
        const h = hmax * (1 - Math.log10(maxE / d.L2) / (el === 'Q4' ? 2.6 : 3.5));
        const b = S('rect', { x: x + 150, y: 350 - h, width: 34, height: h, rx: 6 }, g);
        est(b, { relleno: col });
        const v = S('text', { x: x + 167, y: 350 - h - 10, 'text-anchor': 'middle', text: EF.fmtCient(d.L2, 2) }, g);
        est(v, { relleno: 'var(--texto-2)', estilo: 'font:650 16px var(--fuente)' });
        barras.push([gm, b, v]);
        if (k > 0) {
          const razon = datos[k - 1].L2 / d.L2;
          const rz = S('text', { x: x - 20, y: 368, 'text-anchor': 'middle', text: '÷ ' + EF.fmt(razon, 1) }, g);
          est(rz, { relleno: col, estilo: 'font:800 24px var(--fuente)' });
          barras[k].push(rz);
        }
      });
      grupos.push({ g, barras });
    });
    function mostrar(r, anim) {
      const G2 = grupos[r];
      G2.g.style.opacity = '1';
      G2.barras.forEach((b, k) => b.forEach((e) => {
        if (!anim) { e.style.opacity = '1'; return; }
        e.style.opacity = '0';
        EF.tween({ dur: 450, retraso: 200 + k * 520, cada: (t) => { e.style.opacity = String(t); } });
      }));
    }
    function ocultar(r) { grupos[r].g.style.opacity = '0'; }
    return {
      entrar(p, op) {
        const anim = !op.instantaneo && !op.impresion;
        if (p >= 1) mostrar(0, anim && p === 1); else ocultar(0);
        if (p >= 2) mostrar(1, anim && p === 2); else ocultar(1);
      },
      paso(k, op) {
        if (k >= 1) mostrar(0, op.adelante && k === 1); else ocultar(0);
        if (k >= 2) mostrar(1, op.adelante && k === 2); else ocultar(1);
      },
    };
  });
})();
