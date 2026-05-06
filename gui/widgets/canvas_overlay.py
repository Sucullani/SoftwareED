"""
CanvasOverlay — panel flotante draggable sobre el MeshCanvas.

Implementa el "Modo B" de la propuesta UX: en lugar de abrir un Toplevel,
los módulos educativos pueden mostrar su contenido en un panel translúcido
posicionado sobre el canvas compartido. El alumno NO pierde el contexto del
modelo; la "capa educativa" se posa sobre la malla real.

Diseño:
    - El overlay es un ttk.Frame colocado vía place() dentro del frame padre
      (típicamente el MeshCanvas). Esto lo levanta sobre el tk.Canvas sin
      interferir con su redraw.
    - Header con título + botón cerrar; arrastrable haciendo click+drag en
      el header (estilo CAD: panel acoplable que el usuario reposiciona).
    - Body expuesto como `self.body` — los módulos lo pueblan con sus
      controles + visualización.
    - Cierra vía botón × o llamada externa a `close()`. Dispara on_close
      callback para que el módulo limpie sus highlights del canvas.

Uso típico:
    overlay = CanvasOverlay(mesh_canvas, title="② Matriz B",
                            initial_pos=(24, 24), on_close=cleanup_fn)
    ttk.Label(overlay.body, text="...").pack()
    overlay.show()
"""

from __future__ import annotations

from typing import Callable, Optional, Tuple

import tkinter as tk
import ttkbootstrap as ttk

from config.settings import (
    PHASE_PRE_COLOR, PHASE_PROC_COLOR, PHASE_POST_COLOR,
)


# Color de la barra de header según fase del módulo. Coherente con la
# identidad visual de fases que ya usa la GUI principal.
PHASE_BAR_COLORS = {
    "pre":  PHASE_PRE_COLOR,
    "proc": PHASE_PROC_COLOR,
    "post": PHASE_POST_COLOR,
    None:   PHASE_PROC_COLOR,
}

OVERLAY_BG       = "#252535"   # Fondo del body — un pelín más claro que CANVAS_BG
OVERLAY_BORDER   = "#3a3a55"   # Borde sutil
OVERLAY_TITLE_FG = "#ffffff"
OVERLAY_BAR_PADX = 10
OVERLAY_BAR_PADY = 6


