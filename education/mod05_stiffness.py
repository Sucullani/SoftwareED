"""
Módulo 5 — Matriz de Rigidez Elemental K_e (overlay)

Construye y muestra LA FORMA ANALÍTICA de la rigidez elemental:

        k_e = ∫∫ Bᵀ D B |det J| t  dξ dη   sobre   [-1, 1]²

El alumno selecciona una entrada (i, j) y ve el integrando simbólico
K_(i,j)(ξ, η) renderizado. La expresión crece a varias páginas incluso
para Q4 con elementos rectos, y excede el parser de mathtext en Q9
(donde B es 3×18). **El mensaje pedagógico es justamente ese**: la
integral no se puede resolver analíticamente.

Narrativa par M5 → M5b:
    M5 (este):  "esta es la rigidez analítica. Mirá el integrando. NO
                 se puede integrar en cerrado."
    M5b:        "por eso integramos numéricamente, evaluando en puntos
                 de Gauss y sumando con pesos."

`SymbolicIntegrandQ4` vive en este archivo (movida de la versión previa
`mod05_gauss.py`). Importada por `file_io.memoria_calculo` para el PDF
de memoria — **no mover sin actualizar también ese import**.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk
import sympy as sp

from education.overlay_module import CanvasOverlayModule
from education.components import LatexExpressionImage

from config.settings import (
    ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN,
    EDU_FIG_BG, EDU_AXES_BG, EDU_LABEL_BG, EDU_FG, EDU_FG_MUTED,
)


# ────────────── CAPA SIMBÓLICA ──────────────


class SymbolicIntegrandQ4:
    """Construcción simbólica de [B^T D B |det J| t] para Q4."""

    def __init__(self, E=225000.0, nu=0.2, t=0.8, coords=None):
        self.E = E
        self.nu = nu
        self.t = t
        self.coords = coords if coords is not None else [
            [0, 0], [5, 0], [7, 4], [2, 3]
        ]
        self.xi, self.eta = sp.symbols(r"\xi \eta", real=True)

    def _shape_functions(self):
        xi, eta = self.xi, self.eta
        return [
            sp.Rational(1, 4) * (1 - xi) * (1 - eta),
            sp.Rational(1, 4) * (1 + xi) * (1 - eta),
            sp.Rational(1, 4) * (1 + xi) * (1 + eta),
            sp.Rational(1, 4) * (1 - xi) * (1 + eta),
        ]

    def _jacobian(self, dN_dxi, dN_deta):
        c = self.coords
        dx_dxi  = sum(dN_dxi[i]  * c[i][0] for i in range(4))
        dy_dxi  = sum(dN_dxi[i]  * c[i][1] for i in range(4))
        dx_deta = sum(dN_deta[i] * c[i][0] for i in range(4))
        dy_deta = sum(dN_deta[i] * c[i][1] for i in range(4))
        return sp.Matrix([[dx_dxi, dy_dxi], [dx_deta, dy_deta]])

    def _b(self, dN_dxi, dN_deta, J):
        detJ = J.det()
        i11 =  J[1, 1] / detJ
        i12 = -J[0, 1] / detJ
        i21 = -J[1, 0] / detJ
        i22 =  J[0, 0] / detJ
        B_parts = []
        for i in range(4):
            dNx = i11 * dN_dxi[i] + i12 * dN_deta[i]
            dNy = i21 * dN_dxi[i] + i22 * dN_deta[i]
            B_parts.append(sp.Matrix([[dNx, 0], [0, dNy], [dNy, dNx]]))
        return sp.Matrix.hstack(*B_parts), detJ

    def _d(self, analysis):
        E = sp.Rational(self.E).limit_denominator(1_000_000)
        nu = sp.Rational(self.nu).limit_denominator(1000)
        if analysis == ANALYSIS_PLANE_STRESS:
            f = E / (1 - nu ** 2)
            return f * sp.Matrix([
                [1,  nu, 0],
                [nu, 1,  0],
                [0,  0,  (1 - nu) / 2],
            ])
        f = E / ((1 + nu) * (1 - 2 * nu))
        return f * sp.Matrix([
            [1 - nu, nu,    0],
            [nu,     1 - nu, 0],
            [0,      0,      (1 - 2 * nu) / 2],
        ])

    def integrand_entry(self, i, j, analysis):
        Ns = self._shape_functions()
        dN_dxi  = [sp.diff(N, self.xi)  for N in Ns]
        dN_deta = [sp.diff(N, self.eta) for N in Ns]
        J = self._jacobian(dN_dxi, dN_deta)
        B, detJ = self._b(dN_dxi, dN_deta, J)
        D = self._d(analysis)
        K = (B.T * D * B) * sp.Abs(detJ) * sp.Rational(self.t).limit_denominator(1000)
        return sp.simplify(K[i, j])


# ────────────── MÓDULO M5 OVERLAY ──────────────


class StiffnessElementModule(CanvasOverlayModule):
    """M5 overlay: matriz K_e analítica + integrando "imposible"."""

    TITLE = "⑤  Matriz K_e  (rigidez elemental)"
    PHASE = "proc"
    OVERLAY_INITIAL_POS = (24, 24)
    OVERLAY_WIDTH = 560
    OVERLAY_HEIGHT = None
    REQUIRES_ELEMENT = False

    def build_overlay(self, body):
        # Estado
        self._i = 1
        self._j = 1
        self._last_kij_expr = None
        self._last_kij_key = None

        # Banner: la fórmula central del módulo.
        ttk.Label(
            body,
            text=("k_e = ∫∫  Bᵀ D B  |det J|  t  dξ dη"
                  "     sobre  [-1, 1]²"),
            font=("Consolas", 10, "bold"),
            foreground="#90caf9", justify="center",
        ).pack(fill="x", padx=4, pady=(0, 2))

        # Mensaje pedagógico inmediato.
        ttk.Label(
            body,
            text=("Imposible de resolver analíticamente — el integrando "
                  "crece a varias páginas incluso para Q4."),
            font=("Segoe UI", 9, "italic"),
            foreground="#ef5350", wraplength=540, justify="left",
        ).pack(fill="x", padx=4, pady=(0, 2))

        # Métrica de complejidad en vivo — el alumno ve la afirmación
        # "imposible" cuantificada: # de términos del polinomio en (ξ,η)
        # tras expansión, # de chars del LaTeX, y una equivalencia visual
        # ("~ N páginas"). Cambia con (i, j) y con la geometría del
        # elemento. Anti-rule del "banner sin evidencia".
        #
        # El label es CLICKEABLE — abre un Toplevel scrollable con la
        # expresión REAL sin truncar. Convierte la afirmación textual
        # ("crece a varias páginas") en una experiencia: el alumno
        # scrollea por el integrando entero y ve con sus propios ojos
        # que sí, son páginas. No queda como dato — queda como vivencia.
        self._lbl_complexity = ttk.Label(
            body, text="", font=("Consolas", 9, "bold"),
            foreground="#ffd54f", wraplength=540, justify="left",
            cursor="hand2",
        )
        self._lbl_complexity.pack(fill="x", padx=4, pady=(0, 4))
        self._lbl_complexity.bind(
            "<Button-1>", lambda _e: self._open_full_integrand_window()
        )
        # Handle del Toplevel expandido (singleton — segundo click trae
        # al frente en vez de abrir un duplicado).
        self._full_window: Optional[tk.Toplevel] = None

        # Chips: selector de entrada K_(i,j) a inspeccionar
        chips = ttk.Frame(body)
        chips.pack(fill="x", pady=(0, 4))
        ttk.Label(chips, text="Entrada K_(i,j):",
                   font=("Segoe UI", 9), foreground=EDU_FG_MUTED,
                   ).pack(side="left", padx=(0, 4))
        n_dofs_init = 2 * (self.element.num_nodes if self.element else 4)
        self._var_i = tk.StringVar(value=str(self._i))
        ttk.Spinbox(chips, from_=1, to=n_dofs_init, width=4,
                     textvariable=self._var_i,
                     command=self._on_ij_change,
                     ).pack(side="left", padx=1)
        self._var_j = tk.StringVar(value=str(self._j))
        ttk.Spinbox(chips, from_=1, to=n_dofs_init, width=4,
                     textvariable=self._var_j,
                     command=self._on_ij_change,
                     ).pack(side="left", padx=1)

        ttk.Separator(chips, orient="vertical").pack(side="left",
                                                       fill="y", padx=8)
        self._lbl_dim = ttk.Label(chips, text="",
                                    font=("Segoe UI", 9),
                                    foreground=EDU_FG_MUTED)
        self._lbl_dim.pack(side="left")

        # Panel del integrando simbólico — renderizado como imagen LaTeX
        # independiente (Tk Label con PhotoImage), no como ax matplotlib.
        # Ventaja: la expresión completa cabe a fontsize legible, sin
        # truncamientos artificiales por overflow del axes.
        self._integrand_container = tk.Frame(body, bg=EDU_LABEL_BG,
                                              relief="solid", borderwidth=1)
        self._integrand_container.pack(fill="both", expand=True, pady=(2, 2))
        self._integrand_widget: Optional[LatexExpressionImage] = None
        # Placeholder mientras no hay elemento seleccionado.
        self._integrand_placeholder = tk.Label(
            self._integrand_container,
            text="◎  Clickeá un elemento\nen el canvas",
            bg=EDU_LABEL_BG, fg=EDU_FG_MUTED,
            font=("Segoe UI", 11),
        )
        self._integrand_placeholder.pack(expand=True, fill="both", padx=8, pady=8)

        # Cross-reference clickeable a M5b (bridge pedagógico explícito).
        self._pack_crossref(
            body, "mod05b",
            "👉 Como no se puede integrar analíticamente, en "
            "⑤′ Cuadratura de Gauss aproximamos numéricamente.",
            wraplength=540,
        )

        self._refresh_all()

    def on_element_selected(self, elem_id):
        if elem_id == self.element_id:
            return
        self.element_id = elem_id
        self.element = self.project.elements.get(elem_id) if self.project else None
        # Invalida cache simbólico — coords cambiaron.
        self._last_kij_expr = None
        self._last_kij_key = None
        self._refresh_all()

    # ── Callbacks ──────────────────────────────────────────────────
    def _on_ij_change(self):
        if self.element is None:
            return
        try:
            n_dofs = 2 * self.element.num_nodes
            i = max(1, min(n_dofs, int(self._var_i.get())))
            j = max(1, min(n_dofs, int(self._var_j.get())))
        except (tk.TclError, ValueError):
            return
        self._i, self._j = i, j
        self._var_i.set(str(i))
        self._var_j.set(str(j))
        self._refresh_integrand()

    # ── Render ─────────────────────────────────────────────────────
    def _refresh_all(self):
        # Update label dim (depende del element_type)
        n_nodes = self.element.num_nodes if self.element else 4
        n_dof = 2 * n_nodes
        try:
            self._lbl_dim.configure(
                text=f"k_e es {n_dof}×{n_dof}  ·  {'Q9' if n_nodes==9 else 'Q4'}"
            )
        except tk.TclError:
            pass
        self._refresh_integrand()

    def _is_q9(self) -> bool:
        return (self.element is not None
                 and getattr(self.element, "num_nodes", 0) == 9)

    def _refresh_integrand(self):
        """Refresca el integrando simbólico.

        Migrado a `LatexExpressionImage`: cada render produce su propio
        PNG en una figura matplotlib aislada con `bbox_inches="tight"`,
        embebido como `tk.Label` PhotoImage. Sin competencia por el espacio
        de un ax compartido — la fórmula crece a su tamaño natural.
        """
        # Caso vacío: mostrar placeholder, ocultar el widget LaTeX.
        if self.element is None or self.project is None:
            self._show_placeholder("◎  Clickeá un elemento\nen el canvas")
            self._set_complexity("")
            return

        if self._is_q9():
            self._show_q9_notice()
            # Estimación conservadora para Q9: B es 3×18, BᵀDB tiene 18×18
            # = 324 entradas, cada una con cientos de monomios. Damos un
            # rango grueso en vez del número exacto (el sympy expand
            # podría tomar segundos).
            self._set_complexity(
                "Q9: B es 3×18 ⇒ cada K_(i,j) expande a 10³–10⁴ términos."
            )
            return

        coords = self._node_coords()
        if coords is None:
            self._show_placeholder("(sin coords)")
            self._set_complexity("")
            return

        E, nu, t = self._resolve_params()
        analysis = self._analysis_type()
        coords_list = coords[:4].tolist()
        cache_key = (self._i, self._j, analysis, tuple(map(tuple, coords_list)))
        if cache_key == self._last_kij_key and self._last_kij_expr is not None:
            expr = self._last_kij_expr
        else:
            try:
                sym = SymbolicIntegrandQ4(E, nu, t, coords_list)
                expr = sym.integrand_entry(self._i - 1, self._j - 1, analysis)
                self._last_kij_expr = expr
                self._last_kij_key = cache_key
            except Exception as exc:
                self._show_placeholder(f"Error K_(i={self._i},j={self._j}):\n{exc}",
                                        fg="#ef5350")
                self._set_complexity("")
                return

        try:
            latex_body = sp.latex(expr)
        except Exception:
            latex_body = str(expr)
        # Métricas SOBRE EL LATEX COMPLETO (antes de truncar) — el
        # contador refleja la expresión real, no la versión recortada
        # para mostrar. Estimación de páginas: ~1500 chars LaTeX / página
        # A4 fontsize 11 con tight layout.
        n_terms = self._count_terms(expr)
        n_chars = len(latex_body)
        pages = max(1, round(n_chars / 1500))
        cmp_txt = (f"📏 K_({self._i},{self._j}): {n_terms} términos · "
                   f"{n_chars:,} chars LaTeX · ≈{pages} pág impresas")
        self._set_complexity(cmp_txt.replace(",", "."))

        latex_body = self._truncate_latex(latex_body, max_chars=320)
        full = (f"K_{{{self._i},{self._j}}}(\\xi,\\eta) \\;=\\; "
                + latex_body)
        self._show_latex(full)

    def _set_complexity(self, text: str) -> None:
        """Escribe el label de complejidad (silenciosamente robusto)."""
        try:
            self._lbl_complexity.configure(text=text)
        except (tk.TclError, AttributeError):
            pass

    @staticmethod
    def _count_terms(expr) -> int:
        """N° de monomios tras `expand`. Acota a 0 si sympy falla."""
        try:
            expanded = sp.expand(expr)
        except Exception:
            return 0
        # sympy.Add.make_args devuelve la tupla de sumandos top-level;
        # para una expresión monomial devuelve (expr,) — len = 1, correcto.
        try:
            return len(sp.Add.make_args(expanded))
        except Exception:
            return 0

    # ── Toplevel expandido: la expresión REAL, sin truncar ──────────
    def _open_full_integrand_window(self) -> None:
        """Abre un Toplevel scrollable con `sp.pretty(sp.expand(expr))` —
        la expresión completa, sin truncar, tabulada por sympy.

        Pedagogía: el banner "imposible" + el contador "N términos" son
        afirmaciones. Esto las convierte en EXPERIENCIA — el alumno
        scrollea, ve la expresión real y siente el crecimiento polinomial
        en su propio dedo. Después de scrollear 3-4 segundos por una
        sola entrada K_(i,j) entiende emocionalmente por qué Gauss
        existe, no solo intelectualmente.

        Singleton suave: segundo click trae al frente en vez de duplicar."""
        if self._last_kij_expr is None:
            return
        # Singleton: traer al frente si ya está abierto
        if (self._full_window is not None
                and self._full_window.winfo_exists()):
            try:
                self._full_window.lift()
                self._full_window.focus_set()
                return
            except tk.TclError:
                self._full_window = None

        top = tk.Toplevel(self._mesh.canvas)
        top.title(f"Integrando K_({self._i},{self._j}) — expresión completa")
        top.geometry("900x700")
        top.configure(bg=EDU_AXES_BG)
        # Posicionar relativo al canvas (un poco hacia adentro para que
        # no caiga sobre el overlay flotante de M5).
        try:
            top.geometry(f"+{self._mesh.canvas.winfo_rootx() + 80}"
                         f"+{self._mesh.canvas.winfo_rooty() + 60}")
        except tk.TclError:
            pass

        # Header con metadata pedagógica
        try:
            latex_full = sp.latex(self._last_kij_expr)
        except Exception:
            latex_full = ""
        n_terms = self._count_terms(self._last_kij_expr)
        n_chars = len(latex_full)
        n_dofs = 2 * (self.element.num_nodes if self.element else 4)

        header = tk.Frame(top, bg=EDU_AXES_BG)
        header.pack(fill="x", padx=10, pady=(10, 4))
        tk.Label(
            header,
            text=(f"K_({self._i},{self._j})(ξ, η)  ·  {n_terms} términos  ·  "
                  f"{n_chars:,} chars LaTeX").replace(",", "."),
            bg=EDU_AXES_BG, fg="#ffd54f",
            font=("Consolas", 12, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            header,
            text=(f"Esta es UNA entrada de la matriz k_e ({n_dofs}×{n_dofs}). "
                  f"Hay {n_dofs * n_dofs} expresiones como esta — y todavía "
                  "falta integrarlas. Por eso Gauss."),
            bg=EDU_AXES_BG, fg=EDU_FG_MUTED,
            font=("Segoe UI", 9, "italic"),
            anchor="w", justify="left", wraplength=860,
        ).pack(fill="x", pady=(2, 2))

        # Body: tk.Text con scrollbar V+H. sp.pretty produce ASCII art
        # multi-línea, así que necesitamos scroll en ambos ejes.
        body_frame = tk.Frame(top, bg=EDU_AXES_BG)
        body_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        text = tk.Text(
            body_frame, wrap="none", bg=EDU_LABEL_BG, fg="#dcdcdc",
            font=("Consolas", 9), insertbackground="#dcdcdc",
            relief="flat", borderwidth=0,
        )
        vscroll = ttk.Scrollbar(body_frame, orient="vertical",
                                command=text.yview)
        hscroll = ttk.Scrollbar(body_frame, orient="horizontal",
                                command=text.xview)
        text.configure(yscrollcommand=vscroll.set,
                       xscrollcommand=hscroll.set)
        text.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")
        body_frame.rowconfigure(0, weight=1)
        body_frame.columnconfigure(0, weight=1)

        # Volcar la expresión expandida con sp.pretty. num_columns alto
        # para minimizar wrap automático (que rompería términos).
        try:
            pretty = sp.pretty(sp.expand(self._last_kij_expr),
                                num_columns=240, use_unicode=True)
        except Exception:
            pretty = str(self._last_kij_expr)
        text.insert("1.0", pretty)
        text.configure(state="disabled")  # read-only

        # Footer con stats de "qué tan grande es"
        footer = tk.Frame(top, bg=EDU_AXES_BG)
        footer.pack(fill="x", padx=10, pady=(0, 10))
        n_lines = pretty.count("\n") + 1
        tk.Label(
            footer,
            text=(f"📏 {n_lines:,} líneas tabuladas  ·  "
                  f"≈ {max(1, n_lines // 60)} páginas impresas "
                  "(Esc cierra)").replace(",", "."),
            bg=EDU_AXES_BG, fg=EDU_FG_MUTED,
            font=("Consolas", 9), anchor="w",
        ).pack(fill="x")

        # Cleanup del singleton al cerrar
        def _close(_e=None):
            try:
                top.destroy()
            except tk.TclError:
                pass
            self._full_window = None
        top.protocol("WM_DELETE_WINDOW", _close)
        top.bind("<Escape>", _close)

        self._full_window = top

    def _show_placeholder(self, text: str, *, fg: str = EDU_FG_MUTED) -> None:
        """Reemplaza el widget LaTeX por un label de texto plano."""
        if self._integrand_widget is not None:
            self._integrand_widget.destroy()
            self._integrand_widget = None
        try:
            self._integrand_placeholder.configure(text=text, fg=fg)
            if not self._integrand_placeholder.winfo_ismapped():
                self._integrand_placeholder.pack(expand=True, fill="both",
                                                   padx=8, pady=8)
        except tk.TclError:
            pass

    def _show_q9_notice(self) -> None:
        """Q9: muestra fórmula simbólica + texto explicativo (no calcula
        la expansión, que excede mathtext)."""
        if self._integrand_widget is not None:
            self._integrand_widget.destroy()
            self._integrand_widget = None
        try:
            self._integrand_placeholder.configure(
                text=("K_(i,j)(ξ, η) = [Bᵀ D B]_(i,j) · |det J| · t\n\n"
                      "Q9: B es 3×18 → la expansión simbólica de K_(i,j)\n"
                      "excede el parser de mathtext.\n"
                      "La conclusión es la misma: imposible analíticamente."),
                fg="#dcdcdc",
            )
            if not self._integrand_placeholder.winfo_ismapped():
                self._integrand_placeholder.pack(expand=True, fill="both",
                                                   padx=8, pady=8)
        except tk.TclError:
            pass

    def _show_latex(self, expr: str) -> None:
        """Reemplaza placeholder por widget LaTeX renderizado a imagen."""
        try:
            if self._integrand_placeholder.winfo_ismapped():
                self._integrand_placeholder.pack_forget()
        except tk.TclError:
            pass
        # Re-build del widget en cada cambio (cada (i,j) es una imagen
        # distinta; reusar la instancia para set_expression aprovecha la
        # cache interna del renderer).
        if self._integrand_widget is None:
            self._integrand_widget = LatexExpressionImage(
                self._integrand_container, expr=expr,
                fontsize=13, color="#dcdcdc", bg=EDU_LABEL_BG,
                cache=True,
            )
            self._integrand_widget.pack(expand=True, padx=8, pady=8)
        else:
            try:
                self._integrand_widget.set_expression(expr)
            except tk.TclError:
                pass

    # ── Helpers ─────────────────────────────────────────────────────
    def _node_coords(self) -> Optional[np.ndarray]:
        if self.project and self.element:
            try:
                return np.array([
                    [self.project.nodes[nid].x, self.project.nodes[nid].y]
                    for nid in self.element.node_ids
                ], dtype=float)
            except KeyError:
                return None
        return None

    def _resolve_params(self):
        E_def, nu_def, t_def = 225_000.0, 0.2, 0.8
        if self.project is None or self.element is None:
            return E_def, nu_def, t_def
        mat = self.project.materials.get(
            getattr(self.element, "material_name", None)
        )
        if mat is not None:
            return float(mat.E), float(mat.nu), float(self.element.thickness)
        return E_def, nu_def, t_def

    def _analysis_type(self) -> str:
        if self.project is not None:
            at = getattr(self.project, "analysis_type", None)
            if at in (ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN):
                return at
        return ANALYSIS_PLANE_STRESS

    @staticmethod
    def _truncate_latex(s: str, max_chars: int = 320) -> str:
        if len(s) <= max_chars:
            return s
        cut = max_chars - 12
        depth = 0
        last_safe = 0
        for i, ch in enumerate(s[:cut]):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth = max(0, depth - 1)
            elif depth == 0 and ch in "+-" and i > 0:
                last_safe = i
        if last_safe == 0:
            stub = s[:cut]
            opens = stub.count("{") - stub.count("}")
            return stub + "}" * max(0, opens) + r"\,\cdots"
        return s[:last_safe] + r"\,\cdots"
