/* =====================================================================
   nucleo.js — reloj, motor de animación y utilidades comunes.

   Toda animación de la presentación pasa por EF.tween / EF.bucle, que leen
   la hora de EF.Reloj. En vivo, el reloj es performance.now() y un único
   requestAnimationFrame mueve todo. En la captura del video, el reloj es
   virtual: el capturador llama EF.captura.avanzar(ms) y cada cuadro sale
   idéntico en cada corrida (determinista), sin importar cuánto tarde el
   equipo en dibujarlo.
   ===================================================================== */
(function () {
  'use strict';
  const EF = (window.EF = window.EF || {});

  // ------------------------------------------------------------------ registro de visualizaciones
  // Los archivos viz/*.js se cargan antes que deck.js y se registran aquí.
  EF._fabricas = EF._fabricas || {};
  EF.registrarViz = function (nombre, fabrica) { EF._fabricas[nombre] = fabrica; };

  // ------------------------------------------------------------------ estilo de la presentación
  // 'moderno' (versión 1) o 'ppt' (versión 2, aspecto de la plantilla PowerPoint). Lo fija el
  // atributo data-estilo de <html>; la hoja estilo_ppt.css cuelga de ese atributo.
  EF.estilo = document.documentElement.getAttribute('data-estilo') || 'moderno';

  // ------------------------------------------------------------------ reloj
  const Reloj = (EF.Reloj = {
    virtual: false,
    t: 0,
    ahora() { return this.virtual ? this.t : performance.now(); },
  });

  // ------------------------------------------------------------------ curvas de suavizado
  const S = (EF.suave = {
    lineal: (t) => t,
    entra: (t) => t * t * t,
    sale: (t) => 1 - Math.pow(1 - t, 3),
    salePlus: (t) => 1 - Math.pow(1 - t, 4),
    ambos: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
    rebote: (t) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
    expo: (t) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
    seno: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
  });

  // ------------------------------------------------------------------ motor
  const tweens = new Set();
  const bucles = new Set();
  const esperas = new Set();   // promesas que el capturador debe aguardar (videos buscando)
  let rafId = 0;
  let sucio = false;

  function tick() {
    const ahora = Reloj.ahora();
    for (const tw of Array.from(tweens)) {
      if (tw.inicio === null) tw.inicio = ahora + tw.retraso;
      if (ahora < tw.inicio) continue;
      const p = tw.dur <= 0 ? 1 : Math.min(1, (ahora - tw.inicio) / tw.dur);
      const e = tw.curva(p);
      try { tw.cada(e, p); } catch (err) { console.error(err); }
      sucio = true;
      if (p >= 1) {
        tweens.delete(tw);
        try { tw.fin && tw.fin(); } catch (err) { console.error(err); }
        tw._resolver();
      }
    }
    for (const b of Array.from(bucles)) {
      if (b.t0 === null) b.t0 = ahora;
      // En la captura, los bucles continuos (decorativos) se redibujan a su propio ritmo:
      // un cuadro que no cambia no obliga a fotografiar de nuevo.
      if (Reloj.virtual && b.fps) {
        const k = Math.floor(((ahora - b.t0) / 1000) * b.fps);
        if (k === b.ultimo) continue;
        b.ultimo = k;
      }
      try { b.fn((ahora - b.t0) / 1000, ahora); } catch (err) { console.error(err); }
      sucio = true;
    }
  }

  function bucleVivo() {
    rafId = 0;
    tick();
    if (!Reloj.virtual && (tweens.size || bucles.size)) rafId = requestAnimationFrame(bucleVivo);
  }
  function despertar() {
    if (!Reloj.virtual && !rafId) rafId = requestAnimationFrame(bucleVivo);
  }

  /** Interpola de 0 a 1 en `dur` ms y llama cada(e, p). Devuelve {cancelar, promesa}. */
  EF.tween = function (op) {
    const tw = {
      dur: op.dur == null ? 500 : op.dur,
      retraso: op.retraso || 0,
      curva: typeof op.curva === 'function' ? op.curva : (S[op.curva] || S.sale),
      cada: op.cada || (() => {}),
      fin: op.fin,
      inicio: null,
    };
    tw.promesa = new Promise((res) => (tw._resolver = res));
    tweens.add(tw);
    despertar();
    return {
      promesa: tw.promesa,
      cancelar(completar) {
        if (!tweens.has(tw)) return;
        tweens.delete(tw);
        if (completar) { try { tw.cada(1, 1); tw.fin && tw.fin(); } catch (e) { console.error(e); } }
        tw._resolver();
      },
    };
  };

  /** Llama fn(segundos, ahora) en cada cuadro hasta detener(). En la captura del video,
   *  op.fps (15 por omisión) limita cuántas veces por segundo se redibuja. */
  EF.bucle = function (fn, op) {
    // conversor a PowerPoint: cada bucle se dibuja una sola vez, en un instante representativo
    if (EF.congelarBucles != null) {
      try { fn(EF.congelarBucles, Reloj.ahora()); } catch (err) { console.error(err); }
      sucio = true;
      return { detener() {}, get activo() { return false; } };
    }
    const b = { fn, t0: null, fps: (op && op.fps) || 15, ultimo: -1 };
    bucles.add(b);
    despertar();
    return { detener() { bucles.delete(b); }, get activo() { return bucles.has(b); } };
  };

  /** Espera `ms` en el reloj de la presentación (sirve también en la captura). */
  EF.esperar = function (ms) { return EF.tween({ dur: ms, curva: 'lineal' }).promesa; };

  /** El capturador aguarda estas promesas antes de fotografiar el cuadro. */
  EF.registrarEspera = function (p) {
    esperas.add(p);
    p.finally(() => esperas.delete(p));
    return p;
  };

  EF.marcarSucio = function () { sucio = true; despertar(); };
  EF.motorOcioso = function () { return tweens.size === 0 && bucles.size === 0; };
  /** Animaciones finitas en curso (los bucles continuos no cuentan). */
  EF.tweensActivos = function () { return tweens.size; };

  // API de captura (la usa herramientas/capturar_video.mjs)
  EF.captura = {
    activar() { Reloj.virtual = true; Reloj.t = 0; if (rafId) { cancelAnimationFrame(rafId); rafId = 0; } },
    async avanzar(ms) {
      Reloj.t += ms;
      sucio = false;
      tick();
      if (esperas.size) await Promise.all(Array.from(esperas));
      const huboCambio = sucio;
      sucio = false;
      return { sucio: huboCambio, ocioso: EF.motorOcioso(), tweens: tweens.size, t: Reloj.t };
    },
  };

  // ------------------------------------------------------------------ utilidades DOM
  EF.$ = (sel, raiz) => (raiz || document).querySelector(sel);
  EF.$$ = (sel, raiz) => Array.from((raiz || document).querySelectorAll(sel));
  EF.el = function (tag, atributos, hijos) {
    const e = document.createElement(tag);
    if (atributos) for (const [k, v] of Object.entries(atributos)) {
      if (v == null || v === false) continue;
      if (k === 'class') e.className = v;
      else if (k === 'html') e.innerHTML = v;
      else if (k === 'text') e.textContent = v;
      else if (k === 'style') e.style.cssText = v;
      else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v === true ? '' : v);
    }
    if (hijos) for (const h of [].concat(hijos)) if (h != null) e.append(h.nodeType ? h : document.createTextNode(h));
    return e;
  };
  const NS = 'http://www.w3.org/2000/svg';
  EF.svg = function (tag, atributos, padre) {
    const e = document.createElementNS(NS, tag);
    if (atributos) for (const [k, v] of Object.entries(atributos)) {
      if (v == null || v === false) continue;
      if (k === 'text') e.textContent = v;
      else if (k === 'html') e.innerHTML = v;
      else e.setAttribute(k, v);
    }
    if (padre) padre.appendChild(e);
    return e;
  };

  /** Lee una variable CSS del tema activo. */
  EF.css = function (nombre, el) {
    return getComputedStyle(el || document.documentElement).getPropertyValue(nombre).trim();
  };
  /** Familia tipográfica del tema, para el texto que se dibuja en los lienzos. */
  EF.fuente = function () { return EF.css('--fuente') || "'Inter', 'Segoe UI', sans-serif"; };

  // ------------------------------------------------------------------ números (coma decimal, como la tesis)
  const ESP_FINO = ' ';
  function agruparMiles(entero) {
    return entero.replace(/\B(?=(\d{3})+(?!\d))/g, ESP_FINO);
  }
  /** Número con `dec` decimales, coma decimal y miles separados por espacio fino. */
  EF.fmt = function (x, dec = 2, opciones) {
    if (x == null || !isFinite(x)) return '—';
    const op = opciones || {};
    let s = Math.abs(x).toFixed(dec);
    if (Number(s) === 0) x = 0;
    let [ent, frac] = s.split('.');
    if (op.miles !== false && ent.length > 4) ent = agruparMiles(ent);
    const signo = x < 0 ? '−' : (op.signo && x > 0 ? '+' : '');
    return signo + ent + (frac ? ',' + frac : '');
  };
  /** Cifras significativas. */
  EF.fmtSig = function (x, sig = 4) {
    if (x == null || !isFinite(x)) return '—';
    if (x === 0) return '0';
    const mag = Math.floor(Math.log10(Math.abs(x)));
    const dec = Math.max(0, sig - 1 - mag);
    return EF.fmt(x, dec);
  };
  const SUP = { '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹' };
  EF.sup = (s) => String(s).split('').map((c) => SUP[c] || c).join('');
  /** Notación científica en texto: 1,7 × 10⁻¹³ */
  EF.fmtCient = function (x, dec = 2) {
    if (x == null || !isFinite(x)) return '—';
    if (x === 0) return '0';
    const exp = Math.floor(Math.log10(Math.abs(x)));
    const man = x / Math.pow(10, exp);
    return EF.fmt(man, dec) + ' × 10' + EF.sup(exp);
  };
  /** Número para KaTeX: coma decimal con {,} */
  EF.tex = function (x, dec = 4) {
    if (x == null || !isFinite(x)) return '\\text{—}';
    let s = Math.abs(x).toFixed(dec);
    if (Number(s) === 0) x = 0;
    s = s.replace('.', '{,}');
    return (x < 0 ? '-' : '') + s;
  };
  EF.texAuto = function (x, sig = 4) {
    if (x === 0) return '0';
    const ax = Math.abs(x);
    if (ax >= 1e-3 && ax < 1e6) {
      const mag = Math.floor(Math.log10(ax));
      return EF.tex(x, Math.max(0, sig - 1 - mag));
    }
    const exp = Math.floor(Math.log10(ax));
    return EF.tex(x / Math.pow(10, exp), sig - 1) + '\\times10^{' + exp + '}';
  };
  EF.pct = (x, dec = 2) => EF.fmt(x, dec) + ' %';
  /** «u_y» o «σ_{VM}» -> [{t:'u'}, {t:'y', sub:true}] para rotular con subíndices. */
  EF.partesSub = function (texto) {
    const out = [];
    const re = /_(\{[^}]*\}|.)/g;
    let k = 0, m;
    while ((m = re.exec(texto))) {
      if (m.index > k) out.push({ t: texto.slice(k, m.index) });
      out.push({ t: m[1].replace(/^\{|\}$/g, ''), sub: true });
      k = m.index + m[0].length;
    }
    if (k < texto.length) out.push({ t: texto.slice(k) });
    return out;
  };
  /** Versión HTML: «u_y» -> u<sub>y</sub> */
  EF.htmlSub = (texto) => EF.partesSub(texto).map((p) => (p.sub ? `<sub>${p.t}</sub>` : p.t)).join('');

  // ------------------------------------------------------------------ KaTeX
  EF.katex = function (el, tex, display) {
    if (!window.katex) { el.textContent = tex; return el; }
    try {
      window.katex.render(tex, el, { throwOnError: false, displayMode: !!display, strict: 'ignore', output: 'html' });
    } catch (e) { el.textContent = tex; }
    return el;
  };
  /** Reemplaza el contenido de todo [data-tex] (y .tex-bloque) por su fórmula. */
  EF.renderizarFormulas = function (raiz) {
    for (const el of EF.$$('[data-tex]', raiz)) {
      EF.katex(el, el.getAttribute('data-tex'), el.hasAttribute('data-bloque'));
    }
  };

  // ------------------------------------------------------------------ colores
  /** Mapa de color jet (el de EduFEM y matplotlib). t en [0, 1] -> [r, g, b] 0..255 */
  EF.jet = function (t) {
    t = Math.max(0, Math.min(1, t));
    const r = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * t - 3)));
    const g = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * t - 2)));
    const b = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * t - 1)));
    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
  };
  const LUT = new Uint8ClampedArray(256 * 3);
  for (let i = 0; i < 256; i++) { const c = EF.jet(i / 255); LUT[3 * i] = c[0]; LUT[3 * i + 1] = c[1]; LUT[3 * i + 2] = c[2]; }
  EF.jetLUT = LUT;
  EF.jetCss = function (t, a) { const c = EF.jet(t); return a == null ? `rgb(${c[0]},${c[1]},${c[2]})` : `rgba(${c[0]},${c[1]},${c[2]},${a})`; };
  /** Mezcla dos colores CSS hex/rgb en proporción t. */
  EF.hexARgb = function (hex) {
    hex = hex.trim();
    if (hex.startsWith('rgb')) return hex.match(/[\d.]+/g).slice(0, 3).map(Number);
    if (hex.length === 4) hex = '#' + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3];
    const n = parseInt(hex.slice(1, 7), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  };
  EF.rgba = function (colorCss, a) { const c = EF.hexARgb(colorCss); return `rgba(${c[0]},${c[1]},${c[2]},${a})`; };
  EF.mezclar = function (c1, c2, t) {
    const a = EF.hexARgb(c1), b = EF.hexARgb(c2);
    return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * t)).join(',')})`;
  };

  // ------------------------------------------------------------------ matemática
  EF.lerp = (a, b, t) => a + (b - a) * t;
  EF.clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  EF.rango = (n) => Array.from({ length: n }, (_, i) => i);

  // ------------------------------------------------------------------ revelado de elementos
  /** Aparición estándar de un elemento (opacidad + desplazamiento). */
  EF.aparecer = function (el, op) {
    op = op || {};
    // en la versión PowerPoint, las entradas son un fundido («Desvanecer»), sin desplazamiento
    const tipo = op.tipo || el.getAttribute('data-anim') || (EF.estilo === 'ppt' ? 'fundido' : 'sube');
    const dur = op.dur || Number(el.getAttribute('data-dur')) || 560;
    const retraso = op.retraso || 0;
    const desde = {
      sube: [0, 34, 1], baja: [0, -34, 1], izq: [-50, 0, 1], der: [50, 0, 1],
      escala: [0, 0, 0.9], fundido: [0, 0, 1], zoom: [0, 0, 1.08],
    }[tipo] || [0, 34, 1];
    el.style.visibility = 'visible';
    el.style.opacity = '0';
    el.style.transform = `translate(${desde[0]}px, ${desde[1]}px) scale(${desde[2]})`;
    return EF.tween({
      dur, retraso, curva: op.curva || 'sale',
      cada(e) {
        el.style.opacity = String(e);
        el.style.transform = `translate(${desde[0] * (1 - e)}px, ${desde[1] * (1 - e)}px) scale(${desde[2] + (1 - desde[2]) * e})`;
      },
      fin() { el.style.transform = ''; el.style.opacity = ''; },
    });
  };
  EF.ocultar = function (el) { el.style.visibility = 'hidden'; el.style.opacity = '0'; el.style.transform = ''; };
  EF.mostrar = function (el) { el.style.visibility = 'visible'; el.style.opacity = ''; el.style.transform = ''; };

  /** Cuenta ascendente de un número en el texto de un elemento. */
  EF.contar = function (el, hasta, op) {
    op = op || {};
    const dec = op.dec != null ? op.dec : Number(el.getAttribute('data-dec') || 0);
    const desde = op.desde || 0;
    const suf = op.sufijo != null ? op.sufijo : (el.getAttribute('data-sufijo') || '');
    const pre = op.prefijo || '';
    return EF.tween({
      dur: op.dur || 1400, retraso: op.retraso || 0, curva: 'expo',
      cada(e) { el.textContent = pre + EF.fmt(desde + (hasta - desde) * e, dec) + suf; },
    });
  };

  /** Dibuja un trazo SVG (stroke-dasharray) de 0 a 100 %. */
  EF.trazar = function (path, op) {
    op = op || {};
    let L = 0;
    try { L = path.getTotalLength(); } catch (e) { L = 1000; }
    path.style.strokeDasharray = `${L} ${L}`;
    path.style.strokeDashoffset = String(L);
    return EF.tween({
      dur: op.dur || 900, retraso: op.retraso || 0, curva: op.curva || 'ambos',
      cada(e) { path.style.strokeDashoffset = String(L * (1 - e)); },
      fin() { if (!op.conservar) { path.style.strokeDasharray = ''; path.style.strokeDashoffset = ''; } },
    });
  };

  EF.log = function () { if (window.__DEPURAR) console.log.apply(console, arguments); };
})();
