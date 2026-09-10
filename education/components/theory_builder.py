"""
TheoryDoc: helper sobre pylatex.Document con preámbulo estandarizado y
utilidades para secciones, ecuaciones, matrices y tablas de valores.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from pylatex import (
    Document,
    Section,
    Subsection,
    Command,
    NoEscape,
    Package,
)
from pylatex.utils import escape_latex


class TheoryDoc:
    """Envuelve pylatex.Document con helpers para los módulos educativos."""

    # Por debajo de `RELATIVE_ZERO * max|x|` una entrada es ruido de punto
    # flotante, no un valor: no cuenta para el rango dinamico que decide si
    # una matriz/vector se factoriza o cae a notacion cientifica por entrada.
    # Ver `matrix_factored_tex`.
    RELATIVE_ZERO = 1e-12

    def __init__(self, title: str, subtitle: str = ""):
        geometry_options = {
            "margin": "2.2cm",
            "headheight": "14pt",
        }
        self.doc = Document(
            geometry_options=geometry_options,
            documentclass="article",
            document_options=["11pt", "a4paper"],
        )
        self._packages_added: set[str] = set()
        for pkg in ("amsmath", "amssymb", "amsfonts", "bm",
                    "xcolor", "booktabs", "hyperref"):
            self.doc.preamble.append(Package(pkg))
            self._packages_added.add(pkg)
        self.doc.preamble.append(NoEscape(r"\hypersetup{colorlinks=true, linkcolor=blue!60!black}"))
        self.doc.preamble.append(Command("title", NoEscape(title)))
        if subtitle:
            self.doc.preamble.append(Command("author", NoEscape(subtitle)))
        self.doc.preamble.append(Command("date", NoEscape(r"\today")))
        self.doc.append(NoEscape(r"\maketitle"))

    # ---------- estructura ----------
    # NO llamar `needspace()` desde aca. Se probo: reservar 4 renglones antes
    # de cada `\section`/`\subsection` para que ningun encabezado quede solo
    # al pie cuesta TRES hojas en la Memoria Q4 educativa (16 -> 19) y baja la
    # tinta por hoja del 58 % al 48 %, porque son ~37 encabezados y cada
    # reserva que dispara deja el pie de hoja vacio. Aprovechar la hoja pesa
    # mas que un encabezado viudo ocasional. Si alguna vez se reintenta:
    # medirlo con `medir_memoria.py`, no a ojo.
    def section_numbered(self, title: str) -> None:
        """Seccion numerada automaticamente por LaTeX, aparece en TOC."""
        self.doc.append(NoEscape(rf"\section{{{title}}}"))

    def subsection_numbered(self, title: str) -> None:
        """Subseccion numerada automaticamente (X.Y), aparece en TOC.

        Usar siempre que la subseccion forme parte del flujo principal
        del documento: el numero permite referencias cruzadas estables y
        permite reordenar capitulos sin reescribir titulos.
        """
        self.doc.append(NoEscape(rf"\subsection{{{title}}}"))

    def para(self, text: str) -> None:
        self.doc.append(NoEscape(text))
        self.doc.append(NoEscape(r"\par\medskip"))

    # ---------- ecuaciones ----------
    def equation(self, latex: str) -> None:
        self.doc.append(NoEscape(r"\begin{equation*}"))
        self.doc.append(NoEscape(latex))
        self.doc.append(NoEscape(r"\end{equation*}"))

    # ---------- matrices ----------
    # Convencion de formato: los positivos NO llevan prefijo '+' (solo el '-'
    # de los negativos). La alineacion de columnas la garantiza el entorno
    # bmatrix (cada celda separada por '&' es una columna centrada), no el
    # signo. Ver CLAUDE.md §Memoria de Calculo (formateo numerico).
    @staticmethod
    def matrix_tex(M: np.ndarray, fmt: str = "{:.4g}", name: Optional[str] = None) -> str:
        rows = [" & ".join(fmt.format(x) for x in row) for row in np.asarray(M)]
        body = r" \\ ".join(rows)
        m = rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"
        if name:
            return rf"{name} = {m}"
        return m

    def matrix(self, M: np.ndarray, name: Optional[str] = None, fmt: str = "{:.4g}") -> None:
        self.equation(self.matrix_tex(M, fmt=fmt, name=name))

    # ---------- matrices y vectores con exponente factorizado ----------
    # Tope de decimales del formato factorizado. Por encima, una celda mide
    # mas que en notacion cientifica y conviene cambiar de formato. Medido
    # sobre la k_e 18x18 de Q9 en bloques de 9 columnas: con 6 decimales la
    # celda mas ancha son 9 caracteres y el bloque NO desborda (472 pt
    # disponibles); tampoco desborda con 10.
    _MAX_DECIMALES_FACTORIZADO = 6

    @staticmethod
    def _decidir_formato(A, *, sig_digits, dynamic_range_threshold, tol):
        """Como imprimir `A` sin aplastar a cero ninguna entrada real.

        Devuelve `(modo, p, decimals)`:
          - `("vacia", 0, 0)`   todo por debajo de `tol`.
          - `("factor", p, d)`  exponente comun 10^p y `d` decimales fijos.
          - `("cientifica", 0, sig_digits)` una potencia por entrada.

        El punto es que **ninguna entrada significativa se imprima como
        cero**. `sig_digits=3` fija 2 decimales, con lo que toda entrada por
        debajo del 0,5 % del maximo sale `0.00` — indistinguible de un cero
        estructural. En la k_e 18x18 del Q9 canonico eso eran **64 celdas de
        324, y esa matriz no tiene ni un cero de verdad**; en una K de 16 GDL,
        32 de 256. En un documento que existe para verificar resultados, eso
        no es un redondeo: es un numero equivocado.

        La eleccion:
          1. Los decimales que hagan falta para que la entrada significativa
             mas chica muestre **al menos una cifra**, nunca menos que
             `sig_digits - 1`.
          2. Si eso pasa `_MAX_DECIMALES_FACTORIZADO`, notacion cientifica —
             que nunca miente pero es mas ancha.
          3. Salvo que el llamador haya pedido lo contrario: mientras el
             rango dinamico no pase `dynamic_range_threshold`, se factoriza
             igual con los decimales del tope. Asi la Memoria puede forzar el
             formato factorizado en los vectores globales (pasa 1e12), donde
             la cientifica sencillamente NO entra en la hoja.

        El ruido de punto flotante NO cuenta: un `2.5e-18` al lado de un
        `1.7e-01` es un cero fisico, y tomarlo en serio manda a notacion
        cientifica —el formato mas ancho— justo cuando el ancho es el
        problema. Se mide contra `RELATIVE_ZERO * max`, no contra `tol`.
        """
        A = np.asarray(A, dtype=float)
        abs_A = np.abs(A)
        if not (abs_A > tol).any():
            return "vacia", 0, 0
        max_val = float(abs_A[abs_A > tol].max())
        significativos = abs_A[abs_A > max_val * TheoryDoc.RELATIVE_ZERO]
        min_val = float(significativos.min()) if significativos.size else max_val
        dyn_range = max_val / min_val if min_val > 0 else float("inf")
        p = int(np.floor(np.log10(max_val)))
        norm_min = min_val / (10.0 ** p)
        faltan = int(np.ceil(-np.log10(norm_min))) if 0 < norm_min < 1 else 0
        decimals = max(sig_digits - 1, faltan)
        if decimals > TheoryDoc._MAX_DECIMALES_FACTORIZADO:
            if dyn_range > dynamic_range_threshold:
                return "cientifica", 0, sig_digits
            decimals = TheoryDoc._MAX_DECIMALES_FACTORIZADO
        return "factor", p, decimals

    @staticmethod
    def cell_width(M, *, sig_digits: int = 3,
                   dynamic_range_threshold: float = 1e4,
                   tol: float = 1e-30) -> int:
        """Caracteres que ocupa la celda mas ancha con el formato elegido.

        El formato ya no tiene un ancho fijo: `_decidir_formato` sube los
        decimales cuando hacen falta, y una celda mas ancha entra menos veces
        por renglon. Quien tenga que elegir `max_cols_per_line` (o un ancho
        de bloque) lo pregunta aca en vez de suponer.
        """
        A = np.asarray(M, dtype=float)
        modo, p, dec = TheoryDoc._decidir_formato(
            A, sig_digits=sig_digits,
            dynamic_range_threshold=dynamic_range_threshold, tol=tol)
        if modo == "vacia":
            return 1
        if modo == "cientifica":
            plantilla, vals = f"{{:.{dec}e}}", A
        else:
            plantilla, vals = f"{{:.{dec}f}}", A / (10.0 ** p)
        planos = np.ravel(vals)
        if not planos.size:
            return 1
        return max(len(plantilla.format(float(x))) for x in planos)

    @staticmethod
    def matrix_factored_tex(
        M: np.ndarray,
        *,
        name: Optional[str] = None,
        sig_digits: int = 3,
        dynamic_range_threshold: float = 1e4,
        tol: float = 1e-30,
    ) -> str:
        """LaTeX de M con un exponente comun 10^p factorizado al frente.

        Pensado para resolver overflow horizontal en matrices con valores
        de magnitud uniforme (K, k_e, vectores de fuerza/desplazamiento).

        Si el rango dinamico max(|x|)/min(|x_nonzero|) supera
        `dynamic_range_threshold`, cae al fallback de notacion cientifica
        por entrada (preserva precision).

        Salida tipica:
            name = 10^{p} \\cdot \\begin{bmatrix} ... \\end{bmatrix}
        """
        A = np.asarray(M, dtype=float)
        if A.ndim == 1:
            A = A.reshape(-1, 1)
        modo, p, decimals = TheoryDoc._decidir_formato(
            A, sig_digits=sig_digits,
            dynamic_range_threshold=dynamic_range_threshold, tol=tol)

        if modo == "vacia":
            body = r" \\ ".join(
                " & ".join("0" for _ in row) for row in A
            )
            m = rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"
            return rf"{name} = {m}" if name else m

        # Rango dinamico alto -> notacion cientifica por entrada. Es el
        # formato mas ANCHO, pero es el unico que no aplasta a cero una
        # entrada real. Sin prefijo '+' en positivos (solo '-' en negativos).
        if modo == "cientifica":
            fmt_sci = f"{{:.{decimals}e}}"
            rows = [
                " & ".join(fmt_sci.format(float(x)) for x in row)
                for row in A
            ]
            body = r" \\ ".join(rows)
            m = rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"
            return rf"{name} = {m}" if name else m

        # Factorizacion: 10^p al frente, con los decimales que hagan falta
        # para que la entrada mas chica siga mostrando una cifra.
        norm = A / (10.0 ** p)
        fmt_fixed = f"{{:.{decimals}f}}"
        rows = [
            " & ".join(fmt_fixed.format(float(x)) for x in row)
            for row in norm
        ]
        body = r" \\ ".join(rows)
        bm = rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"
        # Manejo de p == 0 (sin factor visible) y p == 1 (10 explicit).
        if p == 0:
            inner = bm
        else:
            inner = rf"10^{{{p}}} \cdot {bm}"
        return rf"{name} = {inner}" if name else inner

    def matrix_factored(
        self,
        M: np.ndarray,
        *,
        name: Optional[str] = None,
        sig_digits: int = 3,
        dynamic_range_threshold: float = 1e4,
    ) -> None:
        self.equation(self.matrix_factored_tex(
            M, name=name, sig_digits=sig_digits,
            dynamic_range_threshold=dynamic_range_threshold,
        ))

    @staticmethod
    def vector_factored_tex(
        v: np.ndarray,
        *,
        name: Optional[str] = None,
        sig_digits: int = 3,
        dynamic_range_threshold: float = 1e4,
        transpose: bool = True,
        max_cols_per_line: int = 12,
        tol: float = 1e-30,
    ) -> str:
        """LaTeX de un vector con exponente factorizado.

        Si `transpose=True` muestra el vector como fila + `^T` (compacto,
        ideal para u y F: ocupa 1 linea en vez de N). Si es False, lo
        muestra como columna `[bmatrix]` tradicional.

        Si la cantidad de entradas excede `max_cols_per_line` (default 12),
        chunk-ea el vector en multiples filas de esa anchura — necesario
        para vectores Q9 grandes (50+ GDLs) que de otro modo excederian
        el limite `MaxMatrixCols` de amsmath y romperian la compilacion.

        Comparte la logica de factorizacion con `matrix_factored_tex`.
        """
        a = np.asarray(v, dtype=float).reshape(-1)
        n = a.size
        abs_a = np.abs(a)
        mask = abs_a > tol

        def _build_body(entries: list[str]) -> str:
            """Arma el cuerpo del `bmatrix`: una sola fila si `transpose`,
            troceada en varias cuando pasa de `max_cols_per_line`; una
            entrada por fila si no. Devuelve SOLO el cuerpo interno, sin la
            envoltura `\\begin{bmatrix} ... \\end{bmatrix}`."""
            if transpose:
                # Una sola fila si entra; chunkear si no.
                if len(entries) <= max_cols_per_line:
                    return " & ".join(entries)
                # Chunkear en filas de max_cols_per_line. Padding con celdas
                # vacias en la ultima para que pylatex no se queje.
                rows: list[str] = []
                for i in range(0, len(entries), max_cols_per_line):
                    chunk = entries[i:i + max_cols_per_line]
                    if len(chunk) < max_cols_per_line:
                        chunk = chunk + [""] * (max_cols_per_line - len(chunk))
                    rows.append(" & ".join(chunk))
                return r" \\ ".join(rows)
            else:
                # Columna tradicional: una entrada por fila.
                return r" \\ ".join(entries)

        def _wrap(body: str) -> str:
            bm = rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"
            # ^T solo cuando es realmente una fila visualmente (chunkeado o no,
            # mantenemos la convencion de notacion vector-columna).
            if transpose:
                bm = bm + r"^T"
            return bm

        # Misma decision de formato que `matrix_factored_tex` (helper
        # compartido): los decimales salen del rango dinamico real, no de
        # `sig_digits` a secas, para que ninguna entrada se imprima como cero.
        modo, p, decimals = TheoryDoc._decidir_formato(
            a, sig_digits=sig_digits,
            dynamic_range_threshold=dynamic_range_threshold, tol=tol)

        # Caso 1: vector cero.
        if modo == "vacia":
            entries = ["0" for _ in a]
            m = _wrap(_build_body(entries))
            return rf"{name} = {m}" if name else m

        # Caso 2: rango dinamico alto -> notacion cientifica por entrada.
        # Sin prefijo '+' en positivos (solo '-' en negativos).
        if modo == "cientifica":
            fmt_sci = f"{{:.{decimals}e}}"
            entries = [fmt_sci.format(float(x)) for x in a]
            m = _wrap(_build_body(entries))
            return rf"{name} = {m}" if name else m

        # Caso 3: factorizacion comun de 10^p. Sin '+'.
        norm = a / (10.0 ** p)
        fmt_fixed = f"{{:.{decimals}f}}"
        entries = [fmt_fixed.format(float(x)) for x in norm]
        bm = _wrap(_build_body(entries))
        if p == 0:
            inner = bm
        else:
            inner = rf"10^{{{p}}} \cdot {bm}"
        return rf"{name} = {inner}" if name else inner

    def vector_factored(
        self,
        v: np.ndarray,
        *,
        name: Optional[str] = None,
        sig_digits: int = 3,
        dynamic_range_threshold: float = 1e4,
        transpose: bool = True,
        max_cols_per_line: int = 12,
    ) -> None:
        """Ver `vector_factored_tex`. `max_cols_per_line` estaba hardcodeado
        en el helper estatico y el wrapper no lo dejaba pasar: con 12
        columnas en notacion cientifica el vector se sale del papel, y el
        llamador no tenia forma de angostarlo."""
        self.equation(self.vector_factored_tex(
            v, name=name, sig_digits=sig_digits,
            dynamic_range_threshold=dynamic_range_threshold,
            transpose=transpose, max_cols_per_line=max_cols_per_line,
        ))

    # ---------- maquetacion: hoja completa sin sobrepuestos (2026-09-09) ----
    #
    # Tres helpers que la Memoria necesita para aprovechar la hoja A4 sin
    # desbordes ni bloques huerfanos. Son mecanica LaTeX pura: no deciden
    # contenido, solo como entra en la pagina.

    def ensure_layout_macros(self) -> None:
        """Define (idempotente) la macro `\\edufemNeedspace{<alto>}`.

        Reserva vertical: si en la pagina actual no quedan `<alto>` libres,
        salta de pagina ANTES de emitir lo que sigue. Es la implementacion
        clasica de `needspace.sty`, escrita a mano porque ese paquete **no
        esta en el TeX Live embebido** (`vendor/texlive`) y agregarlo obliga
        a rehacer el bundle.

        Cierra con `\\penalty\\@M`, que no esta en el original: sin el, un
        `\\section` que venga inmediatamente despues arranca con `\\addvspace`,
        que BORRA el ultimo skip de la lista — justo el `\\vskip-\\dimen@` que
        compensa al `\\vskip\\dimen@` — y deja el alto reservado como espacio
        en blanco real. Medido: una hoja entera de mas por documento.

        Ojo con el costo: cada reserva que dispara vacia el pie de la hoja.
        Antes de cablearla en algo que se repita muchas veces, medirlo.
        """
        if getattr(self, "_layout_macros_defined", False):
            return
        # Sin `%` de continuacion: el preambulo se emite en UNA linea, asi que
        # un comentario se tragaria el resto de la definicion (`File ended
        # while scanning use of \@argdef`). Los tokens se separan solos.
        self.doc.preamble.append(NoEscape(
            r"\makeatletter"
            r"\newcommand{\edufemNeedspace}[1]{"
            r"\begingroup\setlength{\dimen@}{#1}"
            r"\vskip\z@\@plus\dimen@\penalty-100"
            r"\vskip\z@\@plus-\dimen@\vskip\dimen@\penalty9999"
            r"\vskip-\dimen@\penalty\@M\endgroup}"
            r"\makeatother"
        ))
        self._layout_macros_defined = True

    def needspace(self, height: str = "4cm") -> None:
        """Pide `height` de alto libre; si no queda, salta de pagina."""
        self.ensure_layout_macros()
        self.doc.append(NoEscape(rf"\edufemNeedspace{{{height}}}"))

    def figures_row(self, items, *, caption: str = "", label: str = "",
                    width: float = 0.48) -> None:
        """Fila de figuras lado a lado en UNA sola figura flotante.

        `items` es una lista de `(image_path, subcaption)`. Cada imagen entra
        en un `minipage` de `width\\textwidth` con su `\\subcaption`, de modo
        que dos contornos comparten hoja en vez de ocupar media pagina cada
        uno. `caption` es el pie comun (opcional).

        Requiere `subcaption`, que SI esta en el bundle (viene con `caption`).
        """
        items = [(p, c) for p, c in items if p]
        if not items:
            return
        self.package("graphicx")
        self.package("float")
        self.package("subcaption")
        self.doc.append(NoEscape(r"\begin{figure}[H]\centering"))
        for k, (path, sub) in enumerate(items):
            path_tex = str(path).replace("\\", "/")
            self.doc.append(NoEscape(
                rf"\begin{{subfigure}}[t]{{{width}\textwidth}}\centering"))
            self.doc.append(NoEscape(
                rf"\includegraphics[width=\linewidth]{{{path_tex}}}"))
            if sub:
                self.doc.append(NoEscape(rf"\caption{{{sub}}}"))
            self.doc.append(NoEscape(r"\end{subfigure}"))
            # `%` para que el salto de linea no meta un espacio entre
            # minipages (correria la segunda a la fila siguiente).
            if k % 2 == 0 and k + 1 < len(items):
                self.doc.append(NoEscape(r"\hfill"))
            elif k + 1 < len(items):
                self.doc.append(NoEscape(r"\par\bigskip"))
        if caption:
            self.doc.append(NoEscape(rf"\caption{{{caption}}}"))
        if label:
            self.doc.append(NoEscape(rf"\label{{{label}}}"))
        self.doc.append(NoEscape(r"\end{figure}"))

    def ensure_matrix_cols(self, n: int) -> None:
        """Sube a por lo menos `n` el tope de columnas de `bmatrix`.

        `amsmath` limita las matrices a `MaxMatrixCols` columnas (10 por
        defecto) y pasarse no da un aviso: aborta la compilacion con un
        `Extra alignment tab`, o sea que el documento entero no sale. Es
        idempotente y solo sube el tope, nunca lo baja, asi que el orden en
        que la llamen los distintos emisores de matrices no importa.
        """
        n = int(n)
        if n <= getattr(self, "_max_matrix_cols", 10):
            return
        self._max_matrix_cols = n
        # Al preambulo, no al cuerpo: asi vale para cualquier matriz del
        # documento aunque quien la emita corra despues.
        self.doc.preamble.append(
            NoEscape(rf"\setcounter{{MaxMatrixCols}}{{{n}}}"))

    def matrix_blocks(self, M: np.ndarray, *, name: str,
                      block_cols: int = 9, fmt: str = "{:.4g}",
                      size: str = r"\scriptsize",
                      factored: bool = False, sig_digits: int = 3,
                      dynamic_range_threshold: float = 1e4) -> None:
        """Matriz ancha partida en BLOQUES de columnas, uno debajo del otro.

        Una `B` de 3x18 o una `k_e` de 18x18 (Q9) no entran en A4 portrait ni
        en `\\tiny`, y ponerlas apaisadas gasta una hoja entera. Partidas en
        bloques de `block_cols` columnas entran holgadas y se leen mejor:
        cada bloque rotula el rango de columnas que contiene
        (`k_e [1-9]`), que son los GDL de los primeros nodos.

        Con `factored=True` se factoriza **un exponente comun para toda la
        matriz** (no por bloque: asi los bloques son comparables entre si) y
        las celdas quedan cortas — `5.58` en vez de `5.58e+04`, que es lo
        que hace la diferencia entre entrar y no entrar en la hoja. El
        exponente se repite en la etiqueta de cada bloque para que cada uno
        se lea solo. La cantidad de decimales NO es fija: la elige
        `_decidir_formato` para que ninguna entrada real se imprima como
        cero, y si ni con el tope alcanza, cae a notacion cientifica.

        Si la matriz entra en un solo bloque se emite como matriz normal.
        """
        A = np.asarray(M, dtype=float)
        if A.ndim != 2:
            A = A.reshape(1, -1)
        n_cols = A.shape[1]
        # `block_cols` puede ser un entero (bloques iguales) o una lista de
        # anchos: la B de Q9 se parte en 8 + 10 para que el primer bloque
        # sean los GDL de los 4 nodos de esquina y el segundo los de los 5
        # nodos internos — un corte con sentido fisico, no aritmetico.
        if isinstance(block_cols, (list, tuple)):
            anchos = [int(x) for x in block_cols if int(x) > 0]
        else:
            anchos = None

        prefijo = ""
        if factored:
            # MISMA decision que `matrix_factored_tex` (helper compartido).
            # Antes esta rama normalizaba por 10^p y fijaba `sig_digits-1`
            # decimales sin mirar el rango dinamico, asi que toda entrada por
            # debajo del 0,5 % del maximo se imprimia `0.00`: 64 celdas de 324
            # en la k_e 18x18 del Q9 canonico, que no tiene un solo cero de
            # verdad. Era ademas una regresion — la version apaisada pasaba
            # por `matrix_factored`, que si tiene el guardia.
            modo, p, decimals = TheoryDoc._decidir_formato(
                A, sig_digits=sig_digits,
                dynamic_range_threshold=dynamic_range_threshold, tol=1e-30)
            if modo == "cientifica":
                fmt = f"{{:.{decimals}e}}"
            elif modo == "factor":
                if p != 0:
                    A = A / (10.0 ** p)
                    prefijo = rf"10^{{{p}}} \cdot "
                fmt = f"{{:.{decimals}f}}"
            else:
                fmt = "{:.0f}"

        # Cortes: [(inicio, fin), ...] en indices 0-based.
        if anchos:
            cortes, pos = [], 0
            for ancho in anchos:
                if pos >= n_cols:
                    break
                cortes.append((pos, min(pos + ancho, n_cols)))
                pos += ancho
            if pos < n_cols:
                cortes.append((pos, n_cols))
        else:
            paso = int(block_cols)
            cortes = [(s, min(s + paso, n_cols))
                      for s in range(0, n_cols, paso)]

        # Precondicion explicita: el bloque mas ancho manda. Sin esto, un
        # `block_cols` alto compila o no segun lo que haya declarado otro.
        if cortes:
            self.ensure_matrix_cols(max(b - a for a, b in cortes))
        self.doc.append(NoEscape(r"{" + size))
        if len(cortes) <= 1:
            self.equation(rf"{name} = {prefijo}" + self.matrix_tex(A, fmt=fmt))
        else:
            for start, stop in cortes:
                etiqueta = rf"{name}\,[\,{start + 1}\!-\!{stop}\,] = {prefijo}"
                self.equation(etiqueta
                              + self.matrix_tex(A[:, start:stop], fmt=fmt))
        self.doc.append(NoEscape(r"}"))

    # ---------- paleta de fase (compartida por teaser/box/card/header) ----------
    # Los cuatro colores salen de `config/settings.py` (regla dura 2). Antes
    # eran hex literales escritos aca, con un comentario que se auto-otorgaba
    # una excepcion a esa regla; y `edufemInfo` ni siquiera era espejo de
    # nada: era un color huerfano sin origen en config.
    _PHASE_COLOR_NAME = {
        "pre": "edufemPre",
        "proc": "edufemProc",
        "post": "edufemPost",
        "info": "edufemInfo",
    }

    @staticmethod
    def _hex_tex(color: str) -> str:
        """`#0d6efd` -> `0D6EFD`, que es lo que espera `\\definecolor{HTML}`."""
        return color.lstrip("#").upper()

    def ensure_edu_colors(self) -> None:
        """Define (idempotente) los 4 colores de fase en el preambulo.

        Llamado por educational_box/teaser/chapter_io_card/margin_formula y
        por cualquier consumidor que pinte por fase (p.ej. la barra de fase
        del encabezado de la Memoria)."""
        if getattr(self, "_edu_colors_defined", False):
            return
        from config.settings import (
            PHASE_PRE_COLOR, PHASE_PROC_COLOR, PHASE_POST_COLOR,
            PHASE_INFO_COLOR,
        )
        h = TheoryDoc._hex_tex
        self.doc.preamble.append(NoEscape(
            rf"\definecolor{{edufemPre}}{{HTML}}{{{h(PHASE_PRE_COLOR)}}}"
            rf"\definecolor{{edufemProc}}{{HTML}}{{{h(PHASE_PROC_COLOR)}}}"
            rf"\definecolor{{edufemPost}}{{HTML}}{{{h(PHASE_POST_COLOR)}}}"
            rf"\definecolor{{edufemInfo}}{{HTML}}{{{h(PHASE_INFO_COLOR)}}}"
        ))
        self._edu_colors_defined = True

    def _phase_color(self, phase: str) -> str:
        return self._PHASE_COLOR_NAME.get(phase, "edufemProc")

    # ---------- tarjeta de capitulo "entra -> formula -> sale" ----------
    def chapter_io_card(self, entra: str, formula: str, sale: str,
                        phase: str = "proc") -> None:
        """Tarjeta de 3 celdas ENTRA -> [formula] -> SALE coloreada por fase.

        Reemplaza el parrafo introductorio de cada capitulo: hace explicito
        el flujo de datos del pipeline FEM (que consume y que produce ese
        paso) sin prosa. `entra`/`sale` son LaTeX cortos (math inline OK);
        `formula` es una expresion matematica (sin `$`).
        """
        self.package("tcolorbox", options="most")
        self.ensure_edu_colors()
        col = self._phase_color(phase)
        self.doc.append(NoEscape(
            rf"\begin{{tcolorbox}}[enhanced, colback={col}!5!white, "
            rf"colframe={col}!55!black, boxrule=0.5pt, arc=2pt, "
            rf"left=4pt, right=4pt, top=3pt, bottom=3pt]"
        ))
        self.doc.append(NoEscape(r"\centering\small"))
        self.doc.append(NoEscape(r"\begin{tabular}{c c c}"))
        self.doc.append(NoEscape(
            rf"\textbf{{\textcolor{{{col}!60!black}}{{ENTRA}}}} & & "
            rf"\textbf{{\textcolor{{{col}!60!black}}{{SALE}}}} \\"
        ))
        self.doc.append(NoEscape(
            rf"{entra} & $\;\boldsymbol{{\Rightarrow}}\; {formula} "
            rf"\;\boldsymbol{{\Rightarrow}}\;$ & {sale} \\"
        ))
        self.doc.append(NoEscape(r"\end{tabular}"))
        self.doc.append(NoEscape(r"\end{tcolorbox}"))

    # ---------- formula al margen ----------
    def margin_formula(self, latex: str, phase: str = "proc") -> None:
        """Coloca la formula clave del concepto en el margen (riel hojeable).

        Usa \\marginpar (nativo, sin paquetes extra). Si el margen aprieta,
        degrada visualmente pero no rompe la compilacion."""
        self.ensure_edu_colors()
        col = self._phase_color(phase)
        # \scriptsize + raggedright para caber en el margen estrecho (2.2cm).
        self.doc.append(NoEscape(
            rf"\marginpar{{\scriptsize\raggedright\textcolor{{{col}!70!black}}"
            rf"{{$\displaystyle {latex}$}}}}"
        ))

    # ---------- bloques pedagogicos (educational_box, educational_teaser) ----------
    def educational_teaser(
        self,
        body: str,
        *,
        cross_ref: Optional[str] = None,
        phase: str = "proc",
    ) -> None:
        """Mini-banner pedagogico (1-2 lineas) con una idea clave.

        Caja chica con barra de color de fase a la izquierda. El cuerpo es
        autocontenido: explica el `por que' directamente, sin remitir a otro
        documento. `cross_ref` quedo como parametro opcional por
        compatibilidad — si se pasa, agrega un puntero en italic, pero el
        diseño reformulado (2026-05) NO usa referencias cruzadas circulares.

        Args:
            body: contenido LaTeX de 1-2 lineas. Puede incluir formulas inline.
            cross_ref: opcional. Puntero textual (p.ej. otra seccion). Si es
                       None (recomendado), el teaser se cierra en si mismo.
            phase: "pre" | "proc" | "post" | "info". Controla el color.
        """
        self.package("tcolorbox", options="most")
        self.ensure_edu_colors()
        col = self._phase_color(phase)
        # Caja chica (left bar mas grueso para identidad de fase + padding minimo).
        # Sin titulo: el icono lampara hace de marker visual.
        self.doc.append(NoEscape(
            rf"\begin{{tcolorbox}}[enhanced, colback={col}!4!white, "
            rf"colframe={col}!4!white, leftrule=2.5pt, "
            rf"toprule=0pt, bottomrule=0pt, rightrule=0pt, "
            rf"left=8pt, right=6pt, top=3pt, bottom=3pt, "
            rf"borderline west={{2.5pt}}{{0pt}}{{{col}}}]"
        ))
        # Cuerpo autocontenido. Si se pasa cross_ref (legacy), se agrega un
        # puntero textual en italic; el diseño reformulado lo omite.
        tail = ""
        if cross_ref:
            tail = (rf" \, \emph{{\textcolor{{{col}!70!black}}{{$\rightarrow$ "
                    rf"{cross_ref}}}}}")
        self.doc.append(NoEscape(
            rf"\small \textbf{{\textcolor{{{col}}}{{\textsf{{i}}}}}}\,\, "
            rf"{body}{tail}"
        ))
        self.doc.append(NoEscape(r"\end{tcolorbox}"))

    def educational_box(
        self,
        body: str,
        *,
        title: str = r"\textbf{¿Por qué?}",
        phase: str = "proc",
    ) -> None:
        """Banner pedagogico coloreado por fase del MEF.

        Encapsula la pregunta tipica del alumno "¿por que estamos haciendo
        esto?" en una caja `tcolorbox`. Las fases siguen la paleta del
        proyecto (pre/proc/post de `config.settings`).

        Args:
            body: contenido LaTeX del cuerpo (puede incluir formulas).
            title: titulo de la caja (default "¿Por que?").
            phase: "pre" | "proc" | "post" | "info". Controla el color.
        """
        self.package("tcolorbox", options="most")
        self.ensure_edu_colors()
        col = self._phase_color(phase)
        self.doc.append(NoEscape(
            rf"\begin{{tcolorbox}}[colback={col}!5!white, "
            rf"colframe={col}!75!black, title={{{title}}}, "
            rf"fonttitle=\bfseries\small, boxrule=0.6pt, "
            rf"left=6pt, right=6pt, top=4pt, bottom=4pt]"
        ))
        self.doc.append(NoEscape(body))
        self.doc.append(NoEscape(r"\end{tcolorbox}"))

    # ---------- valores tabulados ----------
    def values(self, rows: list[tuple[str, str]]) -> None:
        self.doc.append(NoEscape(r"\begin{center}\begin{tabular}{ll}\toprule"))
        for k, v in rows:
            self.doc.append(NoEscape(rf"{k} & {v} \\"))
        self.doc.append(NoEscape(r"\bottomrule\end{tabular}\end{center}"))

    def values_2col(self, rows: list) -> None:
        """Ficha de datos en DOS columnas de pares etiqueta/valor.

        `values()` apila los pares en una sola columna y una ficha de 10
        filas se come media hoja. A dos columnas ocupa la mitad de alto y
        deja lugar para que la portada lleve también el mapa del cálculo y
        el diagrama del modelo, en vez de gastar tres hojas al 40 %.

        Se construye con `tabular` + `booktabs`, NUNCA con `tcolorbox`: la
        ficha se emite en los dos estilos y el `directo` tiene prohibidas
        las cajas de color.
        """
        if not rows:
            return
        mitad = (len(rows) + 1) // 2
        izq, der = rows[:mitad], rows[mitad:]
        self.doc.append(NoEscape(
            r"\begin{center}\small"
            r"\begin{tabular}{@{}lr@{\hspace{1.1cm}}lr@{}}\toprule"))
        for i in range(mitad):
            k1, v1 = izq[i]
            if i < len(der):
                k2, v2 = der[i]
                self.doc.append(NoEscape(rf"{k1} & {v1} & {k2} & {v2} \\"))
            else:
                self.doc.append(NoEscape(rf"{k1} & {v1} & & \\"))
        self.doc.append(NoEscape(r"\bottomrule\end{tabular}\end{center}"))

    # ---------- acceso al Document ----------
    def document(self) -> Document:
        return self.doc

    # ---------- extensiones para Memoria de Calculo ----------
    def package(self, name: str, options: Optional[str] = None) -> None:
        """Agrega un paquete LaTeX al preambulo si no fue agregado antes.

        Idempotente: llamadas repetidas con el mismo `name` no duplican la
        entrada en el preambulo (pdflatex acepta duplicados con warning,
        pero conviene mantenerlo limpio).
        """
        if name in self._packages_added:
            return
        if options is not None:
            self.doc.preamble.append(Package(name, options=options))
        else:
            self.doc.preamble.append(Package(name))
        self._packages_added.add(name)

    def raw(self, latex: str) -> None:
        """Inserta LaTeX literal sin escape (escape hatch para chapter,
        appendix, newpage, landscape, etc.)."""
        self.doc.append(NoEscape(latex))

    def toc(self) -> None:
        """Inserta tabla de contenidos seguida de salto de pagina."""
        self.doc.append(NoEscape(r"\tableofcontents"))
        self.doc.append(NoEscape(r"\newpage"))

    def figure(self, image_path: str, caption: str = "", label: str = "",
               width: str = r"0.85\textwidth") -> None:
        """Inserta una figura con caption y label opcionales.

        `image_path` es absoluto o relativo al `workdir` de `compile_to`
        (la Memoria guarda sus figuras en ese directorio y las referencia
        por nombre: asi el .tex no lleva rutas con tildes ni espacios). Se
        normaliza a forward-slash porque pdflatex bajo Windows interpreta
        backslash como inicio de macro.
        """
        self.package("graphicx")
        self.package("float")
        path_tex = image_path.replace("\\", "/")
        self.doc.append(NoEscape(r"\begin{figure}[H]\centering"))
        self.doc.append(NoEscape(rf"\includegraphics[width={width}]{{{path_tex}}}"))
        if caption:
            self.doc.append(NoEscape(rf"\caption{{{caption}}}"))
        if label:
            self.doc.append(NoEscape(rf"\label{{{label}}}"))
        self.doc.append(NoEscape(r"\end{figure}"))

    def compile_to(self, filepath_no_ext: str, *, keep_tex: bool = False,
                   workdir: Optional[str] = None) -> None:
        """Compila el documento a PDF.

        `filepath_no_ext` no debe llevar la extension `.pdf`. El compilador lo
        resuelve `latex_runtime.find_latex_runtime` (TeX Live embebido →
        PATH); si no hay ninguno eleva `FileNotFoundError`, y si pdflatex
        falla, `latex_runtime.LatexCompileError` (con las ultimas lineas del
        log en `.log_tail`).

        `workdir` es el directorio donde se compila; las figuras incluidas
        por ruta relativa (`figure(nombre)`) deben estar ahi. Por defecto se
        usa un temporal con ruta ASCII (TeX Live en Windows no resuelve
        rutas con tildes). El documento usa `\\tableofcontents`, que
        requiere DOS pasadas de pdflatex (la primera escribe el .toc, la
        segunda lo inserta); `compile_document` las hace.
        """
        from .latex_runtime import compile_document

        compile_document(self.doc, filepath_no_ext + ".pdf",
                         workdir=workdir, keep_tex=keep_tex)

    @staticmethod
    def escape(s) -> str:
        """Escapa caracteres especiales LaTeX para strings provenientes
        del modelo (project_name, nombres de material, etc.). NO usar
        sobre formulas o LaTeX literal."""
        if s is None:
            return ""
        return escape_latex(str(s))
