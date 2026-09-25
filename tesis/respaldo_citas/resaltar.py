# -*- coding: utf-8 -*-
"""Resalta en amarillo, dentro de cada PDF fuente, los pasajes que respaldan la tesis.

Guarda una copia marcada en tesis/bibliografia/resaltados/ y deja los originales
intactos. Las paginas escaneadas sin capa de texto no se pueden buscar: reciben una
nota amarilla en la esquina.

Lo que no se puede marcar se INFORMA al final. La version anterior de este script
saltaba en silencio las fuentes cuyo archivo no encontraba y los respaldos sin
pagina, y por eso Alvarez y Oberkampf quedaron sin resaltar sin que nadie lo notara.

Requiere PyMuPDF (`pip install pymupdf`), que NO es dependencia de EduFEM: se
retiro del programa el 2026-09-25 por su licencia AGPL-3.0, que obliga al
distribuirlo. Este guion es una herramienta local de la tesis y no se distribuye.
"""
import json, os, io, sys, re, unicodedata, fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

AQUI = os.path.dirname(os.path.abspath(__file__))
BIB = os.path.normpath(os.path.join(AQUI, '..', 'bibliografia'))
DEST = os.path.join(BIB, 'resaltados')
JSON = os.path.join(AQUI, 'verificado.json')       # el versionado, no el temporal

os.makedirs(DEST, exist_ok=True)
datos = json.load(open(JSON, encoding='utf-8'))


def sin_ligaduras(s):
    """'deﬁnitions' -> 'definitions'. PyMuPDF extrae las ligaduras tipograficas
    tal cual y una busqueda literal no las encuentra."""
    return unicodedata.normalize('NFKC', s)


def paginas_de(r):
    """Paginas del PDF donde buscar este respaldo.

    El campo no es un numero: trae rangos y listas ('161-163, 179') y a veces
    prosa ("87 (el numero '83' esta impreso al pie)", '202 (y 215) de 569'). Se
    descarta lo que va entre parentesis -donde viven los folios impresos, que no
    son paginas del PDF- y el total de paginas que sigue a 'de'.
    """
    if r.get('paginas_pdf'):
        return sorted({int(p) for p in r['paginas_pdf']})
    txt = str(r.get('pagina_pdf') or '')
    txt = re.sub(r'\([^)]*\)', ' ', txt)             # aclaraciones entre parentesis
    txt = re.sub(r'\bde\s+\d+', ' ', txt)            # '... de 569' es el total
    fuera = set()
    for m in re.finditer(r'(\d{1,4})\s*[-–]\s*(\d{1,4})', txt):
        a, b = int(m.group(1)), int(m.group(2))
        if b >= a and b - a <= 12:
            fuera.update(range(a, b + 1))
    for m in re.finditer(r'\d{1,4}', txt):
        fuera.add(int(m.group()))
    return sorted(fuera)


def fragmentos(pasaje, largo=58):
    """Trozos buscables: search_for no cruza saltos de linea ni tolera pasajes
    largos, asi que se buscan frases cortas y se resalta cada una que aparezca."""
    txt = re.sub(r'\s+', ' ', sin_ligaduras(str(pasaje or ''))).strip()
    txt = re.sub(r'\[[^\]]{0,30}\]', ' ', txt)          # marcas del extractor
    txt = re.sub(r'\bp\.\s*\d+[-\u2013]?\d*\s*:', ' ', txt)   # prefijos "p.311:"
    txt = txt.replace('//', ' ')
    piezas, actual = [], ''
    for parte in re.split(r'(?<=[.;:,])\s+', txt):
        if len(actual) + len(parte) < largo:
            actual = (actual + ' ' + parte).strip()
        else:
            if len(actual) >= 18:
                piezas.append(actual)
            actual = parte.strip()
    if len(actual) >= 18:
        piezas.append(actual)
    return [p.strip('"\u00ab\u00bb\u201c\u201d ') for p in piezas if len(p) <= 190][:14]


def _palabras(pagina):
    """Palabras de la pagina normalizadas, con su rectangulo."""
    fuera = []
    for x0, y0, x1, y1, w, *_ in pagina.get_text('words'):
        n = re.sub(r'[^0-9a-z]+', '', sin_ligaduras(w).lower())
        if n:
            fuera.append((n, fitz.Rect(x0, y0, x1, y1)))
    return fuera


def buscar_por_palabras(pagina, frag, minimo=6):
    """Rectangulos del tramo mas largo de 'frag' presente en la pagina.

    search_for exige coincidencia literal y falla con las ligaduras tipograficas
    ('deﬁnitions'), los guiones de corte de linea y los saltos de columna. Comparar
    secuencias de palabras normalizadas atraviesa las tres cosas.
    """
    objetivo = [w for w in (re.sub(r'[^0-9a-z]+', '', x) for x in
                            sin_ligaduras(frag).lower().split()) if w]
    if len(objetivo) < minimo:
        return []
    palabras = _palabras(pagina)
    if not palabras:
        return []
    indice = {}
    for i, (w, _) in enumerate(palabras):
        indice.setdefault(w, []).append(i)
    mejor = (0, 0)
    for j, f in enumerate(objetivo):
        for i in indice.get(f, ()):
            k = 0
            while (i + k < len(palabras) and j + k < len(objetivo)
                   and palabras[i + k][0] == objetivo[j + k]):
                k += 1
            if k > mejor[0]:
                mejor = (k, i)
    largo, ini = mejor
    if largo < minimo:
        return []
    return [r for _, r in palabras[ini:ini + largo]]


