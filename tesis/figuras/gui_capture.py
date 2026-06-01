# -*- coding: utf-8 -*-
"""
gui_capture.py — Captura figuras de la tesis desde la GUI REAL de EduFEM.

A diferencia de generar_figuras.py (que rinde con el motor Pillow de la
Memoria de Cálculo, fondo blanco), este script LANZA la aplicación real
(MainWindow), la lleva a cada estado y captura el lienzo oscuro tal cual lo
ve el usuario, usando la API PrintWindow de Windows (captura el contenido
del widget aunque no esté al frente — robusto y sin depender del foco).

Produce capturas auténticas de la interfaz (tema oscuro `darkly`, contornos
jet, paneles flotantes, símbolos de apoyo/carga), de modo que las figuras
de la tesis CORRESPONDAN a la GUI del software.

Figuras generadas (en tesis/figuras/):
  - fig_lienzo_lod.png        Pre-proceso: lienzo + modo dibujo de elemento.
  - fig_modulo_capa.png       Proceso: módulo educativo M3 (matriz B) como
                              capa superpuesta + puntos de Gauss sobre el
                              elemento seleccionado.
  - fig_postproceso.png       Post-proceso: contorno von Mises + deformada
                              + panel de detalles con círculo de Mohr.
  - fig_timoshenko_contorno.png  Post-proceso de la viga de Timoshenko:
                              contorno sigma_x + deformada.

Ejecutar (Windows, con el stack GUI en el .venv):
    .venv\\Scripts\\python.exe tesis\\figuras\\gui_capture.py

Requiere una sesión gráfica (no headless puro). No usa mainloop: avanza el
bucle de eventos con update() + pausas cortas.
"""

from __future__ import annotations

import ctypes
import os
import struct
import sys
import time
from ctypes import wintypes

# Raíz del repo en el path (este archivo vive en tesis/figuras/).
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)

import tkinter as tk
from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.SetProcessDPIAware()  # coords físicas correctas en pantallas escaladas


# ───────────────────────── Captura por HWND (PrintWindow) ──────────────────

def _window_rect(hwnd):
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def _grab_hwnd(hwnd):
    """Devuelve (PIL.Image, (left, top)) del contenido del HWND."""
    left, top, right, bottom = _window_rect(hwnd)
    w, h = right - left, bottom - top
    if w <= 0 or h <= 0:
        return None, (left, top)
    hdc = user32.GetWindowDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    user32.PrintWindow(hwnd, mdc, 0x2)  # PW_RENDERFULLCONTENT
    hdr = struct.pack("IiiHHIIiiII", 40, w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    info = ctypes.create_string_buffer(hdr, 40)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, info, 0)
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mdc)
    user32.ReleaseDC(hwnd, hdc)
    return img, (left, top)


def _composite(widgets, bg=(30, 30, 46)):
    """Compone varias ventanas (widgets Tk) por sus rects de pantalla.

    Captura cada HWND y las pega sobre un lienzo del tamaño de la unión de
    sus rectángulos, respetando la posición relativa real en pantalla. Así
    un panel flotante que se extiende fuera del canvas queda incluido.
    """
    shots = []
    for wdg in widgets:
        try:
            hwnd = wdg.winfo_id()
        except Exception:
            continue
        img, (l, t) = _grab_hwnd(hwnd)
        if img is None:
            continue
        shots.append((img, l, t))
    if not shots:
        return None
    minx = min(l for _, l, _ in shots)
    miny = min(t for _, _, t in shots)
    maxx = max(l + im.width for im, l, _ in shots)
    maxy = max(t + im.height for im, _, t in shots)
    out = Image.new("RGB", (maxx - minx, maxy - miny), bg)
    for im, l, t in shots:
        out.paste(im, (l - minx, t - miny))
    return out


def _results_clean(mc):
    """Para figuras de RESULTADOS con malla fina: oculta cargas, etiquetas
    de valores nodales y nodos, dejando el contorno + deformada + apoyos
    nítidos (evita el amontonamiento de flechas/labels)."""
    try:
        mc.show_loads = False
        mc.show_nodes = False
        mc.set_node_label_mode("never")
        mc.set_elem_label_mode("never")
    except Exception:
        pass


def _pump(root, n=12, dt=0.05):
    for _ in range(n):
        root.update_idletasks()
        root.update()
        time.sleep(dt)


def _save(img, name):
    if img is None:
        print(f"  [FALLO] {name}: captura vacía")
        return
    path = os.path.join(_HERE, name)
    img.save(path)
    print(f"  [OK] {name}  ({img.size[0]}x{img.size[1]})")


def _find_toplevels(root, cls_name):
    """Toplevels descendientes cuyo type().__name__ == cls_name."""
    found = []
    for w in root.winfo_children():
        if type(w).__name__ == cls_name:
            found.append(w)
    return found


# ───────────────────────── Construcción de la app ──────────────────────────

def _build_app():
    """Crea UNA sola instancia de MainWindow. ttkbootstrap no tolera bien
    crear/destruir múltiples ttk.Window (pierde estilos custom como
    'Round.Toggle'), así que se reutiliza para todas las figuras."""
    from gui.main_window import MainWindow
    app = MainWindow()
    app.root.update_idletasks()
    app.root.update()
    return app


