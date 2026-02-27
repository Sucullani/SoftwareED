"""
MaterialDialog: Diálogo para gestionar la librería de materiales.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from models.material import Material


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
