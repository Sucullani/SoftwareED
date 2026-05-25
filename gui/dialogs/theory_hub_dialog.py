"""
Theory Hub — documento unificado de teoría FEM accesible desde Ayuda.

Diseño:
    El botón "?" / "Teoría" fue removido del header de cada módulo
    educativo (propuesta UX 2026 minimalista). Toda la teoría se centraliza
    aquí, en un solo documento navegable, accesible desde el menú principal
    Ayuda ▸ Teoría FEM en cualquier momento del flujo — no solo cuando un
    módulo está abierto.

    Cada sección corresponde a un módulo (M0..M9) y resume el concepto
    fundamental + las ecuaciones clave. Sin redundancias con el modelo:
    NO incluimos los valores específicos del usuario (E, ν, ρ, etc.),
    solo la teoría general.

API:
    open_theory_hub(parent) — abre un TheoryViewer flotante con el doc
    agregado. No es modal, el usuario puede consultarlo mientras opera
    el resto del software.
"""

from __future__ import annotations

from education.components import TheoryViewer, TheoryDoc


def open_theory_hub(parent) -> TheoryViewer:
    """Abre el hub de teoría MEF. Llamado desde el menú Ayuda."""
    return TheoryViewer.open(
        parent,
        title="Teoría MEF — EduFEM",
        doc_builder=_build_full_theory_document,
        subtitle="Módulos M0..M9 — fundamentos para análisis Q4/Q9 plano",
    )


# ────────────────────────────────────────────────────────────────────
# Constructor del documento agregado
# ────────────────────────────────────────────────────────────────────


def _build_full_theory_document(doc: TheoryDoc) -> None:
    # TOC clickeable al inicio (hyperref ya esta cargado por TheoryDoc).
    doc.toc()
    _intro(doc)
    _m0_mesh_quality(doc)
    _m1_iso_mapping(doc)
    _m2_jacobian(doc)
    _m3_constitutive(doc)
    _m4_b_matrix(doc)
    _m5_stiffness_gauss(doc)
    _m6_equivalent_forces(doc)
    _m7_assembly(doc)
    _m8_post_processing(doc)
    _m9_convergence(doc)


def _intro(doc: TheoryDoc) -> None:
    doc.section_numbered("Introducción")
    doc.para(
        r"El Método de los Elementos Finitos (MEF) busca el campo de "
        r"desplazamientos $\mathbf{u}(x,y)$ que satisface el equilibrio "
        r"elástico $\nabla\cdot\boldsymbol\sigma(\mathbf{u})+\mathbf{b}="
        r"\mathbf{0}$ en $\Omega$, sujeto a desplazamientos prescritos en "
        r"parte del contorno y tracciones aplicadas en el resto."
    )
    doc.para(
        r"Para geometrías generales esta EDP no tiene solución analítica, "
        r"así que se la reemplaza por su \emph{forma débil}: encontrar "
        r"$\mathbf{u}$ que minimice la energía potencial del sistema en "
        r"un espacio de funciones admisibles. El MEF restringe ese "
        r"espacio a funciones lineales o cuadráticas a trozos definidas "
        r"sobre una malla finita — de ahí su nombre."
    )
    doc.para(
        r"En lugar de resolver la EDP en infinitos puntos, dividimos el "
        r"dominio en $N$ \textbf{elementos} unidos por \textbf{nodos}. El "
        r"campo $\mathbf{u}$ pasa de ser una función continua a un vector "
        r"de $2\cdot N_{nodos}$ incógnitas. Cada elemento aporta una "
        r"matriz de rigidez $k_e$ y un vector de fuerzas $f_e$ que, "
        r"ensamblados, conforman el sistema algebraico global "
        r"$\mathbf{K}\,\mathbf{u}=\mathbf{F}$."
    )
    # Embeber pipeline figure reusando file_io.figure_export.render_fem_pipeline
    _embed_fem_pipeline(doc)
    doc.para(
        r"Este documento sigue el orden canónico del cálculo en EduFEM y "
        r"alinea cada módulo con el código que lo implementa. Cada módulo "
        r"siguiente desarrolla un eslabón del pipeline."
    )


