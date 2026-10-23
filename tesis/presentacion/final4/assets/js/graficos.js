/* =====================================================================
   graficos.js — gráficos SVG livianos (ejes lineales o logarítmicos,
   series que se dibujan solas, bandas, triángulos de pendiente).
   Los colores se pasan como CSS (var(--q4)...) y se aplican por style,
   así el cambio de tema no obliga a redibujar.
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const svg = EF.svg;

  function estilo(e, op) {
    const s = [];
    if (op.trazo) s.push(`stroke:${op.trazo}`);
    if (op.relleno) s.push(`fill:${op.relleno}`);
    if (op.opacidad != null) s.push(`opacity:${op.opacidad}`);
    if (op.estilo) s.push(op.estilo);
    if (s.length) e.setAttribute('style', s.join(';'));
    return e;
  }

  class Grafico {
    constructor(contenedor, op) {
      this.op = op;
      this.W = op.ancho; this.H = op.alto;
      const m = (this.m = Object.assign({ s: 30, d: 30, i: 90, iz: 120 }, op.margen || {}));
      this.svg = svg('svg', { class: 'viz grafico', width: this.W, height: this.H, viewBox: `0 0 ${this.W} ${this.H}` }, contenedor);
      this.x = Object.assign({ min: 0, max: 1, log: false }, op.x);
      this.y = Object.assign({ min: 0, max: 1, log: false }, op.y);
      this.px0 = m.iz; this.px1 = this.W - m.d;
      this.py0 = this.H - m.i; this.py1 = m.s;
      const id = 'rec' + Math.random().toString(36).slice(2, 8);
      const defs = svg('defs', {}, this.svg);
      const cp = svg('clipPath', { id }, defs);
      svg('rect', { x: this.px0, y: this.py1 - 12, width: this.px1 - this.px0 + 12, height: this.py0 - this.py1 + 14 }, cp);
      this.gFondo = svg('g', {}, this.svg);
      this.gEjes = svg('g', {}, this.svg);
      this.gDatos = svg('g', { 'clip-path': `url(#${id})` }, this.svg);
      this.gSobre = svg('g', {}, this.svg);
    }
    _t(eje, v) {
      if (eje.log) return (Math.log10(v) - Math.log10(eje.min)) / (Math.log10(eje.max) - Math.log10(eje.min));
      return (v - eje.min) / (eje.max - eje.min);
    }
    sx(v) { return this.px0 + this._t(this.x, v) * (this.px1 - this.px0); }
    sy(v) { return this.py0 - this._t(this.y, v) * (this.py0 - this.py1); }

    _marcas(eje) {
      if (eje.marcas) return eje.marcas;
      if (eje.log) {
        const a = Math.ceil(Math.log10(eje.min) - 1e-9), b = Math.floor(Math.log10(eje.max) + 1e-9);
        return EF.rango(b - a + 1).map((k) => Math.pow(10, a + k));
      }
      const paso = eje.paso || niceStep((eje.max - eje.min) / 5);
      const out = [];
      for (let v = Math.ceil(eje.min / paso) * paso; v <= eje.max + 1e-9 * paso; v += paso) out.push(+v.toFixed(10));
      return out;
    }
    _etq(eje, v) {
      if (eje.fmt) return eje.fmt(v);
      if (eje.log) return '10' + EF.sup(Math.round(Math.log10(v)));
      const dec = eje.dec != null ? eje.dec : (Math.abs(v) < 10 && v % 1 ? 1 : 0);
      return EF.fmt(v, dec);
    }
    ejes(op) {
      op = op || {};
      const g = this.gEjes;
      g.innerHTML = '';
      const fx = this._marcas(this.x), fy = this._marcas(this.y);
      // cuadrícula menor en escala log
      const menores = (eje, dir) => {
        if (!eje.log || op.sinMenores) return;
        const a = Math.floor(Math.log10(eje.min)), b = Math.ceil(Math.log10(eje.max));
        for (let k = a; k < b; k++) for (let j = 2; j < 10; j++) {
          const v = j * Math.pow(10, k);
          if (v < eje.min || v > eje.max) continue;
          if (dir === 'x') estilo(svg('line', { x1: this.sx(v), x2: this.sx(v), y1: this.py0, y2: this.py1 }, g), { trazo: 'var(--linea)', estilo: 'stroke-width:1;opacity:.55' });
          else estilo(svg('line', { x1: this.px0, x2: this.px1, y1: this.sy(v), y2: this.sy(v) }, g), { trazo: 'var(--linea)', estilo: 'stroke-width:1;opacity:.55' });
        }
      };
      menores(this.x, 'x'); menores(this.y, 'y');
      for (const v of fx) {
        const X = this.sx(v);
        estilo(svg('line', { x1: X, x2: X, y1: this.py0, y2: this.py1 }, g), { trazo: 'var(--linea)', estilo: 'stroke-width:1.2' });
        estilo(svg('text', { x: X, y: this.py0 + 38, 'text-anchor': 'middle', text: this._etq(this.x, v) }, g),
          { relleno: 'var(--texto-3)', estilo: `font:600 ${op.tamMarcas || 24}px var(--fuente)` });
      }
      for (const v of fy) {
        const Y = this.sy(v);
        estilo(svg('line', { x1: this.px0, x2: this.px1, y1: Y, y2: Y }, g), { trazo: 'var(--linea)', estilo: 'stroke-width:1.2' });
        estilo(svg('text', { x: this.px0 - 16, y: Y + 8, 'text-anchor': 'end', text: this._etq(this.y, v) }, g),
          { relleno: 'var(--texto-3)', estilo: `font:600 ${op.tamMarcas || 24}px var(--fuente)` });
      }
      estilo(svg('line', { x1: this.px0, x2: this.px1, y1: this.py0, y2: this.py0 }, g), { trazo: 'var(--linea-2)', estilo: 'stroke-width:2' });
      estilo(svg('line', { x1: this.px0, x2: this.px0, y1: this.py0, y2: this.py1 }, g), { trazo: 'var(--linea-2)', estilo: 'stroke-width:2' });
      if (this.x.etiqueta) estilo(svg('text', { x: (this.px0 + this.px1) / 2, y: this.H - 14, 'text-anchor': 'middle', text: this.x.etiqueta }, g),
        { relleno: 'var(--texto-2)', estilo: 'font:650 27px var(--fuente)' });
      if (this.y.etiqueta) {
        const t = svg('text', { x: 0, y: 0, 'text-anchor': 'middle', transform: `translate(${28},${(this.py0 + this.py1) / 2}) rotate(-90)` }, g);
        textoConSub(t, this.y.etiqueta);
        estilo(t, { relleno: 'var(--texto-2)', estilo: `font:650 ${this.y.tamEtiqueta || 27}px var(--fuente)` });
      }
      return this;
    }
    ruta(puntos) {
      return puntos.map((p, k) => `${k ? 'L' : 'M'}${this.sx(p[0]).toFixed(1)},${this.sy(p[1]).toFixed(1)}`).join('');
    }
    /** Serie con marcadores. Devuelve {g, path, marcas} */
    serie(puntos, op) {
      op = op || {};
      const g = svg('g', { class: 'serie' }, this.gDatos);
      const path = svg('path', { d: this.ruta(puntos), fill: 'none' }, g);
      estilo(path, { trazo: op.color || 'var(--primario)', estilo: `stroke-width:${op.ancho || 5};stroke-linejoin:round;stroke-linecap:round;${op.discontinua ? 'stroke-dasharray:' + op.discontinua : ''}` });
      const marcas = [];
      if (op.marcador !== null) {
        for (const p of puntos) {
          const X = this.sx(p[0]), Y = this.sy(p[1]);
          const r = op.radio || 11;
          let m;
          if (op.marcador === 'cuadro') m = svg('rect', { x: X - r, y: Y - r, width: 2 * r, height: 2 * r, rx: 3 }, this.gSobre);
          else if (op.marcador === 'rombo') m = svg('path', { d: `M${X},${Y - r * 1.3}L${X + r * 1.3},${Y}L${X},${Y + r * 1.3}L${X - r * 1.3},${Y}Z` }, this.gSobre);
          else m = svg('circle', { cx: X, cy: Y, r }, this.gSobre);
          estilo(m, { relleno: op.relleno || 'var(--fondo)', trazo: op.color || 'var(--primario)', estilo: 'stroke-width:4' });
          m.__p = p;
          marcas.push(m);
        }
      }
      return { g, path, marcas, puntos };
    }
    animar(serie, op) {
      op = op || {};
      const dur = op.dur || 1100, ret = op.retraso || 0;
      EF.trazar(serie.path, { dur, retraso: ret });
      serie.marcas.forEach((m, k) => {
        m.style.opacity = '0';
        EF.tween({ dur: 320, retraso: ret + (dur * (k + 0.5)) / Math.max(1, serie.marcas.length), curva: 'sale', cada: (e) => { m.style.opacity = String(e); } });
      });
      return EF.esperar(dur + ret);
    }
    hLinea(v, op) {
      op = op || {};
      const l = svg('line', { x1: this.px0, x2: this.px1, y1: this.sy(v), y2: this.sy(v) }, this.gDatos);
      return estilo(l, { trazo: op.color || 'var(--texto-3)', estilo: `stroke-width:${op.ancho || 3};stroke-dasharray:${op.discontinua || '12 10'}` });
    }
    vLinea(v, op) {
      op = op || {};
      const l = svg('line', { x1: this.sx(v), x2: this.sx(v), y1: this.py0, y2: this.py1 }, this.gDatos);
      return estilo(l, { trazo: op.color || 'var(--texto-3)', estilo: `stroke-width:${op.ancho || 3};stroke-dasharray:${op.discontinua || '12 10'}` });
    }
    banda(v0, v1, op) {
      op = op || {};
      const r = svg('rect', { x: this.px0, width: this.px1 - this.px0, y: this.sy(Math.max(v0, v1)), height: Math.abs(this.sy(v0) - this.sy(v1)) }, this.gFondo);
      return estilo(r, { relleno: op.color || 'var(--acento-suave)' });
    }
    texto(x, y, txt, op) {
      op = op || {};
      const t = svg('text', { x: op.px ? x : this.sx(x), y: op.px ? y : this.sy(y), 'text-anchor': op.ancla || 'start', text: txt }, this.gSobre);
      return estilo(t, { relleno: op.color || 'var(--texto-2)', estilo: `font:${op.peso || 650} ${op.tam || 26}px var(--fuente)` });
    }
    /** Triángulo de pendiente en ejes log-log: parte de (x0,y0), avanza una década en x. */
    pendiente(x0, y0, m, op) {
      op = op || {};
      const x1 = x0 * (op.factor || 10);
      const y1 = y0 * Math.pow(x1 / x0, m);
      const g = svg('g', {}, this.gSobre);
      const d = `M${this.sx(x0)},${this.sy(y0)}L${this.sx(x1)},${this.sy(y0)}L${this.sx(x1)},${this.sy(y1)}Z`;
      estilo(svg('path', { d }, g), { relleno: op.relleno || 'none', trazo: op.color || 'var(--texto-3)', estilo: 'stroke-width:2.5' });
      const t = svg('text', { x: this.sx(x1) + 14, y: (this.sy(y0) + this.sy(y1)) / 2 + 9, text: op.etiqueta || EF.fmt(m, 0) }, g);
      estilo(t, { relleno: op.color || 'var(--texto-2)', estilo: 'font:750 28px var(--fuente)' });
      return g;
    }
    leyenda(items, x, y, op) {
      op = op || {};
      const g = svg('g', { transform: `translate(${x},${y})` }, this.gSobre);
      items.forEach((it, k) => {
        const Y = k * (op.salto || 44);
        const l = svg('line', { x1: 0, x2: 44, y1: Y, y2: Y }, g);
        estilo(l, { trazo: it.color, estilo: `stroke-width:5;${it.discontinua ? 'stroke-dasharray:' + it.discontinua : ''}` });
        if (it.marcador !== null) estilo(svg('circle', { cx: 22, cy: Y, r: 9 }, g), { relleno: 'var(--fondo)', trazo: it.color, estilo: 'stroke-width:4' });
        estilo(svg('text', { x: 60, y: Y + 9, text: it.texto }, g), { relleno: 'var(--texto-2)', estilo: `font:650 ${op.tam || 26}px var(--fuente)` });
      });
      return g;
    }
  }

  /** Escribe el texto en un <text> SVG con los subíndices («u_y») como tspan. */
  function textoConSub(el, texto) {
    for (const p of EF.partesSub(texto)) {
      const ts = svg('tspan', { text: p.t }, el);
      if (p.sub) { ts.setAttribute('baseline-shift', 'sub'); ts.setAttribute('font-size', '72%'); }
    }
  }

  function niceStep(raw) {
    const p = Math.pow(10, Math.floor(Math.log10(raw)));
    const f = raw / p;
    return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p;
  }

  EF.Grafico = Grafico;
  EF.estiloSvg = estilo;
})();
