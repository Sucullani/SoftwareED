"""
DxfImportDialog: dialogo modal para importar geometria DXF al proyecto.

Flujo:
    1. main_window abre directamente el file picker. Si cancela, no se muestra
       este dialogo.
    2. El dialogo recibe `filepath` y carga en el constructor: capas + preview.
    3. Un combo define la unidad de longitud del PROYECTO (preseleccionada con
       la longitud actual de project.unit_system; si el usuario la cambia, el
       unit_system del proyecto se actualiza al sistema canonico con esa
       longitud).
    4. Un combo selecciona la capa de elementos.
    5. Preview en `tk.Canvas` nativo (coherente con el canvas principal).

Las coordenadas del DXF se toman LITERALMENTE: el combo define en que
unidades trabaja el proyecto, y el numero crudo del DXF se interpreta en esa
unidad (flujo SAP2000).
"""

from __future__ import annotations

import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from config.units import UNIT_SYSTEMS
from config.settings import (
    DXF_PREVIEW_BG_COLOR, EDU_NATURAL_OUTLINE_COLOR, DXF_PREVIEW_ELEM_FILL_COLOR,
    CANVAS_NODE_COLOR, DIALOG_MUTED_FG_COLOR, HEALTH_ERROR_LIGHT_COLOR,
    FONT_UI, FONT_UI_LARGE,
)
from file_io.dxf_io import (
    import_dxf, list_dxf_layers, _extract_polyline_vertices,
)
from models.mesh_utils import auto_expand_if_q9


# Colores del canvas principal (coherencia visual)
_PREVIEW_BG = DXF_PREVIEW_BG_COLOR
_PREVIEW_ELEM_OUTLINE = EDU_NATURAL_OUTLINE_COLOR
_PREVIEW_ELEM_FILL = DXF_PREVIEW_ELEM_FILL_COLOR
_PREVIEW_NODE_COLOR = CANVAS_NODE_COLOR
_PREVIEW_NODE_RADIUS = 3
_PREVIEW_MARGIN = 20

# Longitudes soportadas y mapeo canonico a unit_system.
_LENGTH_OPTIONS = ["mm", "cm", "m", "in", "ft"]
_LENGTH_DEFAULT_SYSTEM = {
    "mm": "SI (N, mm, MPa)",
    "cm": "Técnico (kgf, cm, kgf/cm²)",
    "m":  "SI (N, m, Pa)",
    "in": "Imperial (lb, in, psi)",
    "ft": None,  # sin sistema predefinido con ft → se mantiene el actual
}

# Factor de conversion a metros para cada unidad de longitud.
_LENGTH_TO_M = {
    "mm": 0.001,
    "cm": 0.01,
    "m":  1.0,
    "in": 0.0254,
    "ft": 0.3048,
}


def _convert_project_coords(project, from_length, to_length):
    """Re-escala todas las coordenadas del proyecto al cambiar la unidad de
    longitud. Solo aplica a project.nodes (elementos/BCs/cargas son
    referencias por id). Retorna el factor aplicado, o 1.0 si no hay cambio.
    """
    if from_length == to_length or from_length is None or to_length is None:
        return 1.0
    from_m = _LENGTH_TO_M.get(from_length)
    to_m = _LENGTH_TO_M.get(to_length)
    if from_m is None or to_m is None or to_m == 0:
        return 1.0
    factor = from_m / to_m
    if abs(factor - 1.0) < 1e-15:
        return 1.0
    for node in project.nodes.values():
        node.x *= factor
        node.y *= factor
    project.is_modified = True
    project.is_solved = False
    return factor


def _project_length_unit(project):
    """Longitud del sistema de unidades actual ('m', 'mm', ...) o None si
    `unit_system` no esta en `UNIT_SYSTEMS`.
    """
    cfg = UNIT_SYSTEMS.get(project.unit_system)
    if cfg is None:
        return None
    lu = cfg.get("longitud", "").strip()
    return lu or None