resumen, avisos = [], []
for d in datos:
    clave = d['clave']
    nombre = d.get('id', {}).get('nombre_archivo_propuesto', '')
    ruta = os.path.join(BIB, nombre)
    if not nombre:
        avisos.append('%s: la ficha no dice que archivo es' % clave)
        continue
    if not os.path.exists(ruta):
        avisos.append('%s: no existe %s' % (clave, nombre))
        continue

    respaldos = [r for r in d.get('respaldos', []) if r.get('pasaje_textual')]
    ausentes = [r for r in d.get('respaldos', [])
                if str(r.get('pagina_impresa', '')).strip().upper().startswith('AUSENTE')]
    utiles = [r for r in respaldos if r not in ausentes]
    if not utiles:
        avisos.append('%s: sin pasajes que marcar (%d declarados AUSENTE)'
                      % (clave, len(ausentes)))
        continue

    doc = fitz.open(ruta)
    marcados, notas, paginas, sin_pagina = 0, 0, set(), 0
    for r in utiles:
        candidatas = [p for p in paginas_de(r) if 1 <= p <= doc.page_count]
        if not candidatas:
            sin_pagina += 1
            continue
        nota = 'Pagina impresa %s. Respalda en la tesis: %s\n\n%s' % (
            str(r.get('pagina_impresa', '?'))[:120],
            str(r.get('afirmacion_tesis', ''))[:300],
            str(r.get('pasaje_textual', ''))[:900])

        hallado = False
        for largo in (58, 30):                     # frases largas, luego trozos
            for num in candidatas:
                pagina = doc[num - 1]
                if not pagina.get_text().strip():
                    continue
                for frag in fragmentos(r['pasaje_textual'], largo):
                    try:
                        rects = pagina.search_for(frag, quads=False)
                    except Exception:
                        rects = []
                    if not rects:
                        rects = buscar_por_palabras(pagina, frag)
                    if rects:
                        anot = pagina.add_highlight_annot(rects)
                        anot.set_colors(stroke=(1, 0.92, 0.35))
                        anot.set_info(content=nota)
                        anot.update()
                        hallado = True
                        paginas.add(num)
            if hallado:
                break

        if hallado:
            marcados += 1
        else:
            # Escaneo sin capa de texto, o pasaje que no calza literalmente: nota
            # amarilla en la esquina para que la pagina no pase inadvertida.
            pagina = doc[candidatas[0] - 1]
            marca = pagina.add_text_annot(
                fitz.Point(pagina.rect.width - 34, 26), nota, icon='Comment')
            marca.set_colors(stroke=(1, 0.86, 0.20))
            marca.update()
            notas += 1
            paginas.add(candidatas[0])

    if marcados or notas:
        # Se escribe aparte y se reemplaza: si el PDF esta abierto en un visor,
        # Windows no deja borrarlo y se perderia el trabajo de toda la fuente.
        destino = os.path.join(DEST, nombre)
        temporal = destino + '.nuevo'
        doc.save(temporal, garbage=3, deflate=True)
        doc.close()
        try:
            os.replace(temporal, destino)
        except OSError:
            avisos.append(
                '%s: no se pudo reemplazar la copia marcada porque el PDF esta '
                'abierto en un visor. La version nueva quedo al lado como '
                '"%s.nuevo": cerra el visor y volve a correr este script, que la '
                'pone en su lugar.' % (clave, nombre))
    else:
        avisos.append('%s: no se pudo marcar nada' % clave)
        doc.close()
    if sin_pagina:
        avisos.append('%s: %d respaldos sin pagina en la ficha' % (clave, sin_pagina))
    resumen.append((clave, len(utiles), marcados, notas, sorted(paginas)))

print('%-30s %6s %6s %6s  %s' % ('CLAVE', 'CITAS', 'RESALT', 'NOTAS', 'PAGINAS PDF'))
tot_c = tot_m = tot_n = 0
for clave, n, m, no, pags in sorted(resumen):
    tot_c += n; tot_m += m; tot_n += no
    print('%-30s %6d %6d %6d  %s' % (clave[:30], n, m, no, str(pags)[:46]))
print('\ntotal: %d pasajes -> %d resaltados + %d notas = %d marcados en %d PDF'
      % (tot_c, tot_m, tot_n, tot_m + tot_n, len(resumen)))
if avisos:
    print('\nSIN MARCAR (revisar):')
    for a in avisos:
        print('  -', a)
print('copias marcadas en:', DEST)
