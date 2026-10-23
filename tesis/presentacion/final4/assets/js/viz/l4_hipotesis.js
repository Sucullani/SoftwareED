/* =====================================================================
   viz/l4_hipotesis.js — visualizaciones del grupo «hipotesis» (final4).

   h7-hipotesis   lámina 07. Paso 0: el enunciado entra palabra por palabra.
                  Paso 1: las palabras vuelan a cuatro filas, una por parte
                  (condición, intervención, efecto, antecedente), y cada parte
                  se subraya con su color. Paso 2: la Figura 2.1 de la tesis,
                  animada (el problema, EduFEM y el cambio de nivel que la
                  hipótesis predice). Paso 3: PI-1 y PI-2 cuelgan de las
                  cláusulas (a) y (b) del efecto.
   c42-contraste  lámina 42. La Figura CR.1 y la Tabla 3.11: las premisas se
                  respaldan, los criterios de cada cláusula se marcan uno a uno
                  y el sello «Hipótesis comprobada» cae con la regla conjuntiva.

   Todo lo que se mueve pasa por EF.tween (reloj virtual del video). Los colores
   son variables CSS (--h-vi, --h-vd, --h-int, --h-ok, --h-mal), así la versión
   oscura y la clara se leen igual.
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const est = (e, op) => EF.estiloSvg(e, op);

  // ------------------------------------------------------------------ utilidades
  /** Junta las animaciones de una lámina para cortarlas al cambiar de paso. */
  function animador() {
    let lista = [];
    return {
      t(op) { const tw = EF.tween(op); lista.push(tw); return tw; },
      trazar(path, op) { const tw = EF.trazar(path, op); lista.push(tw); return tw; },
      parar() { const l = lista; lista = []; for (const tw of l) tw.cancelar(false); },
    };
  }
  /** Posición de el respecto de base (un ancestro posicionado), en px de diseño, sin
   *  transformaciones: sirve aunque el escenario esté escalado o la lámina entrando. */
  function posRel(el, base) {
    let x = 0, y = 0, e = el;
    while (e && e !== base) { x += e.offsetLeft; y += e.offsetTop; e = e.offsetParent; }
    return { x, y, w: el.offsetWidth, h: el.offsetHeight };
  }
  /** Rectángulos de cada línea de un elemento en línea, respecto de base, en px de diseño. */
  function lineasRel(el, base) {
    const b = base.getBoundingClientRect();
    const s = base.offsetWidth ? b.width / base.offsetWidth : 1;
    return Array.from(el.getClientRects()).filter((r) => r.width > 0.5)
      .map((r) => ({ x: (r.left - b.left) / s, y: (r.top - b.top) / s, w: r.width / s, h: r.height / s }));
  }
  /** Ejecuta fn con los elementos dentro del flujo aunque el motor de pasos los tenga fuera
   *  (clase nodisp): sirve para medir dónde caerá lo que todavía no se muestra. */
  function conFlujo(els, fn) {
    const quitados = els.filter((e) => e && e.classList.contains('nodisp'));
    for (const e of quitados) e.classList.remove('nodisp');
    try { return fn(); } finally { for (const e of quitados) e.classList.add('nodisp'); }
  }
  /** Envuelve cada palabra de los textos de raiz en <span class="clase"> (sin tocar el texto:
   *  los espacios quedan como están). Omite lo que cuelga de «saltar». */
  function partirPalabras(raiz, clase, saltar) {
    const nodos = [];
    const w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
    while (w.nextNode()) {
      const n = w.currentNode;
      if (saltar && n.parentElement.closest(saltar)) continue;
      if (n.textContent.trim()) nodos.push(n);
    }
    const out = [];
    for (const n of nodos) {
      const frag = document.createDocumentFragment();
      for (const p of n.textContent.split(/(\s+)/)) {
        if (!p) continue;
        if (/^\s+$/.test(p)) { frag.append(document.createTextNode(p)); continue; }
        const s = EF.el('span', { class: clase, text: p });
        frag.append(s);
        out.push(s);
      }
      n.replaceWith(frag);
    }
    return out;
  }
  const limpiar = (el) => { el.style.opacity = ''; el.style.transform = ''; };
  /** Deja un trazo SVG sin dibujar y sin su punta de flecha (la punta aparece al final). */
  function ocultarTrazo(p) {
    p.removeAttribute('marker-end');
    let L = 1000;
    try { L = p.getTotalLength() || L; } catch (e) { /* sin geometría */ }
    p.style.strokeDasharray = `${L} ${L}`;
    p.style.strokeDashoffset = String(L);
  }
  /** Dibuja el trazo a partir de «retraso» y le pone la punta cuando llega. */
  function trazarConPunta(an, p, punta, retraso, dur) {
    an.t({ dur: 1, retraso, fin: () => an.trazar(p, { dur }) });
    an.t({ dur: 1, retraso: retraso + dur + 30, fin: () => p.setAttribute('marker-end', punta) });
  }
  const COLOR = { 'p-int': '--h-int', 'p-vd': '--h-vd', 'p-vi': '--h-vi' };
  const claseParte = (el) => Object.keys(COLOR).find((c) => el.classList.contains(c)) || 'p-int';

  // ------------------------------------------------------------------ Figura 2.1
  // La de la tesis (tesis/figuras/generar_figuras_formulacion.py, fig_relacion_variables): los
  // dos círculos, la flecha roja del problema, la caja de EduFEM y las flechas de la
  // intervención, con los mismos textos. La animación agrega lo que la figura dice en palabras:
  // los niveles conmutan, caja negra → a la vista y baja → alta.
  function figuraVariables(cont) {
    const W = 1720, H = 716;
    const s = EF.svg('svg', { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: 'xMidYMin meet' }, cont);
    const defs = EF.svg('defs', {}, s);
    const punta = (id, color) => {
      const m = EF.svg('marker', { id, viewBox: '0 0 12 12', refX: 10, refY: 6, markerWidth: 6, markerHeight: 6, orient: 'auto-start-reverse' }, defs);
      est(EF.svg('path', { d: 'M1,1 L11,6 L1,11 Z' }, m), { relleno: color });
    };
    punta('h7-punta-mal', 'var(--h-mal)');
    punta('h7-punta-gris', 'var(--texto-3)');
    const texto = (g, x, y, t, estilo, color, ancla) =>
      est(EF.svg('text', { x, y, 'text-anchor': ancla || 'middle', text: t }, g), { relleno: color || 'var(--texto)', estilo });

    // una variable: rótulo arriba, círculo, nombre y sus dos niveles
    function variable(op) {
      const { cx, cy, r, titulo, lineas, y0, tam, niveles, ancho, color, suave } = op;
      const g = EF.svg('g', {}, s);
      texto(g, cx, 36, titulo, 'font:800 24px var(--fuente);letter-spacing:.06em', color);
      const circ = est(EF.svg('circle', { cx, cy, r }, g), { relleno: suave, trazo: color, estilo: 'stroke-width:5' });
      lineas.forEach((l, k) => texto(g, cx, y0 + k * (tam + 9), l, `font:800 ${tam}px var(--fuente)`, 'var(--texto)'));
      const yn = y0 + lineas.length * (tam + 9) + 6;
      texto(g, cx, yn, 'niveles', 'font:650 22px var(--fuente)', 'var(--texto-3)');
      const pills = niveles.map((n, k) => {
        const x = k ? cx + 6 : cx - 6 - ancho;
        const gp = EF.svg('g', {}, g);
        const rr = est(EF.svg('rect', { x, y: yn + 14, width: ancho, height: 46, rx: 23 }, gp), { relleno: color, trazo: color, estilo: 'stroke-width:2.5' });
        const tt = texto(gp, x + ancho / 2, yn + 46, n, 'font:750 24px var(--fuente)', color);
        return { rr, tt, color };
      });
      return { g, circ, pills, cx, cy };
    }
    const vi = variable({ cx: 300, cy: 262, r: 200, titulo: 'VARIABLE INDEPENDIENTE (CAUSA)', lineas: ['Transparencia', 'del procedimiento', 'de cálculo'],
      y0: 192, tam: 31, niveles: ['caja negra', 'a la vista'], ancho: 146, color: 'var(--h-vi)', suave: 'var(--h-vi-suave)' });
    const vd = variable({ cx: 1420, cy: 262, r: 200, titulo: 'VARIABLE DEPENDIENTE (EFECTO)', lineas: ['Trazabilidad y', 'verificabilidad del', 'procedimiento', 'de cálculo'],
      y0: 168, tam: 29, niveles: ['baja', 'alta'], ancho: 118, color: 'var(--h-vd)', suave: 'var(--h-vd-suave)' });
    /** Nivel k de una variable, encendido en la proporción t (0 apagado, 1 encendido). */
    function nivel(v, k, t) {
      const p = v.pills[k];
      p.rr.style.fillOpacity = String(t);
      p.tt.style.fill = t > 0.5 ? 'var(--fondo)' : p.color;
    }

    // el problema: la causa en su nivel de partida incide en el efecto
    const gProb = EF.svg('g', {}, s);
    const flechaProb = est(EF.svg('path', { d: 'M525,176 Q860,46 1195,176', 'marker-end': 'url(#h7-punta-mal)' }, gProb),
      { relleno: 'none', trazo: 'var(--h-mal)', estilo: 'stroke-width:5' });
    const txtProb = EF.svg('g', {}, gProb);
    texto(txtProb, 860, 206, 'Problema', 'font:800 27px var(--fuente)', 'var(--h-mal)');
    ['la escasa transparencia (caja negra)', 'incide en la baja trazabilidad', 'y verificabilidad']
      .forEach((l, k) => texto(txtProb, 860, 246 + k * 34, l, 'font:600 25px var(--fuente)', 'var(--texto)'));

    // la intervención: EduFEM actúa sobre la causa
    const gSol = EF.svg('g', {}, s);
    const flechaA = est(EF.svg('path', { d: 'M1384,470 Q1372,618 1264,620', 'marker-end': 'url(#h7-punta-gris)' }, gSol),
      { relleno: 'none', trazo: 'var(--texto-3)', estilo: 'stroke-width:4' });
    const flechaB = est(EF.svg('path', { d: 'M456,620 Q348,618 336,470', 'marker-end': 'url(#h7-punta-gris)' }, gSol),
      { relleno: 'none', trazo: 'var(--texto-3)', estilo: 'stroke-width:4' });
    const caja = EF.svg('g', {}, gSol);
    est(EF.svg('rect', { x: 470, y: 548, width: 780, height: 142, rx: 20 }, caja), { relleno: 'var(--h-int-suave)', trazo: 'var(--h-int)', estilo: 'stroke-width:4' });
    texto(caja, 860, 586, 'Variable interviniente (solución)', 'font:650 24px var(--fuente)', 'var(--texto-2)');
    texto(caja, 860, 634, 'EduFEM', 'font:850 42px var(--fuente)', 'var(--h-int)');
    texto(caja, 860, 672, 'desarrollado bajo un método de diseño de software educativo', 'font:600 24px var(--fuente)', 'var(--texto)');
    const txtInt = EF.svg('g', {}, gSol);
    const l1 = est(EF.svg('text', { x: 860, y: 430, 'text-anchor': 'middle' }, txtInt), { relleno: 'var(--texto)', estilo: 'font:600 25px var(--fuente)' });
    est(EF.svg('tspan', { text: 'Intervención: ' }, l1), { relleno: 'var(--h-int)', estilo: 'font-weight:800' });
    EF.svg('tspan', { text: 'el desarrollo de EduFEM pone el procedimiento' }, l1);
    texto(txtInt, 860, 464, 'a la vista. La hipótesis predice que permitirá mejorar', 'font:600 25px var(--fuente)', 'var(--texto)');
    texto(txtInt, 860, 498, 'la trazabilidad y la verificabilidad del análisis', 'font:600 25px var(--fuente)', 'var(--texto)');

    const op = (el, v) => { el.style.opacity = String(v); };
    const centro = (el, cx, cy, k) => el.setAttribute('transform', `translate(${cx},${cy}) scale(${k}) translate(${-cx},${-cy})`);
    const flechas = [[flechaProb, 'url(#h7-punta-mal)'], [flechaA, 'url(#h7-punta-gris)'], [flechaB, 'url(#h7-punta-gris)']];
    /** Estado final: todo a la vista y los niveles ya conmutados. */
    function fijar() {
      for (const el of [vi.g, vd.g, txtProb, gSol, caja, txtInt]) op(el, 1);
      op(gProb, 1);
      for (const [f, punta] of flechas) { f.style.strokeDasharray = ''; f.style.strokeDashoffset = ''; f.setAttribute('marker-end', punta); }
      caja.removeAttribute('transform'); vd.circ.removeAttribute('transform');
      nivel(vi, 0, 0); nivel(vi, 1, 1); nivel(vd, 0, 0); nivel(vd, 1, 1);
    }
    /** El problema, la intervención y el cambio de nivel, en ≈ 3,3 s. */
    function animar(an) {
      fijar();
      for (const el of [vi.g, vd.g, txtProb, gSol, caja, txtInt]) op(el, 0);
      op(gProb, 1);
      nivel(vi, 0, 1); nivel(vi, 1, 0); nivel(vd, 0, 1); nivel(vd, 1, 0);
      for (const [f] of flechas) ocultarTrazo(f);
      an.t({ dur: 480, retraso: 150, cada: (e) => op(vi.g, e) });
      an.t({ dur: 480, retraso: 380, cada: (e) => op(vd.g, e) });
      trazarConPunta(an, flechaProb, flechas[0][1], 820, 760);
      an.t({ dur: 450, retraso: 1180, cada: (e) => op(txtProb, e) });
      an.t({ dur: 10, retraso: 1640, fin: () => op(gSol, 1) });
      an.t({ dur: 460, retraso: 1640, curva: 'salePlus', cada: (e) => { op(caja, e); centro(caja, 860, 619, 0.86 + 0.14 * e); }, fin: () => caja.removeAttribute('transform') });
      trazarConPunta(an, flechaA, flechas[1][1], 1860, 560);
      trazarConPunta(an, flechaB, flechas[2][1], 2080, 560);
      an.t({ dur: 420, retraso: 1960, cada: (e) => op(txtInt, e) });
      // lo que la hipótesis predice: los niveles conmutan
      an.t({ dur: 420, retraso: 2560, cada: (e) => { nivel(vi, 0, 1 - e); nivel(vi, 1, e); } });
      an.t({ dur: 420, retraso: 2760, cada: (e) => { nivel(vd, 0, 1 - e); nivel(vd, 1, e); } });
      an.t({ dur: 560, retraso: 2760, curva: 'ambos', cada: (e) => centro(vd.circ, vd.cx, vd.cy, 1 + 0.06 * Math.sin(Math.PI * e)),
        fin: () => vd.circ.removeAttribute('transform') });
    }
    fijar();
    return { fijar, animar };
  }

  // ------------------------------------------------------------------ lámina 07 · hipótesis
  EF.registrarViz('h7-hipotesis', function (cont) {
    const an = animador();
    const P = cont.querySelector('.h7-enun');
    const R = cont.querySelector('.h7-partes');
    const E3 = cont.querySelector('.h7-efe3');
    const cnx = cont.querySelector('.h7-conect');
    const frags = Array.from(R.querySelectorAll('.h7-frag'));
    const rots = Array.from(R.querySelectorAll('.h7-rot'));
    const letras = Array.from(R.querySelectorAll('.h7-letra'));
    const nota = R.querySelector('.h7-nota');
    const glosa = R.querySelector('.h7-glosa');
    const vuelo = EF.el('div', { class: 'h7-vuelo' });
    cont.appendChild(vuelo);

    // el enunciado y sus partes, palabra por palabra (las mismas palabras, en el mismo orden)
    const wP = partirPalabras(P, 'h7-w', '.h7-comilla');
    const wR = [], parteDe = [];
    frags.forEach((f, j) => { for (const w of partirPalabras(f, 'h7-w', '.h7-letra')) { wR.push(w); parteDe.push(j); } });
    if (wP.length !== wR.length || wP.some((w, i) => w.textContent !== wR[i].textContent)) {
      console.warn('h7-hipotesis: el enunciado y sus partes no tienen las mismas palabras');
    }
    const primera = frags.map((f, j) => parteDe.indexOf(j));

    const fig = figuraVariables(cont.querySelector('.h7-fig'));

    // ---- paso 0: el enunciado entra palabra por palabra
    function entradaPalabras() {
      wP.forEach((w, i) => {
        w.style.opacity = '0';
        an.t({ dur: 340, retraso: 240 + i * 52, curva: 'sale', cada: (e) => { w.style.opacity = String(e); }, fin: () => { w.style.opacity = ''; } });
      });
    }

    // ---- paso 1: las palabras vuelan a sus filas y cada parte se subraya con su color
    function animarPartes() {
      const n = Math.min(wP.length, wR.length);
      const orig = wP.map((w) => posRel(w, cont));
      const { dest, lineas, tamR } = conFlujo([R], () => ({
        dest: wR.map((w) => posRel(w, cont)),
        lineas: frags.map((f) => lineasRel(f, R)),
        tamR: parseFloat(getComputedStyle(wR[0]).fontSize),
      }));
      const tamP = parseFloat(getComputedStyle(wP[0]).fontSize);
      const k = tamR / tamP;
      const colTexto = EF.css('--texto');
      for (const w of wP) w.style.visibility = 'hidden';
      for (const w of wR) w.style.visibility = 'hidden';
      for (const f of frags) { f.style.background = 'transparent'; f.style.borderBottomColor = 'transparent'; }
      for (const el of [...rots, ...letras, nota]) el.style.opacity = '0';
      glosa.style.textDecorationColor = 'transparent';   // su punteado se vería bajo el espacio entre palabras
      const PASO = 430;   // ms entre una parte y la siguiente: pocas palabras en el aire a la vez
      const VUELO = 850;
      const aterriza = frags.map(() => 0);
      for (let i = 0; i < n; i++) {
        const o = orig[i], d = dest[i], j = parteDe[i];
        const color = EF.css(COLOR[claseParte(frags[j])]);
        const c = EF.el('span', { class: 'h7-clon', text: wP[i].textContent });
        c.style.cssText = `left:${o.x}px;top:${o.y}px;font-size:${tamP}px;line-height:${o.h}px;transform-origin:0 0`;
        vuelo.appendChild(c);
        const ret = j * PASO + (i - primera[j]) * 16;
        aterriza[j] = Math.max(aterriza[j], ret + VUELO);
        an.t({
          dur: VUELO, retraso: ret, curva: 'ambos',
          cada: (e) => {
            c.style.transform = `translate(${(d.x - o.x) * e}px, ${(d.y - o.y) * e}px) scale(${1 + (k - 1) * e})`;
            c.style.color = EF.mezclar(colTexto, color, 0.9 * Math.sin(Math.PI * Math.min(1, e * 1.15)));
          },
          fin: () => { c.remove(); wR[i].style.visibility = ''; },
        });
      }
      // el rótulo de cada parte entra con sus palabras
      rots.forEach((r, j) => an.t({ dur: 460, retraso: j * PASO + 120, curva: 'sale',
        cada: (e) => { r.style.opacity = String(e); r.style.transform = `translateX(${-28 * (1 - e)}px)`; }, fin: () => limpiar(r) }));
      // el subrayado se dibuja cuando la parte termina de llegar
      frags.forEach((f, j) => {
        const rs = lineas[j];
        const total = rs.reduce((s, r) => s + r.w, 0) || 1;
        const t0 = aterriza[j] - 260;
        const cls = claseParte(f);
        const barras = rs.map((r) => {
          const b = EF.el('div', { class: 'h7-barra ' + cls });
          b.style.cssText = `left:${r.x}px;top:${r.y}px;width:0px;height:${r.h}px`;
          R.insertBefore(b, R.firstChild);
          return b;
        });
        let acum = 0;
        rs.forEach((r, q) => {
          const dur = 520 * r.w / total, ret = t0 + 520 * acum / total;
          acum += r.w;
          an.t({ dur: Math.max(dur, 1), retraso: ret, curva: 'lineal', cada: (e) => { barras[q].style.width = `${r.w * e}px`; } });
        });
        an.t({ dur: 1, retraso: t0 + 540, fin: () => { for (const b of barras) b.remove(); f.style.background = ''; f.style.borderBottomColor = ''; } });
      });
      // las dos cláusulas del efecto y la glosa de «el software»
      const tEfecto = aterriza[2];
      letras.forEach((l, q) => an.t({ dur: 440, retraso: tEfecto + 120 + q * 170, curva: 'rebote',
        cada: (e) => { l.style.opacity = String(Math.min(1, 2 * e)); l.style.transform = `scale(${0.35 + 0.65 * e})`; }, fin: () => limpiar(l) }));
      an.t({ dur: 1, retraso: aterriza[3], fin: () => { glosa.style.textDecorationColor = ''; } });
      an.t({ dur: 460, retraso: aterriza[3] + 260, curva: 'sale', cada: (e) => { nota.style.opacity = String(e); }, fin: () => limpiar(nota) });
    }

    // ---- paso 3: PI-1 y PI-2 cuelgan de las cláusulas (a) y (b)
    function conectores(animar) {
      cnx.innerHTML = '';
      const W = cont.offsetWidth, H = cont.offsetHeight;
      const s = EF.svg('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}` }, cnx);
      const m = EF.svg('marker', { id: 'h7-punta-vd', viewBox: '0 0 12 12', refX: 10, refY: 6, markerWidth: 5, markerHeight: 5, orient: 'auto-start-reverse' }, EF.svg('defs', {}, s));
      est(EF.svg('path', { d: 'M1,1 L11,6 L1,11 Z' }, m), { relleno: 'var(--h-vd)' });
      ['a', 'b'].forEach((cl, q) => {
        const a = posRel(E3.querySelector(`.h7-letra[data-cl="${cl}"]`), cont);
        const c = posRel(cont.querySelector(`.h7-pi[data-pi="${cl}"]`), cont);
        const x0 = a.x + a.w / 2, y0 = a.y + a.h + 8;
        const x1 = EF.clamp(x0, c.x + 90, c.x + c.w - 90), y1 = c.y - 6;
        let d;
        if (Math.abs(x1 - x0) < 3) d = `M${x0},${y0} L${x0},${y1}`;
        else {
          const ym = (y0 + y1) / 2, sg = Math.sign(x1 - x0);
          const r = Math.min(18, Math.abs(x1 - x0) / 2, (y1 - y0) / 4);
          d = `M${x0},${y0} L${x0},${ym - r} Q${x0},${ym} ${x0 + sg * r},${ym} L${x1 - sg * r},${ym} Q${x1},${ym} ${x1},${ym + r} L${x1},${y1}`;
        }
        const p = est(EF.svg('path', { d, 'marker-end': 'url(#h7-punta-vd)' }, s), { relleno: 'none', trazo: 'var(--h-vd)', estilo: 'stroke-width:4;stroke-linecap:round' });
        const punto = est(EF.svg('circle', { cx: x0, cy: y0, r: 6 }, s), { relleno: 'var(--h-vd)' });
        if (animar) {
          ocultarTrazo(p);
          punto.style.opacity = '0';
          an.t({ dur: 1, retraso: 300 + q * 300, fin: () => { punto.style.opacity = ''; } });
          trazarConPunta(an, p, 'url(#h7-punta-vd)', 300 + q * 300, 520);
        }
      });
    }

    // ---- estados fijos (al saltar de paso, al volver atrás, al imprimir)
    function estado(p) {
      an.parar();
      vuelo.innerHTML = '';
      for (const b of R.querySelectorAll('.h7-barra')) b.remove();
      for (const w of wP) { w.style.opacity = ''; w.style.visibility = ''; }
      for (const w of wR) w.style.visibility = '';
      for (const f of frags) { f.style.background = ''; f.style.borderBottomColor = ''; }
      for (const el of [...rots, ...letras, nota]) limpiar(el);
      glosa.style.textDecorationColor = '';
      fig.fijar();
      if (p >= 3) conectores(false); else cnx.innerHTML = '';
    }

    return {
      entrar(p, o) {
        estado(p);
        if (p === 0 && !o.instantaneo && !o.impresion) entradaPalabras();
      },
      paso(k, o) {
        if (!o.adelante) { estado(k); return; }
        estado(k - 1);
        if (k === 1) animarPartes();
        else if (k === 2) fig.animar(an);
        else if (k === 3) conectores(true);
      },
      salir() { an.parar(); },
    };
  });

  // ------------------------------------------------------------------ lámina 42 · contraste
  EF.registrarViz('c42-contraste', function (cont) {
    const an = animador();
    const items = {
      a: Array.from(cont.querySelectorAll('.c42-lista[data-c="a"] .c42-item')),
      b: Array.from(cont.querySelectorAll('.c42-lista[data-c="b"] .c42-item')),
    };
    const cuenta = { a: cont.querySelector('.c42-ver[data-c="a"] .c42-cuenta b'), b: cont.querySelector('.c42-ver[data-c="b"] .c42-cuenta b') };
    const selloEf = { a: cont.querySelector('.c42-ver[data-c="a"] .l4-sello'), b: cont.querySelector('.c42-ver[data-c="b"] .l4-sello') };
    const sellosPrem = Array.from(cont.querySelectorAll('.c42-ver[data-prem] .l4-sello'));
    const terms = Array.from(cont.querySelectorAll('.c42-term'));
    const opFin = cont.querySelector('.c42-op.fin');
    const sello = cont.querySelector('.c42-sello');
    const anillo = cont.querySelector('.c42-anillo');
    // foco: en cada paso quedan en primer plano las filas de las que se habla
    // (filas: condición, intervención, efecto (a), efecto (b), antecedente)
    const filas = Array.from(cont.querySelectorAll('.c42-fila'));
    const ACTIVAS = { 0: [0, 1, 2, 3, 4], 1: [0, 1, 4], 2: [2], 3: [3], 4: [0, 1, 2, 3, 4] };
    const TENUE = 0.4;
    const vuelo = EF.el('div', { class: 'c42-vuelo' });
    cont.appendChild(vuelo);

    // paso 4: el clímax. Se atenúan la parte y la evidencia de cada fila y quedan a plena
    // intensidad los cinco veredictos, que conducen a la regla conjuntiva y al sello.
    const columnas = Array.from(cont.querySelectorAll('.c42-fila .c42-parte, .c42-fila .c42-evid'));
    const TENUE_FINAL = 0.35;
    function atenuarColumnas(on, animar) {
      const meta = on ? TENUE_FINAL : 1;
      columnas.forEach((el) => {
        const ini = el.style.opacity === '' ? 1 : Number(el.style.opacity);
        if (!animar || Math.abs(ini - meta) < 0.01) { el.style.opacity = on ? String(meta) : ''; return; }
        an.t({ dur: 520, curva: 'sale', cada: (e) => { el.style.opacity = String(ini + (meta - ini) * e); },
          fin: () => { el.style.opacity = on ? String(meta) : ''; } });
      });
    }
    function foco(p, animar) {
      atenuarColumnas(p >= 4, animar);
      filas.forEach((f, j) => {
        const meta = (ACTIVAS[p] || ACTIVAS[0]).includes(j) ? 1 : TENUE;
        if (!animar) { f.style.opacity = meta === 1 ? '' : String(meta); return; }
        const ini = f.style.opacity === '' ? 1 : Number(f.style.opacity);
        if (Math.abs(ini - meta) < 0.01) return;
        an.t({ dur: 450, curva: 'sale', cada: (e) => { f.style.opacity = String(ini + (meta - ini) * e); },
          fin: () => { f.style.opacity = meta === 1 ? '' : String(meta); } });
      });
    }
    function marcar(c, n) {
      items[c].forEach((it, j) => { it.classList.toggle('hecho', j < n); it.querySelector('.c42-caja').style.transform = ''; });
      cuenta[c].textContent = String(n);
    }
    function estado(p) {
      an.parar();
      marcar('a', p >= 2 ? items.a.length : 0);
      marcar('b', p >= 3 ? items.b.length : 0);
      for (const el of [selloEf.a, selloEf.b, sello, opFin, ...sellosPrem, ...terms]) limpiar(el);
      terms.forEach((t) => t.classList.toggle('encendido', p >= 4));
      anillo.style.opacity = '0'; anillo.style.transform = '';
      vuelo.innerHTML = '';
      foco(p, false);
    }
    /** Los criterios de una cláusula se marcan uno a uno; al final, «Se cumple». */
    function animarClausula(c, intervalo) {
      const its = items[c], s = selloEf[c];
      marcar(c, 0);
      s.style.opacity = '0';
      const t0 = 760;
      its.forEach((it, j) => {
        const caja = it.querySelector('.c42-caja');
        let hecho = false;
        an.t({ dur: 300, retraso: t0 + j * intervalo, curva: 'sale',
          cada: (e) => {
            if (!hecho) { hecho = true; it.classList.add('hecho'); cuenta[c].textContent = String(j + 1); }
            caja.style.transform = `scale(${1.6 - 0.6 * e})`;
          },
          fin: () => { caja.style.transform = ''; } });
      });
      const tf = t0 + (its.length - 1) * intervalo + 320;
      an.t({ dur: 480, retraso: tf, curva: 'rebote',
        cada: (e) => { s.style.opacity = String(Math.min(1, 2.5 * e)); s.style.transform = `scale(${0.5 + 0.5 * e})`; }, fin: () => limpiar(s) });
    }
    /** Regla conjuntiva: cada veredicto viaja de la tabla a su término, y cae el sello. */
    function animarRegla() {
      terms.forEach((t) => t.classList.remove('encendido'));
      sello.style.opacity = '0';
      const grupos = [[terms[0], sellosPrem], [terms[1], [selloEf.a]], [terms[2], [selloEf.b]]];
      const VIAJE = 640;
      grupos.forEach(([t, pills], j) => {
        const t0 = 250 + j * 330;
        const dest = posRel(t, cont);
        // una copia de cada veredicto sale de su fila y se funde en el término de la regla
        pills.forEach((q, m) => {
          const o = posRel(q, cont);
          const caja = EF.el('div', { class: 'c42-ver c42-volador' });
          caja.style.cssText = `left:${o.x}px;top:${o.y}px;opacity:0`;
          caja.appendChild(q.cloneNode(true));
          vuelo.appendChild(caja);
          const dx = dest.x + dest.w / 2 - (o.x + o.w / 2), dy = dest.y + dest.h / 2 - (o.y + o.h / 2);
          an.t({ dur: VIAJE, retraso: t0 + m * 70, curva: 'ambos',
            cada: (e) => {
              caja.style.opacity = String(e < 0.8 ? 1 : (1 - e) * 5);
              caja.style.transform = `translate(${dx * e}px, ${dy * e}px) scale(${1 - 0.25 * e})`;
            },
            fin: () => caja.remove() });
        });
        let on = false;
        an.t({ dur: 420, retraso: t0 + VIAJE - 120 + (pills.length - 1) * 70, curva: 'sale',
          cada: (e) => {
            if (!on) { on = true; t.classList.add('encendido'); }
            t.style.transform = `scale(${1 + 0.14 * Math.sin(Math.PI * e)})`;
          },
          fin: () => limpiar(t) });
      });
      an.t({ dur: 360, retraso: 1720, curva: 'sale', cada: (e) => { opFin.style.transform = `scale(${1 + 0.35 * Math.sin(Math.PI * e)})`; }, fin: () => limpiar(opFin) });
      // el sello cae desde arriba, grande e inclinado, y asienta con un golpe
      const T = 1880, D = 560;
      an.t({ dur: D, retraso: T, curva: 'entra',
        cada: (e) => {
          sello.style.opacity = String(Math.min(1, 2.2 * e));
          sello.style.transform = `translateY(${-60 * (1 - e)}px) rotate(${-9 * (1 - e)}deg) scale(${1 + 0.75 * (1 - e)})`;
        },
        fin: () => limpiar(sello) });
      an.t({ dur: 160, retraso: T + D, cada: (e) => { sello.style.transform = `scale(${1 - 0.06 * Math.sin(Math.PI * e)})`; }, fin: () => limpiar(sello) });
      an.t({ dur: 700, retraso: T + D, curva: 'sale',
        cada: (e) => {
          const w = anillo.offsetWidth || 1, h = anillo.offsetHeight || 1;
          anillo.style.opacity = String(0.8 * (1 - e));
          anillo.style.transform = `scale(${1 + (70 * e) / w}, ${1 + (70 * e) / h})`;
        },
        fin: () => { anillo.style.opacity = '0'; anillo.style.transform = ''; } });
    }
    return {
      entrar(p, o) { estado(p); if (o && o.impresion) foco(4, false); },
      paso(k, o) {
        if (!o.adelante) { estado(k); return; }
        estado(k - 1);
        foco(k, true);
        if (k === 2) animarClausula('a', 300);
        else if (k === 3) animarClausula('b', 235);
        else if (k === 4) animarRegla();
      },
      salir() { an.parar(); },
    };
  });
})();
