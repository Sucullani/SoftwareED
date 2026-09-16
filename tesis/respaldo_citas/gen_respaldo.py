# -*- coding: utf-8 -*-
"""Genera tesis/respaldo_citas/respaldo_citas.tex desde verificado.json."""
import json, os, io, sys, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DEST = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(DEST)
JSON = os.path.join(DEST, 'verificado.json')      # el versionado, no un temporal

os.makedirs(DEST, exist_ok=True)
datos = json.load(open(JSON, encoding='utf-8'))

# ---------------------------------------------------------------- escapado ---
_MAP = {'\\': r'\textbackslash{}', '{': r'\{', '}': r'\}', '$': r'\$', '&': r'\&',
        '#': r'\#', '^': r'\textasciicircum{}', '_': r'\_', '%': r'\%',
        '~': r'\textasciitilde{}', '<': r'\textless{}', '>': r'\textgreater{}',
        '|': r'\textbar{}',
        # babel-spanish vuelve activa la comilla recta ("a -> a con dieresis), asi
        # que un " suelto del OCR se come la letra siguiente. Hay que neutralizarlo.
        '"': r'\textquotedbl{}'}


# Griegas y simbolos que aparecen en los pasajes: van a modo matematico, nunca
# literales (regla dura 20 del proyecto: un sigma suelto rompe la compilacion).
_MATH = {
    '\u03b1': 'alpha', '\u03b2': 'beta', '\u03b3': 'gamma', '\u03b4': 'delta', '\u03b5': 'varepsilon',
    '\u03b6': 'zeta', '\u03b7': 'eta', '\u03b8': 'theta', '\u03ba': 'kappa', '\u03bb': 'lambda', '\u03bc': 'mu',
    '\u03bd': 'nu', '\u03be': 'xi', '\u03c0': 'pi', '\u03c1': 'rho', '\u03c3': 'sigma', '\u03c4': 'tau',
    '\u03c6': 'phi', '\u03c7': 'chi', '\u03c8': 'psi', '\u03c9': 'omega',
    '\u0393': 'Gamma', '\u0394': 'Delta', '\u0398': 'Theta', '\u039b': 'Lambda', '\u039e': 'Xi', '\u03a0': 'Pi',
    '\u03a3': 'Sigma', '\u03a6': 'Phi', '\u03a8': 'Psi', '\u03a9': 'Omega',
    '\u2264': 'le', '\u2265': 'ge', '\u2260': 'neq', '\u2248': 'approx', '\u2192': 'rightarrow',
    '\u00d7': 'times', '\u00b1': 'pm', '\u2208': 'in', '\u2207': 'nabla', '\u2202': 'partial',
    '\u222b': 'int', '\u221a': 'surd', '\u221e': 'infty', '\u00b7': 'cdot', '\u2212': '-',
}


def tex(s):
    """Escapa texto plano para LaTeX. Los pasajes vienen de OCR: puede haber de todo."""
    if s is None:
        return ''
    s = str(s)
    # normaliza comillas y guiones raros del OCR
    for a, b in [('\u2018', "'"), ('\u2019', "'"), ('\u201c', '``'), ('\u201d', "''"),
                 ('\u2013', '--'), ('\u2014', '---'), ('\ufb01', 'fi'), ('\ufb02', 'fl'),
                 ('\u2026', '...'), ('\u00a0', ' '), ('\ufffd', '?'),
                 ('\u00a9', '(c)'), ('\u00ae', '(R)'), ('\u2122', '(TM)'),
                 ('\u2032', "'"), ('\u2033', "''")]:
        s = s.replace(a, b)
    out = []
    for ch in s:
        if ch in _MAP:
            out.append(_MAP[ch])
        elif ch in _MATH:
            out.append('$\\%s$' % _MATH[ch])
        elif ord(ch) > 0x024F:          # fuera de latin extendido: OCR ilegible
            out.append('?')
        else:
            out.append(ch)
    return ''.join(out)


def corta(s, n):
    s = str(s or '').strip()
    return s if len(s) <= n else s[:n].rsplit(' ', 1)[0] + '...'


ORDEN_GRAV = {'alta': 0, 'media': 1, 'baja': 2, 'ninguna': 3, '': 4}
reales = [d for d in datos if not d['clave'].startswith(('NO_ESTA', 'SIN_BIB'))]
reales.sort(key=lambda d: (ORDEN_GRAV.get(d['id'].get('gravedad', ''), 4), d['clave']))

L = []
A = L.append

