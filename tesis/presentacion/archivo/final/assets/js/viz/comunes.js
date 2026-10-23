/* =====================================================================
   viz/comunes.js — carátula, separadores de bloque, videos del software
   y cierre. Contrato de toda visualización (lo llama deck.js):
     entrar(paso, {instantaneo, nueva, impresion})   al mostrarse la lámina
     paso(k, {adelante, salto})                      al cambiar de paso
     salir()  redimensionar()  tema()  final()
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const DAT = () => window.EDUFEM_DATOS;

  // ------------------------------------------------------------------ utilidades
  /** Percentil de un arreglo (para recortar singularidades en el color). */
  EF.percentil = function (v, p) {
    const s = Array.from(v).sort((a, b) => a - b);
    return s[Math.min(s.length - 1, Math.max(0, Math.round((p / 100) * (s.length - 1))))];
  };
  /** Nodos de las aristas de una malla (para dibujar solo el contorno). */
  EF.bordeMalla = function (elems) {
    const cuenta = new Map();
    const clave = (a, b) => (a < b ? a + '-' + b : b + '-' + a);
    for (const con of elems) for (let k = 0; k < 4; k++) {
      const a = con[k], b = con[(k + 1) % 4];
      cuenta.set(clave(a, b), (cuenta.get(clave(a, b)) || 0) + 1);
    }
    return cuenta;
  };

  // ------------------------------------------------------------------ carátula
  EF.registrarViz('portada', function (cont) {
    const cook = DAT().cook.casos.Q9['8'];
    const W = 760, H = 720;
    const caja = EF.el('div', { style: `position:absolute;left:0;top:120px;width:${W}px;height:${H}px` });
    cont.appendChild(caja);
    const lz = new EF.LienzoMEF(caja, W, H);
    const nodos = cook.nodos, elems = cook.elems, u = cook.u, vm = cook.vm;
    // caja que contiene la malla sin deformar y la deformada a la escala máxima
    const ESC_MAX = 0.55;
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    nodos.forEach((p, i) => {
      for (const s of [0, ESC_MAX]) {
        const x = p[0] + s * u[i][0], y = p[1] + s * u[i][1];
        x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
      }
    });
    lz.encuadrar(x0, x1, y0, y1, { s: 70, d: 90, i: 30, iz: 120 });
    const vmax = EF.percentil(vm, 96), vmin = Math.min(...vm);
    const iSonda = nodos.findIndex((p) => Math.abs(p[0] - 48) < 1e-6 && Math.abs(p[1] - 52) < 1e-6);
    const borde = nodos.map((p, i) => [p, i]).filter(([p]) => Math.abs(p[0] - 48) < 1e-6)
      .sort((a, b) => a[0][1] - b[0][1]).map(([, i]) => i).filter((_, k) => k % 4 === 1);
    let fase = { malla: 1, campo: 1, esc: 0 };
    let bucle = null;

    function dibujar() {
      const c = lz.inicio(null);
      const nEl = Math.ceil(elems.length * fase.malla);
      if (fase.campo > 0) lz.campo(nodos, elems, vm, { min: vmin, max: vmax, u, escala: fase.esc, alfa: fase.campo, sub: 4 });
      lz.malla(nodos, elems.slice(0, nEl), { color: fase.campo > 0.5 ? 'rgba(10,15,28,.55)' : '#86d68a', ancho: 1.3, u, escala: fase.esc });
      // empotramiento en x = 0
      lz.empotramiento(0, 0, 44, { color: '#ffa62b' });
      // carga tangencial (hacia arriba) repartida en el borde derecho, que se mueve con la deformada
      const P0 = EF.LienzoMEF.pos(nodos, u, fase.esc, iSonda);
      for (const i of borde) {
        const q = EF.LienzoMEF.pos(nodos, u, fase.esc, i);
        lz.flecha(q[0] + 2.2, q[1] + 1.2, 0, 1, { largo: 30, ancho: 3, color: '#ff5a52' });
      }
      // sonda en (48; 52)
      c.save();
      const X = lz.X(P0[0]), Y = lz.Y(P0[1]);
      c.beginPath(); c.arc(X, Y, 9, 0, 2 * Math.PI); c.fillStyle = '#fff'; c.fill();
      c.lineWidth = 3; c.strokeStyle = '#ff8a3d'; c.stroke();
      c.restore();
      if (fase.campo > 0.6) {
        lz.etiqueta(P0[0], P0[1], `u_y(48; 52) = ${EF.fmt(cook.uy, 3)}`, { dx: -18, dy: -34, ancla: 'right', tam: 22, color: '#eef3fc', fondo: '#0b1222', borde: '#ff8a3d' });
      }
      void c;
    }
    function animarEntrada() {
      if (bucle) bucle.detener();
      fase = { malla: 0, campo: 0, esc: 0 };
      EF.tween({ dur: 1500, curva: 'ambos', cada: (e) => { fase.malla = e; dibujar(); } });
      EF.tween({ dur: 1100, retraso: 1300, curva: 'sale', cada: (e) => { fase.campo = e; dibujar(); } });
      EF.tween({ dur: 10, retraso: 2400, fin: () => {
        bucle = EF.bucle((s) => { fase.esc = ESC_MAX * (0.5 - 0.5 * Math.cos((2 * Math.PI * s) / 6)); dibujar(); });
      } });
    }
    return {
      entrar(p, op) {
        lz.redimensionar();
        if (op.instantaneo || op.impresion) { fase = { malla: 1, campo: 1, esc: 0.45 }; dibujar(); if (!op.impresion && !op.estatico) { bucle && bucle.detener(); bucle = EF.bucle((s) => { fase.esc = 0.45 + 0.1 * Math.sin((2 * Math.PI * s) / 6); dibujar(); }); } return; }
        animarEntrada();
      },
      salir() { if (bucle) { bucle.detener(); bucle = null; } },
      redimensionar() { if (lz.redimensionar()) dibujar(); },
      tema() { dibujar(); },
    };
  });

  // ------------------------------------------------------------------ separadores de bloque
  EF.registrarViz('separador', function (cont, L, D) {
    // cadena del hilo conductor: cada bloque es un botón que lleva a su separador
    const cadena = L.el.querySelector('.cadena');
    const bi = EF.BLOQUES.findIndex((b) => b.id === L.bloque);
    if (cadena) {
      cadena.innerHTML = '';
      EF.BLOQUES.forEach((b, k) => {
        const destino = D && D.principales.find((x) => x.bloque === b.id);
        cadena.appendChild(EF.el('button', {
          class: k < bi ? 'hecho' : k === bi ? 'actual' : '', html: `<b>${b.n}</b><br>${b.corto}`,
          'data-ir': destino ? destino.id : null, 'data-sin-historial': true, title: `Ir a ${b.nombre}`,
        }));
      });
    }
    const W = 1920, H = 1080;
    const lz = new EF.LienzoMEF(cont, W, H);
    const nx = 26, ny = 15;
    let bucle = null, alfa = 0;
    function dibujar(t) {
      const c = lz.inicio(null);
      c.save();
      c.strokeStyle = EF.css('--acento');
      c.lineWidth = 1.2;
      const def = (i, j) => {
        const x = (i / nx) * W * 1.1 - 60, y = (j / ny) * H * 1.1 - 50;
        const a = Math.sin(i * 0.45 + t * 0.35) * 14 + Math.cos(j * 0.6 - t * 0.3) * 12;
        const b = Math.cos(i * 0.3 - t * 0.25) * 12 + Math.sin(j * 0.5 + t * 0.4) * 14;
        return [x + a, y + b];
      };
      for (let i = 0; i <= nx; i++) for (let j = 0; j <= ny; j++) {
        const p = def(i, j);
        // más visible hacia la derecha: la malla «emerge» detrás del número
        const w = Math.pow(i / nx, 1.6) * alfa * 0.5;
        if (w < 0.01) continue;
        c.globalAlpha = w;
        if (i < nx) { const q = def(i + 1, j); c.beginPath(); c.moveTo(p[0], p[1]); c.lineTo(q[0], q[1]); c.stroke(); }
        if (j < ny) { const q = def(i, j + 1); c.beginPath(); c.moveTo(p[0], p[1]); c.lineTo(q[0], q[1]); c.stroke(); }
        c.globalAlpha = w * 1.4;
        c.fillStyle = EF.css('--acento');
        c.beginPath(); c.arc(p[0], p[1], 2.2, 0, 2 * Math.PI); c.fill();
      }
      c.restore();
    }
    return {
      entrar(p, op) {
        lz.redimensionar();
        if (bucle) bucle.detener();
        if (op.instantaneo || op.impresion) { alfa = 1; dibujar(0); }
        else { alfa = 0; EF.tween({ dur: 1400, cada: (e) => { alfa = e; } }); }
        if (!op.impresion) bucle = EF.bucle((s) => dibujar(s), { fps: 12 });
      },
      salir() { if (bucle) { bucle.detener(); bucle = null; } },
      redimensionar() { lz.redimensionar(); dibujar(0); },
      tema() { dibujar(0); },
    };
  });

  // ------------------------------------------------------------------ videos del software (Manim)
  // En vivo se reproducen en bucle; en la captura se busca el cuadro exacto del reloj virtual.
  EF.registrarViz('video', function (cont) {
    const src = cont.getAttribute('data-src');
    const v = EF.el('video', { src, muted: true, loop: true, playsinline: true, preload: 'auto', style: 'width:100%;height:100%;object-fit:contain;display:block;border-radius:14px' });
    v.muted = true;
    cont.appendChild(v);
    let bucle = null;
    const captura = () => EF.Reloj.virtual;
    // En la captura del video, si el capturador extrajo los cuadros (?cuadros=<carpeta>), se
    // muestran como imágenes: mucho más rápido que buscar un cuadro del MP4 en cada paso.
    const carpeta = new URLSearchParams(location.search).get('cuadros');
    const nCuadros = Number(cont.getAttribute('data-cuadros') || 0);
    const fpsVideo = Number(cont.getAttribute('data-fps') || 22);
    if (carpeta && nCuadros) {
      const nombre = src.split('/').pop().replace(/\.[^.]+$/, '');
      const img = EF.el('img', { alt: '', style: 'width:100%;height:100%;object-fit:contain;display:block;border-radius:14px' });
      v.replaceWith(img);
      let actual = -1;
      const mostrar = (s) => {
        const k = Math.floor(s * fpsVideo) % nCuadros;
        if (k === actual) return;
        actual = k;
        img.src = `${carpeta}/${nombre}/f${String(k + 1).padStart(4, '0')}.jpg`;
        EF.registrarEspera(img.decode().catch(() => null));
      };
      return {
        entrar(p, op) { actual = -1; mostrar(op.impresion ? 1.5 : 0); if (bucle) bucle.detener(); if (!op.impresion) bucle = EF.bucle((s) => mostrar(s), { fps: fpsVideo }); },
        salir() { if (bucle) { bucle.detener(); bucle = null; } },
      };
    }
    function buscar(t) {
      if (!v.duration || !isFinite(v.duration)) return;
      const objetivo = t % v.duration;
      if (Math.abs(v.currentTime - objetivo) < 0.004) return;
      const p = new Promise((res) => {
        const listo = () => { v.removeEventListener('seeked', listo); res(); };
        v.addEventListener('seeked', listo);
        setTimeout(listo, 1500);
      });
      v.currentTime = objetivo;
      EF.registrarEspera(p);
    }
    return {
      entrar(p, op) {
        if (op.impresion) { v.currentTime = Math.min(2, (v.duration || 4) * 0.6); return; }
        if (captura()) {
          v.pause();
          const esperarMeta = v.readyState >= 1 ? Promise.resolve() : new Promise((res) => v.addEventListener('loadedmetadata', res, { once: true }));
          EF.registrarEspera(esperarMeta);
          if (bucle) bucle.detener();
          bucle = EF.bucle((s) => buscar(s), { fps: 22 });
        } else {
          v.currentTime = 0;
          v.play().catch(() => {});
        }
      },
      salir() { v.pause(); if (bucle) { bucle.detener(); bucle = null; } },
    };
  });
})();