from gui.dialogs._dialog_helpers import center_dialog
class DxfImportDialog:
    """Dialogo modal para importar un DXF al proyecto actual."""

    def __init__(self, parent, project, main_window=None, filepath=None):
        if not filepath or not os.path.isfile(filepath):
            raise ValueError("DxfImportDialog requiere un filepath valido.")

        self.project = project
        self.main_window = main_window
        self.parent = parent
        self._filepath = filepath

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("📐  Importar desde AutoCAD (DXF)")
        self.dialog.geometry("760x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)

        # Preseleccionar con la longitud del proyecto actual.
        proj_len = _project_length_unit(project)
        default_len = proj_len if proj_len in _LENGTH_OPTIONS else "m"

        self._length_var = tk.StringVar(value=default_len)
        self._layer_var = tk.StringVar(value="FEM_ELEMENTS")

        self._available_layers = []
        self._preview_canvas = None

        self._build()
        self._center()
        self.dialog.after(50, self._load_dxf)

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build(self):
        outer = ttk.Frame(self.dialog, padding=12)
        outer.pack(fill=BOTH, expand=YES)

        # Header: titulo + nombre del archivo en una linea
        header = ttk.Frame(outer)
        header.pack(fill=X, pady=(0, 10))
        ttk.Label(header, text="Importar geometria desde DXF",
                  font=("Segoe UI", 13, "bold")
                  ).pack(side=LEFT)
        ttk.Label(header,
                  text=f"  ·  {os.path.basename(self._filepath)}",
                  foreground=DIALOG_MUTED_FG_COLOR, font=FONT_UI,
                  ).pack(side=LEFT)

        body = ttk.Frame(outer)
        body.pack(fill=BOTH, expand=YES)

        # ── Columna izquierda: 2 opciones ─────────────────────────────
        left = ttk.Frame(body)
        left.pack(side=LEFT, fill=Y, padx=(0, 12))

        units_frame = ttk.Labelframe(
            left, text="  Unidades del proyecto  ", padding=10
        )
        units_frame.pack(fill=X, pady=(0, 10))
        self._length_combo = ttk.Combobox(
            units_frame, textvariable=self._length_var,
            values=_LENGTH_OPTIONS, state="readonly", width=12,
        )
        self._length_combo.pack(anchor=W)

        layers_frame = ttk.Labelframe(
            left, text="  Capa de elementos  ", padding=10
        )
        layers_frame.pack(fill=X, pady=(0, 10))
        self._layer_combo = ttk.Combobox(
            layers_frame, textvariable=self._layer_var,
            values=[], state="readonly", width=32,
        )
        self._layer_combo.pack(fill=X)
        self._layer_combo.bind(
            "<<ComboboxSelected>>", lambda e: self._refresh_preview()
        )

        # ── Columna derecha: preview ──────────────────────────────────
        right = ttk.Labelframe(body, text="  Preview  ", padding=8)
        right.pack(side=LEFT, fill=BOTH, expand=YES)
        self._preview_canvas = tk.Canvas(
            right, bg=_PREVIEW_BG, highlightthickness=0, bd=0
        )
        self._preview_canvas.pack(fill=BOTH, expand=YES)
        self._preview_canvas.bind(
            "<Configure>", lambda e: self._refresh_preview()
        )
        self._preview_info = ttk.Label(
            right, text="", foreground=DIALOG_MUTED_FG_COLOR, font=("Segoe UI", 8)
        )
        self._preview_info.pack(anchor=W, pady=(4, 0))

        # ── Botones ──────────────────────────────────────────────────
        btn_bar = ttk.Frame(outer)
        btn_bar.pack(fill=X, pady=(10, 0))
        ttk.Button(
            btn_bar, text="Cancelar", bootstyle="secondary",
            command=self._on_cancel, width=12,
        ).pack(side=RIGHT, padx=4)
        self._import_btn = ttk.Button(
            btn_bar, text="Importar", bootstyle="success",
            command=self._on_import, width=14,
        )
        self._import_btn.pack(side=RIGHT, padx=4)
        self._import_btn.configure(state="disabled")

    # ------------------------------------------------------------------
    # CARGA DEL DXF
    # ------------------------------------------------------------------
    def _load_dxf(self):
        try:
            layers = list_dxf_layers(self._filepath)
        except ImportError as exc:
            messagebox.showerror(
                "Falta dependencia 'ezdxf'", str(exc), parent=self.dialog,
            )
            return
        except Exception as exc:
            messagebox.showerror(
                "Error al leer DXF",
                f"No se pudieron listar las capas:\n{exc}",
                parent=self.dialog,
            )
            return

        self._available_layers = layers
        self._layer_combo.configure(values=layers)
        if "FEM_ELEMENTS" in layers:
            self._layer_var.set("FEM_ELEMENTS")
        elif layers:
            for lay in layers:
                if lay not in ("0", "Defpoints"):
                    self._layer_var.set(lay)
                    break
            else:
                self._layer_var.set(layers[0])

        self._import_btn.configure(state="normal")
        self._refresh_preview()

    # ------------------------------------------------------------------
    # PREVIEW (tk.Canvas)
    # ------------------------------------------------------------------
    def _collect_polylines(self):
        if not self._filepath or not os.path.isfile(self._filepath):
            return []
        try:
            from file_io.dxf_io import _require_ezdxf
            ezdxf = _require_ezdxf()
            doc = ezdxf.readfile(self._filepath)
            msp = doc.modelspace()
        except Exception:
            return []
        target = self._layer_var.get()
        out = []
        for poly in msp.query("LWPOLYLINE POLYLINE"):
            if poly.dxf.layer != target:
                continue
            pts = _extract_polyline_vertices(poly)
            if pts is None or len(pts) != 4:
                continue
            out.append(pts)
        return out

    def _refresh_preview(self):
        canvas = self._preview_canvas
        if canvas is None:
            return
        canvas.delete("all")

        polylines = self._collect_polylines()
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w <= 1 or h <= 1:
            return

        if not polylines:
            canvas.create_text(
                w / 2, h / 2,
                text=f"(no hay polilineas cerradas de 4 vertices\n"
                     f"en la capa '{self._layer_var.get()}')",
                fill=HEALTH_ERROR_LIGHT_COLOR, font=FONT_UI_LARGE,
                justify=tk.CENTER,
            )
            self._preview_info.configure(text="0 elementos detectados")
            return

        all_pts = [p for poly in polylines for p in poly]
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        span_x = max(xmax - xmin, 1e-9)
        span_y = max(ymax - ymin, 1e-9)

        avail_w = w - 2 * _PREVIEW_MARGIN
        avail_h = h - 2 * _PREVIEW_MARGIN
        scale_view = min(avail_w / span_x, avail_h / span_y)
        offset_x = (w - span_x * scale_view) / 2 - xmin * scale_view
        offset_y = (h + span_y * scale_view) / 2 + ymin * scale_view

        def w2s(x, y):
            return (x * scale_view + offset_x, -y * scale_view + offset_y)

        unique_nodes = {}
        for poly in polylines:
            screen_pts = []
            for (x, y) in poly:
                sx, sy = w2s(x, y)
                screen_pts.extend([sx, sy])
                key = (round(x, 9), round(y, 9))
                unique_nodes[key] = (sx, sy)
            canvas.create_polygon(
                *screen_pts,
                outline=_PREVIEW_ELEM_OUTLINE,
                fill=_PREVIEW_ELEM_FILL,
                width=1.3,
            )

        r = _PREVIEW_NODE_RADIUS
        for (sx, sy) in unique_nodes.values():
            canvas.create_oval(
                sx - r, sy - r, sx + r, sy + r,
                fill=_PREVIEW_NODE_COLOR, outline="",
            )

        self._preview_info.configure(
            text=f"{len(polylines)} elementos · {len(unique_nodes)} nodos unicos"
        )

    # ------------------------------------------------------------------
    # IMPORT
    # ------------------------------------------------------------------
    def _apply_project_unit(self):
        """Si el usuario cambio el combo de longitud:
        1. Re-escala todas las coordenadas existentes del proyecto (nodos) al
           nuevo sistema — asi una pieza que media 5 m sigue siendo de 5 m
           fisicamente, aunque ahora se exprese como 5000 mm.
        2. Asigna el sistema canonico correspondiente a project.unit_system.

        Retorna el factor aplicado (1.0 si no hubo cambio).
        """
        chosen = self._length_var.get()
        current = _project_length_unit(self.project)
        if chosen == current or current is None:
            return 1.0

        factor = _convert_project_coords(self.project, current, chosen)
        target_system = _LENGTH_DEFAULT_SYSTEM.get(chosen)
        if target_system and target_system in UNIT_SYSTEMS:
            self.project.unit_system = target_system
        return factor

    def _on_import(self):
        if not self._filepath or not os.path.isfile(self._filepath):
            messagebox.showerror(
                "Error", "El archivo seleccionado no existe.",
                parent=self.dialog,
            )
            return

        conv_factor = self._apply_project_unit()
        layer_elems = self._layer_var.get().strip() or "FEM_ELEMENTS"

        # Snapshot para undo: el import muta el modelo de forma masiva
        # (potencialmente cientos de nodos + elementos). Capturar antes
        # de cualquier mutacion permite Ctrl+Z para revertir todo.
        try:
            stack = getattr(self.main_window, "undo_stack", None)
            if stack is not None:
                stack.capture("importar DXF")
        except Exception:
            pass

        try:
            summary = import_dxf(
                filepath=self._filepath,
                project=self.project,
                scale=1.0,
                layer_elements=layer_elems,
            )
        except ImportError as exc:
            messagebox.showerror(
                "Falta dependencia 'ezdxf'", str(exc), parent=self.dialog,
            )
            return
        except Exception as exc:
            messagebox.showerror(
                "Error al importar",
                f"No se pudo importar el DXF:\n{exc}",
                parent=self.dialog,
            )
            return

        # Safety net: si el proyecto esta en Q9, expandir los Q4 importados
        # del DXF (siempre vienen con 4 vertices distintos, validos).
        num_expanded = auto_expand_if_q9(self.project)
        if num_expanded:
            summary["q9_auto_expanded"] = num_expanded

        if self.main_window is not None:
            try:
                self.main_window._update_all_project_refs()
                self.main_window._refresh_all_tabs()
                self.main_window._update_status_info()
                self.main_window._update_title()
                self.main_window._refresh_menu_state()
                self.main_window.root.after(
                    100, self.main_window.mesh_canvas.fit_view
                )
            except Exception:
                pass

        warn_txt = ""
        if summary["warnings"]:
            warn_txt = "\n\nAdvertencias:\n" + "\n".join(
                f"  • {w}" for w in summary["warnings"][:8]
            )
            if len(summary["warnings"]) > 8:
                warn_txt += f"\n  … ({len(summary['warnings']) - 8} mas)"

        conv_txt = ""
        if abs(conv_factor - 1.0) > 1e-12:
            conv_txt = (f"\nCoordenadas existentes reescaladas × {conv_factor:g}")
        skipped_txt = ""
        if summary.get("elements_skipped_duplicate", 0):
            skipped_txt = (f"\nElementos duplicados omitidos: "
                           f"{summary['elements_skipped_duplicate']}")
        q9_txt = ""
        if summary.get("q9_auto_expanded", 0):
            q9_txt = (f"\nElementos expandidos a Q9 automaticamente: "
                      f"{summary['q9_auto_expanded']} (nodos medios + "
                      f"centroide generados)")

        messagebox.showinfo(
            "Importacion completa",
            f"Importado desde:\n{os.path.basename(self._filepath)}\n\n"
            f"Nodos agregados: {summary['nodes_added']}\n"
            f"Elementos agregados: {summary['elements_added']}"
            f"{skipped_txt}{q9_txt}\n"
            f"Unidades del proyecto: {self.project.unit_system}"
            f"{conv_txt}"
            f"{warn_txt}",
            parent=self.dialog,
        )
        self.dialog.destroy()

    def _on_cancel(self):
        self.dialog.destroy()

    def _center(self):
        center_dialog(self.dialog, self.parent)
