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

import traceback

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from config.settings import LABEL_BG, LABEL_FG, CANVAS_SELECTED_ROW_BG, CANVAS_SELECTED_ROW_FG
from gui.preprocessing._table_helpers import to_float_flex
from models.material import Material, POISSON_MAX, POISSON_MIN


from gui.dialogs._dialog_helpers import bind_dialog_keys, center_dialog


# Etiqueta visible de cada campo del editor. Fuente unica: la consume el
# form Y el aviso del Return cuando algun campo bloquea el guardado.
_FIELD_LABELS = {
    "name":    "Nombre",
    "E":       "Módulo de Young  E",
    "nu":      "Coef. de Poisson ν",
    "density": "Densidad  ρ",
}


class MaterialDialog:
    """Ventana de gestion de materiales del proyecto."""

    def __init__(self, parent, project, main_window=None, *, seleccionar=None):
        """`seleccionar`: nombre del material que queda elegido al abrir. Lo usa
        el "📍 Ir al item" del reporte de salud para llevar al alumno al
        material que causa el issue."""
        self.project = project
        self.main_window = main_window
        self.parent = parent

        self.selected_name = (seleccionar
                              if seleccionar in project.materials else None)
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
        # Escape cierra (no hay Aceptar global: cada material se guarda
        # con su propio botón). Return guarda el material abierto.
        bind_dialog_keys(self.dialog,
                         on_escape=self.dialog.destroy, on_return=self._on_return)

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
            (clave, _FIELD_LABELS[clave], var)
            for clave, var in (
                ("name",    self.var_name),
                ("E",       self.var_E),
                ("nu",      self.var_nu),
                ("density", self.var_density),
            )
        ]

        # Los Entry se guardan por clave para poder marcar en rojo el campo que
        # mantiene deshabilitado el boton Guardar: sin esa marca, el unico
        # feedback era un boton gris que no dice cual de los 4 campos esta mal.
        # No es un status label (decision tomada, ver arquitectura.md): es el
        # propio control el que se señala.
        self._entries = {}
        for i, (clave, label, var) in enumerate(fields):
            ttk.Label(edit, text=label, font=("Segoe UI", 10)).grid(
                row=i, column=0, sticky=E, pady=4, padx=(0, 8)
            )
            entry = ttk.Entry(
                edit, textvariable=var, font=("Segoe UI", 10), width=22,
            )
            entry.grid(row=i, column=1, sticky=W, pady=4)
            self._entries[clave] = entry

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

    def campos_invalidos(self):
        """Claves de los campos que hoy impiden guardar, en orden de fila.

        Los numeros se leen con `to_float_flex`, no con `float()`: un Excel en
        español escribe `0,3` y el resto del programa ya lo acepta (editores de
        celda del spreadsheet desde 2026-09, campos del Post desde 2026-09).
        Aca `0,3` en ν dejaba el boton Guardar gris para siempre, sin decir por
        que — dos reglas distintas para escribir el mismo numero.
        """
        malos = []
        if not self.var_name.get().strip():
            malos.append("name")
        try:
            if to_float_flex(self.var_E.get()) <= 0:
                malos.append("E")
        except (ValueError, TypeError):
            malos.append("E")
        try:
            # Mismos limites que `Material.validate()` y que el chequeo
            # `_check_material_properties` del reporte de salud.
            if not (POISSON_MIN < to_float_flex(self.var_nu.get()) < POISSON_MAX):
                malos.append("nu")
        except (ValueError, TypeError):
            malos.append("nu")
        try:
            if to_float_flex(self.var_density.get()) < 0:
                malos.append("density")
        except (ValueError, TypeError):
            malos.append("density")
        return malos

    def _validate_live(self):
        """Habilita el boton Guardar si y solo si TODOS los campos son validos,
        y marca en rojo los que no lo son. Sigue sin haber status label (ver
        arquitectura.md): el feedback es el estado del boton MAS el borde del
        campo culpable, que es lo que faltaba para saber cual arreglar."""
        malos = set(self.campos_invalidos())
        for clave, entry in getattr(self, "_entries", {}).items():
            try:
                entry.configure(bootstyle="danger" if clave in malos else "default")
            except tk.TclError:
                pass
        self.save_btn.configure(state="disabled" if malos else "normal")

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
        self._mark_dirty()
        self.selected_name = name
        self._populate_list()
        self._notify_main_window(f"Material «{name}» agregado.")

    def _remove_material(self):
        if not self.selected_name:
            return
        if len(self.project.materials) <= 1:
            messagebox.showwarning(
                "Aviso", "Debe haber al menos un material.",
                parent=self.dialog,
            )
            return
        # Cuantos elementos se quedan sin material: borrarlo los deja
        # apuntando a un nombre inexistente y el modelo pasa a tener un error
        # critico (ELEM_MATERIAL_MISSING) que el alumno recien ve al resolver.
        # La confirmacion tiene que nombrar la consecuencia, no solo el nombre.
        en_uso = sum(1 for e in self.project.elements.values()
                     if e.material_name == self.selected_name)
        aviso = f"¿Eliminar '{self.selected_name}'?"
        if en_uso:
            aviso += (
                f"\n\n{en_uso} elemento(s) lo tienen asignado y van a quedar "
                f"sin material: el modelo no se va a poder resolver hasta que "
                f"les asignes otro desde la tabla de Elementos.\n\n"
                f"Se puede deshacer con Ctrl+Z."
            )
        if not messagebox.askyesno(
            "Eliminar material", aviso, parent=self.dialog,
        ):
            return
        borrado = self.selected_name
        self._capture(f"eliminar material '{borrado}'")
        del self.project.materials[borrado]
        self._mark_dirty()
        self.selected_name = None
        self._populate_list()
        aviso_estado = f"Material «{borrado}» eliminado."
        if en_uso:
            aviso_estado += f" {en_uso} elemento(s) quedaron sin material."
        self._notify_main_window(aviso_estado)

    def _on_return(self):
        """Return dentro del diálogo = 💾 Guardar cambios.

        Es la única acción primaria del panel derecho, que es donde está
        el foco mientras se tipea. Si algún campo es inválido el botón
        está gris: en vez de no hacer nada, se repinta la marca roja y se
        nombra el campo culpable en la barra de estado — el mismo criterio
        que el resto de los diálogos (ningún control visible queda mudo).
        """
        if not self.selected_name:
            self._status("Elegí primero un material de la lista.")
            return
        malos = self.campos_invalidos()
        if malos:
            self._validate_live()          # repinta los Entry en rojo
            # `split()` + `join` colapsa el doble espacio con que el form
            # separa el símbolo de su nombre ("Densidad  ρ").
            nombres = ", ".join(
                " ".join(_FIELD_LABELS.get(c, c).split()) for c in malos
            )
            self._status(f"Revisá {nombres} antes de guardar el material.")
            return
        self._save_material()

    def _status(self, mensaje):
        """Canal de aviso del diálogo: la barra de estado de la ventana
        principal (sin status label propio, ver arquitectura.md)."""
        if self.main_window is not None:
            try:
                self.main_window.set_status(mensaje)
            except Exception:
                traceback.print_exc()

    def _save_material(self):
        if not self.selected_name:
            return
        new_name = self.var_name.get().strip()
        if not new_name:
            messagebox.showerror(
                "Error", "El nombre no puede estar vacío.",
                parent=self.dialog,
            )
            return
        # Misma lectura tolerante que la validacion live: si el boton Guardar
        # esta habilitado, estos tres parseos no pueden fallar.
        try:
            E = to_float_flex(self.var_E.get())
            nu = to_float_flex(self.var_nu.get())
            density = to_float_flex(self.var_density.get())
        except (ValueError, TypeError):
            etiquetas = {"E": "Módulo de Young E", "nu": "Coef. de Poisson ν",
                         "density": "Densidad ρ", "name": "Nombre"}
            malos = ", ".join(etiquetas[c] for c in self.campos_invalidos())
            messagebox.showerror(
                "Error",
                f"Revisá estos campos: {malos}.\n\n"
                f"Los números se escriben con punto o coma decimal "
                f"(ej. 0.3 o 0,3).",
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
        self._mark_dirty()
        self.selected_name = new_name
        self._populate_list()
        renombrado = "" if new_name == old_name else f" (antes «{old_name}»)"
        self._notify_main_window(f"Material «{new_name}» guardado{renombrado}.")

    # ═════════════════════════════════════════════════════════════════════
    # NOTIFICACION + UNDO
    # ═════════════════════════════════════════════════════════════════════

    def _mark_dirty(self):
        """Marca el proyecto como modificado E INVALIDA la solucion.

        Regla dura 12. Faltaba el `is_solved = False`, y no era cosmetico:
        `post_tab._auto_solve` corta con `if self.solution is not None and
        self.project.is_solved: return`, asi que tras cambiar E, ν o ρ el
        **F5 no recalculaba** — el alumno veia los desplazamientos y las
        tensiones del material viejo, sin ningun aviso. Y *Exportar Memoria
        PDF* seguia habilitado (`_refresh_menu_state` mira `is_solved`),
        generando un documento con la tabla del material nuevo y la K, la u
        y las σ de la corrida vieja. K depende de E y de ν via D, y F del
        peso propio depende de ρ: cualquier edicion de la libreria invalida
        la corrida. El autofix de `UNUSED_MATERIAL` en
        `models/model_health.py` ya lo hacia bien; este dialogo era el unico
        camino de mutacion del proyecto que no.
        """
        self.project.is_modified = True
        self.project.is_solved = False

    def _notify_main_window(self, status=None):
        if self.main_window is not None:
            try:
                self.main_window._refresh_all_tabs()
                # Recalcula el badge de salud: borrar un material en uso deja
                # los elementos apuntando a un nombre inexistente (error
                # critico ELEM_MATERIAL_MISSING) y el badge seguia diciendo
                # "✓ Modelo sano" hasta la siguiente accion en otra pestaña.
                self.main_window._update_status_info()
                self.main_window._update_title()
                if status:
                    # Era el unico dialogo del menu Modelo que no decia nada
                    # en la barra de estado: Unidades, Gravedad, Tipo de
                    # analisis y Tipo de elemento si lo hacen.
                    self.main_window.set_status(status)
            except Exception:
                # Si falla, las tablas del Pre siguen mostrando el material
                # viejo: sin traza es indepurable.
                traceback.print_exc()

    def _capture(self, label):
        """Snapshot del estado actual en el undo stack. Llamar ANTES de
        mutar `project.materials`."""
        try:
            stack = getattr(self.main_window, "undo_stack", None)
            if stack is not None:
                stack.capture(label)
        except Exception:
            # Sin snapshot esta accion queda fuera del Ctrl+Z (regla dura 4).
            traceback.print_exc()

    # ═════════════════════════════════════════════════════════════════════
    # CENTRADO
    # ═════════════════════════════════════════════════════════════════════

    def _center(self):
        center_dialog(self.dialog, self.parent)
