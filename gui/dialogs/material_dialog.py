"""
MaterialDialog: Diálogo para gestionar la librería de materiales del proyecto.
Incluye un importador de materiales típicos (valores en unidades consistentes
con N, mm, MPa; el usuario debe convertir si usa otro sistema).
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from models.material import Material


# Valores en unidades SI (N, mm, MPa) — consistentes con DEFAULT_UNIT_SYSTEM.
# Densidad en kg/m³ (unidad SI estándar, común para toda la ingeniería).
TYPICAL_MATERIALS = [
    ("Acero estructural A36",   {"E": 200000.0, "nu": 0.30, "density": 7850.0, "color": "#4fc3f7"}),
    ("Acero AISI 1020",         {"E": 205000.0, "nu": 0.29, "density": 7860.0, "color": "#4fc3f7"}),
    ("Acero inoxidable 304",    {"E": 193000.0, "nu": 0.29, "density": 8000.0, "color": "#90caf9"}),
    ("Aluminio 6061-T6",        {"E":  68900.0, "nu": 0.33, "density": 2700.0, "color": "#81c784"}),
    ("Aluminio 7075",           {"E":  71700.0, "nu": 0.33, "density": 2810.0, "color": "#a5d6a7"}),
    ("Cobre puro",              {"E": 110000.0, "nu": 0.34, "density": 8960.0, "color": "#ffb74d"}),
    ("Bronce",                  {"E": 103000.0, "nu": 0.34, "density": 8800.0, "color": "#ff8a65"}),
    ("Titanio Grado 5",         {"E": 113000.0, "nu": 0.34, "density": 4430.0, "color": "#ce93d8"}),
    ("Concreto f'c=21 MPa",     {"E":  21538.0, "nu": 0.20, "density": 2400.0, "color": "#bdbdbd"}),
    ("Concreto f'c=28 MPa",     {"E":  24870.0, "nu": 0.20, "density": 2400.0, "color": "#bdbdbd"}),
    ("Madera pino",             {"E":  11000.0, "nu": 0.30, "density":  550.0, "color": "#d7ccc8"}),
    ("Vidrio",                  {"E":  70000.0, "nu": 0.22, "density": 2500.0, "color": "#b3e5fc"}),
]


class MaterialDialog:
    """Ventana de gestión de propiedades de materiales."""

    def __init__(self, parent, project):
        self.project = project

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("Propiedades de Material")
        self.dialog.geometry("650x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        main = ttk.Frame(self.dialog, padding=15)
        main.pack(fill=BOTH, expand=YES)

        # ─── Paneles ────────────────────────────────────────────────────
        paned = ttk.Panedwindow(main, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=YES)

        # Lista de materiales
        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        ttk.Label(left, text="Materiales", font=("Segoe UI", 11, "bold")).pack(
            anchor=W, pady=(0, 5)
        )

        self.mat_listbox = tk.Listbox(left, font=("Segoe UI", 10))
        self.mat_listbox.pack(fill=BOTH, expand=YES, pady=5)
        self.mat_listbox.bind("<<ListboxSelect>>", self._on_select)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=X, pady=5)
        ttk.Button(
            btn_frame, text="➕ Nuevo", bootstyle="success-outline",
            command=self._add_material, width=8
        ).pack(side=LEFT, padx=2)
        ttk.Button(
            btn_frame, text="🗑️ Eliminar", bootstyle="danger-outline",
            command=self._remove_material, width=8
        ).pack(side=LEFT, padx=2)

        ttk.Button(
            left, text="📚 Importar material típico…",
            bootstyle="info-outline",
            command=self._import_typical_material,
        ).pack(fill=X, pady=(6, 0))

        # Propiedades del material seleccionado
        right = ttk.Labelframe(paned, text="Propiedades", padding=15)
        paned.add(right, weight=1)

        fields = [
            ("Nombre:", "name"),
            ("Módulo de Young (E):", "E"),
            ("Coef. de Poisson (ν):", "nu"),
            ("Densidad:", "density"),
        ]

        self.entries = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(right, text=label).grid(
                row=i, column=0, sticky=E, pady=5, padx=(0, 8)
            )
            entry = ttk.Entry(right, width=20)
            entry.grid(row=i, column=1, sticky=W, pady=5)
            self.entries[key] = entry

        ttk.Button(
            right, text="💾 Guardar Cambios", bootstyle="primary",
            command=self._save_material
        ).grid(row=len(fields), column=0, columnspan=2, pady=15)

        # ─── Popular lista ──────────────────────────────────────────────
        self._refresh_list()

        # Centrar ventana
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _refresh_list(self):
        self.mat_listbox.delete(0, tk.END)
        for name in sorted(self.project.materials.keys()):
            self.mat_listbox.insert(tk.END, name)

    def _on_select(self, event):
        sel = self.mat_listbox.curselection()
        if not sel:
            return
        name = self.mat_listbox.get(sel[0])
        mat = self.project.materials.get(name)
        if mat:
            self.entries["name"].delete(0, tk.END)
            self.entries["name"].insert(0, mat.name)
            self.entries["E"].delete(0, tk.END)
            self.entries["E"].insert(0, str(mat.E))
            self.entries["nu"].delete(0, tk.END)
            self.entries["nu"].insert(0, str(mat.nu))
            self.entries["density"].delete(0, tk.END)
            self.entries["density"].insert(0, str(mat.density))

    def _save_material(self):
        try:
            name = self.entries["name"].get().strip()
            if not name:
                messagebox.showerror("Error", "El nombre no puede estar vacío.")
                return
            E = float(self.entries["E"].get())
            nu = float(self.entries["nu"].get())
            density = float(self.entries["density"].get())

            mat = Material(name, E, nu, density)
            errors = mat.validate()
            if errors:
                messagebox.showerror("Error", "\n".join(errors))
                return

            self.project.materials[name] = mat
            self.project.is_modified = True
            self._refresh_list()
            messagebox.showinfo("Material", f"Material '{name}' guardado.")
        except ValueError:
            messagebox.showerror("Error", "Valores numéricos inválidos.")

    def _add_material(self):
        mat = Material("Nuevo Material", 200000, 0.3, 7850)
        self.project.materials[mat.name] = mat
        self.project.is_modified = True
        self._refresh_list()

    def _remove_material(self):
        sel = self.mat_listbox.curselection()
        if not sel:
            return
        name = self.mat_listbox.get(sel[0])
        if len(self.project.materials) <= 1:
            messagebox.showwarning("Aviso", "Debe haber al menos un material.")
            return
        del self.project.materials[name]
        self.project.is_modified = True
        self._refresh_list()

    def _import_typical_material(self):
        """Abre un selector con materiales típicos precargados."""
        picker = ttk.Toplevel(self.dialog)
        picker.title("📚 Importar material típico")
        picker.geometry("460x240")
        picker.transient(self.dialog)
        picker.grab_set()
        picker.resizable(False, False)

        frame = ttk.Frame(picker, padding=15)
        frame.pack(fill=BOTH, expand=YES)

        ttk.Label(
            frame, text="Seleccione un material de la biblioteca:",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor=W, pady=(0, 8))

        names = [name for name, _ in TYPICAL_MATERIALS]
        selected = tk.StringVar(value=names[0])

        combo = ttk.Combobox(
            frame, textvariable=selected, values=names,
            state="readonly", font=("Segoe UI", 10),
        )
        combo.pack(fill=X, pady=(0, 8))

        info_lbl = ttk.Label(
            frame, text="", foreground="#aaa",
            font=("Segoe UI", 9), justify=LEFT,
        )
        info_lbl.pack(anchor=W, pady=(0, 4))

        warn_lbl = ttk.Label(
            frame,
            text=(
                "ℹ  Valores en E [MPa], ν, densidad [kg/m³].\n"
                "     Ajuste si su sistema de unidades es distinto."
            ),
            foreground="#ffa726", font=("Segoe UI", 8), justify=LEFT,
        )
        warn_lbl.pack(anchor=W, pady=(4, 8))

        def _refresh_info(*_):
            props = dict(TYPICAL_MATERIALS).get(selected.get(), {})
            info_lbl.config(
                text=(
                    f"E = {props.get('E', 0):g} MPa    "
                    f"ν = {props.get('nu', 0):g}    "
                    f"ρ = {props.get('density', 0):g} kg/m³"
                )
            )

        combo.bind("<<ComboboxSelected>>", _refresh_info)
        _refresh_info()

        btn_bar = ttk.Frame(frame)
        btn_bar.pack(fill=X, pady=(4, 0))

        def _do_import():
            name = selected.get()
            props = dict(TYPICAL_MATERIALS).get(name)
            if props is None:
                picker.destroy()
                return
            final_name = name
            i = 2
            while final_name in self.project.materials:
                final_name = f"{name} ({i})"
                i += 1
            self.project.materials[final_name] = Material(name=final_name, **props)
            self.project.is_modified = True
            self._refresh_list()
            picker.destroy()
            messagebox.showinfo(
                "Importar material",
                f"Material '{final_name}' agregado a la librería.",
                parent=self.dialog,
            )

        ttk.Button(
            btn_bar, text="Cancelar", bootstyle="secondary",
            command=picker.destroy, width=12,
        ).pack(side=RIGHT, padx=4)
        ttk.Button(
            btn_bar, text="Importar", bootstyle="success",
            command=_do_import, width=12,
        ).pack(side=RIGHT, padx=4)

        picker.update_idletasks()
        w = picker.winfo_width()
        h = picker.winfo_height()
        x = self.dialog.winfo_x() + (self.dialog.winfo_width() - w) // 2
        y = self.dialog.winfo_y() + (self.dialog.winfo_height() - h) // 2
        picker.geometry(f"+{max(x, 0)}+{max(y, 0)}")
