# -*- coding: utf-8 -*-
"""Mapa pagina impresa <-> pagina del PDF, leido del numero impreso en cada pagina.

El desfase NO es constante dentro de un mismo ejemplar (en este libro salta de +16
a +24), asi que no se calcula: se lee. Cada pagina aporta varios numeros candidatos
(encabezado, pie, numero de capitulo) y se elige el que concuerda con sus vecinas,
que es lo unico que distingue el folio real del numero de capitulo.

Requiere PyMuPDF (`pip install pymupdf`), que NO es dependencia de EduFEM: se
retiro del programa el 2026-09-25 por su licencia AGPL-3.0, que obliga al
distribuirlo. Este guion es una herramienta local de la tesis y no se distribuye.
"""
import io, sys, re, collections, fitz

VENTANA = 25          # paginas a cada lado para decidir el desfase dominante


def candidatos(pagina):
    """Numeros que podrian ser el folio: al principio o al final de la primera
    y la ultima linea con texto."""
    lineas = [l.strip() for l in pagina.get_text().splitlines() if l.strip()]
    if not lineas:
        return set()
    fuera = set()
    for linea in {lineas[0], lineas[-1]}:
        for m in (re.match(r'^(\d{1,4})\b', linea), re.search(r'\b(\d{1,4})$', linea)):
            if m:
                n = int(m.group(1))
                if 1 <= n <= 3000:
                    fuera.add(n)
    return fuera


def mapa_impresas(ruta):
    doc = fitz.open(ruta)
    cands = [candidatos(doc[i]) for i in range(doc.page_count)]
    doc.close()

    # desfases posibles por pagina (pdf - impresa)
    desf = [{i + 1 - c for c in cs} for i, cs in enumerate(cands)]
    frec = collections.Counter(d for s in desf for d in s)

    impresa_de = {}
    for i, cs in enumerate(cands):
        if not cs:
            continue
        ini, fin = max(0, i - VENTANA), min(len(desf), i + VENTANA + 1)
        local = collections.Counter(d for s in desf[ini:fin] for d in s)
        # el candidato cuyo desfase se repite mas entre las paginas vecinas
        mejor = max(cs, key=lambda c: (local[i + 1 - c], frec[i + 1 - c]))
        if local[i + 1 - mejor] >= 3:        # exige respaldo de las vecinas
            impresa_de[i + 1] = mejor

    pdf_de = {}
    for pdf, impresa in sorted(impresa_de.items()):
        pdf_de.setdefault(impresa, pdf)

    # Muchas paginas no llevan folio (aperturas de capitulo, laminas). Se rellenan
    # con el desfase de la pagina folidada mas cercana, nunca con uno global.
    if pdf_de:
        conocidas = sorted(pdf_de)
        for impresa in range(1, max(conocidas) + 1):
            if impresa in pdf_de:
                continue
            vecina = min(conocidas, key=lambda k: abs(k - impresa))
            pdf_de[impresa] = impresa + (pdf_de[vecina] - vecina)
    return pdf_de, impresa_de


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    ruta = sys.argv[1]
    pdf_de, impresa_de = mapa_impresas(ruta)
    print('paginas con folio reconocido:', len(impresa_de))
    ant = None
    for pdf in sorted(impresa_de):
        d = pdf - impresa_de[pdf]
        if d != ant:
            print('  desde PDF %-5d (impresa %-5d)  desfase %+d' % (pdf, impresa_de[pdf], d))
            ant = d
    for p in [int(x) for x in sys.argv[2:]]:
        print('  impresa %-5d -> PDF %s' % (p, pdf_de.get(p, 'NO ENCONTRADA')))
