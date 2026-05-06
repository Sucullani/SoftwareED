"""
MaterialDialog: Diálogo interactivo para gestionar la librería de materiales
del proyecto.

Diseño:
- Panel izquierdo: lista de materiales con un swatch de color a la izquierda
  de cada nombre (Canvas custom, render directo — no listbox).
- Panel derecho: propiedades con entries validados, color picker y tarjeta
  de vista previa que se actualiza en vivo mientras el usuario escribe.
- Botón "📚 Importar material típico…" con picker de 12 materiales comunes.

Valores de los típicos en N/mm/MPa (consistentes con DEFAULT_UNIT_SYSTEM).
Densidad en kg/m³. El usuario debe convertir si usa otro sistema.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, colorchooser

from models.material import Material


# Valores en unidades SI (N, mm, MPa) — consistentes con DEFAULT_UNIT_SYSTEM.
# Densidad en kg/m³.
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

# Paleta rápida sugerida (click para aplicar)
QUICK_PALETTE = [
    "#4fc3f7", "#81c784", "#ffb74d", "#ba68c8",
    "#e57373", "#ffd54f", "#4db6ac", "#90a4ae",
    "#a1887f", "#f06292", "#aed581", "#7986cb",
]


class MaterialDialog:
    """Ventana interactiva de gestión de propiedades de materiales."""

    def __init__(self, parent, project, main_window=None):
        self.project = project
        self.main_window = main_window
        self.parent = parent

        # Estado de edición
        self.selected_name = None
        self._suppress_preview = False

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("🧱  Propiedades de Material")
        self.dialog.geometry("780x560")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.minsize(720, 500)

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
        ).pack(anchor=W)
        ttk.Label(
            main,
            text="Edita las propiedades y observa la vista previa actualizarse en vivo.",
            foreground="#aaa", font=("Segoe UI", 9),
        ).pack(anchor=W, pady=(0, 10))

        paned = ttk.Panedwindow(main, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=YES)

        # ─── Panel izquierdo: lista de materiales ───────────────────────
        left = ttk.Frame(paned)
        paned.add(left, weight=2)
        self._build_list_panel(left)

        # ─── Panel derecho: editor interactivo ──────────────────────────
        right = ttk.Frame(paned)
        paned.add(right, weight=3)
        self._build_editor_panel(right)

        # ─── Botones de cierre ──────────────────────────────────────────
        close_bar = ttk.Frame(main)
        close_bar.pack(fill=X, pady=(10, 0))
        ttk.Button(
            close_bar, text="Cerrar", bootstyle="secondary",
            command=self.dialog.destroy, width=12,
        ).pack(side=RIGHT)

    def _build_list_panel(self, parent):
        header = ttk.Frame(parent)
        header.pack(fill=X, pady=(0, 4))
        ttk.Label(
            header, text="Materiales", font=("Segoe UI", 10, "bold")
        ).pack(side=LEFT)
        self.count_lbl = ttk.Label(
            header, text="", foreground="#888", font=("Segoe UI", 9)
        )
        self.count_lbl.pack(side=RIGHT)

        # Lista custom con swatch: Canvas scrollable con rows
        list_frame = ttk.Frame(parent, bootstyle="dark")
        list_frame.pack(fill=BOTH, expand=YES)

        self.list_canvas = tk.Canvas(
            list_frame, highlightthickness=0, bg="#2b2b2b",
        )
        vsb = ttk.Scrollbar(
            list_frame, orient=VERTICAL, command=self.list_canvas.yview,
        )
        self.list_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=RIGHT, fill=Y)
        self.list_canvas.pack(side=LEFT, fill=BOTH, expand=YES)

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

        # Botones
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, pady=(8, 0))
        ttk.Button(
            btn_frame, text="➕ Nuevo", bootstyle="success-outline",
            command=self._add_material, width=9,
        ).pack(side=LEFT, padx=2)
        ttk.Button(
            btn_frame, text="🗑 Eliminar", bootstyle="danger-outline",
            command=self._remove_material, width=10,
        ).pack(side=LEFT, padx=2)
        ttk.Button(
            btn_frame, text="📋 Duplicar", bootstyle="secondary-outline",
            command=self._duplicate_material, width=10,
        ).pack(side=LEFT, padx=2)

        ttk.Button(
            parent, text="📚  Importar material típico…",
            bootstyle="info-outline",
            command=self._import_typical_material,
        ).pack(fill=X, pady=(6, 0))

    def _build_editor_panel(self, parent):
        # Tarjeta de vista previa (arriba del todo)
        preview = ttk.Labelframe(
            parent, text="  Vista previa en vivo  ", padding=10,
            bootstyle="info",
        )
        preview.pack(fill=X, pady=(0, 10))

        self.preview_canvas = tk.Canvas(
            preview, height=64, highlightthickness=0, bg="#1a1a1a",
        )
        self.preview_canvas.pack(fill=X)

        self.preview_info_lbl = ttk.Label(
            preview, text="", font=("Consolas", 9), foreground="#ccc",
            justify=LEFT,
        )
        self.preview_info_lbl.pack(anchor=W, pady=(6, 0))

        # Formulario de edición
        edit = ttk.Labelframe(parent, text="  Edición  ", padding=14)
        edit.pack(fill=BOTH, expand=YES)

        # StringVars para traces
        self.var_name = tk.StringVar()
        self.var_E = tk.StringVar()
        self.var_nu = tk.StringVar()
        self.var_density = tk.StringVar()
        self.var_color = tk.StringVar(value="#4fc3f7")

        fields = [
            ("Nombre",             self.var_name,    "Texto descriptivo (único)."),
            ("Módulo de Young  E", self.var_E,       "Rigidez del material. Unidades de tensión del sistema."),
            ("Coef. de Poisson ν", self.var_nu,      "Adimensional, entre -1 y 0.5."),
            ("Densidad  ρ",        self.var_density, "Masa por unidad de volumen (kg/m³ o equivalente)."),
        ]

        for i, (label, var, hint) in enumerate(fields):
            ttk.Label(edit, text=label, font=("Segoe UI", 10)).grid(
                row=i * 2, column=0, sticky=E, pady=(4, 0), padx=(0, 8)
            )
            entry = ttk.Entry(
                edit, textvariable=var, font=("Segoe UI", 10), width=22,
            )
            entry.grid(row=i * 2, column=1, sticky=W, pady=(4, 0))
            ttk.Label(
                edit, text=hint, foreground="#888", font=("Segoe UI", 8),
            ).grid(row=i * 2 + 1, column=1, sticky=W, pady=(0, 2))

        # Color picker + swatch + paleta rápida
        color_row = ttk.Frame(edit)
        color_row.grid(row=len(fields) * 2, column=0, columnspan=2,
                       sticky=EW, pady=(10, 4))
        ttk.Label(
            color_row, text="Color", font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(0, 10))

        self.color_swatch = tk.Canvas(
            color_row, width=34, height=26, highlightthickness=1,
            highlightbackground="#555", bg="#4fc3f7",
        )
        self.color_swatch.pack(side=LEFT, padx=(0, 8))

        ttk.Button(
            color_row, text="🎨  Elegir…", bootstyle="info-outline",
            command=self._pick_color, width=11,
        ).pack(side=LEFT)

        # Paleta rápida
        palette_row = ttk.Frame(edit)
        palette_row.grid(row=len(fields) * 2 + 1, column=0, columnspan=2,
                         sticky=W, pady=(2, 4))
        ttk.Label(
            palette_row, text="Paleta:", font=("Segoe UI", 8),
            foreground="#888",
        ).pack(side=LEFT, padx=(0, 6))
        for c in QUICK_PALETTE:
            sw = tk.Canvas(
                palette_row, width=18, height=18, highlightthickness=1,
                highlightbackground="#444", bg=c, cursor="hand2",
            )
            sw.pack(side=LEFT, padx=1)
            sw.bind("<Button-1>", lambda _e, col=c: self._apply_color(col))

        edit.columnconfigure(1, weight=1)

        # Validación / estado
        self.status_lbl = ttk.Label(
            edit, text="", font=("Segoe UI", 9), foreground="#888",
        )
        self.status_lbl.grid(row=len(fields) * 2 + 2, column=0, columnspan=2,
                             sticky=W, pady=(6, 4))

        # Botón guardar
        self.save_btn = ttk.Button(
            edit, text="💾  Guardar cambios", bootstyle="success",
            command=self._save_material,
        )
        self.save_btn.grid(row=len(fields) * 2 + 3, column=0, columnspan=2,
                           sticky=EW, pady=(6, 0))

        # Live traces
        for var in (self.var_name, self.var_E, self.var_nu,
                    self.var_density, self.var_color):
            var.trace_add("write", lambda *_: self._on_field_changed())

    # ═════════════════════════════════════════════════════════════════════
    # POBLAR LISTA
    # ═════════════════════════════════════════════════════════════════════

    def _populate_list(self):
        for w in self.list_inner.winfo_children():
            w.destroy()

        names = sorted(self.project.materials.keys())
        self.count_lbl.config(text=f"{len(names)} material(es)")

        self._row_widgets = {}  # name -> row frame
        for name in names:
            mat = self.project.materials[name]
            row = tk.Frame(self.list_inner, bg="#2b2b2b", cursor="hand2")
            row.pack(fill=X, padx=4, pady=2)

            swatch = tk.Canvas(
                row, width=14, height=20, highlightthickness=1,
                highlightbackground="#555", bg=mat.color,
            )
            swatch.pack(side=LEFT, padx=(6, 8), pady=3)

            lbl = tk.Label(
                row, text=name, bg="#2b2b2b", fg="#eee",
                font=("Segoe UI", 10), anchor=W,
            )
            lbl.pack(side=LEFT, fill=X, expand=YES, pady=3)

            # Info compacta a la derecha
            meta = tk.Label(
                row,
                text=f"E={mat.E:g}  ν={mat.nu:g}",
                bg="#2b2b2b", fg="#888", font=("Consolas", 8),
            )
            meta.pack(side=RIGHT, padx=6)

            # Click handler para todo el row
            for widget in (row, swatch, lbl, meta):
                widget.bind(
                    "<Button-1>",
                    lambda _e, n=name: self._select(n),
                )

            self._row_widgets[name] = (row, lbl, meta, swatch)

        # Re-seleccionar o cargar el primero
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

        # Resaltar row
        for n, (row, lbl, meta, _sw) in self._row_widgets.items():
            if n == name:
                row.config(bg="#0d6efd")
                lbl.config(bg="#0d6efd", fg="white")
                meta.config(bg="#0d6efd", fg="#e9ecef")
            else:
                row.config(bg="#2b2b2b")
                lbl.config(bg="#2b2b2b", fg="#eee")
                meta.config(bg="#2b2b2b", fg="#888")

        # Cargar en editor sin disparar preview spam
        self._suppress_preview = True
        self.var_name.set(mat.name)
        self.var_E.set(f"{mat.E:g}")
        self.var_nu.set(f"{mat.nu:g}")
        self.var_density.set(f"{mat.density:g}")
        self.var_color.set(mat.color)
        self._suppress_preview = False
        self._refresh_preview()

    def _clear_editor(self):
        self._suppress_preview = True
        self.var_name.set("")
        self.var_E.set("")
        self.var_nu.set("")
        self.var_density.set("")
        self.var_color.set("#4fc3f7")
        self._suppress_preview = False
        self.preview_canvas.delete("all")
        self.preview_info_lbl.config(text="(sin material seleccionado)")
        self.status_lbl.config(text="", foreground="#888")

    # ═════════════════════════════════════════════════════════════════════
    # LIVE PREVIEW
    # ═════════════════════════════════════════════════════════════════════

    def _on_field_changed(self):
        if self._suppress_preview:
            return
        self._refresh_preview()

    def _refresh_preview(self):
        color = self.var_color.get() or "#4fc3f7"
        # Actualizar swatch del color picker
        try:
            self.color_swatch.config(bg=color)
        except tk.TclError:
            color = "#4fc3f7"
            self.color_swatch.config(bg=color)

        # Redibujar vista previa — barrita coloreada con etiqueta
        self.preview_canvas.delete("all")
        self.preview_canvas.update_idletasks()
        w = self.preview_canvas.winfo_width() or 400
        h = 64

        # Fondo
        self.preview_canvas.create_rectangle(
            0, 0, w, h, fill="#1a1a1a", outline="",
        )

        # Barra de color proporcional al módulo E (visual "rigidez")
        try:
            E_val = float(self.var_E.get())
        except (ValueError, TypeError):
            E_val = 0.0
        E_max_ref = 250000.0  # referencia: acero ~ 200 GPa en MPa
        ratio = max(0.03, min(1.0, E_val / E_max_ref)) if E_val > 0 else 0.03
        bar_w = int((w - 24) * ratio)
        self.preview_canvas.create_rectangle(
            12, 16, 12 + bar_w, 44,
            fill=color, outline="#fff", width=1,
        )
        # Texto dentro / junto
        name = self.var_name.get().strip() or "(sin nombre)"
        self.preview_canvas.create_text(
            16, 30, anchor=W,
            text=name, fill="white", font=("Segoe UI", 10, "bold"),
        )
        # Ruler
        self.preview_canvas.create_text(
            w - 12, 54, anchor=E,
            text=f"E ≈ {E_val:g}  (barra relativa a 250 GPa)",
            fill="#888", font=("Segoe UI", 8),
        )

        # Info textual
        try:
            nu = float(self.var_nu.get())
            nu_str = f"{nu:g}"
        except (ValueError, TypeError):
            nu_str = self.var_nu.get() or "?"
        try:
            rho = float(self.var_density.get())
            rho_str = f"{rho:g}"
        except (ValueError, TypeError):
            rho_str = self.var_density.get() or "?"

        self.preview_info_lbl.config(
            text=(
                f"  E  = {self.var_E.get() or '?'}\n"
                f"  ν  = {nu_str}\n"
                f"  ρ  = {rho_str}\n"
                f"  🎨  {color}"
            )
        )

        # Validación en vivo
        self._validate_live()

    def _validate_live(self):
        errs = []
        try:
            E = float(self.var_E.get())
            if E <= 0:
                errs.append("E debe ser > 0")
        except ValueError:
            errs.append("E inválido")
        try:
            nu = float(self.var_nu.get())
            if not (-1.0 < nu < 0.5):
                errs.append("ν debe estar entre -1 y 0.5")
        except ValueError:
            errs.append("ν inválido")
        try:
            rho = float(self.var_density.get())
            if rho < 0:
                errs.append("ρ no puede ser negativa")
        except ValueError:
            errs.append("ρ inválida")
        if not self.var_name.get().strip():
            errs.append("Nombre vacío")

        if errs:
            self.status_lbl.config(
                text="⚠  " + " · ".join(errs), foreground="#e57373",
            )
            self.save_btn.configure(state="disabled")
        else:
            self.status_lbl.config(
                text="✓  Válido — listo para guardar",
                foreground="#81c784",
            )
            self.save_btn.configure(state="normal")

    # ═════════════════════════════════════════════════════════════════════
    # COLOR
    # ═════════════════════════════════════════════════════════════════════

    def _pick_color(self):
        initial = self.var_color.get() or "#4fc3f7"
        result = colorchooser.askcolor(
            color=initial, title="Color del material", parent=self.dialog,
        )
        if result and result[1]:
            self._apply_color(result[1])

    def _apply_color(self, color):
        self.var_color.set(color)

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
        mat = Material(name, 200000.0, 0.3, 7850.0, "#4fc3f7")
        self.project.materials[name] = mat
        self.project.is_modified = True
        self.selected_name = name
        self._populate_list()
        self._notify_main_window()

    def _duplicate_material(self):
        if not self.selected_name:
            return
        src = self.project.materials.get(self.selected_name)
        if not src:
            return
        base = f"{src.name} (copia)"
        name = base
        i = 2
        while name in self.project.materials:
            name = f"{base} {i}"
            i += 1
        self._capture(f"duplicar material '{src.name}'")
        self.project.materials[name] = Material(
            name, src.E, src.nu, src.density, src.color
        )
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

        # Si el nombre cambió y el nuevo ya existe, rechazar
        if new_name != self.selected_name and new_name in self.project.materials:
            messagebox.showerror(
                "Error", f"Ya existe un material con el nombre '{new_name}'.",
                parent=self.dialog,
            )
            return

        mat = Material(new_name, E, nu, density, self.var_color.get())
        errors = mat.validate()
        if errors:
            messagebox.showerror("Error", "\n".join(errors), parent=self.dialog)
            return

        # Si cambió el nombre, hay que re-asociar elementos que lo usaban
        old_name = self.selected_name
        # Snapshot para undo: cubre tanto cambio de nombre como propiedades.
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
        self.status_lbl.config(
            text=f"✓  '{new_name}' guardado.", foreground="#81c784",
        )

    # ═════════════════════════════════════════════════════════════════════
    # IMPORTAR TÍPICO
    # ═════════════════════════════════════════════════════════════════════

    def _import_typical_material(self):
        """Picker de materiales típicos con previsualización."""
        picker = ttk.Toplevel(self.dialog)
        picker.title("📚  Importar material típico")
        picker.geometry("500x300")
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
        combo.pack(fill=X, pady=(0, 10))

        # Tarjeta de vista previa en el picker
        preview_card = ttk.Frame(frame, bootstyle="dark", padding=10)
        preview_card.pack(fill=X, pady=(0, 8))

        swatch = tk.Canvas(
            preview_card, width=40, height=40, highlightthickness=1,
            highlightbackground="#555",
        )
        swatch.pack(side=LEFT, padx=(0, 12))

        info_lbl = ttk.Label(
            preview_card, text="", foreground="#ddd",
            font=("Consolas", 9), justify=LEFT,
        )
        info_lbl.pack(side=LEFT, fill=X, expand=YES)

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
            swatch.config(bg=props.get("color", "#888"))
            info_lbl.config(
                text=(
                    f"  E = {props.get('E', 0):g} MPa\n"
                    f"  ν = {props.get('nu', 0):g}\n"
                    f"  ρ = {props.get('density', 0):g} kg/m³"
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
            self._capture(f"importar material tipico '{final_name}'")
            self.project.materials[final_name] = Material(name=final_name, **props)
            self.project.is_modified = True
            self.selected_name = final_name
            self._populate_list()
            self._notify_main_window()
            picker.destroy()

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

    # ═════════════════════════════════════════════════════════════════════
    # NOTIFICACION
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
        """Snapshot del estado actual del proyecto en el undo stack del
        main_window. Llamar ANTES de mutar `project.materials`."""
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
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        self.dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
