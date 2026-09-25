/* =====================================================================
   viz/intro.js — animaciones del bloque de Introducción.
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const DAT = () => window.EDUFEM_DATOS;

  const ETAPAS = (EF.ETAPAS = [
    { n: 1, t: 'Mapeo isoparamétrico', l: ['Mapeo', 'isoparamétrico'], tex: 'x(\\xi,\\eta)=\\sum_i N_i(\\xi,\\eta)\\,x_i', mod: 'M1', sec: '§ 1.5', mem: 'Formulación elemental', post: false },
    { n: 2, t: 'Matriz Jacobiana', l: ['Matriz', 'Jacobiana'], tex: '\\mathbf{J}=\\dfrac{\\partial\\mathbf{N}}{\\partial(\\xi,\\eta)}\\,\\mathbf{X}_e', mod: 'M2', sec: '§ 1.6', mem: 'Formulación elemental', post: false },
    { n: 3, t: 'Matriz de deformación B', l: ['Matriz B', 'deformación'], tex: '\\boldsymbol{\\varepsilon}=\\mathbf{B}\\,\\mathbf{u}_e', mod: 'M3', sec: '§ 1.7', mem: 'Formulación elemental', post: false },
    { n: 4, t: 'Matriz constitutiva D', l: ['Matriz D', 'material'], tex: '\\boldsymbol{\\sigma}=\\mathbf{D}\\,\\boldsymbol{\\varepsilon}', mod: 'M4', sec: '§ 1.4', mem: 'Formulación elemental', post: false },
    { n: 5, t: 'Rigidez por cuadratura de Gauss', l: ['Rigidez', 'por Gauss'], tex: '\\mathbf{k}_e\\approx\\sum_g w_g\\,\\mathbf{B}^T\\mathbf{D}\\mathbf{B}\\,t\\,|\\det\\mathbf{J}|', mod: 'M5', sec: '§ 1.8', mem: 'Formulación elemental', post: false },
    { n: 6, t: 'Fuerzas nodales equivalentes', l: ['Fuerzas', 'equivalentes'], tex: 'F_1=\\tfrac{L}{6}(2q_1+q_2),\\;\\;F_2=\\tfrac{L}{6}(q_1+2q_2)', mod: 'M6', sec: '§ 1.10', mem: 'Ensamblaje', post: false },
    { n: 7, t: 'Ensamblaje', l: ['Ensamblaje', 'de K y F'], tex: '\\mathbf{K}=\\mathop{\\mathsf{A}}_{e}\\,\\mathbf{k}_e', mod: 'M7', sec: '§ 1.10', mem: 'Ensamblaje', post: false },
    { n: 8, t: 'Restricciones y solución', l: ['Restricciones', 'y solución'], tex: '\\mathbf{K}_{ff}\\,\\mathbf{u}_f=\\mathbf{F}_f-\\mathbf{K}_{fr}\\,\\mathbf{u}_r', mod: null, sec: '§ 1.11', mem: 'Restricciones y solución', post: true },
    { n: 9, t: 'Recuperación de tensiones', l: ['Recuperación', 'de tensiones'], tex: '\\boldsymbol{\\sigma}_{\\text{nodos}}=\\mathbf{E}\\,\\boldsymbol{\\sigma}_{\\text{Gauss}}', mod: null, sec: '§ 1.11', mem: 'Post-proceso', post: true },
  ]);
  // rótulo de una palabra para barras compactas
  ['Mapeo', 'Jacobiano', 'Matriz B', 'Matriz D', 'Rigidez', 'Fuerzas', 'Ensamblaje', 'Solución', 'Tensiones'].forEach((c, k) => { ETAPAS[k].c = c; });

  // ------------------------------------------------------------------ miniatura del resultado (post-proceso real)
  /** Dibuja el contorno de von Mises del ejemplo canónico sobre la deformada. */
  EF.miniaturaCanonico = function (contenedor, W, H, op) {
    op = op || {};
    const C = DAT().canonico;
    const nodos = C.nodos.map((n) => [n.x, n.y]);
    const idx = Object.fromEntries(C.nodos.map((n, i) => [n.id, i]));
    const elems = Object.values(C.elementos_conect).map((con) => con.map((id) => idx[id]));
    const u = C.nodos.map((n, i) => [C.u[2 * i], C.u[2 * i + 1]]);
    const vm = C.nodos.map((n) => C.nodal[String(n.id)].vm);
    const lz = new EF.LienzoMEF(contenedor, W, H);
    function dibujar() {
      lz.redimensionar();
      lz.encuadrar(-0.8, 11.8, -0.6, 8.8, op.pad || 26);
      lz.inicio(op.fondo || EF.css('--lienzo'));
      const esc = op.escala == null ? 60 : op.escala;
      lz.malla(nodos, elems, { color: EF.css('--texto-3'), ancho: 1.2, discontinua: [6, 6], alfa: 0.5 });
      lz.campo(nodos, elems, vm, { u, escala: esc, sub: 6 });
      lz.malla(nodos, elems, { color: 'rgba(255,255,255,.55)', ancho: 1.4, u, escala: esc });
      for (const a of C.apoyos) { const p = nodos[idx[a]]; lz.apoyo(p[0], p[1], { tam: 11 }); }
      const p7 = EF.LienzoMEF.pos(nodos, u, esc, idx[7]);
      lz.flecha(p7[0], p7[1], 0, -1, { largo: 50, ancho: 3.5 });
    }
    dibujar();
    return { lz, dibujar, nodos, elems, u, vm, idx };
  };

  // ------------------------------------------------------------------ caja negra
  EF.registrarViz('cajanegra', function (cont) {
    const W = 1720, H = 500;
    const s = EF.svg('svg', { class: 'viz', width: W, height: H, viewBox: `0 0 ${W} ${H}`, style: 'position:absolute;left:0;top:0;overflow:visible' }, cont);
    const est = EF.estiloSvg;
    const g = EF.svg('g', {}, s);
    const entradas = [
      { t: 'Geometría y malla', s: 'nodos · elementos', y: 30, ico: 'malla' },
      { t: 'Material', s: 'E · ν · espesor t', y: 191, ico: 'mat' },
      { t: 'Cargas y apoyos', s: 'fuerzas · restricciones', y: 352, ico: 'carga' },
    ];
    for (const e of entradas) {
      const gg = EF.svg('g', { transform: `translate(0,${e.y})` }, g);
      est(EF.svg('rect', { x: 0, y: 0, width: 300, height: 118, rx: 20 }, gg), { relleno: 'var(--superficie-2)', trazo: 'var(--linea-2)', estilo: 'stroke-width:1.5' });
      est(EF.svg('text', { x: 104, y: 52, text: e.t }, gg), { relleno: 'var(--texto)', estilo: 'font:750 27px var(--fuente)' });
      est(EF.svg('text', { x: 104, y: 88, text: e.s }, gg), { relleno: 'var(--texto-3)', estilo: 'font:600 20px var(--fuente)' });
      const ic = EF.svg('g', { transform: 'translate(22,24)' }, gg);
      if (e.ico === 'malla') {
        for (let i = 0; i <= 3; i++) {
          est(EF.svg('line', { x1: i * 20, y1: 0, x2: i * 20 + 6, y2: 66 }, ic), { trazo: 'var(--malla)', estilo: 'stroke-width:2.5' });
          est(EF.svg('line', { x1: 0, y1: i * 22, x2: 64, y2: i * 22 + 4 }, ic), { trazo: 'var(--malla)', estilo: 'stroke-width:2.5' });
        }
      } else if (e.ico === 'mat') {
        est(EF.svg('rect', { x: 2, y: 6, width: 62, height: 56, rx: 8 }, ic), { relleno: 'var(--primario-suave)', trazo: 'var(--primario)', estilo: 'stroke-width:3' });
        est(EF.svg('text', { x: 33, y: 45, 'text-anchor': 'middle', text: 'E, ν' }, ic), { relleno: 'var(--primario)', estilo: 'font:800 22px var(--fuente)' });
      } else {
        est(EF.svg('path', { d: 'M34 0 V42 M22 30 L34 46 L46 30' }, ic), { trazo: 'var(--carga)', relleno: 'none', estilo: 'stroke-width:5;stroke-linecap:round' });
        est(EF.svg('path', { d: 'M12 70 L34 52 L56 70 Z' }, ic), { trazo: 'var(--apoyo)', relleno: 'none', estilo: 'stroke-width:4' });
      }
    }
    const flechas = [];
    for (const e of entradas) {
      const p = EF.svg('path', { d: `M308,${e.y + 59} C380,${e.y + 59} 380,250 440,250` }, g);
      est(p, { trazo: 'var(--texto-3)', relleno: 'none', estilo: 'stroke-width:3;stroke-dasharray:8 8' });
      flechas.push(p);
    }
    const salida = EF.svg('path', { d: 'M858,250 L950,250' }, g);
    est(salida, { trazo: 'var(--texto-3)', relleno: 'none', estilo: 'stroke-width:3;stroke-dasharray:8 8' });
    est(EF.svg('path', { d: 'M944,238 L964,250 L944,262 Z' }, g), { relleno: 'var(--texto-3)' });
    flechas.push(salida);

    // caja: interior (procedimiento) + frente opaco que se abre como una persiana
    const caja = EF.svg('g', {}, g);
    const borde = EF.svg('rect', { x: 450, y: 50, width: 400, height: 400, rx: 26 }, caja);
    est(borde, { relleno: 'var(--superficie)', trazo: 'var(--linea-2)', estilo: 'stroke-width:2' });
    const interior = EF.svg('g', {}, caja);
    const chips = [];
    EF.ETAPAS.forEach((et, k) => {
      const col = k % 3, fila = Math.floor(k / 3);
      const x = 464 + col * 128, y = 124 + fila * 108;
      const gc = EF.svg('g', { transform: `translate(${x},${y})` }, interior);
      est(EF.svg('rect', { x: 0, y: 0, width: 116, height: 98, rx: 13 }, gc), { relleno: 'var(--acento-suave)', trazo: 'var(--acento)', estilo: 'stroke-width:1.5' });
      est(EF.svg('text', { x: 12, y: 30, text: String(et.n) }, gc), { relleno: 'var(--acento)', estilo: 'font:850 26px var(--fuente)' });
      est(EF.svg('text', { x: 12, y: 60, text: et.l[0] }, gc), { relleno: 'var(--texto)', estilo: 'font:750 16.5px var(--fuente)' });
      est(EF.svg('text', { x: 12, y: 82, text: et.l[1] }, gc), { relleno: 'var(--texto-2)', estilo: 'font:600 15px var(--fuente)' });
      chips.push(gc);
    });
    est(EF.svg('text', { x: 650, y: 98, 'text-anchor': 'middle', text: 'Procedimiento a la vista' }, interior), { relleno: 'var(--acento)', estilo: 'font:800 25px var(--fuente)' });
    const frente = EF.svg('g', {}, caja);
    est(EF.svg('rect', { x: 450, y: 50, width: 400, height: 400, rx: 26 }, frente), { relleno: '#05070c', trazo: '#2a3550', estilo: 'stroke-width:2' });
    est(EF.svg('text', { x: 650, y: 245, 'text-anchor': 'middle', text: '?' }, frente), { relleno: '#1e2840', estilo: 'font:900 190px var(--fuente)' });
    est(EF.svg('text', { x: 650, y: 360, 'text-anchor': 'middle', text: 'Software de análisis' }, frente), { relleno: '#c5d0e6', estilo: 'font:750 29px var(--fuente)' });
    est(EF.svg('text', { x: 650, y: 398, 'text-anchor': 'middle', text: '(caja negra)' }, frente), { relleno: '#6f7f9e', estilo: 'font:650 22px var(--fuente)' });
    const clip = EF.svg('clipPath', { id: 'clipFrente' }, EF.svg('defs', {}, s));
    const clipR = EF.svg('rect', { x: 450, y: 50, width: 400, height: 400 }, clip);
    frente.setAttribute('clip-path', 'url(#clipFrente)');

    // resultado: contorno real del ejemplo canónico (post-proceso de EduFEM)
    const res = EF.el('div', { style: 'position:absolute;left:970px;top:90px;width:380px;height:320px;border-radius:18px;overflow:hidden;border:1px solid var(--linea-2);box-shadow:var(--sombra-s)' });
    cont.appendChild(res);
    const mini = EF.miniaturaCanonico(res, 380, 320, { escala: 60, pad: 20 });
    cont.appendChild(EF.el('div', { style: 'position:absolute;left:970px;top:424px;width:380px;text-align:center;font:650 22px var(--fuente);color:var(--texto-3)', text: 'Resultado: contorno de tensiones' }));

    cont.append(
      EF.el('div', { class: 'pregunta', 'data-paso': '1', style: 'left:1380px;top:70px;width:340px', html: '¿De dónde sale <b>esta tensión nodal</b>?' }),
      EF.el('div', { class: 'pregunta', 'data-paso': '1', 'data-retraso': '350', style: 'left:1380px;top:238px;width:340px', html: '¿Cierran las tensiones de los nodos con las de los <b>puntos de Gauss</b>?' }),
    );

    const puntos = flechas.map(() => { const c = EF.svg('circle', { r: 7 }, g); est(c, { relleno: 'var(--acento)' }); c.style.opacity = '0'; return c; });
    function flujo() {
      return EF.tween({
        dur: 2600, curva: 'lineal',
        cada: (e) => {
          flechas.forEach((p, k) => {
            const L = p.getTotalLength();
            const f = k < 3 ? EF.clamp(e * 1.6, 0, 1) : EF.clamp((e - 0.62) * 2.7, 0, 1);
            const q = p.getPointAtLength(L * f);
            puntos[k].setAttribute('cx', q.x); puntos[k].setAttribute('cy', q.y);
            puntos[k].style.opacity = f > 0 && f < 1 ? '1' : '0';
          });
        },
      });
    }
    function fijarApertura(a) {
      clipR.setAttribute('height', String(400 * (1 - a)));
      est(borde, { relleno: 'var(--superficie)', trazo: a > 0.5 ? 'var(--acento)' : 'var(--linea-2)', estilo: `stroke-width:${a > 0.5 ? 3 : 2}` });
      interior.style.opacity = String(EF.clamp(a * 1.4, 0, 1));
    }
    function abrir(anim) {
      if (!anim) { fijarApertura(1); chips.forEach((c) => (c.style.opacity = '1')); return; }
      chips.forEach((c) => (c.style.opacity = '0'));
      EF.tween({ dur: 900, curva: 'ambos', cada: (e) => fijarApertura(e) });
      chips.forEach((c, k) => EF.tween({ dur: 420, retraso: 650 + k * 110, curva: 'sale', cada: (e) => { c.style.opacity = String(e); } }));
    }
    return {
      entrar(p, op) {
        mini.dibujar();
        if (p >= 3) abrir(false); else fijarApertura(0);
        if (!op.instantaneo && !op.impresion && p < 3) flujo();
      },
      paso(k, op) {
        if (k === 3 && op.adelante) abrir(true);
        else if (k >= 3) abrir(false);
        else fijarApertura(0);
      },
      tema() { mini.dibujar(); },
      redimensionar() { mini.dibujar(); },
    };
  });
})();
