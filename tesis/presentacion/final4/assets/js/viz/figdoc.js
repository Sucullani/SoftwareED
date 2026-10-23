/* =====================================================================
   viz/figdoc.js — las gráficas de la tesis, idénticas, animadas por partes.

   Las figuras salen de herramientas/figuras_documento.py, que llama a las MISMAS
   funciones de dibujo que generan las figuras de la tesis (final4) y las guarda en
   SVG (assets/data/figuras_doc.js -> window.EDUFEM_FIGDOC). Aquí no se redibuja nada:
   solo se muestran, se ocultan o se trazan las series que llevan identificador.

   Claves y series disponibles:
     mms_l2, mms_h1   serie_q4, serie_q9, pend_q4, pend_q9, leyenda   (Figura 3.1 a y b)
     cook             serie_q4, serie_q9, referencia, leyenda          (Figura 3.4)
     margen_cr2       barra_0..8, punto_0..8, umbral                   (Figura CR.2)

   Uso desde el HTML (la lámina decide qué se ve en cada paso):
     <div data-viz="figdoc" data-fig="mms_l2"
          data-fig-pasos='{"0":["serie_q4","pend_q4"],"1":["serie_q9","pend_q9"]}'></div>
   Las series que no figuran en data-fig-pasos están siempre visibles (ejes, rótulos).
   Acción según el nombre: serie_* se traza del primer al último punto (de la malla
   más gruesa a la más fina); punto_k se desliza desde el umbral hasta su valor, con su
   barra; lo demás aparece con un fundido.

   Uso desde otra visualización:
     const f = EF.figuraDoc(contenedor, 'cook');  f.ocultar('serie_q4');  f.trazar('serie_q4', {dur: 1600});
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const XLINK = 'http://www.w3.org/1999/xlink';
  const FIG = () => window.EDUFEM_FIGDOC || {};

  function numeros(d) {
    return (d.match(/-?\d+(?:\.\d+)?(?:e-?\d+)?/gi) || []).map(Number);
  }
  function puntos(d) {
    const n = numeros(d), out = [];
    for (let i = 0; i + 1 < n.length; i += 2) out.push([n[i], n[i + 1]]);
    return out;
  }

  class FiguraDoc {
    constructor(contenedor, clave, op) {
      op = op || {};
      this.clave = clave;
      this.tweens = [];
      const s = FIG()[clave];
      this.caja = EF.el('div', { class: 'figdoc' });
      contenedor.appendChild(this.caja);
      if (!s) { this.caja.textContent = 'Falta la figura ' + clave + ' (correr herramientas/figuras_documento.py)'; this.svg = null; return; }
      this.caja.innerHTML = s;
      this.svg = this.caja.querySelector('svg');
      this.svg.setAttribute('preserveAspectRatio', op.alinear || 'xMidYMid meet');
      Object.assign(this.svg.style, { width: '100%', height: '100%', display: 'block', overflow: 'visible' });
      // posición x del umbral (Figura CR.2), para deslizar los puntos desde él
      const u = this.g('umbral');
      const pu = u && u.querySelector('path');
      this.xUmbral = pu ? puntos(pu.getAttribute('d'))[0][0] : null;
    }

    g(gid) { return this.svg ? this.svg.getElementById(this.clave + '__' + gid) : null; }
    existe(gid) { return !!this.g(gid); }

    detener() { for (const t of this.tweens) if (t && t.cancelar) t.cancelar(true); this.tweens = []; }

    /** Deja la serie en su estado final, visible. */
    mostrar(...gids) {
      for (const gid of gids.flat()) {
        const e = this.g(gid);
        if (!e) continue;
        e.style.opacity = '1';
        e.removeAttribute('transform');
        for (const p of e.querySelectorAll('path')) { p.style.strokeDasharray = ''; p.style.strokeDashoffset = ''; }
        for (const m of e.querySelectorAll('use')) m.style.opacity = '';
        if (gid.startsWith('punto_')) this._barra(gid, 0);
      }
    }
    ocultar(...gids) {
      for (const gid of gids.flat()) {
        const e = this.g(gid);
        if (e) e.style.opacity = '0';
        if (gid.startsWith('punto_')) { const b = this.g('barra_' + gid.slice(6)); if (b) b.style.opacity = '0'; }
      }
    }

    /** Fundido de entrada. */
    aparecer(gid, op) {
      op = op || {};
      const e = this.g(gid);
      if (!e) return EF.esperar(0);
      this.mostrar(gid);
      e.style.opacity = '0';
      const t = EF.tween({ dur: op.dur || 700, retraso: op.retraso || 0, curva: 'sale', cada: (v) => { e.style.opacity = String(v); } });
      this.tweens.push(t);
      return EF.esperar((op.dur || 700) + (op.retraso || 0));
    }

    /** Traza una serie (línea con marcadores) desde su primer punto hasta el último. */
    trazar(gid, op) {
      op = op || {};
      const e = this.g(gid);
      if (!e) return EF.esperar(0);
      this.mostrar(gid);
      const linea = e.querySelector('path:not(defs path)');
      const marcas = Array.from(e.querySelectorAll('use'));
      const dur = op.dur || 1600, ret = op.retraso || 0;
      if (!linea) return this.aparecer(gid, op);
      const pts = puntos(linea.getAttribute('d'));
      // longitud acumulada de la poligonal, para soltar cada marcador cuando la línea lo alcanza
      const acum = [0];
      for (let i = 1; i < pts.length; i++) acum.push(acum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
      const L = acum[acum.length - 1] || 1;
      const fr = marcas.map((m) => {
        const x = Number(m.getAttribute('x')), y = Number(m.getAttribute('y'));
        let best = 0, dmin = Infinity;
        pts.forEach((p, i) => { const d = Math.hypot(p[0] - x, p[1] - y); if (d < dmin) { dmin = d; best = i; } });
        return acum[best] / L;
      });
      linea.style.strokeDasharray = `${L} ${L}`;
      linea.style.strokeDashoffset = String(L);
      marcas.forEach((m) => { m.style.opacity = '0'; });
      const t = EF.tween({
        dur, retraso: ret, curva: op.curva || 'ambos',
        cada: (v) => {
          linea.style.strokeDashoffset = String(L * (1 - v));
          marcas.forEach((m, k) => { m.style.opacity = v + 1e-9 >= fr[k] ? '1' : '0'; });
        },
        fin: () => { linea.style.strokeDasharray = ''; linea.style.strokeDashoffset = ''; marcas.forEach((m) => { m.style.opacity = ''; }); },
      });
      this.tweens.push(t);
      return EF.esperar(dur + ret);
    }

    /** Figura CR.2: el punto del criterio k parte del umbral y se desliza hasta su valor. */
    _barra(gidPunto, dx) {
      const k = gidPunto.slice(6);
      const b = this.g('barra_' + k);
      const p = b && b.querySelector('path');
      if (!p) return;
      if (!p.__d) p.__d = p.getAttribute('d');
      const [a, z] = puntos(p.__d);
      p.setAttribute('d', `M ${a[0]} ${a[1]} L ${z[0] + dx} ${z[1]}`);
      b.style.opacity = '1';
    }
    deslizar(gid, op) {
      op = op || {};
      const e = this.g(gid);
      if (!e || this.xUmbral == null) return this.aparecer(gid, op);
      this.mostrar(gid);
      const u = e.querySelector('use');
      const x = u ? Number(u.getAttribute('x')) : this.xUmbral;
      const dx0 = this.xUmbral - x;
      const dur = op.dur || 1300, ret = op.retraso || 0;
      e.setAttribute('transform', `translate(${dx0} 0)`);
      this._barra(gid, dx0);
      e.style.opacity = '0';
      const t = EF.tween({
        dur, retraso: ret, curva: 'salePlus',
        cada: (v) => {
          const dx = dx0 * (1 - v);
          e.style.opacity = String(Math.min(1, v * 4));
          e.setAttribute('transform', `translate(${dx} 0)`);
          this._barra(gid, dx);
        },
        fin: () => { e.removeAttribute('transform'); this._barra(gid, 0); },
      });
      this.tweens.push(t);
      return EF.esperar(dur + ret);
    }

    /** La acción que corresponde a cada serie según su nombre. */
    animar(gid, op) {
      if (gid.startsWith('serie_')) return this.trazar(gid, op);
      if (gid.startsWith('punto_')) return this.deslizar(gid, op);
      return this.aparecer(gid, op);
    }
  }

  EF.FiguraDoc = FiguraDoc;
  EF.figuraDoc = (contenedor, clave, op) => new FiguraDoc(contenedor, clave, op);

  // ------------------------------------------------------------------ viz genérica
  EF.registrarViz('figdoc', function (cont) {
    const clave = cont.getAttribute('data-fig');
    let mapa = {};
    try { mapa = JSON.parse(cont.getAttribute('data-fig-pasos') || '{}'); } catch (e) { console.error('data-fig-pasos', e); }
    const escalon = Number(cont.getAttribute('data-fig-escalon') || 260);   // ms entre series de un mismo paso
    const f = new FiguraDoc(cont, clave, { alinear: cont.getAttribute('data-fig-alinear') || undefined });
    const pasoDe = {};
    for (const [k, lista] of Object.entries(mapa)) for (const gid of lista) pasoDe[gid] = Number(k);
    function estado(p, animar) {
      f.detener();
      const animables = [];
      for (const [gid, k] of Object.entries(pasoDe)) {
        if (k < p || (k === p && !animar)) f.mostrar(gid);
        else if (k === p) animables.push(gid);
        else f.ocultar(gid);
      }
      animables.forEach((gid, j) => { f.ocultar(gid); f.animar(gid, { retraso: 250 + j * escalon }); });
    }
    return {
      figura: f,
      entrar(p, op) { estado(p, !op.instantaneo && !op.impresion); },
      paso(k, op) { estado(k, !!op.adelante && !op.salto); },
      salir() { f.detener(); },
    };
  });
})();
