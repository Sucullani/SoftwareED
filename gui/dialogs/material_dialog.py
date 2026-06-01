"""
MaterialDialog: gestiona la libreria de materiales del proyecto.

Layout master-detail compacto:
- Panel izquierdo: lista con nombres (sin swatch ni meta) + botones
  Nuevo / Eliminar. Scroll exclusivamente con la rueda del mouse — sin
  scrollbar visible, alineado con el patron del spreadsheet.
- Panel derecho: form con 4 entries (Nombre, E, ν, ρ) + boton Guardar.
  Sin selector de color, sin Labelframe "Vista previa", sin status
  label, sin hints debajo de cada entry — el boton Guardar ya se
  habilita/deshabilita segun validacion.

No hay boton 'Cerrar' al pie del dialogo — la X nativa del Toplevel ya
cierra (y los cambios se guardan por-material con el boton Guardar, no
hay un commit global que justifique un 'Aceptar'). Alineado con la
direccion minimalista del resto del menu Modelo: solo agregamos un
boton de footer cuando hay una accion que requiere commit explicito.

El atributo `color` del material fue eliminado en 2026-05 (no era
consumido por el solver ni por el canvas). Si se reintroduce a futuro
como mejora visual, agregar campo opcional en `Material.__init__` con
backward-compat en `from_dict`, y reintroducir el selector de color
aqui.

El cambio de nombre cascadea a `element.material_name`. Captura undo
antes de cada mutacion.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from config.settings import LABEL_BG, LABEL_FG, CANVAS_SELECTED_ROW_BG, CANVAS_SELECTED_ROW_FG
from models.material import Material


from gui.dialogs._dialog_helpers import center_dialog
class MaterialDialog:
    """Ventana de gestion de materiales del proyecto."""

    def __init__(self, parent, project, main_window=None):
        self.project = project
        self.main_window = main_window
        self.parent = parent

        self.selected_name = None
        self._suppress_preview = False

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("🧱  Materiales")
        # Altura: padding(28) + header(32) + paned con editor de 4 entries
        # + Guardar (~210) + breathing room. 460 px asegura que Nuevo/Eliminar
        # del panel izquierdo y Guardar del panel derecho queden visibles
        # sin scroll en pantallas de 768 px con taskbar.
        self.dialog.geometry("680x460")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.minsize(640, 440)

        self._build()
        self._populate_list()
        self._center()

    # ═════════════════════════════════════════════════════════════════════
    # LAYOUT
    # ═════════════════════════════════════════════════════════════════════

    def _build(self):
        main = ttk.Frame(self.dialog, padding=14)
        main.pack(fill=BOTH, expand=YES)

        ttk.Label(
            main, text="🧱  Librería de materiales",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor=W, pady=(0, 10))

        paned = ttk.Panedwindow(main, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=YES)

        left = ttk.Frame(paned)
        paned.add(left, weight=2)
        self._build_list_panel(left)

        right = ttk.Frame(paned)
        paned.add(right, weight=3)
        self._build_editor_panel(right)

        # Sin footer de 'Cerrar' — la X nativa cierra y no hay accion
        # de commit global que justifique un 'Aceptar' (cada material
        # se guarda con su propio boton Guardar del panel derecho).

    def _build_list_panel(self, parent):
        ttk.Label(
            parent, text="Materiales", font=("Segoe UI", 10, "bold")
        ).pack(anchor=W, pady=(0, 6))

        # Lista custom: Canvas + Frame interno, scroll EXCLUSIVAMENTE con
        # la rueda del mouse (sin scrollbar visible, igual que el
        # spreadsheet del pre/post-proc).
        self.list_canvas = tk.Canvas(
            parent, highlightthickness=0, bg=LABEL_BG,
        )
        self.list_canvas.pack(fill=BOTH, expand=YES)

        self.list_inner = ttk.Frame(self.list_canvas)
        self.list_window = self.list_canvas.create_window(
            (0, 0), window=self.list_inner, anchor=NW,
        )
        self.list_inner.bind(
            "<Configure>",
            lambda e: self.list_canvas.configure(
                scrollregion=self.list_canvas.bbox("all")
            ),
        )
        self.list_canvas.bind(
            "<Configure>",
            lambda e: self.list_canvas.itemconfig(
                self.list_window, width=e.width
            ),
        )
        # Mousewheel — bind sobre el canvas y el frame interno; los rows
        # heredan el bind al populate (cada widget hijo lo recibe).
        self.list_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.list_inner.bind("<MouseWheel>", self._on_mousewheel)

        # Botones de accion (sin Duplicar). Bootstyle solido + texto-only:
        # la combinacion `success-outline`/`danger-outline` + emojis
        # (➕, 🗑) renderizaba los botones como rectangulos vacios en
        # algunas combos Python/tk de Windows (el outline mostraba pero
        # el texto se perdia por fallback de fuente emoji). Sin emojis
        # y con bootstyle solido el render es 100% reliable.
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, pady=(8, 0))
        ttk.Button(
            btn_frame, text="Nuevo", bootstyle="success",
            command=self._add_material, width=10,
        ).pack(side=LEFT, padx=2)
        ttk.Button(
            btn_frame, text="Eliminar", bootstyle="danger",
            command=self._remove_material, width=11,
        ).pack(side=LEFT, padx=2)

    def _on_mousewheel(self, event):
        """Scroll de la lista de materiales con la rueda del mouse.
        Windows envia event.delta = ±120 por click. Negamos porque
        rueda hacia arriba = scrolling hacia arriba.
        """
        self.list_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _build_editor_panel(self, parent):
        edit = ttk.Labelframe(parent, text="  Edición  ", padding=14)
        edit.pack(fill=BOTH, expand=YES)

        self.var_name = tk.StringVar()
        self.var_E = tk.StringVar()
        self.var_nu = tk.StringVar()
        self.var_density = tk.StringVar()

        fields = [
            ("Nombre",             self.var_name),
            ("Módulo de Young  E", self.var_E),
            ("Coef. de Poisson ν", self.var_nu),
            ("Densidad  ρ",        self.var_density),
        ]

        for i, (label, var) in enumerate(fields):
            ttk.Label(edit, text=label, font=("Segoe UI", 10)).grid(
                row=i, column=0, sticky=E, pady=4, padx=(0, 8)
            )
            ttk.Entry(
                edit, textvariable=var, font=("Segoe UI", 10), width=22,
            ).grid(row=i, column=1, sticky=W, pady=4)

        edit.columnconfigure(1, weight=1)

        # Boton Guardar (su state habilitado/deshabilitado = feedback de
        # validacion, sin necesidad de label de status separado).
        self.save_btn = ttk.Button(
            edit, text="💾  Guardar cambios", bootstyle="success",
            command=self._save_material,
        )
        self.save_btn.grid(
            row=len(fields), column=0, columnspan=2,
            sticky=EW, pady=(16, 0),
        )

        # Live traces: revalidan boton Guardar al editar cualquier campo.
        for var in (self.var_name, self.var_E, self.var_nu, self.var_density):
            var.trace_add("write", lambda *_: self._on_field_changed())

    # ═════════════════════════════════════════════════════════════════════
    # POBLAR LISTA
    # ═════════════════════════════════════════════════════════════════════

    def _populate_list(self):
        for w in self.list_inner.winfo_children():
            w.destroy()

        names = sorted(self.project.materials.keys())

        self._row_widgets = {}
        for name in names:
            row = tk.Frame(self.list_inner, bg=LABEL_BG, cursor="hand2")
            row.pack(fill=X, padx=4, pady=2)

            lbl = tk.Label(
                row, text=name, bg=LABEL_BG, fg=LABEL_FG,
                font=("Segoe UI", 10), anchor=W,
            )
            lbl.pack(side=LEFT, fill=X, expand=YES, pady=4, padx=8)

            for widget in (row, lbl):
                widget.bind(
                    "<Button-1>",
                    lambda _e, n=name: self._select(n),
                )
                # Propagar el bind de mousewheel a cada widget hijo:
                # sin esto el scroll se detiene cuando el cursor pasa
                # sobre un row (los widgets hijos consumen el evento).
                widget.bind("<MouseWheel>", self._on_mousewheel)

            self._row_widgets[name] = (row, lbl)

        if self.selected_name and self.selected_name in self.project.materials:
            self._select(self.selected_name)
        elif names:
            self._select(names[0])
        else:
            self._clear_editor()

    def _select(self, name):
        self.selected_name = name
        mat = self.project.materials.get(name)
        if not mat:
            return

        # Resaltar row con el color canonico del proyecto.
        for n, (row, lbl) in self._row_widgets.items():
            if n == name:
                row.config(bg=CANVAS_SELECTED_ROW_BG)
                lbl.config(
                    bg=CANVAS_SELECTED_ROW_BG, fg=CANVAS_SELECTED_ROW_FG,
                )
            else:
                row.config(bg=LABEL_BG)
                lbl.config(bg=LABEL_BG, fg=LABEL_FG)

        # Cargar en editor sin disparar traces.
        self._suppress_preview = True
        self.var_name.set(mat.name)
        self.var_E.set(f"{mat.E:g}")
        self.var_nu.set(f"{mat.nu:g}")
        self.var_density.set(f"{mat.density:g}")
        self._suppress_preview = False
        self._validate_live()

    def _clear_editor(self):
        self._suppress_preview = True
        self.var_name.set("")
        self.var_E.set("")
        self.var_nu.set("")
        self.var_density.set("")
        self._suppress_preview = False
        self._validate_live()

    # ═════════════════════════════════════════════════════════════════════
    # LIVE UPDATE
    # ═════════════════════════════════════════════════════════════════════

    def _on_field_changed(self):
        if self._suppress_preview:
            return
        self._validate_live()

    def _validate_live(self):
        """Habilita el boton Guardar si y solo si TODOS los campos son
        validos. Sin status label — el state del boton es el feedback.
        """
        ok = True
        try:
            E = float(self.var_E.get())
            if E <= 0:
                ok = False
        except (ValueError, TypeError):
            ok = False
        try:
            nu = float(self.var_nu.get())
            if not (-1.0 < nu < 0.5):
                ok = False
        except (ValueError, TypeError):
            ok = False
        try:
            rho = float(self.var_density.get())
            if rho < 0:
                ok = False
        except (ValueError, TypeError):
            ok = False
        if not self.var_name.get().strip():
            ok = False
        self.save_btn.configure(state="normal" if ok else "disabled")

    # ═════════════════════════════════════════════════════════════════════
    # ACCIONES DE LISTA
    # ═════════════════════════════════════════════════════════════════════

    def _add_material(self):
        base = "Nuevo Material"
        name = base
        i = 2
        while name in self.project.materials:
            name = f"{base} {i}"
            i += 1
        self._capture("agregar material")
        mat = Material(name, 200000.0, 0.3, 7850.0)
        self.project.materials[name] = mat
        self.project.is_modified = True
        self.selected_name = name
        self._populate_list()
        self._notify_main_window()

    def _remove_material(self):
        if not self.selected_name:
            return
        if len(self.project.materials) <= 1:
            messagebox.showwarning(
                "Aviso", "Debe haber al menos un material.",
                parent=self.dialog,
            )
            return
        if not messagebox.askyesno(
            "Eliminar material",
            f"¿Eliminar '{self.selected_name}'?",
            parent=self.dialog,
        ):
            return
        self._capture(f"eliminar material '{self.selected_name}'")
        del self.project.materials[self.selected_name]
        self.project.is_modified = True
        self.selected_name = None
        self._populate_list()
        self._notify_main_window()

    def _save_material(self):
        if not self.selected_name:
            return
        try:
            new_name = self.var_name.get().strip()
            if not new_name:
                messagebox.showerror(
                    "Error", "El nombre no puede estar vacío.",
                    parent=self.dialog,
                )
                return
            E = float(self.var_E.get())
            nu = float(self.var_nu.get())
            density = float(self.var_density.get())
        except ValueError:
            messagebox.showerror(
                "Error", "Valores numéricos inválidos.",
                parent=self.dialog,
            )
            return

        if new_name != self.selected_name and new_name in self.project.materials:
            messagebox.showerror(
                "Error", f"Ya existe un material con el nombre '{new_name}'.",
                parent=self.dialog,
            )
            return

        mat = Material(new_name, E, nu, density)
        errors = mat.validate()
        if errors:
            messagebox.showerror("Error", "\n".join(errors), parent=self.dialog)
            return

        old_name = self.selected_name
        self._capture(f"editar material '{old_name}'")
        if new_name != old_name:
            del self.project.materials[old_name]
            for elem in self.project.elements.values():
                if elem.material_name == old_name:
                    elem.material_name = new_name

        self.project.materials[new_name] = mat
        self.project.is_modified = True
        self.selected_name = new_name
        self._populate_list()
        self._notify_main_window()

    # ═════════════════════════════════════════════════════════════════════
    # NOTIFICACION + UNDO
    # ═════════════════════════════════════════════════════════════════════

    def _notify_main_window(self):
        if self.main_window is not None:
            try:
                self.main_window._refresh_all_tabs()
                self.main_window._update_title()
                self.main_window._refresh_menu_state()
            except Exception:
                pass

    def _capture(self, label):
        """Snapshot del estado actual en el undo stack. Llamar ANTES de
        mutar `project.materials`."""
        try:
            stack = getattr(self.main_window, "undo_stack", None)
            if stack is not None:
                stack.capture(label)
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════════════════
    # CENTRADO
    # ═════════════════════════════════════════════════════════════════════

    def _center(self):
        center_dialog(self.dialog, self.parent)