class CanvasOverlay(ttk.Frame):
    """Panel flotante draggable que vive sobre el MeshCanvas compartido.

    El parent debe ser un widget Tk (frame) sobre el cual se hará `place()`.
    Para EduFEM el parent natural es la `MeshCanvas` (que es un ttk.Frame
    contenedor), no el `tk.Canvas` interno.

    Args:
        parent: Widget Tk donde se posará el overlay.
        title: Texto del header.
        initial_pos: (x_px, y_px) relativos a la esquina sup-izq del parent.
        on_close: callable() ejecutado al cerrar (limpieza de highlights).
        phase: "pre" / "proc" / "post" — define color de la barra de header.
        closable: Si False, el botón × se omite (caller controla el ciclo).
        width / height: Tamaño fijo en px (None = auto).
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        title: str = "",
        initial_pos: Tuple[int, int] = (24, 24),
        on_close: Optional[Callable[[], None]] = None,
        phase: Optional[str] = None,
        closable: bool = True,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        super().__init__(parent)
        self._parent = parent
        self._on_close = on_close
        self._closable = closable
        self._x, self._y = initial_pos
        self._fixed_size = (width, height)
        self._destroyed = False

        # Borde sutil que define el panel sobre el canvas oscuro.
        self.configure(borderwidth=1, relief="solid")

        # ── Header con barra de color de fase + título + cerrar ───────
        bar_color = PHASE_BAR_COLORS.get(phase, PHASE_BAR_COLORS[None])
        self._header = tk.Frame(self, bg=bar_color, height=28, cursor="fleur")
        self._header.pack(fill="x", side="top")
        self._header.pack_propagate(False)

        self._title_lbl = tk.Label(
            self._header, text=title, bg=bar_color, fg=OVERLAY_TITLE_FG,
            font=("Segoe UI Semibold", 10), padx=OVERLAY_BAR_PADX,
            pady=OVERLAY_BAR_PADY, anchor="w", cursor="fleur",
        )
        self._title_lbl.pack(side="left", fill="x", expand=True)

        if closable:
            # Botón cerrar nativo tk para integrarse con el bg de la barra
            close_btn = tk.Label(
                self._header, text="✕", bg=bar_color, fg=OVERLAY_TITLE_FG,
                font=("Segoe UI", 11, "bold"), padx=10, cursor="hand2",
            )
            close_btn.pack(side="right")
            close_btn.bind("<ButtonPress-1>", lambda _e: self.close())
            close_btn.bind("<Enter>",
                           lambda _e: close_btn.configure(bg="#c0392b"))
            close_btn.bind("<Leave>",
                           lambda _e: close_btn.configure(bg=bar_color))

        # ── Body donde el módulo poblará su contenido ────────────────
        self.body = tk.Frame(self, bg=OVERLAY_BG, padx=8, pady=8,
                              highlightthickness=0,
                              highlightbackground=OVERLAY_BORDER)
        self.body.pack(fill="both", expand=True)

        # ── Drag por header ──────────────────────────────────────────
        for w in (self._header, self._title_lbl):
            w.bind("<ButtonPress-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)

    # ── API pública ────────────────────────────────────────────────
    def show(self) -> None:
        """Muestra el overlay en su posición inicial."""
        kw = {"x": self._x, "y": self._y}
        w, h = self._fixed_size
        if w is not None:
            kw["width"] = w
        if h is not None:
            kw["height"] = h
        self.place(**kw)
        self.lift()

    def set_title(self, text: str) -> None:
        """Actualiza el texto del header sin reconstruir el overlay."""
        try:
            self._title_lbl.configure(text=text)
        except tk.TclError:
            pass

    def close(self) -> None:
        """Cierra el overlay y dispara el callback on_close (una sola vez)."""
        if self._destroyed:
            return
        self._destroyed = True
        cb = self._on_close
        try:
            self.place_forget()
            self.destroy()
        except tk.TclError:
            pass
        if cb is not None:
            try:
                cb()
            except Exception:
                pass

    def reposition(self, x: int, y: int) -> None:
        """Mueve el overlay a coordenadas (x, y) relativas al parent."""
        self._x, self._y = self._clamp(x, y)
        try:
            self.place_configure(x=self._x, y=self._y)
        except tk.TclError:
            pass

    # ── Drag interno ──────────────────────────────────────────────
    def _start_drag(self, event: tk.Event) -> None:
        # Offset del cursor dentro del header en el momento del press.
        self._drag_dx = event.x
        self._drag_dy = event.y

    def _on_drag(self, event: tk.Event) -> None:
        # Calculamos posición nueva en coordenadas del parent:
        #   parent_local_x = event.x_root - parent.x_root
        # Restamos el offset inicial para que el cursor se mantenga sobre
        # el punto del header donde el usuario hizo press.
        try:
            px = self._parent.winfo_rootx()
            py = self._parent.winfo_rooty()
        except tk.TclError:
            return
        nx = event.x_root - px - self._drag_dx
        ny = event.y_root - py - self._drag_dy
        self.reposition(nx, ny)

    def _clamp(self, x: int, y: int) -> Tuple[int, int]:
        """Mantiene el overlay dentro de los límites del parent."""
        try:
            pw = max(1, self._parent.winfo_width())
            ph = max(1, self._parent.winfo_height())
            ow = max(1, self.winfo_width())
            oh = max(1, self.winfo_height())
        except tk.TclError:
            return x, y
        # Permitir overflow del header pero no perder el panel completo.
        x = max(0, min(x, pw - ow))
        y = max(0, min(y, ph - oh))
        return x, y
