"""
GravityDialog: dialogo del menu Modelo > Gravedad.

Ubicado DESPUES de Materiales en la jerarquia FEM porque la gravedad
genera una fuerza volumetrica F = rho * g * V por elemento — depende de
la densidad del material asignado. Por eso conceptualmente es una CARGA,
no una propiedad del sistema de medida.

Layout minimalista (440x260 px) — header + 2 entries + toggle + footer.
Sin Labelframes, sin subtitulo descriptivo, sin labels "(unidad coherente
con el sistema activo)" junto a cada Entry (redundante con el sistema
activo del proyecto), sin boton preset "0, -9.81" (el usuario lo tipea
sin esfuerzo) y sin hint debajo del toggle. La flecha en vivo sobre el
MeshCanvas hace todo el trabajo pedagogico — el dialogo es solo data
entry.

Fields:
  - gx, gy (aceleracion)
  - include_gravity (checkbox toggle)

Mientras el dialogo esta abierto, registra una capa de preview sobre el
MeshCanvas que muestra el vector g como flecha desde el centro del modelo
(o del canvas si el modelo esta vacio). Se actualiza en vivo al cambiar
gx / gy.
"""

import math
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from config.settings import PHASE_PROC_COLOR, TEXT_MUTED_FG


# Constantes del preview sobre el canvas.
_PREVIEW_ARROW_PX   = 70   # longitud del asta en pixels screen
_PREVIEW_HEAD_PX    = 14   # tamaño de la cabeza triangular
_PREVIEW_TAG        = "gravity_preview"


