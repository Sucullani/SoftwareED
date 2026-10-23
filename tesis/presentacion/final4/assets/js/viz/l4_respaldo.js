/* =====================================================================
   viz/l4_respaldo.js — láminas de respaldo para preguntas (final4).
   Copias de las de final3 (viz/analisis.js) con la redacción de final4:
     calculo-manual4   el Jacobiano de E3, la D y el equilibrio, rehechos a mano (Anexo G)
     margenes4         de dónde sale cada umbral y su margen (§ 2.1.6, Tabla 2.4, Figura CR.2)
     dp4               qué verifica hoy la deformación plana (§ 3.2, § 3.7.5, Tablas D.1 y D.3)
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const DAT = () => window.EDUFEM_DATOS;

  // ------------------------------------------------------------------ el cálculo, a mano
  EF.registrarViz('calculo-manual4', function (cont) {
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
    lineas.forEach(([paso, tex]) => {
      const d = EF.el('div', { class: 'k', 'data-paso': paso ? String(paso) : null, style: 'margin:10px 0' });
      EF.katex(d, tex, true);
      panel.appendChild(d);
    });
    panel.appendChild(EF.el('div', { class: 'mini', 'data-paso': '2', style: 'margin-top:12px', text: 'Mismas cifras que el Anexo G de la tesis (pp. 168–172) y que la memoria que genera EduFEM.' }));
    return {};
  });

  // ------------------------------------------------------------------ umbrales y márgenes
  EF.registrarViz('margenes4', function (cont) {
    const filas = [
      ['σ<sub>x</sub> frente a la analítica (máx., punto B)', 0.04, 1, '%', 2, 'Tolerancia de ingeniería fijada por el autor'],
      ['Diferencia de σ<sub>x</sub> frente a SAP2000 (máx., punto B)', 0.21, 1, '%', 2, 'Tolerancia de ingeniería fijada por el autor'],
      ['Flecha central frente a la analítica', 0.26, 3, '%', 2, 'Tolerancia de ingeniería fijada por el autor'],
      ['Cook, Q9 con N = 8 (valor absoluto)', 0.144, 1.5, '%', 3, 'Tolerancia de ingeniería fijada por el autor'],
      ['Residuo del equilibrio', 1.7e-13, 1e-8, '', 1, 'Orden del cero numérico del motor'],
      ['Tasas L² y H¹ (MMS)', null, null, '', 0, 'Medio orden (± 0,5): separa el orden esperado del inmediato inferior'],
    ];
    const cuerpo = filas.map(([n, o, u, un, dec, proc]) => {
      if (o == null) return `<tr><td>${n}</td><td class="der">teórica ± 0,5</td><td>${proc}</td><td class="der ok">desvío ≤ 0,0032</td><td class="der fuerte">&gt; 150 ×</td></tr>`;
      const r = u / o;
      const umbral = un ? '&lt; ' + EF.fmt(u, u < 2 ? 1 : 0) + ' ' + un : '&lt; ' + EF.fmtCient(u, 0);
      const obs = un ? EF.fmt(o, dec) + ' ' + un : EF.fmtCient(o, dec);
      const margen = r >= 1000 ? EF.fmtCient(r, 0) + ' ×' : EF.fmt(r, r < 10 ? 1 : 0) + ' ×';
      return `<tr><td>${n}</td><td class="der">${umbral}</td><td>${proc}</td><td class="der ok">${obs}</td><td class="der fuerte">${margen}</td></tr>`;
    }).join('');
    const t = EF.el('div');
    t.innerHTML = `<table class="tabla umbrales r-tabla"><thead><tr><th>Criterio</th><th class="der">Umbral</th><th>Procedencia del umbral (Tabla 2.4)</th><th class="der">Observado</th><th class="der">Margen</th></tr></thead><tbody>${cuerpo}</tbody></table>
    <div class="rejilla-2" style="margin-top:28px">
      <div class="tarjeta plana"><div class="etq">Umbrales explícitos, con lo que los refutaría</div><p>Ninguno se escribió antes de las primeras corridas ni se calculó a partir de sus resultados: los de la flecha, Cook y las tasas entraron a los guiones al comienzo de la verificación; los de σ<sub>x</sub> y del equilibrio, al final del desarrollo (§ 2.1.6). El del equilibrio no es una tolerancia de ingeniería: es el orden del cero numérico del motor.</p></div>
      <div class="tarjeta plana"><div class="etq">Por eso el veredicto descansa en el margen (Figura CR.2)</div><p>El criterio más cercano a su umbral, la diferencia de σ<sub>x</sub> frente a SAP2000, consume la quinta parte de él; los demás quedan a uno o varios órdenes de magnitud.</p></div>
    </div>`;
    cont.appendChild(t);
    return {};
  });

  // ------------------------------------------------------------------ deformación plana
  EF.registrarViz('dp4', function (cont) {
    const M = DAT().mms.tablas;
    const nombres = { unif_tp: 'Cuadrado · tensión plana', dist_tp: 'Distorsionado · tensión plana', unif_dp: 'Cuadrado · deformación plana', dist_dp: 'Distorsionado · deformación plana' };
    const fila = (k) => {
      const a = M[k].Q4[4], b = M[k].Q9[4];
      return `<tr class="${k.endsWith('dp') ? 'destacada' : ''}"><td>${nombres[k]}</td><td class="der">${EF.fmt(a.tL2, 3)}</td><td class="der">${EF.fmt(a.tH1, 3)}</td><td class="der">${EF.fmt(b.tL2, 3)}</td><td class="der">${EF.fmt(b.tH1, 3)}</td></tr>`;
    };
    cont.innerHTML = `<table class="tabla r-tabla"><thead><tr><th>Configuración (tasas N = 16 → 32, Tabla D.3)</th><th class="der">Q4 L²</th><th class="der">Q4 H¹</th><th class="der">Q9 L²</th><th class="der">Q9 H¹</th></tr></thead><tbody>${Object.keys(nombres).map(fila).join('')}</tbody></table>
      <div class="rejilla-3" style="margin-top:28px;gap:22px">
        <div class="tarjeta exito"><div class="etq" style="color:var(--h-ok)">Lo que muestran estas filas</div><p>Las tasas teóricas también en deformación plana y con elementos distorsionados: el ensamblaje, la cuadratura, el mapeo y las restricciones no degradan el orden.</p></div>
        <div class="tarjeta acentuada"><div class="etq" style="color:var(--acento)">Lo que no alcanzan a ver</div><p>El campo manufacturado tiene traza de la deformación y distorsión angular nulas: solo interviene D<sub>11</sub> − D<sub>12</sub>, que vale lo mismo en los dos estados planos. Estas filas no distinguen la D de deformación plana de la de tensión plana (§ 3.2).</p></div>
        <div class="tarjeta primaria"><div class="etq" style="color:var(--h-neutro)">Lo que sí acota esa D</div><p>Una prueba de deformación uniaxial con solución cerrada (Tabla D.1) acota, junto con el MMS, D<sub>11</sub> y D<sub>12</sub>: falla si en deformación plana se usa la matriz de tensión plana. D<sub>33</sub> no tiene prueba propia, y falta un contraste externo: queda como recomendación (§ 3.7.5).</p></div>
      </div>`;
    return {};
  });
})();
