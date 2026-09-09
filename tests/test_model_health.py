"""
Test del validador de salud (`models/model_health.py`), la unica via de
validacion del modelo (regla dura 16): lo que este archivo NO detecta es
lo que el alumno descubre recien cuando el solucionador falla, con un
mensaje que no nombra la causa.

Casos cubiertos:
- A) Espesor cero  -> error critico (antes: "Modelo sano" + NaN del solver)
- B) Espesor negativo -> error critico (antes: "Modelo sano" y el modelo
     resolvia con TODOS los desplazamientos con el signo invertido)
- C) E <= 0 en un material EN USO -> error critico, y sin el warning de
     unidades encima (dos diagnosticos distintos del mismo numero)
- D) nu fuera de (-1, 0.5) -> error critico; nu = 0.5 en deformacion plana
     nombra la division por (1-2nu) = 0 que rompia con ZeroDivisionError
- E) Un material invalido SIN USO no genera error critico (ya sale como
     UNUSED_MATERIAL): un error debe bloquear algo real
- F) Densidad negativa con gravedad -> error (el peso propio se invierte);
     densidad cero -> sigue siendo warning
- G) Los limites de nu son los mismos en `Material.validate()` y en el
     validador (una sola fuente)
- H) El ejemplo canonico y la Membrana de Cook siguen sanos (sin falsos
     positivos de los chequeos nuevos)
- I) Repeticiones del mismo codigo se colapsan en una tarjeta de resumen,
     y los issues fixables NO se colapsan (perderian su boton Corregir)
- J) Todo codigo emitido tiene hint educativo en EDUCATIONAL_HINTS y, si
     lleva target, un destino que `_on_goto` sabe abrir
- K) Todo codigo tiene recomendacion en el capitulo ⑧ de la Memoria
- L) Ningun mensaje del validador mete simbolos que pdflatex no compila
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config.settings import ANALYSIS_PLANE_STRAIN, ANALYSIS_PLANE_STRESS, ELEMENT_Q4
from models.example_library import (
    load_example_cook_q4, load_example_project, load_example_project_q9,
)
from models.material import POISSON_MAX, POISSON_MIN, Material
from models.mesh_utils import generate_structured_quad_mesh
from models.model_health import (
    HealthCode, HealthIssue, Severity, _MAX_ISSUES_POR_CODIGO,
    _colapsar_repetidos, HealthReport, validate_project,
)


def _codigos(issues):
    return [i.code for i in issues]


# ─── A / B. Espesor ────────────────────────────────────────────────────

def test_espesor_cero_es_error():
    p = load_example_project()
    assert not validate_project(p).has_errors(), "el ejemplo canonico no esta sano"
    for e in p.elements.values():
        e.thickness = 0.0
    report = validate_project(p)
    codes = _codigos(report.errors)
    assert HealthCode.NON_POSITIVE_THICKNESS in codes, codes
    msg = next(i.message for i in report.errors
               if i.code == HealthCode.NON_POSITIVE_THICKNESS)
    assert "espesor" in msg.lower(), msg
    assert "singular" in msg, msg
    print("[OK] A. espesor 0 -> error critico que nombra la causa")


def test_espesor_negativo_es_error_y_nombra_el_signo():
    """El caso peor: el modelo RESUELVE y devuelve todo invertido."""
    import numpy as np
    from fem.solver import solve_system

    p = load_example_project()
    u_ok = solve_system(p)["u"].copy()
    for e in p.elements.values():
        e.thickness = -e.thickness
    u_mal = solve_system(p)["u"]
    assert np.allclose(u_mal, -u_ok), \
        "el espesor negativo ya no invierte el resultado: revisar el test"

    report = validate_project(p)
    issue = next((i for i in report.errors
                  if i.code == HealthCode.NON_POSITIVE_THICKNESS), None)
    assert issue is not None, _codigos(report.errors)
    assert "signo" in issue.message, issue.message
    assert issue.target_kind == "element" and issue.target_id is not None
    print("[OK] B. espesor negativo -> error que avisa del signo invertido")


# ─── C / D / E. Material ───────────────────────────────────────────────

def test_young_no_positivo_es_error_sin_warning_de_unidades():
    p = load_example_project()
    for m in p.materials.values():
        m.E = 0.0
    report = validate_project(p)
    assert HealthCode.NON_POSITIVE_YOUNG in _codigos(report.errors)
    assert HealthCode.SUSPICIOUS_YOUNG_MODULUS not in _codigos(report.warnings), \
        "E = 0 no puede diagnosticarse ademas como problema de unidades"
    # E negativo: mismo error.
    for m in p.materials.values():
        m.E = -200.0
    assert HealthCode.NON_POSITIVE_YOUNG in _codigos(validate_project(p).errors)
    print("[OK] C. E <= 0 -> error critico, sin el warning de unidades encima")


def test_poisson_fuera_de_rango_es_error():
    p = load_example_project()
    p.analysis_type = ANALYSIS_PLANE_STRAIN
    for m in p.materials.values():
        m.nu = POISSON_MAX          # 0.5: incompresible
    report = validate_project(p)
    issue = next((i for i in report.errors
                  if i.code == HealthCode.INVALID_POISSON), None)
    assert issue is not None, _codigos(report.errors)
    assert "1-2nu" in issue.message or "1-2ν" in issue.message, issue.message
    assert issue.target_kind == "material", issue.target_kind

    # Tension plana con nu = 0.6: no divide por cero, pero D deja de ser
    # definida positiva y el resultado no significa nada.
    p.analysis_type = ANALYSIS_PLANE_STRESS
    for m in p.materials.values():
        m.nu = 0.6
    report = validate_project(p)
    assert HealthCode.INVALID_POISSON in _codigos(report.errors)
    print("[OK] D. nu fuera de (-1, 0.5) -> error critico en TP y en DP")


def test_material_invalido_sin_uso_no_es_error():
    """Un error critico tiene que bloquear algo real; un material que no
    usa ningun elemento no entra a D."""
    p = load_example_project()
    p.materials["Goma sin usar"] = Material("Goma sin usar", E=-1.0, nu=0.499)
    report = validate_project(p)
    assert HealthCode.NON_POSITIVE_YOUNG not in _codigos(report.errors), \
        "un material sin asignar no puede bloquear el solve"
    assert HealthCode.UNUSED_MATERIAL in _codigos(report.warnings)
    print("[OK] E. material invalido pero sin uso -> solo UNUSED_MATERIAL")


# ─── F. Densidad y gravedad ────────────────────────────────────────────

def test_densidad_negativa_con_gravedad_es_error():
    p = load_example_project()
    p.include_gravity = True
    for m in p.materials.values():
        m.density = -2400.0
    report = validate_project(p)
    issue = next((i for i in report.errors
                  if i.code == HealthCode.NEGATIVE_DENSITY), None)
    assert issue is not None, _codigos(report.errors)
    assert "invertido" in issue.message or "arriba" in issue.message, issue.message
    assert "nula" not in issue.message, \
        "el mensaje viejo decia que la fuerza era nula: es falso con rho < 0"

    # rho = 0 sigue siendo warning: el resultado es correcto, sin peso propio.
    for m in p.materials.values():
        m.density = 0.0
    report = validate_project(p)
    assert HealthCode.NEGATIVE_DENSITY not in _codigos(report.errors)
    assert HealthCode.GRAVITY_NO_DENSITY in _codigos(report.warnings)

    # Sin gravedad, la densidad no participa de nada: ni error ni warning.
    p.include_gravity = False
    for m in p.materials.values():
        m.density = -2400.0
    report = validate_project(p)
    assert HealthCode.NEGATIVE_DENSITY not in _codigos(report.errors)
    print("[OK] F. rho < 0 con gravedad -> error; rho = 0 -> warning; "
          "sin gravedad -> nada")


# ─── G. Una sola fuente para el rango de nu ────────────────────────────

def test_limites_de_poisson_son_unicos():
    mat = Material("x", E=1.0, nu=POISSON_MAX)
    assert mat.validate(), "Material.validate() dejo pasar nu = POISSON_MAX"
    mat.nu = POISSON_MIN
    assert mat.validate(), "Material.validate() dejo pasar nu = POISSON_MIN"
    mat.nu = 0.3
    assert not mat.validate(), mat.validate()
    print(f"[OK] G. rango de nu unico: ({POISSON_MIN:g}, {POISSON_MAX:g})")


# ─── H. Sin falsos positivos en los modelos del propio programa ────────

def test_ejemplos_del_programa_siguen_sanos():
    nuevos = {HealthCode.NON_POSITIVE_THICKNESS, HealthCode.NON_POSITIVE_YOUNG,
              HealthCode.INVALID_POISSON, HealthCode.NEGATIVE_DENSITY}
    for nombre, cargar in (("canonico Q4", load_example_project),
                           ("canonico Q9", load_example_project_q9),
                           ("Cook Q4", load_example_cook_q4)):
        report = validate_project(cargar())
        emitidos = set(_codigos(report.errors)) & nuevos
        assert not emitidos, f"{nombre}: falso positivo {emitidos}"
        assert not report.has_errors(), \
            f"{nombre}: {_codigos(report.errors)}"
    print("[OK] H. canonico Q4/Q9 y Cook Q4 sin falsos positivos")


# ─── I. Colapso de repeticiones ────────────────────────────────────────

def test_colapso_de_repeticiones():
    p = generate_structured_quad_mesh(
        [(0, 0), (10, 0), (10, 10), (0, 10)], 8, 8,
        element_type=ELEMENT_Q4, material_name="Acero Estructural",
        thickness=1.0, analysis_type=ANALYSIS_PLANE_STRESS,
    )
    assert len(p.elements) == 64
    for e in p.elements.values():
        e.thickness = 0.0
    report = validate_project(p)
    espesor = [i for i in report.errors
               if i.code == HealthCode.NON_POSITIVE_THICKNESS]
    assert len(espesor) == _MAX_ISSUES_POR_CODIGO + 1, len(espesor)
    resumen = espesor[-1]
    assert "54" in resumen.message, resumen.message
    assert resumen.target_kind is None and not resumen.fixable, \
        "el resumen no puede ofrecer botones que no pueden actuar"
    # El resumen queda pegado a las tarjetas que resume, no al final.
    idx = [i for i, it in enumerate(report.errors) if it is resumen][0]
    assert report.errors[idx - 1].code == HealthCode.NON_POSITIVE_THICKNESS
    print(f"[OK] I1. 64 espesores en cero -> {_MAX_ISSUES_POR_CODIGO} "
          f"tarjetas + 1 resumen")


def test_issues_fixables_no_se_colapsan():
    """Cada tarjeta fixable es la unica via de aplicar su 🔧 Corregir."""
    report = HealthReport()
    for nid in range(1, 40):
        report.warnings.append(HealthIssue(
            severity=Severity.WARNING, code=HealthCode.ZERO_NODAL_LOAD,
            message=f"carga {nid}", target_kind="load", target_id=nid,
            fixable=True,
        ))
    _colapsar_repetidos(report)
    assert len(report.warnings) == 39, len(report.warnings)
    print("[OK] I2. los issues con Corregir no se colapsan")


# ─── J. Contrato con la UI del reporte ─────────────────────────────────

def test_todo_codigo_tiene_hint_y_destino():
    from gui.dialogs.health_report_dialog import CODE_ICONS, EDUCATIONAL_HINTS

    codigos = {v for k, v in vars(HealthCode).items()
               if not k.startswith("_") and isinstance(v, str)}
    sin_hint = sorted(c for c in codigos
                      if c != HealthCode.SUMMARY and c not in EDUCATIONAL_HINTS)
    assert not sin_hint, f"codigos sin hint educativo: {sin_hint}"
    sin_icono = sorted(c for c in codigos if c not in CODE_ICONS)
    assert not sin_icono, f"codigos sin icono: {sin_icono}"

    # `_on_goto` solo sabe navegar estos target_kind (el resto lo dice en
    # la barra de estado, pero un boton que no lleva a ningun lado es un
    # boton mudo: ver no-reintroducir.md).
    navegables = {"node", "element", "load", "bc", "surface", "material",
                  "project", None}
    p = load_example_project()
    p.include_gravity = True
    for m in p.materials.values():
        m.E, m.nu, m.density = -1.0, 0.9, -1.0
    for e in p.elements.values():
        e.thickness = -1.0
    for issue in validate_project(p).all_issues():
        assert issue.target_kind in navegables, issue.target_kind
    print("[OK] J. todo codigo tiene hint + icono, y todo target es navegable")


def test_todo_codigo_tiene_recomendacion_en_la_memoria():
    """El capitulo ⑧ de la Memoria imprime una recomendacion por hallazgo.
    Su diccionario se indexa por el string del codigo, asi que un codigo
    nuevo cae en el generico "Revisar el item indicado." sin que nadie se
    entere. `orphan_free_node` llevaba asi desde que se agrego el chequeo.
    """
    from file_io.memoria_calculo import MemoriaCalculo

    codigos = {v for k, v in vars(HealthCode).items()
               if not k.startswith("_") and isinstance(v, str)}
    faltan = sorted(c for c in codigos
                    if c != HealthCode.SUMMARY
                    and c not in MemoriaCalculo._DIAG_RECO)
    assert not faltan, f"codigos sin recomendacion en la Memoria: {faltan}"
    print("[OK] K. todo codigo tiene recomendacion en el capitulo de "
          "diagnostico de la Memoria")


def test_mensajes_del_validador_son_compilables():
    """Los mensajes van tal cual al capitulo ⑧ de la Memoria. pdflatex no
    lee griego ni simbolos matematicos sueltos en modo texto (regla dura
    20): un modelo con gravedad activa y densidad cero traia "ρ·g·V" y
    generaba un .tex que no compilaba."""
    from file_io.memoria_calculo import MemoriaCalculo

    p = load_example_project()
    p.include_gravity = True
    p.analysis_type = ANALYSIS_PLANE_STRAIN
    for m in p.materials.values():
        m.density, m.nu = 0.0, POISSON_MAX
    for e in p.elements.values():
        e.thickness = 0.0
    mensajes = [i.message for i in validate_project(p).all_issues()]
    assert any("ρ" in m or "ν" in m for m in mensajes), \
        "el modelo de prueba ya no ejercita ningun simbolo griego"

    permitidos = set("áéíóúüñÁÉÍÓÚÜÑ¿¡°…")  # los que inputenc utf8 resuelve
    for mensaje in mensajes:
        latex = MemoriaCalculo._texto_validador(mensaje)
        sobran = sorted({c for c in latex
                         if ord(c) > 127 and c not in permitidos})
        assert not sobran, f"sin traducir a LaTeX: {sobran} en «{latex}»"
    print("[OK] L. ningun mensaje del validador mete simbolos que pdflatex "
          "no sabe leer")


if __name__ == "__main__":
    test_espesor_cero_es_error()
    test_espesor_negativo_es_error_y_nombra_el_signo()
    test_young_no_positivo_es_error_sin_warning_de_unidades()
    test_poisson_fuera_de_rango_es_error()
    test_material_invalido_sin_uso_no_es_error()
    test_densidad_negativa_con_gravedad_es_error()
    test_limites_de_poisson_son_unicos()
    test_ejemplos_del_programa_siguen_sanos()
    test_colapso_de_repeticiones()
    test_issues_fixables_no_se_colapsan()
    test_todo_codigo_tiene_hint_y_destino()
    test_todo_codigo_tiene_recomendacion_en_la_memoria()
    test_mensajes_del_validador_son_compilables()
    print("\nTodos los tests del validador de salud pasan.")
