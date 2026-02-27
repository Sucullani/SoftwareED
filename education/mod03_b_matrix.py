"""
Módulo 3: Matriz B (Deformación-Desplazamiento)
Relación entre desplazamientos nodales y deformaciones: epsilon = B * u
"""

import numpy as np
from education.base_module import BaseEducationalModule, HAS_MATPLOTLIB
from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian, compute_dN_physical
from fem.b_matrix import compute_b_matrix
from fem.gauss_quadrature import get_gauss_points_for_element


class BMatrixModule(BaseEducationalModule):
    """Módulo educativo: Matriz B."""

    def __init__(self, parent, project, element_id):
        super().__init__(parent, project, element_id,
                         "Matriz B (Deformacion-Desplazamiento)", width=1200, height=800)

        self._build_explanation()
        self._build_visualization()

    def _build_explanation(self):
        self.add_title("Matriz B", "③")

        self.add_text(
            "La matriz B es el operador que transforma desplazamientos "
            "nodales en deformaciones internas del elemento.\n\n"
            "Es el corazón de la formulación por elementos finitos "
            "para problemas de elasticidad."
        )

        self.add_subtitle("Relacion fundamental")
        self.add_formula(
            "epsilon = B * u_e\n\n"
            "| epsilon_x  |       | dN1/dx   0     dN2/dx   0   ...|\n"
            "| epsilon_y  |  = B  | 0     dN1/dy    0    dN2/dy ...| * u_e\n"
            "| gamma_xy   |       | dN1/dy dN1/dx  dN2/dy dN2/dx..|"
        )

        self.add_text(
            "Donde:\n"
            "  epsilon_x = du/dx  (deformacion normal en x)\n"
            "  epsilon_y = dv/dy  (deformacion normal en y)\n"
            "  gamma_xy = du/dy + dv/dx  (deformacion cortante)"
        )

        self.add_subtitle("Construccion de B")
        self.add_text(
            "B se construye con las derivadas de N en coordenadas FISICAS:\n\n"
            "  1. Calcular dN/d(xi), dN/d(eta) (derivadas naturales)\n"
            "  2. Calcular J (Jacobiano)\n"
            "  3. dN/dx, dN/dy = J^(-1) * [dN/d(xi); dN/d(eta)]\n"
            "  4. Ensamblar B con las derivadas fisicas"
        )

        self.add_separator()
        self.add_subtitle("Calculo para su elemento")

        _, dN_func = get_shape_functions(self.project.element_type)
        gauss_pts, _ = get_gauss_points_for_element(self.project.element_type)

        # Mostrar B en el primer punto de Gauss
        gp = gauss_pts[0]
        xi, eta = gp[0], gp[1]

        dN_nat = dN_func(xi, eta)
        J, det_J, inv_J = compute_jacobian(dN_nat, self.node_coords)
        dN_phys = compute_dN_physical(dN_nat, inv_J)
        B = compute_b_matrix(dN_phys)

        self.add_text(f"Punto de Gauss 1: (xi={xi:.4f}, eta={eta:.4f})")
        self.add_text("\nDerivadas en coordenadas naturales dN/d(xi,eta):")
        self.add_matrix_display(dN_nat, "dN_nat", ".6f")

        self.add_text("\nDerivadas en coordenadas fisicas dN/d(x,y):")
        self.add_matrix_display(dN_phys, "dN_phys", ".6f")

        self.add_text(f"\nMatriz B ({B.shape[0]}x{B.shape[1]}):")
        self.add_matrix_display(B, "B", ".6f")

    def _build_visualization(self):
        """Visualización de la estructura de B."""
        if not HAS_MATPLOTLIB:
            return

        fig, self.canvas = self.create_figure(figsize=(7, 6))

        _, dN_func = get_shape_functions(self.project.element_type)
        gauss_pts, _ = get_gauss_points_for_element(self.project.element_type)

        # Heatmap de la matriz B en el primer punto de Gauss
        ax1 = fig.add_subplot(2, 1, 1)
        self.style_axis(ax1, "Estructura de la Matriz B (Punto Gauss 1)")

        gp = gauss_pts[0]
        dN_nat = dN_func(gp[0], gp[1])
        J, det_J, inv_J = compute_jacobian(dN_nat, self.node_coords)
        dN_phys = compute_dN_physical(dN_nat, inv_J)
        B = compute_b_matrix(dN_phys)

        im = ax1.imshow(np.abs(B), cmap='YlOrRd', aspect='auto')
        ax1.set_ylabel("Componente\n(ex, ey, gxy)", color='white')
        ax1.set_yticks([0, 1, 2])
        ax1.set_yticklabels(["ex", "ey", "gxy"])

        n_nodes = B.shape[1] // 2
        x_labels = []
        for i in range(n_nodes):
            x_labels.extend([f"u{i+1}", f"v{i+1}"])
        ax1.set_xticks(range(B.shape[1]))
        ax1.set_xticklabels(x_labels, fontsize=7, rotation=45)
        fig.colorbar(im, ax=ax1, shrink=0.6)

        # Comparación de det(J) en todos los puntos de Gauss
        ax2 = fig.add_subplot(2, 1, 2)
        self.style_axis(ax2, "Determinante del Jacobiano en cada Pt. Gauss")

        det_values = []
        labels = []
        for i, gp in enumerate(gauss_pts):
            dN_nat = dN_func(gp[0], gp[1])
            _, det_J, _ = compute_jacobian(dN_nat, self.node_coords)
            det_values.append(det_J)
            labels.append(f"PG{i+1}\n({gp[0]:.2f},{gp[1]:.2f})")

        colors = ['#4fc3f7' if d > 0 else '#ef5350' for d in det_values]
        ax2.bar(range(len(det_values)), det_values, color=colors, alpha=0.8)
        ax2.set_xticks(range(len(labels)))
        ax2.set_xticklabels(labels, fontsize=7)
        ax2.set_ylabel("det(J)", color='white')
        ax2.axhline(y=0, color='#ff5252', ls='--', alpha=0.5)
        ax2.grid(True, alpha=0.2)

        fig.tight_layout()
        self.canvas.draw()