def _embed_fem_pipeline(doc: TheoryDoc) -> None:
    """Renderiza render_fem_pipeline() a un PNG temporal y lo embebe.

    El PNG queda en un directorio temporal que se preserva hasta que se
    compile el PDF; cleanup posterior queda a cargo del OS (los archivos
    en %TEMP%/edufem_hub_* se borran al cerrar la sesion).
    """
    try:
        import os
        import tempfile
        from file_io.figure_export import render_fem_pipeline
        fig = render_fem_pipeline()
        tmpdir = tempfile.mkdtemp(prefix="edufem_hub_")
        path = os.path.join(tmpdir, "fem_pipeline.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        doc.figure(
            path,
            caption=("Hoja de ruta del MEF: cada nodo del pipeline está "
                     "coloreado por la fase del proyecto donde se ejecuta."),
            label="fig:hub_fem_pipeline",
            width=r"0.95\textwidth",
        )
    except Exception:
        # Degradacion silenciosa: si matplotlib falla, el hub sigue
        # compilando sin la figura.
        pass


def _m0_mesh_quality(doc: TheoryDoc) -> None:
    doc.section_numbered("M0 · Calidad geométrica de la malla")
    doc.para(
        r"Antes de calcular cualquier rigidez, la malla debe ser válida: "
        r"sin elementos invertidos, sin distorsión excesiva, sin pliegues. "
        r"EduFEM evalúa tres métricas geométricas combinadas. Cuando un "
        r"análisis concreto reporta elementos en estado \emph{Pobre} o "
        r"\emph{Inválido}, este módulo aporta los criterios para "
        r"interpretar la advertencia (la Memoria de Cálculo generada por "
        r"el software muestra esos estados en su Cap.\ 3 \emph{Calidad de "
        r"la malla})."
    )
    doc.subsection("Razón de Jacobianos (JR)")
    doc.equation(r"\mathrm{JR}=\min_p \det \mathbf{J}(\xi_p,\eta_p)\,/\,\max_p \det \mathbf{J}(\xi_p,\eta_p)")
    doc.para(
        r"Mide la uniformidad de la distorsión local. $\mathrm{JR}=1$ "
        r"para un rectángulo perfecto; $\mathrm{JR}<0$ indica pliegue."
    )
    doc.subsection("Aspect ratio (Robinson)")
    doc.para(
        r"Razón entre las longitudes de los lados opuestos. Idealmente "
        r"cercana a 1. Valores muy altos producen elementos alargados "
        r"que rinden mal en cortante."
    )
    doc.subsection("Admisibilidad de nodos medios (Q9)")
    doc.para(
        r"En elementos Q9, los nodos de arista deben estar cercanos al "
        r"punto medio físico de la arista para no inducir errores en la "
        r"interpolación cuadrática."
    )


def _m1_iso_mapping(doc: TheoryDoc) -> None:
    doc.section_numbered("M1 · Mapeo isoparamétrico y funciones de forma N")
    doc.para(
        r"Todo elemento físico distorsionado se describe como mapeo desde "
        r"un cuadrado de referencia $\hat\Omega=[-1,1]^2$:"
    )
    doc.equation(
        r"x(\xi,\eta)=\sum_{i=1}^{n} N_i(\xi,\eta)\,x_i,\qquad "
        r"y(\xi,\eta)=\sum_{i=1}^{n} N_i(\xi,\eta)\,y_i"
    )
    doc.para(
        r"Las funciones de forma $N_i(\xi,\eta)$ son interpoladores de "
        r"Lagrange: $N_i=1$ en el nodo $i$ y $0$ en los demás. Para Q4 "
        r"son bilineales; para Q9, biquadráticas (tensor-product)."
    )
    doc.subsection("Por qué se trabaja en coordenadas naturales")
    doc.para(
        r"Escribir $N_i(x,y)$ directamente requeriría invertir el mapeo "
        r"$\Phi:(\xi,\eta)\mapsto(x,y)$ — solo es analíticamente "
        r"posible para elementos rectos. En cambio, en $(\xi,\eta)$ las "
        r"$N_i$ tienen forma tensor-product limpia, idéntica para todos "
        r"los elementos. Toda la complejidad geométrica se concentra "
        r"en el Jacobiano de $\Phi$."
    )
    doc.subsection("Propiedad de partición de la unidad")
    doc.equation(r"\sum_{i=1}^{n} N_i(\xi,\eta) \equiv 1 \quad \forall(\xi,\eta)\in\hat\Omega")
    doc.para(
        r"Garantiza que el elemento puede representar movimientos rígidos "
        r"de cuerpo y deformaciones constantes — requisito mínimo de "
        r"convergencia (consistency)."
    )