A(r'\documentclass[11pt,a4paper]{article}')
A(r'\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}')
A(r'\usepackage[spanish,es-noquoting]{babel}')
A(r'\usepackage[margin=2.3cm]{geometry}')
A(r'\usepackage{longtable,booktabs,array,xcolor,fancyhdr,titlesec,enumitem,hyperref}')
A(r'\usepackage[most]{tcolorbox}')
A(r'\definecolor{resalte}{RGB}{255,243,166}')
A(r'\definecolor{gris}{RGB}{95,95,95}')
A(r'\newtcolorbox{pasaje}{colback=resalte,colframe=resalte!62!black,boxrule=0.3pt,'
  r'left=5pt,right=5pt,top=4pt,bottom=4pt,before skip=4pt,after skip=7pt,breakable}')
A(r'\hypersetup{colorlinks=true,linkcolor=black,urlcolor=black,pdftitle={Respaldo documental de las citas}}')
A(r'\pagestyle{fancy}\fancyhf{}\fancyhead[L]{\small Respaldo documental de las citas}'
  r'\fancyhead[R]{\small\thepage}\renewcommand{\headrulewidth}{0.4pt}')
A(r'\titleformat{\section}{\large\bfseries}{\thesection.}{0.6em}{}')
A(r'\titleformat{\subsection}{\normalsize\bfseries}{}{0em}{}')
A(r'\setlist{nosep,leftmargin=1.4em}')
A(r'\newcommand{\campo}[1]{\textcolor{gris}{\footnotesize #1}}')
A(r'\begin{document}')

A(r'\begin{center}')
A(r'{\LARGE\bfseries Respaldo documental de las citas}\\[3pt]')
A(r'{\large EduFEM --- tesis de grado}\\[8pt]')
A(r'\begin{minipage}{0.86\textwidth}\small')
A(r'Este documento acompaña a la tesis y no forma parte de ella. Registra, para cada fuente '
  r'citada, el ejemplar exactamente consultado, la página donde se encuentra lo que la tesis '
  r'le atribuye y el pasaje textual que lo sostiene. Las citas del cuerpo de la tesis llevan '
  r'localizador de página cuando sostienen una ecuación, un valor numérico, un umbral, una '
  r'definición o una atribución concreta, y van sin localizador cuando son de encuadre (regla '
  r'declarada en la Introducción de la tesis); este documento registra, para todas, la página '
  r'impresa y el pasaje.\\[4pt]')
A(r'Todas las páginas indicadas son \textbf{páginas impresas del ejemplar}, leídas del '
  r'encabezado o del pie de la propia página. No se calcularon por desplazamiento: en varios '
  r'ejemplares el desfase entre la página del visor y la impresa no es constante.')
A(r'\end{minipage}\end{center}')
A(r'\vspace{4pt}\hrule\vspace{10pt}')

# ------------------------------------------------------------- 1. resumen ---
A(r'\section{Estado de las fuentes}')
A(r'\begin{longtable}{@{}p{4.6cm}p{2.1cm}p{1.5cm}p{1.3cm}p{5.4cm}@{}}')
A(r'\toprule \textbf{Fuente} & \textbf{Cotejo} & \textbf{Riesgo} & \textbf{Citas} & '
  r'\textbf{Observación} \\ \midrule \endhead')
for d in reales:
    i = d['id']
    ver = i.get('veredicto', '')
    grav = i.get('gravedad', '')
    obs = 'Coincide con lo declarado.' if ver == 'COINCIDE' else corta(i.get('campos_que_discrepan', ''), 150)
    A('%s & %s & %s & %d & %s \\\\ \\addlinespace[2pt]' % (
        tex(corta(i.get('titulo_real', d['clave']), 58)), tex(ver), tex(grav),
        len(d['respaldos']), tex(obs)))
A(r'\bottomrule\end{longtable}')

# ------------------------------------------------- 2. discrepancias graves ---
graves = [d for d in reales if d['id'].get('gravedad') in ('alta', 'media')]
if graves:
    A(r'\section{Discrepancias entre el ejemplar y lo que declara la bibliografía}')
    A(r'\noindent\small Cada bloque contrasta lo que el archivo \texttt{referencias.bib} '
      r'afirma con lo que está impreso en el ejemplar que se consultó.\par\vspace{6pt}')
    for d in graves:
        i = d['id']
        A(r'\subsection{%s \normalfont\small(\texttt{%s}) --- riesgo %s}' % (
            tex(corta(i.get('titulo_real', ''), 70)), tex(d['clave']), tex(i.get('gravedad'))))
        A(r'\begin{itemize}\small')
        A(r'\item \campo{Ejemplar consultado:} %s%s%s%s%s' % (
            tex(i.get('autores_reales', '')),
            tex('. ' + i['edicion_real']) if i.get('edicion_real') else '',
            tex('. ' + i['editorial_real']) if i.get('editorial_real') else '',
            tex('. ' + i['ciudad_real']) if i.get('ciudad_real') else '',
            tex('. ' + i['anio_real']) if i.get('anio_real') else ''))
        if i.get('isbn_real'):
            A(r'\item \campo{ISBN impreso:} %s' % tex(i['isbn_real']))
        A(r'\item \campo{Difiere en:} %s' % tex(corta(i.get('campos_que_discrepan', ''), 1400)))
        A(r'\end{itemize}')

