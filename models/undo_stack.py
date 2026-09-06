"""
UndoStack: snapshot-based undo/redo para EduFEM.

Apoyado en `ProjectModel.to_dict` / `from_dict` que ya existen y serializan
el estado completo del modelo (geometria + cargas + BCs + materiales +
analysis_type + element_type + unidades + gravedad). Crucialmente, esos
metodos NO incluyen los resultados de la solucion (`displacements`,
`stresses`, `K`, `F`, `is_solved`), asi que los snapshots son livianos
(~5-50 KB tipicos para modelos educativos).

Diseño:
- Stack-based: dos colas FIFO con tope (`_undo` y `_redo`), profundidad
  por defecto 50.
- Captura explicita: el caller invoca `capture(label)` ANTES de cada
  accion mutadora del usuario. Una accion = un snapshot, sin importar
  cuantas mutaciones internas dispara (paste de N filas, expansion
  Q4->Q9, cleanup en cascada al borrar elementos, etc.).
- Sin command pattern: para el dominio educativo, snapshots son simples
  y mas robustos que tener N clases de comandos con su `do/undo`.
- Sin decorador automatico: la captura explicita hace explicito *que*
  es una accion del usuario vs. consecuencia interna.

Listeners (`on_state_restored`):
- Solo se invocan en `undo()` y `redo()`, NO en `capture()`.
- MainWindow registra un callback que limpia state derivado (solucion
  cacheada, pending lock, highlights) y refresca toda la UI.
"""

from collections import deque
from typing import Callable, List, Optional


class UndoStack:
    """Stack de snapshots para undo/redo. Pure model, sin UI."""

    def __init__(self, project, max_depth: int = 50):
        self.project = project
        self.max_depth = int(max_depth)
        # deque con maxlen descarta automaticamente el mas viejo al pasar
        # el tope. Comportamiento estandar para undo stacks.
        self._undo: deque = deque(maxlen=self.max_depth)
        self._redo: deque = deque(maxlen=self.max_depth)
        # Listeners notificados tras un undo/redo exitoso. La firma de
        # los callbacks es `()` (sin argumentos) -- ya tienen acceso al
        # project via captura.
        self.on_state_restored: List[Callable[[], None]] = []

    # ─── API publica ────────────────────────────────────────────────

    def capture(self, label: Optional[str] = None) -> None:
        """Toma un snapshot del estado actual y lo agrega al stack de
        undo. Limpia el stack de redo (estandar: una nueva accion
        invalida el redo path).

        Llamar ANTES de la mutacion: el snapshot representa el estado
        *previo* a la accion del usuario, que es lo que `undo()` debe
        restaurar.
        """
        snap = self.project.to_dict()
        self._undo.append({"snap": snap, "label": label or ""})
        self._redo.clear()

    def undo(self) -> Optional[str]:
        """Restaura el snapshot mas reciente del stack de undo. El estado
        actual se empuja al stack de redo antes de restaurar.

        Retorna el `label` del snapshot restaurado (string), o `None`
        si no hay nada para deshacer.
        """
        if not self._undo:
            return None
        # Snapshot del estado actual -> redo
        current_snap = self.project.to_dict()
        entry = self._undo.pop()
        self._redo.append({"snap": current_snap, "label": entry["label"]})
        # Restaurar
        self.project.restore_from_dict(entry["snap"])
        self._notify_restored()
        return entry["label"]

    def redo(self) -> Optional[str]:
        """Inverso de `undo`. Restaura el snapshot mas reciente del stack
        de redo. El estado actual se empuja al stack de undo antes de
        restaurar.

        Retorna el `label` del snapshot restaurado, o `None` si no hay
        nada para rehacer.
        """
        if not self._redo:
            return None
        current_snap = self.project.to_dict()
        entry = self._redo.pop()
        self._undo.append({"snap": current_snap, "label": entry["label"]})
        self.project.restore_from_dict(entry["snap"])
        self._notify_restored()
        return entry["label"]

    def can_undo(self) -> bool:
        return len(self._undo) > 0

    def can_redo(self) -> bool:
        return len(self._redo) > 0

    def clear(self) -> None:
        """Vacia ambos stacks. Llamar tras File>New, File>Open,
        Cargar Ejemplo, o import_model en modo replace -- el estado
        anterior ya no es accesible logicamente."""
        self._undo.clear()
        self._redo.clear()

    def set_project(self, project) -> None:
        """Reasigna el project que el stack opera sobre. Usado cuando
        MainWindow reemplaza `self.project` por un objeto nuevo (load
        example, open file). Limpia ambos stacks porque el estado del
        project anterior ya no es accesible.
        """
        self.project = project
        self.clear()

    def depth(self) -> tuple:
        """Retorna (undo_count, redo_count). Util para debugging y para
        UI que muestre profundidad disponible."""
        return (len(self._undo), len(self._redo))

    # ─── Internals ──────────────────────────────────────────────────

    def _notify_restored(self) -> None:
        """Dispara los listeners. Errores en un listener no bloquean
        a los demas (el undo/redo en si ya se ejecuto)."""
        for cb in self.on_state_restored:
            try:
                cb()
            except Exception:
                # No interrumpir al resto de listeners, pero dejar rastro: un
                # bug en _on_state_restored desincroniza la UI y sin traza es
                # invisible (se manifiesta mucho despues como estado raro).
                import traceback
                traceback.print_exc()
