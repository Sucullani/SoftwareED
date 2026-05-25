"""
ProbeTooltip: tooltip flotante para el modo "Consulta interactiva" del
Post-Proceso.

A diferencia del ToolTip generico (gui/widgets/tooltip.py), que se
bindea a un widget con Enter/Leave y muestra texto estatico, este
tooltip:
    - Se posiciona explicitamente via show(sx, sy, lines)
    - Refresca el contenido en cada motion (sin destruir el Toplevel)
    - Auto-flip cerca del borde de la pantalla
    - Soporta lineas con color por linea (titulo, alerta, info)
"""

import tkinter as tk

from config.settings import (
    LABEL_BG, LABEL_FG, FONT_UI_BOLD, FONT_MONO_SMALL,
    PROBE_PIN_COLOR, GAUSS_SNAP_COLOR, PROBE_NODE_SNAP_COLOR,
)


class ProbeTooltip:
    """Tooltip flotante posicionado junto al cursor en el MeshCanvas."""

    OFFSET_X = 14
    OFFSET_Y = 14
    PAD_X = 10
    PAD_Y = 6

    def __init__(self, parent):
        """parent: cualquier widget Tk (tipicamente el canvas o su master)."""
        self.parent = parent
        self._tip = None
        self._labels = []

    # ─── API publica ───────────────────────────────────────────────────────

    def show(self, sx, sy, lines, *, accent="default"):
        """Muestra el tooltip en posicion (sx, sy) screen-relative al parent.

        lines: lista de strings (una por linea visible).
        accent: "default" | "gauss" | "pinned" controla el borde del
            tooltip y el color del titulo (1ra linea).
        """
        if self._tip is None:
            self._build()
        # Reusa el Toplevel y solo actualiza contenido + posicion.
        self._set_lines(lines, accent)
        self._reposition(sx, sy)

    def hide(self):
        """Oculta el tooltip (no destruye el Toplevel para reuso)."""
        if self._tip is not None:
            try:
                self._tip.withdraw()
            except Exception:
                pass

    def destroy(self):
        """Destruye el Toplevel. Llamar al deactivate del overlay."""
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None
            self._labels = []

    # ─── Construccion del Toplevel ─────────────────────────────────────────

    def _build(self):
        tw = tk.Toplevel(self.parent)
        tw.wm_overrideredirect(True)
        try:
            tw.attributes("-topmost", True)
        except tk.TclError:
            pass
        tw.configure(bg=LABEL_BG, highlightthickness=1,
                     highlightbackground="#555")
        # Withdraw mientras no se posiciona, evita parpadeo en (0,0)
        tw.withdraw()
        self._tip = tw
        self._frame = tk.Frame(tw, bg=LABEL_BG)
        self._frame.pack(padx=self.PAD_X, pady=self.PAD_Y)

    def _set_lines(self, lines, accent):
        # Reciclar labels existentes; crear / destruir solo si la cantidad
        # cambia. Evita flicker de re-empaquetado en cada hover.
        n_lines = len(lines)
        # Borrar labels sobrantes
        while len(self._labels) > n_lines:
            lbl = self._labels.pop()
            try:
                lbl.destroy()
            except Exception:
                pass

        # Crear labels faltantes
        while len(self._labels) < n_lines:
            lbl = tk.Label(
                self._frame, text="", bg=LABEL_BG, fg=LABEL_FG,
                font=FONT_MONO_SMALL, anchor="w", justify="left",
            )
            lbl.pack(anchor="w")
            self._labels.append(lbl)

        # Color del titulo segun acento
        accent_fg = {
            "gauss":  GAUSS_SNAP_COLOR,
            "pinned": PROBE_PIN_COLOR,
            "node":   PROBE_NODE_SNAP_COLOR,
            "details": PROBE_PIN_COLOR,
        }.get(accent, "#ffffff")

        # Borde del Toplevel segun acento
        border_color = {
            "gauss":  GAUSS_SNAP_COLOR,
            "pinned": PROBE_PIN_COLOR,
            "node":   PROBE_NODE_SNAP_COLOR,
            "details": PROBE_PIN_COLOR,
        }.get(accent, "#555")
        try:
            self._tip.configure(highlightbackground=border_color)
        except tk.TclError:
            pass

        # Aplicar texto y estilo
        for i, line in enumerate(lines):
            lbl = self._labels[i]
            if i == 0:
                lbl.configure(text=line, font=FONT_UI_BOLD, fg=accent_fg)
            else:
                lbl.configure(text=line, font=FONT_MONO_SMALL, fg=LABEL_FG)

    def _reposition(self, sx, sy):
        if self._tip is None:
            return
        # Convertir sx, sy (relativos al parent) a coords absolutas screen.
        try:
            root_x = self.parent.winfo_rootx() + int(sx) + self.OFFSET_X
            root_y = self.parent.winfo_rooty() + int(sy) + self.OFFSET_Y
        except tk.TclError:
            return

        self._tip.update_idletasks()
        w = self._tip.winfo_reqwidth()
        h = self._tip.winfo_reqheight()

        # Auto-flip si se sale por la derecha / abajo de la pantalla.
        try:
            screen_w = self._tip.winfo_screenwidth()
            screen_h = self._tip.winfo_screenheight()
        except tk.TclError:
            screen_w = screen_h = 99999
        if root_x + w > screen_w - 4:
            root_x = self.parent.winfo_rootx() + int(sx) - w - self.OFFSET_X
        if root_y + h > screen_h - 4:
            root_y = self.parent.winfo_rooty() + int(sy) - h - self.OFFSET_Y

        self._tip.geometry(f"+{root_x}+{root_y}")
        try:
            self._tip.deiconify()
        except tk.TclError:
            pass
