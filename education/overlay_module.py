"""
CanvasOverlayModule — base class para módulos educativos en modo Overlay.

Implementa el "Modo B" del documento de propuesta UX. A diferencia de
`BaseEducationalModule` (que abre un Toplevel), este módulo:

    1. Crea un `CanvasOverlay` flotante DENTRO del `MeshCanvas` compartido.
    2. Registra una "capa educativa" en el canvas que dibuja sus
       highlights, glows, particles, etc. SOBRE la malla real.
    3. Engancha callbacks del canvas (click en elemento, click en nodo,
       hover) para que el alumno opere desde el canvas, no desde combos
       redundantes en el overlay.
    4. Al cerrar el overlay (botón × o reset), limpia AUTOMÁTICAMENTE su
       capa de dibujo y restaura los callbacks originales del canvas —
       el modelo siempre vuelve a un estado coherente.

Reglas de oro (del documento UX):

    * El elemento bajo análisis se elige por click en el MeshCanvas, NO
      por combobox interno. El módulo sólo *consume* la selección.
    * La iluminación (glow/halo/coloreado) se aplica al canvas REAL via
      `add_overlay_layer`, no a una copia auxiliar.
    * Los datos extensos (matrices LaTeX, gráficos secundarios) viven en
      el overlay flotante — arrastrable y cerrable.

Uso típico (un módulo concreto):

    class BMatrixOverlay(CanvasOverlayModule):
        TITLE = "② Matriz B"
        PHASE = "proc"

        def build_overlay(self, body):
            # Poblar self.body con widgets (toggle Fórmula/Valores, etc.)
            ...

        def draw_canvas_layer(self, canvas):
            # Dibujar glow en puntos Gauss del elemento seleccionado.
            ...

        def on_element_selected(self, elem_id):
            # El usuario clickeó otro elemento: refrescar la matriz.
            self.element_id = elem_id
            self.refresh_overlay()
            self._mesh.redraw()  # dispara draw_canvas_layer con nuevo eid

Singleton por clase: `activate()` reusa la instancia activa si existe
(lift al frente). Cerrar el overlay libera el slot.
"""

from __future__ import annotations

from typing import Callable, Optional, Tuple

import tkinter as tk

from gui.widgets.canvas_overlay import CanvasOverlay


# Registry de instancias activas: (id(main_window), cls) -> instance.
# Permite que volver a invocar el mismo módulo lo lleve al frente en
# lugar de duplicarlo. Singleton suave: distintos main_windows pueden
# tener cada uno su instancia.
_ACTIVE: dict = {}