def _m2_jacobian(doc: TheoryDoc) -> None:
    doc.section_numbered("M2 · Jacobiano del mapeo")
    doc.para(
        r"El Jacobiano controla cómo el cuadrado natural se deforma para "
        r"convertirse en el elemento físico:"
    )
    doc.equation(
        r"\mathbf{J}(\xi,\eta)=\frac{\partial(x,y)}{\partial(\xi,\eta)}=\begin{bmatrix}"
        r"\partial x/\partial\xi & \partial y/\partial\xi \\ "
        r"\partial x/\partial\eta & \partial y/\partial\eta"
        r"\end{bmatrix}"
    )
    doc.subsection("Determinante: indicador de validez")
    doc.equation(
        r"\det\mathbf{J}=\frac{\partial x}{\partial\xi}\frac{\partial y}{\partial\eta}"
        r"-\frac{\partial y}{\partial\xi}\frac{\partial x}{\partial\eta}"
    )
    doc.para(
        r"$\det\mathbf{J}>0$ en TODO el cuadrado natural garantiza que "
        r"el mapeo es invertible y orientación-preservante. Si $\det\mathbf{J}$ "
        r"cambia de signo en algún punto, el elemento está plegado y NO "
        r"puede usarse: el integrando explota y la rigidez asociada queda "
        r"indefinida."
    )
    doc.subsection("Relación con áreas")
    doc.para(
        r"En un punto $(\xi,\eta)$, $|\det\mathbf{J}|$ es el factor de "
        r"escala local entre el diferencial de área natural y el físico:"
    )
    doc.equation(r"dA_{\text{físico}} = |\det\mathbf{J}|\,d\xi\,d\eta")


def _m3_constitutive(doc: TheoryDoc) -> None:
    doc.section_numbered("M3 · Matriz constitutiva D")
    doc.para(
        r"Relaciona deformaciones $\boldsymbol\varepsilon$ y tensiones "
        r"$\boldsymbol\sigma$ en régimen elástico lineal:"
    )
    doc.equation(r"\boldsymbol\sigma = \mathbf{D}\,\boldsymbol\varepsilon")
    doc.subsection("Tensión plana (TP)")
    doc.para(r"Pieza delgada con cargas en su plano (placas, membranas):")
    doc.equation(
        r"\mathbf{D}_{TP}=\frac{E}{1-\nu^2}\begin{bmatrix}"
        r"1 & \nu & 0 \\ \nu & 1 & 0 \\ 0 & 0 & (1-\nu)/2"
        r"\end{bmatrix}"
    )
    doc.subsection("Deformación plana (DP)")
    doc.para(r"Cuerpo largo restringido en una dirección (presas, tuberías):")
    doc.equation(
        r"\mathbf{D}_{DP}=\frac{E}{(1+\nu)(1-2\nu)}\begin{bmatrix}"
        r"1-\nu & \nu & 0 \\ \nu & 1-\nu & 0 \\ 0 & 0 & (1-2\nu)/2"
        r"\end{bmatrix}"
    )
    doc.subsection("Locking volumétrico (DP, $\\nu \\to 0.5$)")
    doc.para(
        r"En DP, $1/(1-2\nu)\to\infty$ cuando $\nu\to 0.5$: el módulo "
        r"volumétrico diverge. Los elementos isoparamétricos estándar NO "
        r"pueden representar materiales incompresibles sin formulaciones "
        r"mixtas (B-bar, SRI, u/p)."
    )


