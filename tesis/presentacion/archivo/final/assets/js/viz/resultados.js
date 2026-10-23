/* =====================================================================
   viz/resultados.js — animaciones del bloque «Presentación de resultados».
   Tablas y campos: EDUFEM_DATOS (motor de EduFEM y docs/vyv/datos/*.csv).
   Las cifras de las tablas de la tesis se escriben tal como allí figuran.
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const DAT = () => window.EDUFEM_DATOS;
  const est = (e, o) => EF.estiloSvg(e, o);
  const S = EF.svg;

  // ================================================================== MMS: convergencia
  EF.registrarViz('mms', function (cont) {
    const M = DAT().mms;
    const CONF = { unif_tp: 'Cuadrado · tensión plana', dist_tp: 'Distorsionado · tensión plana', unif_dp: 'Cuadrado · deformación plana', dist_dp: 'Distorsionado · deformación plana' };
    let cfg = 'unif_tp', norma = 'L2';
    const NORMAS = { L2: { k: 'L2', t: 'tL2', et: 'Norma L² del desplazamiento', teo: [2, 3] }, H1: { k: 'H1', t: 'tH1', et: 'Seminorma H¹ del desplazamiento', teo: [1, 2] }, S: { k: 'S', t: 'tS', et: 'Norma L² de la tensión recuperada σ*', teo: [null, null] } };
    const caja = EF.el('div', { style: 'position:absolute;left:0;top:0;width:1060px;height:600px' });
    cont.appendChild(caja);
    const titG = EF.el('div', { style: 'position:absolute;left:0;top:604px;width:1060px;text-align:center;font:650 24px var(--fuente);color:var(--texto-2)' });
    cont.appendChild(titG);
    const ctr = EF.el('div', { class: 'grupo-botones solo-vivo', style: 'position:absolute;right:0;top:-174px' });
    const segN = EF.el('div', { class: 'segmentado' });
    const bN = Object.entries({ L2: 'L²', H1: 'H¹', S: 'σ*' }).map(([k, t]) => { const b = EF.el('button', { text: t }); b.onclick = () => { norma = k; dibujar(true); }; segN.appendChild(b); return [k, b]; });
    const segC = EF.el('div', { class: 'segmentado naranja' });
    const bC = Object.keys(CONF).map((k, j) => { const b = EF.el('button', { text: ['□ TP', '◇ TP', '□ DP', '◇ DP'][j], title: CONF[k] }); b.onclick = () => { cfg = k; dibujar(true); }; segC.appendChild(b); return [k, b]; });
    ctr.append(segN, segC);
    cont.appendChild(ctr);
    // panel derecho: tasas asintóticas
    const der = EF.el('div', { style: 'position:absolute;left:1110px;top:0;width:610px' });
    cont.appendChild(der);
    const lzE = new EF.LienzoMEF(EF.el('div', { style: 'position:absolute;left:1110px;top:462px;width:610px;height:236px;border-radius:14px;overflow:hidden;border:1px solid var(--linea-2)' }), 610, 236);
    cont.appendChild(lzE.canvas.parentNode);
    let campoN = 2, bucleCampo = null;
    function dibujarCampo() {
      const c = M.campos.Q4[String(campoN)];
      lzE.redimensionar();
      lzE.encuadrar(-0.05, 1.05, -0.05, 1.05, { s: 16, d: 250, i: 16, iz: 16 });
      lzE.inicio(EF.css('--lienzo'));
      const todos = Object.values(M.campos.Q4).flatMap((x) => x.err);
      lzE.rellenoElementos(c.nodos, c.elems, c.err, { log: true, min: Math.min(...todos), max: Math.max(...todos) });
      lzE.malla(c.nodos, c.elems, { color: 'rgba(255,255,255,.4)', ancho: 1 });
      lzE.etiqueta(1.12, 0.85, `Q4, N = ${campoN}`, { tam: 22, color: EF.css('--texto') });
      lzE.etiqueta(1.12, 0.62, 'error por elemento', { tam: 18, color: EF.css('--texto-3') });
      lzE.etiqueta(1.12, 0.45, '(escala logarítmica)', { tam: 18, color: EF.css('--texto-3') });
      lzE.etiqueta(1.12, 0.2, 'cuadrilátero distorsionado', { tam: 17, color: EF.css('--texto-3') });
    }
    let G = null, series = [];
    function dibujar(animar) {
      bN.forEach(([k, b]) => b.classList.toggle('sel', k === norma));
      bC.forEach(([k, b]) => b.classList.toggle('sel', k === cfg));
      caja.innerHTML = '';
      const nm = NORMAS[norma];
      const T = M.tablas[cfg];
      const todos = [...T.Q4, ...T.Q9].map((f) => f[nm.k]);
      const ymin = Math.pow(10, Math.floor(Math.log10(Math.min(...todos)))), ymax = Math.pow(10, Math.ceil(Math.log10(Math.max(...todos))));
      G = new EF.Grafico(caja, {
        ancho: 1060, alto: 600, margen: { s: 20, d: 30, i: 80, iz: 120 },
        x: { min: 1.6, max: 46, log: true, marcas: [2, 4, 8, 16, 32], fmt: (v) => String(v), etiqueta: 'Elementos por lado N  (h = 1/N)' },
        y: { min: ymin, max: ymax, log: true, etiqueta: 'Error' },
      }).ejes();
      series = [];
      [['Q4', 'var(--q4)', 'circulo'], ['Q9', 'var(--q9)', 'cuadro']].forEach(([el, col, mk], j) => {
        const pts = T[el].map((f) => [f.N, f[nm.k]]);
        const s = G.serie(pts, { color: col, marcador: mk, radio: 10 });
        series.push(s);
        if (animar) G.animar(s, { dur: 1200, retraso: j * 400 });
        // pendiente teórica junto a las dos mallas más finas
        const teo = nm.teo[j];
        const f16 = T[el][3];
        const tasa = T[el][4][nm.t];
        const ult = T[el][4];
        if (teo) G.pendiente(12, f16[nm.k] * 0.32, -teo, { factor: 2.2, color: col, etiqueta: String(teo) });
        const u = T[el][4];
        G.texto(ult.N * 1.08, ult[nm.k] * (j === 0 ? 2.2 : 1.9), `${EF.fmt(tasa, 2)}`, { color: col, tam: 26, peso: 850, ancla: 'start' });
      });
      G.leyenda([{ color: 'var(--q4)', texto: 'Q4 (p = 1)' }, { color: 'var(--q9)', texto: 'Q9 (p = 2)' }], 700, 50);
      titG.innerHTML = `${nm.et} · ${CONF[cfg]}` + (norma === 'S' ? ' · <span style="color:var(--texto-3)">se reporta; no es criterio de la hipótesis</span>' : '');
      panel();
    }
    function panel() {
      const T = M.tablas[cfg];
      const r = (el, t) => T[el][4][t];
      const celda = (v, teo) => `<td class="der num-tab" style="font-size:34px;font-weight:800">${EF.fmt(v, 2)}${teo != null ? `<div style="font-size:17px;color:var(--texto-3);font-weight:600">teórica ${teo}</div>` : '<div style="font-size:17px;color:var(--texto-3);font-weight:600">observada</div>'}</td>`;
      der.innerHTML = `<div class="etq" style="margin-bottom:8px">Tasas asintóticas (N = 16 → 32)</div>
        <table class="tabla" style="font-size:26px"><thead><tr><th></th><th class="der">L²</th><th class="der">H¹</th><th class="der">σ*</th></tr></thead>
        <tbody><tr><td style="color:var(--q4);font-weight:800;font-size:30px">Q4</td>${celda(r('Q4', 'tL2'), 2)}${celda(r('Q4', 'tH1'), 1)}${celda(r('Q4', 'tS'), null)}</tr>
        <tr><td style="color:var(--q9);font-weight:800;font-size:30px">Q9</td>${celda(r('Q9', 'tL2'), 3)}${celda(r('Q9', 'tH1'), 2)}${celda(r('Q9', 'tS'), null)}</tr></tbody></table>
        <div class="mini" style="margin-top:10px">Tabla 3.1 y Anexo D: las tasas del desplazamiento difieren menos de 0,01 entre las cuatro configuraciones; la de σ* se mantiene cerca de 1,5 (Q4) y de 2 (Q9).</div>`;
    }
    const crit = EF.el('div', { 'data-paso': '3', style: 'position:absolute;left:1110px;top:410px;width:610px' });
    crit.innerHTML = '<span class="insignia-ok">Teórica ± 0,5 · se cumple</span>';
    cont.appendChild(crit);
    function estado(p, animar) {
      norma = p === 1 ? 'H1' : p === 2 ? 'S' : 'L2';
      if (p < 3) cfg = 'unif_tp';
      dibujar(animar);
      if (bucleCampo) { bucleCampo.detener(); bucleCampo = null; }
      if (p === 3 && animar) {
        // recorrido por las cuatro configuraciones: mismas tasas
        const orden = Object.keys(CONF);
        let k = 0;
        EF.tween({ dur: 4 * 1500, curva: 'lineal', cada: (t) => { const j = Math.min(3, Math.floor(t * 4)); if (j !== k) { k = j; cfg = orden[j]; dibujar(false); } } });
      }
      campoN = 2; dibujarCampo();
      if (animar !== null && !EF.Deck.impresion) {
        const Ns = [2, 4, 8, 16];
        bucleCampo = EF.bucle((s) => { const n = Ns[Math.floor(s / 1.4) % 4]; if (n !== campoN) { campoN = n; dibujarCampo(); } }, { fps: 4 });
      }
    }
    return {
      entrar(p, op) { estado(p, !op.instantaneo && !op.impresion ? true : (op.impresion ? null : false)); },
      paso(k, op) { estado(k, op.adelante); },
      salir() { if (bucleCampo) { bucleCampo.detener(); bucleCampo = null; } },
      redimensionar() { dibujarCampo(); }, tema() { dibujar(false); dibujarCampo(); },
    };
  });

  // ================================================================== consistencia interna
  EF.registrarViz('consistencia-interna', function (cont) {
    const { C, P, idx, elems } = EF.canonico();
    const q9 = C.q9;
    const fila = EF.el('div', { class: 'rejilla-3', style: 'gap:26px' });
    cont.appendChild(fila);
    const tarjeta = (paso, etq, titulo, pie) => {
      const t = EF.el('div', { class: 'tarjeta', style: 'padding:22px 24px', 'data-paso': paso ? String(paso) : null, 'data-entrada': paso ? null : '1' });
      t.append(EF.el('div', { class: 'etq', text: etq }), EF.el('h3', { style: 'font-size:33px', text: titulo }));
      const cajaV = EF.el('div', { style: 'height:300px;border-radius:14px;overflow:hidden;background:var(--lienzo);margin:12px 0 14px;position:relative' });
      t.appendChild(cajaV);
      t.appendChild(EF.el('div', { style: 'font-size:24px;line-height:1.35;color:var(--texto-2)', html: pie }));
      fila.appendChild(t);
      return cajaV;
    };
    const v1 = tarjeta(0, 'Ciclo de elementos', 'Q4 → Q9 → Q4', 'Expandir crea 5 nodos por elemento (16 en esta malla); reducir los quita.<br><b style="color:var(--ok)">máx |Δu| &lt; 10⁻⁹</b>');
    const v2 = tarjeta(1, 'Identidad del nodo', '{1, 5, 50, 99} ≡ {1, 2, 3, 4}', 'El mismo problema con identificadores no contiguos da el mismo resultado.<br><b style="color:var(--ok)">diferencia &lt; 10⁻⁹</b>');
    const v3 = tarjeta(2, 'Intercambio de datos', 'CSV, DXF y memoria', 'CSV ida y vuelta: 9 nodos, 4 elementos, material, cargas y apoyos, <b style="color:var(--ok)">máx |Δu| &lt; 10⁻¹²</b>. DXF: reimportar crea 0 nodos y 0 elementos (6 duplicados omitidos).');
    const lz1 = new EF.LienzoMEF(v1, 505, 300);
    let fase = 0, bucle = null;
    const P9 = q9.nodos, E9 = q9.elems;
    function dib1() {
      lz1.redimensionar();
      lz1.encuadrar(-0.6, 11.6, -0.6, 8.6, 22);
      lz1.inicio(EF.css('--lienzo'));
      const t = fase; // 0 = Q4, 1 = Q9
      lz1.malla(P, elems.map((e) => e.con), { color: EF.css('--malla'), ancho: 2.2 });
      lz1.nodos(P, P.map((_, i) => i), { radio: 6 });
      if (t > 0) {
        const nuevos = P9.map((p, i) => i).filter((i) => !P.some((q) => Math.hypot(q[0] - P9[i][0], q[1] - P9[i][1]) < 1e-9));
        const c = lz1.ctx;
        c.save(); c.globalAlpha = t;
        for (const i of nuevos) { c.beginPath(); c.arc(lz1.X(P9[i][0]), lz1.Y(P9[i][1]), 6, 0, 2 * Math.PI); c.fillStyle = '#ffd23f'; c.fill(); c.lineWidth = 2; c.strokeStyle = '#111'; c.stroke(); }
        c.restore();
      }
      const n = t > 0.5 ? P9.length : P.length;
      lz1.etiqueta(-0.4, 8.3, t > 0.5 ? `Q9: ${n} nodos` : `Q4: ${n} nodos`, { tam: 24, color: t > 0.5 ? '#ffd23f' : EF.css('--texto'), peso: 800 });
    }
    // identidad: dos elementos idénticos con distinta numeración
    const s2 = S('svg', { class: 'viz', width: 505, height: 300, viewBox: '0 0 505 300' }, v2);
    [[0, [1, 5, 50, 99], 'var(--acento)'], [1, [1, 2, 3, 4], 'var(--primario)']].forEach(([k, ids, col]) => {
      const x0 = 50 + k * 260, y0 = 70, t = 150;
      est(S('rect', { x: x0, y: y0, width: t, height: t, rx: 4 }, s2), { relleno: 'var(--superficie-2)', trazo: 'var(--malla)', estilo: 'stroke-width:3' });
      [[x0, y0 + t], [x0 + t, y0 + t], [x0 + t, y0], [x0, y0]].forEach(([x, y], j) => {
        est(S('circle', { cx: x, cy: y, r: 9 }, s2), { relleno: 'var(--lienzo)', trazo: 'var(--nodo)', estilo: 'stroke-width:3' });
        est(S('text', { x: x + (j === 0 || j === 3 ? -14 : 14), y: y + (j < 2 ? 30 : -14), 'text-anchor': j === 0 || j === 3 ? 'end' : 'start', text: String(ids[j]) }, s2), { relleno: col, estilo: 'font:800 22px var(--fuente)' });
      });
    });
    est(S('text', { x: 255, y: 165, 'text-anchor': 'middle', text: '≡' }, s2), { relleno: 'var(--ok)', estilo: 'font:900 60px var(--fuente)' });
    // intercambio: formatos
    const s3 = S('svg', { class: 'viz', width: 505, height: 300, viewBox: '0 0 505 300' }, v3);
    [['.edufem', 'JSON'], ['CSV', 'ZIP'], ['DXF', 'CAD'], ['PDF', 'memoria']].forEach(([a, b], k) => {
      const x = 22 + (k % 2) * 245, y = 26 + Math.floor(k / 2) * 138;
      est(S('rect', { x, y, width: 220, height: 116, rx: 16 }, s3), { relleno: 'var(--superficie-2)', trazo: 'var(--linea-2)', estilo: 'stroke-width:1.5' });
      est(S('text', { x: x + 110, y: y + 56, 'text-anchor': 'middle', text: a }, s3), { relleno: 'var(--texto)', estilo: 'font:800 32px var(--mono)' });
      est(S('text', { x: x + 110, y: y + 90, 'text-anchor': 'middle', text: b + '  ✓' }, s3), { relleno: 'var(--ok)', estilo: 'font:750 22px var(--fuente)' });
    });
    const insignia = EF.el('div', { 'data-paso': '2', style: 'position:absolute;left:0;top:660px' });
    insignia.innerHTML = '<span class="insignia-ok">Sin pérdida y sin error · se cumple</span>';
    cont.appendChild(insignia);
    return {
      entrar(p, op) {
        if (bucle) bucle.detener();
        fase = 0; dib1();
        if (!op.impresion) bucle = EF.bucle((s) => { const ciclo = (s % 5) / 5; const t = ciclo < 0.15 ? 0 : ciclo < 0.35 ? (ciclo - 0.15) / 0.2 : ciclo < 0.7 ? 1 : ciclo < 0.9 ? 1 - (ciclo - 0.7) / 0.2 : 0; fase = t; dib1(); });
        else { fase = 1; dib1(); }
      },
      salir() { if (bucle) { bucle.detener(); bucle = null; } },
      redimensionar: dib1, tema: dib1,
    };
  });

  // ================================================================== viga de Timoshenko
  EF.registrarViz('timoshenko', function (cont) {
    const T = DAT().timoshenko;
    const cajaV = EF.el('div', { style: 'position:absolute;left:0;top:0;width:1720px;height:300px;border-radius:16px;overflow:hidden;border:1px solid var(--linea-2)' });
    cont.appendChild(cajaV);
    const lz = new EF.LienzoMEF(cajaV, 1720, 300);
    const leyenda = EF.el('div', { style: 'position:absolute;left:0;top:306px;width:1720px;display:flex;align-items:center;gap:14px;font:650 21px var(--fuente);color:var(--texto-3)' });
    cont.appendChild(leyenda);
    const sxMin = Math.min(...T.sx), sxMax = Math.max(...T.sx);
    leyenda.innerHTML = `σx (kgf/cm²) <span class="num-tab">${EF.fmt(sxMin, 1)}</span><span style="flex:0 0 360px;height:14px;border-radius:7px;background:linear-gradient(90deg,${EF.rango(11).map((k) => EF.jetCss(k / 10)).join(',')})"></span><span class="num-tab">${EF.fmt(sxMax, 1)}</span><span style="margin-left:auto">Q9 56 × 8 · ${T.nodos_n} nodos · ${T.gdl} GDL · deformada ampliada ×15</span>`;
    const u = T.u.map((p) => [p[0] / 100, p[1] / 100]);
    // puntos de control: marco de Timoshenko-Goodier (y hacia la fibra traccionada) -> malla (y hacia arriba)
    const puntos = { A: [0, -0.6], B: [-4.5, 0.3], C: [-3.5, 0.2] };
    let esc = 15;
    function dibujar() {
      lz.redimensionar();
      lz.encuadrar(-7.4, 7.4, -1.05, 0.95, { s: 20, d: 30, i: 26, iz: 30 });
      lz.inicio(EF.css('--lienzo'));
      lz.campo(T.nodos, T.elems, T.sx, { min: sxMin, max: sxMax, u, escala: esc, sub: 2 });
      lz.malla(T.nodos, T.elems, { color: 'rgba(0,0,0,.18)', ancho: 0.6, u, escala: esc });
      lz.apoyo(-7, 0 + esc * 0, { tam: 12 });
      lz.apoyo(7, 0, { tam: 12, movil: true });
      for (let x = -6.8; x <= 6.85; x += 0.68) {
        const i = T.nodos.reduce((b, p, k) => (Math.abs(p[1] - 0.6) < 1e-6 && Math.abs(p[0] - x) < Math.abs(T.nodos[b][0] - x) ? k : b), 0);
        const q = EF.LienzoMEF.pos(T.nodos, u, esc, i);
        lz.flecha(q[0], q[1] + 0.02, 0, -1, { largo: 26, ancho: 2.2 });
      }
      for (const [n, [x, y]] of Object.entries(puntos)) {
        const i = T.nodos.reduce((b, p, k) => (Math.hypot(p[0] - x, p[1] - y) < Math.hypot(T.nodos[b][0] - x, T.nodos[b][1] - y) ? k : b), 0);
        const q = EF.LienzoMEF.pos(T.nodos, u, esc, i);
        const c = lz.ctx;
        c.beginPath(); c.arc(lz.X(q[0]), lz.Y(q[1]), 10, 0, 2 * Math.PI); c.fillStyle = '#fff'; c.fill(); c.lineWidth = 3; c.strokeStyle = '#111'; c.stroke();
        lz.etiqueta(q[0], q[1], n, { dx: 16, dy: 0, tam: 26, peso: 850, color: '#111', fondo: '#fff', alfaFondo: 0.9 });
      }
    }
    // tabla de tensiones (Tabla 3.2) con barras frente al umbral del 1 %
    const tabla = EF.el('div', { 'data-paso': '1', style: 'position:absolute;left:0;top:350px;width:1000px' });
    const filas = T.csv_tensiones.map((r) => ({ p: r.punto, fem: +r.sigma_x_fem_kgcm2, an: +r.sigma_x_anal_kgcm2, sap: +r.sigma_x_sap_kgcm2, ea: +r.err_anal_pct, es: +r.err_sap_pct }));
    const barra = (v) => `<div style="position:relative;height:12px;border-radius:6px;background:var(--superficie-3);margin-top:6px"><div style="position:absolute;left:0;top:0;bottom:0;width:${Math.max(1.5, v * 100)}%;border-radius:6px;background:var(--ok)"></div></div>`;
    tabla.innerHTML = `<table class="tabla" style="font-size:25px"><thead><tr><th>Punto</th><th class="der">EduFEM</th><th class="der">Analítica</th><th class="der">SAP2000</th><th class="der">Error anal.</th><th class="der">Difer. SAP</th></tr></thead><tbody>
      ${filas.map((f) => `<tr><td style="font-weight:800">${f.p} · σ<sub>x</sub></td><td class="der">${EF.fmt(f.fem, 4)}</td><td class="der">${EF.fmt(f.an, 4)}</td><td class="der">${EF.fmt(f.sap, 4)}</td><td class="der" style="color:var(--ok);font-weight:800">${EF.fmt(f.ea, 4)} %${barra(f.ea)}</td><td class="der" style="color:var(--ok);font-weight:800">${EF.fmt(f.es, 4)} %${barra(f.es)}</td></tr>`).join('')}
      </tbody></table><div class="mini" style="margin-top:8px">kgf/cm². La barra llena representa el umbral del 1 %. SAP2000 (cáscara) no es el patrón de EduFEM (continuo): por eso «diferencia».</div>`;
    cont.appendChild(tabla);
    // panel derecho cambiante: perfil, flecha, equilibrio
    const der = EF.el('div', { style: 'position:absolute;left:1040px;top:350px;width:680px;height:370px' });
    cont.appendChild(der);
    function perfil() {
      der.innerHTML = '';
      const pf = T.perfiles.A;
      const G = new EF.Grafico(der, { ancho: 680, alto: 370, margen: { s: 16, d: 20, i: 84, iz: 90 }, x: { min: -150, max: 150, etiqueta: 'σx (kgf/cm²) en el centro del vano', paso: 50 }, y: { min: -0.6, max: 0.6, etiqueta: 'y (m)', paso: 0.3, dec: 1 } }).ejes();
      const an = G.serie(pf.sx_anal.map((v, k) => [v, pf.y_anal[k]]), { color: 'var(--texto-2)', marcador: null, ancho: 3 });
      const fe = G.serie(pf.sx_fem.map((v, k) => [v, pf.y_fem[k]]), { color: 'var(--acento)', marcador: 'circulo', radio: 7, ancho: 0.01 });
      G.leyenda([{ color: 'var(--texto-2)', texto: 'Analítica', marcador: null }, { color: 'var(--acento)', texto: 'EduFEM (nodos)' }], 420, 40, { tam: 22, salto: 36 });
      return [an, fe];
    }
    function flecha() {
      const F = T.csv_flecha[0];
      const vf = +F.v_fem_cm, va = +F.v_anal_cm, eb = 1.9976;
      const fila2 = (et, v, col, nota) => `<div style="margin:14px 0"><div style="display:flex;justify-content:space-between;font-size:24px"><span>${et}</span><b class="num-tab">${EF.fmt(v, 5)} cm</b></div><div style="height:22px;border-radius:8px;background:var(--superficie-3);margin-top:6px;overflow:hidden"><div class="bf" data-w="${(v / 2.1) * 100}" style="height:100%;width:0;border-radius:8px;background:${col}"></div></div><div class="mini">${nota}</div></div>`;
      der.innerHTML = `<div class="etq">Flecha en el centro de la luz (Tabla 3.3)</div>` +
        fila2('EduFEM', vf, 'var(--acento)', '') +
        fila2('Analítica con corrección de cortante', va, 'var(--primario)', `error <b style="color:var(--ok)">${EF.fmt(+F.err_pct, 4)} %</b> · umbral 3 %`) +
        fila2('Euler-Bernoulli (sin cortante)', eb, 'var(--texto-3)', 'el error aparente sería 1,85 %: la referencia debe acompañar al modelo');
      for (const b of der.querySelectorAll('.bf')) EF.tween({ dur: 900, cada: (t) => { b.style.width = `${Number(b.getAttribute('data-w')) * t}%`; } });
    }
    function equilibrio() {
      der.innerHTML = `<div class="etq">Equilibrio global</div>
        <div class="kpi ok" style="margin-top:8px"><div class="valor" style="font-size:86px">1,7<small>× 10⁻¹³</small></div><div class="etq">residuo relativo de ΣR<sub>y</sub> frente a qL = 70 000 kgf (umbral 10⁻⁸)</div></div>
        <div class="grupo-botones" style="margin-top:22px"><span class="insignia-ok">σx &lt; 1 %</span><span class="insignia-ok">flecha &lt; 3 %</span><span class="insignia-ok">residuo &lt; 10⁻⁸</span></div>`;
    }
    function estado(p, animar) {
      if (p === 0 && animar) { EF.tween({ dur: 1600, retraso: 300, curva: 'ambos', cada: (t) => { esc = 15 * t; dibujar(); } }); } else { esc = 15; dibujar(); }
      if (p <= 1) { der.style.visibility = p === 1 ? 'visible' : 'hidden'; const s = perfil(); if (animar && p === 1) s.forEach((x, k) => x.path && EF.trazar(x.path, { dur: 1000, retraso: k * 300 })); }
      if (p === 2) { der.style.visibility = 'visible'; flecha(); }
      if (p === 3) { der.style.visibility = 'visible'; equilibrio(); }
    }
    return {
      entrar(p, op) { estado(p, !op.instantaneo && !op.impresion); },
      paso(k, op) { estado(k, op.adelante); },
      redimensionar: dibujar, tema() { dibujar(); },
    };
  });

  // ================================================================== membrana de Cook
  EF.registrarViz('cook', function (cont) {
    const CK = DAT().cook;
    const Ns = [2, 4, 8, 16, 32];
    const caja = EF.el('div', { style: 'position:absolute;left:0;top:0;width:700px;height:640px;border-radius:16px;overflow:hidden;border:1px solid var(--linea-2)' });
    cont.appendChild(caja);
    const lz = new EF.LienzoMEF(caja, 700, 640);
    const ctr = EF.el('div', { class: 'grupo-botones solo-vivo', style: 'position:absolute;right:0;top:-174px' });
    const segE = EF.el('div', { class: 'segmentado' });
    const bE = ['Q4', 'Q9'].map((e) => { const b = EF.el('button', { text: e }); b.onclick = () => { el = e; dibujar(); }; segE.appendChild(b); return [e, b]; });
    const segN = EF.el('div', { class: 'segmentado naranja' });
    const bNs = Ns.map((n) => { const b = EF.el('button', { text: 'N = ' + n }); b.onclick = () => { N = n; dibujar(); }; segN.appendChild(b); return [n, b]; });
    ctr.append(segE, segN);
    cont.appendChild(ctr);
    const cajaG = EF.el('div', { style: 'position:absolute;left:740px;top:0;width:980px;height:470px' });
    cont.appendChild(cajaG);
    const inferior = EF.el('div', { style: 'position:absolute;left:740px;top:486px;width:980px' });
    cont.appendChild(inferior);
    let el = 'Q4', N = 2, paso = 0;
    let G = null, sQ4 = null, sQ9 = null, sSt = null, linea578 = null;
    function grafico() {
      cajaG.innerHTML = '';
      G = new EF.Grafico(cajaG, { ancho: 980, alto: 470, margen: { s: 20, d: 24, i: 76, iz: 100 }, x: { min: 12, max: 12000, log: true, etiqueta: 'Grados de libertad (escala logarítmica)' }, y: { min: 10, max: 25.5, paso: 2.5, dec: 1, etiqueta: 'Desplazamiento vertical en (48; 52)', tamEtiqueta: 21 } }).ejes();
      G.hLinea(CK.ref, { color: 'var(--ok)', discontinua: '14 10', ancho: 3 });
      G.texto(9000, CK.ref + 0.9, 'referencia 23,96', { ancla: 'end', color: 'var(--ok)', tam: 22, peso: 750 });
      const pts = (e) => Ns.map((n) => [CK.casos[e][String(n)].gdl, CK.casos[e][String(n)].uy]);
      sQ4 = G.serie(pts('Q4'), { color: 'var(--q4)', marcador: 'circulo', radio: 10 });
      sQ9 = G.serie(pts('Q9'), { color: 'var(--q9)', marcador: 'cuadro', radio: 9 });
      sSt = G.serie(Ns.map((n, k) => [CK.casos.Q4[String(n)].gdl, CK.stembera_q4[k]]), { color: 'var(--texto)', marcador: 'rombo', radio: 15, relleno: 'none', ancho: 0.01 });
      linea578 = G.vLinea(578, { color: 'var(--acento)', discontinua: '6 6', ancho: 3 });
      G.leyenda([{ color: 'var(--q4)', texto: 'Q4' }, { color: 'var(--q9)', texto: 'Q9' }], 720, 290, { tam: 24, salto: 40 });
    }
    function mostrarSerie(s, vis, animar) {
      s.path.style.opacity = vis ? '1' : '0';
      s.marcas.forEach((m) => (m.style.opacity = vis ? '1' : '0'));
      if (vis && animar) G.animar(s, { dur: 1400 });
    }
    function dibujar() {
      bE.forEach(([e, b]) => b.classList.toggle('sel', e === el));
      bNs.forEach(([n, b]) => b.classList.toggle('sel', n === N));
      const c = CK.casos[el][String(N)];
      lz.redimensionar();
      lz.encuadrar(-3, 51, -6, 80, { s: 24, d: 30, i: 30, iz: 60 });
      lz.inicio(EF.css('--lienzo'));
      const escala = 0.45;
      lz.malla(c.nodos, c.elems, { color: EF.css('--texto-3'), ancho: 1, discontinua: [5, 5], alfa: 0.5 });
      lz.campo(c.nodos, c.elems, c.vm, { max: EF.percentil(c.vm, 96), u: c.u, escala, sub: el === 'Q9' ? 3 : 2 });
      lz.malla(c.nodos, c.elems, { color: 'rgba(0,0,0,.4)', ancho: N >= 16 ? 0.5 : 1.2, u: c.u, escala });
      lz.empotramiento(0, 0, 44, {});
      const i = c.nodos.findIndex((p) => Math.abs(p[0] - 48) < 1e-6 && Math.abs(p[1] - 52) < 1e-6);
      const q = EF.LienzoMEF.pos(c.nodos, c.u, escala, i);
      const ctx = lz.ctx;
      ctx.beginPath(); ctx.arc(lz.X(q[0]), lz.Y(q[1]), 9, 0, 2 * Math.PI); ctx.fillStyle = '#fff'; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = '#111'; ctx.stroke();
      lz.etiqueta(-2, 79, `${el} · N = ${N} · ${c.gdl} GDL`, { tam: 28, peso: 850, color: el === 'Q4' ? EF.css('--q4') : EF.css('--q9') });
      lz.etiqueta(-2, 75, `u_y = ${EF.fmt(c.uy, 3)}   (error ${EF.fmt(c.error, 3, { signo: true })} %)`, { tam: 24, color: EF.css('--texto') });
    }
    function tablaInf() {
      const f = (n) => { const a = CK.casos.Q4[String(n)], b = CK.casos.Q9[String(n)]; return `<tr><td>${n}</td><td class="der">${a.gdl}</td><td class="der">${EF.fmt(a.uy, 3)}</td><td class="der" style="color:var(--q4)">${EF.fmt(a.error, 3)} %</td><td class="der">${b.gdl}</td><td class="der">${EF.fmt(b.uy, 3)}</td><td class="der" style="color:var(--q9)">${EF.fmt(b.error, 3)} %</td></tr>`; };
      inferior.innerHTML = paso >= 3
        ? `<div class="grupo-botones" style="margin-bottom:10px"><span class="insignia-ok">Q9, N = 8: 0,144 % &lt; 1,5 %</span><span class="insignia-ok">Q4 &lt; Q9 en las 5 mallas</span></div><div style="font-size:24px;line-height:1.35;color:var(--texto-2)"><b style="color:var(--texto)">◇ Štembera y Füssl [26, p. 28]</b> publican para su Q4: 11,845 · 18,299 · 22,079 · 23,430 · 23,818 — <b style="color:var(--texto)">los mismos valores que EduFEM</b>, hasta la última cifra.</div>`
        : paso === 2
          ? `<div class="explica" style="margin:0;font-size:27px">Con <b>578 GDL</b>: Q4 (N = 16) <b style="color:var(--q4)">−2,210 %</b> · Q9 (N = 8) <b style="color:var(--q9)">−0,144 %</b>. El error del Q9 es <b>más de diez veces menor</b> (12 a 15 veces según la referencia; 13 con 23,965).</div>`
          : `<table class="tabla" style="font-size:21px"><thead><tr><th>N</th><th class="der">GDL</th><th class="der">Q4 u<sub>y</sub></th><th class="der">error</th><th class="der">GDL</th><th class="der">Q9 u<sub>y</sub></th><th class="der">error</th></tr></thead><tbody>${[2, 8, 32].map(f).join('')}</tbody></table>`;
    }
    let recorrido = null;
    function recorrer(e, alTerminar) {
      if (recorrido) recorrido.cancelar();
      el = e; N = 2; dibujar();
      let k = 0;
      recorrido = EF.tween({ dur: 5 * 1100, curva: 'lineal', cada: (t) => { const j = Math.min(4, Math.floor(t * 5)); if (j !== k) { k = j; N = Ns[j]; dibujar(); } }, fin: () => { recorrido = null; alTerminar && alTerminar(); } });
    }
    function estado(p, animar) {
      paso = p;
      if (recorrido) { recorrido.cancelar(); recorrido = null; }
      grafico();
      mostrarSerie(sQ4, true, animar && p === 0);
      mostrarSerie(sQ9, p >= 1, animar && p === 1);
      mostrarSerie(sSt, p >= 3, false);
      linea578.style.opacity = p >= 2 ? '1' : '0';
      if (p === 0) { if (animar) recorrer('Q4'); else { el = 'Q4'; N = 32; dibujar(); } }
      if (p === 1) { if (animar) recorrer('Q9'); else { el = 'Q9'; N = 32; dibujar(); } }
      if (p === 2) { el = 'Q9'; N = 8; dibujar(); }
      if (p === 3) { el = 'Q4'; N = 8; dibujar(); if (animar) sSt.marcas.forEach((m, k) => { m.style.opacity = '0'; EF.tween({ dur: 350, retraso: 200 + k * 220, cada: (t) => { m.style.opacity = String(t); } }); }); }
      tablaInf();
    }
    return {
      entrar(p, op) { estado(p, !op.instantaneo && !op.impresion); },
      paso(k, op) { estado(k, op.adelante); },
      salir() { if (recorrido) { recorrido.cancelar(); recorrido = null; } },
      redimensionar: dibujar, tema() { dibujar(); },
    };
  });

  // ================================================================== cobertura de contenido (49 ítems)
  const UNIVERSO = {
    FEA13: ['Selección del tipo de elemento', 'Conversión Q4 ↔ Q9 del modelo'],
    FEA14: ['Definición del tamaño de elemento', 'Refinamiento manual; mallas de 2 a 32 elementos por lado'],
    FEA15: ['Efecto de la relación de aspecto y la distorsión', 'M0 (calidad en vivo); M2 (det J); MMS sobre malla distorsionada'],
    FEA16: ['Efecto del orden del elemento', 'Cook: Q4 frente a Q9 a igual número de GDL'],
    FEA17: ['Refinamiento y convergencia de la malla', 'Tasas de convergencia; curvas de error'],
    FEA18: ['Refinar en zonas de concentración de tensiones', 'Malla de densidad variable, por tabla o en el lienzo, con la calidad a la vista en M0'],
    FEA26: ['Presentar desplazamientos y tensiones', 'Contornos, isolíneas, vista 3D, tabla de resultados'],
    FEA27: ['Tensiones nodales frente a elementales', 'Sonda y vista 3D en modo crudo y suavizado'],
    FEA28: ['Deformada escalada', 'Deformada con factor de escala configurable'],
    FEA29: ['Efecto de las cargas frente a los resultados', 'Lienzo único: cargas y campos sobre el mismo modelo'],
    FEA30: ['Prueba de convergencia hasta una diferencia dada', 'Secuencias de malla con la diferencia entre mallas sucesivas como regla de parada'],
    FEA31: ['Definición de la tensión de von Mises', 'Contorno y sonda de von Mises; círculo de Mohr'],
    FEA32: ['Revisar las tensiones para decidir el refinamiento', 'Modo crudo frente a suavizado; diagnóstico de la memoria'],
    FEA33: ['Comparar reacciones con las cargas aplicadas', 'Reacciones en el post-proceso; equilibrio en la memoria'],
    FEA34: ['Correlacionar con referencias externas', 'Contraste con la solución analítica y con SAP2000'],
    FEM2: ['Ensamblar, aplicar restricciones y resolver', 'M7; memoria (ensamblaje y solución)'],
    FEM8: ['Formulación isoparamétrica bidimensional', 'M1, M2, M3 y M4'],
    FEM9: ['Integración numérica de Gauss', 'M5 (puntos de Gauss variables); sonda del post-proceso'],
  };
  const FUERA = ['FEM1', 'FEM4', 'FEM5', 'FEM6', 'FEM7', 'FEM10', 'FEM11', 'FEM12', 'FEM13', 'FEM14', 'FEM15', 'FEA6', 'FEA7', 'FEA8', 'FEA9', 'FEA21', 'FEA22', 'FEA23'];
  const ANTES = ['FEA1', 'FEA2', 'FEA3', 'FEA4', 'FEA5', 'FEA10', 'FEA11', 'FEA12', 'FEA19', 'FEA20', 'FEA24', 'FEA25'];
  EF.registrarViz('cobertura49', function (cont) {
    const izq = EF.el('div', { style: 'position:absolute;left:0;top:0;width:1110px' });
    cont.appendChild(izq);
    const grupo = (titulo, ids) => {
      izq.appendChild(EF.el('div', { class: 'etq', style: 'margin:14px 0 10px', text: titulo }));
      const g = EF.el('div', { class: 'items49', style: 'grid-template-columns:repeat(17,1fr)' });
      izq.appendChild(g);
      return ids.map((id) => { const t = EF.el('div', { class: 'item49', text: id }); t.onclick = () => detalle(id); g.appendChild(t); return [id, t]; });
    };
    const fem = grupo('Conceptos teóricos · FEM1 a FEM15', EF.rango(15).map((k) => 'FEM' + (k + 1)));
    const fea = grupo('Destrezas prácticas · FEA1 a FEA34', EF.rango(34).map((k) => 'FEA' + (k + 1)));
    const tiles = Object.fromEntries([...fem, ...fea]);
    const nota = EF.el('div', { class: 'mini', style: 'margin-top:18px;font-size:22px', html: 'Pérez-Santiago y Campos [3, pp. 1162–1163]: consenso de 67 expertos de la industria y la academia. Ítems traducidos por el autor.' });
    izq.appendChild(nota);
    const der = EF.el('div', { style: 'position:absolute;left:1150px;top:0;width:570px' });
    cont.appendChild(der);
    const leyenda = EF.el('div', { class: 'pila' });
    der.appendChild(leyenda);
    const det = EF.el('div', { class: 'tarjeta', style: 'margin-top:20px;min-height:200px;padding:20px 24px' });
    der.appendChild(det);
    const prec = EF.el('div', { 'data-paso': '3', class: 'explica', style: 'position:absolute;left:0;top:470px;width:1110px;margin:0;font-size:25px;padding:14px 22px', html: 'Prueba <b>cobertura</b>, no suficiencia ni efecto sobre quien lo usa. Es un <b>cotejo del autor</b> con una regla de marcado escrita. FEA18 y FEA30 los ejecuta el usuario sobre su modelo.' });
    cont.appendChild(prec);
    let cuenta = 0;
    function pintarLeyenda(p) {
      const fila = (color, n, t) => `<div style="display:flex;gap:16px;align-items:center;font-size:27px"><span style="width:26px;height:26px;border-radius:7px;background:${color}"></span><b class="num-tab" style="font-size:36px;min-width:56px">${n}</b><span>${t}</span></div>`;
      leyenda.innerHTML = p === 0
        ? `<div class="kpi"><div class="valor">49</div><div class="etq">ítems del consenso</div></div>`
        : fila('var(--acento)', 18, 'universo: procedimiento y su verificación') + fila('var(--primario)', 12, 'anteriores al procedimiento') + fila('var(--superficie-3)', 18, 'fuera del alcance disciplinar') + fila('var(--mal)', 1, 'no expuesto: FEM3 (deducción teórica)') +
          (p >= 2 ? `<div class="kpi ok" style="margin-top:8px"><div class="valor"><span id="c18">${cuenta}</span><small>de 18</small></div><div class="etq">con instrumento en EduFEM</div></div>` : '');
    }
    function detalle(id) {
      const u = UNIVERSO[id];
      if (!u) { det.innerHTML = `<div class="etq">${id}</div><p style="font-size:24px">${FUERA.includes(id) ? 'Fuera del alcance disciplinar (resortes, barras y vigas, axisimetría, 3D, placas y cáscaras, térmico, CAD, cargas de un análisis previo, elementos rígidos o contacto).' : ANTES.includes(id) ? 'Anterior al procedimiento: planificación, materiales o modelado de cargas y apoyos.' : id === 'FEM3' ? 'Deducción de la rigidez por métodos alternativos: un desarrollo teórico que el software no expone.' : ''}</p>`; return; }
      det.innerHTML = `<div class="etq" style="color:var(--acento)">${id}</div><h3 style="font-size:30px;margin:4px 0 10px">${u[0]}</h3><p style="font-size:24px;color:var(--texto)"><b style="color:var(--ok)">Instrumento:</b> ${u[1]}</p>`;
    }
    function clasificar(p) {
      for (const [id, t] of Object.entries(tiles)) {
        t.className = 'item49';
        if (p >= 1) {
          if (UNIVERSO[id]) t.classList.add('u');
          else if (FUERA.includes(id)) t.classList.add('fuera');
          else if (ANTES.includes(id)) t.classList.add('antes');
          else if (id === 'FEM3') t.classList.add('noexp');
        }
      }
    }
    let anim = null;
    function marcarUniverso(animar) {
      const ids = Object.keys(UNIVERSO);
      if (!animar) { ids.forEach((id) => tiles[id].classList.add('ok')); cuenta = 18; pintarLeyenda(2); detalle('FEA34'); return; }
      cuenta = 0; pintarLeyenda(2);
      anim = EF.tween({ dur: ids.length * 380, curva: 'lineal', cada: (t) => {
        const n = Math.min(ids.length, Math.floor(t * ids.length) + 1);
        while (cuenta < n) { const id = ids[cuenta]; tiles[id].classList.add('ok'); detalle(id); cuenta++; const c = document.getElementById('c18'); if (c) c.textContent = String(cuenta); }
      } });
    }
    function estado(p, animar) {
      if (anim) { anim.cancelar(); anim = null; }
      cuenta = 0;
      clasificar(p);
      pintarLeyenda(p);
      det.innerHTML = '<p style="font-size:23px;color:var(--texto-3)">Clic en un ítem para ver su instrumento.</p>';
      if (p >= 2) marcarUniverso(animar && p === 2);
    }
    return {
      entrar(p, op) { estado(p, !op.instantaneo && !op.impresion); },
      paso(k, op) { estado(k, op.adelante); },
      salir() { if (anim) { anim.cancelar(); anim = null; } },
    };
  });
})();
