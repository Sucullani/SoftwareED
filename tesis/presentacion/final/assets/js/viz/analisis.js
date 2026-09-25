/* =====================================================================
   viz/analisis.js — «Análisis de resultados» y láminas de respaldo.
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const DAT = () => window.EDUFEM_DATOS;
  const est = (e, o) => EF.estiloSvg(e, o);
  const S = EF.svg;

  // ================================================================== Q4 frente a Q9 a igualdad de GDL
  EF.registrarViz('q4q9', function (cont) {
    const CK = DAT().cook;
    const Ns = [2, 4, 8, 16, 32];
    const caja = EF.el('div', { style: 'position:absolute;left:0;top:0;width:1000px;height:640px' });
    cont.appendChild(caja);
    const der = EF.el('div', { 'data-paso': '2', style: 'position:absolute;left:1050px;top:0;width:670px' });
    der.innerHTML = `<div class="etq" style="margin-bottom:8px">Síntesis Q4 frente a Q9 (Tabla 3.5)</div>
      <table class="tabla" style="font-size:21px;white-space:nowrap"><thead><tr><th>Aspecto</th><th class="der" style="color:var(--q4)">Q4</th><th class="der" style="color:var(--q9)">Q9</th></tr></thead><tbody>
      <tr><td>Tasa L² (MMS)</td><td class="der">h<sup>2,00</sup></td><td class="der">h<sup>3,00</sup></td></tr>
      <tr><td>Tasa H¹ (MMS)</td><td class="der">h<sup>1,00</sup></td><td class="der">h<sup>2,00</sup></td></tr>
      <tr><td>Cook N = 8</td><td class="der">22,079 (−7,850 %)</td><td class="der">23,925 (−0,144 %)</td></tr>
      <tr><td>Cook N = 16</td><td class="der">23,430 (−2,210 %)</td><td class="der">23,949 (−0,044 %)</td></tr>
      <tr><td>Timoshenko σ<sub>x</sub></td><td class="der">—</td><td class="der">0,0414 %</td></tr>
      <tr><td>Bajo distorsión</td><td class="der">bloqueo parcial</td><td class="der">sin bloqueo apreciable</td></tr></tbody></table>
      <div class="mini" style="margin-top:10px">La viga se resolvió solo con Q9 (§ 2.1.4).</div>`;
    cont.appendChild(der);
    const nota = EF.el('div', { 'data-paso': '1', class: 'explica', style: 'position:absolute;left:0;top:650px;width:1000px;margin:0;font-size:25px;padding:12px 22px', html: 'Con 578 GDL el error del Q9 es <b>más de diez veces menor</b> que el del Q4 (entre 12 y 15 veces según la referencia). Con 2178 GDL el error del Q9 cae dentro de la incertidumbre de la referencia y la razón deja de ser significativa.' });
    cont.appendChild(nota);
    let G = null;
    function dibujar(p, animar) {
      caja.innerHTML = '';
      G = new EF.Grafico(caja, { ancho: 1000, alto: 640, margen: { s: 20, d: 30, i: 80, iz: 120 }, x: { min: 12, max: 12000, log: true, etiqueta: 'Grados de libertad' }, y: { min: 0.001, max: 100, log: true, etiqueta: 'Error del desplazamiento en Cook (%)', fmt: (v) => EF.fmtSig(v, 1).replace(/,0+$/, '') } }).ejes();
      const banda = G.banda(0.001, 0.05, { color: 'var(--ok-suave)' });
      banda.style.opacity = p >= 2 ? '1' : '0';
      if (p >= 2) G.texto(14, 0.02, 'incertidumbre de la referencia ≈ 0,05 %', { ancla: 'start', color: 'var(--ok)', tam: 21 });
      const pts = (e) => Ns.map((n) => [CK.casos[e][String(n)].gdl, Math.max(1e-3, Math.abs(CK.casos[e][String(n)].error))]);
      const s4 = G.serie(pts('Q4'), { color: 'var(--q4)', marcador: 'circulo', radio: 10 });
      const s9 = G.serie(pts('Q9'), { color: 'var(--q9)', marcador: 'cuadro', radio: 9 });
      if (animar && p === 0) { G.animar(s4, { dur: 1200 }); G.animar(s9, { dur: 1200, retraso: 500 }); }
      G.leyenda([{ color: 'var(--q4)', texto: 'Q4 bilineal' }, { color: 'var(--q9)', texto: 'Q9 bicuadrático' }], 620, 60);
      if (p >= 1) {
        G.vLinea(578, { color: 'var(--acento)', discontinua: '6 6', ancho: 3 });
        const y4 = 2.210, y9 = 0.144;
        const lin = S('line', { x1: G.sx(578) + 18, x2: G.sx(578) + 18, y1: G.sy(y4), y2: G.sy(y9) }, G.gSobre);
        est(lin, { trazo: 'var(--acento)', estilo: 'stroke-width:4' });
        G.texto(G.sx(578) + 34, (G.sy(y4) + G.sy(y9)) / 2 + 10, '> 10 ×', { px: true, color: 'var(--acento)', tam: 36, peso: 850 });
        G.texto(G.sx(578) - 14, G.sy(y4) + 34, '−2,210 %', { px: true, ancla: 'end', color: 'var(--q4)', tam: 23, peso: 800 });
        G.texto(G.sx(578) - 14, G.sy(y9) + 34, '−0,144 %', { px: true, ancla: 'end', color: 'var(--q9)', tam: 23, peso: 800 });
        if (animar && p === 1) EF.trazar(lin, { dur: 700 });
      }
    }
    return { entrar(p, op) { dibujar(p, !op.instantaneo && !op.impresion); }, paso(k, op) { dibujar(k, op.adelante); } };
  });

  // ================================================================== la lección de la extrapolación
  EF.registrarViz('leccion', function (cont) {
    const { C, P, idx, elems } = EF.canonico();
    const E3 = C.elementos[String(C.showcase)];
    const linea = EF.el('div', { class: 'linea-tiempo' });
    const hitos = [
      ['1', 'El defecto', 'La matriz de extrapolación del Q4 estaba escrita para otra numeración de los puntos de Gauss.'],
      ['2', 'Las tasas no lo ven', 'Esa matriz actúa después de resolver: los desplazamientos, y sus tasas, no cambian.'],
      ['3', 'La memoria lo delata', 'Leída paso a paso, las tensiones nodales no cerraban con las de los puntos de Gauss.'],
      ['4', 'Corrección y prueba nueva', 'E se construye invirtiendo M con los puntos del motor; una prueba exige reproducir campos polinómicos.'],
    ];
    hitos.forEach(([n, t, d], k) => linea.appendChild(EF.el('div', { class: 'hito', 'data-paso': k === 0 ? null : String(k), 'data-entrada': k === 0 ? '1' : null }, [EF.el('b', { text: n }), EF.el('div', { class: 't', text: t }), EF.el('div', { class: 'd', text: d })])));
    cont.appendChild(linea);
    const caja = EF.el('div', { style: 'position:absolute;left:0;top:220px;width:820px;height:380px;border-radius:16px;overflow:hidden;border:1px solid var(--linea-2)' });
    cont.appendChild(caja);
    const lz = new EF.LienzoMEF(caja, 820, 380);
    const der = EF.el('div', { style: 'position:absolute;left:860px;top:220px;width:860px' });
    cont.appendChild(der);
    let mal = false;
    const seg = EF.el('div', { class: 'segmentado solo-vivo', style: 'position:absolute;right:0;top:-174px' });
    const bB = EF.el('button', { class: 'sel', text: 'E correcta' }), bM = EF.el('button', { text: 'E con la numeración equivocada' });
    bB.onclick = () => { mal = false; bB.classList.add('sel'); bM.classList.remove('sel'); dibujar(); tabla(); };
    bM.onclick = () => { mal = true; bM.classList.add('sel'); bB.classList.remove('sel'); dibujar(); tabla(); };
    seg.append(bB, bM);
    cont.appendChild(seg);
    function valores() { return C.nodos.map((n) => (mal ? C.nodal[String(n.id)].mal[1] : C.nodal[String(n.id)].sy)); }
    function dibujar() {
      lz.redimensionar();
      lz.encuadrar(-0.6, 11.6, -0.6, 8.6, { s: 26, d: 30, i: 40, iz: 30 });
      lz.inicio(EF.css('--lienzo'));
      const v = valores();
      const ref = C.nodos.map((n) => C.nodal[String(n.id)].sy);
      const vmin = Math.min(...v, ...ref), vmax = Math.max(...v, ...ref);
      lz.campo(P, elems.map((e) => e.con), v, { min: vmin, max: vmax, sub: 6 });
      lz.malla(P, elems.map((e) => e.con), { color: 'rgba(255,255,255,.7)', ancho: 1.6 });
      C.nodos.forEach((n, i) => {
        const dif = Math.abs(v[i] - ref[i]) > 0.05;
        lz.etiqueta(P[i][0], P[i][1], EF.fmt(v[i], 1), { dx: 10, dy: -14, tam: 18, color: dif ? '#fff' : '#fff', fondo: dif ? '#d23c3c' : 'rgba(10,16,30,.75)', alfaFondo: 0.9 });
      });
      lz.etiqueta(-0.4, -0.45, mal ? 'σy nodal con la E mal escrita' : 'σy nodal con la E correcta (la del motor)', { tam: 22, color: mal ? '#ff7a7a' : EF.css('--texto'), peso: 750 });
    }
    function tabla() {
      const sg = E3.sigma_gauss.map((s) => s[1]);
      const cb = E3.cierre_bien.map((s) => s[1]);
      const cm = E3.cierre_mal.map((s) => s[1]);
      const fila = (k) => { const ok = Math.abs(cm[k] - sg[k]) < 1e-6; return `<tr><td>PG${k + 1}</td><td class="der">${EF.fmt(sg[k], 2)}</td><td class="der" style="color:var(--ok)">${EF.fmt(cb[k], 2)}</td><td class="der" style="${mal ? (ok ? 'color:var(--ok)' : 'color:var(--mal);font-weight:800') : 'color:var(--texto-3)'}">${EF.fmt(cm[k], 2)}${mal && !ok ? ' ✗' : ''}</td></tr>`; };
      der.innerHTML = `<div class="etq" style="margin-bottom:6px">¿Cierran? Volver a interpolar en los puntos de Gauss los valores nodales de E${C.showcase} (σy)</div>
        <table class="tabla" style="font-size:22px"><thead><tr><th></th><th class="der">σ en Gauss</th><th class="der">con E correcta</th><th class="der">con E mal escrita</th></tr></thead><tbody>${[0, 1, 2, 3].map(fila).join('')}</tbody></table>
        <div class="mini" style="margin-top:8px">Con la E correcta, lo extrapolado vuelve exacto a los puntos de Gauss; con la mal escrita, los puntos 3 y 4 salen intercambiados.</div>`;
    }
    const remate = EF.el('div', { class: 'remate', 'data-paso': '3', style: 'position:absolute;left:0;right:0;top:648px;bottom:auto' }, [EF.el('span', { class: 'ico', text: '◆' }), EF.el('span', { text: 'Fue la trazabilidad la que hizo visible un defecto de exactitud que las métricas agregadas no mostraban: la hipótesis no es circular.' })]);
    cont.appendChild(remate);
    return {
      entrar(p) { mal = p === 2; bB.classList.toggle('sel', !mal); bM.classList.toggle('sel', mal); dibujar(); tabla(); },
      paso(k) { mal = k === 2; bB.classList.toggle('sel', !mal); bM.classList.toggle('sel', mal); dibujar(); tabla(); },
      redimensionar: dibujar, tema() { dibujar(); },
    };
  });

  // ================================================================== escalabilidad (Tabla 3.9)
  const TIEMPOS = [
    [578, 0.004, 0.007, 3, 0.21], [2178, 0.013, 0.026, 38, 0.81], [4802, 0.028, 0.061, 184, 1.81],
    [8450, 0.049, 0.127, 571, 3.20], [18818, 0.111, 0.329, 2833, 7.19], [33282, 0.191, 0.721, 8862, 12.77],
  ];
  EF.registrarViz('escalabilidad', function (cont) {
    const izq = EF.el('div', { style: 'position:absolute;left:0;top:0;width:840px;height:600px' });
    cont.appendChild(izq);
    const der = EF.el('div', { 'data-paso': '1', style: 'position:absolute;left:880px;top:0;width:840px;height:600px' });
    cont.appendChild(der);
    const nota = EF.el('div', { 'data-paso': '2', style: 'position:absolute;left:0;top:616px;width:1720px' });
    nota.innerHTML = '<div class="grupo-botones"><span class="ficha acento" style="font-size:24px">Reordenamiento de mínimo grado: 1,7 × más rápido con 2178 GDL · 2,0 × con 8450 · 2,9 × con 33 282</span></div><div class="mini" style="margin-top:10px">Intel de 2012, Windows 10, Python 3.13; una corrida representativa (puede variar hasta un 50 %). Reproducible con tests/bench_timing.py.</div>';
    cont.appendChild(nota);
    function dibujar(p, animar) {
      izq.innerHTML = ''; der.innerHTML = '';
      const G = new EF.Grafico(izq, { ancho: 840, alto: 600, margen: { s: 20, d: 20, i: 80, iz: 110 }, x: { min: 400, max: 50000, log: true, etiqueta: 'Grados de libertad (Cook, Q9)' }, y: { min: 0.002, max: 2, log: true, etiqueta: 'Tiempo (s)', fmt: (v) => EF.fmtSig(v, 1).replace(/,0+$/, '') } }).ejes();
      const sa = G.serie(TIEMPOS.map((t) => [t[0], t[1]]), { color: 'var(--primario)', marcador: 'circulo', radio: 9 });
      const ss = G.serie(TIEMPOS.map((t) => [t[0], t[2]]), { color: 'var(--acento)', marcador: 'cuadro', radio: 8 });
      G.leyenda([{ color: 'var(--primario)', texto: 'Ensamblaje' }, { color: 'var(--acento)', texto: 'Solución' }], 140, 50);
      G.texto(33282, 0.721, '0,72 s', { color: 'var(--acento)', tam: 24, peso: 800, ancla: 'end' });
      if (animar && p === 0) { G.animar(sa, { dur: 1100 }); G.animar(ss, { dur: 1100, retraso: 400 }); }
      if (p >= 1) {
        const H = new EF.Grafico(der, { ancho: 840, alto: 600, margen: { s: 20, d: 20, i: 80, iz: 110 }, x: { min: 0.5, max: 6.5, marcas: [1, 2, 3, 4, 5, 6], fmt: (v) => EF.fmt(TIEMPOS[v - 1][0], 0) }, y: { min: 0.1, max: 20000, log: true, etiqueta: 'Memoria de K (MB)', fmt: (v) => EF.fmtSig(v, 1).replace(/,0+$/, '') } }).ejes();
        TIEMPOS.forEach((t, k) => {
          const x = H.sx(k + 1);
          [[t[3], 'var(--mal)', -30], [t[4], 'var(--ok)', 4]].forEach(([v, col, dx]) => {
            const y0 = H.sy(0.1), y1 = H.sy(v);
            const r = S('rect', { x: x + dx, y: y1, width: 26, height: y0 - y1, rx: 4 }, H.gDatos);
            est(r, { relleno: col });
            if (animar && p === 1) { r.setAttribute('height', '0'); r.setAttribute('y', String(y0)); EF.tween({ dur: 700, retraso: 150 + k * 120, cada: (e) => { r.setAttribute('height', String((y0 - y1) * e)); r.setAttribute('y', String(y0 - (y0 - y1) * e)); } }); }
          });
        });
        H.texto(H.sx(6) - 30, H.sy(8862) - 14, '8,9 GB', { px: true, ancla: 'middle', color: 'var(--mal)', tam: 22, peso: 800 });
        H.texto(H.sx(6) + 17, H.sy(12.77) - 22, '13 MB', { px: true, ancla: 'middle', color: 'var(--ok)', tam: 22, peso: 800 });
        H.leyenda([{ color: 'var(--mal)', texto: 'K densa', marcador: null }, { color: 'var(--ok)', texto: 'K dispersa', marcador: null }], 140, 50);
      }
    }
    return { entrar(p, op) { dibujar(p, !op.instantaneo && !op.impresion); }, paso(k, op) { dibujar(k, op.adelante); } };
  });

  // ================================================================== respaldo: márgenes frente a los umbrales
  EF.registrarViz('margenes', function (cont) {
    const filas = [
      ['σx frente a la analítica (máx., punto B)', 0.0414, 1, '%', 4], ['σx frente a SAP2000 (máx., punto B)', 0.2066, 1, '%', 4],
      ['Flecha frente a la analítica', 0.2633, 3, '%', 4], ['Cook, Q9 con N = 8', 0.144, 1.5, '%', 3], ['Residuo del equilibrio', 1.7e-13, 1e-8, '', 1],
    ];
    const t = EF.el('div');
    t.innerHTML = `<table class="tabla" style="font-size:27px"><thead><tr><th>Criterio</th><th class="der">Umbral</th><th class="der">Observado</th><th class="der">Margen</th><th style="width:34%"></th></tr></thead><tbody>${filas.map(([n, o, u, un, dec]) => {
      const r = u / o;
      const w = Math.min(100, (Math.log10(r) / 5) * 100);
      return `<tr><td>${n}</td><td class="der">${un ? EF.fmt(u, u < 2 ? 1 : 0) + ' ' + un : EF.fmtCient(u, 0)}</td><td class="der" style="color:var(--ok);font-weight:800">${un ? EF.fmt(o, dec) + ' ' + un : EF.fmtCient(o, dec)}</td><td class="der" style="font-weight:800">${r > 1000 ? EF.fmtCient(r, 0) : EF.fmt(r, 1)} ×</td><td><div style="height:14px;border-radius:7px;background:var(--superficie-3)"><div style="height:100%;width:${w}%;border-radius:7px;background:var(--ok)"></div></div></td></tr>`;
    }).join('')}</tbody></table>
    <div class="rejilla-2" style="margin-top:30px">
      <div class="tarjeta plana"><div class="etq">Criterios de aceptación, no estimaciones</div><p>Se fijaron antes de las corridas (§ 2.1.6) y cada uno declara qué lo refutaría. El del equilibrio no es una tolerancia de ingeniería: es el orden del cero numérico del motor.</p></div>
      <div class="tarjeta plana"><div class="etq">Con umbrales más exigentes</div><p>Con 0,5 % para σ<sub>x</sub> y 1 % para la flecha y Cook, los mismos datos seguirían cumpliendo.</p></div>
    </div>`;
    cont.appendChild(t);
    return {};
  });

  // ================================================================== respaldo: deformación plana
  EF.registrarViz('dp', function (cont) {
    const M = DAT().mms.tablas;
    const nombres = { unif_tp: 'Cuadrado · tensión plana', dist_tp: 'Distorsionado · tensión plana', unif_dp: 'Cuadrado · deformación plana', dist_dp: 'Distorsionado · deformación plana' };
    const fila = (k) => { const a = M[k].Q4[4], b = M[k].Q9[4]; const dp = k.endsWith('dp'); return `<tr class="${dp ? 'destacada' : ''}"><td>${nombres[k]}</td><td class="der">${EF.fmt(a.tL2, 3)}</td><td class="der">${EF.fmt(a.tH1, 3)}</td><td class="der">${EF.fmt(b.tL2, 3)}</td><td class="der">${EF.fmt(b.tH1, 3)}</td></tr>`; };
    cont.innerHTML = `<table class="tabla" style="font-size:28px"><thead><tr><th>Configuración (N = 16 → 32)</th><th class="der">Q4 L²</th><th class="der">Q4 H¹</th><th class="der">Q9 L²</th><th class="der">Q9 H¹</th></tr></thead><tbody>${Object.keys(nombres).map(fila).join('')}</tbody></table>
      <div class="rejilla-3" style="margin-top:28px;gap:22px">
        <div class="tarjeta exito"><div class="etq" style="color:var(--ok)">Lo que muestran estas filas</div><p style="font-size:25px">Las tasas teóricas también en deformación plana y con elementos distorsionados: el ensamblaje, la cuadratura, el mapeo y las restricciones no degradan el orden.</p></div>
        <div class="tarjeta acentuada"><div class="etq" style="color:var(--acento)">Lo que no alcanzan a ver</div><p style="font-size:25px">El campo manufacturado tiene tr ε = 0 y γ<sub>xy</sub> = 0: λ y D<sub>33</sub> no intervienen, y la misma u<sub>M</sub> resuelve el problema con la D de cualquiera de los dos estados. Estas filas no distinguen una D de la otra.</p></div>
        <div class="tarjeta primaria"><div class="etq" style="color:var(--primario)">Lo que sí comprueba la D</div><p style="font-size:25px">Un estado uniaxial con solución exacta ejercita sus términos normales: σ<sub>x</sub> = (λ + 2μ)δ, σ<sub>y</sub> = σ<sub>z</sub> = λδ y von Mises = 2μδ, con error menor que 10<sup>−9</sup>. Falta un contraste externo: un caso civil con peso propio.</p></div>
      </div>`;
    return {};
  });

  // ================================================================== respaldo: el cálculo, a mano
  EF.registrarViz('calculo-manual', function (cont) {
    const C = DAT().canonico;
    const E3 = C.elementos[String(C.showcase)];
    const g = E3.gauss[0];
    const X = E3.X;
    const dN = g.dN;
    const term = (fila, col) => dN[fila].map((d, i) => `(${EF.tex(d, 4)})(${EF.tex(X[i][col], 0)})`).join('+');
    const panel = EF.el('div', { class: 'panel-mat traza-panel', style: 'height:700px' });
    cont.appendChild(panel);
    const lineas = [
      [0, `\\text{Nodos }${E3.nodos.join(',')}:\\;\\mathbf{X}_e=${EF.texMat(X, 0)},\\quad (\\xi,\\eta)=\\left(-\\tfrac{1}{\\sqrt3},-\\tfrac{1}{\\sqrt3}\\right)`],
      [0, `J_{11}=\\sum_i \\frac{\\partial N_i}{\\partial\\xi}x_i=${term(0, 0)}=${EF.tex(g.J[0][0], 4)}`],
      [0, `J_{12}=${term(0, 1)}=${EF.tex(g.J[0][1], 4)}`],
      [0, `J_{21}=${term(1, 0)}=${EF.tex(g.J[1][0], 4)}`],
      [0, `J_{22}=${term(1, 1)}=${EF.tex(g.J[1][1], 4)}`],
      [0, `\\det\\mathbf{J}=(${EF.tex(g.J[0][0], 4)})(${EF.tex(g.J[1][1], 4)})-(${EF.tex(g.J[0][1], 4)})(${EF.tex(g.J[1][0], 4)})=\\boxed{${EF.tex(g.detJ, 4)}}`],
      [1, `\\mathbf{D}=\\frac{E}{1-\\nu^2}\\begin{bmatrix}1&\\nu&0\\\\\\nu&1&0\\\\0&0&\\frac{1-\\nu}{2}\\end{bmatrix}=\\frac{225\\,000}{1-0{,}2^2}\\begin{bmatrix}1&0{,}2&0\\\\0{,}2&1&0\\\\0&0&0{,}4\\end{bmatrix}=${EF.texMat(C.D, 0)}`],
      [2, `\\textstyle\\sum R_y=${C.apoyos.map((a) => EF.tex(C.R[2 * C.nodos.findIndex((n) => n.id === a) + 1], 2)).join('+')}=${EF.tex(C.apoyos.reduce((s, a) => s + C.R[2 * C.nodos.findIndex((n) => n.id === a) + 1], 0), 2)}=P`],
    ];
    const els = lineas.map(([paso, tex]) => {
      const d = EF.el('div', { class: 'k', 'data-paso': paso ? String(paso) : null, style: 'margin:10px 0' });
      EF.katex(d, tex, true);
      panel.appendChild(d);
      return d;
    });
    panel.appendChild(EF.el('div', { class: 'mini', 'data-paso': '2', style: 'margin-top:12px', text: 'Mismas cifras que el Anexo G (pp. 166, 167 y 169) y que la memoria que genera EduFEM.' }));
    return {};
  });
})();