def _m4_b_matrix(doc: TheoryDoc) -> None:
    doc.section_numbered("M4 · Matriz B (deformación–desplazamiento)")
    doc.para(
        r"Relaciona los desplazamientos nodales con las deformaciones "
        r"continuas $\boldsymbol\varepsilon=(\varepsilon_x,\varepsilon_y,"
        r"\gamma_{xy})^T$:"
    )
    doc.equation(r"\boldsymbol\varepsilon = \mathbf{B}(\xi,\eta)\,\mathbf{u}_e")
    doc.para(
        r"Cada par de columnas $(2i-1, 2i)$ corresponde a un nodo $i$:"
    )
    doc.equation(
        r"\mathbf{B}_i=\begin{bmatrix}"
        r"\partial N_i/\partial x & 0 \\ "
        r"0 & \partial N_i/\partial y \\ "
        r"\partial N_i/\partial y & \partial N_i/\partial x"
        r"\end{bmatrix}"
    )
    doc.subsection("Regla de la cadena vía J inversa")
    doc.para(
        r"Las derivadas en $(x,y)$ se obtienen de las derivadas en "
        r"$(\xi,\eta)$ mediante $\mathbf{J}^{-1}$:"
    )
    doc.equation(
        r"\begin{bmatrix}\partial N_i/\partial x \\ \partial N_i/\partial y\end{bmatrix}"
        r"=\mathbf{J}^{-1}\,\begin{bmatrix}\partial N_i/\partial\xi \\ \partial N_i/\partial\eta\end{bmatrix}"
    )
    doc.subsection("Superconvergencia de Gauss (Barlow 1976)")
    doc.para(
        r"Las tensiones obtenidas como $\boldsymbol\sigma=\mathbf{D B u}$ "
        r"son discontinuas entre elementos (la formulación de Galerkin "
        r"sólo garantiza continuidad $C^0$ del desplazamiento). Pero dentro "
        r"de cada elemento existen puntos privilegiados donde la "
        r"convergencia del error es de orden mayor al promedio:"
    )
    doc.equation(
        r"\|\sigma_h - \sigma\|_{PG} = O(h^{p+1}), \quad "
        r"\text{vs.\ } O(h^{p}) \text{ en el resto del elemento}"
    )
    doc.para(
        r"Barlow (1976) demostró que esos puntos coinciden con los puntos "
        r"de cuadratura de Gauss-Legendre del orden $p$ usado para "
        r"integrar $\mathbf{k}_e$. Para Q4 son los 4 puntos $2\times 2$ "
        r"en $(\pm 1/\sqrt{3},\pm 1/\sqrt{3})$; para Q9, los 9 puntos "
        r"$3\times 3$. Por eso EduFEM calcula primero la tensión en los "
        r"PG y después la \emph{extrapola} a los nodos: evaluar "
        r"$\boldsymbol\sigma$ directamente en el nodo del elemento "
        r"daría un valor menos preciso que extrapolarlo desde su PG más "
        r"cercano. El procedimiento completo de extrapolación + promediado "
        r"vive en el módulo M8."
    )


def _m5_stiffness_gauss(doc: TheoryDoc) -> None:
    doc.section_numbered("M5 · Matriz de rigidez $k_e$ e integración de Gauss")
    doc.para(
        r"La rigidez de cada elemento surge del principio de los trabajos "
        r"virtuales:"
    )
    doc.equation(
        r"k_e = \int_{\Omega_e} \mathbf{B}^T \mathbf{D} \mathbf{B}\,t\,dA "
        r"= \int_{-1}^{1}\!\!\int_{-1}^{1} \mathbf{B}^T \mathbf{D} \mathbf{B}\,t\,|\det\mathbf{J}|\,d\xi\,d\eta"
    )
    doc.subsection("La integral es analíticamente intratable")
    doc.para(
        r"El integrando contiene $\det\mathbf{J}$ en denominador (vía "
        r"$\mathbf{J}^{-1}$ dentro de B). Para elementos rectos $\det\mathbf{J}$ "
        r"es constante y la integral cierra en forma cerrada, pero apenas "
        r"el elemento se distorsiona $\det\mathbf{J}$ es polinómico en "
        r"$(\xi,\eta)$ y el integrando se vuelve racional — no admite "
        r"primitivas elementales. Por eso usamos integración numérica."
    )
    doc.subsection("Cuadratura de Gauss-Legendre")
    doc.para(
        r"Aproxima la integral por una suma ponderada en $n_g$ puntos:"
    )
    doc.equation(
        r"k_e \approx \sum_{p=1}^{n_g} w_p\,\mathbf{B}^T(\xi_p,\eta_p)\,\mathbf{D}\,"
        r"\mathbf{B}(\xi_p,\eta_p)\,t\,|\det\mathbf{J}(\xi_p,\eta_p)|"
    )
    doc.para(
        r"Los puntos $(\xi_p,\eta_p)$ y pesos $w_p$ son los de Gauss-Legendre "
        r"unidimensionales tensorizados. Para Q4 se usa $2\times 2$ (4 puntos); "
        r"para Q9, $3\times 3$ (9 puntos) — orden suficiente para integrar "
        r"exactamente cualquier polinomio del integrando en el caso recto."
    )
    doc.subsection("Sub-integración y modos espurios (hourglass)")
    doc.para(
        r"Usar $1\times 1$ en Q4 (sub-integración) reduce costo pero deja "
        r"sin penalizar los modos espurios de deformación nula en el punto "
        r"de Gauss — conocidos en la literatura como \emph{hourglass modes}. "
        r"EduFEM advierte al alumno cuando elige este orden."
    )


