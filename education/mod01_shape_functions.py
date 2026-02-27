"""
Módulo 1: Funciones de Forma
Visualización interactiva de funciones de forma N para Q4/Q9.
"""

import numpy as np
from education.base_module import BaseEducationalModule, HAS_MATPLOTLIB
from fem.shape_functions import (
    shape_functions_q4, shape_functions_q9,
    dshape_functions_q4, dshape_functions_q9, get_shape_functions
)


class ShapeFunctionsModule(BaseEducationalModule):
    """Módulo educativo: Funciones de Forma."""

    def __init__(self, parent, project, element_id):
        super().__init__(parent, project, element_id,
                         "Funciones de Forma", width=1200, height=800)

        self.is_q4 = "4 nodos" in str(project.element_type) or "Q4" in str(project.element_type)
        self.n_nodes = 4 if self.is_q4 else 9
        self.selected_node = 0  # Nodo a visualizar

        self._build_explanation()
        self._build_visualization()

    def _build_explanation(self):
        """Panel izquierdo con teoría."""
        self.add_title("Funciones de Forma", "①")

        self.add_text(
            "Las funciones de forma Ni son las herramientas matemáticas que "
            "permiten interpolar (aproximar) el desplazamiento en cualquier "
            "punto interior del elemento a partir de valores conocidos en "
            "los nodos."
        )

        self.add_subtitle("Significado Físico")
        self.add_text(
            "Cada función Ni vale 1 en su nodo i y 0 en los demás nodos. "
            "Esto garantiza que el desplazamiento interpolado coincide "
            "exactamente con el desplazamiento nodal en cada nodo."
        )

        self.add_subtitle("Elemento Q4 (Bilineal)")
        self.add_text("Las funciones de forma del elemento de 4 nodos son:")
        self.add_formula(
            "N1 = 1/4 (1-xi)(1-eta)\n"
            "N2 = 1/4 (1+xi)(1-eta)\n"
            "N3 = 1/4 (1+xi)(1+eta)\n"
            "N4 = 1/4 (1-xi)(1+eta)"
        )

        self.add_text(
            "Donde (xi, eta) son las coordenadas naturales en [-1, 1]."
        )

        self.add_separator()
        self.add_subtitle("Propiedad de particion de la unidad")
        self.add_formula("N1 + N2 + N3 + N4 = 1  (en todo punto)")
        self.add_text(
            "Esta propiedad garantiza que un campo constante se "
            "representa exactamente. Es necesaria para convergencia."
        )

        self.add_separator()
        self.add_subtitle("Valores en su elemento actual")

        # Evaluar en el centro
        N_func, _ = get_shape_functions(project.element_type)
        N_center = N_func(0.0, 0.0)

        self.add_text(f"Elemento {element_id}: Nodos {self.element.node_ids}")
        self.add_text(f"Valores de N en el centro (xi=0, eta=0):")
        for i, val in enumerate(N_center):
            nid = self.element.node_ids[i]
            self.add_value(f"  N{i+1} (nodo {nid})", val, ".4f")

        self.add_value("  Suma", sum(N_center), ".4f")

    def _build_visualization(self):
        """Panel derecho con gráficas 3D de N."""
        if not HAS_MATPLOTLIB:
            return

        fig, self.canvas = self.create_figure(figsize=(7, 6))

        # Grilla de puntos en coordenadas naturales
        xi_range = np.linspace(-1, 1, 30)
        eta_range = np.linspace(-1, 1, 30)
        XI, ETA = np.meshgrid(xi_range, eta_range)

        N_func, _ = get_shape_functions(self.project.element_type)

        # Crear 2x2 subplots para las 4 funciones de forma principales
        axes = []
        for i in range(4):
            ax = fig.add_subplot(2, 2, i + 1, projection='3d')
            self.style_axis(ax)
            axes.append(ax)

            # Evaluar Ni en toda la grilla
            N_vals = np.zeros_like(XI)
            for r in range(XI.shape[0]):
                for c in range(XI.shape[1]):
                    N_all = N_func(XI[r, c], ETA[r, c])
                    N_vals[r, c] = N_all[i]

            # Superficie 3D
            ax.plot_surface(
                XI, ETA, N_vals,
                cmap='viridis', alpha=0.8, edgecolor='none',
            )

            nid = self.element.node_ids[i] if self.element else i + 1
            ax.set_title(f"N{i+1} (Nodo {nid})", color="white", fontsize=10)
            ax.set_xlabel("xi", color="#aaa", fontsize=8)
            ax.set_ylabel("eta", color="#aaa", fontsize=8)
            ax.set_zlabel(f"N{i+1}", color="#aaa", fontsize=8)
            ax.set_zlim(0, 1.1)
            ax.tick_params(labelsize=6, colors='#aaa')
            ax.xaxis.pane.fill = False
            ax.yaxis.pane.fill = False
            ax.zaxis.pane.fill = False

        fig.suptitle(
            "Funciones de Forma en Coordenadas Naturales",
            color="white", fontsize=12, fontweight="bold"
        )
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        self.canvas.draw()
