"""
TheoryViewer: compila un TheoryDoc con pdflatex, renderiza el PDF con
PyMuPDF y muestra las páginas en un Canvas+Scrollbar dentro de un
ttk.Toplevel.

La compilación corre en un thread para no bloquear la UI.
"""

from __future__ import annotations

import hashlib
import threading
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
    """Hash del código LaTeX para cachear PDFs."""
    try:
        tex = doc.doc.dumps()
    except Exception:
        tex = ""
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
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry("900x820")

        self._zoom = zoom
        self._status = ttk.Label(self, text="Compilando PDF…", anchor="w")
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

        self._canvas.bind_all("<MouseWheel>", self._on_wheel)

        self._images: list[ImageTk.PhotoImage] = []

        self._build_and_render(doc_builder, title, subtitle)

    def _on_wheel(self, event):
        try:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
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
            except Exception as e:
                msg = f"Error al compilar LaTeX: {e}"
                self.after(0, lambda: self._status.configure(text=msg))

        threading.Thread(target=worker, daemon=True).start()

    def _compile(self, td: TheoryDoc, key: str) -> Path:
        # Cache en el directorio de usuario aislado (~/.edufem), no en el TEMP
        # compartido del sistema: en %TEMP%/C:\Windows\Temp el nombre {key}.pdf
        # es predecible (hash de contenido publico) y otro usuario local podria
        # pre-crearlo. ~/.edufem ya es la convencion del resto de la app.
        tmp_dir = Path(USER_CONFIG_DIR) / "theory_cache"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        out_base = tmp_dir / key
        try:
            td.document().generate_pdf(
                str(out_base),
                clean=False,
                clean_tex=False,
                compiler="pdflatex",
                silent=True,
            )
        except Exception:
            # Windows puede dar PermissionError en el cleanup aunque el PDF
            # se haya generado correctamente.
            pass
        pdf = tmp_dir / f"{key}.pdf"
        if not pdf.exists():
            raise FileNotFoundError(f"No se generó el PDF en {pdf}")
        for ext in ("aux", "log", "out", "toc", "fls", "fdb_latexmk",
                     "synctex.gz", "tex"):
            try:
                (tmp_dir / f"{key}.{ext}").unlink(missing_ok=True)
            except (PermissionError, OSError):
                pass
        return pdf

    def _render_pdf(self, pdf_path: Path) -> None:
        self._status.configure(text=f"Teoría — {pdf_path.name}")
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            self._status.configure(text=f"Error al abrir PDF: {e}")
            return

        mat = fitz.Matrix(self._zoom, self._zoom)
        for page in doc:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            photo = ImageTk.PhotoImage(img)
            lbl = ttk.Label(self._inner, image=photo)
            lbl.pack(padx=6, pady=6)
            self._images.append(photo)
        doc.close()

    # ---------- API estática ----------
    @classmethod
    def open(
        cls,
        parent,
        title: str,
        doc_builder: Callable[[TheoryDoc], None],
        subtitle: str = "",
    ) -> "TheoryViewer":
        win = cls(parent, title=title, doc_builder=doc_builder, subtitle=subtitle)
        win.lift()
        win.focus_force()
        return win
