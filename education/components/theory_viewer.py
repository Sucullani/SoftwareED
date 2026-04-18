"""
TheoryViewer: compila un TheoryDoc con pdflatex, renderiza el PDF con
PyMuPDF y muestra las páginas en un Canvas+Scrollbar dentro de un
ttk.Toplevel.

La compilación corre en un thread para no bloquear la UI.
"""

from __future__ import annotations

import hashlib
import tempfile
import threading
from pathlib import Path
from typing import Callable, Optional

import tkinter as tk
import ttkbootstrap as ttk
import fitz  # PyMuPDF
from PIL import Image, ImageTk

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
                                  background="#2b2b3c")
        self._sb = ttk.Scrollbar(outer, orient="vertical",
                                  command=self._canvas.yview,
                                  bootstyle="round")
        self._canvas.configure(yscrollcommand=self._sb.set)
        self._sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = ttk.Frame(self._canvas)
        self._inner_id = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )
        self._inner.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )

        self._canvas.bind_all("<MouseWheel>", self._on_wheel)

        self._images: list[ImageTk.PhotoImage] = []

        self._build_and_render(doc_builder, title, subtitle)

    def _on_wheel(self, event):
        try:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
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
        tmp_dir = Path(tempfile.gettempdir()) / "edufem_theory"
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
