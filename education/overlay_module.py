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

import traceback
from typing import Callable, Optional, Tuple

import tkinter as tk

from gui.widgets.canvas_overlay import CanvasOverlay
from config.settings import EDU_AXES_BG, HEALTH_ERROR_COLOR, OVERLAY_ACCENT_AMBER


# Registry de instancias activas: (id(main_window), cls) -> instance.
# Permite que volver a invocar el mismo módulo lo lleve al frente en
# lugar de duplicarlo. Singleton suave: distintos main_windows pueden
# tener cada uno su instancia.
_ACTIVE: dict = {}

# Listeners notificados cuando `_ACTIVE` cambia (activate / cleanup).
# Cada listener recibe `(main_window, active_module_keys: set[str])` donde
# `active_module_keys` son los `mod_key` resueltos vía el module_launcher
# (p. ej. "mod04"). Usado por el breadcrumb del status bar para iluminar
# el chip del módulo activo.
_OVERLAY_CHANGE_LISTENERS: list = []


def subscribe_overlay_change(callback) -> None:
    """Registra un callback `(main_window, mod_keys)` que se invoca cada
    vez que un módulo overlay se abre o cierra. El callback se llama
    sincronamente desde `activate()` / `_cleanup()` — debe ser barato."""
    if callback not in _OVERLAY_CHANGE_LISTENERS:
        _OVERLAY_CHANGE_LISTENERS.append(callback)


