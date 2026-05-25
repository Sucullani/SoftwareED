"""
ProbeOverlay: consulta interactiva de resultados FEM sobre el MeshCanvas.

Modo herramienta del Post-Proceso. Se activa automaticamente al entrar
a Post con `is_solved=True` (no requiere checkbox master).

Comportamiento (rediseño minimalista 2026):

  - Hover sobre la malla -> tooltip transitorio con (x, y) y la magnitud
    activa (la del radio button "Tipo de Resultado"). Throttled
    (PROBE_THROTTLE_MS).

  - Click izquierdo en la malla -> pinea UNA SOLA probe (reemplaza la
    anterior si existia). Marcador circular naranja sin etiqueta de
    texto -- el valor se ve hovereando sobre el pin.

  - Click sobre la probe existente -> la quita (toggle off).

  - Click en vacio (fuera de cualquier elemento) -> quita la probe.

  - Esc -> quita la probe (gestionado por MainWindow._on_escape_global).

  - Toggle "Mostrar Gauss" -> renderiza cuadrados azules en cada GP del
    modelo. Cuando el cursor esta dentro de PROBE_GAUSS_SNAP_PX, snap
    automatico al GP mas cercano: el tooltip muestra valores OFICIALES
    del solver y "Δ vs interpolado: X%". Materializa el Teorema de
    Superconvergencia de Barlow (1976).

El render se hace via mesh_canvas.add_overlay_layer(...) -- todo lo
que dibuja el probe lleva tag prefijo "edu_probe" para limpiarlo en
cada redraw del canvas. No toca el dibujo principal del MeshCanvas.

Referencias:
    - Barlow, J. (1976). IJNME 10(2). -- superconvergencia en Gauss.
    - Hinton & Campbell (1974). IJNME 8(3). -- promediado nodal.
    - Hua, C. (1990). FEAD 7. -- mapeo inverso isoparametrico.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import tkinter as tk

from config.settings import (
    PROBE_PIN_COLOR, GAUSS_MARKER_COLOR, GAUSS_MARKER_SIZE_PX,
    PROBE_GAUSS_SNAP_PX, PROBE_NODE_SNAP_PX, PROBE_NODE_SNAP_COLOR,
    PROBE_NODE_RING_PX, PROBE_THROTTLE_MS, PROBE_PIN_RADIUS_PX,
    PROBE_PIN_DELETE_PX, fmt,
)
from fem.probe_query import (
    inverse_iso_map_NR, compute_raw, compute_smooth,
    crude_values_at_node, gauss_physical_coords,
)
from gui.widgets.probe_tooltip import ProbeTooltip


_TAG = "edu_probe"


@dataclass
class Probe:
    """Probe pinneada: posicion en coords naturales del elemento + cache de
    posicion fisica para render rapido. Los VALORES se recomputan al vuelo
    (cambio de modo crudo/suavizado o de magnitud visualizada). UNA sola
    instancia activa a la vez (no hay numeracion P1/P2/...)."""
    elem_id: int
    xi: float
    eta: float
    world_x: float
    world_y: float


# Mapeo result_type del Post (radio button) -> clave del dict de valores
# y label corto para el tooltip. Compartido entre tooltip de hover y
# tooltip de la probe pinneada -> coherencia visual.
_RESULT_LABEL = {
    "Ux":   ("ux", "Ux", "displacement"),
    "Uy":   ("uy", "Uy", "displacement"),
    "Umag": (None, "|U|", "displacement"),  # caso especial (no esta en vals)
    "Sx":   ("sigma_x", "σx", "stress"),
    "Sy":   ("sigma_y", "σy", "stress"),
    "Txy":  ("tau_xy", "τxy", "stress"),
    "S1":   ("sigma_1", "σ1", "stress"),
    "S2":   ("sigma_2", "σ2", "stress"),
    "VM":   ("von_mises", "VM", "stress"),
}


class ProbeOverlay:
    """Overlay de consulta interactiva sobre MeshCanvas (modo Post)."""

    def __init__(self, mesh_canvas, post_tab, main_window):
        self.mesh_canvas = mesh_canvas
        self.post_tab = post_tab
        self.main_window = main_window
        self.project = post_tab.project

        # Estado
        self.active = False
        self.smooth_mode = True        # default suavizado (alineado con post_tab)
        self.show_gauss = False
        self.pinned: Optional[Probe] = None   # UNA sola probe activa

        # Cache
        self._last_hit_elem_id: Optional[int] = None
        self._all_gauss: list[dict] = []   # gauss_physical_coords flat
        self._snapped_node_id: Optional[int] = None  # nodo bajo el cursor

        # Tooltip "Detalles completos" persistente (click derecho).
        # Cuando esta abierto, el hover normal se pausa para no parpadear.
        # Es un DetailsPanel (Toplevel con valores + Mohr inset embebido)
        # en lugar del ProbeTooltip text-only legacy.
        self._details_open: bool = False
        self._details_panel = None  # type: Optional[DetailsPanel]

        # Hover throttle
        self._after_id = None
        self._last_motion_xy = None

        # Tooltip flotante (lazy)
        self._tooltip = ProbeTooltip(self.mesh_canvas.canvas)

        # Bind IDs para poder desconectar al deactivate
        self._bind_ids: list[tuple[str, str]] = []

        # Referencias a la solucion (las setea post_tab tras auto_solve).
        self.solution = None
        self.nodal_stresses = None
        self.element_stresses = None

    # ─── Ciclo de vida ─────────────────────────────────────────────────────

    def activate(self, solution, element_stresses, nodal_stresses):
        """Activa el modo. post_tab lo llama tras auto_solve exitoso."""
        self.solution = solution
        self.element_stresses = element_stresses
        self.nodal_stresses = nodal_stresses

        if self.active:
            # Re-activacion: solo refrescar datos (re-evaluar pin).
            self._recompute_gauss_cache()
            self.mesh_canvas.redraw()
            return

        self.active = True
        # Flag de modo en el canvas -> _on_click hace early-return
        self.mesh_canvas.probe_mode_active = True

        # Registrar capa de overlay + bindings
        self.mesh_canvas.add_overlay_layer(self._draw_layer)
        self._bind("<Motion>", self._on_motion)
        self._bind("<ButtonPress-1>", self._on_click)
        self._bind("<ButtonPress-3>", self._on_right_click)
        self._bind("<Control-c>", self._on_ctrl_copy)
        self._bind("<Control-C>", self._on_ctrl_copy)
        self._bind("<Leave>", self._on_leave)

        self._recompute_gauss_cache()
        self.mesh_canvas.redraw()

        # Hint al usuario sobre los nuevos gestos disponibles
        try:
            self.main_window.set_status(
                "Consulta interactiva activa  ·  clic: pinear  ·  "
                "clic derecho: detalles  ·  Ctrl+C: copiar"
            )
        except Exception:
            pass

    def deactivate(self):
        """Desactiva el modo. Llamar al salir de Post."""
        if not self.active:
            return
        self.active = False
        self.mesh_canvas.probe_mode_active = False
        self.pinned = None

        self.mesh_canvas.remove_overlay_layer(self._draw_layer)
        self._unbind_all()

        if self._after_id is not None:
            try:
                self.mesh_canvas.canvas.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        # Tooltip lo destruimos para evitar Toplevel huerfanos.
        try:
            self._tooltip.destroy()
        except Exception:
            pass
        self._tooltip = ProbeTooltip(self.mesh_canvas.canvas)

        # DetailsPanel persistente: destruir si quedo abierto al salir.
        if self._details_panel is not None:
            try:
                self._details_panel.destroy()
            except Exception:
                pass
            self._details_panel = None
        self._details_open = False

        # Limpiar pin del canvas (el redraw siguiente lo borra,
        # pero por las dudas hacemos delete del tag).
        try:
            self.mesh_canvas.canvas.delete(_TAG)
        except Exception:
            pass

    # ─── Sliders / toggles del panel de control ───────────────────────────

    def set_smooth_mode(self, smooth: bool):
        """Toggle crudo (False) <-> suavizado (True). Refresca pin."""
        self.smooth_mode = bool(smooth)
        self.mesh_canvas.redraw()

    def set_show_gauss(self, show: bool):
        """Toggle render de puntos Gauss."""
        self.show_gauss = bool(show)
        self.mesh_canvas.redraw()

    def clear_pinned(self):
        """Quita la probe pinneada Y los detalles persistentes si los hay
        (gestionado por Esc desde MainWindow)."""
        changed = False
        if self._close_details_if_open():
            changed = True
        if self.pinned is not None:
            self.pinned = None
            changed = True
        if changed:
            self.mesh_canvas.redraw()

    def has_pinned(self) -> bool:
        return self.pinned is not None or self._details_open

    # ─── Bindings helpers ──────────────────────────────────────────────────

    def _bind(self, sequence: str, handler):
        cid = self.mesh_canvas.canvas.bind(sequence, handler, add="+")
        self._bind_ids.append((sequence, cid))

    def _unbind_all(self):
        canvas = self.mesh_canvas.canvas
        for sequence, cid in self._bind_ids:
            try:
                canvas.unbind(sequence, cid)
            except Exception:
                pass
        self._bind_ids.clear()

    # ─── Hit-test ──────────────────────────────────────────────────────────

    def _find_element_at(self, x: float, y: float):
        """Devuelve (elem_id, xi, eta) o None.

        (1) Intenta primero el `_last_hit_elem_id` (cache O(1) tipico).
        (2) Itera linealmente sobre todos los elementos (~1 ms para N<=1000).

        Las coords del elemento se toman SIEMPRE originales (sin
        deformacion) -- formulacion Lagrangiana total: el punto material
        no se desplaza en el espacio material.
        """
        proj = self.project
        if not proj.elements:
            return None

        def _try_elem(eid):
            elem = proj.elements.get(eid)
            if elem is None:
                return None
            coords = self._elem_coords(elem)
            sol = inverse_iso_map_NR(x, y, coords, proj.element_type)
            if sol is None:
                return None
            return (eid, sol[0], sol[1])

        if self._last_hit_elem_id is not None:
            hit = _try_elem(self._last_hit_elem_id)
            if hit is not None:
                return hit

        for eid in proj.elements.keys():
            if eid == self._last_hit_elem_id:
                continue
            hit = _try_elem(eid)
            if hit is not None:
                self._last_hit_elem_id = eid
                return hit
        return None

    def _elem_coords(self, elem):
        """Coords originales del elemento en orden de node_ids."""
        import numpy as np
        return np.array(
            [[self.project.nodes[nid].x, self.project.nodes[nid].y]
             for nid in elem.node_ids],
            dtype=float,
        )

    def _hit_test_pin(self, sx: int, sy: int) -> bool:
        """Devuelve True si (sx, sy) cae sobre la probe pinneada."""
        if self.pinned is None:
            return False
        psx, psy = self.mesh_canvas.world_to_screen(
            self.pinned.world_x, self.pinned.world_y
        )
        return math.hypot(psx - sx, psy - sy) <= PROBE_PIN_DELETE_PX

    def _hit_test_gauss(self, sx: int, sy: int) -> Optional[dict]:
        """Punto Gauss bajo el cursor (dentro de PROBE_GAUSS_SNAP_PX) o None."""
        if not self.show_gauss or not self._all_gauss:
            return None
        best = None
        best_d = PROBE_GAUSS_SNAP_PX + 1
        for gp in self._all_gauss:
            gsx, gsy = self.mesh_canvas.world_to_screen(gp["x"], gp["y"])
            d = math.hypot(gsx - sx, gsy - sy)
            if d <= PROBE_GAUSS_SNAP_PX and d < best_d:
                best_d = d
                best = gp
        return best

    def _hit_test_node(self, sx: int, sy: int) -> Optional[int]:
        """Nodo bajo el cursor (dentro de PROBE_NODE_SNAP_PX) o None.

        Snap siempre activo (los nodos son visibles en el canvas de todos
        modos -- no requiere toggle). Iteracion lineal sobre todos los
        nodos del proyecto: O(N) ~= 0.1 ms para 1000 nodos.

        Devuelve el node_id del mas cercano dentro del radio, o None.
        """
        if not self.project.nodes:
            return None
        best_id = None
        best_d = PROBE_NODE_SNAP_PX + 1
        for nid in self.project.nodes:
            # Coords ORIGINALES del nodo (sin deformacion) -- coherente
            # con el resto del probe (Lagrangiano total).
            node = self.project.nodes[nid]
            nsx, nsy = self.mesh_canvas.world_to_screen(node.x, node.y)
            d = math.hypot(nsx - sx, nsy - sy)
            if d <= PROBE_NODE_SNAP_PX and d < best_d:
                best_d = d
                best_id = nid
        return best_id

    # ─── Hover (throttled) ─────────────────────────────────────────────────

    def _on_motion(self, event):
        if not self.active or self._details_open:
            return

        # Trackear posicion siempre (no solo en hover libre): Ctrl+C la
        # necesita para resolver el target.
        self._last_motion_xy = (event.x, event.y)

        # Jerarquia de snap (SIN throttle: son solo distancias euclideas):
        #   1. Gauss (si toggle activo)
        #   2. Nodo (siempre activo)
        #   3. Punto libre (con throttle)
        # Resolve conflicto: si ambos en rango, gana el de menor distancia.
        gp = self._hit_test_gauss(event.x, event.y)
        nid = self._hit_test_node(event.x, event.y)
        if gp is not None and nid is not None:
            # Comparar distancias
            gsx, gsy = self.mesh_canvas.world_to_screen(gp["x"], gp["y"])
            node = self.project.nodes[nid]
            nsx, nsy = self.mesh_canvas.world_to_screen(node.x, node.y)
            d_g = math.hypot(gsx - event.x, gsy - event.y)
            d_n = math.hypot(nsx - event.x, nsy - event.y)
            if d_g < d_n:
                self._snapped_node_id = None
                self._show_gauss_tooltip(gp, event.x, event.y)
            else:
                self._snapped_node_id = nid
                self._show_node_tooltip(nid, event.x, event.y)
                self.mesh_canvas.redraw()
            return
        if gp is not None:
            if self._snapped_node_id is not None:
                self._snapped_node_id = None
                self.mesh_canvas.redraw()
            self._show_gauss_tooltip(gp, event.x, event.y)
            return
        if nid is not None:
            if self._snapped_node_id != nid:
                self._snapped_node_id = nid
                self.mesh_canvas.redraw()
            self._show_node_tooltip(nid, event.x, event.y)
            return

        # Si veniamos snappeados a un nodo, redibujar para quitar el anillo
        if self._snapped_node_id is not None:
            self._snapped_node_id = None
            self.mesh_canvas.redraw()

        # Punto libre: con throttle.
        self._last_motion_xy = (event.x, event.y)
        if self._after_id is not None:
            try:
                self.mesh_canvas.canvas.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = self.mesh_canvas.canvas.after(
            PROBE_THROTTLE_MS, self._process_hover
        )

    def _on_leave(self, _event):
        # Cursor salio del canvas
        if self._after_id is not None:
            try:
                self.mesh_canvas.canvas.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        # Si los detalles persistentes estan abiertos, NO los escondemos
        # al salir del canvas (la idea es que persistan hasta cerrar
        # explicitamente con clic, Esc o click derecho).
        if self._details_open:
            return
        try:
            self._tooltip.hide()
        except Exception:
            pass

    def _process_hover(self):
        self._after_id = None
        if not self.active or self._last_motion_xy is None:
            return
        sx, sy = self._last_motion_xy
        wx, wy = self.mesh_canvas.screen_to_world(sx, sy)
        hit = self._find_element_at(wx, wy)
        if hit is None:
            try:
                self._tooltip.hide()
            except Exception:
                pass
            return
        elem_id, xi, eta = hit
        vals = self._compute_values(elem_id, xi, eta)
        if vals is None:
            return
        wx_exact, wy_exact = self._natural_to_physical(elem_id, xi, eta)
        lines = self._format_hover_lines(wx_exact, wy_exact, vals)
        self._tooltip.show(sx, sy, lines, accent="default")

    def _show_gauss_tooltip(self, gp: dict, sx: int, sy: int):
        """Tooltip especifico para snap a Gauss: valores oficiales + delta.

        Muestra solo la magnitud activa (no satura). Calcula Δ% sobre esa
        magnitud (no sobre VM si la activa es otra). Materializa Barlow.
        """
        rtype = self._active_result_type()
        key, label_short, kind = _RESULT_LABEL.get(rtype, (None, rtype, "stress"))

        # Calcular valor oficial (Gauss) y interpolado en el mismo (xi, eta)
        gauss_val = self._gp_value(gp, rtype)
        interp_vals = self._compute_values(gp["elem_id"], gp["xi"], gp["eta"])

        # Coords NO incluidas: el toolbar del canvas las muestra.
        lines = [f"GAUSS PG#{gp['gp_idx'] + 1}"]
        if gauss_val is not None:
            lines.append(f"{label_short} = {fmt(gauss_val, kind)}  oficial")
            if interp_vals is not None and key in interp_vals and abs(gauss_val) > 1e-12:
                delta = abs(interp_vals[key] - gauss_val) / abs(gauss_val) * 100.0
                lines.append(f"Δ vs interpolado: {delta:.2f}%")
        else:
            # Magnitud no disponible en Gauss (ej. Ux/Uy/Umag: no son
            # esfuerzos). Mostrar VM como referencia.
            lines.append(f"VM = {fmt(gp['von_mises'], 'stress')}  oficial")

        self._tooltip.show(sx, sy, lines, accent="gauss")

    def _gp_value(self, gp: dict, result_type: str):
        """Devuelve el valor del Gauss para la magnitud activa.

        Para Ux/Uy/|U| no existe (los desplazamientos son interpolados,
        no se almacenan en el Gauss) -- devuelve None.
        """
        key = _RESULT_LABEL.get(result_type, (None, None, None))[0]
        if key is None or key not in gp:
            return None
        return gp[key]

    def _show_node_tooltip(self, nid: int, sx: int, sy: int):
        """Tooltip al snappear a un nodo.

        Modo SUAVIZADO: muestra el valor nodal promediado (lo que el
        contorno muestra en ese nodo). Tooltip pequeño.

        Modo CRUDO: muestra los N valores discontinuos -- uno por cada
        elemento que contiene el nodo -- y la desviacion estandar (medida
        de discontinuidad C0). Tooltip expandido. ORO PEDAGOGICO: el
        alumno *ve* la naturaleza C0 del MEF.
        """
        node = self.project.nodes[nid]
        rtype = self._active_result_type()
        key, label_short, kind = _RESULT_LABEL.get(rtype, (None, rtype, "stress"))
        rol = self._node_role(nid)

        # Coords NO incluidas: el toolbar del canvas ya muestra (x, y).
        # Header con ID + rol identifica al nodo sin ambiguedad.
        lines = [f"NODO N{nid}  ({rol})"]

        if self.smooth_mode or not key or kind == "displacement":
            # Modo suavizado o desplazamiento: valor unico.
            if kind == "displacement" and self.solution is not None:
                idx = self.project.node_index_map.get(nid)
                if idx is not None:
                    u = self.solution["u"]
                    ux = float(u[2 * idx])
                    uy = float(u[2 * idx + 1])
                    if rtype == "Ux":
                        lines.append(f"Ux = {fmt(ux, 'displacement')}")
                    elif rtype == "Uy":
                        lines.append(f"Uy = {fmt(uy, 'displacement')}")
                    elif rtype == "Umag":
                        lines.append(
                            f"|U| = {fmt(math.hypot(ux, uy), 'displacement')}"
                        )
                    else:
                        lines.append(f"Ux = {fmt(ux, 'displacement')}")
                        lines.append(f"Uy = {fmt(uy, 'displacement')}")
            else:
                # Esfuerzo en suavizado: valor nodal promediado
                ns = (self.nodal_stresses or {}).get(nid)
                if ns is not None and key in ns:
                    lines.append(f"{label_short} = {fmt(ns[key], kind)}  (promedio)")
        else:
            # Modo crudo + esfuerzo: N valores discontinuos
            crude = crude_values_at_node(self.project, self.solution, nid)
            if not crude:
                lines.append(f"{label_short} = (sin datos)")
            else:
                lines.append(f"{label_short} segun cada elemento:")
                vals_only = []
                for entry in crude:
                    v = entry.get(key)
                    if v is None:
                        continue
                    vals_only.append(v)
                    lines.append(
                        f"  Elem #{entry['elem_id']:>2}:  "
                        f"{fmt(v, kind)}"
                    )
                if len(vals_only) >= 2:
                    import statistics
                    vmin = min(vals_only)
                    vmax = max(vals_only)
                    std = statistics.stdev(vals_only)
                    lines.append(f"  rango: {fmt(vmax - vmin, kind)}")
                    lines.append(f"  std:   {fmt(std, kind)}  (discontinuidad C0)")

        self._tooltip.show(sx, sy, lines, accent="node")

    def _node_role(self, nid: int) -> str:
        """Rol del nodo: 'vertice', 'medio de arista', 'centro Q9'."""
        for elem in self.project.elements.values():
            if nid not in elem.node_ids:
                continue
            idx = elem.node_ids.index(nid)
            if idx < 4:
                return "vertice"
            if idx < 8:
                return "medio de arista"
            return "centro Q9"
        return "huerfano"

    # ─── Click pinea probe ─────────────────────────────────────────────────

    def _on_click(self, event):
        if not self.active:
            return

        # (0) Si hay detalles persistentes abiertos -> cerrarlos primero.
        # El click izq se "consume" en cerrarlos, no pinea ni quita pin.
        if self._close_details_if_open():
            return

        # (1) Click sobre la probe pinneada -> toggle off
        if self._hit_test_pin(event.x, event.y):
            self.pinned = None
            self.mesh_canvas.redraw()
            return

        # (2) Snap a Gauss tiene prioridad sobre click libre
        gp = self._hit_test_gauss(event.x, event.y)
        if gp is not None:
            self._pin_probe(
                gp["elem_id"], gp["xi"], gp["eta"], gp["x"], gp["y"]
            )
            return

        # (3) Click en la malla -> pinea (reemplaza la anterior)
        sx, sy = event.x, event.y
        wx, wy = self.mesh_canvas.screen_to_world(sx, sy)
        hit = self._find_element_at(wx, wy)
        if hit is None:
            # Click en vacio (fuera de cualquier elemento) -> quita la probe
            # si existia. No hace nada si no habia probe.
            if self.pinned is not None:
                self.pinned = None
                self.mesh_canvas.redraw()
            return
        elem_id, xi, eta = hit
        wx_exact, wy_exact = self._natural_to_physical(elem_id, xi, eta)
        self._pin_probe(elem_id, xi, eta, wx_exact, wy_exact)

    def _pin_probe(self, elem_id, xi, eta, wx, wy):
        """Reemplaza la probe pinneada (si existia) con una nueva."""
        self.pinned = Probe(
            elem_id=elem_id, xi=xi, eta=eta,
            world_x=wx, world_y=wy,
        )
        self.mesh_canvas.redraw()

    # ─── Click derecho: menu contextual ────────────────────────────────────

    def _on_right_click(self, event):
        """Click derecho -> abre directamente el tooltip persistente con
        TODOS los valores. Sin menu intermedio: una sola accion = un solo
        click. Patron analogo a "modifier opens detail panel" de
        Figma/Photoshop/Blender.

        Si los detalles ya estan abiertos, click derecho los CIERRA
        (toggle): permite usar el mismo gesto para abrir/cerrar.

        Acciones complementarias accesibles desde otros gestos:
          - Click izquierdo: pinea probe.
          - Ctrl+C: copia valores TSV al portapapeles.
          - Esc: cierra detalles + quita probe.
        """
        if not self.active:
            return

        # Toggle: si hay detalles abiertos, cerrar.
        if self._close_details_if_open():
            return

        # Resolver punto bajo el cursor (mismo orden que hover)
        target = self._resolve_target_at(event.x, event.y)
        if target is None:
            return

        self._show_details_persistent(target, event.x, event.y)

    def _on_ctrl_copy(self, _event):
        """Ctrl+C en el canvas -> copia los valores del punto bajo el
        cursor en formato TSV al portapapeles.

        El "punto bajo el cursor" se resuelve via _last_motion_xy (la
        ultima posicion conocida del mouse en el canvas). Si el canvas
        no tiene foco o el mouse nunca se movio sobre el, no hace nada
        (no consume el evento -- propaga al binding nativo).
        """
        if not self.active or self._last_motion_xy is None:
            return None
        sx, sy = self._last_motion_xy
        target = self._resolve_target_at(int(sx), int(sy))
        if target is None:
            return None
        self._copy_values_tsv(target)
        return "break"  # consume el evento -- no propaga

    def _resolve_target_at(self, sx: int, sy: int):
        """Devuelve dict {kind, elem_id, xi, eta, world_x, world_y, ...}
        describiendo el punto bajo (sx, sy), o None si no hay malla.

        kind in {"node", "gauss", "free"}. Incluye campos extra segun
        kind: para "node" agrega "node_id"; para "gauss" agrega "gp_idx".
        """
        # Prioridad 1: nodo
        nid = self._hit_test_node(sx, sy)
        if nid is not None:
            node = self.project.nodes[nid]
            # Para coords (xi, eta) usamos cualquier elemento que contiene
            # el nodo: lo necesitamos para compute_raw / compute_smooth.
            target_elem = None
            local_idx = None
            for eid, elem in self.project.elements.items():
                if nid in elem.node_ids:
                    target_elem = eid
                    local_idx = elem.node_ids.index(nid)
                    break
            if target_elem is None or local_idx is None:
                return None
            # Coords naturales del nodo dentro de ese elemento
            from fem.probe_query import _Q4_NODE_NATURAL, _Q9_NODE_NATURAL
            table = (_Q4_NODE_NATURAL if self.project.element_type.startswith("Q4")
                     else _Q9_NODE_NATURAL)
            if local_idx >= len(table):
                return None
            xi, eta = table[local_idx]
            return {
                "kind": "node",
                "node_id": nid,
                "elem_id": target_elem,
                "xi": xi, "eta": eta,
                "world_x": node.x, "world_y": node.y,
            }

        # Prioridad 2: Gauss
        gp = self._hit_test_gauss(sx, sy)
        if gp is not None:
            return {
                "kind": "gauss",
                "gp_idx": gp["gp_idx"],
                "elem_id": gp["elem_id"],
                "xi": gp["xi"], "eta": gp["eta"],
                "world_x": gp["x"], "world_y": gp["y"],
            }

        # Prioridad 3: punto libre en algun elemento
        wx, wy = self.mesh_canvas.screen_to_world(sx, sy)
        hit = self._find_element_at(wx, wy)
        if hit is None:
            return None
        eid, xi, eta = hit
        wx_exact, wy_exact = self._natural_to_physical(eid, xi, eta)
        return {
            "kind": "free",
            "elem_id": eid,
            "xi": xi, "eta": eta,
            "world_x": wx_exact, "world_y": wy_exact,
        }

    def _gather_full_values(self, target) -> Optional[dict]:
        """Calcula TODOS los valores (ux, uy, σx..VM) en el target.

        Para nodos: usa el elemento target['elem_id'] como contexto pero
        en modo SUAVIZADO devuelve los nodales promediados (no per-elem).
        Para Gauss: usa los valores oficiales del solver.
        Para punto libre: compute_raw o compute_smooth segun el modo.
        """
        if target["kind"] == "gauss" and self.element_stresses:
            # Buscar el dict oficial del Gauss
            data = self.element_stresses.get(target["elem_id"])
            if data is not None and target["gp_idx"] < len(data["gauss_stresses"]):
                gp = data["gauss_stresses"][target["gp_idx"]]
                ux, uy = self._ux_uy_at(target["elem_id"], target["xi"], target["eta"])
                return {
                    "ux": ux, "uy": uy,
                    "sigma_x": gp["sigma_x"],
                    "sigma_y": gp["sigma_y"],
                    "tau_xy":  gp["tau_xy"],
                    "sigma_1": gp["sigma_1"],
                    "sigma_2": gp["sigma_2"],
                    "von_mises": gp["von_mises"],
                }
        # Nodo y libre: usar el modo activo
        return self._compute_values(target["elem_id"], target["xi"], target["eta"])

    def _ux_uy_at(self, elem_id, xi, eta):
        """Helper: interpola (ux, uy) usando las shape functions."""
        from fem.probe_query import displacement_at
        return displacement_at(self.project, self.solution, elem_id, xi, eta)

    def _copy_values_tsv(self, target):
        """Copia los valores del target al portapapeles en formato TSV.

        Header + 1 fila. Pegable en Excel/Word/Google Sheets para uso en
        informes, validacion cruzada o debugging del solver.
        """
        vals = self._gather_full_values(target)
        if vals is None:
            return
        headers = ["x", "y", "Elem", "xi", "eta",
                   "ux", "uy", "sigma_x", "sigma_y", "tau_xy",
                   "sigma_1", "sigma_2", "von_mises"]
        if target["kind"] == "node":
            headers.insert(0, "Nodo")
            row = [str(target["node_id"])]
        else:
            row = []
        row.extend([
            f"{target['world_x']:.6f}",
            f"{target['world_y']:.6f}",
            str(target["elem_id"]),
            f"{target['xi']:+.6f}",
            f"{target['eta']:+.6f}",
            f"{vals['ux']:.6e}",
            f"{vals['uy']:.6e}",
            f"{vals['sigma_x']:.6f}",
            f"{vals['sigma_y']:.6f}",
            f"{vals['tau_xy']:.6f}",
            f"{vals['sigma_1']:.6f}",
            f"{vals['sigma_2']:.6f}",
            f"{vals['von_mises']:.6f}",
        ])
        text = "\t".join(headers) + "\n" + "\t".join(row)
        try:
            canvas = self.mesh_canvas.canvas
            canvas.clipboard_clear()
            canvas.clipboard_append(text)
            self.main_window.set_status(
                "Valores copiados al portapapeles (TSV) - pegable en Excel"
            )
        except Exception:
            self.main_window.set_status("Error al copiar al portapapeles")

    def _show_details_persistent(self, target, sx, sy):
        """Panel persistente con TODOS los valores + circulo de Mohr.

        Reemplaza el tooltip text-only legacy: ahora es un Toplevel con
        valores numericos a la izq + Mohr inset matplotlib a la der.
        Cierra con click izq fuera, Esc, click derecho de nuevo sobre el
        mismo target, o boton ✕ del panel.

        Decision: el circulo de Mohr es respuesta PUNTUAL al estado de
        tension -- vive donde se consulta el punto, no como modulo aparte.
        Absorbe la pedagogia de M8 (legacy) sin la rotacion drag-todo
        (decision documentada: rotar todas las cruces de la malla a la vez
        confundia mas que enseñaba).
        """
        vals = self._gather_full_values(target)
        if vals is None:
            return

        # Cerrar panel anterior si quedo huerfano (defense in depth)
        if self._details_panel is not None:
            try:
                self._details_panel.destroy()
            except Exception:
                pass
            self._details_panel = None

        from gui.postprocessing.details_panel import DetailsPanel
        # Accent segun tipo de target -- coherente con el ProbeTooltip de
        # hover (verde gauss / azul nodo / naranja libre).
        accent = {"node": "node", "gauss": "gauss"}.get(
            target["kind"], "details"
        )
        self._details_panel = DetailsPanel(
            self.mesh_canvas.canvas, target, vals, accent=accent,
            on_close=self._on_details_panel_closed,
        )
        self._details_panel.show(sx, sy)
        self._details_open = True
        self.main_window.set_status(
            "Detalles abiertos - clic en el canvas, Esc o ✕ para cerrar"
        )

    def _on_details_panel_closed(self):
        """Callback registrado en el DetailsPanel: el usuario clickeo ✕
        o presiono Esc dentro del propio panel. Sincroniza el flag y
        destruye el Toplevel."""
        self._details_open = False
        if self._details_panel is not None:
            try:
                self._details_panel.destroy()
            except Exception:
                pass
            self._details_panel = None

    def _close_details_if_open(self) -> bool:
        """Cierra el DetailsPanel si esta abierto. Retorna True si habia
        algo abierto (para que el caller sepa que el click no debe
        propagarse a otra accion)."""
        if not self._details_open:
            return False
        self._details_open = False
        if self._details_panel is not None:
            try:
                self._details_panel.destroy()
            except Exception:
                pass
            self._details_panel = None
        return True


    def _natural_to_physical(self, elem_id, xi, eta):
        from fem.shape_functions import get_shape_functions
        elem = self.project.elements[elem_id]
        coords = self._elem_coords(elem)
        N_func, _ = get_shape_functions(self.project.element_type)
        N = N_func(xi, eta)
        return (
            float(N @ coords[:len(N), 0]),
            float(N @ coords[:len(N), 1]),
        )

    # ─── Computo del valor (crudo o suavizado) ────────────────────────────

    def _compute_values(self, elem_id, xi, eta):
        if self.smooth_mode:
            return compute_smooth(
                self.project, self.solution, self.nodal_stresses,
                elem_id, xi, eta,
            )
        return compute_raw(self.project, self.solution, elem_id, xi, eta)

    def _active_result_type(self) -> str:
        """Lee el radio button activo del Post-Proceso ('VM', 'Sx', ...)."""
        result_var = getattr(self.post_tab, "result_var", None)
        if result_var is None:
            return "VM"
        return result_var.get() or "VM"

    def _format_hover_lines(self, world_x, world_y, vals) -> list:
        """Tooltip minimo: solo la magnitud activa.

        Coords NO se incluyen -- el toolbar del canvas ya las muestra en
        vivo (`x: --  y: --`). Repetir la posicion en el tooltip era
        ruido visual. Para mas datos: click derecho abre detalles.

        El usuario ya eligio la magnitud que le importa con el radio button.
        Mostrar 8 valores en cada movimiento del cursor es ruido.
        """
        rtype = self._active_result_type()
        key, label_short, kind = _RESULT_LABEL.get(rtype, (None, rtype, "stress"))

        if rtype == "Umag":
            ux = vals.get("ux", 0.0)
            uy = vals.get("uy", 0.0)
            umag = math.hypot(ux, uy)
            return [f"|U| = {fmt(umag, 'displacement')}"]
        if key is not None and key in vals:
            return [f"{label_short} = {fmt(vals[key], kind)}"]
        return [f"VM = {fmt(vals.get('von_mises', 0.0), 'stress')}"]

    # ─── Render layer ──────────────────────────────────────────────────────

    def _draw_layer(self, _canvas):
        """Capa overlay registrada en mesh_canvas.add_overlay_layer.

        Dibuja: puntos Gauss (si show_gauss) y la probe pinneada (si existe,
        UNA sola). El halo del hover se maneja con el tooltip Toplevel,
        no aqui (para que no parpadee con cada motion).
        """
        canvas = self.mesh_canvas.canvas
        # El redraw global ya limpio todo via canvas.delete("all"). No
        # hace falta delete(_TAG) aqui.

        if self.show_gauss:
            self._draw_gauss_markers(canvas)

        if self._snapped_node_id is not None:
            self._draw_snap_ring(canvas)

        if self.pinned is not None:
            self._draw_pinned_probe(canvas)

    def _draw_snap_ring(self, canvas):
        """Anillo cyan alrededor del nodo enganchado. Feedback visual de
        que el snap esta activo -- como el inspector de SolidWorks."""
        nid = self._snapped_node_id
        if nid not in self.project.nodes:
            return
        node = self.project.nodes[nid]
        sx, sy = self.mesh_canvas.world_to_screen(node.x, node.y)
        r = PROBE_NODE_RING_PX
        canvas.create_oval(
            sx - r, sy - r, sx + r, sy + r,
            outline=PROBE_NODE_SNAP_COLOR, fill="",
            width=2, tags=(_TAG,),
        )

    def _draw_gauss_markers(self, canvas):
        s = GAUSS_MARKER_SIZE_PX
        for gp in self._all_gauss:
            sx, sy = self.mesh_canvas.world_to_screen(gp["x"], gp["y"])
            canvas.create_rectangle(
                sx - s, sy - s, sx + s, sy + s,
                outline=GAUSS_MARKER_COLOR, fill="",
                width=1, tags=(_TAG,),
            )

    def _draw_pinned_probe(self, canvas):
        """Marcador minimo de la probe activa: doble circulo naranja.

        SIN etiqueta de texto -- el valor se ve hovereando sobre el pin
        (motion sobre la posicion fisica del pin dispara el tooltip
        normal de hover, que ya muestra la magnitud activa).
        """
        r = PROBE_PIN_RADIUS_PX
        p = self.pinned
        sx, sy = self.mesh_canvas.world_to_screen(p.world_x, p.world_y)
        # Cuerpo: circulo solido naranja
        canvas.create_oval(
            sx - r, sy - r, sx + r, sy + r,
            outline=PROBE_PIN_COLOR, fill=PROBE_PIN_COLOR,
            width=1, tags=(_TAG,),
        )
        # Halo: circulo exterior delgado (indica "esta seleccionado")
        canvas.create_oval(
            sx - r - 2, sy - r - 2, sx + r + 2, sy + r + 2,
            outline=PROBE_PIN_COLOR, fill="",
            width=1, tags=(_TAG,),
        )

    # ─── Cache de Gauss ────────────────────────────────────────────────────

    def _recompute_gauss_cache(self):
        """Reconstruye self._all_gauss con todos los GP del modelo.

        Llamar al activate o cuando element_stresses cambia (re-solve).
        """
        self._all_gauss = []
        if not self.element_stresses:
            return
        for eid in self.project.elements.keys():
            gp_list = gauss_physical_coords(
                self.project, eid, self.element_stresses,
            )
            self._all_gauss.extend(gp_list)
