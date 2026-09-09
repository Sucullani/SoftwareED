"""
TheoryViewer: compila un TheoryDoc con pdflatex, renderiza el PDF con
PyMuPDF y muestra las páginas en un Canvas+Scrollbar dentro de un
ttk.Toplevel.

La compilación corre en un thread para no bloquear la UI.

El visor **no es modal** a propósito (se consulta mientras se opera el resto
del programa), y de ahí salen sus tres reglas — ver
`docs/convenciones/memoria-calculo.md` §Visor de PDF:

* la rueda se ata al **Toplevel**, nunca con `bind_all` (que es el bindtag de
  toda la aplicación: la rueda sobre el `MeshCanvas` hacía zoom **y**
  scrolleaba este PDF);
* sin `pdflatex` se abre el **mismo** diálogo con botón de descarga que la
  Memoria de Cálculo (`documento` nombra cuál de los dos se pedía);
* la barra de estado habla de páginas, no del nombre-hash del PDF cacheado.
"""

from __future__ import annotations

import hashlib
import traceback
import threading
import uuid
from pathlib import Path
from typing import Callable, Optional

import tkinter as tk
import ttkbootstrap as ttk
import fitz  # PyMuPDF
from PIL import Image, ImageTk

from config.settings import USER_CONFIG_DIR, THEORY_VIEWER_BG_COLOR
from .theory_builder import TheoryDoc


_PDF_CACHE: dict[str, Path] = {}


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