def _notify_overlay_change(main_window) -> None:
    """Notifica a los listeners el estado actual de overlays activos."""
    try:
        from education.module_launcher import MODULE_MAP
    except Exception:
        MODULE_MAP = {}
    target_id = id(main_window) if main_window is not None else None
    active_keys = set()
    for (mw_id, cls), _inst in _ACTIVE.items():
        if mw_id != target_id:
            continue
        for mk, (_mod, cls_name) in MODULE_MAP.items():
            if cls.__name__ == cls_name:
                active_keys.add(mk)
                break
    for cb in list(_OVERLAY_CHANGE_LISTENERS):
        try:
            cb(main_window, active_keys)
        except Exception:
            # Hoy el único listener es el breadcrumb de la barra de estado: si
            # falla mudo, el chip del módulo queda encendido (o apagado) sin
            # relación con lo que está abierto.
            traceback.print_exc()


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
        """Punto de entrada del launcher. Singleton por (main_window, cls).

        Política de overlay único: al abrir un módulo overlay nuevo, se
        cierran AUTOMÁTICAMENTE todos los demás overlays activos en el
        mismo `main_window`. Razón pedagógica: dos overlays superponen
        sus capas en el canvas (p.ej. los vuelos de M7 quedaban marcados
        cuando el alumno abría M4 sin cerrar M7), generando ruido visual
        y confusión sobre "qué módulo está hablando ahora". Convención
        explícita: el alumno explora UN concepto a la vez.

        Reabrir la MISMA clase mantiene la instancia (lift + opcional
        cambio de elemento) — no destruye y recrea innecesariamente.
        """
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

        # Cerrar otros overlays activos en este main_window (convención
        # de overlay único). Iteramos sobre snapshot para que el .close()
        # — que muta `_ACTIVE` vía _cleanup — no rompa el loop.
        target_id = id(main_window)
        others = [(k, v) for k, v in list(_ACTIVE.items())
                  if k[0] == target_id and k[1] is not cls]
        for _k, inst in others:
            try:
                inst.close()
            except Exception:
                # Si el overlay anterior no se cierra, su capa (las trazas de
                # M7, el X-ray de M0) queda dibujada DEBAJO del módulo nuevo —
                # exactamente el ruido visual que la política de overlay único
                # evita. Sin traza era indepurable.
                traceback.print_exc()

        inst = cls(main_window, project, element_id)
        _ACTIVE[key] = inst
        _notify_overlay_change(main_window)
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
        # Guard de traza de la capa: una sola por instancia (ver
        # `_draw_layer_wrapper`).
        self._layer_error_traced = False

        # **API moderna**: el MeshCanvas dispara `on_selection_changed(dict)`
        # cuando cambia cualquier selección. Las legacy `on_element_select`
        # / `on_node_select` (que el código previo intentaba enganchar) están
        # MUERTAS — no las dispara ningún flujo del canvas actual. Por eso
        # los overlays no se actualizaban al clickear otro elemento.
        #
        # Nos encadenamos al callback existente (proc_tab / post_tab / etc.)
        # con un wrapper que primero invoca al previo y después decodifica
        # la selección para reenviar a los hooks per-element/per-node de los
        # módulos. Multi-select silencioso (no propagamos a los hooks — la
        # mayoría de módulos operan sobre UN elemento por convención).
        #
        # Implementación: el wrapper es una CLOSURE (no un bound method),
        # porque necesitamos colgarle el atributo `_overlay_edu_chain` para
        # que `_cleanup` lo identifique en `_cleanup`. Los bound methods en
        # Python NO permiten asignación de atributos (`'method' object has
        # no attribute ...`). Las funciones regulares sí.
        self._prev_selection_cb = self._mesh.on_selection_changed
        self._last_seen_eid: Optional[int] = self.element_id
        self._last_seen_nid: Optional[int] = None
        self._chained_selection_cb = self._make_selection_chain(
            self._prev_selection_cb
        )
        self._mesh.on_selection_changed = self._chained_selection_cb

        # Snapshot del hover callback para restaurarlo al cerrar (algunos
        # módulos como M0 lo sobrescriben en `on_activated`).
        self._saved_on_hover_element = self._mesh.on_hover_element

        # Construir contenido del overlay (template method)
        try:
            self.build_overlay(self._overlay.body)
        except Exception as exc:
            # El alumno ve el cartel; el traceback va a stderr porque `str(exc)`
            # solo no alcanza para ubicar el fallo (el cartel dice "KeyError:
            # 'mod03'" sin una línea).
            traceback.print_exc()
            self._show_overlay_error(str(exc))

        # Registrar la capa de dibujo y mostrar el overlay
        self._mesh.add_overlay_layer(self._layer)
        self._overlay.show()

        # Hook adicional para subclases (ej. resaltar elemento inicial)
        try:
            self.on_activated()
        except Exception:
            # `on_activated` es donde los módulos registran su click consumer,
            # el hover y los loops de animación: si falla mudo, el overlay abre
            # pero NO REACCIONA a nada de lo que haga el alumno en el lienzo
            # (M0 sin hover ni drag, M1/M2/M3 sin snap a nodo/PG).
            traceback.print_exc()

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

    def on_element_deselected(self) -> None:
        """Callback: el usuario deseleccionó TODOS los elementos (Esc,
        click en zona vacía, etc.). Default: limpia self.element/_id y
        refresca — la capa educativa desaparece junto con el contexto.
        Subclases pueden override si necesitan limpiar estado adicional.
        """
        self.set_element(None)

    def on_node_selected(self, node_id: int) -> None:
        """Callback override: el usuario clickeó un nodo en el canvas.

        Default: no-op. Reservado para módulos que operen por-nodo (el ex-M8
        del estado tensional puntual, que lo usaba, fue eliminado en 2026-05;
        el círculo de Mohr vive ahora en el DetailsPanel del Post).
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
            # Sin redraw la capa educativa se queda con el dibujo del estado
            # anterior: el alumno ve el marcador/glow donde ya no corresponde.
            traceback.print_exc()

    def refit_overlay(self) -> None:
        """Re-ajusta el alto del overlay flotante a su contenido actual.

        Llamar cuando el body cambia de tamaño DESPUÉS de `show()` — p.ej.
        al expandir/colapsar un `Expander` de derivación (M0, M5): la
        geometría del Toplevel se fija una sola vez y no crece sola, así que
        el contenido nuevo quedaría recortado. No-op si el overlay no existe
        o no expone `refit` (Toplevels legacy)."""
        ov = getattr(self, "_overlay", None)
        refit = getattr(ov, "refit", None)
        if callable(refit):
            try:
                refit()
            except Exception:
                # El Toplevel borderless no crece solo: sin refit, el contenido
                # que acaba de aparecer (el banner de M0, un expander) empuja y
                # RECORTA lo de abajo, incluido el cross-ref al pie.
                traceback.print_exc()

    def on_activated(self) -> None:
        """Hook tras inicialización completa (overlay visible + layer
        registrada). Default: no-op."""
        return None

    def on_closed(self) -> None:
        """Hook ANTES de la limpieza estándar. Default: no-op."""
        return None

    # ── Helper: cross-ref clickeable al pie del overlay ────────────
    def _pack_crossref(self, parent, target_module_id: Optional[str],
                       text: str, wraplength: int = 480):
        """Pinta una etiqueta `👉 ...` clickeable que abre el módulo
        `target_module_id` reusando el elemento actual.

        Si `target_module_id` es None (caso M7 → "Post-Proceso"), la
        etiqueta queda como label decorativo sin click.
        """
        import ttkbootstrap as ttk_local
        lbl = ttk_local.Label(
            parent, text=text,
            font=("Segoe UI", 9), foreground=OVERLAY_ACCENT_AMBER,
            wraplength=wraplength, justify="left",
        )
        lbl.pack(fill="x", padx=4, pady=(4, 0))
        if target_module_id:
            lbl.configure(cursor="hand2")
            lbl.bind("<Button-1>",
                      lambda _e, t=target_module_id: self._open_crossref(t))
        return lbl

    def _open_crossref(self, target_module_id: str) -> None:
        """Abre otro módulo overlay con el mismo elemento.

        El propio `cls.activate()` del módulo destino cerrará a éste por
        la política de overlay único — no hace falta close() explícito.
        """
        try:
            from education.module_launcher import open_module
            open_module(self.main_window, self.project, target_module_id,
                         mesh_canvas=self._mesh,
                         elem_id=self.element_id)
        except Exception:
            # El `👉 …` del pie es clickeable (cursor hand2): si falla mudo, el
            # alumno clickea y NO PASA NADA. `open_module` ya avisa sus propios
            # casos esperables (sin malla, sin canvas); lo que cae acá es un
            # fallo inesperado y hasta ahora era invisible.
            traceback.print_exc()

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

    def _make_selection_chain(self, prev):
        """Factory que devuelve una closure encadenada al callback `prev`.

        La closure es una función regular (no bound method) para poder
        colgarle el atributo `_overlay_edu_chain` que `_cleanup` usa para
        identificarla. Captura `prev` y `self` por defecto para evitar
        late binding.

        Reglas de "cambio significativo":
          • Single-element selection que difiere del último visto →
            `on_element_selected(eid)`.
          • Single-node selection que difiere del único visto →
            `on_node_selected(nid)`.
          • DESELECCIÓN total de elementos (0 elementos seleccionados,
            habiendo visto uno antes) → `on_element_deselected()`. La
            capa educativa debe desaparecer junto con el chip `#N` del
            panel de módulos — el alumno limpió el contexto.
          • Multi-select: no propagamos a hooks (los módulos operan
            sobre UN elemento; mostrar `N` cosas a la vez confunde).
        """

        def _chained(sel, _prev=prev, _self=self):
            if _prev is not None:
                try:
                    _prev(sel)
                except Exception:
                    # Eslabón previo de la cadena (proc_tab / pre_tab): si falla
                    # mudo, el chip `#N` del panel de módulos y la barra de
                    # estado se quedan con la selección anterior. Misma
                    # convención que proc_tab (sesión 03).
                    traceback.print_exc()

            elems = sel.get("elements", set()) if sel else set()
            nodes = sel.get("nodes", set()) if sel else set()
            eid = next(iter(elems)) if len(elems) == 1 else None
            nid = next(iter(nodes)) if len(nodes) == 1 else None

            if eid is not None and eid != _self._last_seen_eid:
                _self._last_seen_eid = eid
                try:
                    _self.on_element_selected(eid)
                except Exception:
                    # Si el hook falla mudo, el módulo DEJA DE SEGUIR al lienzo:
                    # el alumno clickea otro elemento, el halo se mueve y el
                    # overlay sigue mostrando los números del anterior.
                    traceback.print_exc()
            elif eid is None and not elems and _self._last_seen_eid is not None:
                # Caso deselección explícita (set vacío). Solo propagamos
                # si el último visto era un elemento real — evita disparar
                # `on_element_deselected` por estados intermedios donde el
                # canvas envía un sel vacío justo antes de re-poblar.
                _self._last_seen_eid = None
                try:
                    _self.on_element_deselected()
                except Exception:
                    # Idem: el overlay quedaría mostrando el elemento que el
                    # alumno acaba de deseleccionar.
                    traceback.print_exc()

            if nid is not None and nid != _self._last_seen_nid:
                _self._last_seen_nid = nid
                try:
                    _self.on_node_selected(nid)
                except Exception:
                    traceback.print_exc()

            # Multi-select de elementos o de nodos: solo resetear el
            # "último visto" para que la próxima selección single dispare
            # incluso si vuelve al mismo id. No propagamos a hooks.
            if eid is None and len(elems) > 1:
                _self._last_seen_eid = None
            if nid is None:
                _self._last_seen_nid = None

        _chained._overlay_edu_chain = True
        return _chained

    def _cleanup_child_widgets(self, widget) -> None:
        """Recorre recursivamente los hijos de `widget` y llama `cleanup()`
        en los que lo expongan (duck-typing). Usado para cerrar popups y
        desenganchar bindings de componentes (LatexMatrixImage,
        GaussCoordReadout) que sobreviven al withdraw del overlay."""
        try:
            children = widget.winfo_children()
        except Exception:
            return
        for child in children:
            fn = getattr(child, "cleanup", None)
            if callable(fn):
                try:
                    fn()
                except Exception:
                    # El overlay se cierra con withdraw (no destroy), así que un
                    # `cleanup()` que falla deja el recurso vivo: el caso real es
                    # el ToolTip de `ScrollableMatrixImage`, que queda como
                    # Toplevel huérfano flotando sobre el escritorio.
                    traceback.print_exc()
            self._cleanup_child_widgets(child)

    def _draw_layer_wrapper(self, mesh_canvas):
        # Wrapper que aisla excepciones: una capa rota NO bloquea redraw.
        try:
            self.draw_canvas_layer(mesh_canvas)
        except Exception:
            # Una capa rota dibuja NADA sobre el lienzo y el módulo se ve
            # "desconectado" del modelo (sin glow, sin X-ray, sin marcador).
            # Traza UNA sola vez por instancia: `draw_canvas_layer` corre en
            # cada redraw y M3 lo llama a ~30 fps desde su loop de pulso — sin
            # el guard, un fallo persistente inundaría stderr.
            if not self._layer_error_traced:
                self._layer_error_traced = True
                traceback.print_exc()

    def _show_overlay_error(self, msg: str) -> None:
        body = self._overlay.body
        for child in body.winfo_children():
            child.destroy()
        lbl = tk.Label(
            body, text=f"⚠ Error al construir el overlay:\n\n{msg}",
            bg=EDU_AXES_BG, fg=HEALTH_ERROR_COLOR, font=("Segoe UI", 10),
            justify="left", anchor="w", wraplength=400,
        )
        lbl.pack(fill="both", expand=True, padx=10, pady=10)

    def _cleanup(self) -> None:
        # Hook usuario ANTES de tocar el canvas — el módulo puede querer
        # cancelar after_id pendientes, borrar tags privados, etc.
        try:
            self.on_closed()
        except Exception:
            # `on_closed` es donde los módulos cancelan sus `after` y devuelven
            # el lienzo a su estado: si falla mudo quedan secuelas visibles tras
            # cerrar — M0 deja TODA la malla en modo fantasma gris, M3 deja su
            # loop de pulso repintando a 30 fps sobre un overlay cerrado.
            traceback.print_exc()

        # Cerrar recursos de widgets hijos que sobreviven al withdraw del
        # overlay (popups de zoom de LatexMatrixImage, bindings de
        # GaussCoordReadout, etc.). El overlay se cierra con withdraw — NO
        # destroy —, así que el `<Destroy>` de los widgets no dispara; un
        # popup Toplevel abierto quedaría huérfano. Recorremos el árbol del
        # body y llamamos `cleanup()` en cualquier widget que lo exponga.
        try:
            self._cleanup_child_widgets(self._overlay.body)
        except Exception:
            traceback.print_exc()

        # Restaurar callbacks del canvas
        try:
            if self._mesh is not None:
                # Desencadenar `on_selection_changed`: si nuestro wrapper
                # sigue siendo el callback activo, lo reemplazamos por el
                # previo. Si otro overlay/tab encadenó después de nosotros,
                # el wrapper actual NO es el nuestro — en ese caso no
                # tocamos nada (rompería el chain) y dejamos que el GC
                # eventualmente libere el closure.
                if getattr(self._mesh.on_selection_changed,
                             "_overlay_edu_chain", False) \
                        and self._mesh.on_selection_changed \
                        is self._chained_selection_cb:
                    self._mesh.on_selection_changed = self._prev_selection_cb

                # on_hover_element: si el módulo lo sobrescribió, restaurar.
                if (self._mesh.on_hover_element is not None
                        and self._mesh.on_hover_element
                        is not self._saved_on_hover_element):
                    self._mesh.on_hover_element = self._saved_on_hover_element

                # Quitar nuestra capa de dibujo. `remove_overlay_layer`
                # YA dispara `redraw()` internamente, así que tras esto
                # el canvas queda limpio de items dibujados por nuestra
                # capa. Defensivo extra: forzamos un redraw adicional por
                # si la capa nunca corrió (overlay con error en build).
                self._mesh.remove_overlay_layer(self._layer)
                try:
                    self._mesh.redraw()
                except Exception:
                    pass
        except Exception:
            # Si esta restauración falla, el lienzo queda con NUESTRO eslabón de
            # la cadena de selección y con la capa educativa registrada: un
            # módulo cerrado que sigue dibujando y filtrando clicks. Es el fallo
            # más caro del ciclo de vida y era completamente mudo.
            traceback.print_exc()

        # Liberar slot del singleton
        cls = type(self)
        key = (id(self.main_window), cls)
        _ACTIVE.pop(key, None)
        _notify_overlay_change(self.main_window)


def is_active(main_window, cls) -> bool:
    """Retorna True si el módulo `cls` está activo en este main_window."""
    return (id(main_window), cls) in _ACTIVE


def is_any_overlay_active(main_window) -> bool:
    """Retorna True si CUALQUIER módulo overlay está activo en este
    main_window. Consultado por `MeshCanvas._on_click` para suprimir la
    rama "second-click deselects" mientras hay un módulo abierto — el
    elemento bajo análisis queda pinneado por la duración del módulo."""
    target_id = id(main_window) if main_window is not None else None
    if target_id is None:
        return False
    return any(k[0] == target_id for k in _ACTIVE.keys())


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