def _m6_equivalent_forces(doc: TheoryDoc) -> None:
    doc.section_numbered("M6 · Fuerzas equivalentes nodales")
    doc.para(
        r"Las cargas distribuidas (presión sobre una arista, peso propio) "
        r"se convierten en fuerzas nodales mediante el principio de los "
        r"trabajos virtuales:"
    )
    doc.subsection("Carga sobre una arista (tracción)")
    doc.equation(
        r"\mathbf{f}_e^{(\text{arista})} = \int_{\Gamma_e} \mathbf{N}^T \mathbf{q}\,t\,ds"
    )
    doc.para(
        r"Para una arista recta con carga $q$ constante por unidad de "
        r"longitud, en Q4 el reparto es L/2, L/2 (mitad y mitad) y en Q9 "
        r"el patrón clásico es $L/6,\;4L/6,\;L/6$ entre nodos extremos y "
        r"medio. La asimetría sale directamente de integrar las $N_i$ "
        r"cuadráticas a lo largo del lado."
    )
    doc.subsection("Peso propio (fuerza volumétrica)")
    doc.equation(
        r"\mathbf{f}_e^{(\text{volumen})} = \int_{\Omega_e} \mathbf{N}^T \rho\,\mathbf{g}\,t\,dA"
    )
    doc.para(
        r"$\rho$ es la densidad del material y $\mathbf{g}$ el vector "
        r"gravedad. La integral se evalúa con Gauss usando el mismo "
        r"esquema que para $k_e$."
    )


