# Fuentes bundleadas con EduFEM

## Computer Modern (CMU Serif)

EduFEM usa la fuente **CMU Serif** (Computer Modern Unicode) para los
*overlays de valores live* del componente `LatexBlock` modo parametric.
Coincide exactamente con la tipografía de los PNGs compilados con
pdflatex (que usa Computer Modern por default), produciendo una
transición invisible entre el render LaTeX y el valor superpuesto.

### Cómo conseguir los archivos

CMU Serif tiene licencia OFL (Open Font License — uso comercial OK,
redistribución OK). Fuente recomendada:

- https://www.fontsquirrel.com/fonts/computer-modern  (CMU Serif Roman + Italic + Bold)
- https://cm-unicode.sourceforge.io  (paquete oficial completo)

Una vez descargado, copiar los TTF a esta carpeta con estos nombres:

```
resources/fonts/
├── cmunrm.ttf       # CMU Serif Roman (regular)
├── cmunti.ttf       # CMU Serif Italic
├── cmunbx.ttf       # CMU Serif Bold
└── cmunbi.ttf       # CMU Serif Bold Italic
```

### Activación en runtime

`gui/main_window.py::_register_cmu_fonts()` registra estas fuentes como
*privadas del proceso* en Windows (vía `AddFontResourceEx` con flag
`FR_PRIVATE`). No requiere instalación system-wide ni privilegios de
administrador. La fuente queda disponible para `tk.Label(font=("CMU Serif", ...))`.

En Linux/macOS la activación es vía `Tcl/Tk` directamente (Tk lee fuentes
desde el config de fontconfig); si las TTF están en `~/.fonts/` o
`/usr/share/fonts/` el sistema las indexa automáticamente.

### Fallback sin la fuente

Si las TTF no están en esta carpeta, `LatexBlock` cae al fallback Tk
del serif italic del sistema (Times New Roman en Windows). Visualmente
peor que CMU pero funcional — los módulos siguen siendo legibles.

### Bundling con PyInstaller

`build.spec` incluye:

```python
datas=[
    ("resources/fonts/*.ttf", "resources/fonts"),
    ...
]
```

de modo que las TTF viajan dentro del `.exe` y `_register_cmu_fonts`
resuelve el path correcto vía `sys._MEIPASS` (carpeta temporal de
PyInstaller en runtime).
