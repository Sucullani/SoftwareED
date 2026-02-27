"""
Módulo 2: Jacobiano y Coordenadas Naturales
Transformación geométrica del elemento físico al patrón.
"""

import numpy as np
from education.base_module import BaseEducationalModule, HAS_MATPLOTLIB
from fem.shape_functions import (
    shape_functions_q4, dshape_functions_q4, get_shape_functions
)
from fem.jacobian import compute_jacobian
from fem.gauss_quadrature import get_gauss_points_for_element


class JacobianModule(BaseEducationalModule):
    """Módulo educativo: Jacobiano y Coordenadas Naturales."""

    def __init__(self, parent, project, element_id):
        super().__init__(parent, project, element_id,
                         "Jacobiano y Coordenadas Naturales", width=1200, height=800)

        self._build_explanation()
        self._build_visualization()

    def _build_explanation(self):
        """Panel izquierdo con teoría y cálculos."""
        self.add_title("Jacobiano y Coord. Naturales", "②")

        self.add_text(
            "¿Por qué cambiar de coordenadas?\n\n"
            "En la formulación isoparamétrica, la integración se realiza "
            "en el dominio natural (xi, eta) del elemento patrón cuadrado "
            "[-1,1] x [-1,1]. El Jacobiano establece la relación entre "
            "el elemento físico (real) y el elemento patrón."
        )

        self.add_subtitle("Mapeo Isoparamétrico")
        self.add_formula(
            "x(xi,eta) = SUM Ni(xi,eta) * xi\n"
            "y(xi,eta) = SUM Ni(xi,eta) * yi"
        )
        self.add_text(
            "Las mismas funciones de forma que interpolan desplazamientos "
            "también interpolan la geometría. Por eso se llama 'isoparamétrico'."
        )

        self.add_subtitle("Matriz Jacobiana J")
        self.add_formula(
            "J = | dx/d(xi)   dy/d(xi)  |\n"
            "    | dx/d(eta)  dy/d(eta) |"
        )

        self.add_text(
            "El Jacobiano transforma las derivadas de coordenadas naturales "
            "a coordenadas físicas:\n\n"
            "  d/dx = J^(-1) * d/d(xi)"
        )

        self.add_separator()
        self.add_subtitle("Cálculo para su elemento")

        _, dN_func = get_shape_functions(self.project.element_type)
        gauss_pts, _ = get_gauss_points_for_element(self.project.element_type)

        self.add_text(f"Elemento {self.element_id}, nodos: {self.element.node_ids}")
        self.add_text(f"Coordenadas de los nodos:")
        for i, nid in enumerate(self.element.node_ids):
            n = self.project.nodes[nid]
            self.add_text(f"  Nodo {nid}: ({n.x}, {n.y})")

        # Evaluar en cada punto de Gauss
        for gp_idx, gp in enumerate(gauss_pts):
            xi, eta = gp[0], gp[1]
            dN_nat = dN_func(xi, eta)
            J, det_J, inv_J = compute_jacobian(dN_nat, self.node_coords)

            self.add_separator()
            self.add_subtitle(f"Punto de Gauss {gp_idx + 1}: (xi={xi:.4f}, eta={eta:.4f})")
            self.add_matrix_display(J, "J", ".4f")
            self.add_value("det(J)", det_J)
            self.add_matrix_display(inv_J, "J^(-1)", ".6f")

    def _build_visualization(self):
        """Gráfica mostrando el elemento físico y el patrón."""
        if not HAS_MATPLOTLIB:
            return

        fig, self.canvas = self.create_figure(figsize=(7, 6))

        # Subplot 1: Elemento físico
        ax1 = fig.add_subplot(1, 2, 1)
        self.style_axis(ax1, "Elemento Fisico (x, y)")

        coords = self.node_coords
        n = min(len(coords), 4)
        polygon = np.vstack([coords[:n], coords[0]])  # cerrar polígono
        ax1.fill(polygon[:, 0], polygon[:, 1], alpha=0.2, color='#4fc3f7')
        ax1.plot(polygon[:, 0], polygon[:, 1], 'o-', color='#4fc3f7', lw=2, ms=8)

        # Etiquetas de nodos
        for i, nid in enumerate(self.element.node_ids[:n]):
            ax1.annotate(
                f"N{nid}\n({coords[i, 0]}, {coords[i, 1]})",
                xy=(coords[i, 0], coords[i, 1]),
                fontsize=8, color='white', ha='center', va='bottom',
                textcoords="offset points", xytext=(0, 10),
            )

        # Puntos de Gauss en coordenadas físicas
        N_func, _ = get_shape_functions(self.project.element_type)
        gauss_pts, _ = get_gauss_points_for_element(self.project.element_type)

        for gp in gauss_pts:
            xi, eta = gp[0], gp[1]
            N = N_func(xi, eta)
            x_phys = N @ coords[:n, 0]
            y_phys = N @ coords[:n, 1]
            ax1.plot(x_phys, y_phys, 'x', color='#ef5350', ms=10, mew=2)

        ax1.set_xlabel("x")
        ax1.set_ylabel("y")
        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.2)

        # Subplot 2: Elemento patrón
        ax2 = fig.add_subplot(1, 2, 2)
        self.style_axis(ax2, "Elemento Patron (xi, eta)")

        pattern = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]])
        ax2.fill(pattern[:, 0], pattern[:, 1], alpha=0.2, color='#81c784')
        ax2.plot(pattern[:, 0], pattern[:, 1], 'o-', color='#81c784', lw=2, ms=8)

        # Etiquetas de nodos del patrón
        labels_pos = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        for i, (xi, eta) in enumerate(labels_pos):
            nid = self.element.node_ids[i] if i < n else i + 1
            ax2.annotate(
                f"N{nid}\n({xi}, {eta})",
                xy=(xi, eta), fontsize=8, color='white', ha='center',
                textcoords="offset points", xytext=(0, 12),
            )

        # Puntos de Gauss en patrón
        for gp in gauss_pts:
            ax2.plot(gp[0], gp[1], 'x', color='#ef5350', ms=10, mew=2)

        ax2.set_xlabel("xi")
        ax2.set_ylabel("eta")
        ax2.set_aspect('equal')
        ax2.set_xlim(-1.5, 1.5)
        ax2.set_ylim(-1.5, 1.5)
        ax2.grid(True, alpha=0.2)

        # Flecha de transformación
        fig.text(0.5, 0.02, "J transforma d(xi,eta) -> d(x,y)",
                 ha='center', color='#ffa726', fontsize=11, fontweight='bold')

        fig.tight_layout(rect=[0, 0.05, 1, 1])
        self.canvas.draw()