class TheoryViewer(ttk.Toplevel):
    """Ventana que muestra el PDF de teoría generado con pylatex."""

    def __init__(
        self,
        parent,
        title: str = "Teoría",
        doc_builder: Optional[Callable[[TheoryDoc], None]] = None,
        subtitle: str = "",
        zoom: float = 1.5,
        documento: str = "la teoría en PDF",
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry("900x820")

        self._zoom = zoom
        # Nombre del documento en prosa ("la Teoría MEF"): lo consume el
        # dialogo de pdflatex faltante, que es compartido con la Memoria.
        self._doc_label = documento
        # wraplength: los mensajes de error de LaTeX no entran en una linea y
        # un label sin wrap los recorta justo donde esta la causa.
        self._status = ttk.Label(self, text="Compilando el PDF…", anchor="w",
                                 justify="left", wraplength=860)
        self._status.pack(fill="x", padx=10, pady=(8, 4))

        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._canvas = tk.Canvas(outer, highlightthickness=0,
                                  background=THEORY_VIEWER_BG_COLOR)
        self._sb = ttk.Scrollbar(outer, orient="vertical",
                                  command=self._canvas.yview,
                                  bootstyle="round")
        self._canvas.configure(yscrollcommand=self._sb.set)
        # Scrollbar NO se packea inicial — se muestra solo si hay overflow
        # (ver `_sync_scrollbar_visibility`). Filosofia UX 2026: cero
        # scrollbars visibles cuando no son necesarios.
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = ttk.Frame(self._canvas)
        self._inner_id = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )

        def _on_inner_configure(_evt):
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
            self._sync_scrollbar_visibility()

        self._inner.bind("<Configure>", _on_inner_configure)
        self._canvas.bind("<Configure>",
                           lambda _e: self._sync_scrollbar_visibility())

        # Rueda atada al TOPLEVEL, nunca con `bind_all`: el bindtag del
        # toplevel esta en los bindtags de todos sus descendientes, asi que
        # cubre la ventana entera sin salirse de ella. `bind_all` escribe en
        # el bindtag `all`, que es de TODA la aplicacion — y este visor NO es
        # modal (esta pensado para consultarlo mientras se opera el resto del
        # programa), asi que la rueda sobre el MeshCanvas hacia zoom Y
        # scrolleaba este PDF a la vez; ademas el binding global sobrevivia al
        # cierre de la ventana apuntando a un canvas ya destruido. Es la misma
        # regla que fijo `docs/convenciones/arquitectura.md` para los dialogos.
        self.bind("<MouseWheel>", self._on_wheel)

        self._images: list[ImageTk.PhotoImage] = []

        # Escape cierra, igual que la X del Toplevel. Sin `Return`: no hay
        # accion primaria que dar por Enter en un visor de lectura.
        from gui.dialogs._dialog_helpers import bind_dialog_keys, center_dialog
        bind_dialog_keys(self, on_escape=self.destroy)
        center_dialog(self, parent, clamp_screen=True)

        self._build_and_render(doc_builder, title, subtitle)

    def _on_wheel(self, event):
        try:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            # El canvas puede estar destruyendose (cierre de la ventana con el
            # cursor encima): guard de teardown, no un fallo que reportar.
            pass

    def _sync_scrollbar_visibility(self) -> None:
        """Muestra el scrollbar solo cuando hay overflow vertical."""
        try:
            self.update_idletasks()
            req = self._inner.winfo_reqheight()
            vis = self._canvas.winfo_height()
        except tk.TclError:
            return
        try:
            if req > vis + 1:
                if not self._sb.winfo_ismapped():
                    self._sb.pack(side="right", fill="y", before=self._canvas)
            else:
                if self._sb.winfo_ismapped():
                    self._sb.pack_forget()
        except tk.TclError:
            pass

    # ---------- pipeline ----------
    def _build_and_render(
        self,
        doc_builder: Optional[Callable[[TheoryDoc], None]],
        title: str,
        subtitle: str,
    ) -> None:
        def worker():
            try:
                td = TheoryDoc(title=title, subtitle=subtitle)
                if doc_builder:
                    doc_builder(td)
                key = _hash_doc(td)
                pdf_path = _PDF_CACHE.get(key)
                if pdf_path is None or not pdf_path.exists():
                    pdf_path = self._compile(td, key)
                    _PDF_CACHE[key] = pdf_path
                self.after(0, lambda: self._render_pdf(pdf_path))
            except FileNotFoundError:
                # MISMA causa, MISMA salida que la Memoria de Calculo: el
                # dialogo con boton de descarga. Antes esto era una linea de
                # texto gris en el encabezado de una ventana vacia — el alumno
                # quedaba bloqueado sin ninguna accion a mano, que es
                # justamente lo que ese dialogo existe para evitar.
                self.after(0, self._show_missing_latex)
            except Exception as e:
                traceback.print_exc()
                detail = getattr(e, "log_tail", "") or str(e)
                first = next((ln for ln in str(detail).splitlines() if ln.strip()),
                             str(e))
                msg = ("No se pudo compilar el PDF de teoría. "
                       f"pdflatex informó: {first}")
                self.after(0, lambda: self._status.configure(text=msg))

        threading.Thread(target=worker, daemon=True).start()

    def _show_missing_latex(self) -> None:
        """Falta pdflatex: abre el diálogo con botón de descarga y cierra el
        visor (que no puede mostrar nada) en cuanto el alumno lo cierra."""
        try:
            from gui.dialogs.pdflatex_missing_dialog import (
                show_pdflatex_missing_dialog,
            )
            show_pdflatex_missing_dialog(self, documento=self._doc_label)
        except Exception:
            traceback.print_exc()
            self._status.configure(text=(
                "No se encontró pdflatex: falta la carpeta 'texlive' que "
                "acompaña a EduFEM (reinstalá con el instalador completo o "
                "instalá MiKTeX)."
            ))
            return
        try:
            self.destroy()
        except tk.TclError:
            pass

    def _compile(self, td: TheoryDoc, key: str) -> Path:
        # Cache en el directorio de usuario aislado (~/.edufem), no en el TEMP
        # compartido del sistema: en %TEMP%/C:\Windows\Temp el nombre {key}.pdf
        # es predecible (hash de contenido publico) y otro usuario local podria
        # pre-crearlo. ~/.edufem ya es la convencion del resto de la app.
        tmp_dir = Path(USER_CONFIG_DIR) / "theory_cache"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        out_base = tmp_dir / key
        # compile_to resuelve el compilador (TeX Live embebido → PATH),
        # compila en un temporal con ruta ASCII y mueve el PDF al cache
        # (que sí puede llevar el nombre del usuario con tildes).
        td.compile_to(str(out_base))
        pdf = tmp_dir / f"{key}.pdf"
        if not pdf.exists():
            raise FileNotFoundError(f"No se generó el PDF en {pdf}")
        return pdf

    def _render_pdf(self, pdf_path: Path) -> None:
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            traceback.print_exc()
            self._status.configure(text=f"No se pudo abrir el PDF generado: {e}")
            return

        mat = fitz.Matrix(self._zoom, self._zoom)
        try:
            for page in doc:
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                photo = ImageTk.PhotoImage(img)
                lbl = ttk.Label(self._inner, image=photo)
                lbl.pack(padx=6, pady=6)
                self._images.append(photo)
        finally:
            doc.close()
        # El nombre del archivo es un hash de contenido del cache interno
        # (`a3f2b9c1d4e5f607.pdf`): no le dice NADA al alumno. Lo que le sirve
        # es cuanto tiene para leer y que puede scrollear.
        n = len(self._images)
        self._status.configure(
            text=f"{n} página{'s' if n != 1 else ''} — rueda del mouse "
                 f"para recorrer, Escape para cerrar."
        )

    # ---------- API estática ----------
    @classmethod
    def open(
        cls,
        parent,
        title: str,
        doc_builder: Callable[[TheoryDoc], None],
        subtitle: str = "",
        documento: str = "la teoría en PDF",
    ) -> "TheoryViewer":
        win = cls(parent, title=title, doc_builder=doc_builder,
                  subtitle=subtitle, documento=documento)
        win.lift()
        win.focus_force()
        return win
