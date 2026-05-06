"""
model_health: Validador de integridad y salud del modelo FEM.

Detecta problemas que afectarian al solver o que indican modelos mal
formados, agrupados por severidad:

- ERROR (criticos): bloquean el solve hasta que el usuario los resuelva
  o decida explicitamente "continuar igual" desde el HealthReportDialog.
  Ejemplos: surface load referenciando un nodo inexistente, elemento sin
  material valido, ningun nodo restringido (K singular), nodo con BC
  pero sin pertenecer a ningun elemento (DOF colgante restringido).

- WARNING (no-criticos): el modelo puede resolverse pero hay algo que
  conviene revisar. Ejemplos: nodo sin elemento pero con carga aplicada
  (la carga no contribuye), materiales definidos sin uso, elementos con
  Jacobiano negativo (CW orientation), cargas de magnitud cero.

- INFO: contadores generales (N nodos, N elementos, DOF totales/libres/
  restringidos). Siempre se generan.

`validate_project(project)` es la entrada principal. Retorna un
HealthReport que agrupa los issues por severidad. La capa de UI (modal,
banner, badge) se encarga de presentar.

Diseño:
- Pure-function: no toca UI ni el modelo. Solo lee project.
- Sin dependencias en GUI: importable desde tests, scripts, etc.
- Cada issue tiene un `code` estable para que la UI pueda mostrar
  iconos, hints o auto-fixes especificos por codigo.

Uso tipico desde post_tab:
    from models.model_health import validate_project, Severity
    report = validate_project(project)
    if report.has_errors():
        HealthReportDialog(parent, report).show()
        if not user_chose_continue:
            return  # cancelar solve
    elif report.warnings:
        post_tab.show_health_banner(report)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─── Severidad ──────────────────────────────────────────────────────────
class Severity:
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# ─── Codigos de issue (estables para UI) ────────────────────────────────
class HealthCode:
    # Errores criticos
    ELEM_NODE_MISSING       = "elem_node_missing"
    ELEM_MATERIAL_MISSING   = "elem_material_missing"
    SURFACE_NODE_MISSING    = "surface_node_missing"
    NO_RESTRAINTS           = "no_restraints"
    INSUFFICIENT_RESTRAINTS = "insufficient_restraints"
    BC_ORPHAN_NODE          = "bc_orphan_node"
    NO_ELEMENTS             = "no_elements"
    DEGENERATE_ELEMENT      = "degenerate_element"
    # Warnings
    LOAD_ORPHAN_NODE        = "load_orphan_node"
    UNUSED_MATERIAL         = "unused_material"
    NEGATIVE_JACOBIAN       = "negative_jacobian"
    ZERO_NODAL_LOAD         = "zero_nodal_load"
    ZERO_SURFACE_LOAD       = "zero_surface_load"
    # Info
    SUMMARY                 = "summary"


@dataclass
class HealthIssue:
    """Un problema detectado en el modelo. La UI usa `code` para decidir
    iconos o auto-fixes; `target_kind` + `target_id` para "ir al item"."""
    severity: str
    code: str
    message: str
    # Tipo del item al que apunta el issue (para que la UI haga "ir al
    # item" y selecciono la fila correspondiente). None si es global.
    target_kind: Optional[str] = None  # "node" | "element" | "load" | "bc" | "surface" | "material"
    target_id: Any = None
    # Si es True, la UI puede ofrecer un boton "Corregir" que aplica
    # un auto-fix conocido (eliminar carga huerfana, eliminar material
    # sin uso, etc.). Falso para problemas que requieren intervencion
    # del usuario (cambiar nodo, agregar elemento, etc.).
    fixable: bool = False
    # Datos extra (e.g. el ID del nodo faltante referenciado por un elem)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthReport:
    """Resultado de la validacion. Acceso semantico via has_errors() /
    counts_by_severity()."""
    errors: List[HealthIssue] = field(default_factory=list)
    warnings: List[HealthIssue] = field(default_factory=list)
    info: List[HealthIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def total(self) -> int:
        return len(self.errors) + len(self.warnings)

    def counts_by_severity(self) -> Dict[str, int]:
        return {
            Severity.ERROR: len(self.errors),
            Severity.WARNING: len(self.warnings),
            Severity.INFO: len(self.info),
        }

    def status_label(self) -> str:
        """Etiqueta corta para el badge de status bar."""
        if self.errors:
            return f"✗ {len(self.errors)} error(es)"
        if self.warnings:
            return f"⚠ {len(self.warnings)} warning(s)"
        return "✓ Modelo sano"

    def all_issues(self) -> List[HealthIssue]:
        """Concatenacion ordenada por severidad."""
        return self.errors + self.warnings + self.info


# ─── Validacion ─────────────────────────────────────────────────────────
def validate_project(project) -> HealthReport:
    """Valida todos los aspectos relevantes del proyecto y retorna el
    HealthReport. No muta nada.
    """
    report = HealthReport()

    # ─── Errores criticos ────────────────────────────────────────────
    _check_no_elements(project, report)
    _check_element_node_refs(project, report)
    _check_element_materials(project, report)
    _check_degenerate_elements(project, report)
    _check_surface_load_refs(project, report)
    _check_restraints(project, report)
    _check_bc_orphan_nodes(project, report)

    # ─── Warnings ────────────────────────────────────────────────────
    _check_load_orphan_nodes(project, report)
    _check_unused_materials(project, report)
    _check_negative_jacobians(project, report)
    _check_zero_loads(project, report)

    # ─── Info ────────────────────────────────────────────────────────
    _add_summary(project, report)

    return report


# ─── Chequeos individuales ─────────────────────────────────────────────

def _check_no_elements(project, report):
    if not project.elements:
        report.errors.append(HealthIssue(
            severity=Severity.ERROR,
            code=HealthCode.NO_ELEMENTS,
            message="El modelo no tiene elementos. Agrega al menos un elemento "
                    "para poder resolver.",
        ))


def _check_element_node_refs(project, report):
    """Cada node_id en elem.node_ids debe existir en project.nodes."""
    for elem in project.elements.values():
        for nid in elem.node_ids:
            if nid not in project.nodes:
                report.errors.append(HealthIssue(
                    severity=Severity.ERROR,
                    code=HealthCode.ELEM_NODE_MISSING,
                    message=f"Elemento {elem.id} referencia el nodo {nid} "
                            f"que no existe.",
                    target_kind="element", target_id=elem.id,
                    extra={"missing_node_id": nid},
                ))


def _check_element_materials(project, report):
    for elem in project.elements.values():
        if elem.material_name not in project.materials:
            report.errors.append(HealthIssue(
                severity=Severity.ERROR,
                code=HealthCode.ELEM_MATERIAL_MISSING,
                message=f"Elemento {elem.id} usa el material "
                        f"\"{elem.material_name}\" que no existe en la "
                        f"libreria.",
                target_kind="element", target_id=elem.id,
                extra={"material_name": elem.material_name},
            ))


def _check_degenerate_elements(project, report):
    """Vertices repetidos (Q4 con menos de 4 distintos)."""
    for elem in project.elements.values():
        verts = elem.node_ids[:4]
        if len(set(verts)) < 4:
            report.errors.append(HealthIssue(
                severity=Severity.ERROR,
                code=HealthCode.DEGENERATE_ELEMENT,
                message=f"Elemento {elem.id} tiene vertices repetidos "
                        f"{verts}. El Jacobiano sera cero o negativo.",
                target_kind="element", target_id=elem.id,
            ))


def _check_surface_load_refs(project, report):
    for i, sl in enumerate(project.surface_loads):
        for label, nid in (("node_start", sl.node_start),
                           ("node_end", sl.node_end)):
            if nid not in project.nodes:
                report.errors.append(HealthIssue(
                    severity=Severity.ERROR,
                    code=HealthCode.SURFACE_NODE_MISSING,
                    message=f"Carga superficial #{i} referencia el nodo "
                            f"{nid} ({label}) que no existe.",
                    target_kind="surface", target_id=i,
                    fixable=True,
                    extra={"missing_node_id": nid, "field": label},
                ))


def _check_restraints(project, report):
    """Chequea que haya suficientes restricciones para que K_red no sea
    singular. Como minimo: 3 DOF restringidos no colineales para suprimir
    los 3 modos de cuerpo rigido en 2D (2 traslaciones + 1 rotacion rigida
    en el plano XY -- aunque los elementos plane stress/strain no tienen
    DOF rotacional, el cuerpo completo puede girar como solido rigido)."""
    if not project.boundary_conditions:
        report.errors.append(HealthIssue(
            severity=Severity.ERROR,
            code=HealthCode.NO_RESTRAINTS,
            message="No hay restricciones definidas. El modelo tendra "
                    "modos de cuerpo rigido y la matriz K reducida sera "
                    "singular.",
        ))
        return
    # Contar DOF totales restringidos
    total_restrained = 0
    for bc in project.boundary_conditions.values():
        if bc.restrain_x:
            total_restrained += 1
        if bc.restrain_y:
            total_restrained += 1
    if total_restrained < 3:
        report.errors.append(HealthIssue(
            severity=Severity.ERROR,
            code=HealthCode.INSUFFICIENT_RESTRAINTS,
            message=f"Solo hay {total_restrained} DOF restringido(s). Se "
                    f"necesitan al menos 3 DOF (2 traslaciones + 1 rotacion "
                    f"rigida en el plano) para suprimir los modos de cuerpo "
                    f"rigido en 2D.",
        ))


def _check_bc_orphan_nodes(project, report):
    """Nodo con BC pero sin elemento que lo referencie -> DOF colgante
    restringido. K_red queda mal condicionada (filas/columnas con cero
    fuera de la diagonal)."""
    nodes_in_elements = set()
    for elem in project.elements.values():
        nodes_in_elements.update(elem.node_ids)
    for nid in project.boundary_conditions:
        if nid not in nodes_in_elements:
            report.errors.append(HealthIssue(
                severity=Severity.ERROR,
                code=HealthCode.BC_ORPHAN_NODE,
                message=f"Nodo {nid} tiene restriccion pero no pertenece "
                        f"a ningun elemento (DOF colgante restringido).",
                target_kind="bc", target_id=nid,
                fixable=True,
            ))


def _check_load_orphan_nodes(project, report):
    """Nodo con carga pero sin elemento -> la carga no entra a F (no hay
    DOFs ensamblados)."""
    nodes_in_elements = set()
    for elem in project.elements.values():
        nodes_in_elements.update(elem.node_ids)
    for nid in project.nodal_loads:
        if nid not in nodes_in_elements:
            report.warnings.append(HealthIssue(
                severity=Severity.WARNING,
                code=HealthCode.LOAD_ORPHAN_NODE,
                message=f"Nodo {nid} tiene carga pero no pertenece a "
                        f"ningun elemento. La carga no contribuye al "
                        f"analisis.",
                target_kind="load", target_id=nid,
                fixable=True,
            ))


def _check_unused_materials(project, report):
    used = {e.material_name for e in project.elements.values()}
    for mat_name in project.materials:
        if mat_name not in used:
            report.warnings.append(HealthIssue(
                severity=Severity.WARNING,
                code=HealthCode.UNUSED_MATERIAL,
                message=f"Material \"{mat_name}\" definido pero no usado "
                        f"por ningun elemento.",
                target_kind="material", target_id=mat_name,
                fixable=True,
            ))


def _check_negative_jacobians(project, report):
    """Chequeo cheap: orientacion CCW via shoelace de los 4 vertices.
    Si el area es negativa, los nodos estan en orden CW -> el Jacobiano
    sera negativo en todos los Gauss points (invertir el orden corrige).
    """
    for elem in project.elements.values():
        verts = elem.node_ids[:4]
        try:
            pts = [project.nodes[nid] for nid in verts]
        except KeyError:
            continue  # ya capturado por _check_element_node_refs
        # Shoelace
        area2 = 0.0
        for i in range(4):
            x1, y1 = pts[i].x, pts[i].y
            x2, y2 = pts[(i + 1) % 4].x, pts[(i + 1) % 4].y
            area2 += x1 * y2 - x2 * y1
        if area2 <= 0:
            report.warnings.append(HealthIssue(
                severity=Severity.WARNING,
                code=HealthCode.NEGATIVE_JACOBIAN,
                message=f"Elemento {elem.id} tiene orientacion CW (area "
                        f"signada {area2/2:.4g}). El Jacobiano sera "
                        f"negativo. Re-ordena los nodos en sentido CCW.",
                target_kind="element", target_id=elem.id,
            ))


def _check_zero_loads(project, report):
    for nid, load in project.nodal_loads.items():
        if abs(load.fx) < 1e-12 and abs(load.fy) < 1e-12:
            report.warnings.append(HealthIssue(
                severity=Severity.WARNING,
                code=HealthCode.ZERO_NODAL_LOAD,
                message=f"Carga en nodo {nid} tiene Fx=Fy=0. Probablemente "
                        f"olvidaste asignar valores.",
                target_kind="load", target_id=nid,
                fixable=True,
            ))
    for i, sl in enumerate(project.surface_loads):
        if abs(sl.q_start) < 1e-12 and abs(sl.q_end) < 1e-12:
            report.warnings.append(HealthIssue(
                severity=Severity.WARNING,
                code=HealthCode.ZERO_SURFACE_LOAD,
                message=f"Carga superficial #{i} tiene q_start=q_end=0. "
                        f"No contribuye al analisis.",
                target_kind="surface", target_id=i,
                fixable=True,
            ))


def _add_summary(project, report):
    """Contadores generales: nodos, elementos, DOF totales/libres/
    restringidos. Siempre se incluyen como info."""
    n_nodes = len(project.nodes)
    n_elements = len(project.elements)
    n_total_dof = 2 * n_nodes
    n_restrained = 0
    for bc in project.boundary_conditions.values():
        if bc.restrain_x:
            n_restrained += 1
        if bc.restrain_y:
            n_restrained += 1
    n_free = n_total_dof - n_restrained
    report.info.append(HealthIssue(
        severity=Severity.INFO,
        code=HealthCode.SUMMARY,
        message=f"{n_nodes} nodos, {n_elements} elementos, {n_total_dof} DOF "
                f"totales ({n_free} libres, {n_restrained} restringidos).",
        extra={
            "n_nodes": n_nodes, "n_elements": n_elements,
            "n_total_dof": n_total_dof, "n_free_dof": n_free,
            "n_restrained_dof": n_restrained,
        },
    ))


# ─── Auto-fixes ─────────────────────────────────────────────────────────
def apply_autofix(project, issue: HealthIssue) -> bool:
    """Aplica un auto-fix conocido al modelo segun el `code` del issue.
    Solo issues con `fixable=True` deberian llegar aqui; igual hacemos
    el routing por code para evitar misuso.

    Retorna True si el fix se aplico, False si el code no tiene auto-fix
    o no se pudo aplicar (item ya no existe, etc.).
    """
    code = issue.code
    if code == HealthCode.LOAD_ORPHAN_NODE:
        nid = issue.target_id
        if nid in project.nodal_loads:
            project.remove_nodal_load(nid)
            return True
    elif code == HealthCode.BC_ORPHAN_NODE:
        nid = issue.target_id
        if nid in project.boundary_conditions:
            project.remove_boundary_condition(nid)
            return True
    elif code == HealthCode.UNUSED_MATERIAL:
        mat_name = issue.target_id
        if mat_name in project.materials:
            del project.materials[mat_name]
            project.is_modified = True
            project.is_solved = False
            return True
    elif code == HealthCode.SURFACE_NODE_MISSING:
        idx = issue.target_id
        if 0 <= idx < len(project.surface_loads):
            del project.surface_loads[idx]
            project.is_modified = True
            project.is_solved = False
            return True
    elif code == HealthCode.ZERO_NODAL_LOAD:
        nid = issue.target_id
        if nid in project.nodal_loads:
            project.remove_nodal_load(nid)
            return True
    elif code == HealthCode.ZERO_SURFACE_LOAD:
        idx = issue.target_id
        if 0 <= idx < len(project.surface_loads):
            del project.surface_loads[idx]
            project.is_modified = True
            project.is_solved = False
            return True
    return False
