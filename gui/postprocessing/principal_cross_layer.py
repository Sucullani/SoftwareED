"""
PrincipalCrossLayer: capa de cruces principales σ1 / σ2 sobre el MeshCanvas.

Reemplaza al modulo educativo M8 (legacy) -- ahora es una capa de
visualizacion del Post-Proceso que se activa con un checkbutton en la
toolbar. Independiente del probe overlay: ambos pueden coexistir sin
conflicto (la capa solo dibuja, no intercepta eventos del canvas).

Decisiones de diseño:
  - Una cruz por elemento (en su centroide), NO una por nodo. Las cruces
    nodales con promedio entre elementos vecinos saturan visualmente la
    malla; la cruz por elemento es lo que hacia M8 y es lo correcto
    pedagogicamente -- representa el estado promedio del elemento.
  - σ1 (mayor) en azul (traccion), σ2 (menor) en rojo (compresion).
    Convencion clasica de mecanica de medios continuos.
  - Grosor de cada brazo proporcional a |σ_i| / max|σ| del modelo: el
    alumno *ve* donde estan las concentraciones de tension.
  - Sin rotacion interactiva: el campo principal del solver no se rota
    arbitrariamente (la rotacion drag-todo de M8 era visualmente
    impresionante pero pedagogicamente confusa, ¿por que giro yo las
    cruces?). Las cruces son lo que son: campo principal del MEF.

Bibliografía:
  - Timoshenko & Goodier (1970). Theory of Elasticity. §2.3 (Mohr circle
    + direcciones principales).
  - Bathe (2014). Finite Element Procedures. §6.7.4 (campo principal en
    post-proceso).
"""

from __future__ import annotations

import math
from typing import Optional

from config.settings import (
    PRINCIPAL_TENSION_COLOR, PRINCIPAL_COMPRESSION_COLOR,
    PRINCIPAL_CROSS_WIDTH_PX, PRINCIPAL_CROSS_SIZE_FRAC,
)
from fem.probe_query import principal_and_vm


_TAG = "post_principal_crosses"