class GravityDialog:
    """Ventana modal para configurar el vector de gravedad (gx, gy)."""

    def __init__(self, parent, project, main_window=None):
        self.project = project
        self.main_window = main_window
        self.parent = parent

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("🌍  Gravedad")
        self.dialog.geometry("440x260")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Estado local (no muta el project hasta Aceptar).
        self.gx_var = tk.StringVar(value=f"{project.gravity_x:.4g}")
        self.gy_var = tk.StringVar(value=f"{project.gravity_y:.4g}")
        self.include_var = tk.BooleanVar(value=project.include_gravity)

        self._preview_layer = None
        self._gx_live = float(project.gravity_x)
        self._gy_live = float(project.gravity_y)

        self._build()
        self._center()

        # Live update del preview en el canvas.
        self.gx_var.trace_add("write", self._on_field_changed)
        self.gy_var.trace_add("write", self._on_field_changed)
        self.include_var.trace_add("write", self._on_field_changed)
        self._register_preview()

    # ─── Layout ─────────────────────────────────────────────────────────
    def _build(self):
        main = ttk.Frame(self.dialog, padding=16)
        main.pack(fill=BOTH, expand=YES)

        ttk.Label(
            main, text="Vector de gravedad",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor=W, pady=(0, 12))

        # ─── Componentes gx, gy (sin Labelframe, sin labels de unidad) ─
        comp = ttk.Frame(main)
        comp.pack(fill=X, pady=(0, 12))
        for row, (label, var) in enumerate((
            ("gx", self.gx_var),
            ("gy", self.gy_var),
        )):
            ttk.Label(comp, text=f"{label}:", font=("Segoe UI", 10)).grid(
                row=row, column=0, sticky=E, padx=(0, 8), pady=3
            )
            ttk.Entry(
                comp, textvariable=var, width=14, font=("Segoe UI", 10),
            ).grid(row=row, column=1, sticky=W, pady=3)

        # ─── Toggle Incluir gravedad (sin Labelframe, sin hint) ─────────
        ttk.Checkbutton(
            main,
            text="Incluir gravedad en el analisis (peso propio)",
            variable=self.include_var,
            bootstyle="info-round-toggle",
        ).pack(anchor=W, pady=(0, 14))

        # ─── Botones ────────────────────────────────────────────────────
        btn_bar = ttk.Frame(main)
        btn_bar.pack(fill=X, side=BOTTOM)
        ttk.Button(
            btn_bar, text="Cancelar", bootstyle="secondary",
            command=self._on_cancel, width=12,
        ).pack(side=RIGHT, padx=4)
        ttk.Button(
            btn_bar, text="Aceptar", bootstyle="success",
            command=self._on_accept, width=12,
        ).pack(side=RIGHT, padx=4)

    # ─── Preview sobre el canvas ───────────────────────────────────────
    def _register_preview(self):
        canvas = self._get_canvas()
        if canvas is None:
            return
        self._preview_layer = self._draw_preview_layer
        try:
            canvas.add_overlay_layer(self._preview_layer)
        except Exception:
            self._preview_layer = None

    def _unregister_preview(self):
        if self._preview_layer is None:
            return
        canvas = self._get_canvas()
        if canvas is not None:
            try:
                canvas.remove_overlay_layer(self._preview_layer)
            except Exception:
                pass
        self._preview_layer = None

    def _get_canvas(self):
        if self.main_window is None:
            return None
        return getattr(self.main_window, "mesh_canvas", None)

    def _on_field_changed(self, *_args):
        # Parsear sin error: valores intermedios mientras el usuario tipea
        # pueden ser invalidos ("-", "1.", etc) — silenciar y mantener
        # el valor anterior.
        try:
            self._gx_live = float(self.gx_var.get().replace(",", "."))
        except (ValueError, TypeError):
            pass
        try:
            self._gy_live = float(self.gy_var.get().replace(",", "."))
        except (ValueError, TypeError):
            pass
        canvas = self._get_canvas()
        if canvas is not None:
            try:
                canvas.redraw()
            except Exception:
                pass

    def _draw_preview_layer(self, canvas):
        """Dibuja flecha del vector g sobre el canvas. Llamado durante
        cada `canvas.redraw()` mientras este dialogo registre la capa.
        """
        gx = self._gx_live
        gy = self._gy_live
        # Vector nulo: no dibujar nada (evita division por cero).
        mag = math.hypot(gx, gy)
        if mag < 1e-9:
            return

        # Origen: centro del bounding box del modelo, o centro del canvas
        # si no hay nodos.
        if self.project.nodes:
            xs = [n.x for n in self.project.nodes.values()]
            ys = [n.y for n in self.project.nodes.values()]
            ox_world = (min(xs) + max(xs)) / 2
            oy_world = (min(ys) + max(ys)) / 2
            ox, oy = canvas.world_to_screen(ox_world, oy_world)
        else:
            ox = canvas.canvas.winfo_width() / 2
            oy = canvas.canvas.winfo_height() / 2

        # Direccion: (gx, gy) en world → (gx, -gy) en screen (y screen
        # invertido). Normalizar y escalar a longitud fija.
        nx = gx / mag
        ny = -gy / mag
        tip_x = ox + nx * _PREVIEW_ARROW_PX
        tip_y = oy + ny * _PREVIEW_ARROW_PX

        # Color: si include_gravity esta off, mostrar en gris atenuado.
        color = PHASE_PROC_COLOR if self.include_var.get() else TEXT_MUTED_FG

        # Asta de la flecha (linea principal + glow).
        canvas.canvas.create_line(
            ox, oy, tip_x, tip_y,
            fill=color, width=3, capstyle="round",
            tags=_PREVIEW_TAG,
        )
        # Cabeza triangular en la punta.
        # Vector perpendicular para la base de la cabeza.
        px, py = -ny, nx
        base_x = tip_x - nx * _PREVIEW_HEAD_PX
        base_y = tip_y - ny * _PREVIEW_HEAD_PX
        half_w = _PREVIEW_HEAD_PX * 0.55
        head_pts = [
            tip_x, tip_y,
            base_x + px * half_w, base_y + py * half_w,
            base_x - px * half_w, base_y - py * half_w,
        ]
        canvas.canvas.create_polygon(
            head_pts, fill=color, outline=color,
            tags=_PREVIEW_TAG,
        )
        # Punto en el origen (centro del modelo).
        canvas.canvas.create_oval(
            ox - 3, oy - 3, ox + 3, oy + 3,
            fill=color, outline="",
            tags=_PREVIEW_TAG,
        )
        # Label "g" cerca de la punta.
        canvas.canvas.create_text(
            tip_x + nx * 12, tip_y + ny * 12,
            text=f"g = ({gx:.2f}, {gy:.2f})",
            fill=color, font=("Segoe UI", 9, "italic"),
            tags=_PREVIEW_TAG,
        )

    # ─── Aceptar / Cancelar ────────────────────────────────────────────
    def _on_accept(self):
        try:
            gx = float(self.gx_var.get().replace(",", "."))
            gy = float(self.gy_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror(
                "Error",
                "gx y gy deben ser numeros validos (separador decimal '.' o ',').",
                parent=self.dialog,
            )
            return

        include = bool(self.include_var.get())

        changed = (
            gx != self.project.gravity_x
            or gy != self.project.gravity_y
            or include != self.project.include_gravity
        )
        if changed:
            try:
                stack = getattr(self.main_window, "undo_stack", None)
                if stack is not None:
                    stack.capture("cambio de gravedad")
            except Exception:
                pass

        self.project.gravity_x = gx
        self.project.gravity_y = gy
        self.project.include_gravity = include
        if changed:
            self.project.is_modified = True
            self.project.is_solved = False

        if self.main_window is not None:
            try:
                self.main_window._update_status_info()
                self.main_window._update_title()
                self.main_window._refresh_menu_state()
                self.main_window.set_status(
                    f"Gravedad: g = ({gx:.3g}, {gy:.3g})"
                    + ("  ✓ incluida" if include else "  (no aplicada)")
                )
            except Exception:
                pass

        self._unregister_preview()
        self.dialog.destroy()

    def _on_cancel(self):
        self._unregister_preview()
        self.dialog.destroy()

    def _center(self):
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        sw = self.dialog.winfo_screenwidth()
        sh = self.dialog.winfo_screenheight()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        x = max(0, min(x, sw - w))
        y = max(0, min(y, sh - h - 50))
        self.dialog.geometry(f"+{x}+{y}")
