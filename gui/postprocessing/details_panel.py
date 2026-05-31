"""
DetailsPanel: panel persistente con valores completos + circulo de Mohr.

Reemplaza al ProbeTooltip en modo "details" del probe (clic derecho).
Diferencias vs el tooltip text-only:
  - Layout dos columnas: 10 valores numericos a la izquierda + circulo de
    Mohr animado a la derecha (matplotlib embebido).
  - Persistente: NO se cierra al mover el cursor (igual que el tooltip
    legacy de details), solo con clic izq fuera, Esc, otro clic derecho
    sobre el mismo punto, o boton X.
  - El Mohr muestra σ1, σ2 sobre el eje σ y el punto (σx, τxy) sobre el
    circulo, con θp anotado. SIN interaccion drag (decision documentada:
    rotar el plano confundia mas que enseñaba en M8 legacy).

Eliminacion de M8: este panel absorbe el contenido pedagogico del modulo
educativo M8 (legacy). El circulo de Mohr describe el estado tensional en
UN PUNTO material, por eso vive aqui, donde se consulta el punto del probe.
Las cruces principales σ1/σ2 (capa overlay del canvas) fueron eliminadas en
2026-05: el contorno + este Mohr ya cubren el estado principal.
"""

from __future__ import annotations

import math
import tkinter as tk
from typing import Optional

import numpy as np
import ttkbootstrap as ttk

# matplotlib se importa dentro de __init__ / _draw_mohr para diferir el costo
# de arranque (~200-300 ms). El modulo se carga solo cuando el usuario abre un
# DetailsPanel por primera vez (clic derecho sobre el canvas del Post-Proceso).

from config.settings import (
    LABEL_BG, LABEL_FG, FONT_UI_BOLD, FONT_MONO_SMALL,
    PROBE_PIN_COLOR, GAUSS_SNAP_COLOR, PROBE_NODE_SNAP_COLOR,
    PRINCIPAL_TENSION_COLOR, PRINCIPAL_COMPRESSION_COLOR,
    MOHR_CIRCLE_COLOR, MOHR_POINT_COLOR, MOHR_AXIS_COLOR,
    MOHR_BG, MOHR_FG, fmt,
)


# Accent → color del header y del borde del Toplevel.
_ACCENT_COLOR = {
    "node":    PROBE_NODE_SNAP_COLOR,
    "gauss":   GAUSS_SNAP_COLOR,
    "details": PROBE_PIN_COLOR,
    "default": "#ffffff",
}


