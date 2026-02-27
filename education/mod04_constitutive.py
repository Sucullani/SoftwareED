"""
Módulo 4: Ley Constitutiva (Matriz D)
Relación esfuerzo-deformación según el tipo de análisis.
"""

import numpy as np
from education.base_module import BaseEducationalModule, HAS_MATPLOTLIB
from fem.constitutive import constitutive_matrix
from config.settings import ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN


class ConstitutiveModule(BaseEducationalModule):
    """Módulo educativo: Ley Constitutiva (Matriz D)."""

    def __init__(self, parent, project, element_id):
        super().__init__(parent, project, element_id,
                         "Ley Constitutiva (Matriz D)", width=1100, height=750)

        self._build_explanation()
        self._build_visualization()

    def _build_explanation(self):
        material = list(self.project.materials.values())[0]
        E = material.E
        nu = material.nu

        self.add_title("Ley Constitutiva", "④")

        self.add_text(
            "La ley constitutiva establece la relacion entre esfuerzos "
            "y deformaciones del material. Para materiales lineales "
            "elasticos isotropicos, esta relacion es la Ley de Hooke "
            "generalizada."
        )

        self.add_formula("sigma = D * epsilon")

        self.add_text(
            "Donde D depende del tipo de analisis:\n"
            "  - Tension Plana: sigma_z = 0 (placas delgadas)\n"
            "  - Deformacion Plana: epsilon_z = 0 (represas, tuneles)"
        )

        self.add_separator()
        self.add_subtitle("Tension Plana (sigma_z = 0)")
        self.add_formula(
            "D = E/(1-v^2) * | 1    v      0      |\n"
            "                 | v    1      0      |\n"
            "                 | 0    0   (1-v)/2   |"
        )

        D_stress = constitutive_matrix(E, nu, ANALYSIS_PLANE_STRESS)
        self.add_matrix_display(D_stress, "D (Tension Plana)", ".2f")

        self.add_separator()
        self.add_subtitle("Deformacion Plana (epsilon_z = 0)")
        self.add_formula(
            "D = E/((1+v)(1-2v)) * | 1-v    v        0      |\n"
            "                       |  v    1-v       0      |\n"
            "                       |  0     0    (1-2v)/2   |"
        )

        D_strain = constitutive_matrix(E, nu, ANALYSIS_PLANE_STRAIN)
        self.add_matrix_display(D_strain, "D (Deformacion Plana)", ".2f")

        self.add_separator()
        self.add_subtitle("Su modelo actual")
        self.add_value("E (Modulo de Young)", E, ".1f")
        self.add_value("v (Poisson)", nu, ".4f")
        self.add_value("Tipo de analisis", self.project.analysis_type)

        D_current = constitutive_matrix(E, nu, self.project.analysis_type)
        self.add_matrix_display(D_current, "D (actual)", ".4f")

    def _build_visualization(self):
        if not HAS_MATPLOTLIB:
            return

        fig, self.canvas = self.create_figure(figsize=(7, 6))
        material = list(self.project.materials.values())[0]
        E = material.E
        nu = material.nu

        # Comparación visual de ambas matrices D
        ax1 = fig.add_subplot(1, 2, 1)
        self.style_axis(ax1, "D - Tension Plana")
        D_stress = constitutive_matrix(E, nu, ANALYSIS_PLANE_STRESS)
        im1 = ax1.imshow(D_stress, cmap='YlOrRd', aspect='equal')
        for i in range(3):
            for j in range(3):
                ax1.text(j, i, f"{D_stress[i, j]:.0f}",
                         ha='center', va='center', color='white', fontsize=9)
        ax1.set_xticks([0, 1, 2])
        ax1.set_xticklabels(["ex", "ey", "gxy"])
        ax1.set_yticks([0, 1, 2])
        ax1.set_yticklabels(["sx", "sy", "txy"])
        fig.colorbar(im1, ax=ax1, shrink=0.6)

        ax2 = fig.add_subplot(1, 2, 2)
        self.style_axis(ax2, "D - Deformacion Plana")
        D_strain = constitutive_matrix(E, nu, ANALYSIS_PLANE_STRAIN)
        im2 = ax2.imshow(D_strain, cmap='YlOrRd', aspect='equal')
        for i in range(3):
            for j in range(3):
                ax2.text(j, i, f"{D_strain[i, j]:.0f}",
                         ha='center', va='center', color='white', fontsize=9)
        ax2.set_xticks([0, 1, 2])
        ax2.set_xticklabels(["ex", "ey", "gxy"])
        ax2.set_yticks([0, 1, 2])
        ax2.set_yticklabels(["sx", "sy", "txy"])
        fig.colorbar(im2, ax=ax2, shrink=0.6)

        fig.suptitle(
            f"Comparacion de Matrices D\n(E={E:.0f}, v={nu:.2f})",
            color="white", fontsize=11, fontweight="bold"
        )
        fig.tight_layout(rect=[0, 0, 1, 0.92])
        self.canvas.draw()
