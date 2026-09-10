"""Smoke test con Tk real (root.withdraw, sin mainloop) del rediseño de la
capa visual del 2026-09-09: lentes por fase, capa de GDL, lente del
elemento seleccionado, franja lectora, reacciones en Post, vista del
sistema K·u = F y tira del metodo.

Run:  python -m tests.test_canvas_lens_gui   (necesita un display)
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import tkinter as tk                              # noqa: F401
except ImportError:
    print("Tk no disponible — smoke test omitido")
    sys.exit(0)


class _Ev:
    def __init__(self, x, y, state=0):
        self.x, self.y, self.state = x, y, state


class _Wheel:
    def __init__(self, x, y, delta):
        self.x, self.y, self.delta = x, y, delta


def test_lentes():
    from gui.main_window import MainWindow
    from models.example_library import load_example_project

    mw = MainWindow()
    mw.root.withdraw()
    mw.project.restore_from_dict(load_example_project(P=1000.0).to_dict())
    mw._update_all_project_refs()
    mw._refresh_all_tabs()
    mw.root.update_idletasks()
    c = mw.mesh_canvas
    c.canvas.configure(width=900, height=600)
    mw.root.update_idletasks()
    c.fit_view()
    mw.root.update_idletasks()
    canvas = c.canvas

    # ── Pre: cuadricula del mundo + lector ───────────────────────────
    grid = canvas.find_withtag("grid")
    assert grid, "sin cuadricula"
    assert all("world" in canvas.gettags(i) for i in grid), \
        "la cuadricula tiene que viajar con el mundo (tag world), no screen"
    assert c._grid_step_world in (0.5, 1.0, 2.0, 5.0), c._grid_step_world
    assert canvas.find_withtag("inspector"), "sin franja lectora"
    print("[OK] cuadricula anclada al mundo + franja lectora")

    c._on_mouse_move(_Ev(*c.world_to_screen(7, 4)))
    assert c._inspector_target == ("node", 5), c._inspector_target
    assert "mm" in c.coord_label.cget("text") and "cuadrícula" in c.coord_label.cget("text")
    textos = [canvas.itemcget(i, "text") for i in canvas.find_withtag("inspector")
              if canvas.type(i) == "text"]
    assert any(t == "Nodo 5" for t in textos), textos
    assert any("GDL u₅→8" in t for t in textos), textos
    c._on_mouse_move(_Ev(*c.world_to_screen(3, 1.5)))
    assert c._inspector_target == ("element", 1), c._inspector_target
    c._on_canvas_leave(None)
    assert c._inspector_target is None
    textos = [canvas.itemcget(i, "text") for i in canvas.find_withtag("inspector")
              if canvas.type(i) == "text"]
    assert any("Pre-Proceso" in t for t in textos), textos
    print("[OK] lector: nodo -> elemento -> pista de fase")

    # En Pre la capa de GDL esta apagada.
    assert not c.show_dofs and not canvas.find_withtag("dofs")

    # ── Proceso: lente del sistema ───────────────────────────────────
    mw.notebook.select(1)
    mw._on_tab_changed(None)
    mw.root.update_idletasks()
    assert c._phase == "proc" and c.show_dofs
    dofs = canvas.find_withtag("dofs")
    assert dofs, "en Proceso los indices de GDL tienen que verse"
    fuentes = {str(canvas.itemcget(i, "font")) for i in dofs}
    assert any("overstrike" in f for f in fuentes), \
        "los GDL restringidos van tachados (overstrike)"
    textos = {canvas.itemcget(i, "text") for i in dofs}
    assert "0" in textos and "17" in textos, textos
    assert "incógnitas" in mw.status_label.cget("text")
    print("[OK] Proceso: capa de GDL con restringidos tachados")

    c.select_element(1)
    lens = canvas.find_withtag("lens")
    assert lens, "sin lente sobre el elemento seleccionado"
    lens_txt = {canvas.itemcget(i, "text") for i in lens if canvas.type(i) == "text"}
    assert {"ξ", "η", "1", "2", "3", "4"} <= lens_txt, lens_txt
    ovals = [i for i in lens if canvas.type(i) == "oval"]
    assert len(ovals) == 4 + 4, f"4 PG + 4 discos locales, hay {len(ovals)}"
    c.clear_highlights()
    assert not canvas.find_withtag("lens")
    # Con un overlay educativo activo la lente se retira.
    c.select_element(1)
    c.add_overlay_layer(lambda _m: None)
    assert not canvas.find_withtag("lens")
    c.clear_overlay_layers()
    c.redraw()
    assert canvas.find_withtag("lens")
    c.clear_highlights()
    print("[OK] lente del elemento: numeracion local, ejes ξη y PG")

    # M7: la lectura del sistema vive en el modulo de ensamblaje — esqueleto
    # de K (forma que la malla decide) + cabecera con los numeros. Se abre
    # de verdad (overlay Toplevel + matplotlib) con la raiz retirada.
    from education.module_launcher import open_module
    from education.overlay_module import _ACTIVE
    from education.mod07_assembly import AssemblyModule
    assert open_module(mw.root, mw.project, "mod07", mesh_canvas=c,
                       elem_id=None), "M7 no abrio"
    m7 = _ACTIVE[(id(mw), AssemblyModule)]
    assert m7._skeleton_img is not None and m7._skeleton_img.shape == (18, 18, 3), \
        getattr(m7._skeleton_img, "shape", None)
    txt = m7._lbl_system.cget("text")
    assert "2N = 18 GDL" in txt and "12 incógnitas" in txt and "49 de 81" in txt, txt
    # El esqueleto tiene bloque donde la malla lo decide y no donde no: los
    # nodos 1 y 9 (ordinales 0 y 8) no comparten elemento.
    import numpy as np
    bg = m7._skeleton_img[0, 16]
    diag = m7._skeleton_img[0, 0]
    assert not np.array_equal(bg, diag), "el esqueleto no distingue bloque de vacio"
    # Con un overlay abierto la lente base del elemento se retira.
    c.select_element(1)
    assert not canvas.find_withtag("lens")
    m7.close()
    mw.root.update_idletasks()
    assert not c._overlay_layers
    c.clear_highlights()
    print("[OK] M7: esqueleto de K y cabecera del sistema")

    # Tira del metodo.
    strip = mw.proc_tab.method_strip
    assert len(strip._chips) == 7
    assert strip.state_of("mod03") == "inactive"
    strip.set_active({"mod03"})
    assert strip.state_of("mod03") == "active"
    strip.set_active(set())
    assert strip.state_of("mod03") == "visited" and strip.state_of("mod01") == "inactive"
    print("[OK] tira del metodo: inactivo -> activo -> visitado")

    # Menu del titulo: la capa GDL se apaga y prende.
    c._set_layer("show_dofs", False)
    assert not canvas.find_withtag("dofs")
    c._set_layer("show_dofs", True)
    assert canvas.find_withtag("dofs")

    # Zoom: la cuadricula escala con el mundo, la franja no se mueve.
    y_franja = canvas.bbox(canvas.find_withtag("inspector")[0])
    for _ in range(3):
        c._on_mousewheel(_Wheel(450, 300, 120))
    assert canvas.bbox(canvas.find_withtag("inspector")[0]) == y_franja
    c._exit_interaction_mode()
    print("[OK] zoom: franja anclada a pantalla")

    # ── Post: reacciones ─────────────────────────────────────────────
    mw.notebook.select(2)
    mw._on_tab_changed(None)
    mw.root.update_idletasks()
    assert c._phase == "post" and mw.project.is_solved
    assert c.reactions is not None and c.reactions.shape == (18,)
    assert canvas.find_withtag("reactions"), "sin flechas de reaccion"
    assert not c.show_dofs, "Post apaga la capa de GDL"
    rtxt = [canvas.itemcget(i, "text") for i in canvas.find_withtag("reactions")
            if canvas.type(i) == "text"]
    assert any(t.startswith("Ry=") for t in rtxt), rtxt
    # Suma de reacciones verticales = carga aplicada (equilibrio).
    import numpy as np
    R = c.reactions
    idx = mw.project.node_index_map
    ry = sum(R[2 * idx[n] + 1] for n in (1, 3, 6))
    assert abs(ry - 1000.0) < 1e-6, ry
    mw.post_tab.show_reactions_var.set(False)
    mw.post_tab._on_result_changed()
    assert not canvas.find_withtag("reactions")
    mw.post_tab.show_reactions_var.set(True)
    mw.post_tab._on_result_changed()
    assert canvas.find_withtag("reactions")
    # En Post el lector no consulta (la sonda manda): pista de fase.
    c._on_mouse_move(_Ev(*c.world_to_screen(7, 4)))
    assert c._inspector_target is None
    print("[OK] Post: reacciones en los apoyos (ΣRy = P) y toggle")

    # Volver a Pre limpia reacciones y GDL.
    mw.notebook.select(0)
    mw._on_tab_changed(None)
    assert c.reactions is None and not canvas.find_withtag("reactions")
    print("[OK] volver a Pre limpia la lente de campo")

    mw.root.destroy()
    print("\nSmoke test del rediseño de la capa visual: PASS")


if __name__ == "__main__":
    test_lentes()