class DetailsPanel(tk.Toplevel):
    """Toplevel borderless con valores + Mohr inset.

    Uso:
        panel = DetailsPanel(parent, target, vals, accent, on_close=...)
        panel.show(sx, sy)        # posiciona y muestra
        panel.hide()              # oculta sin destruir
        panel.destroy()           # libera recursos matplotlib
    """

    WIDTH = 480
    HEIGHT = 320
    OFFSET_X = 14
    OFFSET_Y = 14

    def __init__(self, parent, target, vals, accent="details", on_close=None):
        super().__init__(parent)
        self.parent = parent
        self.target = target
        self.vals = vals
        self.accent = accent
        self._on_close_cb = on_close

        self.wm_overrideredirect(True)
        try:
            self.attributes("-topmost", True)
        except tk.TclError:
            pass

        # Borde fino del color del accent
        border_color = _ACCENT_COLOR.get(accent, "#ffffff")
        self.configure(
            bg=LABEL_BG,
            highlightthickness=1,
            highlightbackground=border_color,
        )
        self.withdraw()  # mantener oculto hasta show()

        self._build_layout()
        # Permitir cierre con Esc dentro del propio Toplevel
        self.bind("<Escape>", self._on_escape)

    # ── API publica ────────────────────────────────────────────────────
    def show(self, sx: int, sy: int):
        """Posiciona junto a (sx, sy) relativo al parent y se muestra.

        Auto-flip a la izquierda/arriba si se sale de la pantalla.
        """
        try:
            root_x = self.parent.winfo_rootx() + int(sx) + self.OFFSET_X
            root_y = self.parent.winfo_rooty() + int(sy) + self.OFFSET_Y
        except tk.TclError:
            return
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        try:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
        except tk.TclError:
            screen_w = screen_h = 99999
        if root_x + w > screen_w - 4:
            root_x = self.parent.winfo_rootx() + int(sx) - w - self.OFFSET_X
        if root_y + h > screen_h - 4:
            root_y = self.parent.winfo_rooty() + int(sy) - h - self.OFFSET_Y
        if root_x < 4:
            root_x = 4
        if root_y < 4:
            root_y = 4
        self.geometry(f"+{root_x}+{root_y}")
        try:
            self.deiconify()
            self.lift()
        except tk.TclError:
            pass

    def hide(self):
        try:
            self.withdraw()
        except tk.TclError:
            pass

    def update_data(self, target, vals):
        """Refresca contenido sin destruir el Toplevel."""
        self.target = target
        self.vals = vals
        self._render_values()
        self._render_mohr()

    # ── Construccion del layout ────────────────────────────────────────
    def _build_layout(self):
        # Header (40 px): icono + texto + boton X
        header = tk.Frame(self, bg=LABEL_BG, height=36)
        header.pack(fill=tk.X, padx=8, pady=(8, 4))
        header.pack_propagate(False)

        accent_fg = _ACCENT_COLOR.get(self.accent, "#ffffff")
        self._title_label = tk.Label(
            header, text=self._header_text(), bg=LABEL_BG, fg=accent_fg,
            font=FONT_UI_BOLD, anchor="w",
        )
        self._title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            header, text="✕", bg=LABEL_BG, fg=LABEL_FG, bd=0,
            activebackground=LABEL_BG, activeforeground=accent_fg,
            font=FONT_UI_BOLD, cursor="hand2",
            command=self._on_close_clicked,
        ).pack(side=tk.RIGHT)

        # Body horizontal: izq valores | der Mohr
        body = tk.Frame(self, bg=LABEL_BG)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # ── Columna izquierda: 10 labels de valores ───────────────────
        left = tk.Frame(body, bg=LABEL_BG, width=200)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left.pack_propagate(False)

        self._value_labels = []
        for _ in range(11):  # 11 lineas max (pos, nat, ux, uy, |U|, sx..VM)
            lbl = tk.Label(
                left, text="", bg=LABEL_BG, fg=LABEL_FG,
                font=FONT_MONO_SMALL, anchor="w", justify="left",
            )
            lbl.pack(anchor="w", pady=0)
            self._value_labels.append(lbl)

        # ── Columna derecha: Mohr inset ───────────────────────────────
        right = tk.Frame(body, bg=LABEL_BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self._fig = Figure(figsize=(2.6, 2.6), dpi=100, facecolor=MOHR_BG)
        self._ax = self._fig.add_subplot(111)
        self._mpl_canvas = FigureCanvasTkAgg(self._fig, master=right)
        self._mpl_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Renderizar contenido inicial
        self._render_values()
        self._render_mohr()

    # ── Render del header ──────────────────────────────────────────────
    def _header_text(self) -> str:
        kind = self.target.get("kind")
        if kind == "node":
            return f"DETALLES — NODO N{self.target['node_id']}"
        if kind == "gauss":
            return f"DETALLES — GAUSS PG#{self.target['gp_idx'] + 1}"
        return f"DETALLES — Elem #{self.target['elem_id']}"

    # ── Render de los valores (col izquierda) ──────────────────────────
    def _render_values(self):
        accent_fg = _ACCENT_COLOR.get(self.accent, "#ffffff")
        self._title_label.configure(text=self._header_text(), fg=accent_fg)

        vals = self.vals
        t = self.target
        ux = vals.get("ux", 0.0)
        uy = vals.get("uy", 0.0)
        umag = math.hypot(ux, uy)
        lines = [
            (f"Pos:  ({t['world_x']:.3f}, {t['world_y']:.3f})", LABEL_FG),
            (f"Nat:  ξ={t['xi']:+.3f}  η={t['eta']:+.3f}", "#aaaaaa"),
            ("", LABEL_FG),
            (f"ux  = {fmt(ux, 'displacement')}", LABEL_FG),
            (f"uy  = {fmt(uy, 'displacement')}", LABEL_FG),
            (f"|U| = {fmt(umag, 'displacement')}", LABEL_FG),
            ("", LABEL_FG),
            (f"σx  = {fmt(vals['sigma_x'], 'stress')}", LABEL_FG),
            (f"σy  = {fmt(vals['sigma_y'], 'stress')}", LABEL_FG),
            (f"τxy = {fmt(vals['tau_xy'], 'stress')}", LABEL_FG),
            (f"VM  = {fmt(vals['von_mises'], 'stress')}", accent_fg),
        ]
        for i, lbl in enumerate(self._value_labels):
            if i < len(lines):
                text, color = lines[i]
                lbl.configure(text=text, fg=color)
            else:
                lbl.configure(text="")

    # ── Render del Mohr (col derecha) ──────────────────────────────────
    def _render_mohr(self):
        vals = self.vals
        sx = vals["sigma_x"]
        sy = vals["sigma_y"]
        txy = vals["tau_xy"]
        sigma_avg = 0.5 * (sx + sy)
        R = math.hypot(0.5 * (sx - sy), txy)
        s1 = sigma_avg + R
        s2 = sigma_avg - R
        if abs(sx - sy) + abs(txy) > 1e-12:
            theta_p_rad = 0.5 * math.atan2(2 * txy, sx - sy)
        else:
            theta_p_rad = 0.0
        theta_p_deg = math.degrees(theta_p_rad)

        ax = self._ax
        ax.clear()
        ax.set_facecolor(MOHR_BG)
        ax.tick_params(colors=MOHR_FG, labelsize=7)
        for spine in ax.spines.values():
            spine.set_color(MOHR_FG)
        ax.grid(True, color="#404055", linewidth=0.3, alpha=0.5)

        if R < 1e-12:
            # Estado isotropo (σx=σy, τxy=0): Mohr degenera a un punto
            ax.scatter([sigma_avg], [0], s=50, c=MOHR_POINT_COLOR,
                        edgecolors="white", linewidths=1.0, zorder=5)
            ax.text(0.5, 0.5, "Estado isótropo\n(σ₁ = σ₂)",
                     ha="center", va="center", color=MOHR_FG,
                     fontsize=8, transform=ax.transAxes,
                     bbox=dict(boxstyle="round", facecolor=MOHR_BG,
                                edgecolor=MOHR_FG, alpha=0.7))
            ax.set_aspect("equal", adjustable="datalim")
            self._mpl_canvas.draw_idle()
            return

        # Circulo
        ang = np.linspace(0, 2 * math.pi, 200)
        ax.plot(sigma_avg + R * np.cos(ang), R * np.sin(ang),
                 color=MOHR_CIRCLE_COLOR, lw=1.5)

        # σ1, σ2 sobre el eje σ
        ax.scatter([s1], [0], s=60,
                    c=(PRINCIPAL_TENSION_COLOR if s1 >= 0
                       else PRINCIPAL_COMPRESSION_COLOR),
                    edgecolors="white", linewidths=1.0, zorder=6)
        ax.scatter([s2], [0], s=60,
                    c=(PRINCIPAL_TENSION_COLOR if s2 >= 0
                       else PRINCIPAL_COMPRESSION_COLOR),
                    edgecolors="white", linewidths=1.0, zorder=6)
        ax.annotate("σ₁", (s1, 0), textcoords="offset points",
                     xytext=(6, 5), fontsize=8, fontweight="bold",
                     color=(PRINCIPAL_TENSION_COLOR if s1 >= 0
                            else PRINCIPAL_COMPRESSION_COLOR))
        ax.annotate("σ₂", (s2, 0), textcoords="offset points",
                     xytext=(-14, 5), fontsize=8, fontweight="bold",
                     color=(PRINCIPAL_TENSION_COLOR if s2 >= 0
                            else PRINCIPAL_COMPRESSION_COLOR))

        # (σx, τxy) y (σy, -τxy) sobre el circulo + linea diametral
        ax.scatter([sx], [txy], s=55, c=MOHR_POINT_COLOR,
                    edgecolors="white", linewidths=1.0, zorder=7)
        ax.scatter([sy], [-txy], s=40, c=MOHR_POINT_COLOR,
                    edgecolors="white", linewidths=0.8, zorder=6,
                    alpha=0.7)
        ax.plot([sx, sy], [txy, -txy], color=MOHR_POINT_COLOR,
                 lw=0.8, ls="--", alpha=0.6, zorder=4)
        ax.annotate("(σₓ,τ)", (sx, txy), textcoords="offset points",
                     xytext=(8, 3), fontsize=7, color=MOHR_POINT_COLOR)

        # Ejes σ y τ
        ax.axhline(0, color=MOHR_AXIS_COLOR, lw=0.6, alpha=0.7)
        ax.axvline(0, color=MOHR_AXIS_COLOR, lw=0.6, alpha=0.7)

        ax.set_title(f"θₚ = {theta_p_deg:+.1f}°",
                      color=MOHR_FG, fontsize=9, pad=4)

        # Limites con margen para que las anotaciones no se corten
        margen = R * 0.35 + 1e-9
        x_lo = min(s2, sigma_avg - R) - margen
        x_hi = max(s1, sigma_avg + R) + margen
        ax.set_xlim(x_lo, x_hi)
        ax.set_ylim(-R * 1.5 - 1e-9, R * 1.5 + 1e-9)
        ax.set_aspect("equal", adjustable="box")

        try:
            self._fig.tight_layout(pad=0.3)
        except Exception:
            pass
        self._mpl_canvas.draw_idle()

    # ── Cierre ─────────────────────────────────────────────────────────
    def _on_close_clicked(self):
        if self._on_close_cb is not None:
            try:
                self._on_close_cb()
                return
            except Exception:
                pass
        self.destroy()

    def _on_escape(self, _event=None):
        self._on_close_clicked()

    def destroy(self):
        # Cerrar la figura matplotlib explicitamente para liberar memoria
        try:
            import matplotlib.pyplot as _plt
            _plt.close(self._fig)
        except Exception:
            pass
        super().destroy()