def _load(app, variant):
    app._on_load_example(variant)
    _pump(app.root, 8)


def _load_project(app, project):
    """Carga un ProjectModel construido a medida (malla específica) en la app,
    replicando el flujo completo de _on_load_example (vars, undo, overlay, fit)
    para que el canvas se repinte correctamente."""
    app.project = project
    try:
        app.analysis_type_var.set(project.analysis_type)
        app.element_type_var.set(project.element_type)
        app.unit_system_var.set(project.unit_system)
    except Exception:
        pass
    try:
        app.undo_stack.set_project(project)
    except Exception:
        pass
    app._update_all_project_refs()
    app.mesh_canvas.clear_results_overlay()
    app._refresh_all_tabs()
    _pump(app.root, 6)
    app.mesh_canvas.fit_view()
    app.mesh_canvas.redraw()
    _pump(app.root, 14)


def _select_tab(app, idx):
    app.notebook.select(idx)
    _pump(app.root, 18)


def _cleanup(app):
    """Resetea estados transitorios entre figuras: modo dibujo, overlays
    educativos, probe/detalles del post y selección."""
    mc = app.mesh_canvas
    try:
        if mc.is_draw_mode_active():
            mc.disable_draw_mode()
    except Exception:
        pass
    try:
        from education.overlay_module import deactivate_all
        deactivate_all(app)
    except Exception:
        pass
    try:
        po = getattr(app.post_tab, "probe_overlay", None)
        if po is not None:
            if hasattr(po, "_close_details_if_open"):
                po._close_details_if_open()
            po.clear_pinned()
            po.active = False
    except Exception:
        pass
    try:
        mc.clear_highlights()
    except Exception:
        pass
    # Restaurar visibilidad por defecto (por si una figura la cambió).
    try:
        mc.show_loads = True
        mc.show_nodes = True
        mc.set_node_label_mode("auto")
        mc.set_elem_label_mode("auto")
    except Exception:
        pass
    app.notebook.select(0)
    _pump(app.root, 8)


# ───────────────────────── Figuras ─────────────────────────────────────────

def cap_lienzo(app):
    """Pre-proceso: lienzo con modo dibujo de un elemento (3 vértices puestos,
    snap al nodo 3, 4º vértice tentativo en el cursor)."""
    _load(app, "canon_q4")
    _select_tab(app, 0)
    mc = app.mesh_canvas
    mc.fit_view()
    _pump(app.root, 6)
    # Activar modo dibujo y sembrar el estado parcial.
    mc.enable_draw_mode()
    n3 = app.project.nodes[3]
    mc.draw_pending = [(3, float(n3.x), float(n3.y)),
                       (None, 10.5, 0.4), (None, 10.8, 2.6)]
    mc.draw_hover_snap = 3
    try:
        mc._last_cursor_xy = mc.world_to_screen(9.5, 1.0)
    except Exception:
        pass
    mc.redraw()
    _pump(app.root, 8)
    img, _ = _grab_hwnd(mc.winfo_id())
    _save(img, "fig_lienzo_lod.png")


def cap_modulo(app):
    """Proceso: módulo educativo M3 (matriz B) como capa flotante + Gauss
    sobre el elemento 1 seleccionado en la malla real."""
    from education.module_launcher import open_module
    _load(app, "canon_q4")
    _select_tab(app, 1)
    mc = app.mesh_canvas
    mc.fit_view()
    _pump(app.root, 6)
    mc.replace_element_selection({1})
    _pump(app.root, 4)
    open_module(app.root, app.project, "mod03", mesh_canvas=mc, elem_id=1)
    _pump(app.root, 20)
    # Mover el overlay AL LADO del canvas (a su derecha) para que se vean
    # AMBOS: la malla con el glow de Gauss sobre el elemento 1 y el panel
    # flotante con la matriz B. PrintWindow captura aunque quede off-screen.
    overlays = _find_toplevels(app.root, "CanvasOverlay")
    if overlays:
        ov = overlays[0]
        cx, cy, cw = mc.winfo_rootx(), mc.winfo_rooty(), mc.winfo_width()
        try:
            ov.geometry(f"+{cx + cw + 14}+{cy + 16}")
        except Exception:
            pass
    _pump(app.root, 6)
    mc.redraw()   # asegura la capa educativa (Gauss glow + elemento) en el canvas
    _pump(app.root, 8)
    widgets = [mc] + overlays
    img = _composite(widgets, bg=(30, 30, 46))
    _save(img, "fig_modulo_capa.png")