def _m7_assembly(doc: TheoryDoc) -> None:
    doc.section_numbered("M7 · Ensamblaje global, BCs y solver")

    doc.subsection("Mapeo LM (location matrix)")
    doc.para(
        r"Cada elemento $e$ tiene asociada una \textbf{location matrix} "
        r"$\mathbf{LM}_e$ que enumera los GDLs globales de sus "
        r"$2\cdot n_{nodos}$ entradas locales. Para un nodo $i$ del "
        r"modelo, los dos GDLs globales son $\mathrm{GDL}_x = 2(i-1)$ y "
        r"$\mathrm{GDL}_y = 2(i-1)+1$. La $\mathbf{LM}_e$ se construye "
        r"recorriendo los nodos del elemento y concatenando estos índices."
    )
    doc.para(
        r"El ensamblaje recorre los elementos y suma:"
    )
    doc.equation(
        r"\mathbf{K}[\mathbf{LM}_e,\mathbf{LM}_e]\,\mathrel{+}=\,\mathbf{k}_e, "
        r"\qquad \mathbf{F}[\mathbf{LM}_e]\,\mathrel{+}=\,\mathbf{f}_e"
    )
    doc.para(
        r"Por ser una sumatoria, el orden de los elementos no afecta el "
        r"resultado final — propiedad que permite paralelizar el "
        r"ensamblaje en problemas grandes. La sparsity de $\mathbf{K}$ "
        r"refleja la conectividad: $K_{IJ} \neq 0$ si y sólo si los GDLs "
        r"$I$ y $J$ comparten al menos un elemento."
    )

    doc.subsection("Condiciones de contorno (método de eliminación)")
    doc.para(
        r"EduFEM implementa el \textbf{método de eliminación} (también "
        r"llamado de partición): las filas y columnas de los GDLs "
        r"prescritos se quitan de $\mathbf{K}$ y de $\mathbf{F}$, "
        r"formando el sistema reducido:"
    )
    doc.equation(
        r"\mathbf{K}_{red}\,\mathbf{u}_{red} = \mathbf{F}_{red}"
    )
    doc.para(
        r"Tras resolver $\mathbf{u}_{red}$, los desplazamientos prescritos "
        r"(típicamente $0$ para apoyos perfectos) se reinsertan en el "
        r"vector global $\mathbf{u}$; las reacciones en los apoyos se "
        r"calculan como $\mathbf{R} = \mathbf{K}\,\mathbf{u} - \mathbf{F}$ "
        r"(no nulas solo en los GDLs restringidos)."
    )
    doc.para(
        r"\emph{Es el único método de aplicación de BCs implementado en "
        r"EduFEM} — la eliminación directa es suficiente para la familia "
        r"de problemas que aborda el software y preserva exactamente la "
        r"simetría definida positiva de $\mathbf{K}_{red}$, condición "
        r"necesaria para Cholesky."
    )

    doc.subsection("Solver Cholesky")
    doc.para(
        r"$\mathbf{K}_{red}$ es \textbf{simétrica definida positiva} (SPD): "
        r"admite factorización de Cholesky $\mathbf{K}_{red}=\mathbf{L}\,\mathbf{L}^T$, "
        r"donde $\mathbf{L}$ es triangular inferior. La solución se "
        r"obtiene en dos sustituciones triangulares:"
    )
    doc.equation(
        r"\mathbf{L}\,\mathbf{y}=\mathbf{F}_{red}\quad\text{(forward)}, "
        r"\qquad \mathbf{L}^T\,\mathbf{u}_{red}=\mathbf{y}\quad\text{(backward)}"
    )
    doc.para(
        r"Cholesky es preferible a LU general por dos motivos: "
        r"(i) explota la simetría y consume la mitad de memoria y "
        r"operaciones ($\sim \tfrac{1}{6}n^3$ flops vs $\tfrac{1}{3}n^3$ "
        r"de LU); (ii) \emph{no requiere pivoteo}: para una matriz SPD "
        r"siempre existe la factorización, lo que preserva la dispersión "
        r"original. Si por algún motivo $\mathbf{K}_{red}$ no fuera SPD "
        r"(geometría degenerada, BCs insuficientes, elementos invertidos), "
        r"Cholesky \emph{falla limpiamente} indicando el problema, en vez "
        r"de devolver una solución espuria."
    )

    doc.subsection("Sparsity y re-numeración")
    doc.para(
        r"$\mathbf{K}$ tiene estructura de banda: el ancho de banda "
        r"depende del orden de numeración nodal. Algoritmos de "
        r"re-numeración (Reverse Cuthill-McKee) minimizan el ancho y "
        r"aceleran la factorización en problemas grandes. EduFEM no los "
        r"aplica todavía — para los tamaños didácticos típicos el costo "
        r"de la factorización densa es menor que el costo de la "
        r"re-numeración."
    )


