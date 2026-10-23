/* =====================================================================
   viz/l4_conclusiones.js — visualizaciones del grupo «conclusiones» (final4).

   c41-objetivos  lámina 41. El objetivo general entra con su sello «Cumplido». En cada paso
                  se da vuelta la tarjeta de un objetivo específico: el frente es el objetivo
                  (como en la lámina 06); el dorso, su conclusión con la fórmula del documento
                  («De … (Capítulo N) se concluye que…»), su evidencia y su sello. El contador
                  llega a 3 de 3.
   c43-margen     lámina 43. Alrededor de la Figura CR.2 (la dibuja «figdoc», tal cual): el
                  contador de los puntos que llegan a su lugar, el resaltado de la fila más
                  ajustada (σx frente a SAP2000) y su llamada.
   c44-respuesta  lámina 44. La cadena datos → nueve etapas → resultado. Con la caja negra, el
                  camino de vuelta se corta y solo el resultado final se comprueba; al abrirse,
                  el camino llega a los datos y cada magnitud se comprueba. Después, PI-1 y PI-2
                  respondidas.
   c45-ruta       lámina 45. Una vía por capítulo que se dibuja hasta sus recomendaciones.

   Todo lo que se mueve pasa por EF.tween (reloj virtual del video). Los colores son variables
   CSS: la versión oscura y la clara se leen igual.
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const S = EF.svg;
  const est = (e, o) => EF.estiloSvg(e, o);

  // ------------------------------------------------------------------ utilidades
  /** Junta las animaciones de una lámina para cortarlas al cambiar de paso. */
  function animador() {
    let lista = [];
    return {
      t(op) { const tw = EF.tween(op); lista.push(tw); return tw; },
      parar() { const l = lista; lista = []; for (const tw of l) tw.cancelar(false); },
    };
  }
  const limpiar = (el) => { if (el) { el.style.opacity = ''; el.style.transform = ''; } };
  const op = (el, v) => { el.style.opacity = String(v); };

  function linea(g, d, color, ancho, extra) {
    return est(S('path', { d }, g), { trazo: color, relleno: 'none', estilo: `stroke-width:${ancho};stroke-linecap:round;stroke-linejoin:round${extra ? ';' + extra : ''}` });
  }
  function forma(g, d, relleno, trazo, ancho) {
    return est(S('path', { d }, g), { relleno: relleno || 'none', trazo: trazo || 'none', estilo: `stroke-width:${ancho || 0};stroke-linejoin:round` });
  }
  function circ(g, x, y, r, relleno, trazo, ancho) {
    return est(S('circle', { cx: x, cy: y, r }, g), { relleno: relleno || 'none', trazo: trazo || 'none', estilo: `stroke-width:${ancho || 0}` });
  }
  function rect(g, x, y, w, h, rx, relleno, trazo, ancho) {
    return est(S('rect', { x, y, width: w, height: h, rx }, g), { relleno: relleno || 'none', trazo: trazo || 'none', estilo: `stroke-width:${ancho || 0}` });
  }
  function texto(g, x, y, t, estilo, color, ancla) {
    return est(S('text', { x, y, 'text-anchor': ancla || 'middle', text: t }, g), { relleno: color || 'var(--texto)', estilo });
  }
  /** Longitud de un trazo, para dibujarlo con stroke-dashoffset. */
  function largo(p) { try { return p.getTotalLength() || 1; } catch (e) { return 1000; } }
  function trazoParcial(p, f) {
    const L = largo(p);
    p.style.strokeDasharray = `${L} ${L}`;
    p.style.strokeDashoffset = String(L * (1 - EF.clamp(f, 0, 1)));
  }
  function trazoEntero(p) { p.style.strokeDasharray = ''; p.style.strokeDashoffset = ''; }
  /** Aparición con rebote (sellos, marcas): escala desde k0 hasta 1. */
  function rebote(an, el, retraso, k0, dur) {
    op(el, 0);
    an.t({ dur: dur || 460, retraso, curva: 'rebote',
      cada: (e) => { op(el, Math.min(1, 2.4 * e)); el.style.transform = `scale(${k0 + (1 - k0) * e})`; },
      fin: () => limpiar(el) });
  }
  /** Lo mismo para un grupo SVG (transform como atributo, con su centro). */
  function reboteSvg(an, g, cx, cy, retraso, k0) {
    g.style.opacity = '0';
    an.t({ dur: 440, retraso, curva: 'rebote',
      cada: (e) => { g.style.opacity = String(Math.min(1, 2.4 * e)); g.setAttribute('transform', `translate(${cx},${cy}) scale(${k0 + (1 - k0) * e}) translate(${-cx},${-cy})`); },
      fin: () => { g.removeAttribute('transform'); g.style.opacity = ''; } });
  }

  // ------------------------------------------------------------------ íconos (48 × 48)
  // Dibujos simples, con los colores del tema; se insertan en cada <i data-ico="…">.
  const ICONOS = {
    caja(g) {
      rect(g, 7, 9, 34, 30, 6, 'var(--c4-negro)', 'var(--c4-negro-borde)', 1.5);
      texto(g, 24, 32, '?', 'font:900 21px var(--fuente)', 'var(--c4-negro-texto)');
    },
    matriz(g) {   // ningún recurso reúne todos los atributos: a cada columna le falta uno
      const falta = [2, 0, 1];
      for (let c = 0; c < 3; c++) for (let f = 0; f < 3; f++) {
        const x = 7 + c * 12.5, y = 7 + f * 12.5;
        if (falta[c] === f) {
          rect(g, x, y, 10, 10, 2, 'none', 'var(--h-mal)', 1.8);
          linea(g, `M${x + 2.5} ${y + 2.5} L${x + 7.5} ${y + 7.5} M${x + 7.5} ${y + 2.5} L${x + 2.5} ${y + 7.5}`, 'var(--h-mal)', 1.8);
        } else rect(g, x, y, 10, 10, 2, 'var(--h-ok)');
      }
    },
    modulos(g) { [[17, 7], [12, 16], [7, 25]].forEach(([x, y]) => rect(g, x, y, 25, 16, 4, 'var(--superficie)', 'var(--acento)', 2.6)); },
    post(g) {
      ['var(--h-vi)', 'var(--cian)', 'var(--h-ok)', 'var(--aviso)', 'var(--h-mal)'].forEach((c, k) => rect(g, 7 + k * 6.8, 11, 7, 26, 0, c));
      rect(g, 6, 10, 36, 28, 3, 'none', 'var(--texto-2)', 2.2);
      circ(g, 33, 18, 4.5, 'var(--superficie)', 'var(--texto)', 2.2);
    },
    memoria(g) {
      forma(g, 'M12 5 H30 L38 13 V43 H12 Z', 'var(--superficie)', 'var(--texto-2)', 2.4);
      linea(g, 'M30 5 V13 H38', 'var(--texto-2)', 2.4);
      linea(g, 'M17 21 H33 M17 27 H33 M17 33 H27', 'var(--primario)', 2.6);
    },
    traza(g) {
      linea(g, 'M40 14 H12', 'var(--h-vd)', 3);
      forma(g, 'M5 14 L13 8.5 L13 19.5 Z', 'var(--h-vd)');
      [38, 29, 20].forEach((x) => circ(g, x, 14, 3.6, 'var(--superficie)', 'var(--h-vd)', 2.4));
      linea(g, 'M13 32 L20 39 L35 25', 'var(--h-ok)', 4.4);
    },
    margen(g) {
      rect(g, 36, 5, 9, 38, 0, 'var(--superficie-3)');
      linea(g, 'M36 5 V43', 'var(--texto)', 2.4);
      [[15, 13], [25, 24], [10, 35]].forEach(([x, y]) => { linea(g, `M4 ${y} H${x}`, 'var(--linea-2)', 2); circ(g, x, y, 4, 'var(--primario)'); });
    },
    preguntas(g) {
      forma(g, 'M10 7 H36 Q41 7 41 12 V27 Q41 32 36 32 H20 L11 39 V32 H10 Q5 32 5 27 V12 Q5 7 10 7 Z', 'var(--h-vd-suave)', 'var(--h-vd)', 2.4);
      texto(g, 23, 27, '?', 'font:900 18px var(--fuente)', 'var(--h-vd)');
      circ(g, 37, 37, 8.5, 'var(--h-ok)');
      linea(g, 'M33 37 L36 40 L41.5 34', 'var(--fondo)', 2.6);
    },
    doc(g) {
      forma(g, 'M12 5 H29 L37 13 V43 H12 Z', 'none', 'var(--texto-3)', 3.2);
      linea(g, 'M17 22 H31 M17 29 H31 M17 36 H25', 'var(--texto-3)', 3.2);
    },
    cociente(g) { circ(g, 24, 12, 4.5, 'var(--primario)'); linea(g, 'M9 24 H39', 'var(--primario)', 3.8); circ(g, 24, 36, 4.5, 'var(--primario)'); },
    izquierda(g) {
      rect(g, 33, 6, 11, 36, 0, 'var(--superficie-3)');
      linea(g, 'M33 6 V42', 'var(--texto)', 3);
      linea(g, 'M28 24 H11', 'var(--h-ok)', 3.8);
      forma(g, 'M5 24 L13 17.5 L13 30.5 Z', 'var(--h-ok)');
    },
    log(g) {
      linea(g, 'M4 37 H44', 'var(--texto-2)', 2.4);
      [6, 18, 30, 42].forEach((x) => linea(g, `M${x} 32 V42`, 'var(--texto-2)', 2.4));
      [[6, 18], [18, 30], [30, 42]].forEach(([a, b]) => forma(g, `M${a + 1.5} 28 Q${(a + b) / 2} 12 ${b - 1.5} 28`, 'none', 'var(--primario)', 2.6));
    },
    lupa(g) { circ(g, 20, 20, 12, 'var(--superficie)', 'var(--texto-2)', 3.6); linea(g, 'M29 29 L41 41', 'var(--texto-2)', 5.6); circ(g, 20, 20, 4.6, 'var(--h-mal)'); },
    autor(g) { circ(g, 24, 15, 7.5, 'var(--aviso)'); forma(g, 'M9 41 Q9 26 24 26 Q39 26 39 41 Z', 'var(--aviso)'); },
    presa(g) {
      rect(g, 4, 18, 13, 24, 0, 'var(--h-vi-suave)');
      linea(g, 'M6 23 H15 M6 29 H15 M6 35 H15', 'var(--h-vi)', 2.2);
      forma(g, 'M17 8 H24 L39 42 H17 Z', 'var(--aviso)');
      linea(g, 'M2 42 H46', 'var(--texto-2)', 2.4);
    },
    ruta(g) {
      linea(g, 'M24 43 V29 M24 29 Q24 21 13 12 M24 29 Q24 21 35 12', 'var(--aviso)', 3.4, 'stroke-dasharray:5 4');
      circ(g, 13, 11, 4.4, 'var(--aviso)'); circ(g, 35, 11, 4.4, 'var(--aviso)'); circ(g, 24, 43, 3.6, 'var(--aviso)');
    },
    bloqueo(g) {
      forma(g, 'M5 37 L12 12 H33 L26 37 Z', 'var(--acento-suave)', 'var(--acento)', 2.6);
      forma(g, 'M31 27 V22 Q36.5 14 42 22 V27', 'none', 'var(--acento)', 2.8);
      rect(g, 28, 26, 17, 15, 3, 'var(--acento)');
    },
    elementos(g) {
      forma(g, 'M3 40 L14 12 L25 40 Z', 'var(--acento-suave)', 'var(--acento)', 2.4);
      rect(g, 27, 16, 17, 17, 2, 'var(--acento-suave)', 'var(--acento)', 2.4);
      [[27, 16], [35.5, 16], [44, 16], [44, 24.5], [44, 33], [35.5, 33], [27, 33], [27, 24.5]].forEach(([x, y]) => circ(g, x, y, 2.4, 'var(--acento)'));
    },
    malla(g) {
      forma(g, 'M8 38 Q3 18 18 8 Q34 2 41 16 Q46 32 30 41 Q17 46 8 38 Z', 'var(--acento-suave)', 'var(--acento)', 2.4);
      linea(g, 'M18 8 L22 25 L41 16 M22 25 L8 38 M22 25 L30 41 M22 25 L5 22', 'var(--acento)', 1.8);
    },
    grande(g) {
      rect(g, 4, 7, 30, 30, 2, 'none', 'var(--acento)', 2.2);
      for (let k = 1; k < 5; k++) linea(g, `M${4 + 6 * k} 7 V37 M4 ${7 + 6 * k} H34`, 'var(--acento)', 1.3);
      linea(g, 'M37 15 L44 22 L37 29', 'var(--acento)', 3.2);
    },
    guia(g) {
      forma(g, 'M24 14 Q14 8 4 10 V38 Q14 36 24 42 Q34 36 44 38 V10 Q34 8 24 14 Z', 'var(--acento-suave)', 'var(--acento)', 2.4);
      linea(g, 'M24 14 V42', 'var(--acento)', 2.4);
    },
    cubo(g) {
      forma(g, 'M24 5 L41 14 V33 L24 42 L7 33 V14 Z', 'var(--acento-suave)', 'var(--acento)', 2.4);
      linea(g, 'M7 14 L24 23 L41 14 M24 23 V42', 'var(--acento)', 2.4);
    },
    bateria(g) {
      [11, 23, 35].forEach((y) => { rect(g, 5, y - 5, 10, 10, 2, 'var(--h-ok)'); linea(g, `M20 ${y} H33`, 'var(--texto-2)', 2.6); });
      linea(g, 'M40 29 V43 M33 36 H47', 'var(--acento)', 3.2);
    },
    revision(g) {
      circ(g, 15, 14, 6, 'var(--primario)'); forma(g, 'M4 37 Q4 24 15 24 Q26 24 26 37 Z', 'var(--primario)');
      circ(g, 33, 16, 6, 'var(--h-vd)'); forma(g, 'M22 39 Q22 26 33 26 Q44 26 44 39 Z', 'var(--h-vd)');
    },
  };
  function ponerIconos(raiz) {
    for (const i of raiz.querySelectorAll('[data-ico]')) {
      if (i.querySelector('svg')) continue;
      const f = ICONOS[i.getAttribute('data-ico')];
      if (!f) { console.warn('l4_conclusiones: ícono desconocido', i.getAttribute('data-ico')); continue; }
      const s = S('svg', { viewBox: '0 0 48 48', 'aria-hidden': 'true' }, i);
      f(s);
    }
  }

  // ================================================================== 41 · objetivos cumplidos
  EF.registrarViz('c41-objetivos', function (cont) {
    const an = animador();
    ponerIconos(cont);
    const cartas = Array.from(cont.querySelectorAll('.c41-oe'));
    const segs = Array.from(cont.querySelectorAll('.c41-seg i b'));
    const nEl = cont.querySelector('.c41-cuenta .n');
    const cuenta = cont.querySelector('.c41-cuenta');
    const chips = Array.from(cont.querySelectorAll('.c41-og-chips span'));
    const selloOG = cont.querySelector('.c41-og-ver .l4-sello');
    const flecha = cont.querySelector('.c41-og-fl');

    function fijar(p) {
      an.parar();
      cartas.forEach((c, j) => {
        c.classList.toggle('volteada', j < p);   // la tarjeta j se da vuelta en el paso j + 1
        for (const e of c.querySelectorAll('.c41-cara, .c41-cara *')) if (e.style.opacity || e.style.transform) limpiar(e);
      });
      segs.forEach((s, j) => { s.style.width = j < p ? '100%' : '0%'; });
      nEl.textContent = String(Math.min(p, 3));
      cuenta.classList.toggle('completo', p >= 3);
      for (const e of [...chips, selloOG, flecha, cuenta]) limpiar(e);
    }

    /** Paso 0: lo que pide el objetivo general y lo que se logró; cae el sello. */
    function entradaOG() {
      an.t({ dur: 700, retraso: 380, curva: 'ambos', cada: (e) => { flecha.style.transform = `translateX(${-16 * Math.sin(Math.PI * e)}px)`; }, fin: () => limpiar(flecha) });
      chips.forEach((ch, q) => rebote(an, ch, 750 + q * 170, 0.55, 420));
      const T = 750 + chips.length * 170 + 250;
      op(selloOG, 0);
      an.t({ dur: 520, retraso: T, curva: 'entra',
        cada: (e) => { op(selloOG, Math.min(1, 2.2 * e)); selloOG.style.transform = `translateY(${-46 * (1 - e)}px) rotate(${-9 * (1 - e)}deg) scale(${1 + 0.7 * (1 - e)})`; },
        fin: () => limpiar(selloOG) });
      an.t({ dur: 170, retraso: T + 520, cada: (e) => { selloOG.style.transform = `scale(${1 - 0.07 * Math.sin(Math.PI * e)})`; }, fin: () => limpiar(selloOG) });
    }

    /** Pasos 1 a 3: la tarjeta j se da vuelta, su conclusión entra renglón por renglón y cae el sello. */
    function voltear(j) {
      const c = cartas[j];
      const fr = c.querySelector('.c41-frente'), dr = c.querySelector('.c41-dorso');
      const renglones = Array.from(dr.querySelectorAll('.c41-formula, .c41-lista li, .c41-aporte, .c41-pie .c41-chip'));
      const sello = dr.querySelector('.c41-pie .l4-sello');
      const D1 = 430, D2 = 460;
      an.t({ dur: D1, curva: 'entra',
        cada: (e) => { fr.style.transform = `perspective(1500px) rotateY(${88 * e}deg) scale(${1 + 0.05 * e})`; },
        fin: () => {
          c.classList.add('volteada');
          fr.style.transform = '';
          dr.style.transform = 'perspective(1500px) rotateY(-88deg) scale(1.05)';
          for (const r of renglones) op(r, 0);
          op(sello, 0);
        } });
      an.t({ dur: D2, retraso: D1, curva: 'sale',
        cada: (e) => { dr.style.transform = `perspective(1500px) rotateY(${-88 * (1 - e)}deg) scale(${1.05 - 0.05 * e})`; },
        fin: () => { dr.style.transform = ''; } });
      const t0 = D1 + D2 - 120;
      renglones.forEach((r, q) => an.t({ dur: 380, retraso: t0 + q * 175, curva: 'sale',
        cada: (e) => { op(r, e); r.style.transform = `translateY(${14 * (1 - e)}px)`; }, fin: () => limpiar(r) }));
      const ts = t0 + renglones.length * 175 + 220;
      an.t({ dur: 480, retraso: ts, curva: 'rebote',
        cada: (e) => { op(sello, Math.min(1, 2.4 * e)); sello.style.transform = `rotate(${-12 * (1 - e)}deg) scale(${1.9 - 0.9 * e})`; },
        fin: () => limpiar(sello) });
      // el contador avanza cuando cae el sello
      let hecho = false;
      an.t({ dur: 520, retraso: ts + 160, curva: 'ambos',
        cada: (e) => {
          segs[j].style.width = `${100 * e}%`;
          if (!hecho && e > 0.5) { hecho = true; nEl.textContent = String(j + 1); cuenta.classList.toggle('completo', j + 1 >= 3); }
          cuenta.style.transform = `scale(${1 + 0.08 * Math.sin(Math.PI * e)})`;
        },
        fin: () => limpiar(cuenta) });
    }

    return {
      entrar(p, o) { fijar(p); if (p === 0 && !o.instantaneo && !o.impresion) entradaOG(); },
      paso(k, o) {
        if (!o.adelante) { fijar(k); return; }
        fijar(k - 1);
        if (k >= 1 && k <= 3) voltear(k - 1);
      },
      salir() { an.parar(); },
    };
  });

  // ================================================================== 43 · margen (Figura CR.2)
  EF.registrarViz('c43-margen', function (cont) {
    const an = animador();
    ponerIconos(cont);
    const capa = cont.querySelector('.c43-capa');
    const banda = cont.querySelector('.c43-resalte');
    const guia = cont.querySelector('.c43-guia');
    const anillo = cont.querySelector('.c43-anillo');
    const nEl = cont.querySelector('.c43-n');
    const ajust = cont.querySelector('.c43-ajust');
    const der = cont.querySelector('.c43-der');
    const pieFig = cont.querySelector('.c43-pie-fig');
    const caja = cont.querySelector('.c43-fig');

    /** Ubica el resaltado, el anillo, la guía y la llamada con la geometría del SVG de la figura
     *  (punto_6 = σx frente a SAP2000, el criterio más ajustado). */
    function ubicar() {
      const svg = caja.querySelector('svg');
      if (!svg || !caja.clientWidth) return;
      const vb = svg.viewBox.baseVal;
      const W = caja.clientWidth, H = caja.clientHeight;
      const s = Math.min(W / vb.width, H / vb.height);
      const ox = (W - vb.width * s) / 2, oy = (H - vb.height * s) / 2;
      const bx = caja.offsetLeft + caja.clientLeft, by = caja.offsetTop + caja.clientTop;
      const P = (x, y) => [bx + ox + (x - vb.x) * s, by + oy + (y - vb.y) * s];
      const punto = (k) => {
        const g = svg.getElementById('margen_cr2__punto_' + k);
        const u = g && g.querySelector('use');
        return u ? [Number(u.getAttribute('x')), Number(u.getAttribute('y'))] : null;
      };
      const p6 = punto(6), p5 = punto(5), p7 = punto(7);
      if (!p6) return;
      const medio = p5 && p7 ? (p7[1] - p5[1]) / 4 : 11;
      let xDer = vb.width - 4;
      const ejes = svg.getElementById('margen_cr2__patch_2');
      const pe = ejes && ejes.querySelector('path');
      if (pe) xDer = Math.max(...(pe.getAttribute('d').match(/-?\d+(?:\.\d+)?/g) || []).map(Number).filter((v, i) => i % 2 === 0));
      const [x0, y0] = P(3, p6[1] - medio * 1.02);
      const [x1, y1] = P(xDer + 1, p6[1] + medio * 1.02);
      Object.assign(banda.style, { left: `${x0}px`, top: `${y0}px`, width: `${x1 - x0}px`, height: `${y1 - y0}px` });
      const [cx, cy] = P(p6[0], p6[1]);
      Object.assign(anillo.style, { left: `${cx}px`, top: `${cy}px` });
      // la llamada, a la altura de la fila; la guía va del anillo a la llamada
      const hA = ajust.offsetHeight || 220;
      ajust.style.top = `${Math.max(150, cy - hA / 2)}px`;
      const xIni = cx + 28, xFin = der.offsetLeft - 4;
      Object.assign(guia.style, { left: `${xIni}px`, top: `${cy - 1.5}px`, width: `${Math.max(0, xFin - xIni)}px` });
      pieFig.style.top = `${caja.offsetTop + caja.offsetHeight + 8}px`;
    }
    function fijar(p) {
      an.parar();
      ubicar();
      nEl.textContent = p >= 1 ? '9' : '0';
      capa.classList.toggle('c43-on', p >= 2);
      for (const e of [banda, anillo, guia, nEl]) limpiar(e);
    }
    /** Paso 1: el contador sube a medida que cada punto llega a su valor (figdoc: escalón de
     *  200 ms y 1300 ms de recorrido con curva salePlus, que a los ~450 ms ya hizo el 80 %). */
    function contar() {
      nEl.textContent = '0';
      for (let j = 0; j < 9; j++) {
        an.t({ dur: 260, retraso: 700 + j * 200, curva: 'sale',
          cada: (e) => { if (nEl.textContent !== String(j + 1)) nEl.textContent = String(j + 1); nEl.style.transform = `scale(${1.25 - 0.25 * e})`; },
          fin: () => limpiar(nEl) });
      }
    }
    /** Paso 2: el resaltador barre la fila, el anillo cae sobre el punto y la guía se tiende. */
    function resaltar() {
      capa.classList.add('c43-on');
      banda.style.transformOrigin = '0 50%';
      banda.style.transform = 'scaleX(0)';
      an.t({ dur: 650, retraso: 120, curva: 'ambos', cada: (e) => { banda.style.transform = `scaleX(${e})`; }, fin: () => limpiar(banda) });
      op(anillo, 0);
      an.t({ dur: 520, retraso: 650, curva: 'rebote',
        cada: (e) => { op(anillo, Math.min(1, 2 * e)); anillo.style.transform = `scale(${2.3 - 1.3 * e})`; }, fin: () => limpiar(anillo) });
      guia.style.transform = 'scaleX(0)';
      an.t({ dur: 420, retraso: 1000, curva: 'sale', cada: (e) => { guia.style.transform = `scaleX(${e})`; }, fin: () => limpiar(guia) });
    }
    return {
      entrar(p) { fijar(p); },
      paso(k, o) {
        if (!o.adelante) { fijar(k); return; }
        fijar(k - 1);
        if (k === 1) contar();
        else if (k === 2) { nEl.textContent = '9'; resaltar(); }
      },
      salir() { an.parar(); },
    };
  });

  // ================================================================== 44 · respuesta al problema
  // La cadena del cálculo: datos → nueve etapas (sus magnitudes) → resultado.
  const SIMBOLOS = ['N', 'J', 'B', 'D', ['k', 'e'], 'f', 'K', 'u', 'σ'];
  function diagrama44(cont) {
    const W = 1720, H = 318;
    const X0 = 262, PASO = 114, AN = 102;          // nueve fichas de las etapas
    const YF = 96, HF = 100;                       // fila de las fichas
    const YT = 258;                                // línea de la trazabilidad
    const xc = (k) => X0 + k * PASO + AN / 2;      // centro de la ficha k
    // centrado en el bloque de la lámina (la escena puede estar oculta cuando se construye)
    const bloque = cont.closest('.c44') || cont;
    const dx = Math.max(0, ((bloque.offsetWidth || W) - W) / 2);
    // resultado: el contorno real del ejemplo guía (post-proceso de EduFEM)
    const res = EF.el('div', { class: 'c44-res', style: `left:${dx + 1340}px;top:34px;width:380px;height:200px` });
    cont.appendChild(res);
    const mini = EF.miniaturaCanonico(res, 380, 200, { escala: 60, pad: 16 });
    const s = S('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, style: `left:${dx}px` }, cont);
    const defs = S('defs', {}, s);
    const m = S('marker', { id: 'c44-punta', viewBox: '0 0 12 12', refX: 10, refY: 6, markerWidth: 5, markerHeight: 5, orient: 'auto-start-reverse' }, defs);
    est(S('path', { d: 'M1,1 L11,6 L1,11 Z' }, m), { relleno: 'var(--h-vd)' });
    const flechaGris = (d) => { linea(s, d, 'var(--texto-3)', 3); };

    // datos del modelo
    const gDat = S('g', {}, s);
    rect(gDat, 0, 88, 210, 116, 18, 'var(--superficie-2)', 'var(--linea-2)', 1.5);
    const ic = S('g', { transform: 'translate(16,118)' }, gDat);
    for (let i = 0; i <= 3; i++) {
      linea(ic, `M${i * 16} 0 L${i * 16 + 5} 56`, 'var(--malla)', 2.4);
      linea(ic, `M0 ${i * 18} L50 ${i * 18 + 4}`, 'var(--malla)', 2.4);
    }
    texto(gDat, 80, 140, 'Datos', 'font:800 30px var(--fuente)', 'var(--texto)', 'start');
    texto(gDat, 80, 172, 'del modelo', 'font:600 24px var(--fuente)', 'var(--texto-2)', 'start');
    flechaGris('M214 146 H246 M238 138 L247 146 L238 154');
    flechaGris('M1290 146 H1326 M1318 138 L1327 146 L1318 154');
    texto(s, 1530, 24, 'Resultado', 'font:800 26px var(--fuente)', 'var(--texto)');

    // las nueve fichas (debajo de la caja)
    const gFichas = S('g', {}, s);
    const fichas = SIMBOLOS.map((sim, k) => {
      const g = S('g', {}, gFichas);
      rect(g, X0 + k * PASO, YF, AN, HF, 14, 'var(--acento-suave)', 'var(--acento)', 1.8);
      const t = est(S('text', { x: xc(k), y: YF + 64, 'text-anchor': 'middle' }, g), { relleno: 'var(--texto)', estilo: 'font:italic 800 38px var(--fuente)' });
      if (Array.isArray(sim)) { S('tspan', { text: sim[0] }, t); est(S('tspan', { text: sim[1], dy: 9 }, t), { estilo: 'font-size:24px' }); }
      else t.textContent = sim;
      return g;
    });
    const rotEtapas = texto(s, (X0 + xc(8) + AN / 2) / 2, YF + HF + 33, 'las nueve etapas del cálculo, con sus magnitudes intermedias', 'font:700 24px var(--fuente)', 'var(--acento)');

    // (b) verificabilidad: marcas de comprobación
    function marca(g, x, y, r) {
      const gm = S('g', {}, g);
      circ(gm, x, y, r, 'var(--h-ok)');
      linea(gm, `M${x - r * 0.45} ${y + r * 0.02} L${x - r * 0.1} ${y + r * 0.38} L${x + r * 0.48} ${y - r * 0.36}`, 'var(--fondo)', r * 0.22);
      return gm;
    }
    const marcasEt = SIMBOLOS.map((_, k) => marca(s, xc(k), YF - 18, 15));
    const marcaRes = marca(s, 1704, 50, 18);
    const rotVerSolo = texto(s, 1316, 42, '(b) solo el resultado final se comprueba', 'font:700 24px var(--fuente)', 'var(--h-vd)', 'end');

    // la caja negra
    const gCaja = S('g', {}, s);
    rect(gCaja, 252, 80, 1032, 132, 20, 'var(--c4-negro)', 'var(--c4-negro-borde)', 2);
    texto(gCaja, 768, 140, 'caja negra', 'font:800 36px var(--fuente)', 'var(--c4-negro-texto)');
    texto(gCaja, 768, 180, 'las magnitudes intermedias quedan ocultas', 'font:600 24px var(--fuente)', 'var(--c4-negro-texto-2)');

    // (a) trazabilidad: el camino de vuelta, del resultado a los datos
    const fantasma = linea(s, `M1278 ${YT} H105 V210`, 'var(--texto-3)', 2.5, 'stroke-dasharray:7 9;opacity:.6');
    const tramo0 = linea(s, `M1530 236 V${YT} H1300`, 'var(--h-vd)', 5);
    const tramo1 = linea(s, `M1300 ${YT} H105 V214`, 'var(--h-vd)', 5);
    const gCorte = S('g', {}, s);
    circ(gCorte, 1288, YT, 15, 'var(--h-mal)');
    linea(gCorte, `M1282 ${YT - 6} L1294 ${YT + 6} M1294 ${YT - 6} L1282 ${YT + 6}`, 'var(--fondo)', 3.4);
    const rotCorte = texto(s, 1268, YT + 40, '(a) el camino de vuelta se corta en la caja', 'font:700 24px var(--fuente)', 'var(--h-mal)', 'end');
    const puntosT = SIMBOLOS.map((_, k) => circ(s, xc(k), YT, 7, 'var(--superficie)', 'var(--h-vd)', 3));
    const marcaDat = marca(s, 196, 206, 17);
    const rotTraza = texto(s, 232, YT + 40, '(a) cada resultado se sigue, etapa por etapa, hasta los datos', 'font:700 24px var(--fuente)', 'var(--h-vd)', 'start');
    const rotVerTodas = texto(s, 1316, 42, '(b) cada magnitud intermedia puede comprobarse', 'font:700 24px var(--fuente)', 'var(--h-vd)', 'end');
    tramo1.setAttribute('marker-end', 'url(#c44-punta)');
    // el color de los hitos de la traza se cambia por su propiedad: su opacidad queda intacta
    const pintar = (pt, lleno) => { pt.style.fill = lleno ? 'var(--h-vd)' : 'var(--superficie)'; };

    const cerrado = [gCaja, fantasma, gCorte, rotCorte, rotVerSolo];
    const abierto = [gFichas, rotEtapas, ...marcasEt, ...puntosT, marcaDat, rotTraza, rotVerTodas];
    /** p = 0: caja cerrada; p ≥ 1: abierta. */
    function fijar(p) {
      const a = p >= 1;
      for (const e of cerrado) { e.style.opacity = a ? '0' : ''; e.removeAttribute('transform'); }
      for (const e of abierto) { e.style.opacity = a ? '' : '0'; e.removeAttribute('transform'); }
      for (const g of fichas) { g.style.opacity = ''; g.removeAttribute('transform'); }
      for (const e of [gDat, res, marcaRes, tramo0]) { e.style.opacity = ''; e.style.transform = ''; }
      trazoEntero(tramo0); trazoEntero(tramo1);
      tramo1.style.opacity = a ? '' : '0';
      tramo1.setAttribute('marker-end', 'url(#c44-punta)');
      for (const pt of puntosT) pintar(pt, true);
    }
    /** Paso 0: el camino de vuelta se corta en la caja y solo el resultado se comprueba. */
    function animar0(an) {
      fijar(0);
      for (const e of [gDat, gCaja, res]) op(e, 0);
      for (const e of [gCorte, rotCorte, marcaRes, rotVerSolo, fantasma]) op(e, 0);
      an.t({ dur: 420, retraso: 150, cada: (e) => op(gDat, e) });
      an.t({ dur: 480, retraso: 300, cada: (e) => op(gCaja, e) });
      an.t({ dur: 420, retraso: 450, cada: (e) => op(res, e) });
      trazoParcial(tramo0, 0);
      an.t({ dur: 760, retraso: 800, curva: 'ambos', cada: (e) => trazoParcial(tramo0, e), fin: () => trazoEntero(tramo0) });
      an.t({ dur: 400, retraso: 1250, cada: (e) => op(fantasma, e) });
      reboteSvg(an, gCorte, 1288, YT, 1500, 0.3);
      an.t({ dur: 380, retraso: 1650, cada: (e) => op(rotCorte, e) });
      reboteSvg(an, marcaRes, 1704, 50, 1850, 0.3);
      an.t({ dur: 380, retraso: 1950, cada: (e) => op(rotVerSolo, e) });
    }
    /** Paso 1: la caja se abre, el camino llega a los datos y cada magnitud se comprueba. */
    function animar1(an) {
      fijar(0);
      for (const e of abierto) op(e, 0);
      // la tapa sube y se desvanece; lo que la caja impedía, también
      an.t({ dur: 620, curva: 'ambos',
        cada: (e) => { gCaja.setAttribute('transform', `translate(0,${-34 * e})`); op(gCaja, 1 - e); for (const x of [fantasma, gCorte, rotCorte]) op(x, 1 - e); },
        fin: () => { gCaja.removeAttribute('transform'); op(gCaja, 0); } });
      op(gFichas, 1);
      fichas.forEach((g, k) => { g.style.opacity = '0'; reboteSvg(an, g, xc(k), YF + HF / 2, 250 + k * 85, 0.6); });
      an.t({ dur: 380, retraso: 700, cada: (e) => op(rotEtapas, e) });
      // el camino de vuelta, ficha por ficha, hasta los datos
      op(tramo1, 1);
      tramo1.removeAttribute('marker-end');
      trazoParcial(tramo1, 0);
      const L = largo(tramo1), T0 = 1000, DT = 1050;
      const xs = SIMBOLOS.map((_, k) => xc(k));
      for (const pt of puntosT) { op(pt, 1); pintar(pt, false); }
      an.t({ dur: DT, retraso: T0, curva: 'lineal',
        cada: (e) => {
          trazoParcial(tramo1, e);
          const xAct = 1300 - (1300 - 105) * Math.min(1, (e * L) / (1300 - 105));
          puntosT.forEach((pt, k) => { if (xs[k] >= xAct) pintar(pt, true); });
        },
        fin: () => { trazoEntero(tramo1); tramo1.setAttribute('marker-end', 'url(#c44-punta)'); } });
      reboteSvg(an, marcaDat, 196, 206, T0 + DT + 60, 0.3);
      an.t({ dur: 420, retraso: T0 + DT + 120, cada: (e) => op(rotTraza, e) });
      // cada magnitud intermedia puede comprobarse
      an.t({ dur: 300, retraso: 1250, cada: (e) => op(rotVerSolo, 1 - e) });
      marcasEt.forEach((g, k) => reboteSvg(an, g, xc(k), YF - 18, 1350 + k * 90, 0.3));
      an.t({ dur: 380, retraso: 2100, cada: (e) => op(rotVerTodas, e) });
    }
    fijar(0);
    return { fijar, animar0, animar1, mini };
  }

  EF.registrarViz('c44-respuesta', function (cont) {
    const an = animador();
    ponerIconos(cont);
    let dia = null;
    const mods = Array.from(cont.querySelectorAll('.c44-mod'));
    const mem = cont.querySelector('.c44-mem');
    const refs = Array.from(cont.querySelectorAll('.c44-ref'));
    const sellos = Array.from(cont.querySelectorAll('.c44-pi-cab .l4-sello'));

    function escenaB(p) {
      const b = p >= 2;
      mods.forEach((m) => m.classList.toggle('on', b));
      mem.classList.toggle('on', b);
      refs.forEach((r) => r.classList.toggle('hecho', b));
      for (const e of [...mods, mem, ...refs, ...sellos]) limpiar(e);
    }
    function fijar(p) {
      an.parar();
      if (!dia) dia = diagrama44(cont.querySelector('.c44-diag'));
      dia.fijar(p);
      escenaB(p);
    }
    /** Paso 2: la organización se enciende módulo por módulo; las tres partes de PI-2 se marcan. */
    function animarB() {
      escenaB(1);
      mods.forEach((m, j) => an.t({ dur: 240, retraso: 600 + j * 110, curva: 'sale',
        cada: (e) => { m.classList.add('on'); m.style.transform = `scale(${1.25 - 0.25 * e})`; }, fin: () => limpiar(m) }));
      an.t({ dur: 300, retraso: 600 + mods.length * 110 + 80, curva: 'sale',
        cada: (e) => { mem.classList.add('on'); mem.style.transform = `scaleX(${0.6 + 0.4 * e})`; }, fin: () => limpiar(mem) });
      refs.forEach((r, j) => an.t({ dur: 320, retraso: 1250 + j * 260, curva: 'sale',
        cada: (e) => { r.classList.add('hecho'); const c = r.querySelector('.c44-chk'); c.style.transform = `scale(${1.6 - 0.6 * e})`; },
        fin: () => limpiar(r.querySelector('.c44-chk')) }));
      sellos.forEach((s, j) => rebote(an, s, 2000 + j * 260, 1.8, 480));
    }
    return {
      entrar(p, o) {
        fijar(p);
        dia.mini.dibujar();
        if (p === 0 && !o.instantaneo && !o.impresion) dia.animar0(an);
      },
      paso(k, o) {
        if (!o.adelante) { fijar(k); return; }
        fijar(k - 1);
        if (k === 1) dia.animar1(an);
        else if (k === 2) animarB();
        else escenaB(k);
      },
      salir() { an.parar(); },
      tema() { if (dia) dia.mini.dibujar(); },
      redimensionar() { if (dia) dia.mini.dibujar(); },
    };
  });

  // ================================================================== 45 · hoja de ruta
  EF.registrarViz('c45-ruta', function (cont) {
    const an = animador();
    ponerIconos(cont);
    const carriles = Array.from(cont.querySelectorAll('.c45-carril'));
    let vias = [];

    /** Dibuja la vía de cada carril: sale de su cabecera y pasa bajo cada parada. */
    function construir() {
      vias = carriles.map((car) => {
        const caja = car.querySelector('.c45-via');
        caja.innerHTML = '';
        const W = caja.offsetWidth, H = caja.offsetHeight;
        const x0v = caja.offsetLeft;
        const pars = Array.from(car.querySelectorAll('.c45-paradas > *'));
        const base = car.querySelector('.c45-paradas');
        const yv = H - 18;
        const centros = pars.map((q) => base.offsetLeft + q.offsetLeft + q.offsetWidth / 2 - x0v);
        const yPie = base.offsetTop + base.offsetHeight - caja.offsetTop;   // pie de las paradas
        const xFin = W - 4;
        const s = S('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}` }, caja);
        const camino = linea(s, `M0 ${H / 2} C 16 ${H / 2}, 6 ${yv}, 28 ${yv} H ${xFin - 10}`, 'var(--acento)', 6);
        const punta = forma(s, `M${xFin - 14} ${yv - 10} L${xFin + 2} ${yv} L${xFin - 14} ${yv + 10} Z`, 'var(--acento)');
        const hitos = centros.map((cx) => {
          const g = S('g', {}, s);
          linea(g, `M${cx} ${yPie + 2} V${yv - 8}`, 'var(--acento)', 2.5);
          circ(g, cx, yv, 10, 'var(--superficie)', 'var(--acento)', 4);
          return { g, cx };
        });
        const L = largo(camino);
        return { camino, punta, hitos, L, xFin, yv, centros, retrasos: pars.map((q) => Number(q.getAttribute('data-retraso') || 0)) };
      });
    }
    function fijarVia(v, visible) {
      trazoEntero(v.camino);
      for (const e of [v.camino, v.punta, ...v.hitos.map((h) => h.g)]) { e.style.opacity = visible ? '' : '0'; e.removeAttribute('transform'); }
    }
    function fijar(p) {
      an.parar();
      construir();
      vias.forEach((v, k) => fijarVia(v, k <= p));
    }
    /** La vía del carril k avanza y pasa por cada parada cuando esa parada entra en escena. */
    function animarVia(k) {
      const v = vias[k];
      fijarVia(v, true);
      op(v.punta, 0);
      for (const h of v.hitos) op(h.g, 0);
      trazoParcial(v.camino, 0);
      // tiempos de paso por cada hito (los de las paradas, menos un poco) y longitud recorrida
      const tH = v.retrasos.map((r) => Math.max(200, r - 150));
      const T = [0, ...tH, tH[tH.length - 1] + 450];
      const X = [0, ...v.centros.map((c) => c / v.xFin), 1];
      const dur = T[T.length - 1];
      an.t({ dur, retraso: 0, curva: 'lineal',
        cada: (e) => {
          const t = e * dur;
          let i = 1; while (i < T.length - 1 && t > T[i]) i++;
          const f = X[i - 1] + (X[i] - X[i - 1]) * EF.clamp((t - T[i - 1]) / Math.max(1, T[i] - T[i - 1]), 0, 1);
          trazoParcial(v.camino, f);
        },
        fin: () => trazoEntero(v.camino) });
      v.hitos.forEach((h, j) => reboteSvg(an, h.g, h.cx, v.yv, tH[j], 0.2));
      an.t({ dur: 260, retraso: dur, cada: (e) => op(v.punta, e) });
    }
    return {
      entrar(p, o) {
        fijar(p);
        if (p === 0 && !o.instantaneo && !o.impresion) animarVia(0);
      },
      paso(k, o) {
        if (!o.adelante) { fijar(k); return; }
        fijar(k - 1);
        animarVia(k);
      },
      salir() { an.parar(); },
    };
  });
})();
