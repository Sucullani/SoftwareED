"""
model_health: Validador de integridad y salud del modelo FEM.

Detecta problemas que afectarian al solver o que indican modelos mal
formados, agrupados por severidad:

- ERROR (criticos): bloquean el solve hasta que el usuario los resuelva
  o decida explicitamente "continuar igual" desde el HealthReportDialog.
  Ejemplos: surface load referenciando un nodo inexistente, elemento sin
  material valido, ningun nodo restringido (K singular), nodo con BC
  pero sin pertenecer a ningun elemento (GDL colgante restringido).
  Tambien entran aca los parametros fisicamente imposibles: espesor <= 0,
  E <= 0 y nu fuera de (-1, 0.5). Dos de ellos NO bloquean el solve y por
  eso son los peores: con espesor negativo, y con densidad negativa mas la
  gravedad activa, el modelo resuelve y devuelve numeros PLAUSIBLES Y MAL
  (todo con el signo invertido).

- WARNING (no-criticos): el modelo puede resolverse pero hay algo que
  conviene revisar. Ejemplos: nodo sin elemento pero con carga aplicada
  (la carga no contribuye), materiales definidos sin uso, elementos con
  Jacobiano negativo (CW orientation), cargas de magnitud cero.

- INFO: contadores generales (N nodos, N elementos, GDL totales/libres/
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

from config.settings import ANALYSIS_PLANE_STRAIN, fmt
from models.material import POISSON_MAX, POISSON_MIN


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
    NON_POSITIVE_THICKNESS  = "non_positive_thickness"
    NON_POSITIVE_YOUNG      = "non_positive_young"
    INVALID_POISSON         = "invalid_poisson"
    NEGATIVE_DENSITY        = "negative_density"
    # Warnings
    LOAD_ORPHAN_NODE        = "load_orphan_node"
    ORPHAN_FREE_NODE        = "orphan_free_node"
    UNUSED_MATERIAL         = "unused_material"
    NEGATIVE_JACOBIAN       = "negative_jacobian"
    ZERO_NODAL_LOAD         = "zero_nodal_load"
    ZERO_SURFACE_LOAD       = "zero_surface_load"
    SUSPICIOUS_YOUNG_MODULUS= "suspicious_young_modulus"
    SUSPICIOUS_MODEL_SCALE  = "suspicious_model_scale"
    GRAVITY_NO_DENSITY      = "gravity_no_density"
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

    # Set de nodos en elementos — reutilizado por _check_bc/load_orphan_nodes.
    # Si el proyecto tiene el índice inverso (post iter3) usarlo directamente;
    # sino construirlo (proyectos cargados antes del índice, o tests unitarios).
    n2e = getattr(project, "_node_to_elements", None)
    if n2e is not None:
        # Filtrar los sets vacios: remove_element deja la clave del nodo con
        # un set vacio cuando lo preserva como huerfano. Tomar las claves a
        # secas contaba esos huerfanos como si pertenecieran a un elemento.
        nodes_in_elements: set = {nid for nid, s in n2e.items() if s}
    else:
        nodes_in_elements = set()
        for elem in project.elements.values():
            nodes_in_elements.update(elem.node_ids)

    # Nombres de material en uso: computado una vez y compartido por los
    # cuatro checks que lo necesitan (antes cada uno reconstruia el set).
    used_mat_names = {e.material_name for e in project.elements.values()}

    # ─── Errores criticos ────────────────────────────────────────────
    _check_no_elements(project, report)
    _check_element_node_refs(project, report)
    _check_element_materials(project, report)
    _check_degenerate_elements(project, report)
    _check_element_thickness(project, report)
    _check_material_properties(project, report, used_mat_names)
    _check_surface_load_refs(project, report)
    _check_restraints(project, report)
    _check_bc_orphan_nodes(project, report, nodes_in_elements)
    _check_orphan_free_nodes(project, report, nodes_in_elements)

    # ─── Warnings ────────────────────────────────────────────────────
    _check_load_orphan_nodes(project, report, nodes_in_elements)
    _check_unused_materials(project, report, used_mat_names)
    _check_negative_jacobians(project, report)
    _check_zero_loads(project, report)
    _check_unit_consistency(project, report, used_mat_names)
    _check_gravity_density(project, report, used_mat_names)

    # ─── Info ────────────────────────────────────────────────────────
    _add_summary(project, report)

    _colapsar_repetidos(report)
    return report


# Cuantas tarjetas del mismo codigo se listan una por una antes de resumir
# el resto en una sola. El reporte lo lee el alumno en una lista scrolleable
# (`HealthReportDialog`) y lo imprime el capitulo de diagnostico de la
# Memoria: mil tarjetas identicas no informan mas que diez, y tardan.
_MAX_ISSUES_POR_CODIGO = 10


def _colapsar_repetidos(report):
    """Resume las repeticiones de un mismo codigo dentro de cada severidad.

    Los chequeos que recorren elementos o nodos emiten un issue por item, y
    hay columnas que se editan en masa: pegar 1024 filas con el espesor en
    cero en la tabla de Elementos daba 1024 tarjetas identicas en el reporte
    de salud (y 1024 filas en la tabla de diagnostico de la Memoria). El
    alumno necesita saber *que* pasa y *cuantos* items afecta, no leer mil
    veces la misma frase.

    Solo se colapsan los issues NO fixables: en los que tienen 🔧 Corregir,
    cada tarjeta es la unica via de arreglar ese item y resumirlas seria
    sacarle acciones al alumno.
    """
    for lista in (report.errors, report.warnings):
        vistos: Dict[str, int] = {}
        resultado: List[HealthIssue] = []
        excedente: Dict[str, List[HealthIssue]] = {}
        for issue in lista:
            if issue.fixable:
                resultado.append(issue)
                continue
            n = vistos.get(issue.code, 0) + 1
            vistos[issue.code] = n
            if n <= _MAX_ISSUES_POR_CODIGO:
                resultado.append(issue)
            else:
                excedente.setdefault(issue.code, []).append(issue)
        for code, restantes in excedente.items():
            modelo = restantes[0]
            ids = [i.target_id for i in restantes if i.target_id is not None]
            cola = f" (ids {ids[0]}…{ids[-1]})" if ids else ""
            # El resumen va pegado al ultimo caso listado de SU codigo, no al
            # final de la seccion: si no, queda separado de las tarjetas que
            # resume por los issues de otros chequeos.
            corte = max(i for i, it in enumerate(resultado)
                        if it.code == code) + 1
            resultado.insert(corte, HealthIssue(
                severity=modelo.severity,
                code=code,
                message=(f"…y {len(restantes)} caso(s) más con el mismo "
                         f"problema{cola}. Se listan los primeros "
                         f"{_MAX_ISSUES_POR_CODIGO}."),
                # Sin target: el boton 📍 Ir al item no puede llevar a
                # varios items a la vez, y un boton que no actua es un
                # boton mudo (ver no-reintroducir.md).
                target_kind=None, target_id=None,
                fixable=False,
                extra={"colapsados": len(restantes)},
            ))
        lista[:] = resultado


# ─── Unidades para los mensajes ────────────────────────────────────────
# El alumno lee estos mensajes al lado de las tablas del Pre, que desde
# 2026-09 rotulan `Espesor [mm]` y `E [MPa]`. Un numero suelto en el
# reporte de salud obligaria a ir a buscar en que unidad esta.

def _label_longitud(project) -> str:
    """Sufijo `" mm"` para las magnitudes de longitud, o cadena vacia si
    el sistema de unidades del proyecto no se reconoce (archivo corrupto)."""
    return _sufijo_unidad(project, "longitud")


def _label_esfuerzo(project) -> str:
    """Sufijo `" MPa"` para las magnitudes de esfuerzo (E, sigma)."""
    return _sufijo_unidad(project, "esfuerzo")


def _sufijo_unidad(project, clave) -> str:
    from config.units import UNIT_SYSTEMS

    cfg = UNIT_SYSTEMS.get(getattr(project, "unit_system", None))
    etiqueta = cfg.get(clave) if cfg else None
    return f" {etiqueta}" if etiqueta else ""


# ─── Chequeos individuales ─────────────────────────────────────────────

def _check_no_elements(project, report):
    if not project.elements:
        report.errors.append(HealthIssue(
            severity=Severity.ERROR,
            code=HealthCode.NO_ELEMENTS,
            message="El modelo no tiene elementos. Agregá al menos un elemento "
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
                        f"librería.",
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
                message=f"Elemento {elem.id} tiene vértices repetidos "
                        f"{verts}. El Jacobiano será cero o negativo.",
                target_kind="element", target_id=elem.id,
            ))


def _check_element_thickness(project, report):
    """Espesor <= 0. Los dos casos rompen el calculo, pero de forma muy
    distinta y ninguno se veia:

    - `t = 0`: k_e = 0 para ese elemento. Si son todos, K_red queda
      exactamente singular y el solucionador termina en el ValueError
      generico de `fem/solver.py` ("modelo mal restringido, elemento
      degenerado o E/nu fuera de rango"), que no nombra el espesor porque
      nadie lo estaba mirando.
    - `t < 0`: peor, porque NO falla. k_e cambia de signo entero y el
      modelo resuelve devolviendo TODOS los desplazamientos y tensiones
      con el signo invertido (medido en el ejemplo canonico con t = -0,8:
      |u| maximo identico, 0,0130763, y el signo de cada componente al
      reves). El alumno ve la estructura deformarse hacia el otro lado y
      nada en la pantalla dice por que.

    La tabla de Elementos del Pre-Proceso acepta cualquier numero en la
    columna Espesor (no hay validacion por celda, y no la hay a proposito:
    la validacion del modelo es una sola via, la regla dura 16), y el
    importador CSV/ZIP tampoco valida. Por eso el chequeo va aca.

    Sin tolerancia: el criterio es el signo fisico, no la precision
    numerica. Un espesor legitimamente chico (una lamina de 0,001 mm) es
    valido y no debe disparar el error.
    """
    unidad = _label_longitud(project)
    for elem in project.elements.values():
        t = getattr(elem, "thickness", None)
        if t is None or t > 0:
            continue
        if t == 0:
            detalle = ("El elemento no aporta rigidez (k_e = 0) y la matriz "
                       "K queda singular.")
        else:
            detalle = ("Un espesor negativo invierte el signo de k_e: el "
                       "modelo resuelve igual, pero TODOS los "
                       "desplazamientos y tensiones salen con el signo "
                       "cambiado.")
        report.errors.append(HealthIssue(
            severity=Severity.ERROR,
            code=HealthCode.NON_POSITIVE_THICKNESS,
            message=f"Elemento {elem.id} tiene espesor "
                    f"{fmt(t, 'length')}{unidad}. {detalle}",
            target_kind="element", target_id=elem.id,
            extra={"thickness": t},
        ))


def _check_material_properties(project, report, used_mat_names=None):
    """Propiedades fisicamente invalidas de los materiales EN USO.

    `Material.validate()` ya definia que es un material valido (E > 0,
    POISSON_MIN < nu < POISSON_MAX, densidad >= 0) y el `MaterialDialog`
    lo respeta desde su propia validacion live. Pero ese es solo uno de
    los caminos por los que entra un material: el importador CSV/ZIP
    construye `Material(...)` con lo que venga en la fila, y un `.edufem`
    editado a mano tampoco pasa por el dialogo. El validador de salud es
    la unica via comun a todos (regla dura 16). Los limites de nu salen de
    `models/material.py` — las mismas constantes que usa `validate()` —
    para que no queden dos rangos que puedan divergir.

    Solo se evaluan los materiales asignados a algun elemento: son los que
    entran a D y por lo tanto los que rompen el solve. Un material invalido
    guardado en la libreria y sin usar ya sale como `UNUSED_MATERIAL`.

    Medido en el ejemplo canonico: con E = 0 el solucionador termina en el
    ValueError generico de NaN; con nu = 0.5 en deformacion plana el factor
    E/((1+nu)(1-2nu)) divide por cero y sube un `ZeroDivisionError` crudo,
    que el alumno ve como "Error inesperado".
    """
    names = (used_mat_names if used_mat_names is not None
             else {e.material_name for e in project.elements.values()})
    unidad_sigma = _label_esfuerzo(project)
    for name in sorted(n for n in names if n):
        mat = project.materials.get(name)
        if mat is None:
            continue  # ya lo reporta _check_element_materials
        if mat.E <= 0:
            report.errors.append(HealthIssue(
                severity=Severity.ERROR,
                code=HealthCode.NON_POSITIVE_YOUNG,
                message=f"Material \"{name}\" tiene E = "
                        f"{fmt(mat.E, 'stress')}{unidad_sigma}. El módulo "
                        f"de Young debe ser mayor que cero: con E ≤ 0 la "
                        f"matriz D no representa ningún sólido y K queda "
                        f"singular o con rigidez negativa.",
                target_kind="material", target_id=name,
                extra={"E": mat.E},
            ))
        if not (POISSON_MIN < mat.nu < POISSON_MAX):
            if (mat.nu == POISSON_MAX
                    and project.analysis_type == ANALYSIS_PLANE_STRAIN):
                detalle = ("En deformación plana el factor "
                           "E/((1+ν)(1-2ν)) divide por (1-2ν) = 0: el "
                           "material es incompresible y D no existe.")
            else:
                detalle = (f"El coeficiente de Poisson de un material "
                           f"isótropo vive en ({POISSON_MIN:g}, "
                           f"{POISSON_MAX:g}); fuera de ese intervalo D "
                           f"deja de ser definida positiva y el resultado "
                           f"no tiene sentido físico.")
            report.errors.append(HealthIssue(
                severity=Severity.ERROR,
                code=HealthCode.INVALID_POISSON,
                message=f"Material \"{name}\" tiene ν = {mat.nu:g}. "
                        f"{detalle}",
                target_kind="material", target_id=name,
                extra={"nu": mat.nu},
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
                    # `ref` permite que el autofix borre ESTA carga aunque el
                    # indice posicional haya cambiado por un fix anterior.
                    extra={"missing_node_id": nid, "field": label, "ref": sl},
                ))


def _check_restraints(project, report):
    """Chequea que haya suficientes restricciones para que K_red no sea
    singular. Como minimo: 3 GDL restringidos no colineales para suprimir
    los 3 modos de cuerpo rigido en 2D (2 traslaciones + 1 rotacion rigida
    en el plano XY -- aunque los elementos plane stress/strain no tienen
    GDL rotacional, el cuerpo completo puede girar como solido rigido)."""
    if not project.boundary_conditions:
        report.errors.append(HealthIssue(
            severity=Severity.ERROR,
            code=HealthCode.NO_RESTRAINTS,
            message="No hay restricciones definidas. El modelo tendrá "
                    "modos de cuerpo rígido y la matriz K reducida será "
                    "singular.",
        ))
        return
    # Contar GDL totales restringidos
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
            message=f"Solo hay {total_restrained} GDL restringido(s). Se "
                    f"necesitan al menos 3 GDL (2 traslaciones + 1 rotación "
                    f"rígida en el plano) para suprimir los modos de cuerpo "
                    f"rígido en 2D.",
        ))


def _check_bc_orphan_nodes(project, report, nodes_in_elements=None):
    """Nodo con BC pero sin elemento que lo referencie -> GDL colgante
    restringido. K_red queda mal condicionada (filas/columnas con cero
    fuera de la diagonal)."""
    if nodes_in_elements is None:
        nodes_in_elements = {nid for elem in project.elements.values()
                             for nid in elem.node_ids}
    for nid in project.boundary_conditions:
        if nid not in nodes_in_elements:
            report.errors.append(HealthIssue(
                severity=Severity.ERROR,
                code=HealthCode.BC_ORPHAN_NODE,
                message=f"Nodo {nid} tiene restricción pero no pertenece "
                        f"a ningún elemento (GDL colgante restringido).",
                target_kind="bc", target_id=nid,
                fixable=True,
            ))


def _check_load_orphan_nodes(project, report, nodes_in_elements=None):
    """Nodo con carga pero sin elemento -> la carga no entra a F (no hay
    GDLs ensamblados)."""
    if nodes_in_elements is None:
        nodes_in_elements = {nid for elem in project.elements.values()
                             for nid in elem.node_ids}
    for nid in project.nodal_loads:
        if nid not in nodes_in_elements:
            report.warnings.append(HealthIssue(
                severity=Severity.WARNING,
                code=HealthCode.LOAD_ORPHAN_NODE,
                message=f"Nodo {nid} tiene carga pero no pertenece a "
                        f"ningún elemento: la carga SÍ entra al vector F, "
                        f"pero el nodo no aporta rigidez y el sistema queda "
                        f"singular.",
                target_kind="load", target_id=nid,
                fixable=True,
            ))


def _check_orphan_free_nodes(project, report, nodes_in_elements=None):
    """Nodo que no pertenece a ningun elemento y no esta totalmente
    restringido: aporta dos filas y columnas nulas a K, asi que el sistema
    reducido queda singular y el solve falla con un error generico de NaN.
    El validador lo daba por sano porque ningun check miraba este caso.
    """
    if nodes_in_elements is None:
        nodes_in_elements = {nid for elem in project.elements.values()
                             for nid in elem.node_ids}
    for nid in project.nodes:
        if nid in nodes_in_elements:
            continue
        bc = project.boundary_conditions.get(nid)
        if bc is not None and bc.restrain_x and bc.restrain_y:
            # Ambos GDL restringidos: salen del sistema reducido, no hay
            # singularidad. El nodo queda inerte pero es inofensivo.
            continue
        report.errors.append(HealthIssue(
            severity=Severity.ERROR,
            code=HealthCode.ORPHAN_FREE_NODE,
            message=f"Nodo {nid} no pertenece a ningún elemento y tiene GDL "
                    f"libres: aporta filas nulas a K y el sistema queda "
                    f"singular.",
            target_kind="node", target_id=nid,
            fixable=True,
        ))


def _check_unused_materials(project, report, used_mat_names=None):
    used = (used_mat_names if used_mat_names is not None
            else {e.material_name for e in project.elements.values()})
    for mat_name in project.materials:
        if mat_name not in used:
            report.warnings.append(HealthIssue(
                severity=Severity.WARNING,
                code=HealthCode.UNUSED_MATERIAL,
                message=f"Material \"{mat_name}\" definido pero no usado "
                        f"por ningún elemento.",
                target_kind="material", target_id=mat_name,
                fixable=True,
            ))


def _check_negative_jacobians(project, report):
    """Chequeo cheap: orientacion CCW via shoelace de los 4 vertices.
    Si el area es negativa, los nodos estan en orden CW -> el Jacobiano
    sera negativo en todos los Gauss points (invertir el orden corrige).
    """
    nodes = project.nodes
    for elem in project.elements.values():
        verts = elem.node_ids[:4]
        try:
            pts = [nodes[nid] for nid in verts]
        except KeyError:
            continue  # ya capturado por _check_element_node_refs
        # Shoelace inline — evita overhead de llamada a funcion auxiliar.
        p0, p1, p2, p3 = pts
        area2 = (p0.x * p1.y - p1.x * p0.y
               + p1.x * p2.y - p2.x * p1.y
               + p2.x * p3.y - p3.x * p2.y
               + p3.x * p0.y - p0.x * p3.y)
        if area2 <= 0:
            report.warnings.append(HealthIssue(
                severity=Severity.WARNING,
                code=HealthCode.NEGATIVE_JACOBIAN,
                message=f"Elemento {elem.id} tiene orientación CW (área "
                        f"signada {area2/2:.4g}). El Jacobiano será "
                        f"negativo. Reordená los nodos en sentido "
                        f"antihorario (CCW).",
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
                        f"No contribuye al análisis.",
                target_kind="surface", target_id=i,
                fixable=True,
                extra={"ref": sl},
            ))


# ─── Heuristicas de consistencia de unidades ─────────────────────────
# Rango fisico tipico (en SI base): E del orden 1 GPa a 200 GPa cubre
# desde maderas hasta aceros estructurales. Modelos tipicos miden entre
# 1 mm y 1 km (escala lab -> obra de ingenieria). Fuera de eso → warning,
# probable error de unidades.
_E_TYPICAL_MIN_PA = 1.0e8   # 100 MPa (madera blanda, casos limite)
_E_TYPICAL_MAX_PA = 5.0e11  # 500 GPa (cubre incluso ceramicas duras)
_MODEL_SCALE_MIN_M = 1.0e-4  # 0.1 mm
_MODEL_SCALE_MAX_M = 1.0e4   # 10 km


def _check_unit_consistency(project, report, used_mat_names=None):
    """Heuristicas de orden de magnitud para detectar mismatch entre los
    numeros del modelo y el sistema de unidades activo. Skip si el sistema
    no se encuentra en UNIT_SYSTEMS (caso extremo: archivo corrupto).
    """
    from config.units import UNIT_SYSTEMS, _STRESS_TO_PA, _LENGTH_TO_M

    cfg = UNIT_SYSTEMS.get(project.unit_system)
    if cfg is None:
        return
    stress_label = cfg.get("esfuerzo")
    length_label = cfg.get("longitud")
    stress_factor = _STRESS_TO_PA.get(stress_label) if stress_label else None
    length_factor = _LENGTH_TO_M.get(length_label) if length_label else None

    # ─── E de materiales en uso ─────────────────────────────────────
    if stress_factor is not None and project.materials:
        names = (used_mat_names if used_mat_names is not None
                 else {e.material_name for e in project.elements.values()})
        used_mat_names = {n for n in names if n}
        for name, mat in project.materials.items():
            if used_mat_names and name not in used_mat_names:
                continue  # solo evaluar materiales asignados
            if mat.E <= 0:
                # `_check_material_properties` ya lo reporta como error
                # critico y nombra la causa real. Repetirlo aca como
                # "¿las unidades son las correctas?" da un segundo
                # diagnostico, distinto y equivocado, del mismo numero.
                continue
            E_pa = mat.E * stress_factor
            if E_pa < _E_TYPICAL_MIN_PA or E_pa > _E_TYPICAL_MAX_PA:
                expected_in_unit = (
                    f"{_E_TYPICAL_MIN_PA / stress_factor:.3g} - "
                    f"{_E_TYPICAL_MAX_PA / stress_factor:.3g} {stress_label}"
                )
                report.warnings.append(HealthIssue(
                    severity=Severity.WARNING,
                    code=HealthCode.SUSPICIOUS_YOUNG_MODULUS,
                    message=(f"Material '{name}': E = {mat.E:g} {stress_label} "
                             f"está fuera del rango físico típico "
                             f"({expected_in_unit}). ¿Las unidades son las "
                             f"correctas?"),
                    target_kind="material", target_id=name,
                    fixable=False,
                    extra={"E_pa": E_pa, "expected_unit": stress_label},
                ))

    # ─── Escala del modelo ──────────────────────────────────────────
    if length_factor is not None and project.nodes:
        xs = [n.x for n in project.nodes.values()]
        ys = [n.y for n in project.nodes.values()]
        span_x = max(xs) - min(xs) if xs else 0.0
        span_y = max(ys) - min(ys) if ys else 0.0
        max_span = max(span_x, span_y)
        if max_span > 0:
            span_m = max_span * length_factor
            if span_m < _MODEL_SCALE_MIN_M or span_m > _MODEL_SCALE_MAX_M:
                report.warnings.append(HealthIssue(
                    severity=Severity.WARNING,
                    code=HealthCode.SUSPICIOUS_MODEL_SCALE,
                    message=(f"Extensión del modelo: {max_span:g} {length_label} "
                             f"(= {span_m:.3g} m). Está fuera del rango habitual "
                             f"(0.1 mm a 10 km). ¿La unidad de longitud es la "
                             f"correcta?"),
                    target_kind="project", target_id=None,
                    fixable=False,
                    extra={"span_m": span_m, "expected_unit": length_label},
                ))


def _check_gravity_density(project, report, used_mat_names=None):
    """Si gravedad esta activa, verificar la densidad de los materiales en
    uso. Dos casos distintos, que antes compartian un unico mensaje:

    - `rho = 0`: F = rho*g*V = 0. La gravedad esta prendida y no hace
      nada. Es un warning: el resultado es correcto, solo que sin peso
      propio.
    - `rho < 0`: F apunta al REVES. El peso propio empuja hacia arriba y
      el modelo resuelve sin quejarse. El mensaje viejo decia que la
      fuerza "sera nula", que es falso justo en el caso peor, asi que el
      alumno leia un diagnostico equivocado. Va como error critico, igual
      que el espesor negativo: son los dos casos en que el programa
      devuelve numeros plausibles y mal.
    """
    if not project.include_gravity:
        return
    names = (used_mat_names if used_mat_names is not None
             else {e.material_name for e in project.elements.values()})
    for name in sorted(n for n in names if n):
        mat = project.materials.get(name)
        if mat is None:
            continue
        rho = getattr(mat, "density", 0)
        if rho < 0:
            report.errors.append(HealthIssue(
                severity=Severity.ERROR,
                code=HealthCode.NEGATIVE_DENSITY,
                message=(f"Gravedad activa y el material \"{name}\" tiene "
                         f"densidad = {rho:g}, negativa. El peso propio "
                         f"F = ρ·g·V queda invertido: el modelo resuelve "
                         f"igual, pero empujado hacia arriba."),
                target_kind="material", target_id=name,
                fixable=False,
                extra={"density": rho},
            ))
        elif rho == 0:
            report.warnings.append(HealthIssue(
                severity=Severity.WARNING,
                code=HealthCode.GRAVITY_NO_DENSITY,
                message=(f"Gravedad activa pero el material '{name}' tiene "
                         f"densidad = {rho:g}. La fuerza volumétrica "
                         f"F = ρ·g·V sera nula."),
                target_kind="material", target_id=name,
                fixable=False,
            ))


def _add_summary(project, report):
    """Contadores generales: nodos, elementos, GDL totales/libres/
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
        message=f"{n_nodes} nodos, {n_elements} elementos, {n_total_dof} GDL "
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
    elif code == HealthCode.ORPHAN_FREE_NODE:
        nid = issue.target_id
        if nid in project.nodes:
            project.remove_node_with_cascade(nid)
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
        return _remove_surface_load(project, issue)
    elif code == HealthCode.ZERO_NODAL_LOAD:
        nid = issue.target_id
        if nid in project.nodal_loads:
            project.remove_nodal_load(nid)
            return True
    elif code == HealthCode.ZERO_SURFACE_LOAD:
        return _remove_surface_load(project, issue)
    return False


def _remove_surface_load(project, issue) -> bool:
    """Borra la carga superficial del issue por IDENTIDAD de objeto.

    Usar el indice posicional (`issue.target_id`) rompe en cuanto se aplica
    mas de un autofix sobre la misma lista: el segundo click borraba la carga
    equivocada o era un no-op silencioso. El indice queda solo como fallback
    para issues construidos a mano (tests).
    """
    ref = issue.extra.get("ref") if issue.extra else None
    pos = None
    if ref is not None:
        for i, sl in enumerate(project.surface_loads):
            if sl is ref:
                pos = i
                break
    if pos is None:
        idx = issue.target_id
        if isinstance(idx, int) and 0 <= idx < len(project.surface_loads):
            pos = idx
    if pos is None:
        return False
    del project.surface_loads[pos]
    project.is_modified = True
    project.is_solved = False
    return True
