"""
PreProcessTab: Panel izquierdo de Pre-Proceso.
Tablas de datos: Nodos, Elementos, Cargas, Restricciones, Cargas Superficiales.
El canvas de malla es compartido en main_window.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
import csv


class PreProcessTab:
    """Panel de Pre-Proceso con tablas de datos (sin canvas propio)."""

    def __init__(self, parent, project, main_window):
        self.project = project
        self.main_window = main_window
        self.frame = ttk.Frame(parent)

        self._build_panel()

    def _build_panel(self):
        """Construye las sub-pestanas de datos."""
        self.data_notebook = ttk.Notebook(self.frame, bootstyle="info")
        self.data_notebook.pack(fill=BOTH, expand=YES, padx=2, pady=2)

        # Nodos
        self.nodes_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(self.nodes_frame, text="  Nodos  ")
        self._build_nodes_panel()

        # Elementos
        self.elements_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(self.elements_frame, text="  Elementos  ")
        self._build_elements_panel()

        # Cargas Nodales
        self.loads_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(self.loads_frame, text="  Cargas  ")
        self._build_loads_panel()

        # Restricciones
        self.constraints_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(self.constraints_frame, text="  Restricciones  ")
        self._build_constraints_panel()

        # Cargas Superficiales
        self.surface_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(self.surface_frame, text="  Carg. Superf.  ")
        self._build_surface_loads_panel()

    # ─── Panel de Nodos ─────────────────────────────────────────────────

    def _build_nodes_panel(self):
        toolbar = ttk.Frame(self.nodes_frame)
        toolbar.pack(fill=X, padx=5, pady=(5, 2))

        ttk.Button(toolbar, text="Agregar", bootstyle="success-outline",
                   command=self._add_node, width=9).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="Eliminar", bootstyle="danger-outline",
                   command=self._remove_node, width=9).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="Importar CSV", bootstyle="info-outline",
                   command=self._import_nodes_csv, width=11).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="Exportar CSV", bootstyle="info-outline",
                   command=self._export_nodes_csv, width=11).pack(side=LEFT, padx=2)

        columns = ("id", "x", "y")
        self.nodes_tree = ttk.Treeview(
            self.nodes_frame, columns=columns, show="headings",
            bootstyle="info", height=18
        )
        self.nodes_tree.heading("id", text="ID", anchor=CENTER)
        self.nodes_tree.heading("x", text="X", anchor=CENTER)
        self.nodes_tree.heading("y", text="Y", anchor=CENTER)
        self.nodes_tree.column("id", width=50, anchor=CENTER)
        self.nodes_tree.column("x", width=110, anchor=CENTER)
        self.nodes_tree.column("y", width=110, anchor=CENTER)

        scrollbar = ttk.Scrollbar(self.nodes_frame, orient=VERTICAL,
                                  command=self.nodes_tree.yview)
        self.nodes_tree.configure(yscrollcommand=scrollbar.set)
        self.nodes_tree.pack(fill=BOTH, expand=YES, padx=5, pady=2, side=LEFT)
        scrollbar.pack(fill=Y, side=RIGHT, pady=2, padx=(0, 5))

        self.nodes_tree.bind("<Double-1>", self._on_node_double_click)
        self.nodes_tree.bind("<<TreeviewSelect>>", self._on_node_select)

    # ─── Panel de Elementos ─────────────────────────────────────────────

    def _build_elements_panel(self):
        toolbar = ttk.Frame(self.elements_frame)
        toolbar.pack(fill=X, padx=5, pady=(5, 2))

        ttk.Button(toolbar, text="Agregar", bootstyle="success-outline",
                   command=self._add_element, width=9).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="Eliminar", bootstyle="danger-outline",
                   command=self._remove_element, width=9).pack(side=LEFT, padx=2)

        columns = ("id", "n1", "n2", "n3", "n4", "espesor", "material")
        self.elements_tree = ttk.Treeview(
            self.elements_frame, columns=columns, show="headings",
            bootstyle="info", height=18
        )
        self.elements_tree.heading("id", text="ID", anchor=CENTER)
        self.elements_tree.heading("n1", text="N1", anchor=CENTER)
        self.elements_tree.heading("n2", text="N2", anchor=CENTER)
        self.elements_tree.heading("n3", text="N3", anchor=CENTER)
        self.elements_tree.heading("n4", text="N4", anchor=CENTER)
        self.elements_tree.heading("espesor", text="Espesor", anchor=CENTER)
        self.elements_tree.heading("material", text="Material", anchor=CENTER)
        for col in ("id", "n1", "n2", "n3", "n4"):
            self.elements_tree.column(col, width=35, anchor=CENTER)
        self.elements_tree.column("espesor", width=60, anchor=CENTER)
        self.elements_tree.column("material", width=100, anchor=CENTER)

        scrollbar = ttk.Scrollbar(self.elements_frame, orient=VERTICAL,
                                  command=self.elements_tree.yview)
        self.elements_tree.configure(yscrollcommand=scrollbar.set)
        self.elements_tree.pack(fill=BOTH, expand=YES, padx=5, pady=2, side=LEFT)
        scrollbar.pack(fill=Y, side=RIGHT, pady=2, padx=(0, 5))

        self.elements_tree.bind("<Double-1>", self._on_element_double_click)
        self.elements_tree.bind("<<TreeviewSelect>>", self._on_element_select)

    # ─── Panel de Cargas Nodales ────────────────────────────────────────

    def _build_loads_panel(self):
        toolbar = ttk.Frame(self.loads_frame)
        toolbar.pack(fill=X, padx=5, pady=(5, 2))

        ttk.Button(toolbar, text="Agregar", bootstyle="success-outline",
                   command=self._add_load, width=9).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="Eliminar", bootstyle="danger-outline",
                   command=self._remove_load, width=9).pack(side=LEFT, padx=2)

        columns = ("node_id", "fx", "fy")
        self.loads_tree = ttk.Treeview(
            self.loads_frame, columns=columns, show="headings",
            bootstyle="info", height=18
        )
        self.loads_tree.heading("node_id", text="Nodo", anchor=CENTER)
        self.loads_tree.heading("fx", text="Fx", anchor=CENTER)
        self.loads_tree.heading("fy", text="Fy", anchor=CENTER)
        self.loads_tree.column("node_id", width=60, anchor=CENTER)
        self.loads_tree.column("fx", width=110, anchor=CENTER)
        self.loads_tree.column("fy", width=110, anchor=CENTER)

        scrollbar = ttk.Scrollbar(self.loads_frame, orient=VERTICAL,
                                  command=self.loads_tree.yview)
        self.loads_tree.configure(yscrollcommand=scrollbar.set)
        self.loads_tree.pack(fill=BOTH, expand=YES, padx=5, pady=2, side=LEFT)
        scrollbar.pack(fill=Y, side=RIGHT, pady=2, padx=(0, 5))

        self.loads_tree.bind("<Double-1>", self._on_load_double_click)

    # ─── Panel de Restricciones ─────────────────────────────────────────

    def _build_constraints_panel(self):
        toolbar = ttk.Frame(self.constraints_frame)
        toolbar.pack(fill=X, padx=5, pady=(5, 2))

        ttk.Button(toolbar, text="Agregar", bootstyle="success-outline",
                   command=self._add_constraint, width=9).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="Eliminar", bootstyle="danger-outline",
                   command=self._remove_constraint, width=9).pack(side=LEFT, padx=2)

        columns = ("node_id", "rx", "ry")
        self.constraints_tree = ttk.Treeview(
            self.constraints_frame, columns=columns, show="headings",
            bootstyle="info", height=18
        )
        self.constraints_tree.heading("node_id", text="Nodo", anchor=CENTER)
        self.constraints_tree.heading("rx", text="Restringir X", anchor=CENTER)
        self.constraints_tree.heading("ry", text="Restringir Y", anchor=CENTER)
        self.constraints_tree.column("node_id", width=60, anchor=CENTER)
        self.constraints_tree.column("rx", width=110, anchor=CENTER)
        self.constraints_tree.column("ry", width=110, anchor=CENTER)

        scrollbar = ttk.Scrollbar(self.constraints_frame, orient=VERTICAL,
                                  command=self.constraints_tree.yview)
        self.constraints_tree.configure(yscrollcommand=scrollbar.set)
        self.constraints_tree.pack(fill=BOTH, expand=YES, padx=5, pady=2, side=LEFT)
        scrollbar.pack(fill=Y, side=RIGHT, pady=2, padx=(0, 5))

        self.constraints_tree.bind("<Button-1>", self._on_constraint_click)

    # ─── Panel de Cargas Superficiales ──────────────────────────────────

    def _build_surface_loads_panel(self):
        toolbar = ttk.Frame(self.surface_frame)
        toolbar.pack(fill=X, padx=5, pady=(5, 2))

        ttk.Button(toolbar, text="Agregar", bootstyle="success-outline",
                   command=self._add_surface_load, width=9).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="Eliminar", bootstyle="danger-outline",
                   command=self._remove_surface_load, width=9).pack(side=LEFT, padx=2)

        columns = ("elem", "n_start", "n_end", "q_start", "q_end", "angle")
        self.surface_tree = ttk.Treeview(
            self.surface_frame, columns=columns, show="headings",
            bootstyle="info", height=18
        )
        self.surface_tree.heading("elem", text="Elem", anchor=CENTER)
        self.surface_tree.heading("n_start", text="N. Inicio", anchor=CENTER)
        self.surface_tree.heading("n_end", text="N. Final", anchor=CENTER)
        self.surface_tree.heading("q_start", text="q Inicio", anchor=CENTER)
        self.surface_tree.heading("q_end", text="q Final", anchor=CENTER)
        self.surface_tree.heading("angle", text="Angulo", anchor=CENTER)
        for col in columns:
            self.surface_tree.column(col, width=60, anchor=CENTER)

        scrollbar = ttk.Scrollbar(self.surface_frame, orient=VERTICAL,
                                  command=self.surface_tree.yview)
        self.surface_tree.configure(yscrollcommand=scrollbar.set)
        self.surface_tree.pack(fill=BOTH, expand=YES, padx=5, pady=2, side=LEFT)
        scrollbar.pack(fill=Y, side=RIGHT, pady=2, padx=(0, 5))

    # ═════════════════════════════════════════════════════════════════════
    # ACCIONES DE NODOS
    # ═════════════════════════════════════════════════════════════════════

    def _add_node(self):
        dialog = _InputDialog(
            self.frame.winfo_toplevel(), "Agregar Nodo",
            [("X:", "0.0"), ("Y:", "0.0")]
        )
        if dialog.result:
            try:
                x = float(dialog.result[0])
                y = float(dialog.result[1])
                node = self.project.add_node(x, y)
                self._refresh_nodes_tree()
                self.main_window.mesh_canvas.redraw()
                self.main_window._update_status_info()
                self.main_window.set_status(f"Nodo {node.id} agregado en ({x}, {y})")
            except ValueError:
                messagebox.showerror("Error", "Coordenadas invalidas.")

    def _remove_node(self):
        selected = self.nodes_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione un nodo para eliminar.")
            return
        for item in selected:
            node_id = int(self.nodes_tree.item(item)["values"][0])
            self.project.remove_node(node_id)
        self._refresh_nodes_tree()
        self.main_window.mesh_canvas.redraw()
        self.main_window._update_status_info()
        self.main_window.set_status("Nodo(s) eliminado(s).")

    def _import_nodes_csv(self):
        filepath = filedialog.askopenfilename(
            title="Importar Nodos (CSV)",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")]
        )
        if not filepath:
            return
        try:
            with open(filepath, "r") as f:
                reader = csv.reader(f)
                next(reader, None)
                count = 0
                for row in reader:
                    if len(row) >= 2:
                        x, y = float(row[0]), float(row[1])
                        nid = int(row[2]) if len(row) >= 3 else None
                        self.project.add_node(x, y, nid)
                        count += 1
            self._refresh_nodes_tree()
            self.main_window.mesh_canvas.redraw()
            self.main_window._update_status_info()
            self.main_window.set_status(f"{count} nodos importados desde CSV.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al importar CSV:\n{e}")

    def _export_nodes_csv(self):
        filepath = filedialog.asksaveasfilename(
            title="Exportar Nodos (CSV)",
            defaultextension=".csv", filetypes=[("CSV", "*.csv")]
        )
        if not filepath:
            return
        try:
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["X", "Y", "ID"])
                for node in sorted(self.project.nodes.values(), key=lambda n: n.id):
                    writer.writerow([node.x, node.y, node.id])
            self.main_window.set_status(f"Nodos exportados a {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar CSV:\n{e}")

    def _on_node_double_click(self, event):
        item = self.nodes_tree.identify_row(event.y)
        col = self.nodes_tree.identify_column(event.x)
        if not item or not col:
            return
        column_index = int(col.replace("#", "")) - 1
        if column_index == 0:
            return

        values = self.nodes_tree.item(item)["values"]
        node_id = int(values[0])
        node = self.project.nodes.get(node_id)
        if not node:
            return

        bbox = self.nodes_tree.bbox(item, col)
        if not bbox:
            return

        entry = ttk.Entry(self.nodes_tree, width=10)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.insert(0, str(values[column_index]))
        entry.select_range(0, tk.END)
        entry.focus_set()

        def save_edit(e=None):
            try:
                new_val = float(entry.get())
                if column_index == 1:
                    node.x = new_val
                elif column_index == 2:
                    node.y = new_val
                self.project.is_modified = True
                self.project.is_solved = False
                self._refresh_nodes_tree()
                self.main_window.mesh_canvas.redraw()
            except ValueError:
                messagebox.showerror("Error", "Valor numerico invalido.")
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
        entry.bind("<Escape>", lambda e: entry.destroy())

    def _on_node_select(self, event):
        selected = self.nodes_tree.selection()
        if selected:
            node_id = int(self.nodes_tree.item(selected[0])["values"][0])
            self.main_window.mesh_canvas.highlight_node(node_id)
            self.main_window.set_status(f"Nodo {node_id} seleccionado")

    # ═════════════════════════════════════════════════════════════════════
    # ACCIONES DE ELEMENTOS
    # ═════════════════════════════════════════════════════════════════════

    def _add_element(self):
        mat_names = list(self.project.materials.keys())
        dialog = _InputDialog(
            self.frame.winfo_toplevel(), "Agregar Elemento (Q4)",
            [("Nodo 1:", ""), ("Nodo 2:", ""), ("Nodo 3:", ""), ("Nodo 4:", ""),
             ("Espesor:", str(self.project.default_thickness))],
            combo_options={"Material:": mat_names},
        )
        if dialog.result:
            try:
                n1, n2, n3, n4 = [int(dialog.result[i]) for i in range(4)]
                thickness = float(dialog.result[4])
                material = dialog.result[5] if len(dialog.result) > 5 else mat_names[0]
                for nid in [n1, n2, n3, n4]:
                    if nid not in self.project.nodes:
                        messagebox.showerror("Error", f"El nodo {nid} no existe.")
                        return
                elem = self.project.add_element([n1, n2, n3, n4], thickness, material)
                self._refresh_elements_tree()
                self.main_window.mesh_canvas.redraw()
                self.main_window._update_status_info()
                self.main_window.set_status(f"Elemento {elem.id} agregado.")
            except ValueError:
                messagebox.showerror("Error", "Valores invalidos.")

    def _remove_element(self):
        selected = self.elements_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione un elemento.")
            return
        for item in selected:
            eid = int(self.elements_tree.item(item)["values"][0])
            self.project.remove_element(eid)
        self._refresh_elements_tree()
        self.main_window.mesh_canvas.redraw()
        self.main_window._update_status_info()

    def _on_element_double_click(self, event):
        item = self.elements_tree.identify_row(event.y)
        col = self.elements_tree.identify_column(event.x)
        if not item or not col:
            return
        ci = int(col.replace("#", "")) - 1
        if ci == 0:
            return

        values = self.elements_tree.item(item)["values"]
        eid = int(values[0])
        elem = self.project.elements.get(eid)
        if not elem:
            return

        bbox = self.elements_tree.bbox(item, col)
        if not bbox:
            return

        entry = ttk.Entry(self.elements_tree, width=10)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.insert(0, str(values[ci]))
        entry.select_range(0, tk.END)
        entry.focus_set()

        def save_edit(e=None):
            try:
                val = entry.get()
                if ci in (1, 2, 3, 4):
                    elem.node_ids[ci - 1] = int(val)
                elif ci == 5:
                    elem.thickness = float(val)
                elif ci == 6:
                    elem.material_name = val
                self.project.is_modified = True
                self.project.is_solved = False
                self._refresh_elements_tree()
                self.main_window.mesh_canvas.redraw()
            except ValueError:
                messagebox.showerror("Error", "Valor invalido.")
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
        entry.bind("<Escape>", lambda e: entry.destroy())

    def _on_element_select(self, event):
        selected = self.elements_tree.selection()
        if selected:
            eid = int(self.elements_tree.item(selected[0])["values"][0])
            self.main_window.mesh_canvas.highlight_element(eid)
            self.main_window.set_status(f"Elemento {eid} seleccionado")

    # ═════════════════════════════════════════════════════════════════════
    # ACCIONES DE CARGAS
    # ═════════════════════════════════════════════════════════════════════

    def _add_load(self):
        dialog = _InputDialog(
            self.frame.winfo_toplevel(), "Agregar Carga Nodal",
            [("Nodo:", ""), ("Fx:", "0.0"), ("Fy:", "0.0")]
        )
        if dialog.result:
            try:
                nid = int(dialog.result[0])
                fx = float(dialog.result[1])
                fy = float(dialog.result[2])
                if nid not in self.project.nodes:
                    messagebox.showerror("Error", f"El nodo {nid} no existe.")
                    return
                self.project.set_nodal_load(nid, fx, fy)
                self._refresh_loads_tree()
                self.main_window.mesh_canvas.redraw()
                self.main_window.set_status(f"Carga en nodo {nid}: Fx={fx}, Fy={fy}")
            except ValueError:
                messagebox.showerror("Error", "Valores invalidos.")

    def _remove_load(self):
        selected = self.loads_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione una carga.")
            return
        for item in selected:
            nid = int(self.loads_tree.item(item)["values"][0])
            self.project.remove_nodal_load(nid)
        self._refresh_loads_tree()
        self.main_window.mesh_canvas.redraw()

    def _on_load_double_click(self, event):
        item = self.loads_tree.identify_row(event.y)
        col = self.loads_tree.identify_column(event.x)
        if not item or not col:
            return
        ci = int(col.replace("#", "")) - 1
        if ci == 0:
            return

        values = self.loads_tree.item(item)["values"]
        nid = int(values[0])
        load = self.project.nodal_loads.get(nid)
        if not load:
            return

        bbox = self.loads_tree.bbox(item, col)
        if not bbox:
            return

        entry = ttk.Entry(self.loads_tree, width=10)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.insert(0, str(values[ci]))
        entry.select_range(0, tk.END)
        entry.focus_set()

        def save_edit(e=None):
            try:
                val = float(entry.get())
                if ci == 1:
                    load.fx = val
                elif ci == 2:
                    load.fy = val
                self.project.is_modified = True
                self.project.is_solved = False
                self._refresh_loads_tree()
                self.main_window.mesh_canvas.redraw()
            except ValueError:
                messagebox.showerror("Error", "Valor numerico invalido.")
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
        entry.bind("<Escape>", lambda e: entry.destroy())

    # ═════════════════════════════════════════════════════════════════════
    # ACCIONES DE RESTRICCIONES
    # ═════════════════════════════════════════════════════════════════════

    def _add_constraint(self):
        dialog = _InputDialog(
            self.frame.winfo_toplevel(), "Agregar Restriccion",
            [("Nodo:", "")],
            checkboxes={"Restringir X": True, "Restringir Y": True}
        )
        if dialog.result:
            try:
                nid = int(dialog.result[0])
                rx = dialog.result[1]
                ry = dialog.result[2]
                if nid not in self.project.nodes:
                    messagebox.showerror("Error", f"El nodo {nid} no existe.")
                    return
                self.project.set_boundary_condition(nid, rx, ry)
                self._refresh_constraints_tree()
                self.main_window.mesh_canvas.redraw()
                self.main_window.set_status(f"Restriccion en nodo {nid}")
            except ValueError:
                messagebox.showerror("Error", "Valor invalido.")

    def _remove_constraint(self):
        selected = self.constraints_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione una restriccion.")
            return
        for item in selected:
            nid = int(self.constraints_tree.item(item)["values"][0])
            self.project.remove_boundary_condition(nid)
        self._refresh_constraints_tree()
        self.main_window.mesh_canvas.redraw()

    def _on_constraint_click(self, event):
        region = self.constraints_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        item = self.constraints_tree.identify_row(event.y)
        col = self.constraints_tree.identify_column(event.x)
        if not item or not col:
            return
        ci = int(col.replace("#", "")) - 1
        if ci == 0:
            return

        values = list(self.constraints_tree.item(item)["values"])
        nid = int(values[0])
        bc = self.project.boundary_conditions.get(nid)
        if not bc:
            return

        if ci == 1:
            bc.restrain_x = not bc.restrain_x
        elif ci == 2:
            bc.restrain_y = not bc.restrain_y

        self.project.is_modified = True
        self.project.is_solved = False
        self._refresh_constraints_tree()
        self.main_window.mesh_canvas.redraw()

    # ═════════════════════════════════════════════════════════════════════
    # ACCIONES DE CARGAS SUPERFICIALES
    # ═════════════════════════════════════════════════════════════════════

    def _add_surface_load(self):
        dialog = _InputDialog(
            self.frame.winfo_toplevel(), "Agregar Carga Superficial",
            [("Elemento:", ""), ("Nodo Inicio:", ""), ("Nodo Final:", ""),
             ("q Inicio:", "0.0"), ("q Final:", "0.0"), ("Angulo:", "0.0")]
        )
        if dialog.result:
            try:
                eid = int(dialog.result[0])
                ns = int(dialog.result[1])
                ne = int(dialog.result[2])
                qs = float(dialog.result[3])
                qe = float(dialog.result[4])
                angle = float(dialog.result[5])
                self.project.add_surface_load(eid, ns, ne, qs, qe, angle)
                self._refresh_surface_tree()
                self.main_window.mesh_canvas.redraw()
                self.main_window.set_status("Carga superficial agregada.")
            except ValueError:
                messagebox.showerror("Error", "Valores invalidos.")

    def _remove_surface_load(self):
        selected = self.surface_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione una carga.")
            return
        indices = []
        for item in selected:
            indices.append(self.surface_tree.index(item))
        for idx in sorted(indices, reverse=True):
            if idx < len(self.project.surface_loads):
                del self.project.surface_loads[idx]
        self._refresh_surface_tree()
        self.main_window.mesh_canvas.redraw()

    # ═════════════════════════════════════════════════════════════════════
    # REFRESCAR TABLAS
    # ═════════════════════════════════════════════════════════════════════

    def _refresh_nodes_tree(self):
        self.nodes_tree.delete(*self.nodes_tree.get_children())
        for node in sorted(self.project.nodes.values(), key=lambda n: n.id):
            self.nodes_tree.insert(
                "", END, values=(node.id, f"{node.x:.4f}", f"{node.y:.4f}")
            )

    def _refresh_elements_tree(self):
        self.elements_tree.delete(*self.elements_tree.get_children())
        for elem in sorted(self.project.elements.values(), key=lambda e: e.id):
            nids = list(elem.node_ids)
            while len(nids) < 4:
                nids.append("")
            self.elements_tree.insert(
                "", END,
                values=(elem.id, nids[0], nids[1], nids[2], nids[3],
                        f"{elem.thickness:.4f}", elem.material_name)
            )

    def _refresh_loads_tree(self):
        self.loads_tree.delete(*self.loads_tree.get_children())
        for load in sorted(self.project.nodal_loads.values(), key=lambda l: l.node_id):
            self.loads_tree.insert(
                "", END, values=(load.node_id, f"{load.fx:.4f}", f"{load.fy:.4f}")
            )

    def _refresh_constraints_tree(self):
        self.constraints_tree.delete(*self.constraints_tree.get_children())
        for bc in sorted(self.project.boundary_conditions.values(), key=lambda b: b.node_id):
            rx = "Si" if bc.restrain_x else "No"
            ry = "Si" if bc.restrain_y else "No"
            self.constraints_tree.insert("", END, values=(bc.node_id, rx, ry))

    def _refresh_surface_tree(self):
        self.surface_tree.delete(*self.surface_tree.get_children())
        for sl in self.project.surface_loads:
            self.surface_tree.insert(
                "", END,
                values=(sl.element_id, sl.node_start, sl.node_end,
                        f"{sl.q_start:.4f}", f"{sl.q_end:.4f}", f"{sl.angle:.1f}")
            )

    def refresh(self):
        """Refresca toda la pestana de pre-proceso."""
        self._refresh_nodes_tree()
        self._refresh_elements_tree()
        self._refresh_loads_tree()
        self._refresh_constraints_tree()
        self._refresh_surface_tree()


# ═════════════════════════════════════════════════════════════════════════
# DIALOGO DE ENTRADA REUTILIZABLE
# ═════════════════════════════════════════════════════════════════════════

class _InputDialog:
    """Dialogo generico de entrada de datos."""

    def __init__(self, parent, title, fields, combo_options=None, checkboxes=None):
        self.result = None
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)

        self.entries = []
        self.check_vars = []

        for i, (label, default) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(
                row=i, column=0, sticky=E, pady=3, padx=(0, 8)
            )
            entry = ttk.Entry(main_frame, width=20)
            entry.insert(0, default)
            entry.grid(row=i, column=1, sticky=W, pady=3)
            self.entries.append(entry)

        row_offset = len(fields)

        if combo_options:
            for label, options in combo_options.items():
                ttk.Label(main_frame, text=label).grid(
                    row=row_offset, column=0, sticky=E, pady=3, padx=(0, 8)
                )
                combo = ttk.Combobox(main_frame, values=options, state="readonly", width=17)
                if options:
                    combo.current(0)
                combo.grid(row=row_offset, column=1, sticky=W, pady=3)
                self.entries.append(combo)
                row_offset += 1

        if checkboxes:
            for label, default in checkboxes.items():
                var = tk.BooleanVar(value=default)
                ttk.Checkbutton(
                    main_frame, text=label, variable=var, bootstyle="round-toggle"
                ).grid(row=row_offset, column=0, columnspan=2, sticky=W, pady=3)
                self.check_vars.append(var)
                row_offset += 1

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row_offset, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(btn_frame, text="Aceptar", bootstyle="success",
                   command=self._on_ok, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", bootstyle="danger",
                   command=self._on_cancel, width=10).pack(side=LEFT, padx=5)

        if self.entries:
            self.entries[0].focus_set()
        self.dialog.bind("<Return>", lambda e: self._on_ok())
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())

        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.dialog.geometry(f"+{x}+{y}")
        self.dialog.wait_window()

    def _on_ok(self):
        self.result = [e.get() for e in self.entries]
        for var in self.check_vars:
            self.result.append(var.get())
        self.dialog.destroy()

    def _on_cancel(self):
        self.result = None
        self.dialog.destroy()
