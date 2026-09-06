---
paths:
  - "build.spec"
  - "installer/**"
  - "tools/**/*.py"
  - "config/settings.py"
---

# Empaquetado y distribución

Canon: **[docs/convenciones/arquitectura.md](../../docs/convenciones/arquitectura.md)** ·
rutas frágiles: **[docs/MAPA.md](../../docs/MAPA.md)**.

- **Todo acceso a un recurso pasa por `config.settings.resource_path(*parts)`**, que resuelve
  vía `sys._MEIPASS` en el `.exe` y vía la raíz del repo en dev. Una ruta relativa al CWD
  funciona en desarrollo y falla en el ejecutable. `gui/fonts_loader.py::_resources_root` es su
  espejo: si tocás uno, tocá el otro.
- **Los `education/mod*.py` van sí o sí en `hiddenimports`** (el spec los toma por glob):
  `module_launcher.open_module` los carga con `importlib.import_module` y el analizador
  estático de PyInstaller no los ve. Sin esa entrada el `.exe` abre pero cada módulo falla.
  Cualquier import dinámico nuevo replica el patrón.
- Modo **onefile**: un `dist/EduFEM.exe` autoextraíble. Para volver a onedir hay que restaurar
  el `COLLECT` y `exclude_binaries=True`.
- No se bundlea MiKTeX: las fórmulas in-app caen al fallback mathtext, pero la Memoria PDF
  exige `pdflatex` y, si falta, muestra un diálogo con botón de descarga.
- Vía de distribución decidida: instalador **Inno Setup** por usuario, sin admin y sin firma
  de código.
