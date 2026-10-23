/* =====================================================================
   mef.js — funciones de forma Q4/Q9 y un lienzo para dibujar mallas de
   elementos finitos: malla, deformada, apoyos, cargas y contornos con la
   paleta jet, interpolados dentro de cada elemento (sombreado continuo,
   el mismo criterio del post-proceso de EduFEM).
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;

  // ------------------------------------------------------------------ funciones de forma
  const Q4 = {
    N: (x, e) => [0.25 * (1 - x) * (1 - e), 0.25 * (1 + x) * (1 - e), 0.25 * (1 + x) * (1 + e), 0.25 * (1 - x) * (1 + e)],
    dN: (x, e) => [
      [-0.25 * (1 - e), 0.25 * (1 - e), 0.25 * (1 + e), -0.25 * (1 + e)],
      [-0.25 * (1 - x), -0.25 * (1 + x), 0.25 * (1 + x), 0.25 * (1 - x)],
    ],
    nat: [[-1, -1], [1, -1], [1, 1], [-1, 1]],
  };
  const Q9 = {
    N: (x, e) => {
      const lx = [0.5 * x * (x - 1), 1 - x * x, 0.5 * x * (x + 1)];
      const le = [0.5 * e * (e - 1), 1 - e * e, 0.5 * e * (e + 1)];
      // orden del motor: esquinas (a.h.), medios (inf., der., sup., izq.), centro
      return [lx[0] * le[0], lx[2] * le[0], lx[2] * le[2], lx[0] * le[2],
        lx[1] * le[0], lx[2] * le[1], lx[1] * le[2], lx[0] * le[1], lx[1] * le[1]];
    },
    dN: (x, e) => {
      const lx = [0.5 * x * (x - 1), 1 - x * x, 0.5 * x * (x + 1)];
      const le = [0.5 * e * (e - 1), 1 - e * e, 0.5 * e * (e + 1)];
      const dx = [x - 0.5, -2 * x, x + 0.5];
      const de = [e - 0.5, -2 * e, e + 0.5];
      const I = [[0, 0], [2, 0], [2, 2], [0, 2], [1, 0], [2, 1], [1, 2], [0, 1], [1, 1]];
      return [I.map(([a, b]) => dx[a] * le[b]), I.map(([a, b]) => lx[a] * de[b])];
    },
    nat: [[-1, -1], [1, -1], [1, 1], [-1, 1], [0, -1], [1, 0], [0, 1], [-1, 0], [0, 0]],
  };
  EF.Q4 = Q4; EF.Q9 = Q9;
  EF.formas = (n) => (n === 9 ? Q9 : Q4);

  /** J = dN · X (convención de Bathe, la del motor). */
  EF.jacobiano = function (dN, X) {
    let a = 0, b = 0, c = 0, d = 0;
    for (let i = 0; i < X.length; i++) {
      a += dN[0][i] * X[i][0]; b += dN[0][i] * X[i][1];
      c += dN[1][i] * X[i][0]; d += dN[1][i] * X[i][1];
    }
    const det = a * d - b * c;
    return { J: [[a, b], [c, d]], det, inv: [[d / det, -b / det], [-c / det, a / det]] };
  };
  EF.matB = function (dN, inv) {
    const n = dN[0].length;
    const B = [new Array(2 * n).fill(0), new Array(2 * n).fill(0), new Array(2 * n).fill(0)];
    for (let i = 0; i < n; i++) {
      const dx = inv[0][0] * dN[0][i] + inv[0][1] * dN[1][i];
      const dy = inv[1][0] * dN[0][i] + inv[1][1] * dN[1][i];
      B[0][2 * i] = dx; B[1][2 * i + 1] = dy; B[2][2 * i] = dy; B[2][2 * i + 1] = dx;
    }
    return B;
  };
  EF.interp = function (N, vals) { let s = 0; for (let i = 0; i < N.length; i++) s += N[i] * vals[i]; return s; };

  // ------------------------------------------------------------------ lienzo MEF
  class LienzoMEF {
    /** contenedor: elemento donde se inserta el canvas; ancho/alto en px de diseño. */
    constructor(contenedor, ancho, alto, op) {
      this.op = op || {};
      this.W = ancho; this.H = alto;
      this.canvas = EF.el('canvas', { class: 'viz', style: `width:${ancho}px;height:${alto}px` });
      contenedor.appendChild(this.canvas);
      // los campos se pintan píxel a píxel (getImageData/putImageData): lienzo en memoria de CPU
      this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
      this.redimensionar();
      this.vista = { s: 1, ox: 0, oy: 0 };
    }
    redimensionar() {
      const r = EF.escalaRender();
      if (this.r === r && this.canvas.width) return false;
      this.r = r;
      this.canvas.width = Math.round(this.W * r);
      this.canvas.height = Math.round(this.H * r);
      return true;
    }
    /** Ajusta la vista para que la caja [x0,x1]x[y0,y1] entre con márgenes (y hacia arriba). */
    encuadrar(x0, x1, y0, y1, pad) {
      pad = pad || { s: 40, d: 40, i: 40, iz: 40 };
      if (typeof pad === 'number') pad = { s: pad, d: pad, i: pad, iz: pad };
      const w = this.W - pad.iz - pad.d, h = this.H - pad.s - pad.i;
      const s = Math.min(w / (x1 - x0 || 1), h / (y1 - y0 || 1));
      this.vista = {
        s,
        ox: pad.iz + (w - s * (x1 - x0)) / 2 - s * x0,
        oy: pad.s + (h - s * (y1 - y0)) / 2 + s * y1,
      };
      return this;
    }
    X(x) { return this.vista.ox + this.vista.s * x; }
    Y(y) { return this.vista.oy - this.vista.s * y; }
    aMundo(px, py) { return [(px - this.vista.ox) / this.vista.s, (this.vista.oy - py) / this.vista.s]; }
    inicio(fondo) {
      const c = this.ctx;
      c.setTransform(this.r, 0, 0, this.r, 0, 0);
      c.clearRect(0, 0, this.W, this.H);
      if (fondo) { c.fillStyle = fondo; c.fillRect(0, 0, this.W, this.H); }
      return c;
    }

    /** Posición deformada de un nodo. */
    static pos(nodos, u, esc, i) {
      const p = nodos[i];
      return u && esc ? [p[0] + esc * u[i][0], p[1] + esc * u[i][1]] : p;
    }

    /**
     * Contorno continuo de `valores` (uno por nodo). Cada elemento se subdivide en
     * sub x sub celdas con sus funciones de forma (bordes curvos del Q9 incluidos)
     * y cada triángulo se pinta interpolando el valor punto a punto.
     */
    campo(nodos, elems, valores, op) {
      op = op || {};
      const vmin = op.min != null ? op.min : Math.min(...valores);
      const vmax = op.max != null ? op.max : Math.max(...valores);
      const rango = vmax - vmin || 1;
      const u = op.u, esc = op.escala || 0;
      const sub = op.sub || (elems[0].length === 9 ? 4 : 2);
      const r = this.r;
      const Wp = this.canvas.width, Hp = this.canvas.height;
      const img = this.ctx.getImageData(0, 0, Wp, Hp);
      const buf = img.data;
      const alfa = Math.round(255 * (op.alfa == null ? 1 : op.alfa));
      const LUT = EF.jetLUT;
      const vs = this.vista;
      const tri = (ax, ay, av, bx, by, bv, cx, cy, cv) => {
        const minx = Math.max(0, Math.floor(Math.min(ax, bx, cx))), maxx = Math.min(Wp - 1, Math.ceil(Math.max(ax, bx, cx)));
        const miny = Math.max(0, Math.floor(Math.min(ay, by, cy))), maxy = Math.min(Hp - 1, Math.ceil(Math.max(ay, by, cy)));
        const den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy);
        if (Math.abs(den) < 1e-12) return;
        const inv = 1 / den;
        for (let y = miny; y <= maxy; y++) {
          const py = y + 0.5;
          for (let x = minx; x <= maxx; x++) {
            const px = x + 0.5;
            const l1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) * inv;
            const l2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) * inv;
            const l3 = 1 - l1 - l2;
            if (l1 < -1e-4 || l2 < -1e-4 || l3 < -1e-4) continue;
            const v = l1 * av + l2 * bv + l3 * cv;
            const k = Math.max(0, Math.min(255, Math.round(((v - vmin) / rango) * 255))) * 3;
            const o = (y * Wp + x) * 4;
            buf[o] = LUT[k]; buf[o + 1] = LUT[k + 1]; buf[o + 2] = LUT[k + 2]; buf[o + 3] = alfa;
          }
        }
      };
      for (const con of elems) {
        const fam = EF.formas(con.length);
        const P = con.map((i) => LienzoMEF.pos(nodos, u, esc, i));
        const V = con.map((i) => valores[i]);
        const grid = [];
        for (let a = 0; a <= sub; a++) {
          const fila = [];
          for (let b = 0; b <= sub; b++) {
            const xi = -1 + (2 * b) / sub, eta = -1 + (2 * a) / sub;
            const N = fam.N(xi, eta);
            let x = 0, y = 0, v = 0;
            for (let k = 0; k < N.length; k++) { x += N[k] * P[k][0]; y += N[k] * P[k][1]; v += N[k] * V[k]; }
            fila.push([(vs.ox + vs.s * x) * r, (vs.oy - vs.s * y) * r, v]);
          }
          grid.push(fila);
        }
        for (let a = 0; a < sub; a++) for (let b = 0; b < sub; b++) {
          const p00 = grid[a][b], p01 = grid[a][b + 1], p11 = grid[a + 1][b + 1], p10 = grid[a + 1][b];
          tri(p00[0], p00[1], p00[2], p01[0], p01[1], p01[2], p11[0], p11[1], p11[2]);
          tri(p00[0], p00[1], p00[2], p11[0], p11[1], p11[2], p10[0], p10[1], p10[2]);
        }
      }
      this.ctx.putImageData(img, 0, 0);
      return { vmin, vmax };
    }

    /** Relleno plano por elemento (p. ej. error por elemento o calidad). */
    rellenoElementos(nodos, elems, valores, op) {
      op = op || {};
      const c = this.ctx;
      const vmin = op.min != null ? op.min : Math.min(...valores);
      const vmax = op.max != null ? op.max : Math.max(...valores);
      const lg = op.log;
      elems.forEach((con, k) => {
        let t = lg ? (Math.log10(valores[k]) - Math.log10(vmin)) / (Math.log10(vmax) - Math.log10(vmin)) : (valores[k] - vmin) / (vmax - vmin || 1);
        c.fillStyle = op.color ? op.color(t, k) : EF.jetCss(t, op.alfa == null ? 1 : op.alfa);
        this._contorno(nodos, con, op.u, op.escala);
        c.fill();
      });
    }

    _contorno(nodos, con, u, esc) {
      const c = this.ctx;
      c.beginPath();
      const fam = EF.formas(con.length);
      const P = con.map((i) => LienzoMEF.pos(nodos, u, esc, i));
      if (con.length === 4) {
        P.forEach((p, k) => (k ? c.lineTo(this.X(p[0]), this.Y(p[1])) : c.moveTo(this.X(p[0]), this.Y(p[1]))));
      } else {
        // borde curvo del Q9: se recorre el contorno natural con sus funciones de forma
        const bordes = [[[-1, -1], [1, -1]], [[1, -1], [1, 1]], [[1, 1], [-1, 1]], [[-1, 1], [-1, -1]]];
        let primero = true;
        for (const [a, b] of bordes) {
          for (let s = 0; s <= 8; s++) {
            const t = s / 8, xi = a[0] + (b[0] - a[0]) * t, eta = a[1] + (b[1] - a[1]) * t;
            const N = fam.N(xi, eta);
            let x = 0, y = 0;
            for (let k = 0; k < 9; k++) { x += N[k] * P[k][0]; y += N[k] * P[k][1]; }
            if (primero) { c.moveTo(this.X(x), this.Y(y)); primero = false; } else c.lineTo(this.X(x), this.Y(y));
          }
        }
      }
      c.closePath();
    }

    malla(nodos, elems, op) {
      op = op || {};
      const c = this.ctx;
      c.save();
      c.strokeStyle = op.color || EF.css('--malla');
      c.lineWidth = op.ancho || 1.6;
      c.globalAlpha = op.alfa == null ? 1 : op.alfa;
      if (op.discontinua) c.setLineDash(op.discontinua);
      c.lineJoin = 'round';
      for (const con of elems) { this._contorno(nodos, con, op.u, op.escala); c.stroke(); }
      if (op.relleno) {
        c.globalAlpha = op.alfaRelleno || 0.12;
        c.fillStyle = op.relleno;
        for (const con of elems) { this._contorno(nodos, con, op.u, op.escala); c.fill(); }
      }
      c.restore();
    }

    elemento(nodos, con, op) {
      op = op || {};
      const c = this.ctx;
      c.save();
      this._contorno(nodos, con, op.u, op.escala);
      if (op.relleno) { c.globalAlpha = op.alfaRelleno == null ? 0.25 : op.alfaRelleno; c.fillStyle = op.relleno; c.fill(); c.globalAlpha = 1; }
      if (op.color) { c.strokeStyle = op.color; c.lineWidth = op.ancho || 3; if (op.brillo) { c.shadowColor = op.color; c.shadowBlur = op.brillo; } c.stroke(); }
      c.restore();
    }

    nodos(nodos, indices, op) {
      op = op || {};
      const c = this.ctx;
      c.save();
      const r = op.radio || 5;
      for (const i of indices) {
        const p = LienzoMEF.pos(nodos, op.u, op.escala, i);
        c.beginPath();
        c.arc(this.X(p[0]), this.Y(p[1]), r, 0, 2 * Math.PI);
        c.fillStyle = op.relleno || EF.css('--lienzo');
        c.fill();
        c.lineWidth = op.ancho || 2.5;
        c.strokeStyle = op.color || EF.css('--nodo');
        c.stroke();
      }
      c.restore();
    }

    etiqueta(x, y, txt, op) {
      op = op || {};
      const c = this.ctx;
      c.save();
      c.font = `${op.peso || 700} ${op.tam || 22}px ${EF.fuente()}`;
      c.textAlign = op.ancla || 'left';
      c.textBaseline = op.base || 'middle';
      const X = this.X(x) + (op.dx || 0), Y = this.Y(y) + (op.dy || 0);
      if (op.fondo) {
        const m = c.measureText(txt);
        const w = m.width + 14, h = (op.tam || 22) + 10;
        const x0 = op.ancla === 'center' ? X - w / 2 : op.ancla === 'right' ? X - w + 7 : X - 7;
        c.fillStyle = op.fondo; c.globalAlpha = op.alfaFondo || 0.85;
        c.beginPath(); c.roundRect(x0, Y - h / 2, w, h, 6); c.fill(); c.globalAlpha = 1;
        if (op.borde) { c.strokeStyle = op.borde; c.lineWidth = 1.5; c.stroke(); }
      }
      c.fillStyle = op.color || EF.css('--texto');
      if (txt.indexOf('_') < 0) c.fillText(txt, X, Y);
      else {
        // subíndices: se mide el total y se dibuja por tramos alineados a la izquierda
        const tam = op.tam || 22, peso = op.peso || 700;
        const partes = EF.partesSub(txt);
        const fuente = (sub) => `${peso} ${sub ? Math.round(tam * 0.7) : tam}px ${EF.fuente()}`;
        let total = 0;
        for (const p of partes) { c.font = fuente(p.sub); p.w = c.measureText(p.t).width; total += p.w; }
        let x = op.ancla === 'center' ? X - total / 2 : op.ancla === 'right' ? X - total : X;
        c.textAlign = 'left';
        for (const p of partes) { c.font = fuente(p.sub); c.fillText(p.t, x, Y + (p.sub ? tam * 0.28 : 0)); x += p.w; }
      }
      c.restore();
    }

    /** Apoyo: triángulo naranja bajo el nodo (fijo) o con rodillos (móvil). */
    apoyo(x, y, op) {
      op = op || {};
      const c = this.ctx;
      const X = this.X(x), Y = this.Y(y), s = op.tam || 16;
      c.save();
      c.strokeStyle = op.color || EF.css('--apoyo');
      c.fillStyle = EF.rgba(op.color || EF.css('--apoyo'), 0.25);
      c.lineWidth = 3;
      const giro = op.giro || 0;
      c.translate(X, Y); c.rotate(giro);
      c.beginPath(); c.moveTo(0, 0); c.lineTo(-s, 1.5 * s); c.lineTo(s, 1.5 * s); c.closePath(); c.fill(); c.stroke();
      if (op.movil) { for (const dx of [-s * 0.55, s * 0.55]) { c.beginPath(); c.arc(dx, 1.5 * s + 6, 5, 0, 2 * Math.PI); c.stroke(); } }
      c.beginPath(); c.moveTo(-s * 1.4, 1.5 * s + (op.movil ? 13 : 2)); c.lineTo(s * 1.4, 1.5 * s + (op.movil ? 13 : 2)); c.stroke();
      c.restore();
    }

    /** Empotramiento: rayado a lo largo de una recta vertical x = x0 entre y0 e y1. */
    empotramiento(x0, y0, y1, op) {
      op = op || {};
      const c = this.ctx;
      const X = this.X(x0), Ya = this.Y(y0), Yb = this.Y(y1);
      c.save();
      c.strokeStyle = op.color || EF.css('--apoyo');
      c.lineWidth = 3;
      c.beginPath(); c.moveTo(X, Ya); c.lineTo(X, Yb); c.stroke();
      c.lineWidth = 2;
      for (let y = Math.min(Ya, Yb); y <= Math.max(Ya, Yb); y += 14) { c.beginPath(); c.moveTo(X, y); c.lineTo(X - 14, y + 12); c.stroke(); }
      c.restore();
    }

    /** Flecha de carga que termina en (x, y), con dirección (dx, dy) en pantalla. */
    flecha(x, y, dx, dy, op) {
      op = op || {};
      const c = this.ctx;
      const X = this.X(x), Y = this.Y(y);
      const L = op.largo || 70;
      const n = Math.hypot(dx, dy) || 1;
      const ux = dx / n, uy = -dy / n;
      const X0 = X - ux * L, Y0 = Y - uy * L;
      c.save();
      c.strokeStyle = op.color || EF.css('--carga');
      c.fillStyle = op.color || EF.css('--carga');
      c.lineWidth = op.ancho || 4;
      c.beginPath(); c.moveTo(X0, Y0); c.lineTo(X - ux * 14, Y - uy * 14); c.stroke();
      c.beginPath(); c.moveTo(X, Y);
      c.lineTo(X - ux * 20 - uy * 10, Y - uy * 20 + ux * 10);
      c.lineTo(X - ux * 20 + uy * 10, Y - uy * 20 - ux * 10);
      c.closePath(); c.fill();
      if (op.texto) {
        c.font = `700 ${op.tam || 22}px ${EF.fuente()}`;
        c.textAlign = 'center';
        c.fillText(op.texto, X0 - ux * 10 + (op.dxTexto || 0), Y0 - uy * 10 - 10);
      }
      c.restore();
    }
  }
  EF.LienzoMEF = LienzoMEF;

  // ------------------------------------------------------------------ barra de color
  /** Barra de color jet en SVG. Devuelve {svg, actualizar(min, max)} */
  EF.barraColor = function (contenedor, op) {
    op = op || {};
    const W = op.ancho || 150, H = op.alto || 420;
    const s = EF.svg('svg', { class: 'viz', width: W, height: H + 70, viewBox: `0 0 ${W} ${H + 70}` }, contenedor);
    const id = 'jet' + Math.random().toString(36).slice(2, 8);
    const defs = EF.svg('defs', {}, s);
    const lg = EF.svg('linearGradient', { id, x1: 0, y1: 1, x2: 0, y2: 0 }, defs);
    for (let k = 0; k <= 10; k++) EF.svg('stop', { offset: k / 10, 'stop-color': EF.jetCss(k / 10) }, lg);
    const tit = EF.svg('text', { x: 0, y: 26, text: op.titulo || '' }, s);
    EF.estiloSvg(tit, { relleno: 'var(--texto-2)', estilo: 'font:700 24px var(--fuente)' });
    EF.svg('rect', { x: 0, y: 44, width: 34, height: H, rx: 6, fill: `url(#${id})` }, s);
    const g = EF.svg('g', {}, s);
    function actualizar(min, max, dec) {
      g.innerHTML = '';
      const n = op.divisiones || 5;
      for (let k = 0; k <= n; k++) {
        const v = min + ((max - min) * k) / n;
        const y = 44 + H - (H * k) / n;
        EF.estiloSvg(EF.svg('line', { x1: 34, x2: 44, y1: y, y2: y }, g), { trazo: 'var(--texto-3)', estilo: 'stroke-width:2' });
        EF.estiloSvg(EF.svg('text', { x: 52, y: y + 8, text: op.fmt ? op.fmt(v) : EF.fmt(v, dec == null ? 1 : dec) }, g),
          { relleno: 'var(--texto-2)', estilo: 'font:600 22px var(--fuente);font-variant-numeric:tabular-nums' });
      }
    }
    return { svg: s, actualizar };
  };
})();
