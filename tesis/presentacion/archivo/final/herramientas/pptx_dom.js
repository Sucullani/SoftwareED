/* =====================================================================
   pptx_dom.js — se inyecta en la presentación (modo captura) y describe la
   lámina activa, en su paso actual, como una lista de primitivas que
   construir_pptx.py convierte en formas nativas de PowerPoint:

     caja    rectángulo o elipse con relleno, borde, esquinas redondeadas
     texto   cuadro de texto con sus líneas tal como las cortó el navegador
     img     imagen de archivo (PNG/JPG) con su recorte
     raster  región que se fotografía aparte (SVG, lienzos, fórmulas KaTeX)
     video   video del software (MP4) con su cuadro de portada
     enlace  zona con clic hacia otra lámina

   Coordenadas en px de diseño (lámina de 1920 × 1080). Nada de esto se
   carga en la presentación: lo usa herramientas/extraer_pptx.mjs.
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;

  // ------------------------------------------------------------------ utilidades
  const esc = () => document.getElementById('escenario');
  const lamina = () => document.querySelector('.lamina.activa');
  function rel(r) {
    const e = esc().getBoundingClientRect();
    const s = (EF.Deck && EF.Deck.escala) || 1;
    return { x: (r.left - e.left) / s, y: (r.top - e.top) / s, w: r.width / s, h: r.height / s };
  }
  const redondear = (v) => Math.round(v * 100) / 100;

  /** Color CSS calculado -> {hex, a} (null si es transparente). */
  function color(c) {
    if (!c || c === 'transparent') return null;
    let r, g, b, a = 1;
    let m = c.match(/^rgba?\(([^)]+)\)$/);
    if (m) {
      const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number);
      [r, g, b] = p; if (p.length > 3) a = p[3];
    } else if ((m = c.match(/^color\(srgb\s+([^)]+)\)$/))) {
      const [rgb, al] = m[1].split('/');
      const p = rgb.trim().split(/\s+/).map(Number);
      [r, g, b] = p.map((v) => v * 255); if (al) a = Number(al);
    } else return null;
    if (!(a > 0.004)) return null;
    const h = (v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0');
    return { hex: '#' + h(r) + h(g) + h(b), a: redondear(a) };
  }
  /** Separa la lista de argumentos de un gradiente respetando paréntesis. */
  function partirArgs(s) {
    const out = []; let n = 0, ini = 0;
    for (let i = 0; i < s.length; i++) {
      if (s[i] === '(') n++; else if (s[i] === ')') n--;
      else if (s[i] === ',' && n === 0) { out.push(s.slice(ini, i).trim()); ini = i + 1; }
    }
    out.push(s.slice(ini).trim());
    return out;
  }
  /** linear-gradient / repeating-linear-gradient -> descripción del relleno. */
  function gradiente(img) {
    const rep = img.startsWith('repeating-linear-gradient(');
    if (!rep && !img.startsWith('linear-gradient(')) return null;
    const dentro = img.slice(img.indexOf('(') + 1, img.lastIndexOf(')'));
    const args = partirArgs(dentro);
    let ang = 180;
    if (/^-?[\d.]+deg$/.test(args[0])) { ang = parseFloat(args[0]); args.shift(); }
    else if (/^to /.test(args[0])) {
      ang = { 'to top': 0, 'to right': 90, 'to bottom': 180, 'to left': 270 }[args[0]] ?? 180; args.shift();
    }
    const paradas = args.map((a) => {
      const m = a.match(/^(.*\))\s*([\d.]+(?:%|px))?(?:\s+([\d.]+(?:%|px)))?$/) || a.match(/^(\S+)\s*([\d.]+(?:%|px))?/);
      const c = color(m ? m[1] : a) || { hex: '#ffffff', a: 0 };
      return { c, pos: m && m[2] ? parseFloat(m[2]) : null, px: !!(m && m[2] && m[2].endsWith('px')) };
    });
    return { rep, ang, paradas };
  }
  const px = (v) => parseFloat(v) || 0;

  function opacidad(el) {
    let a = 1;
    for (let e = el; e && e !== document.body; e = e.parentElement) a *= Number(getComputedStyle(e).opacity);
    return a;
  }
  function enLamina(el, L) { return L.contains(el); }
  const esInline = (cs) => cs.display === 'inline' || cs.display === 'inline-block' || cs.display === 'inline-flex' || cs.display === 'inline-grid';
  function transformacion(cs) {
    const t = cs.transform;
    if (!t || t === 'none') return null;
    const m = t.match(/^matrix\(([^)]+)\)$/);
    if (!m) return { complejo: true };
    const [a, b, c, d] = m[1].split(',').map(Number);
    const giro = Math.atan2(b, a) * 180 / Math.PI;
    const esc = Math.hypot(a, b);
    if (Math.abs(giro) < 0.05 && Math.abs(esc - 1) < 0.002 && Math.abs(c) < 1e-6 && Math.abs(d - 1) < 0.002) return null;
    return { giro, esc, complejo: Math.abs(esc - 1) > 0.002 };
  }

  // ------------------------------------------------------------------ seudoelementos
  // ::before y ::after no existen en el DOM: se copian como <span> reales, con su estilo
  // calculado, mientras dura la extracción, y el original se apaga.
  let hoja = null;
  function prepararHoja() {
    if (hoja) return;
    hoja = document.createElement('style');
    hoja.textContent = `
      .pptx-sin-antes::before { content: none !important; }
      .pptx-sin-despues::after { content: none !important; }
      html.pptx-aislando, html.pptx-aislando body { background: transparent !important; }
      html.pptx-aislando * { visibility: hidden !important; }
      html.pptx-aislando .pptx-aislado, html.pptx-aislando .pptx-aislado * { visibility: visible !important; }
    `;
    document.head.appendChild(hoja);
  }
  function textoContenido(content, el) {
    if (!content || content === 'none' || content === 'normal') return null;
    if (/^counter\(/.test(content)) {
      const hermanos = Array.from(el.parentElement.children).filter((x) => x.tagName === el.tagName);
      return String(hermanos.indexOf(el) + 1);
    }
    if (content[0] === '"' || content[0] === "'") {
      try { return JSON.parse(content[0] === '"' ? content : '"' + content.slice(1, -1).replace(/"/g, '\\"') + '"'); } catch (e) { return content.slice(1, -1); }
    }
    return null;
  }
  let materializados = [];
  function materializar(L) {
    prepararHoja();
    for (const el of L.querySelectorAll('*')) {
      for (const [ps, clase, antes] of [['::before', 'pptx-sin-antes', true], ['::after', 'pptx-sin-despues', false]]) {
        const cs = getComputedStyle(el, ps);
        const txt = textoContenido(cs.content, el);
        if (txt == null) continue;
        if (cs.display === 'none') continue;
        const sp = document.createElement('span');
        for (let i = 0; i < cs.length; i++) {
          const p = cs[i];
          if (p === 'content') continue;
          sp.style.setProperty(p, cs.getPropertyValue(p));
        }
        sp.textContent = txt;
        sp.setAttribute('data-pptx-seudo', '');
        el.classList.add(clase);
        if (antes) el.insertBefore(sp, el.firstChild); else el.appendChild(sp);
        materializados.push({ el, sp, clase });
      }
    }
  }
  function desmaterializar() {
    for (const m of materializados) { m.sp.remove(); m.el.classList.remove(m.clase); }
    materializados = [];
  }

  // ------------------------------------------------------------------ recorrido
  const SEL_RASTER = 'svg, canvas, video, .katex, .katex-display, [data-raster]';
  let orden = 0, rid = 0;
  let items = [], rasters = [];

  function nuevoRaster(el, r, extra) {
    const id = 'r' + (++rid);
    el.setAttribute('data-pptx-rid', id);
    rasters.push({ rid: id, ...r, canvas: el.tagName === 'CANVAS' });
    items.push({ t: 'raster', rid: id, ...r, orden: orden++, ...extra });
  }

  function marcarEntrada(el, L) {
    const e = el.closest('[data-entrada]');
    return e && L.contains(e) ? Number(e.getAttribute('data-entrada')) : null;
  }

  /** Cuánto se extiende la sombra de un elemento fuera de su caja (px). */
  function extensionSombra(cs) {
    const bs = cs.boxShadow;
    if (!bs || bs === 'none') return 0;
    let e = 0;
    for (const s of partirArgs(bs)) {
      const m = s.match(/(-?[\d.]+)px\s+(-?[\d.]+)px(?:\s+([\d.]+)px)?(?:\s+(-?[\d.]+)px)?/);
      if (!m || /inset/.test(s)) continue;
      e = Math.max(e, Math.max(Math.abs(Number(m[1])), Math.abs(Number(m[2]))) + Number(m[3] || 0) + Math.max(0, Number(m[4] || 0)));
    }
    return Math.ceil(e);
  }

  /** Primera sombra difuminada exterior (box-shadow con blur), para la sombra de PowerPoint. */
  function sombraSuave(cs) {
    const bs = cs.boxShadow;
    if (!bs || bs === 'none') return null;
    for (const s of partirArgs(bs)) {
      const m = s.match(/^((?:rgba?|color)\([^)]*\))\s+(-?[\d.]+)px\s+(-?[\d.]+)px\s+([\d.]+)px(?:\s+(-?[\d.]+)px)?(\s+inset)?$/);
      if (!m || m[6] || !(Number(m[4]) > 0)) continue;
      const c = color(m[1]);
      if (c) return { dx: Number(m[2]), dy: Number(m[3]), blur: Number(m[4]), c };
    }
    return null;
  }

  /** Sombras sin difuminado (anillos): «0 0 0 Npx color» por fuera o «inset» por dentro. */
  function anillos(cs) {
    const bs = cs.boxShadow;
    if (!bs || bs === 'none') return [];
    return partirArgs(bs).map((s) => {
      const m = s.match(/^((?:rgba?|color)\([^)]*\))\s+(-?[\d.]+)px\s+(-?[\d.]+)px\s+([\d.]+)px\s+(-?[\d.]+)px(\s+inset)?$/);
      if (!m) return null;
      const [, c, dx, dy, blur, spread, inset] = m;
      if (Number(dx) || Number(dy) || Number(blur) || !(Number(spread) > 0)) return null;
      const col = color(c);
      return col ? { c: col, w: Number(spread), inset: !!inset } : null;
    }).filter(Boolean);
  }

  /** Caja (fondo y bordes) de un elemento. */
  function caja(el, cs, L, alfa, rects) {
    const ans = anillos(cs);
    if (ans.length && rects.length === 1) {
      const r = rel(rects[0]);
      const radios0 = ['TopLeft', 'TopRight', 'BottomRight', 'BottomLeft'].map((k) => cs[`border${k}Radius`]).map((v) => (/%$/.test(v) ? parseFloat(v) / 100 * Math.min(r.w, r.h) : px(v)));
      for (const a of ans.filter((q) => !q.inset)) {
        // anillo exterior: una forma rellena un poco más grande, detrás de la caja
        items.push({ t: 'caja', x: redondear(r.x - a.w), y: redondear(r.y - a.w), w: redondear(r.w + 2 * a.w), h: redondear(r.h + 2 * a.w), giro: 0,
          fondo: a.c, grad: null, lados: [null, null, null, null], radios: radios0.map((v) => redondear(v > 0 ? v + a.w : 0)), alfa: redondear(alfa),
          entrada: marcarEntrada(el, L), orden: orden++, z: zIndice(el, L) });
      }
    }
    cajaSimple(el, cs, L, alfa, rects);
    if (ans.length && rects.length === 1) {
      const r = rel(rects[0]);
      const bl = px(cs.borderLeftWidth), bt = px(cs.borderTopWidth), brr = px(cs.borderRightWidth), bb = px(cs.borderBottomWidth);
      const radios0 = ['TopLeft', 'TopRight', 'BottomRight', 'BottomLeft'].map((k) => cs[`border${k}Radius`]).map((v) => (/%$/.test(v) ? parseFloat(v) / 100 * Math.min(r.w, r.h) : px(v)));
      for (const a of ans.filter((q) => q.inset)) {
        // anillo interior: un borde por dentro de la caja
        const lado = { w: a.w, c: a.c, estilo: 'solid' };
        items.push({ t: 'caja', x: redondear(r.x + bl), y: redondear(r.y + bt), w: redondear(r.w - bl - brr), h: redondear(r.h - bt - bb), giro: 0,
          fondo: null, grad: null, lados: [lado, lado, lado, lado], radios: radios0.map((v) => redondear(Math.max(0, v - bl))), alfa: redondear(alfa),
          entrada: marcarEntrada(el, L), orden: orden++, z: zIndice(el, L) });
      }
    }
  }

  function cajaSimple(el, cs, L, alfa, rects) {
    const fondo = color(cs.backgroundColor);
    const img = cs.backgroundImage && cs.backgroundImage !== 'none' ? gradiente(cs.backgroundImage) : null;
    const lados = ['Top', 'Right', 'Bottom', 'Left'].map((s) => {
      const w = px(cs[`border${s}Width`]);
      const st = cs[`border${s}Style`];
      const c = color(cs[`border${s}Color`]);
      return w > 0 && st !== 'none' && st !== 'hidden' && c ? { w: redondear(w), c, estilo: st } : null;
    });
    if (!fondo && !img && !lados.some(Boolean)) return;
    // la sombra solo tiene sentido con un relleno opaco que la tape por dentro
    const sombra = fondo && fondo.a > 0.9 ? sombraSuave(cs) : null;
    const radios = ['TopLeft', 'TopRight', 'BottomRight', 'BottomLeft'].map((k) => cs[`border${k}Radius`]);
    const tr = transformacion(cs);
    for (const rr of rects) {
      const r = rel(rr);
      if (r.w < 0.5 || r.h < 0.5) continue;
      const rad = radios.map((v) => (/%$/.test(v) ? parseFloat(v) / 100 * Math.min(r.w, r.h) : px(v)));
      let x = r.x, y = r.y, w = r.w, h = r.h, giro = 0;
      if (tr && !tr.complejo && Math.abs(tr.giro) > 0.05) {
        // la caja girada: tamaño de diseño y centro del rectángulo envolvente
        w = el.offsetWidth; h = el.offsetHeight; giro = tr.giro;
        x = r.x + r.w / 2 - w / 2; y = r.y + r.h / 2 - h / 2;
      }
      items.push({
        t: 'caja', x: redondear(x), y: redondear(y), w: redondear(w), h: redondear(h), giro: redondear(giro),
        fondo, grad: img, lados, radios: rad.map(redondear), alfa: redondear(alfa), sombra,
        entrada: marcarEntrada(el, L), orden: orden++, z: zIndice(el, L),
      });
    }
  }

  function zIndice(el, L) {
    let z = 0;
    for (let e = el; e && e !== L; e = e.parentElement) {
      const zi = getComputedStyle(e).zIndex;
      if (zi !== 'auto' && getComputedStyle(e).position !== 'static') { z = Number(zi) || 0; break; }
    }
    return z;
  }

  // ---------------------------------------------------------------- texto
  function familia(ff) {
    const f = (ff || '').split(',')[0].replace(/["']/g, '').trim();
    if (/consolas|cascadia|mono/i.test(f)) return 'Consolas';
    if (/cambria/i.test(f)) return 'Cambria';
    return 'Calibri';
  }
  function estiloRun(el, base) {
    const cs = getComputedStyle(el);
    let desp = null;
    for (let e = el; e && e !== base; e = e.parentElement) {
      if (e.tagName === 'SUB' || getComputedStyle(e).verticalAlign === 'sub') { desp = 'sub'; break; }
      if (e.tagName === 'SUP' || getComputedStyle(e).verticalAlign === 'super') { desp = 'sup'; break; }
    }
    let tam = px(cs.fontSize);
    if (desp) { const p = el.closest('sub, sup'); tam = p && p.parentElement ? px(getComputedStyle(p.parentElement).fontSize) : tam / 0.83; }
    const c = color(cs.color) || { hex: '#000000', a: 1 };
    const deco = cs.textDecorationLine || '';
    return {
      f: familia(cs.fontFamily), tam: redondear(tam), n: Number(cs.fontWeight) >= 600, i: cs.fontStyle === 'italic',
      c: c.hex, a: c.a, may: cs.textTransform === 'uppercase', esp: redondear(px(cs.letterSpacing) || 0),
      desp, sub: deco.includes('underline'),
    };
  }
  /** ¿El contenedor mezcla, en sus mismas líneas, texto con algo que no se puede escribir como
   *  texto (una fórmula, un SVG o una imagen en línea)? Entonces va entero como imagen. Un SVG
   *  solo en su línea no cuenta: va como imagen y el texto de los bloques vecinos sigue editable. */
  function tieneRasterEnLinea(el) {
    let raster = false;
    for (const r of el.querySelectorAll(SEL_RASTER + ', img')) {
      let b = r.parentElement;
      while (b && b !== el && esInline(getComputedStyle(b))) b = b.parentElement;
      if (b === el) { raster = true; break; }
    }
    return raster && tieneTextoEnLinea(el);
  }
  function tieneTextoEnLinea(el) {
    for (const n of el.childNodes) {
      if (n.nodeType === 3 && n.textContent.trim()) return true;
      if (n.nodeType === 1 && !n.matches(SEL_RASTER) && n.tagName !== 'IMG') {
        const cs = getComputedStyle(n);
        if (cs.display !== 'none' && esInline(cs) && tieneTextoEnLinea(n)) return true;
      }
    }
    return false;
  }
  /** Rectángulo que abarca el elemento y todo lo que dibuja, aunque desborde su caja. */
  function envolvente(el) {
    const r0 = el.getBoundingClientRect();
    let x0 = r0.left, y0 = r0.top, x1 = r0.right, y1 = r0.bottom;
    for (const d of el.querySelectorAll('*')) {
      const r = d.getBoundingClientRect();
      if (!r.width && !r.height) continue;
      x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom);
    }
    return rel({ left: x0, top: y0, width: x1 - x0, height: y1 - y0 });
  }
  /** Palabras del contenido en línea de un contenedor, con su estilo y su rectángulo. */
  function palabras(cont) {
    const out = [];
    let pendienteEspacio = false;
    const visitar = (nodo, estiloPadre) => {
      for (const n of nodo.childNodes) {
        if (n.nodeType === 3) {
          const t = n.textContent;
          const cs = getComputedStyle(n.parentElement);
          if (cs.visibility !== 'visible') continue;
          const re = /[^ \t\n\r\f]+/g; let m, ultimo = 0;
          while ((m = re.exec(t))) {
            if (m.index > ultimo || (m.index === 0 && /^[ \t\n\r\f]/.test(t))) pendienteEspacio = true;
            if (m.index > 0 && /[ \t\n\r\f]/.test(t[m.index - 1])) pendienteEspacio = true;
            const rg = document.createRange(); rg.setStart(n, m.index); rg.setEnd(n, m.index + m[0].length);
            const rs = Array.from(rg.getClientRects()).filter((q) => q.width > 0 || q.height > 0);
            if (!rs.length) { ultimo = m.index + m[0].length; continue; }
            // una palabra partida en dos líneas (raro): se toma cada fragmento
            if (rs.length === 1) out.push({ txt: m[0], r: rel(rs[0]), estilo: estiloPadre(n.parentElement), esp: pendienteEspacio });
            else {
              let pos = m.index;
              for (let k = 0; k < m[0].length; k++) {
                const r1 = document.createRange(); r1.setStart(n, m.index + k); r1.setEnd(n, m.index + k + 1);
                const q = r1.getClientRects()[0];
                if (!q) continue;
                const rq = rel(q);
                const ult = out[out.length - 1];
                if (ult && ult._frag === pos && Math.abs(ult.r.y - rq.y) < 2) { ult.txt += m[0][k]; ult.r.w = rq.x + rq.w - ult.r.x; }
                else out.push({ txt: m[0][k], r: rq, estilo: estiloPadre(n.parentElement), esp: k === 0 ? pendienteEspacio : false, _frag: pos });
              }
            }
            pendienteEspacio = false;
            ultimo = m.index + m[0].length;
          }
          if (ultimo < t.length) pendienteEspacio = true;
        } else if (n.nodeType === 1) {
          const cs = getComputedStyle(n);
          if (cs.display === 'none') continue;
          if (n.matches(SEL_RASTER) || n.tagName === 'IMG' || n.tagName === 'BR') {
            if (n.tagName === 'BR') out.push({ br: true });
            continue;
          }
          if (!esInline(cs)) continue;   // bloque dentro del contenedor: va aparte
          // una ficha en línea (inline-block, inline-flex) es un contenedor propio, con su
          // caja y su texto: aquí deja un hueco que parte la línea en tramos
          if (cs.display !== 'inline') continue;
          visitar(n, estiloPadre);
        }
      }
    };
    const cache = new Map();
    const estiloDe = (el) => { if (!cache.has(el)) cache.set(el, estiloRun(el, cont)); return cache.get(el); };
    visitar(cont, estiloDe);
    return out;
  }

  function lineHeightPx(cs) {
    const lh = cs.lineHeight;
    if (lh === 'normal') return px(cs.fontSize) * 1.2207;   // Calibri: ascendente + descendente
    return px(lh);
  }

  /** Contenedor de texto -> uno o varios cuadros de texto (se parte si hay saltos verticales). */
  function textoDe(cont, cs, L, alfa) {
    const ws = palabras(cont);
    if (!ws.some((w) => w.txt)) return;
    const Lh = lineHeightPx(cs);
    const s = px(cs.fontSize);
    // agrupar en líneas por la posición vertical
    const lineas = [];
    let actual = null;
    for (const w of ws) {
      if (w.br) { if (actual) actual.cerrada = true; continue; }
      const cy = w.r.y + w.r.h / 2;
      const principal = !w.estilo.desp;
      if (!actual || actual.cerrada || (principal && Math.abs(cy - actual.cy) > 0.55 * Lh) || (!principal && Math.abs(cy - actual.cy) > 0.9 * Lh)) {
        actual = { ws: [], cy: cy, top: principal ? w.r.y : Infinity, alto: principal ? w.r.h : 0, x0: w.r.x, x1: w.r.x + w.r.w };
        lineas.push(actual);
      }
      actual.ws.push(w);
      if (principal) {
        if (actual.top === Infinity) { actual.top = w.r.y; actual.alto = w.r.h; actual.cy = cy; }
        actual.top = Math.min(actual.top, w.r.y);
        actual.alto = Math.max(actual.alto, w.r.h);
      }
      actual.x0 = Math.min(actual.x0, w.r.x); actual.x1 = Math.max(actual.x1, w.r.x + w.r.w);
    }
    for (const l of lineas) if (l.top === Infinity) { l.top = Math.min(...l.ws.map((w) => w.r.y)); l.alto = Math.max(...l.ws.map((w) => w.r.h)); }
    // grupos de líneas consecutivas (un salto vertical mayor que una línea separa cuadros)
    const grupos = [];
    for (const l of lineas) {
      const g = grupos[grupos.length - 1];
      if (g && l.top - g[g.length - 1].top < 1.6 * Lh) g.push(l); else grupos.push([l]);
    }
    const r = rel(cont.getBoundingClientRect());
    const x0c = r.x + px(cs.borderLeftWidth) + px(cs.paddingLeft);
    const x1c = r.x + r.w - px(cs.borderRightWidth) - px(cs.paddingRight);
    const ta = cs.textAlign;
    // una línea con un hueco (una ficha en línea que va aparte) se parte en tramos, cada uno
    // en su lugar exacto; el resto del párrafo sigue siendo un solo cuadro de texto
    const tramos = (l) => {
      const out = [[]];
      l.ws.forEach((w, k) => {
        if (k > 0) {
          const a = l.ws[k - 1];
          const hueco = w.r.x - (a.r.x + a.r.w);
          if (hueco > (w.esp ? 0.27 * s : 0.03 * s) + 0.45 * s) out.push([]);
        }
        out[out.length - 1].push(w);
      });
      return out;
    };
    const runsDe = (ws) => {
      const runs = [];
      ws.forEach((w, k) => {
        const txt = (k > 0 && w.esp ? ' ' : '') + w.txt;
        const u = runs[runs.length - 1];
        if (u && JSON.stringify(u.e) === JSON.stringify(w.estilo)) u.txt += txt; else runs.push({ txt, e: w.estilo });
      });
      return runs;
    };
    const conHuecos = grupos.filter((g) => g.some((l) => tramos(l).length > 1));
    for (const g of conHuecos) {
      for (const l of g) {
        const top = l.top - (Lh - l.alto) / 2;
        for (const ws of tramos(l)) {
          const x0 = Math.min(...ws.map((w) => w.r.x)), x1 = Math.max(...ws.map((w) => w.r.x + w.r.w));
          items.push({
            t: 'texto', x: redondear(x0), y: redondear(top), w: redondear(x1 - x0 + Math.max(8, 0.3 * s)), h: redondear(Lh),
            interlineado: redondear(Lh), tamBase: redondear(s), al: 'l', alfa: redondear(alfa),
            lineas: [runsDe(ws)], anchoTexto: redondear(x1 - x0),
            entrada: marcarEntrada(cont, L), orden: orden++, z: zIndice(cont, L),
          });
        }
      }
    }
    for (const g of grupos) {
      if (conHuecos.includes(g)) continue;
      // alineación: la del CSS o la que se ve (texto centrado en una caja flexible o de rejilla)
      let al = ta === 'center' ? 'c' : (ta === 'right' || ta === 'end') ? 'r' : 'l';
      const cc = (x0c + x1c) / 2;
      if (al === 'l') {
        const centradas = g.every((l) => Math.abs((l.x0 + l.x1) / 2 - cc) < 2.5);
        const holgura = g.some((l) => (x1c - x0c) - (l.x1 - l.x0) > 6);
        if (centradas && holgura) al = 'c';
      }
      const anchoL = Math.max(...g.map((l) => l.x1 - l.x0));
      let x0 = Math.min(x0c, ...g.map((l) => l.x0)), x1 = Math.max(x1c, ...g.map((l) => l.x1));
      // si el texto no llena la caja y está alineado a la izquierda, el cuadro empieza donde empieza el texto
      if (al === 'l') x0 = Math.min(...g.map((l) => l.x0));
      const holg = Math.max(8, 0.02 * (x1 - x0));
      if (al === 'l') x1 += holg; else if (al === 'r') x0 -= holg; else { x0 -= holg / 2; x1 += holg / 2; }
      const primera = g[0];
      const topLinea = primera.top - (Lh - primera.alto) / 2;
      items.push({
        t: 'texto', x: redondear(x0), y: redondear(topLinea), w: redondear(x1 - x0), h: redondear(g.length * Lh),
        interlineado: redondear(Lh), tamBase: redondear(s), al, alfa: redondear(alfa),
        lineas: g.map((l) => runsDe(l.ws)),
        anchoTexto: redondear(anchoL),
        entrada: marcarEntrada(cont, L), orden: orden++, z: zIndice(cont, L),
      });
    }
  }

  // ---------------------------------------------------------------- imágenes
  function imagen(el, cs, L, alfa) {
    const r = rel(el.getBoundingClientRect());
    const src = el.currentSrc || el.src;
    const nw = el.naturalWidth, nh = el.naturalHeight;
    if (!nw || !nh || r.w < 1 || r.h < 1) return;
    const fit = cs.objectFit;
    let dx = r.x, dy = r.y, dw = r.w, dh = r.h, rec = { l: 0, t: 0, r: 0, b: 0 };
    const [pxp, pyp] = (cs.objectPosition || '50% 50%').split(' ').map((v) => (/%$/.test(v) ? parseFloat(v) / 100 : v === 'left' || v === 'top' ? 0 : v === 'right' || v === 'bottom' ? 1 : 0.5));
    if (fit === 'contain' || fit === 'scale-down') {
      const k = Math.min(r.w / nw, r.h / nh);
      dw = nw * k; dh = nh * k; dx = r.x + (r.w - dw) * pxp; dy = r.y + (r.h - dh) * pyp;
    } else if (fit === 'cover') {
      const k = Math.max(r.w / nw, r.h / nh);
      const vw = nw * k, vh = nh * k;
      const sobraX = (vw - r.w) / vw, sobraY = (vh - r.h) / vh;
      rec = { l: sobraX * pxp, r: sobraX * (1 - pxp), t: sobraY * pyp, b: sobraY * (1 - pyp) };
    }
    const rad = px(cs.borderTopLeftRadius);
    items.push({
      t: 'img', src, x: redondear(dx), y: redondear(dy), w: redondear(dw), h: redondear(dh), recorte: rec,
      radio: redondear(rad), alfa: redondear(alfa), entrada: marcarEntrada(el, L), orden: orden++, z: zIndice(el, L),
    });
  }

  // ---------------------------------------------------------------- recorrido principal
  function recorrer(el, L) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none') return;
    const alfa = opacidad(el);
    if (alfa < 0.02) return;
    const visible = cs.visibility === 'visible';
    const tr = transformacion(cs);
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0 && !el.children.length) return;

    // videos del software
    if (el.matches('[data-viz="video"]')) {
      const rr = rel(r);
      nuevoRaster(el, { x: redondear(rr.x), y: redondear(rr.y), w: redondear(rr.w), h: redondear(rr.h) },
        { video: el.getAttribute('data-src'), entrada: marcarEntrada(el, L), z: zIndice(el, L) });
      return;
    }
    // regiones que se fotografían: SVG, lienzos, fórmulas, imágenes vectoriales, contenedores girados o con filtros
    const esImgRaster = el.tagName === 'IMG' && (/\.svg($|\?)/i.test(el.currentSrc || el.src) || (cs.filter && cs.filter !== 'none') || tr);
    const girado = tr && el.children.length > 0;
    const filtro = (cs.filter && cs.filter !== 'none') || (cs.clipPath && cs.clipPath !== 'none') || (cs.maskImage && cs.maskImage !== 'none');
    const trazo = px(cs.webkitTextStrokeWidth) > 0;
    const textoConFormula = !esInline(cs) && el.children.length && tieneRasterEnLinea(el);
    if (visible && (el.matches(SEL_RASTER) || esImgRaster || girado || filtro || trazo || textoConFormula || (tr && tr.complejo))) {
      // todo lo que el elemento dibuja, aunque desborde (un pie de figura, una etiqueta), y su
      // sombra (box-shadow), que cae fuera del rectángulo: la foto no los corta
      const rr = el.children.length && !el.matches('svg, canvas, video') ? envolvente(el) : rel(r);
      const e = extensionSombra(cs);
      if (rr.w >= 1 && rr.h >= 1) nuevoRaster(el, { x: redondear(rr.x - e), y: redondear(rr.y - e), w: redondear(rr.w + 2 * e), h: redondear(rr.h + 2 * e) }, { entrada: marcarEntrada(el, L), z: zIndice(el, L) });
      return;
    }
    if (visible) {
      if (el !== L) {
        const rects = esInline(cs) && cs.display === 'inline' ? Array.from(el.getClientRects()) : [r];
        caja(el, cs, L, alfa, rects);
      }
      if (el.tagName === 'IMG') { imagen(el, cs, L, alfa); return; }
      // el fondo de un <span> resaltado va debajo del texto del párrafo: se emite antes
      cajasEnLinea(el, L);
      // texto propio (en línea) de un contenedor de bloque
      if (!esInline(cs) || cs.display !== 'inline') {
        const tieneTexto = Array.from(el.childNodes).some((n) => (n.nodeType === 3 && n.textContent.trim()) ||
          (n.nodeType === 1 && esInline(getComputedStyle(n)) && !n.matches(SEL_RASTER) && n.tagName !== 'IMG' && n.textContent.trim()));
        if (tieneTexto && !esInline(cs)) textoDe(el, cs, L, alfa);
        else if (tieneTexto && esInline(cs) && cs.display !== 'inline') textoDe(el, cs, L, alfa);   // inline-block, inline-flex
      }
    }
    for (const h of el.children) recorrerHijo(h, L);
  }

  /** Los elementos en línea (b, span, sub…) ya van dentro del texto del padre y su caja ya se
   *  emitió (cajasEnLinea); de ellos solo se recorre lo que va aparte: fichas en línea,
   *  imágenes, fórmulas y bloques. */
  function recorrerHijo(h, L) {
    const csh = getComputedStyle(h);
    if (csh.display === 'inline' && !h.matches(SEL_RASTER) && h.tagName !== 'IMG') {
      for (const n of h.children) recorrerHijo(n, L);
      return;
    }
    recorrer(h, L);
  }

  function cajasEnLinea(el, L) {
    for (const h of el.children) {
      const csh = getComputedStyle(h);
      if (csh.display !== 'inline' || h.matches(SEL_RASTER) || h.tagName === 'IMG') continue;
      if (csh.visibility === 'visible' && opacidad(h) >= 0.02) caja(h, csh, L, opacidad(h), Array.from(h.getClientRects()));
      cajasEnLinea(h, L);
    }
  }

  function enlaces(L) {
    for (const el of L.querySelectorAll('[data-ir], button[onclick]')) {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility !== 'visible' || opacidad(el) < 0.05) continue;
      const r = rel(el.getBoundingClientRect());
      if (r.w < 2 || r.h < 2) continue;
      let destino = el.getAttribute('data-ir');
      const oc = el.getAttribute('onclick') || '';
      if (!destino && /siguiente\(/.test(oc)) destino = '__siguiente';
      if (!destino && /alternarCapa\('menu'\)/.test(oc)) destino = '__indice';
      if (!destino) continue;
      items.push({ t: 'enlace', x: redondear(r.x), y: redondear(r.y), w: redondear(r.w), h: redondear(r.h), ir: destino, orden: 1e6 + orden++ });
    }
  }

  // una captura que redimensione la ventana haría que las láminas se redibujen en su estado
  // estático: el extractor vigila que no ocurra
  let redimensiones = 0;
  window.addEventListener('resize', () => { redimensiones++; });

  window.__pptx = {
    redimensiones: () => redimensiones,
    /** Describe la lámina activa en el paso actual. */
    extraer() {
      const L = lamina();
      items = []; rasters = []; orden = 0;
      for (const e of document.querySelectorAll('[data-pptx-rid]')) e.removeAttribute('data-pptx-rid');
      materializar(L);
      try {
        recorrer(L, L);
        enlaces(L);
      } finally { /* los seudoelementos se quitan después de fotografiar */ }
      const csL = getComputedStyle(L);
      return { id: L.id, fondo: color(csL.backgroundColor), items, rasters };
    },
    /** Deja visible solo la región rid (el resto transparente) para fotografiarla. */
    aislar(id) {
      const el = document.querySelector(`[data-pptx-rid="${id}"]`);
      if (!el) return false;
      document.documentElement.classList.add('pptx-aislando');
      el.classList.add('pptx-aislado');
      return true;
    },
    restaurar() {
      document.documentElement.classList.remove('pptx-aislando');
      for (const e of document.querySelectorAll('.pptx-aislado')) e.classList.remove('pptx-aislado');
    },
    limpiar() { desmaterializar(); },
    narracion(id) {
      const N = window.EDUFEM_NARRACION;
      const l = N && N.laminas && N.laminas[id];
      return l ? l.pasos.map((p) => p.texto || '') : [];
    },
  };
})();