def _m8_post_processing(doc: TheoryDoc) -> None:
    doc.section_numbered("M8 · Post-proceso: tensiones derivadas")
    doc.para(
        r"El post-proceso transforma los desplazamientos nodales "
        r"$\mathbf{u}$ —la única incógnita directa del MEF— en las "
        r"magnitudes que un ingeniero usa para juzgar el diseño. La "
        r"cadena es:"
    )
    doc.equation(
        r"\mathbf{u} \;\to\; \boldsymbol{\varepsilon}_{Gauss} \;\to\; "
        r"\boldsymbol{\sigma}_{Gauss} \;\to\; \boldsymbol{\sigma}_{nodo} "
        r"\;\to\; \boldsymbol{\sigma}_{promediado} \;\to\; "
        r"(\sigma_1, \sigma_2, \sigma_{VM})"
    )

    doc.subsection("Tensiones en los puntos de Gauss")
    doc.para(
        r"Para cada elemento se reconstruye la deformación en sus PG vía "
        r"$\boldsymbol{\varepsilon}=\mathbf{B}(\xi_p,\eta_p)\,\mathbf{u}_e$ "
        r"y, por la ley de Hooke, "
        r"$\boldsymbol{\sigma}=\mathbf{D}\,\boldsymbol{\varepsilon}$. La "
        r"implementación vive en \texttt{fem/stress.py::compute\_element\_stresses}. "
        r"La razón para calcularlas allí y no directamente en los nodos "
        r"es la \emph{superconvergencia} discutida en M4: los PG son los "
        r"puntos óptimos del elemento."
    )

    doc.subsection("Extrapolación Gauss → nodos (Q4)")
    doc.para(
        r"Las tensiones en los PG se llevan a los nodos mediante una "
        r"matriz de extrapolación $\mathbf{E}$ que es la inversa de la "
        r"matriz de funciones de forma evaluadas en los PG: "
        r"$\boldsymbol{\sigma}^{\,nodo} = \mathbf{E}\,\boldsymbol{\sigma}^{\,Gauss}$ "
        r"con $\mathbf{E}=\mathbf{N}_p^{-1}$."
    )
    doc.para(
        r"Para Q4 con cuadratura $2\times 2$, los nodos están en "
        r"$(\pm 1,\pm 1)$ y los PG en $(\pm 1/\sqrt{3},\pm 1/\sqrt{3})$. "
        r"La matriz cerrada con $s=\sqrt{3}$ es:"
    )
    doc.equation(
        r"\mathbf{E}_{Q4} = \frac{1}{4}\begin{bmatrix}"
        r"(1+s)^2 & (1-s^2) & (1-s)^2 & (1-s^2) \\"
        r"(1-s^2) & (1-s)^2 & (1-s^2) & (1+s)^2 \\"
        r"(1-s)^2 & (1-s^2) & (1+s)^2 & (1-s^2) \\"
        r"(1-s^2) & (1+s)^2 & (1-s^2) & (1-s)^2"
        r"\end{bmatrix}"
    )
    doc.para(
        r"El factor $\sqrt{3}$ que aparece en la matriz es directamente "
        r"el inverso de las coordenadas naturales de los PG — es por eso "
        r"que se lo llama coloquialmente `factor de extrapolación'. La "
        r"implementación literal está en "
        r"\texttt{fem/stress.py::extrapolate\_to\_nodes\_q4}."
    )

    doc.subsection("Extrapolación Gauss → nodos (Q9)")
    doc.para(
        r"Para Q9 con cuadratura $3\times 3$ no existe expresión cerrada "
        r"simple. La matriz $\mathbf{E}_{Q9}$ (de $9\times 9$) se "
        r"construye evaluando numéricamente las 9 funciones de forma "
        r"bicuadráticas en los 9 PG y luego invirtiendo:"
    )
    doc.equation(
        r"(\mathbf{N}_p)_{ji} = N_i(\xi_p,\eta_p), \qquad "
        r"\mathbf{E}_{Q9} = \mathbf{N}_p^{-1}"
    )
    doc.para(
        r"EduFEM cachea $\mathbf{E}_{Q9}$ a nivel de módulo (es la "
        r"misma para todos los elementos Q9, independiente de su "
        r"geometría física): la inversión $9\times 9$ se hace una sola "
        r"vez por sesión, no por elemento. Ver "
        r"\texttt{fem/stress.py::\_q9\_extrapolation\_matrix}."
    )

    doc.subsection("Promediado nodal entre elementos adyacentes")
    doc.para(
        r"Un nodo compartido por $k$ elementos recibe $k$ valores "
        r"extrapolados distintos — las tensiones del MEF son "
        r"discontinuas entre elementos. EduFEM aplica un promedio "
        r"aritmético simple:"
    )
    doc.equation(
        r"\sigma_n^{\,promediado} = \frac{1}{k_n}\sum_{e\in\mathcal{E}_n} "
        r"\sigma_n^{\,(e)}"
    )
    doc.para(
        r"donde $\mathcal{E}_n$ es el conjunto de elementos que comparten "
        r"el nodo $n$ y $k_n=|\mathcal{E}_n|$. Implementación: "
        r"\texttt{fem/stress.py::compute\_all\_stresses}."
    )
    doc.para(
        r"\textbf{El salto pre-promediado es un indicador de error de malla.} "
        r"Si las $k$ contribuciones a un mismo nodo difieren mucho entre "
        r"sí, la malla es insuficiente para capturar el gradiente local; "
        r"refinarla allí debería reducir el salto. Por eso muchos códigos "
        r"comerciales muestran opcionalmente el campo \emph{no promediado} "
        r"junto al promediado: la diferencia es una herramienta de "
        r"diagnóstico."
    )

    doc.subsection(r"Tensiones principales $\sigma_1$, $\sigma_2$, $\theta_p$")
    doc.para(
        r"En 2D el estado tensional en un punto se describe por "
        r"$(\sigma_x,\sigma_y,\tau_{xy})$. Las tensiones principales "
        r"$\sigma_1\geq\sigma_2$ son los autovalores del tensor de "
        r"tensiones; corresponden a las tensiones normales máxima y "
        r"mínima sobre los planos donde el corte se anula ($\tau=0$). "
        r"La fórmula cerrada es:"
    )
    doc.equation(
        r"\sigma_{1,2} = \frac{\sigma_x+\sigma_y}{2} \pm "
        r"\sqrt{\left(\frac{\sigma_x-\sigma_y}{2}\right)^2 + \tau_{xy}^{\,2}}"
    )
    doc.para(
        r"La dirección principal $\theta_p$ (ángulo del plano "
        r"perpendicular a $\sigma_1$ respecto del eje $x$):"
    )
    doc.equation(
        r"\tan(2\theta_p) = \frac{2\,\tau_{xy}}{\sigma_x-\sigma_y}"
    )
    doc.para(
        r"\textbf{Convención de color en EduFEM}: $\sigma_1>0$ indica "
        r"\emph{tracción} y se grafica en azul (el material se estira); "
        r"$\sigma_2<0$ indica \emph{compresión} y se grafica en rojo (se "
        r"aplasta). Las cruces principales sobre la malla — visibles en "
        r"el Post-tab del software y en la Memoria — usan estos colores. "
        r"Pedagógicamente, las direcciones principales muestran el "
        r"\emph{flujo de carga} de la estructura."
    )

    doc.subsection(r"Tensión equivalente de von Mises $\sigma_{VM}$")
    doc.para(
        r"El criterio de von Mises convierte el estado tensional 2D en "
        r"un escalar comparable contra la tensión de fluencia uniaxial "
        r"$\sigma_y$ del material. Para problemas planos:"
    )
    doc.equation(
        r"\sigma_{VM} = \sqrt{\sigma_x^{\,2} - \sigma_x\,\sigma_y + "
        r"\sigma_y^{\,2} + 3\,\tau_{xy}^{\,2}} = "
        r"\sqrt{\sigma_1^{\,2} - \sigma_1\,\sigma_2 + \sigma_2^{\,2}}"
    )
    doc.para(
        r"El criterio dice: el material plastifica cuando $\sigma_{VM}"
        r"\geq\sigma_y$. Es la métrica más usada en diseño dúctil "
        r"(metales, aceros estructurales) porque captura la contribución "
        r"del corte sin requerir información direccional. \textbf{Atención}: "
        r"para materiales frágiles (hormigón, vidrio, cerámicas) von "
        r"Mises subestima el riesgo — usar criterios específicos para "
        r"frágiles (p.\ ej.\ Rankine, basados en $\sigma_1$ máximo)."
    )


