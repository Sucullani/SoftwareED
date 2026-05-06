"""
HealthReportDialog: ventana flotante (no-modal) que presenta el reporte
de salud del modelo agrupado por severidad. Cada issue ofrece:

- 🔧 Corregir: aplica el auto-fix conocido para ese codigo
- 📍 Ir al item: navega al Pre-Proceso, sub-pestana y selecciona la fila
- 🎓 Por que: hint educativo explicando el problema fisico/matematico

Footer:
- "🔄 Re-validar": vuelve a correr el validador y reconstruye la lista
  (uso tipico: el usuario corrigio manualmente desde la GUI principal).
- "Volver al Pre-Proceso": cancela y regresa al Pre-Proceso.
- "Resolver / Resolver de todos modos": continuar al solve.

Diseño:
- **NO modal** (sin grab_set): permite editar la GUI mientras esta abierto,
  para que el usuario corrija items uno por uno con la lista visible.
  Se mantiene `transient(parent)` para subordinacion visual.
- Solo se abre con errores criticos. Para warnings se usa banner.
- Tema oscuro coherente con el resto del GUI (ttkbootstrap darkly).
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config.settings import (
    HEALTH_OK_COLOR, HEALTH_WARNING_COLOR, HEALTH_ERROR_COLOR, HEALTH_INFO_COLOR,
    LABEL_BG,
)
from models.model_health import (
    Severity, HealthCode, apply_autofix, validate_project,
)


# Hints educativos por codigo de issue. Estilo conversacional, en linea
# con que EduFEM es una herramienta de aprendizaje.
EDUCATIONAL_HINTS = {
    HealthCode.NO_RESTRAINTS:
        "Sin restricciones, el modelo es libre de moverse en el espacio "
        "(tres modos de cuerpo rigido en 2D: dos traslaciones y una "
        "rotacion rigida del cuerpo en el plano XY). Aunque los elementos "
        "plane stress/strain solo tienen 2 DOF por nodo (u, v) y no un DOF "
        "rotacional explicito, el conjunto puede girar como solido rigido: "
        "esa rotacion se manifiesta como desplazamientos u, v que producen "
        "deformacion nula. Eso hace que la matriz K reducida sea singular: "
        "el sistema K_red u = F no tiene solucion unica.",
    HealthCode.INSUFFICIENT_RESTRAINTS:
        "En 2D necesitas suprimir 3 grados de libertad para eliminar los "
        "modos de cuerpo rigido: 2 traslaciones (en X y en Y) + 1 rotacion "
        "rigida en el plano. Aunque los nodos plane stress/strain no tienen "
        "DOF rotacional, el cuerpo completo puede girar y eso debe "
        "bloquearse. Tipicamente: un nodo empotrado (Δx=Δy=0) y otro con "
        "Δy=0 a cierta distancia, o equivalente.",
    HealthCode.BC_ORPHAN_NODE:
        "Un nodo con restriccion pero sin elemento que lo conecte "
        "introduce una fila/columna en K que solo tiene la entrada "
        "diagonal (no hay rigidez relativa a otros nodos). Al imponer "
        "la BC se elimina ese DOF, y el resto del sistema queda mal "
        "condicionado o singular segun el caso.",
    HealthCode.ELEM_NODE_MISSING:
        "El ensamblaje de K iterara sobre los node_ids del elemento "
        "para mapear DOFs locales a globales. Si un node_id no existe, "
        "el modelo es inconsistente y el solver no podra construir K.",
    HealthCode.ELEM_MATERIAL_MISSING:
        "La matriz constitutiva D depende de E y nu (y t para 3D), "
        "que se leen del material asignado. Sin material valido no se "
        "puede formar la rigidez del elemento.",
    HealthCode.SURFACE_NODE_MISSING:
        "La integracion de la carga superficial necesita las "
        "coordenadas de los extremos de la arista (y del nodo medio "
        "en Q9). Si un extremo no existe, no se puede calcular la "
        "longitud ni la direccion normal.",
    HealthCode.DEGENERATE_ELEMENT:
        "Un cuadrilatero con vertices repetidos colapsa geometricamente "
        "(area cero o negativa). El Jacobiano se anula y la inversa "
        "no esta definida -> la matriz B no se puede formar.",
    HealthCode.NEGATIVE_JACOBIAN:
        "La convencion de toda la libreria es CCW (counter-clockwise). "
        "Si tus 4 vertices estan en orden CW, el Jacobiano sale negativo "
        "en todos los puntos de Gauss y la integracion da signos "
        "incorrectos. Solucion: invertir el orden (N1↔N3 o N2↔N4).",
    HealthCode.LOAD_ORPHAN_NODE:
        "Las cargas nodales se mapean al vector global F via los DOFs "
        "del nodo. Si el nodo no esta en ningun elemento, sus DOFs no "
        "se ensamblan a K y la fuerza queda \"colgando\" (no afecta el "
        "resultado).",
    HealthCode.UNUSED_MATERIAL:
        "Los materiales sin uso ocupan memoria y aparecen en la "
        "libreria pero no contribuyen al modelo. Conviene eliminarlos "
        "para mantener la lista corta y evitar errores al elegir "
        "(\"asigne X y Z al elemento Y, pero ninguno de ellos se "
        "esta usando realmente\").",
    HealthCode.ZERO_NODAL_LOAD:
        "Una carga con Fx=Fy=0 no aporta nada a F. Probablemente la "
        "creaste para tomar una nota o te olvidaste de poner valores. "
        "Eliminala o asigna magnitudes reales.",
    HealthCode.ZERO_SURFACE_LOAD:
        "Igual que las cargas nodales con magnitud cero: no contribuyen. "
        "Limpiar la tabla evita confusion al revisar el modelo despues.",
    HealthCode.NO_ELEMENTS:
        "Sin elementos no hay matriz de rigidez K que ensamblar -- el "
        "modelo no representa un solido continuo. Crea al menos un "
        "elemento conectando 4 nodos (Q4) o 9 (Q9) para poder analizar.",
}


# Iconos por codigo (mejora la lectura visual)
CODE_ICONS = {
    HealthCode.NO_RESTRAINTS:           "🔓",
    HealthCode.INSUFFICIENT_RESTRAINTS: "🔓",
    HealthCode.BC_ORPHAN_NODE:          "🔗",
    HealthCode.ELEM_NODE_MISSING:       "❌",
    HealthCode.ELEM_MATERIAL_MISSING:   "🧱",
    HealthCode.SURFACE_NODE_MISSING:    "❌",
    HealthCode.DEGENERATE_ELEMENT:      "📐",
    HealthCode.NEGATIVE_JACOBIAN:       "🔄",
    HealthCode.LOAD_ORPHAN_NODE:        "🔗",
    HealthCode.UNUSED_MATERIAL:         "🧱",
    HealthCode.ZERO_NODAL_LOAD:         "0️⃣",
    HealthCode.ZERO_SURFACE_LOAD:       "0️⃣",
    HealthCode.NO_ELEMENTS:             "📭",
    HealthCode.SUMMARY:                 "📊",
}


class HealthReportDialog:
    """Modal que presenta el HealthReport y permite aplicar auto-fixes
    o navegar a los items con problemas.

    Despues de cerrar, el caller puede consultar:
        dialog.result  → "continue" | "cancel" | None
        dialog.fixes_applied  → cantidad de auto-fixes aplicados
    """

    def __init__(self, parent, report, project, main_window=None,
                 *, allow_continue=True):
        self.parent = parent
        self.report = report
        self.project = project
        self.main_window = main_window
        self.allow_continue = allow_continue

        self.result = None
        self.fixes_applied = 0

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("⚕  Salud del modelo")
        self.dialog.geometry("780x620")
        self.dialog.transient(parent)
        # NO modal: el usuario debe poder editar la GUI principal mientras
        # el dialogo esta abierto, para corregir issues uno por uno con la
        # lista visible. Se cierra con Volver / Resolver / X (WM_DELETE).
        self.dialog.minsize(600, 480)
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._build()
        self._center()

    def show(self):
        """Bloquea hasta que el usuario decide. Retorna self.result."""
        self.dialog.wait_window()
        return self.result

    # ─── UI ──────────────────────────────────────────────────────────

    def _build(self):
        self._outer = ttk.Frame(self.dialog, padding=16)
        self._outer.pack(fill=BOTH, expand=YES)

        # Header con resumen y conteos
        self._build_header(self._outer)

        # Lista scrollable de issues agrupados
        self._build_issue_list(self._outer)

        # Footer con botones
        self._build_footer(self._outer)

    def _build_header(self, parent):
        header = ttk.Frame(parent)
        header.pack(fill=X, pady=(0, 12))
        self._header_frame = header

        # Icono + titulo segun severidad maxima
        if self.report.has_errors():
            icon = "✗"
            color = HEALTH_ERROR_COLOR
            title = "Errores criticos detectados"
            subtitle = ("El modelo no se puede resolver con seguridad hasta "
                        "que se corrijan los errores listados abajo.")
        elif self.report.has_warnings():
            icon = "⚠"
            color = HEALTH_WARNING_COLOR
            title = "Advertencias en el modelo"
            subtitle = ("El modelo se puede resolver, pero conviene revisar "
                        "los puntos siguientes para evitar resultados "
                        "inesperados.")
        else:
            icon = "✓"
            color = HEALTH_OK_COLOR
            title = "Modelo sano"
            subtitle = ("Todos los chequeos pasaron. El modelo esta listo "
                        "para resolverse.")

        title_row = ttk.Frame(header)
        title_row.pack(fill=X)
        tk.Label(
            title_row, text=icon, fg=color, bg=self.dialog.cget("bg"),
            font=("Segoe UI", 22, "bold"),
        ).pack(side=LEFT, padx=(0, 12))
        tk.Label(
            title_row, text=title, fg="#e8e8ea", bg=self.dialog.cget("bg"),
            font=("Segoe UI", 14, "bold"),
        ).pack(side=LEFT, anchor=W)

        ttk.Label(
            header, text=subtitle, foreground="#a0a0a8",
            font=("Segoe UI", 9), wraplength=720, justify=LEFT,
        ).pack(anchor=W, pady=(6, 0))

        # Conteos
        counts = self.report.counts_by_severity()
        chips_row = ttk.Frame(header)
        chips_row.pack(fill=X, pady=(8, 0))
        if counts["error"]:
            self._chip(chips_row, f"{counts['error']} error(es)",
                       HEALTH_ERROR_COLOR)
        if counts["warning"]:
            self._chip(chips_row, f"{counts['warning']} warning(s)",
                       HEALTH_WARNING_COLOR)
        if self.report.info:
            for issue in self.report.info:
                summary_text = issue.message
                if summary_text:
                    self._chip(chips_row, summary_text, HEALTH_INFO_COLOR)
                    break

    def _chip(self, parent, text, color):
        """Pequeño chip con borde de color e info adentro."""
        f = tk.Frame(parent, bg=LABEL_BG, highlightthickness=1,
                     highlightbackground=color)
        tk.Label(
            f, text=text, fg=color, bg=LABEL_BG,
            font=("Segoe UI", 8, "bold"), padx=8, pady=2,
        ).pack()
        f.pack(side=LEFT, padx=(0, 6))

    def _build_issue_list(self, parent):
        # Frame contenedor con scrollbar vertical
        container = ttk.Frame(parent)
        container.pack(fill=BOTH, expand=YES)
        self._issue_container = container

        canvas = tk.Canvas(container, bg=self.dialog.cget("bg"),
                           highlightthickness=0)
        sb = ttk.Scrollbar(container, orient=VERTICAL,
                           command=canvas.yview, bootstyle="round")
        self.scroll_frame = ttk.Frame(canvas)
        self.scroll_frame.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor=NW)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        sb.pack(side=RIGHT, fill=Y)
        # Scroll con rueda
        def _on_wheel(e):
            canvas.yview_scroll(-1 * (e.delta // 120), "units")
        canvas.bind_all("<MouseWheel>", _on_wheel)
        self._wheel_canvas = canvas
        # Despegar el binding cuando el dialog se destruya
        self.dialog.bind("<Destroy>",
                         lambda _e: self._unbind_wheel(), add="+")

        # Renderizar issues
        if self.report.errors:
            self._section_label(self.scroll_frame, "Errores criticos",
                                HEALTH_ERROR_COLOR)
            for issue in self.report.errors:
                self._render_issue(self.scroll_frame, issue,
                                   HEALTH_ERROR_COLOR)

        if self.report.warnings:
            self._section_label(self.scroll_frame, "Advertencias",
                                HEALTH_WARNING_COLOR)
            for issue in self.report.warnings:
                self._render_issue(self.scroll_frame, issue,
                                   HEALTH_WARNING_COLOR)

        if not self.report.errors and not self.report.warnings:
            ttk.Label(
                self.scroll_frame,
                text="No se detectaron problemas en el modelo.",
                foreground=HEALTH_OK_COLOR, font=("Segoe UI", 10),
            ).pack(anchor=W, pady=12)

    def _unbind_wheel(self):
        try:
            self._wheel_canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass

    def _section_label(self, parent, text, color):
        ttk.Label(
            parent, text=text, foreground=color,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=W, pady=(12, 6))

    def _render_issue(self, parent, issue, color):
        """Tarjeta visual de un issue: icono, mensaje, botones."""
        card = tk.Frame(parent, bg=LABEL_BG, highlightthickness=1,
                        highlightbackground="#3a3d42")
        card.pack(fill=X, pady=4, padx=2)

        inner = ttk.Frame(card, padding=10)
        inner.pack(fill=BOTH, expand=YES)

        # Top row: icono + mensaje
        top = ttk.Frame(inner)
        top.pack(fill=X)

        icon = CODE_ICONS.get(issue.code, "•")
        tk.Label(
            top, text=icon, fg=color, bg=LABEL_BG,
            font=("Segoe UI", 14),
        ).pack(side=LEFT, padx=(0, 10))

        tk.Label(
            top, text=issue.message, fg="#e8e8ea", bg=LABEL_BG,
            font=("Segoe UI", 9), wraplength=620, justify=LEFT,
        ).pack(side=LEFT, anchor=W, fill=X, expand=YES)

        # Bottom row: botones de accion
        actions = ttk.Frame(inner)
        actions.pack(fill=X, pady=(8, 0))

        if issue.fixable:
            btn = ttk.Button(
                actions, text="🔧  Corregir",
                bootstyle="success-outline",
                command=lambda i=issue, c=card: self._on_fix(i, c),
            )
            btn.pack(side=LEFT, padx=(0, 6))

        if issue.target_kind and issue.target_id is not None:
            ttk.Button(
                actions, text="📍  Ir al item",
                bootstyle="info-outline",
                command=lambda i=issue: self._on_goto(i),
            ).pack(side=LEFT, padx=(0, 6))

        # Hint educativo (collapsible)
        hint = EDUCATIONAL_HINTS.get(issue.code)
        if hint:
            self._build_hint_toggle(inner, hint, color)

    def _build_hint_toggle(self, parent, hint_text, color):
        """Boton collapsible '🎓 Por que es un problema?' que expande el
        hint educativo. Colapsado por defecto -- minimalista."""
        hint_var = tk.BooleanVar(value=False)
        toggle_frame = ttk.Frame(parent)
        toggle_frame.pack(fill=X, pady=(4, 0))

        hint_lbl = tk.Label(
            toggle_frame, text=hint_text, fg="#b0b0b8", bg=LABEL_BG,
            font=("Segoe UI", 8, "italic"), wraplength=620, justify=LEFT,
        )

        def _toggle():
            if hint_var.get():
                hint_var.set(False)
                hint_lbl.pack_forget()
                btn.config(text="🎓  ¿Por que es un problema?")
            else:
                hint_var.set(True)
                hint_lbl.pack(anchor=W, pady=(4, 0), padx=(24, 0))
                btn.config(text="🎓  Ocultar explicacion")

        btn = ttk.Button(
            toggle_frame, text="🎓  ¿Por que es un problema?",
            bootstyle="link", command=_toggle,
        )
        btn.pack(anchor=W)

    def _build_footer(self, parent):
        # El footer se reconstruye en cada re-validacion porque el texto
        # del boton "Resolver" depende de si el reporte tiene errores.
        if hasattr(self, "_footer_frame") and self._footer_frame is not None:
            try:
                self._footer_frame.destroy()
            except tk.TclError:
                pass
        footer = ttk.Frame(parent)
        footer.pack(fill=X, pady=(12, 0))
        self._footer_frame = footer

        ttk.Button(
            footer, text="Volver al Pre-Proceso", bootstyle="secondary",
            command=self._on_cancel, width=22,
        ).pack(side=LEFT)

        # Re-validar: util tras corregir items manualmente desde la GUI
        # (ahora que el dialogo es no-modal).
        ttk.Button(
            footer, text="🔄  Re-validar", bootstyle="info-outline",
            command=self._on_revalidate, width=14,
        ).pack(side=LEFT, padx=(8, 0))

        if self.allow_continue:
            text = ("Resolver de todos modos" if self.report.has_errors()
                    else "Resolver")
            style = ("danger" if self.report.has_errors()
                     else "success")
            ttk.Button(
                footer, text=text, bootstyle=style,
                command=self._on_continue, width=22,
            ).pack(side=RIGHT)

    # ─── Callbacks ───────────────────────────────────────────────────

    def _on_fix(self, issue, card_widget):
        """Aplica el auto-fix y remueve la tarjeta del DOM."""
        ok = apply_autofix(self.project, issue)
        if ok:
            self.fixes_applied += 1
            # Tachar la tarjeta visualmente y deshabilitar sus botones
            for child in card_widget.winfo_children():
                self._disable_widget_recursive(child)
            card_widget.configure(highlightbackground=HEALTH_OK_COLOR)
            # Refrescar las tablas del pre_tab si existe
            if self.main_window is not None:
                try:
                    self.main_window._refresh_all_tabs()
                    self.main_window._update_status_info()
                except Exception:
                    pass

    def _disable_widget_recursive(self, widget):
        try:
            widget.configure(state=DISABLED)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._disable_widget_recursive(child)

    def _on_goto(self, issue):
        """Navega al Pre-Proceso, sub-pestana del item, y selecciona la
        fila. NO cierra el dialogo: el usuario puede corregir el item
        desde la GUI (gracias al modo no-modal) y luego clickear
        Re-validar para refrescar la lista."""
        if self.main_window is None:
            return
        kind = issue.target_kind
        target_id = issue.target_id
        try:
            # Cambiar al Pre-Proceso (tab index 0)
            self.main_window.notebook.select(0)
            pre_tab = self.main_window.pre_tab
            # Mapeo kind -> (frame, tree)
            mapping = {
                "node":       ("nodes_frame", "nodes_tree"),
                "element":    ("elements_frame", "elements_tree"),
                "load":       ("loads_frame", "loads_tree"),
                "bc":         ("constraints_frame", "constraints_tree"),
                "constraint": ("constraints_frame", "constraints_tree"),
                "surface":    ("surface_frame", "surface_tree"),
            }
            if kind not in mapping:
                return
            frame_attr, tree_attr = mapping[kind]
            frame = getattr(pre_tab, frame_attr, None)
            tree = getattr(pre_tab, tree_attr, None)
            if frame is None or tree is None:
                return
            pre_tab.data_notebook.select(frame)
            iid = str(target_id)
            if iid in tree.get_children():
                tree.selection_set(iid)
                tree.focus(iid)
                tree.see(iid)
        except Exception:
            pass
        # Tras navegar, traer el dialogo al frente para que la lista siga
        # visible mientras el usuario corrige el item. Se mueve el dialogo
        # a una esquina para no tapar la celda recien seleccionada.
        try:
            self.dialog.lift()
            self.dialog.update_idletasks()
            # Mover a la esquina superior derecha del parent
            px = self.parent.winfo_x() + self.parent.winfo_width()
            py = self.parent.winfo_y() + 60
            dw = self.dialog.winfo_width()
            self.dialog.geometry(f"+{max(px - dw - 20, 0)}+{py}")
        except Exception:
            pass

    def _on_revalidate(self):
        """Re-corre validate_project sobre el modelo actual y reconstruye
        header, lista de issues y footer. Usado tras correcciones manuales
        en la GUI principal."""
        try:
            self.report = validate_project(self.project)
        except Exception:
            return
        # Destruir header y container de issues
        try:
            self._header_frame.destroy()
        except (tk.TclError, AttributeError):
            pass
        try:
            self._issue_container.destroy()
        except (tk.TclError, AttributeError):
            pass
        # Reconstruir header y lista en el outer (orden importante:
        # header primero, lista despues, footer ya esta abajo y queda
        # debajo automaticamente al pack-forget + repack).
        try:
            self._footer_frame.pack_forget()
        except (tk.TclError, AttributeError):
            pass
        self._build_header(self._outer)
        self._build_issue_list(self._outer)
        self._build_footer(self._outer)
        # Refrescar GUI principal por si los fixes ya aplicados invalidaron
        # algo del cache de la pestaña activa.
        if self.main_window is not None:
            try:
                self.main_window._refresh_all_tabs()
                self.main_window._update_status_info()
            except Exception:
                pass

    def _on_continue(self):
        self.result = "continue"
        self.dialog.destroy()

    def _on_cancel(self):
        """Cierra el dialogo y navega al Pre-Proceso (coherente con el
        nombre del boton)."""
        self.result = "cancel"
        if self.main_window is not None:
            try:
                self.main_window.notebook.select(0)
            except Exception:
                pass
        self.dialog.destroy()

    def _center(self):
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        try:
            x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
            y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
            self.dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        except Exception:
            pass


def show_health_report(parent, report, project, main_window=None,
                       *, allow_continue=True):
    """Helper: abre el dialogo y bloquea hasta que el usuario decida.
    Retorna ('continue' | 'cancel' | None, fixes_applied).
    """
    dlg = HealthReportDialog(parent, report, project, main_window,
                             allow_continue=allow_continue)
    result = dlg.show()
    return result, dlg.fixes_applied