def cap_postproceso(app):
    """Post-proceso: contorno von Mises + deformada + panel de detalles con
    círculo de Mohr (probe pinneado en el punto de mayor tensión)."""
    _load(app, "canon_q4")
    _select_tab(app, 2)  # auto-solve
    pt = app.post_tab
    _pump(app.root, 10)
    mc = app.mesh_canvas

    # Paso 1: VM SIN deformar -> resolver el probe (las posiciones de nodo
    # coinciden con la transformación de cámara, así el hit-test acierta).
    pt.result_var.set("VM")
    pt.show_deformed_var.set(False)
    pt._on_result_changed()
    _pump(app.root, 8)
    mc.fit_view()
    _pump(app.root, 6)

    details = []
    try:
        pt.maybe_reactivate_probe_overlay()
        po = pt.probe_overlay
        ns = pt.nodal_stresses or {}
        nid = max(ns, key=lambda k: ns[k].get("von_mises", 0.0))
        node = app.project.nodes[nid]
        sx, sy = mc.world_to_screen(node.x, node.y)
        _pump(app.root, 2)
        target = po._resolve_target_at(int(sx), int(sy))
        if target is None:  # fallback: centroide del elemento de ese nodo
            for eid, el in app.project.elements.items():
                if nid in el.node_ids:
                    cs = [app.project.nodes[n] for n in el.node_ids[:4]]
                    cxw = sum(n.x for n in cs) / 4.0
                    cyw = sum(n.y for n in cs) / 4.0
                    sx, sy = mc.world_to_screen(cxw, cyw)
                    target = po._resolve_target_at(int(sx), int(sy))
                    break
        if target is not None:
            po._show_details_persistent(target, int(sx), int(sy))
            _pump(app.root, 14)
            dp = getattr(po, "_details_panel", None)
            if dp is not None:
                details = [dp]
        else:
            print("  [aviso] probe target None")
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc()
        print(f"  [aviso] Mohr/probe no disponible: {e}")

    # Paso 2: activar la deformada (~10%) para el contorno final y capturar.
    pt.show_deformed_var.set(True)
    pt.scale_var.set(1.0)
    pt._on_result_changed()
    _pump(app.root, 10)
    mc.fit_view()
    _pump(app.root, 6)

    # Reubicar el panel de detalles a la derecha del canvas (no tapa el campo).
    if details:
        cx, cy, cw = mc.winfo_rootx(), mc.winfo_rooty(), mc.winfo_width()
        try:
            details[0].geometry(f"+{cx + cw + 14}+{cy + 16}")
        except Exception:
            pass
        _pump(app.root, 6)

    widgets = [mc] + details
    img = _composite(widgets, bg=(30, 30, 46))
    _save(img, "fig_postproceso.png")


def cap_timoshenko(app):
    """Post-proceso de la viga de Timoshenko Q9 (malla 56x8, igual que las
    tablas de V&V): contorno sigma_x + deformada."""
    from models.example_library import load_example_timoshenko
    from config.settings import ELEMENT_Q9
    _load_project(app, load_example_timoshenko(ELEMENT_Q9, nx=56, ny=8))
    _select_tab(app, 2)  # auto-solve (malla pesada: settle generoso)
    pt = app.post_tab
    _pump(app.root, 40, dt=0.12)
    pt.result_var.set("Sx")
    pt.show_deformed_var.set(True)
    pt.scale_var.set(1.0)   # 1.0 = deformación visual ~10% del tamaño del modelo
    pt._on_result_changed()
    _pump(app.root, 30, dt=0.12)
    mc = app.mesh_canvas
    _results_clean(mc)
    mc.fit_view()
    mc.redraw()
    _pump(app.root, 14)
    img, _ = _grab_hwnd(mc.winfo_id())
    _save(img, "fig_timoshenko_contorno.png")


def cap_cook_deformed(app):
    """Post-proceso de la membrana de Cook Q9 (N=8): configuración deformada
    con contorno de magnitud de desplazamiento."""
    from models.example_library import load_example_cook
    from config.settings import ELEMENT_Q9
    _load_project(app, load_example_cook(ELEMENT_Q9, N=8))
    _select_tab(app, 2)  # auto-solve
    pt = app.post_tab
    _pump(app.root, 14)
    pt.result_var.set("Umag")
    pt.show_deformed_var.set(True)
    pt.scale_var.set(1.0)
    pt._on_result_changed()
    _pump(app.root, 14)
    mc = app.mesh_canvas
    _results_clean(mc)
    mc.fit_view()
    mc.redraw()
    _pump(app.root, 10)
    img, _ = _grab_hwnd(mc.winfo_id())
    _save(img, "fig_cook_deformed.png")


def main():
    print("Capturando figuras desde la GUI real de EduFEM…")
    print("-" * 60)
    app = _build_app()
    _all = [
        ("lienzo", cap_lienzo),
        ("modulo", cap_modulo),
        ("postproceso", cap_postproceso),
        ("timoshenko", cap_timoshenko),
        ("cook_deformed", cap_cook_deformed),
    ]
    sel = sys.argv[1:]
    todo = [(n, f) for n, f in _all if not sel or n in sel]
    for name, fn in todo:
        print(f"[{name}]")
        try:
            fn(app)
        except Exception as e:  # noqa: BLE001
            import traceback
            print(f"  [ERROR] {name}: {e}")
            traceback.print_exc()
        try:
            _cleanup(app)
        except Exception:
            pass
        time.sleep(0.3)
    try:
        app.root.destroy()
    except Exception:
        pass
    print("-" * 60)
    print("Listo.")


if __name__ == "__main__":
    main()