# ---------------------------------------- 3. afirmaciones sin respaldo ------
A(r'\section{Afirmaciones sin respaldo o con respaldo parcial}')
A(r'\noindent\small Lo que sigue es el resultado más accionable de la revisión: afirmaciones '
  r'de la tesis cuya fuente citada no las sostiene, o las sostiene solo en parte.\par\vspace{6pt}')
hay = False
for d in reales:
    flojos = [r for r in d['respaldos'] if r.get('respalda') in ('NO', 'PARCIAL')]
    nota = str(d.get('sin_respaldo') or '').strip()
    if not flojos and len(nota) < 12:
        continue
    hay = True
    A(r'\subsection{\texttt{%s}}' % tex(d['clave']))
    if flojos:
        A(r'\begin{itemize}\small')
        for r in flojos:
            A(r'\item \textbf{[%s]} %s' % (tex(r.get('respalda')),
                                           tex(corta(r.get('afirmacion_tesis', ''), 330))))
            if r.get('comentario'):
                A(r'\\ \campo{%s}' % tex(corta(r['comentario'], 460)))
        A(r'\end{itemize}')
    if len(nota) >= 12:
        A(r'{\small\campo{Sin respaldo localizable:} %s\par}' % tex(corta(nota, 1500)))
if not hay:
    A(r'\noindent\small Ninguna.')

# ------------------------------------------------ 4. catalogo de respaldos --
A(r'\section{Catálogo de respaldos}')
A(r'\noindent\small Para cada fuente: el ejemplar consultado y, por cada afirmación de la '
  r'tesis, la página impresa y el pasaje que la sostiene.\par\vspace{5pt}')
A(r'\begin{pasaje}\footnotesize\textbf{Nota de vigencia.} Los comentarios de este catálogo se '
  r'redactaron durante la auditoría y describen el estado de la tesis \emph{en ese momento}. '
  r'Varias de las observaciones que mencionan ya fueron aplicadas el 9 de septiembre de 2026: '
  r'las nueve entradas que declaraban una edición distinta de la del ejemplar están corregidas, '
  r'y las citas a Roache 1998, Pérez-Santiago 2023 y Cook 1974 —fuentes de las que no se '
  r'dispone— fueron sustituidas. Donde un comentario diga «el .bib declara» o «DISCREPA», se '
  r'refiere al estado anterior; la sección 1 de este documento refleja el estado vigente.'
  r'\end{pasaje}')
for d in sorted(reales, key=lambda x: x['clave']):
    i = d['id']
    A(r'\subsection{\texttt{%s} --- %s}' % (tex(d['clave']), tex(corta(i.get('titulo_real', ''), 66))))
    A(r'{\footnotesize\campo{Ejemplar:} %s%s%s. \campo{Archivo:} \texttt{%s}\par}\vspace{4pt}' % (
        tex(i.get('autores_reales', '')),
        tex('. ' + i['editorial_real']) if i.get('editorial_real') else '',
        tex('. ' + i['anio_real']) if i.get('anio_real') else '',
        tex(i.get('nombre_archivo_propuesto', ''))))
    if not d['respaldos']:
        A(r'{\small Sin respaldos registrados.\par}')
        continue
    for r in d['respaldos']:
        pag = r.get('pagina_impresa', '') or 'AUSENTE'
        A(r'\vspace{3pt}\noindent{\small\textbf{p.\ %s} \quad \campo{%s}}\par' % (
            tex(corta(pag, 40)), tex(corta(r.get('afirmacion_tesis', ''), 330))))
        pas = corta(r.get('pasaje_textual', ''), 900)
        if pas:
            A(r'\begin{pasaje}\footnotesize %s\end{pasaje}' % tex(pas))
    A(r'\vspace{6pt}')

A(r'\end{document}')

ruta = os.path.join(DEST, 'respaldo_citas.tex')
open(ruta, 'w', encoding='utf-8').write('\n'.join(L))
print('escrito:', ruta, '|', len(L), 'lineas')
