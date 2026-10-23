/* =====================================================================
   deck.js — motor de la presentación.

   Láminas: <section class="lamina" id="..." data-bloque="teoria" data-titulo="...">
   Pasos dentro de una lámina (se revelan con → o Espacio):
     data-paso="k"          visible desde el paso k
     data-hasta="k"         visible hasta el paso k (inclusive)
     data-solo="k[,j]"      visible solo en esos pasos
     data-entrada="n"       se anima al entrar a la lámina (orden n)
     data-clase-paso="k:c"  agrega la clase c desde el paso k
   Visualizaciones: <div data-viz="nombre"> -> EF.registrarViz(nombre, fábrica)
   Enlaces entre láminas: <button data-ir="id-lamina">  (apila el historial)

   Modos por la URL:  ?tema=claro|oscuro   ?captura=1   ?impresion=1   #/id/paso
   ===================================================================== */
(function () {
  'use strict';
  const EF = window.EF;
  const { $, $$, el } = EF;

  // ------------------------------------------------------------------ hilo conductor (Taller 6)
  const BLOQUES = (EF.BLOQUES = [
    { id: 'intro', n: '01', nombre: 'Introducción', corto: 'Introducción', min: 6 },
    { id: 'teoria', n: '02', nombre: 'Base teórica', corto: 'Base teórica', min: 9 },
    { id: 'diseno', n: '03', nombre: 'Diseño y desarrollo del modelo', corto: 'Diseño y desarrollo', min: 15 },
    { id: 'resultados', n: '04', nombre: 'Presentación de resultados', corto: 'Resultados', min: 7 },
    { id: 'analisis', n: '05', nombre: 'Análisis de resultados', corto: 'Análisis', min: 4 },
    { id: 'conclusiones', n: '06', nombre: 'Conclusiones y recomendaciones', corto: 'Conclusiones', min: 4 },
  ]);
  const BLOQUE = Object.fromEntries(BLOQUES.map((b) => [b.id, b]));

  // ------------------------------------------------------------------ parámetros
  const params = new URLSearchParams(location.search);
  const MODO_CAPTURA = params.has('captura');
  const MODO_IMPRESION = params.has('impresion');

  // ------------------------------------------------------------------ estado
  const D = (EF.Deck = {
    laminas: [],      // {el, id, bloque, titulo, pasos, respaldo, lab, viz: [] }
    principales: [],
    i: -1,
    paso: 0,
    historial: [],
    escala: 1,
    listo: null,
  });
  const fabricas = EF._fabricas;

  // ------------------------------------------------------------------ tema
  const PPT = EF.estilo === 'ppt';
  function temaInicial() {
    if (PPT) return 'claro';   // la versión PowerPoint tiene un solo tema
    const p = params.get('tema');
    if (p === 'claro' || p === 'oscuro') return p;
    try { const g = localStorage.getItem('edufem-tema'); if (g) return g; } catch (e) { /* sin almacenamiento */ }
    return 'oscuro';
  }
  function aplicarTema(t, avisar) {
    document.documentElement.setAttribute('data-tema', t);
    try { localStorage.setItem('edufem-tema', t); } catch (e) { /* sin almacenamiento */ }
    for (const L of D.laminas) for (const v of L.viz) if (v.inst && v.inst.tema) v.inst.tema();
    if (avisar) aviso(t === 'claro' ? 'Tema claro (salas iluminadas)' : 'Tema oscuro (proyección)');
  }
  D.alternarTema = () => {
    if (PPT) { aviso('La versión PowerPoint tiene un solo tema; la oscura es Defensa_EduFEM.html'); return; }
    aplicarTema(document.documentElement.getAttribute('data-tema') === 'claro' ? 'oscuro' : 'claro', true);
  };

  // ------------------------------------------------------------------ escala
  function ajustar() {
    const esc = $('#escenario');
    if (MODO_IMPRESION) { D.escala = 1; return; }
    const W = window.innerWidth, H = window.innerHeight;
    const s = Math.min(W / 1920, H / 1080);
    D.escala = s;
    esc.style.left = '0px';
    esc.style.top = '0px';
    esc.style.transform = `translate(${(W - 1920 * s) / 2}px, ${(H - 1080 * s) / 2}px) scale(${s})`;
    const L = D.laminas[D.i];
    if (L) for (const v of L.viz) if (v.inst && v.inst.redimensionar) v.inst.redimensionar();
  }
  EF.escala = () => D.escala;
  // ?nitidez=2: en la captura, los lienzos se dibujan al doble de resolución (conversor a PowerPoint)
  const NITIDEZ = EF.clamp(Number(params.get('nitidez') || 1), 1, 3);
  EF.escalaRender = () => (MODO_CAPTURA ? NITIDEZ : EF.clamp(D.escala * (window.devicePixelRatio || 1), 1, 2.5));
  /** Coordenadas del cliente -> coordenadas del elemento, en px de diseño. */
  EF.aLocal = function (elemento, clientX, clientY) {
    const r = elemento.getBoundingClientRect();
    return { x: (clientX - r.left) / D.escala, y: (clientY - r.top) / D.escala };
  };

  // ------------------------------------------------------------------ construcción
  function recolectar() {
    D.laminas = $$('.lamina').map((s, k) => {
      const pasosAttr = s.getAttribute('data-pasos');
      let max = 0;
      for (const e of $$('[data-paso]', s)) max = Math.max(max, Number(e.getAttribute('data-paso')));
      for (const e of $$('[data-solo]', s)) for (const v of e.getAttribute('data-solo').split(',')) max = Math.max(max, Number(v));
      const h = $('.titulo', s);
      return {
        el: s, k, id: s.id || 'l' + k,
        bloque: s.getAttribute('data-bloque') || '',
        titulo: s.getAttribute('data-titulo') || (h ? h.textContent.trim() : s.id),
        pasos: pasosAttr != null ? Number(pasosAttr) : max,
        respaldo: s.hasAttribute('data-respaldo'),
        lab: s.getAttribute('data-lab') || '',
        viz: $$('[data-viz]', s).map((c) => ({ contenedor: c, nombre: c.getAttribute('data-viz'), inst: null })),
        visitada: false,
      };
    });
    D.principales = D.laminas.filter((L) => !L.respaldo);
    D.porId = Object.fromEntries(D.laminas.map((L) => [L.id, L]));
  }

  function numerarRotulos() {
    for (const L of D.laminas) {
      const r = $('.rotulo[data-auto]', L.el);
      const b = BLOQUE[L.bloque];
      if (r && b) {
        const sec = r.getAttribute('data-sec');
        r.innerHTML = `<span class="num">${b.n}</span><span>${b.nombre}</span>` +
          (sec ? `<span class="fuente-sec">· ${sec}</span>` : '');
      }
      const rot = $('.rotulo', L.el);
      const fs = rot && $('.fuente-sec', rot);
      const fuente = fs ? fs.textContent.replace(/^\s*·\s*/, '').trim() : '';
      // pie de cada lámina: en la versión 1 solo se imprime; en la PowerPoint se ve siempre
      const n = D.principales.indexOf(L) + 1;
      L.el.appendChild(el('div', { class: 'pie-lamina' }, [
        el('span', { class: 'izq', text: 'EduFEM · Defensa de tesis · Ingeniería Civil · UATF' }),
        el('span', { class: 'cen', text: fuente ? (/^(§|Tabla|Figura|Anexo|Cap)/.test(fuente) ? 'Tesis: ' : '') + fuente : '' }),
        el('span', { class: 'der', text: L.respaldo ? 'Respaldo' : (PPT ? String(n) : `${n} / ${D.principales.length}`) }),
      ]));
      if (PPT) decorarPpt(L, rot);
    }
  }

  /** Versión PowerPoint: barra naranja del rótulo, acento bajo el título y puntos de avance. */
  function decorarPpt(L, rot) {
    if (rot && !$('.barra-rot', rot)) rot.prepend(el('span', { class: 'barra-rot' }));
    const cab = $('.cabecera', L.el);
    const tit = cab && $('.titulo', cab);
    if (tit && !$('.regla-titulo', cab)) tit.after(el('div', { class: 'regla-titulo' }));
    const bi = BLOQUES.findIndex((b) => b.id === L.bloque);
    if (!cab || L.respaldo || bi < 0) return;
    cab.append(el('div', { class: 'puntos-ppt' }, BLOQUES.map((b, k) => {
      const destino = D.principales.find((x) => x.bloque === b.id);
      return el('button', {
        class: k < bi ? 'hecho' : k === bi ? 'actual' : '', title: `${b.n} · ${b.nombre}`,
        'data-ir': destino ? destino.id : null, 'data-sin-historial': true,
      });
    })));
  }

  function construirCromo() {
    const esc = $('#escenario');
    // pie con el hilo conductor
    const pie = el('div', { id: 'pie' });
    const hilo = el('div', { class: 'hilo' });
    for (const b of BLOQUES) {
      hilo.append(el('button', {
        'data-bloque': b.id, title: `Ir a ${b.nombre}`,
        onclick: () => { const L = D.principales.find((x) => x.bloque === b.id); if (L) D.irA(L.id, { apilar: false }); },
      }, [el('span', { class: 'n', text: b.n }), el('span', { text: b.corto })]));
    }
    const volver = el('div', { id: 'volver' }, el('button', { onclick: () => D.volver() }, [el('span', { text: '↩' }), el('span', { class: 'txt', text: 'Volver' })]));
    pie.append(
      hilo,
      PPT ? '' : volver,
      el('div', { class: 'progreso' }, el('i')),
      el('div', { class: 'contador', text: '' }),
      el('div', { class: 'nav' }, [
        el('button', { title: 'Anterior (←)', text: '‹', onclick: () => D.anterior() }),
        el('button', { title: 'Siguiente (→)', text: '›', onclick: () => D.siguiente() }),
        el('button', { title: 'Índice (M)', text: '☰', onclick: () => alternarCapa('menu') }),
        el('button', { title: 'Ayuda (?)', text: '?', onclick: () => alternarCapa('ayuda') }),
      ]),
      el('div', { class: 'marca', html: 'Edu<b>FEM</b>' }),
    );
    esc.append(pie);
    // en la versión PowerPoint el pie global solo lleva los controles: «Volver» va arriba
    if (PPT) esc.append(volver);


    // menú
    const menu = el('div', { id: 'menu', class: 'capa' });
    menu.append(el('button', { class: 'cerrar', text: '×', onclick: () => cerrarCapas() }));
    const cont = el('div', { class: 'contenido' });
    cont.append(el('h2', { text: 'Índice de la defensa' }),
      el('div', { class: 'sub', text: 'Clic en una lámina para ir. Los laboratorios interactivos y el respaldo para preguntas están al final.' }));
    const cols = el('div', { class: 'cols' });
    const col0 = el('div', { class: 'bloque' }, el('h4', { text: 'Carátula' }));
    const grupos = { '': col0 };
    for (const b of BLOQUES) grupos[b.id] = el('div', { class: 'bloque' }, el('h4', { text: `${b.n} · ${b.nombre}` }));
    const labs = el('div', { class: 'bloque especial' }, el('h4', { text: 'Laboratorios interactivos' }));
    const resp = el('div', { class: 'bloque especial' }, el('h4', { text: 'Respaldo para preguntas' }));
    D.laminas.forEach((L) => {
      const n = D.principales.indexOf(L) + 1;
      const b = el('button', { 'data-id': L.id, onclick: () => { cerrarCapas(); D.irA(L.id, { apilar: true }); } },
        [el('span', { class: 'n', text: L.respaldo ? '·' : String(n) }), el('span', { text: L.titulo })]);
      (L.respaldo ? resp : (grupos[L.bloque] || col0)).append(b);
      if (L.lab) labs.append(el('button', { 'data-id': L.id, onclick: () => { cerrarCapas(); D.irA(L.id, { apilar: true }); } },
        [el('span', { class: 'n', text: '◆' }), el('span', { text: L.lab })]));
    });
    // cuatro columnas equilibradas
    const c1 = el('div'), c2 = el('div'), c3 = el('div'), c4 = el('div');
    c1.append(col0, grupos.intro, grupos.teoria);
    c2.append(grupos.diseno);
    c3.append(grupos.resultados, grupos.analisis, grupos.conclusiones);
    c4.append(labs, resp);
    cols.append(c1, c2, c3, c4);
    cont.append(cols);
    menu.append(cont);
    esc.append(menu);

    // ayuda
    const ayuda = el('div', { id: 'ayuda', class: 'capa' });
    ayuda.append(el('button', { class: 'cerrar', text: '×', onclick: () => cerrarCapas() }));
    const teclas = [
      ['→  Espacio', 'Siguiente paso / lámina'], ['←', 'Paso anterior'],
      ['M  Esc', 'Índice de la defensa'], ['S', 'Vista del orador (notas y tiempos)'],
      ['A', 'Presentación narrada automática'], ['C', 'Subtítulos de la narración'],
      ['L', 'Puntero láser'], ['B  .', 'Pantalla en negro (W: en blanco)'],
      ['T', 'Tema claro u oscuro'], ['F', 'Pantalla completa'],
      ['Retroceso', 'Volver después de seguir un enlace'], ['Inicio  Fin', 'Primera y última lámina'],
      ['número + Intro', 'Ir a la lámina con ese número'], ['?', 'Esta ayuda'],
    ];
    ayuda.append(el('div', { class: 'contenido' }, [
      el('h2', { text: 'Atajos de teclado' }),
      el('div', { class: 'teclas' }, teclas.map(([k, d]) => el('div', {}, [
        ...k.split('  ').map((x) => el('kbd', { text: x })), el('span', { text: d }),
      ]))),
      el('p', { class: 'aux', style: 'margin-top:40px', text: 'Los controles dentro de cada lámina (botones, deslizadores, clic sobre la malla) funcionan con el mouse. Un control remoto de presentaciones avanza con Av Pág y retrocede con Re Pág.' }),
    ]));
    esc.append(ayuda);

    // lupa para capturas
    const lupa = el('div', { id: 'lupa', class: 'capa', onclick: () => cerrarCapas() });
    lupa.append(el('div', { class: 'marco' }, el('img', { alt: '' })), el('div', { class: 'pie-lupa' }));
    esc.append(lupa);

    esc.append(el('div', { id: 'apagon' }), el('div', { id: 'puntero' }),
      el('div', { id: 'subtitulos' }), el('div', { id: 'aviso' }));
  }

  // ------------------------------------------------------------------ capas
  function alternarCapa(id) {
    const c = $('#' + id);
    const abrir = !c.classList.contains('visible');
    cerrarCapas();
    if (abrir) {
      c.classList.add('visible');
      if (id === 'menu') {
        for (const b of $$('#menu button[data-id]')) b.classList.toggle('actual', b.getAttribute('data-id') === D.laminas[D.i].id);
      }
    }
  }
  function cerrarCapas() { for (const c of $$('.capa')) c.classList.remove('visible'); }
  D.alternarCapa = alternarCapa;

  let avisoT = null;
  function aviso(txt) {
    const a = $('#aviso');
    a.textContent = txt;
    a.classList.add('visible');
    clearTimeout(avisoT);
    avisoT = setTimeout(() => a.classList.remove('visible'), 1800);
  }
  D.aviso = aviso;

  // ------------------------------------------------------------------ visualizaciones
  function crearViz(L) {
    for (const v of L.viz) {
      if (v.inst) continue;
      const f = fabricas[v.nombre];
      if (!f) { console.warn('Visualización no registrada:', v.nombre); v.inst = {}; continue; }
      try { v.inst = f(v.contenedor, L, D) || {}; } catch (e) { console.error('Error al crear', v.nombre, e); v.inst = {}; }
    }
  }
  function vizLlamar(L, metodo, ...args) {
    for (const v of L.viz) {
      if (v.inst && typeof v.inst[metodo] === 'function') {
        try { v.inst[metodo](...args); } catch (e) { console.error(v.nombre + '.' + metodo, e); }
      }
    }
  }

  // ------------------------------------------------------------------ pasos
  function pasosDe(e) {
    const s = e.getAttribute('data-solo');
    return s ? s.split(',').map(Number) : null;
  }
  function visibleEn(e, p) {
    if (e.hasAttribute('data-paso') && p < Number(e.getAttribute('data-paso'))) return false;
    if (e.hasAttribute('data-hasta') && p > Number(e.getAttribute('data-hasta'))) return false;
    const s = pasosDe(e);
    if (s && !s.includes(p)) return false;
    return true;
  }
  const SEL_PASOS = '[data-paso],[data-hasta],[data-solo]';
  // Lo que aparece (data-paso) reserva su lugar desde el principio: nada salta.
  // Lo que desaparece (data-hasta, data-solo) libera el suyo: display none.
  const transitorio = (e) => e.hasAttribute('data-hasta') || e.hasAttribute('data-solo');
  function ocultarEl(e) { if (transitorio(e)) e.classList.add('nodisp'); EF.ocultar(e); }
  function mostrarEl(e) { e.classList.remove('nodisp'); EF.mostrar(e); }

  /** Deja la lámina en el paso p sin animar. */
  function fijarPaso(L, p) {
    for (const e of $$(SEL_PASOS, L.el)) (visibleEn(e, p) ? mostrarEl : ocultarEl)(e);
    for (const e of $$('[data-clase-paso]', L.el)) {
      for (const par of e.getAttribute('data-clase-paso').split(';')) {
        const [k, c] = par.split(':');
        e.classList.toggle(c.trim(), p >= Number(k));
      }
    }
  }

  /** Transición animada del paso anterior al p (hacia adelante). */
  function animarPaso(L, p) {
    const entrantes = [], salientes = [];
    for (const e of $$(SEL_PASOS, L.el)) {
      const antes = visibleEn(e, p - 1), ahora = visibleEn(e, p);
      if (!antes && ahora) entrantes.push(e);
      else if (antes && !ahora) salientes.push(e);
    }
    // primero se va lo que sale (libera su lugar) y después entra lo nuevo
    const demora = salientes.length ? 200 : 0;
    for (const e of salientes) {
      EF.tween({ dur: demora, cada: (t) => { e.style.opacity = String(1 - t); }, fin: () => ocultarEl(e) });
    }
    entrantes.forEach((e, j) => {
      const r = (e.hasAttribute('data-retraso') ? Number(e.getAttribute('data-retraso')) : j * 120) + demora;
      EF.ocultar(e);
      if (demora) EF.tween({ dur: demora, fin: () => e.classList.remove('nodisp') });
      else e.classList.remove('nodisp');
      EF.aparecer(e, { retraso: r });
    });
    for (const e of $$('[data-clase-paso]', L.el)) {
      for (const par of e.getAttribute('data-clase-paso').split(';')) {
        const [k, c] = par.split(':');
        e.classList.toggle(c.trim(), p >= Number(k));
      }
    }
    for (const e of $$('[data-contar]', L.el)) {
      if (Number(e.getAttribute('data-paso') || 0) === p) EF.contar(e, Number(e.getAttribute('data-contar')), { retraso: 200 });
    }
  }

  function animarEntrada(L) {
    const els = $$('[data-entrada]', L.el).filter((e) => visibleEn(e, D.paso));
    els.sort((a, b) => Number(a.getAttribute('data-entrada')) - Number(b.getAttribute('data-entrada')));
    els.forEach((e, j) => {
      const r = e.hasAttribute('data-retraso') ? Number(e.getAttribute('data-retraso')) : 150 + j * 110;
      EF.ocultar(e);
      EF.aparecer(e, { retraso: r });
    });
    for (const e of $$('[data-contar]', L.el)) {
      if (visibleEn(e, D.paso) && !e.hasAttribute('data-paso')) EF.contar(e, Number(e.getAttribute('data-contar')), { retraso: 300 });
      else if (visibleEn(e, D.paso)) e.textContent = EF.fmt(Number(e.getAttribute('data-contar')), Number(e.getAttribute('data-dec') || 0)) + (e.getAttribute('data-sufijo') || '');
    }
  }

  // ------------------------------------------------------------------ navegación
  let transicion = null;
  function mostrarLamina(i, paso, op) {
    op = op || {};
    const anterior = D.laminas[D.i];
    const L = D.laminas[i];
    if (!L) return;
    const dir = op.dir || (i >= D.i ? 1 : -1);
    if (anterior && anterior !== L) {
      vizLlamar(anterior, 'salir');
      const a = anterior.el;
      a.classList.remove('activa');
      a.classList.add('saliente');
      if (transicion) transicion.cancelar(true);
      const t = EF.tween({
        dur: op.instantaneo ? 0 : 280, curva: 'sale',
        cada: (e) => { a.style.opacity = String(1 - e); },
        fin: () => { a.classList.remove('saliente'); a.style.opacity = ''; a.style.transform = ''; },
      });
      transicion = t;
    }
    D.i = i;
    D.paso = EF.clamp(paso || 0, 0, L.pasos);
    crearViz(L);
    fijarPaso(L, D.paso);
    L.el.classList.add('activa');
    const nueva = !L.visitada;
    L.visitada = true;
    if (op.instantaneo || anterior === L) {
      L.el.style.opacity = '';
      L.el.style.transform = '';
    } else {
      L.el.style.opacity = '0';
      EF.tween({
        dur: PPT ? 420 : 560, retraso: 120, curva: 'salePlus',
        cada: (e) => {
          L.el.style.opacity = String(e);
          // versión PowerPoint: transición «Desvanecer», sin desplazamiento
          L.el.style.transform = PPT ? '' : `translateX(${dir * 46 * (1 - e)}px)`;
        },
        fin: () => { L.el.style.opacity = ''; L.el.style.transform = ''; },
      });
      animarEntrada(L);
    }
    vizLlamar(L, 'entrar', D.paso, { instantaneo: !!op.instantaneo, nueva, dir });
    actualizarCromo();
    notificar();
  }

  D.ir = function (i, paso, op) {
    i = EF.clamp(i, 0, D.laminas.length - 1);
    if (i === D.i && paso != null && paso !== D.paso) { D.irPaso(paso); return; }
    mostrarLamina(i, paso, op);
  };
  D.irPaso = function (p) {
    const L = D.laminas[D.i];
    p = EF.clamp(p, 0, L.pasos);
    if (p === D.paso) return;
    if (p === D.paso + 1) {
      D.paso = p;
      animarPaso(L, p);
      vizLlamar(L, 'paso', p, { adelante: true });
    } else {
      D.paso = p;
      fijarPaso(L, p);
      vizLlamar(L, 'paso', p, { adelante: false, salto: true });
    }
    actualizarCromo();
    notificar();
  };
  D.siguiente = function () {
    const L = D.laminas[D.i];
    if (D.paso < L.pasos) { D.irPaso(D.paso + 1); return true; }
    // no se pasa del cierre al respaldo por accidente
    const sig = D.i + 1;
    if (sig >= D.laminas.length || (D.laminas[sig].respaldo && !L.respaldo)) { aviso('Fin de la presentación'); return false; }
    mostrarLamina(sig, 0, { dir: 1 });
    return true;
  };
  D.anterior = function () {
    const L = D.laminas[D.i];
    if (D.paso > 0) { D.irPaso(D.paso - 1); return; }
    if (D.i === 0) return;
    const prev = D.laminas[D.i - 1];
    mostrarLamina(D.i - 1, prev.pasos, { dir: -1 });
  };
  /** Ir a una lámina por id. apilar: recordar desde dónde para el botón «Volver». */
  D.irA = function (id, op) {
    op = op || {};
    const L = D.porId[id];
    if (!L) { console.warn('No existe la lámina', id); return; }
    if (op.apilar && D.i >= 0 && L.k !== D.i) D.historial.push({ i: D.i, paso: D.paso });
    mostrarLamina(L.k, op.paso != null ? op.paso : (op.final ? L.pasos : 0), { dir: L.k >= D.i ? 1 : -1 });
  };
  D.volver = function () {
    const h = D.historial.pop();
    if (h) mostrarLamina(h.i, h.paso, { dir: -1 });
  };

  function actualizarCromo() {
    const L = D.laminas[D.i];
    const bi = BLOQUES.findIndex((b) => b.id === L.bloque);
    for (const b of $$('#pie .hilo button')) {
      const k = BLOQUES.findIndex((x) => x.id === b.getAttribute('data-bloque'));
      b.classList.toggle('actual', k === bi);
      b.classList.toggle('hecho', bi >= 0 && k < bi);
    }
    const n = D.principales.indexOf(L);
    const total = D.principales.length;
    $('#pie .contador').textContent = L.respaldo ? 'Respaldo' : `${n + 1} / ${total}`;
    const frac = L.respaldo ? 1 : (n + (L.pasos ? D.paso / (L.pasos + 1) : 0)) / Math.max(1, total - 1);
    $('#pie .progreso > i').style.width = `${EF.clamp(frac, 0, 1) * 100}%`;
    const v = $('#volver');
    const h = D.historial[D.historial.length - 1];
    v.classList.toggle('visible', !!h);
    $('#pie').classList.toggle('con-volver', !!h);
    if (h) $('.txt', v).textContent = 'Volver a «' + recortar(D.laminas[h.i].titulo, 26) + '»';
    $('#pie').style.display = L.el.hasAttribute('data-sin-pie') ? 'none' : '';
    if (!MODO_CAPTURA && !MODO_IMPRESION) {
      try { history.replaceState(null, '', `#/${L.id}${D.paso ? '/' + D.paso : ''}`); } catch (e) { /* file:// sin historial */ }
    }
    document.title = `${n + 1}. ${L.titulo} — Defensa EduFEM`;
  }
  function recortar(s, n) { return s.length > n ? s.slice(0, n - 1) + '…' : s; }

  const oyentes = [];
  D.alCambiar = (fn) => oyentes.push(fn);
  function notificar() {
    const L = D.laminas[D.i];
    for (const fn of oyentes) { try { fn(L, D.paso); } catch (e) { console.error(e); } }
  }

  // ------------------------------------------------------------------ teclado, ratón, toque
  let numeroTecleado = '';
  function teclado(ev) {
    if (ev.target && /INPUT|TEXTAREA|SELECT/.test(ev.target.tagName) && ev.target.type !== 'range') return;
    const k = ev.key;
    const capaAbierta = $$('.capa.visible').length > 0;
    if (k === 'Escape') {
      if (capaAbierta) cerrarCapas(); else alternarCapa('menu');
      ev.preventDefault(); return;
    }
    if (capaAbierta && !['m', 'M', '?', 'h', 'H'].includes(k)) {
      if (['ArrowRight', 'ArrowLeft', ' ', 'PageDown', 'PageUp'].includes(k)) cerrarCapas();
      else return;
    }
    if (/^[0-9]$/.test(k)) { numeroTecleado += k; aviso('Ir a la lámina ' + numeroTecleado + ' … (Intro)'); return; }
    if (k === 'Enter' && numeroTecleado) {
      const n = Number(numeroTecleado); numeroTecleado = '';
      const L = D.principales[n - 1];
      if (L) D.irA(L.id, { apilar: true });
      return;
    }
    numeroTecleado = '';
    switch (k) {
      case 'ArrowRight': case 'ArrowDown': case ' ': case 'PageDown': case 'n': case 'N':
        EF.Narrador.pausarPorUsuario(); D.siguiente(); ev.preventDefault(); break;
      case 'ArrowLeft': case 'ArrowUp': case 'PageUp': case 'p': case 'P':
        EF.Narrador.pausarPorUsuario(); D.anterior(); ev.preventDefault(); break;
      case 'Home': D.ir(0, 0); break;
      case 'End': { const L = D.principales[D.principales.length - 1]; D.irA(L.id); break; }
      case 'Backspace': D.volver(); ev.preventDefault(); break;
      case 'm': case 'M': alternarCapa('menu'); break;
      case '?': case 'h': case 'H': alternarCapa('ayuda'); break;
      case 's': case 'S': EF.Orador.abrir(); break;
      case 'a': case 'A': EF.Narrador.alternar(); break;
      case 'c': case 'C': document.body.classList.toggle('con-subtitulos'); aviso(document.body.classList.contains('con-subtitulos') ? 'Subtítulos activados' : 'Subtítulos desactivados'); break;
      case 't': case 'T': D.alternarTema(); break;
      case 'l': case 'L': document.body.classList.toggle('laser'); break;
      case 'f': case 'F': pantallaCompleta(); break;
      case 'b': case 'B': case '.': alternarApagon(false); break;
      case 'w': case 'W': alternarApagon(true); break;
      default: return;
    }
  }
  function alternarApagon(blanco) {
    const a = $('#apagon');
    const vis = a.classList.contains('visible') && a.classList.contains('blanco') === blanco;
    a.classList.toggle('visible', !vis);
    a.classList.toggle('blanco', blanco);
  }
  function pantallaCompleta() {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen().catch(() => {});
    else document.exitFullscreen();
  }

  function ratonYToque() {
    document.addEventListener('keydown', teclado);
    window.addEventListener('resize', ajustar);
    // puntero láser
    const p = $('#puntero');
    document.addEventListener('mousemove', (ev) => {
      if (!document.body.classList.contains('laser')) return;
      const q = EF.aLocal($('#escenario'), ev.clientX, ev.clientY);
      p.style.left = q.x + 'px'; p.style.top = q.y + 'px';
    });
    // enlaces entre láminas
    document.addEventListener('click', (ev) => {
      const b = ev.target.closest('[data-ir]');
      if (b) { ev.preventDefault(); D.irA(b.getAttribute('data-ir'), { apilar: !b.hasAttribute('data-sin-historial'), paso: b.hasAttribute('data-ir-paso') ? Number(b.getAttribute('data-ir-paso')) : undefined }); return; }
      const z = ev.target.closest('img.zoomable, .zoomable img');
      if (z) {
        const lupa = $('#lupa');
        $('img', lupa).src = z.getAttribute('data-grande') || z.src;
        $('.pie-lupa', lupa).textContent = z.getAttribute('alt') || '';
        cerrarCapas();
        lupa.classList.add('visible');
      }
    });
    // deslizar con el dedo
    let x0 = null;
    document.addEventListener('touchstart', (e) => { x0 = e.touches[0].clientX; }, { passive: true });
    document.addEventListener('touchend', (e) => {
      if (x0 == null) return;
      const dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 60) (dx < 0 ? D.siguiente : D.anterior)();
    });
  }

  // ------------------------------------------------------------------ vista del orador
  EF.Orador = (function () {
    let w = null, t0 = null, tLam = null, intervalo = null;
    function narrTexto(L, paso) {
      const N = window.EDUFEM_NARRACION;
      const l = N && N.laminas && N.laminas[L.id];
      if (l && l.pasos) {
        const p = l.pasos.find((x) => x.paso === paso) || l.pasos[paso];
        if (p) return p.texto;
      }
      const a = $('aside.notas', L.el);
      return a ? a.textContent.trim() : '';
    }
    function mmss(ms) { const s = Math.max(0, Math.round(ms / 1000)); return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`; }
    function html() {
      return `<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Orador — Defensa EduFEM</title>
<style>
body{margin:0;background:#0b1222;color:#eef3fc;font:16px/1.45 'Inter','Segoe UI',sans-serif;display:grid;grid-template-rows:auto 1fr auto;height:100vh}
header{display:flex;gap:24px;align-items:center;padding:14px 22px;border-bottom:1px solid #26344f}
header .reloj{font:800 44px/1 'Inter';font-variant-numeric:tabular-nums;color:#ffb547}
header .lam{flex:1}
header .lam b{font-size:22px;display:block}
header .lam span{color:#8394b2}
main{display:grid;grid-template-columns:1.7fr 1fr;gap:0;overflow:hidden}
.notas{padding:22px 26px;overflow:auto;font-size:25px;line-height:1.5;border-right:1px solid #26344f}
.notas .p{color:#8394b2;font-size:15px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px}
aside{padding:18px 22px;overflow:auto}
aside h4{margin:0 0 8px;color:#ff8a3d;letter-spacing:.12em;text-transform:uppercase;font-size:13px}
.sig{color:#b7c5dd;font-size:17px;margin-bottom:22px}
table{width:100%;border-collapse:collapse;font-size:15px}
td{padding:6px 4px;border-bottom:1px solid #26344f}
td.n{text-align:right;font-variant-numeric:tabular-nums}
tr.act td{color:#ff8a3d;font-weight:700}
footer{display:flex;gap:10px;padding:12px 22px;border-top:1px solid #26344f}
button{font:700 18px 'Inter';padding:10px 20px;border-radius:10px;border:1px solid #33486e;background:#182641;color:#eef3fc;cursor:pointer}
button:hover{border-color:#ff8a3d}
.big{font-size:30px;padding:8px 34px}
</style></head><body>
<header><div class="reloj" id="total">00:00</div><div class="lam"><b id="tit"></b><span id="pos"></span></div><div><div style="color:#8394b2;font-size:13px">EN ESTA LÁMINA</div><div id="enlam" style="font:700 26px Inter;font-variant-numeric:tabular-nums">00:00</div></div></header>
<main><div class="notas"><div class="p" id="pasoTxt"></div><div id="notas"></div></div>
<aside><h4>A continuación</h4><div class="sig" id="sig"></div><h4>Tiempo por bloque (Taller 6)</h4><table id="tabla"></table></aside></main>
<footer><button class="big" id="ant">‹</button><button class="big" id="sigB">›</button><button id="rein">Reiniciar cronómetro</button><span style="flex:1"></span><span style="color:#8394b2;align-self:center">Las teclas ← → también funcionan en esta ventana</span></footer>
</body></html>`;
    }
    const tBloque = {};
    let bloqueActual = null, tBloqueIni = null;
    function actualizar() {
      if (!w || w.closed) return;
      const L = D.laminas[D.i];
      const doc = w.document;
      const n = D.principales.indexOf(L) + 1;
      doc.getElementById('tit').textContent = L.titulo;
      doc.getElementById('pos').textContent = (L.respaldo ? 'Respaldo' : `Lámina ${n} de ${D.principales.length}`) + (L.pasos ? ` · paso ${D.paso + 1} de ${L.pasos + 1}` : '');
      doc.getElementById('pasoTxt').textContent = L.pasos ? `Guion · paso ${D.paso + 1}` : 'Guion';
      doc.getElementById('notas').textContent = narrTexto(L, D.paso) || '(sin notas)';
      let sigTxt = '';
      if (D.paso < L.pasos) sigTxt = `Paso ${D.paso + 2} de esta lámina: ` + (narrTexto(L, D.paso + 1) || '').slice(0, 160) + '…';
      else { const S2 = D.laminas[D.i + 1]; sigTxt = S2 && !S2.respaldo ? 'Lámina: ' + S2.titulo : 'Fin de la presentación'; }
      doc.getElementById('sig').textContent = sigTxt;
      if (L.bloque !== bloqueActual) {
        const ahora = Date.now();
        if (bloqueActual && tBloqueIni) tBloque[bloqueActual] = (tBloque[bloqueActual] || 0) + (ahora - tBloqueIni);
        bloqueActual = L.bloque; tBloqueIni = ahora;
      }
      tLam = Date.now();
      pintarTabla();
    }
    function pintarTabla() {
      if (!w || w.closed) return;
      const filas = BLOQUES.map((b) => {
        let ms = tBloque[b.id] || 0;
        if (b.id === bloqueActual && tBloqueIni) ms += Date.now() - tBloqueIni;
        return `<tr class="${b.id === bloqueActual ? 'act' : ''}"><td>${b.n} ${b.corto}</td><td class="n">${mmss(ms)}</td><td class="n">/ ${String(b.min).padStart(2, '0')}:00</td></tr>`;
      }).join('');
      w.document.getElementById('tabla').innerHTML = filas + `<tr><td><b>Total</b></td><td class="n"><b>${mmss(t0 ? Date.now() - t0 : 0)}</b></td><td class="n">/ 45:00</td></tr>`;
    }
    function abrir() {
      if (w && !w.closed) { w.focus(); return; }
      w = window.open('', 'edufem-orador', 'width=1200,height=760');
      if (!w) { aviso('El navegador bloqueó la ventana del orador'); return; }
      w.document.open(); w.document.write(html()); w.document.close();
      t0 = t0 || Date.now();
      w.document.getElementById('ant').onclick = () => D.anterior();
      w.document.getElementById('sigB').onclick = () => D.siguiente();
      w.document.getElementById('rein').onclick = () => { t0 = Date.now(); for (const k in tBloque) delete tBloque[k]; tBloqueIni = Date.now(); };
      w.document.addEventListener('keydown', teclado);
      clearInterval(intervalo);
      intervalo = setInterval(() => {
        if (!w || w.closed) { clearInterval(intervalo); return; }
        w.document.getElementById('total').textContent = mmss(Date.now() - t0);
        w.document.getElementById('enlam').textContent = mmss(Date.now() - (tLam || Date.now()));
        pintarTabla();
      }, 500);
      actualizar();
    }
    D.alCambiar(() => actualizar());
    return { abrir, actualizar };
  })();

  // ------------------------------------------------------------------ narración automática
  EF.Narrador = (function () {
    let activo = false, audio = null, espera = null, subsT = null;
    function datos(L, paso) {
      const N = window.EDUFEM_NARRACION;
      const l = N && N.laminas && N.laminas[L.id];
      if (!l) return null;
      return l.pasos.find((x) => x.paso === paso) || null;
    }
    function reproducir() {
      clearTimeout(espera);
      if (audio) { audio.pause(); audio = null; }
      if (!activo) return;
      const L = D.laminas[D.i];
      const d = datos(L, D.paso);
      const sub = $('#subtitulos');
      if (!d || !d.audio) {
        sub.classList.remove('visible');
        espera = setTimeout(() => { if (activo && !D.siguiente()) detener(); }, 2500);
        return;
      }
      audio = new Audio('assets/audio/' + d.audio);
      audio.onended = () => { espera = setTimeout(() => { if (activo && !D.siguiente()) detener(); }, 700); };
      audio.onerror = () => { aviso('Falta el audio ' + d.audio); espera = setTimeout(() => { if (activo) D.siguiente(); }, 3000); };
      audio.play().catch(() => aviso('Presione A de nuevo para iniciar el audio'));
      // subtítulos por frase, sincronizados con el audio
      const cues = d.subtitulos || [{ ini: 0, fin: 1e9, texto: d.texto }];
      clearInterval(subsT);
      subsT = setInterval(() => {
        if (!audio) return;
        const t = audio.currentTime;
        const c = cues.find((q) => t >= q.ini && t < q.fin);
        sub.textContent = c ? c.texto : '';
        sub.classList.toggle('visible', !!c);
      }, 120);
    }
    function iniciar() { activo = true; aviso('Presentación narrada · A para detener'); reproducir(); }
    function detener() {
      activo = false; clearTimeout(espera); clearInterval(subsT);
      if (audio) { audio.pause(); audio = null; }
      $('#subtitulos').classList.remove('visible');
    }
    D.alCambiar(() => { if (activo) reproducir(); });
    return {
      alternar() { if (activo) { detener(); aviso('Narración detenida'); } else iniciar(); },
      pausarPorUsuario() { /* navegar a mano no detiene: la narración sigue desde el paso nuevo */ },
      get activo() { return activo; },
      detener,
    };
  })();

  // ------------------------------------------------------------------ impresión (PDF)
  async function prepararImpresion() {
    document.body.classList.add('impresion');
    for (const L of D.laminas) {
      L.el.classList.add('activa');
      D.i = L.k; D.paso = L.pasos;
      crearViz(L);
      fijarPaso(L, L.pasos);
      for (const e of $$('[data-contar]', L.el)) e.textContent = EF.fmt(Number(e.getAttribute('data-contar')), Number(e.getAttribute('data-dec') || 0)) + (e.getAttribute('data-sufijo') || '');
      vizLlamar(L, 'entrar', L.pasos, { instantaneo: true, impresion: true, nueva: true });
      vizLlamar(L, 'final');
    }
  }

  // ------------------------------------------------------------------ captura del video
  function exponerCaptura() {
    window.__deck = {
      laminas: () => D.laminas.map((L) => ({ id: L.id, pasos: L.pasos, respaldo: L.respaldo, titulo: L.titulo, bloque: L.bloque })),
      ir: (id, paso) => { const L = D.porId[id]; mostrarLamina(L.k, paso || 0, { dir: 1 }); },
      siguiente: () => D.siguiente(),
      estado: () => ({ id: D.laminas[D.i].id, paso: D.paso }),
      avanzar: (ms) => EF.captura.avanzar(ms),
      subtitulos: (txt) => { const s = $('#subtitulos'); s.textContent = txt || ''; s.classList.toggle('visible', !!txt); },
    };
  }

  // ------------------------------------------------------------------ arranque
  D.iniciar = async function () {
    if (MODO_CAPTURA) { EF.captura.activar(); document.body.classList.add('captura'); }
    // ?pptx=1: el conversor a PowerPoint necesita ver los botones de navegación de la carátula y el cierre
    if (params.has('pptx')) { document.body.classList.add('pptx'); EF.congelarBucles = 4.5; }
    aplicarTema(temaInicial());
    recolectar();
    numerarRotulos();
    construirCromo();
    EF.renderizarFormulas(document);
    for (const L of D.laminas) fijarPaso(L, 0);
    ajustar();
    ratonYToque();
    try {
      // Los lienzos dibujan texto con Inter: se cargan de antemano todos los pesos y los
      // subconjuntos (latín, griego) para que ningún cuadro salga con una fuente de reemplazo.
      const muestra = 'Aá Ññ σ τ ν ξ η ε Σ 0,5';
      const familia = PPT ? 'Carlito' : 'Inter';   // Carlito: respaldo de Calibri con las mismas métricas
      await Promise.all(['400', '500', '600', '700', '800'].flatMap((w) => [
        document.fonts.load(`${w} 24px ${familia}`, muestra), document.fonts.load(`italic ${w} 24px ${familia}`, muestra),
      ]).map((p) => p.catch(() => null)));
      await document.fonts.ready;
    } catch (e) { /* sin API de fuentes */ }
    if (MODO_IMPRESION) { await prepararImpresion(); window.__listo = true; return; }
    exponerCaptura();
    let inicio = 0, pasoIni = 0;
    const m = location.hash.match(/^#\/([^/]+)(?:\/(\d+))?/);
    if (m && D.porId[m[1]]) { inicio = D.porId[m[1]].k; pasoIni = Number(m[2] || 0); }
    mostrarLamina(inicio, pasoIni, { instantaneo: true });
    if (!MODO_CAPTURA) { const L = D.laminas[D.i]; animarEntrada(L); }
    window.__listo = true;
  };

  document.addEventListener('DOMContentLoaded', () => { D.listo = D.iniciar(); });
})();
