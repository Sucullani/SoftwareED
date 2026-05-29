"""
Theory Hub — documento unificado de teoría MEF accesible desde Ayuda.

Documento educativo autocontenido: cada sección desarrolla un eslabón del
pipeline clásico del Método de los Elementos Finitos, en el orden lógico
en que se construye la solución. La exposición es la habitual de los
libros de texto (Zienkiewicz, Hughes, Bathe, Cook): planteo del problema
continuo, formulación débil, discretización con funciones de forma
isoparamétricas, integración numérica, ensamblaje, aplicación de
condiciones de contorno, resolución del sistema lineal y post-proceso.

No incluye valores específicos del proyecto del usuario (E, ν, ρ, etc.)
ni hace referencia a archivos del software: es teoría general que sirve
para cualquier análisis MEF 2D con elementos Q4 / Q9.

API:
    open_theory_hub(parent) — abre un TheoryViewer flotante con el doc
    agregado. No es modal; el usuario puede consultarlo mientras opera
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
        subtitle="Fundamentos clásicos para análisis Q4 / Q9 plano",
    )


# ────────────────────────────────────────────────────────────────────
# Constructor del documento agregado
# ────────────────────────────────────────────────────────────────────


def _build_full_theory_document(doc: TheoryDoc) -> None:
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


# ────────────────────────────────────────────────────────────────────
# Introducción
# ────────────────────────────────────────────────────────────────────


def _intro(doc: TheoryDoc) -> None:
    doc.section_numbered("Introducción")
    doc.para(
        r"El \textbf{Método de los Elementos Finitos (MEF)} busca el campo "
        r"de desplazamientos $\mathbf{u}(x,y)$ que satisface el equilibrio "
        r"elástico"
    )
    doc.equation(
        r"\nabla\cdot\boldsymbol\sigma(\mathbf{u}) + \mathbf{b} = \mathbf{0}"
        r"\quad\text{en }\Omega,"
    )
    doc.para(
        r"sujeto a desplazamientos prescritos $\mathbf{u}=\bar{\mathbf{u}}$ "
        r"en una parte del contorno $\Gamma_u$ y tracciones aplicadas "
        r"$\boldsymbol\sigma\cdot\mathbf{n}=\bar{\mathbf{t}}$ en el resto "
        r"$\Gamma_t$. $\mathbf{b}$ es la fuerza por unidad de volumen "
        r"(peso propio si actúa la gravedad)."
    )
    doc.para(
        r"Para geometrías generales esta ecuación diferencial no tiene "
        r"solución analítica, así que se la reemplaza por su \emph{forma "
        r"débil} (principio de los trabajos virtuales): encontrar "
        r"$\mathbf{u}$ admisible tal que"
    )
    doc.equation(
        r"\int_\Omega \boldsymbol\sigma(\mathbf{u}):\boldsymbol\varepsilon"
        r"(\delta\mathbf{u})\,d\Omega = "
        r"\int_\Omega \mathbf{b}\cdot\delta\mathbf{u}\,d\Omega + "
        r"\int_{\Gamma_t} \bar{\mathbf{t}}\cdot\delta\mathbf{u}\,d\Gamma"
        r"\quad \forall\,\delta\mathbf{u} \text{ admisible.}"
    )
    doc.para(
        r"El MEF restringe el espacio de funciones admisibles a polinomios "
        r"a trozos definidos sobre una malla finita: el dominio $\Omega$ "
        r"se divide en $N$ \textbf{elementos} unidos por \textbf{nodos}, y "
        r"el campo continuo $\mathbf{u}(x,y)$ queda representado por un "
        r"vector $\mathbf{u}$ de $2\cdot N_{nodos}$ valores nodales "
        r"(dos por nodo en 2D: $u_x$ y $u_y$). El equilibrio se reduce "
        r"entonces al sistema algebraico"
    )
    doc.equation(r"\mathbf{K}\,\mathbf{u} = \mathbf{F},")
    doc.para(
        r"con $\mathbf{K}$ la matriz de rigidez global y $\mathbf{F}$ el "
        r"vector de fuerzas nodales equivalentes."
    )
    doc.para(r"Cada elemento aporta:")
    doc.raw(r"\begin{itemize}")
    doc.raw(r"\item una matriz de rigidez local $\mathbf{k}_e$ que mide la "
            r"resistencia del elemento a deformarse, y")
    doc.raw(r"\item un vector de cargas locales $\mathbf{f}_e$ que reparte "
            r"las cargas distribuidas a los nodos.")
    doc.raw(r"\end{itemize}")
    doc.para(
        r"Ensamblar el sistema consiste en sumar todas las contribuciones "
        r"$\mathbf{k}_e$ y $\mathbf{f}_e$ en los GDL globales que les "
        r"corresponden. Una vez resuelto $\mathbf{K}\,\mathbf{u}=\mathbf{F}$ "
        r"se calculan las deformaciones $\boldsymbol\varepsilon$ y "
        r"tensiones $\boldsymbol\sigma$ en el interior de cada elemento "
        r"(post-proceso)."
    )
    doc.para(r"El pipeline canónico del MEF es:")
    doc.equation(
        r"\text{modelo} \;\to\; \mathbf{N} \;\to\; \mathbf{J} \;\to\; "
        r"\mathbf{B} \;\to\; \mathbf{D} \;\to\; \mathbf{k}_e \;\to\; "
        r"\mathbf{K},\,\mathbf{F} \;\to\; \text{BCs} \;\to\; "
        r"\mathbf{K}\,\mathbf{u}=\mathbf{F} \;\to\; \boldsymbol{\sigma}."
    )
    doc.para(
        r"Las secciones siguientes desarrollan cada eslabón en el orden "
        r"en que aparece."
    )


# ────────────────────────────────────────────────────────────────────
# M0 · Calidad geométrica de la malla
# ────────────────────────────────────────────────────────────────────


def _m0_mesh_quality(doc: TheoryDoc) -> None:
    doc.section_numbered("M0 · Calidad geométrica de la malla")
    doc.para(
        r"Antes de calcular cualquier rigidez la malla debe ser válida y, de "
        r"ser posible, bien condicionada: sin elementos invertidos, sin "
        r"distorsión angular excesiva y sin elongación extrema. Dos métricas "
        r"geométricas \emph{ortogonales}, ambas normalizadas al rango $[0,1]$ "
        r"con $1$ = cuadrado ideal, describen la salud de un cuadrilátero: el "
        r"\emph{Jacobiano escalado} mide la forma angular y la validez, y la "
        r"\emph{compacidad} (\textit{stretch}) mide la proporción geométrica."
    )

    doc.subsection_numbered("Jacobiano escalado (forma angular y validez)")
    doc.para(
        r"En cada vértice $i$ se forman los vectores de las dos aristas que "
        r"concurren, $\mathbf{a}_i=\mathbf{r}_{i+1}-\mathbf{r}_i$ y "
        r"$\mathbf{b}_i=\mathbf{r}_{i-1}-\mathbf{r}_i$. El Jacobiano escalado "
        r"del vértice es el determinante normalizado por las longitudes:"
    )
    doc.equation(
        r"\mathrm{SJ}_i = \frac{\det[\,\mathbf{a}_i\ \ \mathbf{b}_i\,]}"
        r"{\lVert\mathbf{a}_i\rVert\,\lVert\mathbf{b}_i\rVert} = \sin\theta_i,"
        r"\qquad \mathrm{SJ} = \min_{i=1,\dots,4}\mathrm{SJ}_i ."
    )
    doc.para(
        r"que para un cuadrilátero convexo orientado en sentido antihorario "
        r"coincide con el seno del ángulo interno $\theta_i$. En un cuadrado "
        r"los cuatro ángulos valen $90^\circ$ y $\mathrm{SJ}=1$; a medida que "
        r"el peor ángulo se aleja de $90^\circ$ (hacia $0^\circ$ o "
        r"$180^\circ$) su seno cae hacia $0$. Un valor $\mathrm{SJ}\le 0$ "
        r"indica un elemento \textbf{invertido} ($\det\mathbf{J}\le 0$): el "
        r"mapeo isoparamétrico deja de ser biyectivo y la formulación se "
        r"rompe."
    )
    doc.para(
        r"El Scaled Jacobian vive en el rango $[-1,1]$ (rango completo de la "
        r"librería Verdict): $\mathrm{SJ}=1$ es el cuadrado perfecto y "
        r"$\mathrm{SJ}\le 0$ señala un elemento inválido. El umbral de "
        r"aceptabilidad es $\mathrm{SJ}\ge 0{,}5$. Conviene distinguir la "
        r"\emph{validez} (binaria: $\mathrm{SJ}>0$ o no) de la \emph{calidad} "
        r"continua de un elemento ya válido."
    )

    doc.subsection_numbered("Compacidad / stretch (proporción geométrica)")
    doc.para(
        r"La compacidad combina la elongación y el aplastamiento en un único "
        r"número, comparando la arista más corta con la diagonal más larga:"
    )
    doc.equation(
        r"Q = \frac{\sqrt{2}\,L_{\min}}{D_{\max}} \;\in\; [0,1],"
    )
    doc.para(
        r"donde $L_{\min}$ es la menor de las cuatro aristas y $D_{\max}$ la "
        r"mayor de las dos diagonales. El factor $\sqrt{2}$ calibra el "
        r"cuadrado perfecto a $Q=1$ (en un cuadrado de lado $L$ la diagonal "
        r"mide $L\sqrt{2}$). Valores bajos delatan elementos alargados o "
        r"aplastados, que empeoran el condicionamiento de la matriz de "
        r"rigidez y la precisión de las tensiones. El umbral de aceptabilidad "
        r"de la librería Verdict es $Q\ge 0{,}25$; un valor $Q\ge 0{,}5$ ya "
        r"corresponde a buena calidad."
    )
    doc.para(
        r"Ambas métricas viven en $[0,1]$ con $1$ = ideal y comparten el "
        r"mismo mapeo cromático rojo$\to$amarillo$\to$verde, de modo que un "
        r"mismo color significa la misma calidad en cualquiera de las dos. No "
        r"detectan la \emph{trapezoidalidad pura} (un cuadrilátero con "
        r"ángulos rectos pero lados opuestos no paralelos), fenómeno ligado "
        r"al \textit{trapezoidal locking} de los elementos de cuatro nodos, "
        r"que se aborda por separado."
    )


# ────────────────────────────────────────────────────────────────────
# M1 · Mapeo isoparamétrico y funciones de forma
# ────────────────────────────────────────────────────────────────────


def _m1_iso_mapping(doc: TheoryDoc) -> None:
    doc.section_numbered("M1 · Mapeo isoparamétrico y funciones de forma N")
    doc.para(
        r"Todo elemento físico se describe como una imagen del cuadrado "
        r"de referencia (o \emph{elemento maestro}) $\hat\Omega=[-1,1]^2$ "
        r"mediante el mapeo isoparamétrico:"
    )
    doc.equation(
        r"x(\xi,\eta) = \sum_{i=1}^{n} N_i(\xi,\eta)\,x_i, \qquad "
        r"y(\xi,\eta) = \sum_{i=1}^{n} N_i(\xi,\eta)\,y_i,"
    )
    doc.para(
        r"donde $(x_i,y_i)$ son las coordenadas físicas del nodo $i$ y "
        r"las $N_i(\xi,\eta)$ son las \textbf{funciones de forma}. La "
        r"palabra \emph{isoparamétrico} significa que las mismas $N_i$ "
        r"interpolan la geometría y los desplazamientos:"
    )
    doc.equation(
        r"u_x(\xi,\eta) = \sum_{i=1}^{n} N_i(\xi,\eta)\,u_{x,i}, \qquad "
        r"u_y(\xi,\eta) = \sum_{i=1}^{n} N_i(\xi,\eta)\,u_{y,i}."
    )

    doc.subsection_numbered("Funciones de forma de Q4 (bilineales)")
    doc.para(
        r"Para el cuadrilátero de 4 nodos, las $N_i$ son los productos "
        r"de polinomios lineales de Lagrange en una dimensión:"
    )
    doc.equation(
        r"N_i(\xi,\eta) = \tfrac{1}{4}(1+\xi_i\xi)(1+\eta_i\eta), "
        r"\quad i=1,\dots,4,"
    )
    doc.para(
        r"con $(\xi_i,\eta_i)\in\{-1,+1\}\times\{-1,+1\}$ las coordenadas "
        r"naturales del nodo $i$. Son \emph{bilineales}: lineales en "
        r"$\xi$ por $\eta$ fijo y viceversa."
    )

    doc.subsection_numbered("Funciones de forma de Q9 (bicuadráticas)")
    doc.para(
        r"Para el cuadrilátero lagrangiano de 9 nodos, las $N_i$ son "
        r"productos tensoriales de polinomios cuadráticos de Lagrange:"
    )
    doc.equation(
        r"N_i(\xi,\eta) = L_a(\xi)\,L_b(\eta), \quad i=1,\dots,9,"
    )
    doc.para(
        r"con $L_a,L_b$ tomados del conjunto "
        r"$\{-\tfrac{1}{2}\xi(1-\xi),\;(1-\xi^2),\;\tfrac{1}{2}\xi(1+\xi)\}$ "
        r"y análogos en $\eta$. Los 4 nodos esquina, 4 nodos medios y "
        r"el nodo central completan los 9. La interpolación es "
        r"\emph{biquadrática}."
    )

    doc.subsection_numbered("Propiedades fundamentales")
    doc.para(
        r"Toda función de forma admisible cumple, por construcción:"
    )
    doc.raw(r"\begin{enumerate}")
    doc.raw(r"\item \textbf{Delta de Kronecker en los nodos}: "
            r"$N_i(\xi_j,\eta_j)=\delta_{ij}$ (vale 1 en su nodo, 0 en los "
            r"demás). Esto garantiza que el valor nodal $u_i$ se recupera "
            r"exactamente al evaluar la interpolación en el nodo $i$.")
    doc.raw(r"\item \textbf{Partición de la unidad}: "
            r"$\sum_{i=1}^{n} N_i(\xi,\eta) \equiv 1$ "
            r"en todo el elemento. Asegura que el elemento puede "
            r"representar movimientos rígidos de cuerpo y estados "
            r"de deformación constante — requisito mínimo para que el "
            r"método converja al refinar la malla.")
    doc.raw(r"\item \textbf{Continuidad $C^0$ entre elementos}: el campo "
            r"interpolado es continuo a través de las aristas comunes "
            r"de elementos adyacentes, aunque sus derivadas (y por tanto "
            r"las tensiones) son en general discontinuas.")
    doc.raw(r"\end{enumerate}")

    doc.subsection_numbered("¿Por qué se trabaja en coordenadas naturales?")
    doc.para(
        r"Escribir $N_i(x,y)$ directamente requeriría invertir el mapeo "
        r"$\Phi:(\xi,\eta)\mapsto(x,y)$, lo cual sólo es analíticamente "
        r"posible para elementos rectos. En cambio, en $(\xi,\eta)$ las "
        r"$N_i$ tienen forma tensor-product limpia, idéntica para todos "
        r"los elementos del mismo tipo. Toda la complejidad geométrica "
        r"se concentra en el Jacobiano del mapeo (sección siguiente)."
    )


# ────────────────────────────────────────────────────────────────────
# M2 · Jacobiano del mapeo
# ────────────────────────────────────────────────────────────────────


def _m2_jacobian(doc: TheoryDoc) -> None:
    doc.section_numbered("M2 · Jacobiano del mapeo")
    doc.para(
        r"El Jacobiano controla cómo el cuadrado natural se deforma para "
        r"convertirse en el elemento físico. Es una matriz $2\times 2$ "
        r"cuyas entradas son las derivadas parciales del mapeo:"
    )
    doc.equation(
        r"\mathbf{J}(\xi,\eta) = "
        r"\frac{\partial(x,y)}{\partial(\xi,\eta)} = "
        r"\begin{bmatrix}"
        r"\partial x/\partial\xi & \partial y/\partial\xi \\ "
        r"\partial x/\partial\eta & \partial y/\partial\eta"
        r"\end{bmatrix}"
        r"= \sum_{i=1}^{n}\begin{bmatrix}"
        r"\partial N_i/\partial\xi\,x_i & \partial N_i/\partial\xi\,y_i \\ "
        r"\partial N_i/\partial\eta\,x_i & \partial N_i/\partial\eta\,y_i"
        r"\end{bmatrix}."
    )

    doc.subsection_numbered("Determinante: indicador de validez")
    doc.equation(
        r"\det\mathbf{J} = "
        r"\frac{\partial x}{\partial\xi}\,\frac{\partial y}{\partial\eta} - "
        r"\frac{\partial y}{\partial\xi}\,\frac{\partial x}{\partial\eta}."
    )
    doc.para(
        r"Que $\det\mathbf{J}>0$ en TODO el cuadrado natural garantiza "
        r"que el mapeo es invertible y orientación-preservante. Si "
        r"$\det\mathbf{J}$ cambia de signo en algún punto, el elemento "
        r"está plegado y no puede usarse: el integrando del MEF "
        r"contiene $\mathbf{J}^{-1}$, así que se vuelve indefinido."
    )

    doc.subsection_numbered("Relación con áreas")
    doc.para(
        r"En cada punto $(\xi,\eta)$, $|\det\mathbf{J}|$ es el factor de "
        r"escala local entre el diferencial de área natural y el físico:"
    )
    doc.equation(r"dA_{\text{físico}} = |\det\mathbf{J}|\,d\xi\,d\eta.")
    doc.para(
        r"Por eso aparece como factor multiplicativo cuando se traslada "
        r"una integral del dominio natural al físico (o viceversa) — "
        r"clave en la integración numérica de Gauss."
    )


# ────────────────────────────────────────────────────────────────────
# M3 · Matriz constitutiva D
# ────────────────────────────────────────────────────────────────────


def _m3_constitutive(doc: TheoryDoc) -> None:
    doc.section_numbered("M3 · Matriz constitutiva D")
    doc.para(
        r"En régimen elástico lineal, las tensiones y las deformaciones "
        r"están relacionadas por la ley de Hooke generalizada:"
    )
    doc.equation(r"\boldsymbol\sigma = \mathbf{D}\,\boldsymbol\varepsilon,")
    doc.para(
        r"con $\boldsymbol\sigma=(\sigma_x,\sigma_y,\tau_{xy})^T$ y "
        r"$\boldsymbol\varepsilon=(\varepsilon_x,\varepsilon_y,\gamma_{xy})^T$. "
        r"La matriz constitutiva $\mathbf{D}$ depende del material "
        r"(módulo de Young $E$ y coeficiente de Poisson $\nu$) y del tipo "
        r"de problema plano."
    )

    doc.subsection_numbered("Tensión plana (TP)")
    doc.para(
        r"Hipótesis: cuerpo delgado, de espesor pequeño respecto de sus "
        r"otras dimensiones, cargado en su plano medio. Las componentes "
        r"fuera del plano se anulan: $\sigma_z=\tau_{xz}=\tau_{yz}=0$. "
        r"Aplica a placas y membranas."
    )
    doc.equation(
        r"\mathbf{D}_{TP} = \frac{E}{1-\nu^2}\begin{bmatrix}"
        r"1 & \nu & 0 \\ \nu & 1 & 0 \\ 0 & 0 & (1-\nu)/2"
        r"\end{bmatrix}."
    )

    doc.subsection_numbered("Deformación plana (DP)")
    doc.para(
        r"Hipótesis: cuerpo prismático muy largo en una dirección, con "
        r"sección y cargas invariantes a lo largo del eje. La deformación "
        r"axial se anula: $\varepsilon_z=\gamma_{xz}=\gamma_{yz}=0$. "
        r"Aplica a presas, túneles, tuberías largas y secciones de cuerpos "
        r"alargados."
    )
    doc.equation(
        r"\mathbf{D}_{DP} = \frac{E}{(1+\nu)(1-2\nu)}\begin{bmatrix}"
        r"1-\nu & \nu & 0 \\ \nu & 1-\nu & 0 \\ 0 & 0 & (1-2\nu)/2"
        r"\end{bmatrix}."
    )
    doc.para(
        r"En deformación plana la tensión axial no se anula: "
        r"$\sigma_z=\nu(\sigma_x+\sigma_y)$, y se reconstruye en el "
        r"post-proceso si se necesita."
    )

    doc.subsection_numbered(r"Limitación: locking volumétrico ($\nu\to 0{,}5$)")
    doc.para(
        r"En deformación plana, el factor $1/(1-2\nu)$ tiende a infinito "
        r"cuando $\nu\to 0{,}5$ (materiales casi incompresibles, como "
        r"caucho o suelos saturados). Los elementos isoparamétricos "
        r"estándar de desplazamientos no pueden representar bien esa "
        r"situación: se vuelven artificialmente rígidos (\emph{volumetric "
        r"locking}). El tratamiento riguroso requiere formulaciones "
        r"mixtas (B-bar, SRI, $u/p$), que exceden el alcance básico."
    )


# ────────────────────────────────────────────────────────────────────
# M4 · Matriz B (deformación-desplazamiento)
# ────────────────────────────────────────────────────────────────────


def _m4_b_matrix(doc: TheoryDoc) -> None:
    doc.section_numbered("M4 · Matriz B (deformación–desplazamiento)")
    doc.para(
        r"La matriz $\mathbf{B}$ relaciona los desplazamientos nodales "
        r"del elemento con las deformaciones continuas en su interior:"
    )
    doc.equation(
        r"\boldsymbol\varepsilon(\xi,\eta) = \mathbf{B}(\xi,\eta)\,"
        r"\mathbf{u}_e."
    )
    doc.para(
        r"$\mathbf{u}_e$ es el vector que apila los $2n$ desplazamientos "
        r"nodales del elemento "
        r"$\mathbf{u}_e=(u_{x,1},u_{y,1},\dots,u_{x,n},u_{y,n})^T$. "
        r"$\mathbf{B}$ tiene tres filas (una por cada componente de "
        r"deformación) y $2n$ columnas. Cada par de columnas "
        r"$(2i{-}1, 2i)$ corresponde al nodo $i$:"
    )
    doc.equation(
        r"\mathbf{B}_i = \begin{bmatrix}"
        r"\partial N_i/\partial x & 0 \\ "
        r"0 & \partial N_i/\partial y \\ "
        r"\partial N_i/\partial y & \partial N_i/\partial x"
        r"\end{bmatrix}."
    )
    doc.para(
        r"Las dos primeras filas dan las deformaciones normales "
        r"$\varepsilon_x=\partial u_x/\partial x$ y "
        r"$\varepsilon_y=\partial u_y/\partial y$; la tercera, la "
        r"deformación angular $\gamma_{xy}=\partial u_x/\partial y + "
        r"\partial u_y/\partial x$."
    )

    doc.subsection_numbered("Regla de la cadena vía la inversa del Jacobiano")
    doc.para(
        r"Las funciones de forma están escritas en coordenadas "
        r"naturales, pero las derivadas que aparecen en $\mathbf{B}$ "
        r"están en coordenadas físicas. Se relacionan por la regla de "
        r"la cadena:"
    )
    doc.equation(
        r"\begin{bmatrix}\partial N_i/\partial x \\ "
        r"\partial N_i/\partial y\end{bmatrix} = "
        r"\mathbf{J}^{-1}\,"
        r"\begin{bmatrix}\partial N_i/\partial\xi \\ "
        r"\partial N_i/\partial\eta\end{bmatrix}."
    )
    doc.para(
        r"De aquí se ve por qué el Jacobiano tiene que ser invertible: "
        r"toda la matriz $\mathbf{B}$ depende de $\mathbf{J}^{-1}$, que "
        r"sólo existe si $\det\mathbf{J}\neq 0$."
    )

    doc.subsection_numbered("Superconvergencia de Gauss (Barlow 1976)")
    doc.para(
        r"Las tensiones $\boldsymbol\sigma=\mathbf{D}\,\mathbf{B}\,"
        r"\mathbf{u}_e$ son discontinuas entre elementos (la formulación "
        r"de Galerkin sólo garantiza continuidad $C^0$ del "
        r"desplazamiento, no de sus derivadas). Pero dentro de cada "
        r"elemento existen puntos privilegiados donde la convergencia "
        r"del error es de orden mayor al promedio:"
    )
    doc.equation(
        r"\|\sigma_h - \sigma\|_{PG} = O(h^{p+1}), \qquad "
        r"\text{vs. } O(h^{p}) \text{ en el resto del elemento.}"
    )
    doc.para(
        r"Barlow (1976) demostró que esos puntos coinciden con los "
        r"puntos de cuadratura de Gauss-Legendre usados para integrar "
        r"$\mathbf{k}_e$. Para Q4 son los 4 puntos $2\times 2$ en "
        r"$(\pm 1/\sqrt{3},\pm 1/\sqrt{3})$; para Q9, los 9 puntos "
        r"$3\times 3$ en $(\pm\sqrt{3/5},0,\pm\sqrt{3/5})\times"
        r"(\pm\sqrt{3/5},0,\pm\sqrt{3/5})$. Esto motiva el procedimiento "
        r"clásico del post-proceso: calcular las tensiones primero en "
        r"los puntos de Gauss y \emph{extrapolarlas} a los nodos."
    )


# ────────────────────────────────────────────────────────────────────
# M5 · Matriz de rigidez ke e integración de Gauss
# ────────────────────────────────────────────────────────────────────


def _m5_stiffness_gauss(doc: TheoryDoc) -> None:
    doc.section_numbered("M5 · Matriz de rigidez $\\mathbf{k}_e$ e integración de Gauss")
    doc.para(
        r"Sustituyendo la interpolación $\mathbf{u}=\mathbf{N}\,"
        r"\mathbf{u}_e$ y la ley de Hooke en el principio de los trabajos "
        r"virtuales (sección 1) se llega a la rigidez elemental:"
    )
    doc.equation(
        r"\mathbf{k}_e = \int_{\Omega_e} \mathbf{B}^T \mathbf{D}\,"
        r"\mathbf{B}\,t\,dA "
        r"= \int_{-1}^{1}\!\!\int_{-1}^{1} \mathbf{B}^T \mathbf{D}\,"
        r"\mathbf{B}\,t\,|\det\mathbf{J}|\,d\xi\,d\eta,"
    )
    doc.para(
        r"con $t$ el espesor del elemento (en problemas planos 2D). El "
        r"cambio de variable al cuadrado natural introduce el factor "
        r"$|\det\mathbf{J}|$ y aprovecha que el dominio de integración "
        r"es fijo, $[-1,1]^2$, idéntico para todos los elementos."
    )

    doc.subsection_numbered("La integral es analíticamente intratable")
    doc.para(
        r"El integrando contiene $\det\mathbf{J}$ en denominador (vía "
        r"$\mathbf{J}^{-1}$ dentro de $\mathbf{B}$). Para elementos rectos "
        r"$\det\mathbf{J}$ es constante y la integral cierra en forma "
        r"cerrada, pero apenas el elemento se distorsiona $\det\mathbf{J}$ "
        r"es polinómico en $(\xi,\eta)$ y el integrando se vuelve "
        r"\emph{racional}: una expresión sin primitiva elemental. La "
        r"única alternativa práctica es la \textbf{integración numérica}."
    )

    doc.subsection_numbered("Cuadratura de Gauss-Legendre")
    doc.para(
        r"La cuadratura de Gauss-Legendre aproxima una integral por una "
        r"suma ponderada del integrando evaluado en $n_g$ puntos "
        r"escogidos óptimamente:"
    )
    doc.equation(
        r"\int_{-1}^{1}\!\!\int_{-1}^{1} f(\xi,\eta)\,d\xi\,d\eta "
        r"\approx \sum_{p=1}^{n_g} w_p\,f(\xi_p,\eta_p)."
    )
    doc.para(
        r"Los puntos $(\xi_p,\eta_p)$ y los pesos $w_p$ son los de la "
        r"cuadratura unidimensional de Gauss-Legendre tensorizados. "
        r"Para $n_g$ puntos en una dimensión la cuadratura integra "
        r"\emph{exactamente} polinomios de grado $\le 2n_g-1$. Aplicada "
        r"a la rigidez elemental:"
    )
    doc.equation(
        r"\mathbf{k}_e \approx \sum_{p=1}^{n_g} w_p\,"
        r"\mathbf{B}^T(\xi_p,\eta_p)\,\mathbf{D}\,"
        r"\mathbf{B}(\xi_p,\eta_p)\,t\,|\det\mathbf{J}(\xi_p,\eta_p)|."
    )
    doc.para(
        r"En la práctica se usa $2\times 2$ (4 puntos) para Q4 y "
        r"$3\times 3$ (9 puntos) para Q9. Son los órdenes mínimos que "
        r"integran exactamente la rigidez en el caso recto y mantienen "
        r"convergencia óptima en el caso distorsionado."
    )

    doc.subsection_numbered("Sub-integración y modos espurios (hourglass)")
    doc.para(
        r"Usar $1\times 1$ (un solo punto en Q4) reduce el costo de "
        r"cálculo pero deja sin penalizar los modos de deformación que "
        r"se anulan en ese único punto: aparecen oscilaciones "
        r"características llamadas \emph{modos espurios} u "
        r"\emph{hourglass modes}. Por simetría con $1\times 1$, también "
        r"hay riesgo de sub-integración en Q9 con $2\times 2$. Los "
        r"órdenes recomendados $2\times 2$ (Q4) y $3\times 3$ (Q9) "
        r"evitan el problema."
    )


# ────────────────────────────────────────────────────────────────────
# M6 · Fuerzas equivalentes nodales
# ────────────────────────────────────────────────────────────────────


def _m6_equivalent_forces(doc: TheoryDoc) -> None:
    doc.section_numbered("M6 · Fuerzas equivalentes nodales")
    doc.para(
        r"Las cargas distribuidas que actúan sobre el cuerpo (tracciones "
        r"sobre aristas, peso propio) se convierten en fuerzas nodales "
        r"equivalentes aplicando el principio de los trabajos virtuales: "
        r"el trabajo virtual de las fuerzas equivalentes debe coincidir "
        r"con el de la carga real para cualquier campo de desplazamientos "
        r"virtuales admisibles."
    )

    doc.subsection_numbered("Carga distribuida sobre una arista (tracción)")
    doc.equation(
        r"\mathbf{f}_e^{(\text{arista})} = \int_{\Gamma_e} \mathbf{N}^T "
        r"\,\bar{\mathbf{t}}\,t\,ds,"
    )
    doc.para(
        r"con $\bar{\mathbf{t}}=(t_x,t_y)$ el vector tracción aplicado "
        r"sobre la arista $\Gamma_e$ y $ds$ el diferencial de longitud "
        r"física. Cambiando de variable a la coordenada natural a lo "
        r"largo de la arista, $ds=|\partial\mathbf{x}/\partial\xi|\,d\xi$, "
        r"la integral se evalúa por Gauss-Legendre 1D."
    )
    doc.para(
        r"Para una arista recta con carga constante $q$ por unidad de "
        r"longitud, la integración exacta arroja:"
    )
    doc.raw(r"\begin{itemize}")
    doc.raw(r"\item En \textbf{Q4} (2 nodos por arista, $N_i$ lineales): "
            r"la carga se reparte simétricamente "
            r"$\;f_1 = f_2 = qL/2$.")
    doc.raw(r"\item En \textbf{Q9} (3 nodos por arista, $N_i$ cuadráticas): "
            r"el reparto es $\;f_{\text{extremo}} = qL/6,\;\; "
            r"f_{\text{medio}} = 4qL/6,\;\; f_{\text{extremo}} = qL/6$. "
            r"La asimetría refleja directamente la integración de las "
            r"$N_i$ cuadráticas a lo largo del lado.")
    doc.raw(r"\end{itemize}")

    doc.subsection_numbered("Peso propio (fuerza volumétrica)")
    doc.equation(
        r"\mathbf{f}_e^{(\text{volumen})} = \int_{\Omega_e} \mathbf{N}^T "
        r"\,\rho\,\mathbf{g}\,t\,dA "
        r"= \int_{-1}^{1}\!\!\int_{-1}^{1} \mathbf{N}^T \,\rho\,\mathbf{g}\,"
        r"t\,|\det\mathbf{J}|\,d\xi\,d\eta,"
    )
    doc.para(
        r"con $\rho$ la densidad del material y $\mathbf{g}=(g_x,g_y)$ "
        r"el vector aceleración gravitatoria. La integral se evalúa con "
        r"la misma cuadratura de Gauss que se usa para $\mathbf{k}_e$."
    )


# ────────────────────────────────────────────────────────────────────
# M7 · Ensamblaje global, BCs y solución del sistema
# ────────────────────────────────────────────────────────────────────


def _m7_assembly(doc: TheoryDoc) -> None:
    doc.section_numbered("M7 · Ensamblaje global, condiciones de contorno y resolución")

    doc.subsection_numbered("De las matrices locales a las globales")
    doc.para(
        r"Cada elemento $e$ tiene asociada una \textbf{tabla de "
        r"conectividad} (también llamada \emph{location matrix} "
        r"$\mathbf{LM}_e$) que indica, para cada uno de los $2\,n_e$ GDL "
        r"locales del elemento, su índice global correspondiente. Con "
        r"esa tabla el ensamblaje suma cada $\mathbf{k}_e$ y cada "
        r"$\mathbf{f}_e$ en los lugares globales que les tocan:"
    )
    doc.equation(
        r"\mathbf{K}[\mathbf{LM}_e,\mathbf{LM}_e]\,\mathrel{+}=\,"
        r"\mathbf{k}_e, \qquad "
        r"\mathbf{F}[\mathbf{LM}_e]\,\mathrel{+}=\,\mathbf{f}_e."
    )
    doc.para(
        r"Por ser una sumatoria, el orden de los elementos no altera el "
        r"resultado final: el ensamblaje es una operación conmutativa. "
        r"$\mathbf{K}$ resulta \emph{dispersa} (la mayoría de sus entradas "
        r"son cero) porque dos GDL globales sólo interactúan si "
        r"pertenecen al menos a un elemento común. La sparsity refleja "
        r"directamente la conectividad de la malla."
    )

    doc.subsection_numbered("Propiedades de la matriz global $\\mathbf{K}$")
    doc.para(
        r"Antes de aplicar restricciones, $\mathbf{K}$ es:"
    )
    doc.raw(r"\begin{itemize}")
    doc.raw(r"\item \textbf{Simétrica}: $\mathbf{K}=\mathbf{K}^T$ por "
            r"construcción ($\mathbf{B}^T\mathbf{D}\mathbf{B}$ es simétrica "
            r"y la suma preserva la simetría).")
    doc.raw(r"\item \textbf{Semidefinida positiva}: "
            r"$\mathbf{v}^T\mathbf{K}\mathbf{v}\ge 0$ "
            r"para todo $\mathbf{v}$, con igualdad sólo para los modos de "
            r"cuerpo rígido (en 2D: dos traslaciones y una rotación, "
            r"3 modos en total). $\mathbf{K}$ es por tanto \emph{singular} "
            r"y no puede invertirse hasta aplicar restricciones.")
    doc.raw(r"\item \textbf{Dispersa y bandeada}: las entradas no nulas se "
            r"concentran cerca de la diagonal, formando una banda cuyo "
            r"ancho depende de la numeración nodal.")
    doc.raw(r"\end{itemize}")

    doc.subsection_numbered("Condiciones de contorno: eliminación de GDL prescritos")
    doc.para(
        r"Las condiciones de contorno esenciales prescriben el valor de "
        r"ciertos GDL: típicamente $u=0$ en apoyos perfectos (empotramiento, "
        r"rodillo), o $u=\bar u$ en desplazamientos impuestos. Separando "
        r"los GDL libres ($f$) de los restringidos ($r$):"
    )
    doc.equation(
        r"\begin{bmatrix} \mathbf{K}_{ff} & \mathbf{K}_{fr} \\ "
        r"\mathbf{K}_{rf} & \mathbf{K}_{rr} \end{bmatrix}"
        r"\begin{bmatrix} \mathbf{u}_f \\ \mathbf{u}_r \end{bmatrix} = "
        r"\begin{bmatrix} \mathbf{F}_f \\ \mathbf{F}_r \end{bmatrix}."
    )
    doc.para(
        r"La primera fila del sistema permite despejar las incógnitas:"
    )
    doc.equation(
        r"\mathbf{K}_{ff}\,\mathbf{u}_f = \mathbf{F}_f - "
        r"\mathbf{K}_{fr}\,\mathbf{u}_r."
    )
    doc.para(
        r"Si los apoyos son homogéneos ($\mathbf{u}_r=\mathbf{0}$) el "
        r"término $\mathbf{K}_{fr}\,\mathbf{u}_r$ se anula y el "
        r"\textbf{sistema reducido} queda simplemente "
        r"$\mathbf{K}_{ff}\,\mathbf{u}_f=\mathbf{F}_f$. Si los apoyos "
        r"prescriben un valor no nulo, ese término actúa como una "
        r"\emph{fuerza equivalente} adicional que se resta del lado "
        r"derecho (condensación estática)."
    )
    doc.para(
        r"Eliminar los GDL restringidos restaura la "
        r"\textbf{definida-positividad} de $\mathbf{K}_{ff}$: ya no "
        r"admite modos de cuerpo rígido y el sistema lineal tiene "
        r"solución única."
    )

    doc.subsection_numbered("Resolución del sistema lineal")
    doc.para(
        r"El sistema reducido se resuelve por métodos directos basados "
        r"en factorización de la matriz. Las opciones clásicas son:"
    )
    doc.raw(r"\begin{itemize}")
    doc.raw(r"\item \textbf{Factorización LU} (Doolittle / Crout): "
            r"$\mathbf{K}_{ff}=\mathbf{L}\,\mathbf{U}$ con $\mathbf{L}$ "
            r"triangular inferior y $\mathbf{U}$ triangular superior. "
            r"Una vez factorizada, se resuelven en cascada los dos "
            r"sistemas triangulares "
            r"$\mathbf{L}\,\mathbf{y}=\mathbf{F}_f$ y "
            r"$\mathbf{U}\,\mathbf{u}_f=\mathbf{y}$.")
    doc.raw(r"\item \textbf{Factorización de Cholesky}: variante "
            r"$\mathbf{K}_{ff}=\mathbf{L}\,\mathbf{L}^T$ aplicable porque "
            r"$\mathbf{K}_{ff}$ es simétrica definida positiva. Cuesta "
            r"la mitad de operaciones que LU pero requiere SPD; si la "
            r"matriz pierde definida-positividad por un error en el "
            r"modelo, falla.")
    doc.raw(r"\end{itemize}")
    doc.para(
        r"Cuando $\mathbf{K}_{ff}$ es grande y dispersa se usan variantes "
        r"\emph{sparse} de estos métodos que sólo almacenan y operan sobre "
        r"las entradas no nulas, reduciendo la memoria de $O(n^2)$ a "
        r"$O(\mathrm{nnz})$. Algoritmos de \textbf{re-numeración nodal} "
        r"(p.ej.\ Cuthill-McKee inverso) minimizan el ancho de banda y "
        r"aceleran la factorización en problemas grandes."
    )

    doc.subsection_numbered("Reacciones en los apoyos")
    doc.para(
        r"Una vez calculados los desplazamientos libres $\mathbf{u}_f$, "
        r"el vector global $\mathbf{u}$ se completa con los valores "
        r"prescritos $\mathbf{u}_r$. Las reacciones en los apoyos se "
        r"obtienen como"
    )
    doc.equation(
        r"\mathbf{R} = \mathbf{K}\,\mathbf{u} - \mathbf{F},"
    )
    doc.para(
        r"y resultan no nulas únicamente en los GDL restringidos. La "
        r"\textbf{verificación de equilibrio global} consiste en "
        r"comprobar que $\sum\mathbf{F}+\sum\mathbf{R}=\mathbf{0}$ "
        r"(en cada dirección $x$ e $y$): es un control de calidad barato "
        r"y debe satisfacerse hasta el error de redondeo."
    )


# ────────────────────────────────────────────────────────────────────
# M8 · Post-proceso: tensiones derivadas
# ────────────────────────────────────────────────────────────────────


def _m8_post_processing(doc: TheoryDoc) -> None:
    doc.section_numbered("M8 · Post-proceso: tensiones derivadas")
    doc.para(
        r"El post-proceso transforma los desplazamientos nodales "
        r"$\mathbf{u}$ — la única incógnita directa del MEF — en las "
        r"magnitudes con las que un ingeniero juzga el diseño "
        r"(tensiones principales, von Mises, contornos). La cadena de "
        r"cálculo es:"
    )
    doc.equation(
        r"\mathbf{u} \;\to\; \boldsymbol\varepsilon_{Gauss} \;\to\; "
        r"\boldsymbol\sigma_{Gauss} \;\to\; \boldsymbol\sigma_{nodo} "
        r"\;\to\; \boldsymbol\sigma_{promediado} \;\to\; "
        r"(\sigma_1, \sigma_2, \sigma_{VM})."
    )

    doc.subsection_numbered("Tensiones en los puntos de Gauss")
    doc.para(
        r"Para cada elemento se reconstruye la deformación en sus "
        r"puntos de Gauss vía"
    )
    doc.equation(
        r"\boldsymbol\varepsilon(\xi_p,\eta_p) = "
        r"\mathbf{B}(\xi_p,\eta_p)\,\mathbf{u}_e,"
    )
    doc.para(
        r"y, por la ley de Hooke, "
        r"$\boldsymbol\sigma(\xi_p,\eta_p) = \mathbf{D}\,"
        r"\boldsymbol\varepsilon(\xi_p,\eta_p)$. Se calculan allí — y "
        r"no directamente en los nodos — por la superconvergencia de "
        r"Barlow: las tensiones en los puntos de Gauss convergen con "
        r"un orden adicional respecto del resto del elemento (sección "
        r"M4)."
    )

    doc.subsection_numbered("Extrapolación de Gauss a nodos (Q4)")
    doc.para(
        r"Las tensiones obtenidas en los puntos de Gauss se llevan a los "
        r"nodos mediante una matriz de extrapolación $\mathbf{E}$ "
        r"definida como la inversa de la matriz de funciones de forma "
        r"evaluadas en los puntos de Gauss:"
    )
    doc.equation(
        r"(\mathbf{N}_p)_{ji} = N_i(\xi_p,\eta_p), \qquad "
        r"\boldsymbol\sigma^{\,nodo} = \mathbf{E}\,"
        r"\boldsymbol\sigma^{\,Gauss}, \qquad "
        r"\mathbf{E} = \mathbf{N}_p^{-1}."
    )
    doc.para(
        r"Para Q4 con cuadratura $2\times 2$, los nodos están en "
        r"$(\pm 1,\pm 1)$ y los puntos de Gauss en "
        r"$(\pm 1/\sqrt{3},\pm 1/\sqrt{3})$. La inversa se calcula "
        r"analíticamente y, con $s=\sqrt{3}$, queda:"
    )
    doc.equation(
        r"\mathbf{E}_{Q4} = \frac{1}{4}\begin{bmatrix}"
        r"(1+s)^2 & (1-s^2) & (1-s)^2 & (1-s^2) \\"
        r"(1-s^2) & (1-s)^2 & (1-s^2) & (1+s)^2 \\"
        r"(1-s)^2 & (1-s^2) & (1+s)^2 & (1-s^2) \\"
        r"(1-s^2) & (1+s)^2 & (1-s^2) & (1-s)^2"
        r"\end{bmatrix}."
    )
    doc.para(
        r"El factor $\sqrt{3}$ refleja directamente las coordenadas "
        r"naturales de los puntos de Gauss en una dimensión "
        r"($\pm 1/\sqrt{3}$): se lo llama habitualmente \emph{factor de "
        r"extrapolación}."
    )

    doc.subsection_numbered("Extrapolación de Gauss a nodos (Q9)")
    doc.para(
        r"Para Q9 con cuadratura $3\times 3$ no existe expresión cerrada "
        r"simple: la matriz $\mathbf{E}_{Q9}$ (de $9\times 9$) se "
        r"construye numéricamente evaluando las 9 funciones de forma "
        r"biquadráticas en los 9 puntos de Gauss y luego invirtiendo. "
        r"Es la misma matriz para todos los elementos Q9, independiente "
        r"de su geometría física."
    )

    doc.subsection_numbered("Promediado nodal entre elementos adyacentes")
    doc.para(
        r"Un nodo compartido por $k$ elementos recibe $k$ valores "
        r"extrapolados distintos — la formulación de Galerkin sólo "
        r"garantiza continuidad $C^0$ del desplazamiento, no de sus "
        r"derivadas. Para mostrar un campo continuo se aplica el "
        r"promedio aritmético sobre los elementos que comparten el nodo:"
    )
    doc.equation(
        r"\sigma_n^{\,promediado} = \frac{1}{k_n}\sum_{e\in\mathcal{E}_n} "
        r"\sigma_n^{\,(e)},"
    )
    doc.para(
        r"con $\mathcal{E}_n$ el conjunto de elementos que comparten el "
        r"nodo $n$ y $k_n=|\mathcal{E}_n|$."
    )
    doc.para(
        r"\textbf{El salto pre-promediado es un indicador de error de "
        r"malla}: si las $k$ contribuciones a un mismo nodo difieren "
        r"mucho entre sí, la malla es insuficiente para capturar el "
        r"gradiente local; refinarla allí debería reducir el salto. "
        r"Por eso es habitual mostrar también el campo \emph{no "
        r"promediado} junto al promediado — la diferencia es una "
        r"herramienta de diagnóstico."
    )

    doc.subsection_numbered(r"Tensiones principales $\sigma_1$, $\sigma_2$, $\theta_p$")
    doc.para(
        r"En 2D el estado tensional en un punto se describe por las "
        r"tres componentes $(\sigma_x,\sigma_y,\tau_{xy})$. Las "
        r"\textbf{tensiones principales} $\sigma_1\geq\sigma_2$ son los "
        r"autovalores del tensor de tensiones y corresponden a las "
        r"tensiones normales máxima y mínima sobre los planos donde el "
        r"corte se anula ($\tau=0$). La fórmula cerrada es:"
    )
    doc.equation(
        r"\sigma_{1,2} = \frac{\sigma_x+\sigma_y}{2} \pm "
        r"\sqrt{\left(\frac{\sigma_x-\sigma_y}{2}\right)^2 + "
        r"\tau_{xy}^{\,2}}."
    )
    doc.para(
        r"La dirección principal $\theta_p$ (ángulo del plano "
        r"perpendicular a $\sigma_1$ respecto del eje $x$) se obtiene "
        r"de:"
    )
    doc.equation(
        r"\tan(2\theta_p) = \frac{2\,\tau_{xy}}{\sigma_x-\sigma_y}."
    )
    doc.para(
        r"\textbf{Convención}: $\sigma_1>0$ indica \emph{tracción} (el "
        r"material se estira); $\sigma_2<0$ indica \emph{compresión} "
        r"(se aplasta). Las direcciones principales muestran el "
        r"\emph{flujo de carga} de la estructura."
    )

    doc.subsection_numbered(r"Tensión equivalente de von Mises")
    doc.para(
        r"El criterio de von Mises (también llamado de la energía "
        r"distorsional) convierte el estado tensional 2D en un escalar "
        r"comparable contra la tensión de fluencia uniaxial $\sigma_y$ "
        r"del material:"
    )
    doc.equation(
        r"\sigma_{VM} = \sqrt{\sigma_x^{\,2} - \sigma_x\,\sigma_y + "
        r"\sigma_y^{\,2} + 3\,\tau_{xy}^{\,2}} = "
        r"\sqrt{\sigma_1^{\,2} - \sigma_1\,\sigma_2 + \sigma_2^{\,2}}."
    )
    doc.para(
        r"El criterio dice: el material plastifica cuando "
        r"$\sigma_{VM}\geq\sigma_y$. Es la métrica más usada en diseño "
        r"de elementos dúctiles (aceros estructurales, aluminios) "
        r"porque captura la contribución del corte sin requerir "
        r"información direccional. \textbf{Atención}: para materiales "
        r"frágiles (hormigón, vidrio, cerámicas) von Mises subestima "
        r"el riesgo — usar criterios específicos para frágiles "
        r"(p.\,ej.\ Rankine, basados en $\sigma_1$ máximo)."
    )


# ────────────────────────────────────────────────────────────────────
# M9 · Convergencia h y comparación Q4 / Q9
# ────────────────────────────────────────────────────────────────────


def _m9_convergence(doc: TheoryDoc) -> None:
    doc.section_numbered("M9 · Convergencia h y comparación Q4 / Q9")
    doc.para(
        r"Refinar la malla (\emph{h-refinamiento}: subdividir cada "
        r"elemento en sub-elementos más pequeños) reduce el error de "
        r"discretización. Si la solución continua tiene suficiente "
        r"regularidad, el error en norma energética decae como:"
    )
    doc.equation(r"\|u - u_h\|_E \le C\,h^{p},")
    doc.para(
        r"con $h$ el tamaño característico del elemento y $p$ el orden "
        r"polinomial de las funciones de forma. Para los cuadriláteros "
        r"isoparamétricos:"
    )
    doc.raw(r"\begin{itemize}")
    doc.raw(r"\item \textbf{Q4} ($p=1$): el error decae linealmente con "
            r"$h$. Duplicar la cantidad de elementos por dirección "
            r"(reducir $h$ a la mitad) baja el error a la mitad.")
    doc.raw(r"\item \textbf{Q9} ($p=2$): el error decae cuadráticamente. "
            r"Reducir $h$ a la mitad baja el error a la cuarta parte.")
    doc.raw(r"\end{itemize}")
    doc.para(
        r"En la norma de las tensiones (norma $L^2$ de "
        r"$\boldsymbol\sigma-\boldsymbol\sigma_h$, un orden por debajo "
        r"de la norma energética) las pendientes son $O(h)$ para Q4 y "
        r"$O(h^2)$ para Q9. En un gráfico log-log de error vs.\ tamaño "
        r"característico, esas pendientes aparecen como rectas con "
        r"pendiente $-1$ y $-2$ respectivamente."
    )

    doc.subsection_numbered("Cuándo conviene cada uno")
    doc.para(
        r"\textbf{Q4}: geometrías simples, gradientes suaves, modelos "
        r"exploratorios. Cuesta poco por elemento (matriz $8\times 8$, "
        r"4 puntos de Gauss) pero requiere muchos elementos para "
        r"capturar bien gradientes fuertes."
    )
    doc.para(
        r"\textbf{Q9}: zonas de concentración de tensiones, contornos "
        r"curvos (las $N_i$ cuadráticas representan exactamente arcos "
        r"parabólicos en el mapeo isoparamétrico), problemas con "
        r"flexión dominante donde Q4 sufre \emph{shear locking}. "
        r"Aunque cada elemento cuesta más (matriz $18\times 18$, "
        r"9 puntos de Gauss), el orden de convergencia más alto "
        r"compensa con mallas mucho más gruesas."
    )

    doc.subsection_numbered("Shear locking en flexión: por qué Q4 falla")
    doc.para(
        r"En flexión pura, la deformación cortante "
        r"$\gamma_{xy}=\partial u_x/\partial y + \partial u_y/\partial x$ "
        r"debe anularse. Las funciones bilineales de Q4 no pueden "
        r"representar esa condición en forma exacta: aparece un corte "
        r"parásito que rigidiza artificialmente el elemento. Q9, con "
        r"bases cuadráticas, sí puede representar la cinemática de "
        r"flexión sin parasitismo. Por eso en problemas dominados por "
        r"flexión (vigas esbeltas, membranas como la de Cook) Q9 "
        r"converge mucho más rápido que Q4."
    )