class PrincipalCrossLayer:
    """Capa de cruces principales σ1/σ2 sobre el MeshCanvas.

    Activada por toggle en toolbar Post. Se registra via
    `mesh_canvas.add_overlay_layer(self.draw)` y se redibuja en cada
    `redraw()` del canvas.

    Uso tipico:
        layer = PrincipalCrossLayer(mesh_canvas, project, nodal_stresses)
        layer.activate()    # registra capa + redraw
        layer.deactivate()  # quita capa + delete del tag
    """

    def __init__(self, mesh_canvas, project, nodal_stresses):
        self.mesh = mesh_canvas
        self.project = project
        self.nodal_stresses = nodal_stresses
        self._active = False
        # Cache de magnitud maxima del modelo (se invalida al re-activate).
        self._max_sigma: Optional[float] = None
        self._model_span: Optional[float] = None
        # Cache por elemento: (cx_world, cy_world, s1, s2, theta_p). Los
        # esfuerzos y el angulo principal no cambian entre redraws (dependen
        # solo de nodal_stresses, fijo tras el solve), asi que se computan
        # UNA vez en _compute_cache. draw() solo proyecta a coords screen.
        self._cross_cache: list = []

    # ── Ciclo de vida ────────────────────────────────────────────────
    def activate(self):
        """Registra la capa y dispara redraw. Idempotente."""
        if self._active:
            return
        self._compute_cache()
        self.mesh.add_overlay_layer(self.draw)
        self._active = True

    def deactivate(self):
        """Quita la capa y limpia el tag del canvas. Idempotente."""
        if not self._active:
            return
        self.mesh.remove_overlay_layer(self.draw)
        try:
            self.mesh.canvas.delete(_TAG)
        except Exception:
            pass
        self._active = False

    def is_active(self) -> bool:
        return self._active

    def update_data(self, project, nodal_stresses):
        """Refresca refs tras un re-solve. Recomputa cache."""
        self.project = project
        self.nodal_stresses = nodal_stresses
        if self._active:
            self._compute_cache()
            self.mesh.redraw()

    # ── Render ───────────────────────────────────────────────────────
    def draw(self, _mesh):
        """Callback registrado en add_overlay_layer. Dibuja todas las
        cruces como create_line con el tag _TAG (se limpia en cada redraw
        global). Consume el cache per-elemento; solo proyecta a screen."""
        canvas = self.mesh.canvas
        if not self._cross_cache:
            return
        max_sigma = self._max_sigma or 1.0
        L_world = (self._model_span or 1.0) * PRINCIPAL_CROSS_SIZE_FRAC
        L_px = L_world * self.mesh.scale

        for cx_world, cy_world, s1, s2, theta_p in self._cross_cache:
            cx, cy = self.mesh.world_to_screen(cx_world, cy_world)

            cos_t = math.cos(theta_p)
            sin_t = math.sin(theta_p)

            # Brazo σ1 (mayor) -- color segun signo
            L1 = L_px * abs(s1) / max_sigma
            color_1 = (PRINCIPAL_TENSION_COLOR if s1 >= 0
                       else PRINCIPAL_COMPRESSION_COLOR)
            canvas.create_line(
                cx - L1 * cos_t, cy + L1 * sin_t,
                cx + L1 * cos_t, cy - L1 * sin_t,
                fill=color_1, width=PRINCIPAL_CROSS_WIDTH_PX,
                capstyle="round", tags=(_TAG,),
            )

            # Brazo σ2 (menor) -- perpendicular
            L2 = L_px * abs(s2) / max_sigma
            color_2 = (PRINCIPAL_TENSION_COLOR if s2 >= 0
                       else PRINCIPAL_COMPRESSION_COLOR)
            canvas.create_line(
                cx + L2 * sin_t, cy + L2 * cos_t,
                cx - L2 * sin_t, cy - L2 * cos_t,
                fill=color_2, width=PRINCIPAL_CROSS_WIDTH_PX,
                capstyle="round", tags=(_TAG,),
            )

    # ── Helpers numericos ────────────────────────────────────────────
    def _avg_stress(self, elem):
        """Promedio nodal de σx, σy, τxy sobre los nodos del elemento.

        Esto representa el "estado promedio" del elemento. Equivalente a
        evaluar σ en el centroide en modo suavizado.
        """
        nids = elem.node_ids
        n_used = 0
        sx = sy = txy = 0.0
        for nid in nids:
            ns = self.nodal_stresses.get(nid)
            if ns is None:
                continue
            sx += ns.get("sigma_x", 0.0)
            sy += ns.get("sigma_y", 0.0)
            txy += ns.get("tau_xy", 0.0)
            n_used += 1
        if n_used == 0:
            return 0.0, 0.0, 0.0
        return sx / n_used, sy / n_used, txy / n_used

    @staticmethod
    def _theta_p(sx, sy, txy):
        """Angulo principal en radianes desde σx, σy, τxy."""
        if abs(sx - sy) + abs(txy) < 1e-12:
            return 0.0
        return 0.5 * math.atan2(2.0 * txy, sx - sy)

    def _element_centroid_world(self, elem):
        """Coords mundo del centroide geometrico del elemento (promedio de
        las 4 esquinas macro). Devuelve (None, None) si falta algun nodo."""
        nids = elem.node_ids[:4]  # solo corners (Q4 o Q9 macro)
        xs = []
        ys = []
        for nid in nids:
            node = self.project.nodes.get(nid)
            if node is None:
                return None, None
            xs.append(node.x)
            ys.append(node.y)
        return sum(xs) / len(xs), sum(ys) / len(ys)

    def _compute_cache(self):
        """Pre-computa span geometrico, max|σ_i| y la geometria + esfuerzos
        por elemento (centroide mundo + σ1/σ2 + θp). Estos no varian entre
        redraws (dependen solo de nodal_stresses, fijo tras el solve), asi
        que draw() se reduce a la proyeccion a screen."""
        xs = [n.x for n in self.project.nodes.values()]
        ys = [n.y for n in self.project.nodes.values()]
        if xs and ys:
            self._model_span = max(
                max(xs) - min(xs), max(ys) - min(ys), 1.0
            )
        else:
            self._model_span = 1.0

        max_sig = 0.0
        if self.nodal_stresses:
            for ns in self.nodal_stresses.values():
                m = max(abs(ns.get("sigma_1", 0.0)),
                        abs(ns.get("sigma_2", 0.0)))
                if m > max_sig:
                    max_sig = m
        self._max_sigma = max_sig if max_sig > 1e-12 else 1.0

        # Cache per-elemento: centroide mundo + esfuerzos principales.
        self._cross_cache = []
        if not self.nodal_stresses:
            return
        for elem in self.project.elements.values():
            cx_world, cy_world = self._element_centroid_world(elem)
            if cx_world is None:
                continue
            sx, sy, txy = self._avg_stress(elem)
            s1, s2, _vm = principal_and_vm(sx, sy, txy)
            theta_p = self._theta_p(sx, sy, txy)
            self._cross_cache.append((cx_world, cy_world, s1, s2, theta_p))
