"""
Teoría en PDF: compila un TheoryDoc con pdflatex y lo abre con el visor de
PDF del sistema, igual que la Memoria de Cálculo (`main_window`,
`os.startfile`).

Hasta el 2026-09-25 el PDF se mostraba en un Toplevel propio que dibujaba
cada página con PyMuPDF. Se retiró porque PyMuPDF se distribuye bajo
AGPL-3.0 (o con licencia comercial): viajaba dentro del instalador y dejaba
el paquete sujeto a esa licencia, contra el MIT de EduFEM. Ninguna de las
bibliotecas que ya usa la app sabe dibujar un PDF (Pillow solo los escribe,
pylatex solo arma el `.tex`), y el visor del sistema da además búsqueda,
zoom e impresión. Ver `docs/convenciones/memoria-calculo.md` §Teoría en PDF.

Tres reglas:

* la compilación (unos 3 s) corre en un hilo, y ese hilo **no toca Tk**:
  deja el resultado en una cola que el hilo principal sondea con `after`
  (`Misc.after` llamado desde otro hilo no es seguro);
* sin `pdflatex` se abre el **mismo** diálogo con botón de descarga que la
  Memoria de Cálculo (`documento` nombra cuál de los dos se pedía);
* el archivo que abre el visor se llama como el documento, no como el hash
  del caché: el visor muestra ese nombre en su barra de título.
"""

from __future__ import annotations

import hashlib
import os
import queue
import re
import threading
import traceback
import uuid
import webbrowser
from pathlib import Path
from tkinter import messagebox
from typing import Callable, Optional

from config.settings import USER_CONFIG_DIR
from .theory_builder import TheoryDoc


# Cada cuánto el hilo principal mira si terminó la compilación.
_SONDEO_MS = 100

# Documentos que se están preparando ahora, por título. Solo lo tocan el
# hilo principal (al pedir el documento y al recibir el resultado), así que
# no necesita candado: un doble clic en el menú no lanza dos pdflatex sobre
# el mismo destino.
_EN_CURSO: set[str] = set()


def _hash_doc(doc: TheoryDoc) -> str:
    """Hash del código LaTeX para cachear PDFs.

    Si `dumps()` falla se devuelve una clave ÚNICA (no la del documento
    vacío): con una clave constante, dos documentos distintos que fallaran
    al serializarse compartirían entrada de caché y el segundo mostraría
    el PDF del primero.
    """
    try:
        tex = doc.doc.dumps()
    except Exception:
        traceback.print_exc()
        return "nohash-" + uuid.uuid4().hex[:10]
    return hashlib.sha256(tex.encode("utf-8", errors="ignore")).hexdigest()[:16]


def pdf_path_for(key: str, title: str) -> Path:
    """Ruta del PDF en el caché: una carpeta por contenido y, adentro, el
    archivo con el nombre del documento.

    La clave va en la carpeta y no en el nombre porque el visor muestra el
    nombre del archivo en su barra de título, y `a3f2b9c1d4e5f607.pdf` no le
    dice nada al alumno. Una carpeta por contenido evita además reescribir un
    PDF que el visor tenga abierto (Acrobat lo bloquea): si el documento
    cambia, el nuevo va a otra carpeta.

    El caché vive en el directorio de usuario aislado (~/.edufem), no en el
    TEMP compartido del sistema: allí el nombre es predecible (hash de
    contenido público) y otro usuario local podría crearlo antes.
    """
    nombre = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title).strip(" .")
    return Path(USER_CONFIG_DIR) / "theory_cache" / key / f"{nombre or 'Teoría'}.pdf"


def build_theory_pdf(
    title: str,
    doc_builder: Optional[Callable[[TheoryDoc], None]] = None,
    subtitle: str = "",
) -> Path:
    """Arma el documento y devuelve su PDF, que solo se compila si no está
    en el caché. No usa Tk: corre en el hilo de trabajo y se prueba sin
    pantalla.

    Eleva `FileNotFoundError` si no hay pdflatex (ni el TeX Live embebido ni
    uno en el PATH) y `latex_runtime.LatexCompileError` si la compilación
    falla.
    """
    td = TheoryDoc(title=title, subtitle=subtitle)
    if doc_builder:
        doc_builder(td)
    pdf = pdf_path_for(_hash_doc(td), title)
    if pdf.exists():
        return pdf
    # compile_to resuelve el compilador (TeX Live embebido → PATH), compila
    # en un temporal con ruta ASCII y mueve el PDF al caché (que sí puede
    # llevar el nombre del usuario con tildes).
    td.compile_to(str(pdf.with_suffix("")))
    if not pdf.exists():
        # RuntimeError y no FileNotFoundError: esa excepción significa «falta
        # pdflatex» y abriría el diálogo de descarga por un fallo que no lo es.
        raise RuntimeError(f"No se generó el PDF en {pdf}")
    return pdf