class CanvasOverlayModule:
    """Base class para módulos educativos en modo Overlay sobre MeshCanvas.

    Atributos de clase a sobrescribir:
        TITLE             — texto del header del overlay
        PHASE             — "pre" / "proc" / "post" (color de la barra)
        OVERLAY_INITIAL_POS  — (x_px, y_px) relativos al canvas
        OVERLAY_WIDTH     — ancho fijo en px (None = auto)
        OVERLAY_HEIGHT    — alto fijo en px (None = auto)
        REQUIRES_ELEMENT  — si True, valida que haya elem_id antes de abrir
    """

    TITLE: str = "Módulo Overlay"
    PHASE: Optional[str] = None
    OVERLAY_INITIAL_POS: Tuple[int, int] = (24, 24)
    OVERLAY_WIDTH: Optional[int] = 460
    OVERLAY_HEIGHT: Optional[int] = None
    REQUIRES_ELEMENT: bool = False

    # ── Construcción / activación ──────────────────────────────────
    @classmethod
    def activate(cls, main_window, project, element_id):
        """Punto de entrada del launcher. Singleton por (main_window, cls)."""
        key = (id(main_window), cls)
        existing = _ACTIVE.get(key)
        if existing is not None:
            try:
                existing._overlay.lift()
            except Exception:
                _ACTIVE.pop(key, None)
            else:
                # Actualizar elemento si vino uno distinto.
                if element_id is not None and element_id != existing.element_id:
                    existing.set_element(element_id)
                return existing
        inst = cls(main_window, project, element_id)
        _ACTIVE[key] = inst
        return inst

    def __init__(self, main_window, project, element_id):
        self.main_window = main_window
        self.project = project
        self.element_id = element_id
        self.element = (project.elements.get(element_id)
                         if project and element_id is not None else None)

        # MeshCanvas compartido — contenedor donde flotará el overlay y
        # lienzo donde se pintará la capa educativa.
        self._mesh = self._resolve_mesh_canvas(main_window)
        if self._mesh is None:
            raise RuntimeError(
                "No se pudo resolver MeshCanvas — el modo Overlay requiere "
                "que el main_window exponga `mesh_canvas`."
            )

        # Crear el overlay flotante. El parent es el WIDGET FRAME del
        # MeshCanvas, no el tk.Canvas interno; place() funciona mejor sobre
        # el contenedor que ya gestiona el toolbar y el canvas.
        self._overlay = CanvasOverlay(
            self._mesh,
            title=self.TITLE,
            initial_pos=self.OVERLAY_INITIAL_POS,
            on_close=self._cleanup,
            phase=self.PHASE,
            width=self.OVERLAY_WIDTH,
            height=self.OVERLAY_HEIGHT,
        )

        # Capa educativa — bound method que se borrará en _cleanup.
        self._layer = self._draw_layer_wrapper

        # Snapshots de callbacks del canvas para restaurarlos al cerrar.
        self._saved_on_element_select = self._mesh.on_element_select
        self._saved_on_node_select = self._mesh.on_node_select
        self._saved_on_hover_element = self._mesh.on_hover_element

        # Wireamos nuestros handlers (los módulos sobrescriben los que
        # necesitan; la base reroutea hacia métodos overrideables).
        self._mesh.on_element_select = self._handle_element_click
        self._mesh.on_node_select = self._handle_node_click

        # Construir contenido del overlay (template method)
        try:
            self.build_overlay(self._overlay.body)
        except Exception as exc:
            self._show_overlay_error(str(exc))

        # Registrar la capa de dibujo y mostrar el overlay
        self._mesh.add_overlay_layer(self._layer)
        self._overlay.show()

        # Hook adicional para subclases (ej. resaltar elemento inicial)
        try:
            self.on_activated()
        except Exception:
            pass

    # ── Hooks que las subclases sobrescriben ────────────────────────
    def build_overlay(self, body: tk.Widget) -> None:
        """Construir el contenido del overlay flotante."""
        raise NotImplementedError

    def draw_canvas_layer(self, mesh_canvas) -> None:
        """Dibujar la capa educativa sobre el MeshCanvas.

        Se invoca al final de cada `redraw()` del canvas. Usar
        `mesh_canvas.canvas.create_*` con tags propios (prefijo "edu_X")
        para que el siguiente redraw global limpie el dibujo previo.
        """
        return None

    def on_element_selected(self, elem_id: int) -> None:
        """Callback override: el usuario clickeó un elemento en el canvas.

        Default: actualiza self.element_id y llama refresh_overlay().
        """
        self.set_element(elem_id)

    def on_node_selected(self, node_id: int) -> None:
        """Callback override: el usuario clickeó un nodo en el canvas.

        Default: no-op. M8 lo usa para cambiar el nodo del Mohr.
        """
        return None

    def refresh_overlay(self) -> None:
        """Llamado tras cambios de estado (selección, dial, toggle).

        Default: pide redibujar canvas (la capa se re-evalúa). Subclases
        que tienen widgets reactivos en el overlay también deben
        actualizarlos aquí.
        """
        try:
            self._mesh.redraw()
        except Exception:
            pass

    def on_activated(self) -> None:
        """Hook tras inicialización completa (overlay visible + layer
        registrada). Default: no-op."""
        return None

    def on_closed(self) -> None:
        """Hook ANTES de la limpieza estándar. Default: no-op."""
        return None

    # ── API pública ────────────────────────────────────────────────
    def set_element(self, elem_id: Optional[int]) -> None:
        """Cambia el elemento bajo análisis y refresca."""
        if elem_id is None:
            self.element_id = None
            self.element = None
        else:
            self.element_id = elem_id
            self.element = (self.project.elements.get(elem_id)
                             if self.project else None)
        self.refresh_overlay()

    def close(self) -> None:
        """Cierre programático (equivalente a clickear el botón ×)."""
        try:
            self._overlay.close()
        except Exception:
            self._cleanup()

    # ── Internos ───────────────────────────────────────────────────
    def _resolve_mesh_canvas(self, main_window):
        return getattr(main_window, "mesh_canvas", None)

    def _handle_element_click(self, elem_id):
        try:
            self.on_element_selected(elem_id)
        except Exception:
            pass
        # No re-disparar el callback original — el módulo overlay TOMA el
        # control del canvas mientras esté activo. Al cerrar se restauran.

    def _handle_node_click(self, node_id):
        try:
            self.on_node_selected(node_id)
        except Exception:
            pass

    def _draw_layer_wrapper(self, mesh_canvas):
        # Wrapper que aisla excepciones: una capa rota NO bloquea redraw.
        try:
            self.draw_canvas_layer(mesh_canvas)
        except Exception:
            pass

    def _show_overlay_error(self, msg: str) -> None:
        body = self._overlay.body
        for child in body.winfo_children():
            child.destroy()
        lbl = tk.Label(
            body, text=f"⚠ Error al construir el overlay:\n\n{msg}",
            bg="#222233", fg="#ef5350", font=("Segoe UI", 10),
            justify="left", anchor="w", wraplength=400,
        )
        lbl.pack(fill="both", expand=True, padx=10, pady=10)

    def _cleanup(self) -> None:
        # Hook usuario antes de la limpieza estándar
        try:
            self.on_closed()
        except Exception:
            pass

        # Restaurar callbacks del canvas
        try:
            if self._mesh is not None:
                if self._mesh.on_element_select is self._handle_element_click:
                    self._mesh.on_element_select = self._saved_on_element_select
                if self._mesh.on_node_select is self._handle_node_click:
                    self._mesh.on_node_select = self._saved_on_node_select
                # on_hover_element: si el módulo lo sobrescribió, restaurar.
                # Comparamos por identidad: cualquier handler nuestro debe
                # ser un attr del módulo, no el original.
                if (self._mesh.on_hover_element is not None
                        and self._mesh.on_hover_element
                        is not self._saved_on_hover_element):
                    self._mesh.on_hover_element = self._saved_on_hover_element
                # Quitar nuestra capa de dibujo
                self._mesh.remove_overlay_layer(self._layer)
        except Exception:
            pass

        # Liberar slot del singleton
        cls = type(self)
        key = (id(self.main_window), cls)
        _ACTIVE.pop(key, None)


def is_active(main_window, cls) -> bool:
    """Retorna True si el módulo `cls` está activo en este main_window."""
    return (id(main_window), cls) in _ACTIVE


def deactivate_all(main_window) -> None:
    """Cierra todos los módulos overlay activos en este main_window.

    Útil al cambiar de fase, hacer un undo/redo masivo, o cerrar el
    proyecto: garantiza que ningún overlay quede colgado.
    """
    target_id = id(main_window)
    instances = [v for k, v in list(_ACTIVE.items()) if k[0] == target_id]
    for inst in instances:
        try:
            inst.close()
        except Exception:
            pass
