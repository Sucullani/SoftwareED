/* =====================================================================
   viz/l4_software.js — visualizaciones del grupo «software» (final4).

   Lámina 21 · evaluacion    (viz «sw21-evaluacion», data-pasos="2")
     0  qué se mide: la cadena de la trazabilidad se corta en su eslabón más débil; la
        verificabilidad, un valor contra una referencia con su tolerancia
     1  los tres casos de estudio y el ejemplo guía (mallas reales, dibujadas con el motor)
     2  los 15 criterios con umbral y la regla conjuntiva
   Lámina 22 · software      (viz «sw22-software», data-pasos="2")
     0  un lienzo, tres fases: capturas con llamadas · 1 los ocho módulos · 2 la memoria en abanico
   Lámina 23 · trazabilidad  (viz «sw23-traza», data-pasos="3")
     0  σVM del nodo 7 = 864,70 · 1 el camino hacia atrás, de la etapa 9 a la 1
     2  los datos del modelo · 3 la memoria lo deja por escrito (Anexo G, una página por etapa)
   Lámina 24 · demo          (viz «sw24-demo», data-pasos="1")
     0  el guion de la demostración · 1 recorrido de respaldo: capturas reales con acercamiento lento

   Los textos de lectura están en el HTML de cada lámina; aquí se dibuja lo gráfico y se mueve lo
   que la lámina anima. Toda animación pasa por EF.tween / EF.bucle (reloj virtual del video) y
   todo color es una variable CSS del tema (los campos de tensión usan la paleta jet de EduFEM).
   Las cifras del ejemplo guía salen de EDUFEM_DATOS, las mismas del Anexo G de la tesis.
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const DAT = () => window.EDUFEM_DATOS;
  const S = (tag, at, padre) => EF.svg(tag, at, padre);
  const est = (e, o) => EF.estiloSvg(e, o);
  const PPT = () => EF.estilo === 'ppt';
  const op = (el, v) => { el.style.opacity = String(v); };
  const limpiar = (el) => { el.style.opacity = ''; el.style.transform = ''; };
  const css = (n) => EF.css(n);

  /** Registro de las animaciones en curso de una visualización, para cancelarlas al saltar. */
  function animador() {
    const activos = new Set();
    return {
      t(o) {
        const fin = o.fin;
        const tw = EF.tween(Object.assign({}, o, { fin: () => { activos.delete(tw); if (fin) fin(); } }));
        activos.add(tw);
        return tw;
      },
      parar() { for (const t of Array.from(activos)) t.cancelar(false); activos.clear(); },
    };
  }
  /** Rebote de aparición (escala y opacidad) de un elemento HTML o SVG. */
  function aparecer(an, el, retraso, dur, desde) {
    op(el, 0);
    return an.t({
      dur: dur || 420, retraso: retraso || 0, curva: 'rebote',
      cada: (e) => { op(el, Math.min(1, e * 1.6)); el.style.transform = `scale(${(desde || 0.7) + (1 - (desde || 0.7)) * e})`; },
      fin: () => limpiar(el),
    });
  }
  function fundir(an, el, retraso, dur) {
    op(el, 0);
    return an.t({ dur: dur || 420, retraso: retraso || 0, curva: 'sale', cada: (e) => op(el, e), fin: () => { el.style.opacity = ''; } });
  }
  /** Texto SVG con subíndices («σ_x»). */
  function texto(g, x, y, t, fuente, color, ancla) {
    const e = S('text', { x, y, 'text-anchor': ancla || 'middle' }, g);
    for (const p of EF.partesSub(String(t))) {
      const ts = S('tspan', { text: p.t }, e);
      if (p.sub) { ts.setAttribute('baseline-shift', 'sub'); ts.setAttribute('font-size', '72%'); }
    }
    return est(e, { relleno: color, estilo: 'font:' + fuente });
  }

  // ------------------------------------------------------------------ el ejemplo guía (datos del motor)
  function guia() {
    const C = DAT().canonico;
    const P = C.nodos.map((n) => [n.x, n.y]);
    const idx = Object.fromEntries(C.nodos.map((n, i) => [n.id, i]));
    const elems = Object.entries(C.elementos_conect).map(([k, con]) => ({ id: Number(k), con: con.map((n) => idx[n]) }));
    const u = C.nodos.map((n, i) => [C.u[2 * i], C.u[2 * i + 1]]);
    return { C, P, idx, elems, u };
  }

  // ====================================================================== 21 · evaluacion
  EF.registrarViz('sw21-evaluacion', function (cont) {
    const an = animador();

    // ---------------------------------------------------------------- (a) la cadena de nueve eslabones
    const sC = S('svg', { class: 'sw-svg', viewBox: '-22 0 884 158', preserveAspectRatio: 'xMidYMid meet', 'aria-hidden': 'true' }, cont.querySelector('.sw21-cadena'));
    const Y = 66;
    const gIzq = S('g', {}, sC), gMed = S('g', {}, sC), gDer = S('g', {}, sC);
    function pastilla(g, x, w, txt) {
      const gg = S('g', {}, g);
      est(S('rect', { x, y: Y - 25, width: w, height: 50, rx: 25 }, gg), { relleno: 'var(--superficie)', trazo: 'var(--texto-3)', estilo: 'stroke-width:2.5' });
      texto(gg, x + w / 2, Y + 8, txt, '750 23px var(--fuente)', 'var(--texto)');
      return gg;
    }
    const cxE = (k) => 160 + (k - 1) * 62.5;
    const piezas = [];                       // orden de aparición: del resultado hacia los datos
    piezas.push(pastilla(gDer, 700, 140, 'Resultado'));
    const eslabon = {};
    for (let k = 9; k >= 1; k--) {
      const g = S('g', {}, k < 5 ? gIzq : k > 5 ? gDer : gMed);
      if (k % 2) est(S('rect', { x: cxE(k) - 36, y: Y - 20, width: 72, height: 40, rx: 20 }, g), { relleno: 'none', trazo: 'var(--h-vd)', estilo: 'stroke-width:8' });
      else est(S('rect', { x: cxE(k) - 37, y: Y - 7, width: 74, height: 14, rx: 7 }, g), { relleno: 'var(--h-vd)' });
      texto(g, cxE(k), Y + 56, String(k), '750 22px var(--fuente)', 'var(--texto-3)');
      eslabon[k] = g;
      piezas.push(g);
    }
    piezas.push(pastilla(gIzq, 0, 120, 'Datos'));
    est(S('line', { x1: 118, y1: Y, x2: 126, y2: Y }, gIzq), { trazo: 'var(--h-vd)', estilo: 'stroke-width:6' });
    est(S('line', { x1: 694, y1: Y, x2: 702, y2: Y }, gDer), { trazo: 'var(--h-vd)', estilo: 'stroke-width:6' });
    // el eslabón 5, oculto: el mismo aro, a trazos y en rojo, con una cruz y su rótulo
    const roto = S('g', {}, gMed);
    est(S('rect', { x: cxE(5) - 36, y: Y - 20, width: 72, height: 40, rx: 20 }, roto), { relleno: 'var(--h-mal-suave)', trazo: 'var(--h-mal)', estilo: 'stroke-width:4;stroke-dasharray:7 6' });
    est(S('path', { d: `M${cxE(5) - 13},${Y - 13} L${cxE(5) + 13},${Y + 13} M${cxE(5) + 13},${Y - 13} L${cxE(5) - 13},${Y + 13}` }, roto), { trazo: 'var(--h-mal)', relleno: 'none', estilo: 'stroke-width:6;stroke-linecap:round' });
    texto(roto, cxE(5), Y - 34, 'oculta', '800 22px var(--fuente)', 'var(--h-mal)');
    const sano5 = eslabon[5].firstChild;
    const pieA = cont.querySelector('.sw21-pie-a');
    function cadena(e) {          // e = 0: la cadena entera · e = 1: cortada en la etapa 5
      gIzq.setAttribute('transform', `translate(${(-18 * e).toFixed(2)},0)`);
      gDer.setAttribute('transform', `translate(${(18 * e).toFixed(2)},0)`);
      op(sano5, 1 - e);
      op(roto, e);
    }

    // ---------------------------------------------------------------- (b) un valor contra su referencia
    // Una recta: la referencia (trazo vertical), la banda de tolerancia a su alrededor y el valor de
    // EduFEM, que llega desde lejos y cae dentro: su punto se vuelve verde, con el visto bueno.
    const sT = S('svg', { class: 'sw-svg', viewBox: '0 0 820 158', preserveAspectRatio: 'xMidYMid meet', 'aria-hidden': 'true' }, cont.querySelector('.sw21-tol'));
    const YE = 96, XR = 400, XF = 448, X0 = 760;
    const gBase = S('g', {}, sT);
    est(S('line', { x1: 24, y1: YE, x2: 796, y2: YE }, gBase), { trazo: 'var(--texto-3)', estilo: 'stroke-width:3;stroke-linecap:round' });
    est(S('rect', { x: 300, y: YE - 11, width: 200, height: 22, rx: 11 }, gBase), { relleno: 'var(--h-ok-suave)', trazo: 'var(--h-ok)', estilo: 'stroke-width:2.5' });
    est(S('line', { x1: XR, y1: YE - 34, x2: XR, y2: YE + 22 }, gBase), { trazo: 'var(--texto)', estilo: 'stroke-width:4;stroke-linecap:round' });
    texto(gBase, XR - 10, YE - 44, 'referencia', '750 22px var(--fuente)', 'var(--texto)', 'end');
    texto(gBase, XR, YE + 48, 'tolerancia', '750 22px var(--fuente)', 'var(--h-ok)');
    const punto = S('g', {}, sT);
    const disco = est(S('circle', { cx: 0, cy: YE, r: 17 }, punto), { relleno: 'var(--h-vd)', trazo: 'var(--superficie)', estilo: 'stroke-width:3' });
    const visto = est(S('path', { d: `M-8,${YE} L-2,${YE + 6} L9,${YE - 7}` }, punto), { trazo: 'var(--fondo)', relleno: 'none', estilo: 'stroke-width:4;stroke-linecap:round;stroke-linejoin:round' });
    const etqP = texto(punto, 8, YE - 44, 'EduFEM', '800 22px var(--fuente)', 'var(--h-vd)', 'start');
    const pieB = cont.querySelector('.sw21-pie-b');
    function ponerPunto(e) {
      punto.setAttribute('transform', `translate(${(X0 + (XF - X0) * e).toFixed(1)},0)`);
    }
    function dentro(on) {
      disco.style.fill = on ? 'var(--h-ok)' : 'var(--h-vd)';
      etqP.style.fill = on ? 'var(--h-ok)' : 'var(--h-vd)';
      op(visto, on ? 1 : 0);
    }
    function tolerancia(e) {      // e = 0: lejos · e = 1: dentro de la banda
      ponerPunto(e);
      dentro(e >= 1);
    }

    // ---------------------------------------------------------------- casos de estudio (mallas reales)
    const lienzos = [];
    function dibujarCaso(lz, caso) {
      const D = DAT();
      const blanco = css('--sw-malla-campo');
      lz.redimensionar();
      // la insignia del caso ocupa la esquina superior izquierda: cada dibujo se corre a la derecha
      if (caso === 'mms') {
        const c = D.mms.campos.Q4['8'];
        lz.encuadrar(-0.02, 1.02, -0.02, 1.02, { s: 12, d: 30, i: 10, iz: 190 });
        lz.inicio(css('--lienzo'));
        lz.campo(c.nodos, c.elems, c.u.map((p) => p[0]), { sub: 3 });
        lz.malla(c.nodos, c.elems, { color: blanco, ancho: 1 });
      } else if (caso === 'timoshenko') {
        const T = D.timoshenko;
        lz.encuadrar(-7.25, 7.25, -1.55, 0.95, { s: 62, d: 14, i: 14, iz: 14 });
        lz.inicio(css('--lienzo'));
        const u = T.u.map((p) => [p[0] / 100, p[1] / 100]);
        lz.campo(T.nodos, T.elems, T.sx, { u, escala: 40, sub: 2 });
        lz.malla(T.nodos, T.elems, { color: css('--sw-malla-fina'), ancho: 0.6, u, escala: 40 });
        lz.apoyo(-7, 0, { tam: 8 }); lz.apoyo(7, 0, { tam: 8, movil: true });
        for (let x = -6.5; x <= 6.6; x += 1.3) lz.flecha(x, 0.6, 0, -1, { largo: 18, ancho: 2.5 });
      } else if (caso === 'cook') {
        const c = D.cook.casos.Q9['8'];
        const esc = 0.4;
        lz.encuadrar(-4, 60, -2, 76, { s: 10, d: 24, i: 10, iz: 190 });
        lz.inicio(css('--lienzo'));
        lz.campo(c.nodos, c.elems, c.vm, { max: EF.percentil(c.vm, 96), u: c.u, escala: esc, sub: 3 });
        lz.malla(c.nodos, c.elems, { color: css('--sw-malla-fina'), ancho: 0.8, u: c.u, escala: esc });
        lz.empotramiento(0, 0, 44, {});
        // la carga, tangencial y hacia arriba, sobre el borde derecho deformado
        let k = 0, dmin = Infinity;
        c.nodos.forEach((p, i) => { const d = Math.hypot(p[0] - 48, p[1] - 52); if (d < dmin) { dmin = d; k = i; } });
        lz.flecha(48 + esc * c.u[k][0] + 3, 52 + esc * c.u[k][1], 0, 1, { largo: 30, ancho: 3 });
      } else {
        const { C, P, idx, elems } = guia();
        lz.encuadrar(-0.6, 11.6, -1.0, 9.0, { s: 34, d: 16, i: 12, iz: 200 });
        lz.inicio(css('--lienzo'));
        lz.malla(P, elems.map((e) => e.con), { color: css('--malla'), ancho: 2.4, relleno: css('--malla'), alfaRelleno: 0.08 });
        lz.nodos(P, P.map((_, i) => i), { radio: 4.5 });
        for (const a of C.apoyos) lz.apoyo(P[idx[a]][0], P[idx[a]][1], { tam: 9 });
        lz.flecha(P[idx[7]][0], P[idx[7]][1], 0, -1, { largo: 28, ancho: 3 });
        elems.forEach((e) => {
          const cx = e.con.reduce((s, i) => s + P[i][0], 0) / 4, cy = e.con.reduce((s, i) => s + P[i][1], 0) / 4;
          lz.etiqueta(cx, cy, 'E' + e.id, { ancla: 'center', tam: 22, color: css('--texto-3') });
        });
      }
    }
    function dibujarCasos() {
      if (!lienzos.length) {
        for (const caja of cont.querySelectorAll('.sw21-img')) {
          const w = Math.max(200, Math.floor(caja.clientWidth || ((PPT() ? 1742 : 1720) - 66) / 4 - 2));
          lienzos.push([new EF.LienzoMEF(caja, w, 168), caja.getAttribute('data-caso')]);
        }
      }
      for (const [lz, caso] of lienzos) dibujarCaso(lz, caso);
    }

    // ---------------------------------------------------------------- criterios (paso 2)
    const chips = Array.from(cont.querySelectorAll('.sw21-ca, .sw21-cb'));

    // ---------------------------------------------------------------- composición
    // En el paso 0 solo están las dos primeras filas: van centradas en la lámina. En el paso 1
    // suben a su lugar y dejan sitio a los casos de estudio.
    const DESPL = 150;
    function desplazar(y) { cont.style.transform = y > 0.5 ? `translateY(${y.toFixed(1)}px)` : ''; }

    // ---------------------------------------------------------------- estados
    function fijar(p) {
      an.parar();
      desplazar(p === 0 ? DESPL : 0);
      cadena(1); tolerancia(1); disco.setAttribute('r', '17');
      for (const el of [...piezas, pieA, pieB, punto]) limpiar(el);
      for (const c of chips) limpiar(c);
    }
    /** Paso 0: la cadena se arma del resultado a los datos y se corta; el valor cae en su banda. */
    function animarMedida() {
      an.parar();
      desplazar(DESPL);
      cadena(0); tolerancia(0);
      const T0 = 450;
      piezas.forEach((g, j) => fundir(an, g, T0 + j * 85, 300));
      an.t({ dur: 520, retraso: T0 + 11 * 85 + 380, curva: 'ambos', cada: (e) => cadena(e) });
      fundir(an, pieA, T0 + 11 * 85 + 900, 450);
      op(punto, 0);
      fundir(an, punto, T0 + 200, 300);
      an.t({ dur: 1300, retraso: T0 + 300, curva: 'sale', cada: (e) => ponerPunto(e) });
      an.t({ dur: 380, retraso: T0 + 1650, curva: 'rebote',
        cada: (e) => { if (e > 0.05) dentro(true); disco.setAttribute('r', String(17 + 6 * Math.sin(Math.PI * Math.min(1, e)))); },
        fin: () => disco.setAttribute('r', '17') });
      fundir(an, pieB, T0 + 1900, 450);
    }
    /** Paso 2: los umbrales se estampan uno tras otro. */
    function animarCriterios() {
      an.parar();
      chips.forEach((c, j) => aparecer(an, c, 260 + j * 70, 360, 0.82));
    }
    return {
      entrar(p, o) {
        dibujarCasos();
        if (p === 0 && !o.instantaneo && !o.impresion) animarMedida(); else fijar(p);
      },
      paso(k, o) {
        if (k === 1 && o.adelante) { fijar(1); desplazar(DESPL); an.t({ dur: 650, curva: 'ambos', cada: (e) => desplazar(DESPL * (1 - e)) }); }
        else if (k === 2 && o.adelante) { fijar(2); animarCriterios(); }
        else fijar(k);
      },
      salir() { an.parar(); },
      redimensionar() { if (lienzos.length) dibujarCasos(); },
      tema() { if (lienzos.length) dibujarCasos(); },
    };
  });

  // ====================================================================== 22 · software
  // Llamadas sobre las capturas: posición relativa (x, y) dentro de cada recorte y diámetro en px
  // de la lámina. Las capturas son de 892 × 596 (el lienzo de EduFEM, sin la barra de estado).
  const LLAMADAS = {
    pre: { x: 0.795, y: 0.78, d: 150 },    // los vértices del elemento que se está dibujando
    proc: { x: 0.365, y: 0.745, d: 150 },  // E1, con sus cuatro puntos de Gauss y los ejes ξ, η
    post: { x: 0.426, y: 0.228, d: 64 },   // el nodo 7, donde está la sonda
  };
  EF.registrarViz('sw22-software', function (cont) {
    const an = animador();
    const fases = Array.from(cont.querySelectorAll('.sw22-fase'));
    const anillos = fases.map((f) => {
      const L = LLAMADAS[f.getAttribute('data-fase')];
      const a = EF.el('div', { class: 'sw-anillo' });
      a.style.cssText = `left:calc(${(L.x * 100).toFixed(2)}% - ${L.d / 2}px);top:calc(${(L.y * 100).toFixed(2)}% - ${L.d / 2}px);width:${L.d}px;height:${L.d}px`;
      f.querySelector('.sw-cap').appendChild(a);
      return a;
    });
    // conector del nodo 7 (post-proceso) a la ventana de la sonda
    const unir = S('svg', { class: 'sw22-unir', 'aria-hidden': 'true' }, cont.querySelector('.sw22-fases'));
    const conector = est(S('path', { d: 'M0,0' }, unir), { trazo: 'var(--sw-anillo)', relleno: 'none', estilo: 'stroke-width:3;stroke-linecap:round' });
    /** Del anillo del nodo 7 a la ventana de la sonda. Se mide con offsetLeft/offsetTop, que no
     *  ven las transformaciones de las entradas (en la versión 1 los elementos suben al entrar). */
    function trazarConector() {
      const f = fases[2], cap = f.querySelector('.sw-cap'), pop = f.querySelector('.sw22-pop'), popCap = pop.querySelector('.sw-cap');
      const L = LLAMADAS.post;
      const x1 = f.offsetLeft + cap.offsetLeft + L.x * cap.offsetWidth;
      const y1 = f.offsetTop + cap.offsetTop + L.y * cap.offsetHeight + L.d / 2;
      const x2 = f.offsetLeft + pop.offsetLeft + popCap.offsetLeft + popCap.offsetWidth * 0.62;
      const y2 = f.offsetTop + pop.offsetTop + popCap.offsetTop;
      conector.setAttribute('d', `M${x1.toFixed(1)},${y1.toFixed(1)} C${x1.toFixed(1)},${(y1 + 120).toFixed(1)} ${x2.toFixed(1)},${(y2 - 160).toFixed(1)} ${x2.toFixed(1)},${y2.toFixed(1)}`);
    }

    // ---------------------------------------------------------------- escena 2: abanico de hojas
    const hojas = Array.from(cont.querySelectorAll('.sw22-hoja'));
    const abanico = cont.querySelector('.sw22-abanico');
    function colocarHojas(e) {     // e = 0: apiladas · e = 1: abiertas en abanico
      const W = abanico.clientWidth || 960, H = abanico.clientHeight || 692;
      const hw = 300, hh = 424;
      const n = hojas.length, mid = (n - 1) / 2;
      const R = 430;                                   // radio del pivote al pie de cada hoja
      const px = W / 2, py = H - 150 + R;              // pivote del abanico, bajo las hojas
      hojas.forEach((h, k) => {
        const th = ((k - mid) * 6 * e * Math.PI) / 180;
        const bx = px + R * Math.sin(th), by = py - R * Math.cos(th);
        const x = bx - hw / 2, y = by - hh - 5 * (1 - e) * (mid - Math.abs(k - mid));
        h.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) rotate(${((th * 180) / Math.PI).toFixed(2)}deg)`;
        h.style.zIndex = String(k + 1);
      });
    }
    function abrir() {
      colocarHojas(0);
      hojas.forEach((h) => op(h, 0));
      hojas.forEach((h, k) => fundir(an, h, 250 + k * 60, 260));
      an.t({ dur: 1500, retraso: 900, curva: 'ambos', cada: (e) => colocarHojas(e) });
    }

    function fijar(p) {
      an.parar();
      for (const a of anillos) limpiar(a);
      limpiar(conector);
      hojas.forEach((h) => { h.style.opacity = ''; });
      colocarHojas(1);
      if (p === 0) trazarConector();
    }
    /** Paso 0: cada fase entra con su llamada (los tiempos siguen a los data-retraso del HTML). */
    function animarFases() {
      an.parar();
      trazarConector();
      const T = [650, 1350, 2050];
      anillos.forEach((a, k) => {
        op(a, 0);
        an.t({ dur: 520, retraso: T[k], curva: 'sale', cada: (e) => { op(a, Math.min(1, e * 1.5)); a.style.transform = `scale(${1.9 - 0.9 * e})`; }, fin: () => limpiar(a) });
      });
      const L = (() => { try { return conector.getTotalLength(); } catch (e) { return 400; } })();
      conector.style.strokeDasharray = `${L} ${L}`; conector.style.strokeDashoffset = String(L);
      an.t({ dur: 600, retraso: T[2] + 300, curva: 'ambos', cada: (e) => { conector.style.strokeDashoffset = String(L * (1 - e)); },
        fin: () => { conector.style.strokeDasharray = ''; conector.style.strokeDashoffset = ''; } });
    }
    return {
      entrar(p, o) {
        if (p === 0 && !o.instantaneo && !o.impresion) animarFases();
        else if (p === 2 && !o.instantaneo && !o.impresion) { fijar(p); abrir(); }
        else fijar(p);
      },
      paso(k, o) {
        if (k === 2 && o.adelante) { fijar(k); abrir(); } else fijar(k);
      },
      salir() { an.parar(); },
      redimensionar() { trazarConector(); colocarHojas(1); },
    };
  });

  // ====================================================================== 23 · trazabilidad
  EF.registrarViz('sw23-traza', function (cont, L) {
    const an = animador();
    const G = guia();
    const { C, P, idx, elems, u } = G;
    const E3 = C.elementos[String(C.showcase)];
    const n7 = idx[7];
    // ---------------------------------------------------------------- el lienzo
    const caja = cont.querySelector('.sw23-lienzo');
    let lz = null;
    let modo = 'resultado', avance = 1;           // avance: fracción del camino ya recorrida (paso 1)
    function dibujar() {
      if (!lz) lz = new EF.LienzoMEF(caja, 640, 590);
      lz.redimensionar();
      lz.encuadrar(-0.9, 11.9, -1.3, 9.3, { s: 30, d: 30, i: 26, iz: 30 });
      lz.inicio(css('--lienzo'));
      const todos = elems.map((e) => e.con);
      const e3 = elems.find((e) => e.id === C.showcase).con;
      const c = lz.ctx;
      if (modo === 'resultado') {
        const esc = 60;
        const vm = C.nodos.map((n) => C.nodal[String(n.id)].vm);
        lz.malla(P, todos, { color: css('--texto-3'), ancho: 1.2, discontinua: [6, 6], alfa: 0.6 });
        lz.campo(P, todos, vm, { u, escala: esc, sub: 8 });
        lz.malla(P, todos, { color: css('--sw-malla-campo'), ancho: 1.8, u, escala: esc });
        const p7 = EF.LienzoMEF.pos(P, u, esc, n7);
        lz.flecha(p7[0], p7[1], 0, -1, { largo: 54, ancho: 4 });
        c.save(); c.beginPath(); c.arc(lz.X(p7[0]), lz.Y(p7[1]), 17, 0, 2 * Math.PI); c.lineWidth = 5; c.strokeStyle = css('--sw-anillo'); c.stroke(); c.restore();
        lz.etiqueta(p7[0], p7[1], 'nodo 7: 864,70', { dx: 26, dy: 34, tam: 24, color: css('--sw-ui-texto'), fondo: css('--sw-ui'), alfaFondo: 0.9 });
        return;
      }
      // camino y datos: la malla sin deformar, E3 resaltado
      const fr = modo === 'datos' ? 1 : avance;
      lz.malla(P, todos, { color: css('--malla'), ancho: 2.2 });
      if (fr > 0.2) lz.elemento(P, e3, { color: css('--h-vd'), ancho: 4.5, relleno: css('--h-vd'), alfaRelleno: 0.16 });
      lz.nodos(P, P.map((_, i) => i), { radio: 6 });
      C.nodos.forEach((nd, i) => lz.etiqueta(P[i][0], P[i][1], String(nd.id), { dx: -12, dy: -16, ancla: 'right', tam: 22, color: css('--texto') }));
      // los cuatro puntos de Gauss de E3 y su extrapolación al nodo 7
      const p7 = P[n7];
      E3.gauss.forEach((g, k) => {
        const e = EF.clamp(fr * 5 - k * 0.5, 0, 1);
        if (e <= 0) return;
        c.save();
        c.globalAlpha = e;
        c.setLineDash([6, 6]); c.lineWidth = 2.5; c.strokeStyle = css('--h-vd');
        c.beginPath(); c.moveTo(lz.X(g.x[0]), lz.Y(g.x[1])); c.lineTo(lz.X(p7[0]), lz.Y(p7[1])); c.stroke();
        c.setLineDash([]);
        c.beginPath(); c.arc(lz.X(g.x[0]), lz.Y(g.x[1]), 9, 0, 2 * Math.PI);
        c.fillStyle = css('--sw-anillo'); c.fill(); c.lineWidth = 2; c.strokeStyle = css('--texto'); c.stroke();
        c.restore();
      });
      c.save(); c.beginPath(); c.arc(lz.X(p7[0]), lz.Y(p7[1]), 17, 0, 2 * Math.PI); c.lineWidth = 5; c.strokeStyle = css('--sw-anillo'); c.stroke(); c.restore();
      if (modo === 'datos') {
        for (const a of C.apoyos) lz.apoyo(P[idx[a]][0], P[idx[a]][1], { tam: 13 });
        lz.flecha(p7[0], p7[1], 0, -1, { largo: 62, ancho: 4.5, texto: 'P = 1000', tam: 24 });
        lz.etiqueta(5.6, -0.85, 'E = 225 000 · ν = 0,2 · t = 0,8', { ancla: 'center', tam: 24, color: css('--h-vi') });
      }
    }

    // ---------------------------------------------------------------- la escalera
    const filas = Array.from(cont.querySelectorAll('.sw23-f[data-n]'));
    const fRes = cont.querySelector('.sw23-f.res');
    const fDatos = cont.querySelector('.sw23-f.datos');
    const camino = filas.filter((f) => /^[1-9]$/.test(f.getAttribute('data-n')));   // 9 … 1, en orden del DOM
    // la flecha del recorrido baja por el hueco entre el lienzo y la escalera, fila por fila
    const flechaSvg = S('svg', { class: 'sw23-flecha', 'aria-hidden': 'true' }, cont);
    const flecha = est(S('path', { d: 'M14,0 L14,0' }, flechaSvg), { trazo: 'var(--h-vd)', relleno: 'none', estilo: 'stroke-width:5;stroke-linecap:round' });
    const punta = est(S('path', { d: 'M0,0' }, flechaSvg), { relleno: 'var(--h-vd)' });
    function centros() {                // centro vertical de cada fila: resultado, 9 … 1, datos
      return [fRes, ...camino, fDatos].map((f) => f.offsetTop + f.offsetHeight / 2);
    }
    function trazarFlecha(e) {          // e ∈ [0, 10]: 0 en el resultado, j en la fila j del camino, 10 en los datos
      const c = centros();
      const j = Math.min(9, Math.floor(e)), f = EF.clamp(e - j, 0, 1);
      const y0 = c[0] + fRes.offsetHeight / 2 - 4;
      const y = Math.max(y0, c[j] + (c[j + 1] - c[j]) * f);
      flecha.setAttribute('d', `M14,${y0.toFixed(1)} L14,${(y - 8).toFixed(1)}`);
      punta.setAttribute('d', `M4,${(y - 12).toFixed(1)} L24,${(y - 12).toFixed(1)} L14,${(y + 2).toFixed(1)} Z`);
      op(flecha, e > 0.02 ? 1 : 0); op(punta, e > 0.02 ? 1 : 0);
    }
    function encender(n) {              // n: cuántas etapas del camino están encendidas (0 … 9); 10 = también los datos
      camino.forEach((f, j) => { f.classList.toggle('on', j < n); f.classList.toggle('foco', j === n - 1 && n <= 9); });
      fDatos.classList.toggle('on', n >= 10);
      fDatos.classList.toggle('foco', n >= 10);
      fRes.classList.toggle('foco', n === 0);
    }
    const TIEMPO = 280;                 // ms entre una etapa y la siguiente (paso 1; los data-retraso del HTML siguen este ritmo)
    // ---------------------------------------------------------------- las hojas (paso 3)
    const hojas = Array.from(cont.querySelectorAll('.sw23-hoja'));
    const POS_HOJA = (k, n) => {        // la última (p. 174) queda al frente; las demás, apiladas detrás
      const atras = n - 1 - k;
      return { x: 172 - atras * 15, y: 14 + atras * 6, r: 0.8 - 0.7 * atras };
    };
    function colocarHojas(e) {
      const n = hojas.length;
      hojas.forEach((h, k) => {
        const p = POS_HOJA(k, n);
        const d = 1 - EF.suave.sale(EF.clamp(e * 1.6 - (k / (n - 1)) * 0.6, 0, 1));
        // llegan desde la izquierda: nunca pasan por debajo de la escalera
        h.style.transform = `translate(${(p.x - 150 * d).toFixed(1)}px, ${(p.y + 30 * d).toFixed(1)}px) rotate(${(p.r - 6 * d).toFixed(2)}deg)`;
        h.style.opacity = String(1 - d);
        h.style.zIndex = String(k + 1);
      });
    }

    function estado(p) {
      an.parar();
      modo = p === 0 ? 'resultado' : p === 1 ? 'camino' : 'datos';
      avance = 1;
      dibujar();
      encender(p === 0 ? 0 : p === 1 ? 9 : 10);
      trazarFlecha(p >= 2 ? 10 : p === 1 ? 9 : 0);
      colocarHojas(p >= 3 ? 1 : 0);
    }
    function animarCamino() {
      an.parar();
      modo = 'camino'; avance = 0; dibujar();
      encender(0); trazarFlecha(0);
      const T0 = 350;
      camino.forEach((f, j) => an.t({ dur: 10, retraso: T0 + j * TIEMPO, fin: () => encender(j + 1) }));
      an.t({ dur: 9 * TIEMPO, retraso: T0 - TIEMPO + 60, curva: 'lineal', cada: (e) => trazarFlecha(9 * e) });
      an.t({ dur: 900, retraso: T0, curva: 'sale', cada: (e) => { avance = e; dibujar(); } });
    }
    function animarDatos() {
      an.parar();
      modo = 'datos'; dibujar();
      encender(9); trazarFlecha(9);
      an.t({ dur: 500, retraso: 150, curva: 'sale', cada: (e) => trazarFlecha(9 + e), fin: () => encender(10) });
    }
    function animarHojas() {
      an.parar();
      colocarHojas(0);
      an.t({ dur: 1800, retraso: 200, curva: 'lineal', cada: (e) => colocarHojas(e) });
    }
    void L;
    return {
      entrar(p, o) { estado(p); if (p === 1 && !o.instantaneo && !o.impresion) animarCamino(); },
      paso(k, o) {
        if (!o.adelante) { estado(k); return; }
        if (k === 1) animarCamino();
        else if (k === 2) animarDatos();
        else if (k === 3) { estado(3); animarHojas(); }
        else estado(k);
      },
      salir() { an.parar(); },
      redimensionar() { if (lz) dibujar(); },
      tema() { if (lz) dibujar(); },
    };
  });

  // ====================================================================== 24 · demo
  // Recorrido de respaldo: cada cuadro es una captura real; el acercamiento va de una vista
  // (centro en px de la imagen, aumento) a otra. Duración de cada cuadro: 4 s (ciclo de 16 s, el
  // largo de la narración del paso; data-pptx-clip del marco lo graba entero para PowerPoint).
  const CUADROS = [
    { w: 1366, h: 685, de: [683, 342, 1.0], a: [905, 330, 1.22], foco: [0, 1] },     // pre-proceso: el ejemplo guía cargado
    { w: 1626, h: 658, de: [420, 380, 1.12], a: [1250, 330, 1.2], foco: [2] },       // módulo M3 sobre E1
    { w: 1392, h: 658, de: [640, 330, 1.0], a: [880, 210, 1.3], foco: [3] },         // post-proceso, sonda en el nodo 7
    { w: 1800, h: 900, de: [900, 450, 1.0], a: [1450, 640, 1.85], foco: [4] },       // la memoria (Anexo G, p. 174)
  ];
  const DUR_CUADRO = 4, FUNDIDO = 0.6;
  EF.registrarViz('sw24-demo', function (cont) {
    const marco = cont.querySelector('.sw24-marco');
    const cuadros = Array.from(marco.querySelectorAll('.sw24-cuadro'));
    const imgs = cuadros.map((c) => c.querySelector('img'));
    const rot = cont.querySelector('.sw24-rot');
    const minis = Array.from(cont.querySelectorAll('.sw24-mini'));
    const pasos = Array.from(cont.querySelectorAll('.sw24-p'));
    let bucle = null, actual = -1;
    function vista(k, e) {           // coloca el cuadro k en la fracción e de su acercamiento
      const Q = CUADROS[k], img = imgs[k];
      const FW = marco.clientWidth || 1060, FH = marco.clientHeight || 530;
      const s0 = Math.max(FW / Q.w, FH / Q.h);
      const ee = EF.suave.ambos(EF.clamp(e, 0, 1));
      const cx = Q.de[0] + (Q.a[0] - Q.de[0]) * ee, cy = Q.de[1] + (Q.a[1] - Q.de[1]) * ee;
      const z = Q.de[2] + (Q.a[2] - Q.de[2]) * ee;
      const s = s0 * z;
      let tx = FW / 2 - cx * s, ty = FH / 2 - cy * s;
      tx = EF.clamp(tx, FW - Q.w * s, 0); ty = EF.clamp(ty, FH - Q.h * s, 0);
      img.style.width = `${Q.w}px`; img.style.height = `${Q.h}px`;
      img.style.transform = `translate(${tx.toFixed(2)}px, ${ty.toFixed(2)}px) scale(${s.toFixed(5)})`;
    }
    function marcar(k) {
      if (k === actual) return;
      actual = k;
      rot.textContent = k >= 0 ? cuadros[k].getAttribute('data-rotulo') : '';
      op(rot, k >= 0 ? 1 : 0);
      minis.forEach((m, j) => m.classList.toggle('foco', j === k));
      pasos.forEach((p, j) => p.classList.toggle('foco', k >= 0 && CUADROS[k].foco.includes(j)));
    }
    function quieto() {              // paso 0: la primera captura, sin movimiento ni foco
      parar();
      cuadros.forEach((c, j) => op(c, j === 0 ? 1 : 0));
      vista(0, 0);
      actual = -2; marcar(-1);
    }
    function cuadroEn(t) {           // t en s desde que empezó el recorrido
      const ciclo = DUR_CUADRO * CUADROS.length;
      const tt = t % ciclo;
      const k = Math.floor(tt / DUR_CUADRO), loc = (tt - k * DUR_CUADRO) / DUR_CUADRO;
      const ant = (k + CUADROS.length - 1) % CUADROS.length;
      const f = EF.clamp((tt - k * DUR_CUADRO) / FUNDIDO, 0, 1);
      // el cuadro nuevo entra fundido sobre el anterior, que se queda quieto en su vista final;
      // el primero ya estaba a la vista en el paso 0 y arranca sin fundido desde esa misma vista
      cuadros.forEach((c, j) => {
        if (j === k) { op(c, t < FUNDIDO && k === 0 ? 1 : f); c.style.zIndex = '2'; vista(j, loc); }
        else if (j === ant && f < 1 && t >= FUNDIDO) { op(c, 1); c.style.zIndex = '1'; vista(j, 1); }
        else { op(c, 0); c.style.zIndex = '0'; }
      });
      marcar(k);
    }
    function recorrer() {
      parar();
      actual = -2;
      bucle = EF.bucle((t) => cuadroEn(t), { fps: 30 });
    }
    function parar() { if (bucle) { bucle.detener(); bucle = null; } }
    return {
      entrar(p, o) {
        if (p >= 1 && !o.impresion) recorrer();
        else if (p >= 1) { parar(); cuadroEn(DUR_CUADRO * 2 + 1.5); }
        else quieto();
      },
      paso(k) { if (k >= 1) recorrer(); else quieto(); },
      salir() { parar(); },
      redimensionar() { if (!bucle) { if (actual >= 0) cuadroEn(DUR_CUADRO * actual + 1.5); else vista(0, 0); } },
    };
  });
})();