def _abrir_con_visor(pdf: Path) -> None:
    """Abre el PDF con el programa que el sistema tenga asociado.

    `os.startfile` solo existe en Windows, la plataforma de distribución; en
    las demás (desarrollo) se delega en el navegador. Eleva OSError si
    Windows no tiene ningún programa asociado a los PDF.
    """
    if hasattr(os, "startfile"):
        os.startfile(str(pdf))  # noqa: attr-defined (solo Windows)
    elif not webbrowser.open(pdf.as_uri()):
        raise OSError("no hay un programa para abrir archivos PDF")


def _con_mayuscula(texto: str) -> str:
    return texto[:1].upper() + texto[1:]


def open_theory_pdf(
    parent,
    title: str,
    doc_builder: Optional[Callable[[TheoryDoc], None]] = None,
    subtitle: str = "",
    documento: str = "la teoría en PDF",
    on_status: Optional[Callable[[str], None]] = None,
) -> None:
    """Prepara el documento de teoría y lo abre en el visor de PDF del
    sistema, sin bloquear la interfaz.

    Vuelve enseguida: el visor se abre cuando termina pdflatex (unos 3 s la
    primera vez, y al instante si el PDF ya está en el caché). `on_status`
    recibe los mensajes para la barra de estado de la ventana principal;
    `documento` nombra el PDF en prosa («la Teoría MEF») para esos mensajes y
    para el diálogo de pdflatex faltante, que es compartido con la Memoria.
    """
    estado = on_status or (lambda _mensaje: None)
    if title in _EN_CURSO:
        estado(f"{_con_mayuscula(documento)} se está preparando…")
        return
    _EN_CURSO.add(title)
    estado(f"Preparando {documento}…")
    resultado: queue.Queue = queue.Queue(maxsize=1)

    def worker():
        # Nada de Tk acá: el resultado viaja por la cola.
        try:
            resultado.put(("ok", build_theory_pdf(title, doc_builder, subtitle)))
        except FileNotFoundError:
            resultado.put(("sin_latex", None))
        except Exception as e:
            traceback.print_exc()
            resultado.put(("error", e))

    def sondear():
        try:
            tipo, valor = resultado.get_nowait()
        except queue.Empty:
            try:
                parent.after(_SONDEO_MS, sondear)
            except Exception:
                # La ventana principal se está cerrando: nadie espera ya el PDF.
                _EN_CURSO.discard(title)
            return
        _EN_CURSO.discard(title)
        if tipo == "ok":
            _mostrar(parent, valor, documento, estado)
        elif tipo == "sin_latex":
            estado("")
            _show_missing_latex(parent, documento, estado)
        else:
            _mostrar_error(parent, valor, documento, estado)

    threading.Thread(target=worker, daemon=True).start()
    parent.after(_SONDEO_MS, sondear)


def _mostrar(parent, pdf: Path, documento: str, estado) -> None:
    try:
        _abrir_con_visor(pdf)
    except Exception:
        traceback.print_exc()
        estado(f"No se pudo abrir el PDF. Está en: {pdf}")
        messagebox.showwarning(
            "No se pudo abrir el PDF",
            f"{_con_mayuscula(documento)} está lista, pero Windows no tiene un "
            f"programa asociado a los archivos PDF.\n\n"
            f"El archivo quedó en:\n{pdf}",
            parent=parent,
        )
        return
    estado(f"{_con_mayuscula(documento)} se abrió en el visor de PDF.")


def _mostrar_error(parent, error: Exception, documento: str, estado) -> None:
    # El traceback ya quedó en stderr; al alumno le sirve la causa, que es la
    # primera línea con texto del .log de pdflatex.
    detalle = getattr(error, "log_tail", "") or str(error)
    primera = next((ln for ln in str(detalle).splitlines() if ln.strip()),
                   str(error))
    estado(f"No se pudo compilar {documento}.")
    messagebox.showerror(
        "No se pudo compilar el PDF",
        f"No se pudo compilar {documento}.\n\npdflatex informó: {primera}",
        parent=parent,
    )


def _show_missing_latex(parent, documento: str, estado) -> None:
    """Falta pdflatex: el mismo diálogo con botón de descarga que la Memoria."""
    try:
        from gui.dialogs.pdflatex_missing_dialog import (
            show_pdflatex_missing_dialog,
        )
        show_pdflatex_missing_dialog(parent, documento=documento)
    except Exception:
        traceback.print_exc()
        estado("No se encontró pdflatex: falta la carpeta 'texlive' que "
               "acompaña a EduFEM (reinstalá con el instalador completo o "
               "instalá MiKTeX).")