def _m9_convergence(doc: TheoryDoc) -> None:
    doc.section_numbered("M9 · Convergencia Q4 vs Q9 (h-refinamiento)")
    doc.para(
        r"Refinar la malla (h-refinamiento: dividir cada elemento en 4 "
        r"sub-elementos) reduce el error de discretización. Si la solución "
        r"continua tiene regularidad suficiente, el error en norma "
        r"energética decae como:"
    )
    doc.equation(r"\|u - u_h\|_E \le C\,h^{p}")
    doc.para(
        r"donde $h$ es el tamaño del elemento y $p$ es el orden polinomial "
        r"de las funciones de forma: $p=1$ para Q4 (decae linealmente) y "
        r"$p=2$ para Q9 (decae cuadráticamente). En problemas regulares, "
        r"Q9 alcanza precisión equivalente a Q4 con MUCHOS menos elementos "
        r"— pero a costo de más GDLs por elemento."
    )
    doc.subsection("Cuándo conviene cada uno")
    doc.para(
        r"Q4: geometrías simples, gradientes suaves, modelos exploratorios. "
        r"Q9: zonas de concentración de tensiones, contornos curvos "
        r"(las $N_i$ cuadráticas representan exactamente arcos parabólicos "
        r"en el mapeo isoparamétrico), problemas con flexión dominante."
    )
