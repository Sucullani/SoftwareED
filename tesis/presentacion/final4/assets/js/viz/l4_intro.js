/* =====================================================================
   viz/l4_intro.js — introducción, separadores y cierre (final4).
     cajanegra4   la caja negra que se abre (copia de 'cajanegra' de intro.js,
                  con la segunda pregunta en los términos de final4)
     icono-traza  ícono animado de la trazabilidad: el camino de vuelta hasta los datos
     icono-verif  ícono animado de la verificabilidad: valor contra patrón, con tolerancia
     ciclo-dsr    las seis actividades de la ciencia del diseño, que se encienden en orden
     ruta-agenda  la línea que une las cinco estaciones del recorrido
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const est = (e, o) => EF.estiloSvg(e, o);

  // ------------------------------------------------------------------ caja negra
  EF.registrarViz('cajanegra4', function (cont) {
    const W = 1720, H = 500;
    const s = EF.svg('svg', { class: 'viz', width: W, height: H, viewBox: `0 0 ${W} ${H}`, style: 'position:absolute;left:0;top:0;overflow:visible' }, cont);
    const g = EF.svg('g', {}, s);
    const entradas = [
      { t: 'Geometría y malla', s: 'nodos · elementos', y: 30, ico: 'malla' },
      { t: 'Material', s: ['E · ', 'ν', ' · espesor t'], y: 191, ico: 'mat' },
      { t: 'Cargas y apoyos', s: 'fuerzas · restricciones', y: 352, ico: 'carga' },
    ];
    for (const e of entradas) {
      const gg = EF.svg('g', { transform: `translate(0,${e.y})` }, g);
      est(EF.svg('rect', { x: 0, y: 0, width: 340, height: 118, rx: 20 }, gg), { relleno: 'var(--superficie-2)', trazo: 'var(--linea-2)', estilo: 'stroke-width:1.5' });
      est(EF.svg('text', { x: 104, y: 52, text: e.t }, gg), { relleno: 'var(--texto)', estilo: 'font:750 27px var(--fuente)' });
      const sub = EF.svg('text', { x: 104, y: 88 }, gg);
      est(sub, { relleno: 'var(--texto-3)', estilo: 'font:600 22px var(--fuente)' });
      // ν en letra matemática: en Calibri se confunde con una «v»
      for (const [k, parte] of [].concat(e.s).entries()) {
        const ts = EF.svg('tspan', { text: parte }, sub);
        if (k === 1) ts.setAttribute('style', "font-family:KaTeX_Math,'Cambria Math',serif;font-style:italic");
      }
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
      const p = EF.svg('path', { d: `M348,${e.y + 59} C400,${e.y + 59} 400,250 440,250` }, g);
      est(p, { trazo: 'var(--texto-3)', relleno: 'none', estilo: 'stroke-width:3;stroke-dasharray:8 8' });
      flechas.push(p);
    }
    const salida = EF.svg('path', { d: 'M858,250 L950,250' }, g);
    est(salida, { trazo: 'var(--texto-3)', relleno: 'none', estilo: 'stroke-width:3;stroke-dasharray:8 8' });
    est(EF.svg('path', { d: 'M944,238 L964,250 L944,262 Z' }, g), { relleno: 'var(--texto-3)' });
    flechas.push(salida);

    // caja: interior (las nueve etapas) + frente opaco que se abre como una persiana
    const caja = EF.svg('g', {}, g);
    const borde = EF.svg('rect', { x: 450, y: 50, width: 400, height: 400, rx: 26 }, caja);
    est(borde, { relleno: 'var(--superficie)', trazo: 'var(--linea-2)', estilo: 'stroke-width:2' });
    const interior = EF.svg('g', {}, caja);
    // nueve etapas, numeradas y con su símbolo (los nombres llegan en la lámina «procedimiento»)
    const SIMB = [['N'], ['J'], ['B'], ['D'], ['k', 'e'], ['f'], ['K'], ['u'], ['σ']];
    const chips = [];
    EF.ETAPAS.forEach((et, k) => {
      const col = k % 3, fila = Math.floor(k / 3);
      const x = 464 + col * 128, y = 124 + fila * 108;
      const gc = EF.svg('g', { transform: `translate(${x},${y})` }, interior);
      est(EF.svg('rect', { x: 0, y: 0, width: 116, height: 98, rx: 13 }, gc), { relleno: 'var(--acento-suave)', trazo: 'var(--acento)', estilo: 'stroke-width:1.5' });
      est(EF.svg('text', { x: 12, y: 32, text: String(et.n) }, gc), { relleno: 'var(--acento)', estilo: 'font:850 28px var(--fuente)' });
      const sim = EF.svg('text', { x: 66, y: 76, 'text-anchor': 'middle' }, gc);
      est(sim, { relleno: 'var(--texto)', estilo: "font:italic 700 44px KaTeX_Math,'Cambria Math',serif" });
      const [base, subi] = SIMB[k];
      EF.svg('tspan', { text: base }, sim);
      if (subi) { const ts = EF.svg('tspan', { text: subi, 'baseline-shift': 'sub' }, sim); ts.setAttribute('font-size', '62%'); }
      chips.push(gc);
    });
    est(EF.svg('text', { x: 650, y: 98, 'text-anchor': 'middle', text: 'Procedimiento a la vista' }, interior), { relleno: 'var(--acento)', estilo: 'font:800 26px var(--fuente)' });
    const frente = EF.svg('g', {}, caja);
    est(EF.svg('rect', { x: 450, y: 50, width: 400, height: 400, rx: 26 }, frente), { relleno: '#05070c', trazo: '#2a3550', estilo: 'stroke-width:2' });
    est(EF.svg('text', { x: 650, y: 245, 'text-anchor': 'middle', text: '?' }, frente), { relleno: '#1e2840', estilo: 'font:900 190px var(--fuente)' });
    est(EF.svg('text', { x: 650, y: 360, 'text-anchor': 'middle', text: 'Software de análisis' }, frente), { relleno: '#c5d0e6', estilo: 'font:750 29px var(--fuente)' });
    est(EF.svg('text', { x: 650, y: 398, 'text-anchor': 'middle', text: '(caja negra)' }, frente), { relleno: '#8a99b8', estilo: 'font:650 24px var(--fuente)' });
    const clip = EF.svg('clipPath', { id: 'clipFrente4' }, EF.svg('defs', {}, s));
    const clipR = EF.svg('rect', { x: 450, y: 50, width: 400, height: 400 }, clip);
    frente.setAttribute('clip-path', 'url(#clipFrente4)');

    // resultado: contorno real del ejemplo guía (post-proceso de EduFEM)
    const res = EF.el('div', { style: 'position:absolute;left:970px;top:90px;width:380px;height:320px;border-radius:18px;overflow:hidden;border:1px solid var(--linea-2);box-shadow:var(--sombra-s)' });
    cont.appendChild(res);
    const mini = EF.miniaturaCanonico(res, 380, 320, { escala: 60, pad: 20 });
    cont.appendChild(EF.el('div', { style: 'position:absolute;left:970px;top:424px;width:380px;text-align:center;font:650 24px var(--fuente);color:var(--texto-3)', text: 'Resultado: contorno de tensiones' }));

    cont.append(
      EF.el('div', { class: 'pregunta', 'data-paso': '1', style: 'left:1380px;top:60px;width:340px', html: '¿De dónde sale <b>esta tensión nodal</b>?' }),
      EF.el('div', { class: 'pregunta', 'data-paso': '1', 'data-retraso': '350', style: 'left:1380px;top:220px;width:340px', html: '¿Cierran las tensiones de los nodos con las del <b>interior de los elementos</b>?' }),
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
    // «esta tensión nodal»: desde el paso 1, el nodo 7 (el que la lámina «trazabilidad» sigue hasta sus datos)
    let pasoActual = 0;
    function dibujarMini() {
      mini.dibujar();
      if (pasoActual < 1) return;
      const P = EF.LienzoMEF.pos(mini.nodos, mini.u, 60, mini.idx[7]);
      const c = mini.lz.ctx;
      c.save();
      c.lineWidth = 4; c.strokeStyle = EF.css('--acento');
      c.beginPath(); c.arc(mini.lz.X(P[0]), mini.lz.Y(P[1]), 15, 0, 2 * Math.PI); c.stroke();
      c.restore();
      mini.lz.etiqueta(P[0], P[1], 'nodo 7', { dx: -24, dy: -30, ancla: 'right', tam: 20, color: EF.css('--texto'), fondo: EF.css('--superficie'), borde: EF.css('--acento'), alfaFondo: 1 });
    }
    return {
      entrar(p, op) {
        pasoActual = p;
        dibujarMini();
        if (p >= 3) abrir(false); else fijarApertura(0);
        if (!op.instantaneo && !op.impresion && p < 3) flujo();
      },
      paso(k, op) {
        pasoActual = k;
        dibujarMini();
        if (k === 3 && op.adelante) abrir(true);
        else if (k >= 3) abrir(false);
        else fijarApertura(0);
      },
      tema() { dibujarMini(); },
      redimensionar() { dibujarMini(); },
    };
  });

  // ------------------------------------------------------------------ íconos de las dos definiciones
  // Se animan cuando llega el paso que los muestra (paso 2 del problema) y quedan quietos después.
  function icono(cont, construir) {
    const W = 120, H = 120;
    const s = EF.svg('svg', { class: 'viz', width: W, height: H, viewBox: `0 0 ${W} ${H}`, style: 'display:block' }, cont);
    const api = construir(s);
    let tw = null;
    function animar() { if (tw) tw.cancelar(false); api.fijar(0); tw = EF.tween({ dur: 1800, retraso: 300, curva: 'ambos', cada: (e) => api.fijar(e) }); }
    return {
      entrar(p, op) { if (op.impresion || op.instantaneo || p !== 2) api.fijar(p >= 2 ? 1 : 0); else animar(); },
      paso(k, op) { if (k === 2 && op.adelante) animar(); else api.fijar(k >= 2 ? 1 : 0); },
    };
  }

  EF.registrarViz('icono-traza', function (cont) {
    return icono(cont, (s) => {
      est(EF.svg('rect', { x: 2, y: 2, width: 116, height: 116, rx: 26 }, s), { relleno: 'var(--h-vd-suave)' });
      // cuatro eslabones: resultado (derecha) ... datos (izquierda)
      const xs = [100, 76, 52, 30], y = 56;
      const linea = EF.svg('path', { d: `M${xs[0]},${y} L${xs[3]},${y}` }, s);
      est(linea, { trazo: 'var(--h-vd)', relleno: 'none', estilo: 'stroke-width:4;stroke-linecap:round' });
      const L = 70;
      const nodos = xs.map((x, k) => { const c = EF.svg('circle', { cx: x, cy: y, r: k === 3 ? 9 : 7 }, s); est(c, { relleno: k === 3 ? 'var(--h-vd)' : 'var(--superficie)', trazo: 'var(--h-vd)', estilo: 'stroke-width:3.5' }); return c; });
      const cabeza = EF.svg('path', { d: 'M0,-9 L-13,0 L0,9 Z' }, s);
      est(cabeza, { relleno: 'var(--h-vd)' });
      const tx = EF.svg('text', { x: 36, y: 98, 'text-anchor': 'middle', text: 'datos' }, s);
      est(tx, { relleno: 'var(--h-vd)', estilo: 'font:800 22px var(--fuente)' });
      return {
        fijar(e) {
          linea.style.strokeDasharray = `${L} ${L}`;
          linea.style.strokeDashoffset = String(L * (1 - e));
          const x = xs[0] - (xs[0] - xs[3]) * e;
          cabeza.setAttribute('transform', `translate(${x - 4},${y})`);
          nodos.forEach((c, k) => { c.style.opacity = e * 3 >= k ? '1' : '.25'; });
          tx.style.opacity = String(EF.clamp((e - 0.8) * 5, 0, 1));
        },
      };
    });
  });

  EF.registrarViz('icono-verif', function (cont) {
    return icono(cont, (s) => {
      est(EF.svg('rect', { x: 2, y: 2, width: 116, height: 116, rx: 26 }, s), { relleno: 'var(--h-vd-suave)' });
      // eje, banda de tolerancia alrededor del patrón y un valor que cae dentro
      est(EF.svg('line', { x1: 16, y1: 84, x2: 104, y2: 84 }, s), { trazo: 'var(--texto-3)', estilo: 'stroke-width:2.5' });
      est(EF.svg('rect', { x: 46, y: 30, width: 28, height: 54, rx: 4 }, s), { relleno: 'var(--h-ok-suave)', trazo: 'var(--h-ok)', estilo: 'stroke-width:2' });
      est(EF.svg('line', { x1: 60, y1: 26, x2: 60, y2: 88 }, s), { trazo: 'var(--h-ok)', estilo: 'stroke-width:2.5;stroke-dasharray:5 4' });
      const p = EF.svg('circle', { cx: 20, cy: 50, r: 8 }, s);
      est(p, { relleno: 'var(--h-vd)' });
      const ok = EF.svg('path', { d: 'M44 104 L54 112 L76 92' }, s);
      est(ok, { trazo: 'var(--h-ok)', relleno: 'none', estilo: 'stroke-width:6;stroke-linecap:round;stroke-linejoin:round' });
      return {
        fijar(e) {
          const x = 20 + (63 - 20) * EF.suave.sale(EF.clamp(e * 1.25, 0, 1));
          p.setAttribute('cx', String(x));
          ok.style.opacity = String(EF.clamp((e - 0.75) * 4, 0, 1));
        },
      };
    });
  });

  // ------------------------------------------------------------------ las seis actividades, en orden
  EF.registrarViz('ciclo-dsr', function (cont) {
    const acts = Array.from(cont.querySelectorAll('.act'));
    function fijar(k) { acts.forEach((a, j) => { a.classList.toggle('encendida', j <= k); a.classList.toggle('foco', j === k); }); }
    let tws = [];
    function recorrer() {
      tws.forEach((t) => t.cancelar(false)); tws = [];
      fijar(-1);
      acts.forEach((a, j) => tws.push(EF.tween({ dur: 10, retraso: 400 + j * 360, fin: () => fijar(j) })));
      tws.push(EF.tween({ dur: 10, retraso: 400 + acts.length * 360 + 200, fin: () => { acts.forEach((a) => a.classList.remove('foco')); } }));
    }
    function final() { fijar(acts.length - 1); acts.forEach((a) => a.classList.remove('foco')); }
    return {
      entrar(p, op) { if (p >= 1) final(); else fijar(-1); },
      paso(k, op) { if (k === 1 && op.adelante) recorrer(); else if (k >= 1) final(); else fijar(-1); },
    };
  });

  // ------------------------------------------------------------------ recorrido de la defensa
  EF.registrarViz('ruta-agenda', function (cont) {
    const est5 = Array.from(cont.querySelectorAll('.estacion'));
    const linea = EF.el('div', { class: 'ruta-linea' });
    const avance = EF.el('i');
    linea.appendChild(avance);
    cont.prepend(linea);
    return {
      entrar(p, op) {
        if (op.instantaneo || op.impresion) { avance.style.width = '100%'; return; }
        avance.style.width = '0%';
        EF.tween({ dur: 1500, retraso: 300, curva: 'ambos', cada: (e) => { avance.style.width = `${e * 100}%`; } });
        void est5;
      },
    };
  });
})();
