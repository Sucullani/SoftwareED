"""
Módulo 6: Integración de Gauss
Puntos, pesos y la técnica de cuadratura numérica.
"""

import numpy as np
from education.base_module import BaseEducationalModule, HAS_MATPLOTLIB
from fem.gauss_quadrature import GAUSS_POINTS_1D, get_gauss_points_2d


class GaussIntegrationModule(BaseEducationalModule):
    """Módulo educativo: Integración de Gauss."""

    def __init__(self, parent, project, element_id):
        super().__init__(parent, project, element_id,
                         "Integracion de Gauss", width=1100, height=750)

        self._build_explanation()
        self._build_visualization()

    def _build_explanation(self):
        self.add_title("Integracion de Gauss", "⑥")

        self.add_text(
            "La cuadratura de Gauss permite evaluar integrales definidas "
            "de forma exacta para polinomios de hasta grado 2n-1, "
            "usando solo n puntos de evaluacion.\n\n"
            "Es el metodo estandar para integrar matrices de rigidez "
            "y vectores de carga en FEM."
        )

        self.add_subtitle("Idea clave")
        self.add_formula(
            "integral_(-1)^(1) f(x) dx  ~=  SUM_i  wi * f(xi)\n\n"
            "Donde xi = puntos de Gauss\n"
            "      wi = pesos de Gauss"
        )

        self.add_separator()
        self.add_subtitle("Puntos 1D")

        for n in [1, 2, 3]:
            gp = GAUSS_POINTS_1D[n]
            self.add_text(f"\n{n} punto(s) (exacto para grado {2*n-1}):")
            for i, (pt, w) in enumerate(zip(gp["points"], gp["weights"])):
                self.add_formula(f"  xi_{i+1} = {pt:+.6f},  w_{i+1} = {w:.6f}")

        self.add_separator()
        self.add_subtitle("Extension a 2D (producto tensorial)")
        self.add_formula(
            "integral integral f(xi,eta) d(xi) d(eta)\n"
            "  ~= SUM_i SUM_j  wi * wj * f(xi_i, eta_j)"
        )

        self.add_text(
            "Para Q4: 2x2 = 4 puntos de Gauss\n"
            "Para Q9: 3x3 = 9 puntos de Gauss"
        )

        # Puntos 2D para Q4
        pts2d, wts2d = get_gauss_points_2d(2)
        self.add_subtitle("Puntos 2D (2x2 para Q4)")
        for i, (pt, w) in enumerate(zip(pts2d, wts2d)):
            self.add_formula(
                f"  PG{i+1}: (xi={pt[0]:+.6f}, eta={pt[1]:+.6f}), w={w:.6f}"
            )

    def _build_visualization(self):
        if not HAS_MATPLOTLIB:
            return

        fig, self.canvas = self.create_figure(figsize=(7, 6))

        # Subplot 1: Puntos 1D
        ax1 = fig.add_subplot(2, 2, 1)
        self.style_axis(ax1, "Gauss 1D: 1 punto")
        gp1 = GAUSS_POINTS_1D[1]
        ax1.plot([-1, 1], [0, 0], '-', color='#555', lw=2)
        ax1.plot(gp1["points"], [0]*len(gp1["points"]), 'o', color='#ef5350', ms=12)
        ax1.set_xlim(-1.5, 1.5)
        ax1.set_ylim(-0.5, 0.5)

        ax2 = fig.add_subplot(2, 2, 2)
        self.style_axis(ax2, "Gauss 1D: 2 puntos")
        gp2 = GAUSS_POINTS_1D[2]
        ax2.plot([-1, 1], [0, 0], '-', color='#555', lw=2)
        ax2.plot(gp2["points"], [0]*len(gp2["points"]), 'o', color='#4fc3f7', ms=12)
        ax2.set_xlim(-1.5, 1.5)
        ax2.set_ylim(-0.5, 0.5)

        # Subplot 3: Puntos 2D (2x2)
        ax3 = fig.add_subplot(2, 2, 3)
        self.style_axis(ax3, "Gauss 2D: 2x2 (Q4)")
        pattern = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]])
        ax3.plot(pattern[:, 0], pattern[:, 1], '-', color='#555', lw=2)
        pts2d_2, wts2d_2 = get_gauss_points_2d(2)
        ax3.scatter(pts2d_2[:, 0], pts2d_2[:, 1],
                    s=wts2d_2 * 200, c='#4fc3f7', zorder=5, edgecolors='white')
        for i, (pt, w) in enumerate(zip(pts2d_2, wts2d_2)):
            ax3.annotate(f"PG{i+1}\nw={w:.2f}", xy=(pt[0], pt[1]),
                         fontsize=7, color='white', ha='center', va='top',
                         textcoords="offset points", xytext=(0, -15))
        ax3.set_xlim(-1.5, 1.5)
        ax3.set_ylim(-1.5, 1.5)
        ax3.set_aspect('equal')

        # Subplot 4: Puntos 2D (3x3)
        ax4 = fig.add_subplot(2, 2, 4)
        self.style_axis(ax4, "Gauss 2D: 3x3 (Q9)")
        ax4.plot(pattern[:, 0], pattern[:, 1], '-', color='#555', lw=2)
        pts2d_3, wts2d_3 = get_gauss_points_2d(3)
        ax4.scatter(pts2d_3[:, 0], pts2d_3[:, 1],
                    s=wts2d_3 * 200, c='#81c784', zorder=5, edgecolors='white')
        for i, (pt, w) in enumerate(zip(pts2d_3, wts2d_3)):
            ax4.annotate(f"{i+1}", xy=(pt[0], pt[1]),
                         fontsize=7, color='white', ha='center', va='top',
                         textcoords="offset points", xytext=(0, -12))
        ax4.set_xlim(-1.5, 1.5)
        ax4.set_ylim(-1.5, 1.5)
        ax4.set_aspect('equal')

        fig.tight_layout()
        self.canvas.draw()
