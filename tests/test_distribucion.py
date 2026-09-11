"""
Tests del contrato de distribucion: instalador, ejecutable y arranque.

El instalador (`installer/EduFEM.iss`) y la aplicacion comparten datos que
NO se pueden derivar el uno del otro y estan escritos dos veces. Cuando se
desincronizan, nada falla al compilar: falla en la maquina del alumno, y de
formas dificiles de atribuir (el icono anclado a la barra de tareas se
desprende, el doble clic sobre un `.edufem` abre el programa vacio, el
asistente copia sobre un `.exe` en uso). Estos tests son el guard.

Que cubre:
  - `APP_VERSION` sigue siendo legible por el preprocesador del `.iss`, que
    la busca al principio de la linea y entre comillas dobles.
  - El AppUserModelID y el nombre del mutex del `.iss` son los mismos que
    los de `config/settings.py`.
  - `main.py` acepta la ruta que le pasa la asociacion de archivos, ignora
    las opciones y no se cae con una ruta inexistente.
  - `MainWindow` recibe ese proyecto y lo agenda para abrirlo.
  - Los archivos que el `.iss` instala existen en el repo (menos los que
    genera el build: `dist/EduFEM/` y `vendor/texlive`).
  - El `.iss` copia la carpeta onedir completa y `build.spec` la produce.
  - Todo `filedialog` declara `initialdir`: sin eso Tk los abre en el
    directorio de trabajo, que en la aplicacion instalada es la carpeta del
    programa.
  - El `.iss` esta guardado en UTF-8 con BOM (sin el, Inno lo lee como ANSI
    y los acentos de los mensajes salen rotos).

Corre sin pantalla: `python -m tests.test_distribucion`.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import inspect
import os
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import main as main_mod                                        # noqa: E402
from config import settings                                    # noqa: E402
from gui.main_window import MainWindow                          # noqa: E402

ISS = RAIZ / "installer" / "EduFEM.iss"


def _texto_iss() -> str:
    return ISS.read_text(encoding="utf-8-sig")


def _define(nombre: str) -> str:
    """Valor de un `#define nombre "valor"` del .iss."""
    m = re.search(rf'^#define\s+{nombre}\s+"([^"]*)"', _texto_iss(), re.MULTILINE)
    assert m, f"el .iss no define {nombre}"
    return m.group(1)


def _expandir(texto: str) -> str:
    """Sustituye las macros `{#Nombre}` por su `#define`. Es lo minimo que
    hace el preprocesador de Inno y alcanza para verificar rutas."""
    def _reemplazo(m):
        try:
            return _define(m.group(1))
        except AssertionError:
            return m.group(0)
    return re.sub(r"\{#(\w+)\}", _reemplazo, texto)


# ── 1. la version, leida como la lee Inno ────────────────────────────

def test_la_version_sigue_siendo_legible_para_el_instalador():
    """El .iss recorre config/settings.py y toma la primera linea que
    EMPIEZA con APP_VERSION, quedandose con lo que hay entre comillas. Si
    la asignacion se indenta o pasa a comillas simples, el build aborta."""
    fuente = (RAIZ / "config" / "settings.py").read_text(encoding="utf-8")
    encontradas = [ln for ln in fuente.splitlines() if ln.startswith("APP_VERSION")]
    assert len(encontradas) == 1, (
        f"se esperaba una sola asignacion APP_VERSION en columna 1, hay {len(encontradas)}"
    )
    linea = encontradas[0]
    assert '"' in linea, f"APP_VERSION debe usar comillas dobles: {linea!r}"
    valor = linea.split('"')[1]
    assert valor == settings.APP_VERSION, (
        f"el .iss leeria {valor!r} y la app usa {settings.APP_VERSION!r}"
    )
    assert re.fullmatch(r"\d+\.\d+\.\d+", valor), (
        f"VersionInfoVersion necesita numeros separados por puntos: {valor!r}"
    )
    print(f"[OK] el instalador leera la version {valor} de config/settings.py")


# ── 2. identificadores compartidos con Windows ───────────────────────

def test_el_appusermodelid_del_instalador_es_el_que_fija_la_app():
    """Los accesos directos lo declaran y el proceso lo fija. Si difieren,
    Windows trata a la ventana como otra aplicacion y el icono anclado
    deja de corresponder al acceso directo."""
    assert _define("MyAppUserModelId") == settings.APP_USER_MODEL_ID, (
        f"el .iss dice {_define('MyAppUserModelId')!r} y settings.py "
        f"{settings.APP_USER_MODEL_ID!r}"
    )
    print("[OK] AppUserModelID coincide entre el .iss y config/settings.py")


def test_el_mutex_del_instalador_es_el_que_crea_main():
    """`AppMutex` es lo que le permite al asistente ver que EduFEM esta
    abierto. Con otro nombre, el instalador copia sobre un .exe en uso."""
    assert _define("MyAppMutex") == settings.APP_MUTEX_NAME, (
        f"el .iss dice {_define('MyAppMutex')!r} y settings.py "
        f"{settings.APP_MUTEX_NAME!r}"
    )
    fuente = inspect.getsource(main_mod)
    assert "APP_MUTEX_NAME" in fuente and "CreateMutexW" in fuente, (
        "main.py dejo de crear el mutex nombrado que el instalador consulta"
    )
    print("[OK] el mutex coincide y main.py sigue creandolo")


def test_la_extension_asociada_es_la_del_modelo():
    assert _define("ProjExt") == settings.PROJECT_FILE_EXTENSION, (
        f"el .iss asocia {_define('ProjExt')!r} y los proyectos se guardan "
        f"como {settings.PROJECT_FILE_EXTENSION!r}"
    )
    print(f"[OK] el instalador asocia {_define('ProjExt')}")


# ── 3. el argumento que llega del doble clic ─────────────────────────

def test_el_argumento_de_la_asociacion_llega_como_proyecto(tmp=None):
    """`shell\\open\\command` del registro invoca `EduFEM.exe "%1"`."""
    import tempfile
    with tempfile.TemporaryDirectory() as carpeta:
        proyecto = os.path.join(carpeta, "modelo" + settings.PROJECT_FILE_EXTENSION)
        with open(proyecto, "w", encoding="utf-8") as f:
            f.write("{}")
        elegido = main_mod._project_path_from_argv(["EduFEM.exe", proyecto])
        assert elegido == os.path.abspath(proyecto), elegido
    print("[OK] la ruta del doble clic se toma como proyecto a abrir")


def test_un_argumento_invalido_no_impide_arrancar():
    """Una opcion o una ruta que no existe no puede tumbar el arranque."""
    assert main_mod._project_path_from_argv(["EduFEM.exe"]) is None
    assert main_mod._project_path_from_argv(["EduFEM.exe", "--debug"]) is None
    assert main_mod._project_path_from_argv(
        ["EduFEM.exe", r"C:\no\existe\modelo.edufem"]) is None
    print("[OK] opciones y rutas inexistentes se ignoran sin romper")


def test_la_ventana_recibe_y_agenda_el_proyecto():
    """MainWindow acepta `project_path` y lo difiere con `after`: cargarlo
    dentro del constructor dejaria el messagebox de error sin ventana padre
    y al canvas sin su tamaño real para `fit_view`."""
    firma = inspect.signature(MainWindow.__init__)
    assert "project_path" in firma.parameters, (
        "MainWindow.__init__ dejo de aceptar project_path: la asociacion de "
        "archivos abriria el programa vacio"
    )
    assert firma.parameters["project_path"].default is None
    cuerpo = inspect.getsource(MainWindow.__init__)
    assert "_load_project_from_path" in cuerpo and "after(" in cuerpo, (
        "el proyecto pedido al arrancar ya no se agenda con after()"
    )
    print("[OK] MainWindow recibe el proyecto y lo abre al entrar al loop")


# ── 4. lo que el instalador copia ────────────────────────────────────

def test_los_archivos_que_instala_el_iss_existen():
    """Cada `Source:` del .iss tiene que existir. Se exceptuan los que
    produce el build (el .exe y el TeX embebido), que no estan versionados."""
    generados = ("dist\\EduFEM", "vendor\\texlive")
    faltan = []
    for m in re.finditer(r'^Source:\s*"([^"]+)"', _texto_iss(), re.MULTILINE):
        origen = _expandir(m.group(1))
        if any(g in origen for g in generados):
            continue
        ruta = (ISS.parent / origen.replace("*", "")).resolve()
        if not ruta.exists():
            faltan.append(origen)
    assert not faltan, f"el .iss copia archivos que no existen: {faltan}"
    print("[OK] todos los archivos versionados que copia el .iss existen")


def test_el_instalador_copia_la_carpeta_onedir():
    """El `.iss` instala `dist\\EduFEM\\*` recursivamente y `build.spec` la
    produce con un COLLECT.

    Son las dos mitades de la misma decision (medida el 2026-09-10: onedir
    arranca en ~3 s contra ~12 s del onefile, y no deja 189 MB en %TEMP% por
    cada cierre anormal). Si alguien vuelve el spec a onefile sin tocar el
    `.iss`, ISCC aborta; al reves, el instalador copiaria una carpeta que no
    existe. Este test los ata.
    """
    fuentes = re.findall(r'^Source:\s*"([^"]+)"[^\n]*', _texto_iss(), re.MULTILINE)
    linea_app = [f for f in _texto_iss().splitlines()
                 if f.startswith("Source:") and "dist" in f]
    assert linea_app, "el .iss ya no copia nada desde dist\\"
    assert any("dist\\EduFEM\\*" in f for f in fuentes), (
        "el .iss deberia copiar 'dist\\EduFEM\\*' (carpeta onedir); "
        f"copia {[f for f in fuentes if 'dist' in f]}"
    )
    assert "recursesubdirs" in linea_app[0], (
        "sin 'recursesubdirs' el instalador copia el lanzador pero no "
        "_internal\\, y el programa no arranca en la maquina del alumno"
    )
    spec = (RAIZ / "build.spec").read_text(encoding="utf-8")
    assert "COLLECT(" in spec and "exclude_binaries=True" in spec, (
        "build.spec volvio a onefile pero el .iss sigue esperando dist\\EduFEM\\"
    )
    print("[OK] el .iss copia la carpeta onedir que produce build.spec")


def test_los_dialogos_de_archivo_arrancan_en_la_carpeta_del_alumno():
    """Todo `filedialog.ask*` de la ventana principal declara `initialdir`, y
    los de guardar tambien `initialfile`.

    Sin `initialdir`, Tk abre el dialogo en el directorio de trabajo del
    proceso. Corriendo desde el repo eso es la raiz del codigo; en la
    aplicacion instalada es la carpeta del programa, porque el acceso directo
    que crea el instalador arranca en `{app}`. El primer «Guardar Como» del
    alumno dejaba su modelo dentro de AppData\\Local\\Programs\\EduFEM, donde
    no lo vuelve a encontrar. Ver `config/user_paths.py`.
    """
    import ast
    fuente = (RAIZ / "gui" / "main_window.py").read_text(encoding="utf-8")
    sin_carpeta, sin_nombre = [], []
    for nodo in ast.walk(ast.parse(fuente)):
        if not isinstance(nodo, ast.Call):
            continue
        f = nodo.func
        if not (isinstance(f, ast.Attribute) and f.attr.startswith("ask")):
            continue
        if not (isinstance(f.value, ast.Name) and f.value.id == "filedialog"):
            continue
        claves = {k.arg for k in nodo.keywords}
        if "initialdir" not in claves:
            sin_carpeta.append(f"{f.attr}() en la linea {nodo.lineno}")
        if f.attr.startswith("asksaveas") and "initialfile" not in claves:
            sin_nombre.append(f"{f.attr}() en la linea {nodo.lineno}")
    assert not sin_carpeta, (
        "estos dialogos abririan en la carpeta del programa por no declarar "
        f"initialdir: {sin_carpeta}"
    )
    assert not sin_nombre, (
        f"estos dialogos de guardar no proponen nombre de archivo: {sin_nombre}"
    )
    print("[OK] los dialogos de archivo abren en la carpeta del alumno")


def test_las_imagenes_del_asistente_estan_generadas():
    """El .iss nombra cada BMP uno por uno; si falta uno, ISCC aborta."""
    faltan = []
    for clave in ("WizardImageFile", "WizardSmallImageFile"):
        m = re.search(rf"^{clave}=(.+)$", _texto_iss(), re.MULTILINE)
        assert m, f"el .iss no declara {clave}"
        for archivo in m.group(1).split(","):
            if not (ISS.parent / archivo.strip()).exists():
                faltan.append(archivo.strip())
    assert not faltan, (
        f"faltan imagenes del asistente: {faltan}. "
        "Correr: python tools/make_installer_images.py"
    )
    print("[OK] las imagenes del asistente estan generadas")


def test_el_icono_de_los_proyectos_existe():
    """El Explorador lee la ruta que apunta el registro, asi que el .ico
    tiene que viajar como archivo suelto, no dentro del .exe."""
    assert (RAIZ / "resources" / "icons" / _define("MyAppDocIcon")).exists(), (
        "falta resources/icons/edufem_doc.ico. Correr: python tools/make_icon.py"
    )
    print("[OK] el icono de los archivos .edufem esta generado")


def test_el_iss_esta_en_utf8_con_bom():
    """Sin BOM, Inno 6 lee el archivo como ANSI y los acentos de los
    mensajes del asistente salen rotos en pantalla."""
    crudo = ISS.read_bytes()
    assert crudo.startswith(b"\xef\xbb\xbf"), (
        "installer/EduFEM.iss perdio el BOM UTF-8"
    )
    print("[OK] el .iss conserva el BOM UTF-8")


def test_ninguna_linea_del_iss_empieza_con_corchete_indentado():
    """Inno lee como etiqueta de seccion toda linea cuyo primer caracter no
    blanco sea '['. Un arreglo de Pascal Script al principio de una linea
    aborta la compilacion con 'Invalid section tag'."""
    malas = []
    for n, linea in enumerate(_texto_iss().splitlines(), start=1):
        pelada = linea.strip()
        if pelada.startswith("[") and linea != pelada:
            malas.append((n, pelada[:50]))
    assert not malas, f"lineas indentadas que empiezan con '[': {malas}"
    print("[OK] ninguna linea indentada del .iss empieza con '['")


if __name__ == "__main__":
    print("=" * 62)
    print("  TEST: contrato de distribucion (instalador y arranque)")
    print("=" * 62)
    test_la_version_sigue_siendo_legible_para_el_instalador()
    test_el_appusermodelid_del_instalador_es_el_que_fija_la_app()
    test_el_mutex_del_instalador_es_el_que_crea_main()
    test_la_extension_asociada_es_la_del_modelo()
    test_el_argumento_de_la_asociacion_llega_como_proyecto()
    test_un_argumento_invalido_no_impide_arrancar()
    test_la_ventana_recibe_y_agenda_el_proyecto()
    test_los_archivos_que_instala_el_iss_existen()
    test_el_instalador_copia_la_carpeta_onedir()
    test_los_dialogos_de_archivo_arrancan_en_la_carpeta_del_alumno()
    test_las_imagenes_del_asistente_estan_generadas()
    test_el_icono_de_los_proyectos_existe()
    test_el_iss_esta_en_utf8_con_bom()
    test_ninguna_linea_del_iss_empieza_con_corchete_indentado()
    print("=" * 62)
    print("  TODOS LOS TESTS PASARON [14/14]")
    print("=" * 62)
