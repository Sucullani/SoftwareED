"""
Módulo 5: Matriz de Rigidez del Elemento ke
Integración: ke = integral B^T * D * B * |detJ| * t
"""

import numpy as np
from education.base_module import BaseEducationalModule, HAS_MATPLOTLIB
from fem.stiffness import element_stiffness


class StiffnessModule(BaseEducationalModule):
    """Módulo educativo: Matriz de Rigidez del Elemento."""

    def __init__(self, parent, project, element_id):
        super().__init__(parent, project, element_id,
                         "Matriz de Rigidez ke", width=1200, height=800)

        self._build_explanation()
        self._build_visualization()

    def _build_explanation(self):
        material = list(self.project.materials.values())[0]

        self.add_title("Matriz de Rigidez ke", "⑤")

        self.add_text(
            "La matriz de rigidez del elemento ke relaciona las fuerzas "
            "nodales con los desplazamientos: f = ke * u\n\n"
            "Se calcula como la integral de B^T * D * B sobre el "
            "dominio del elemento, usando cuadratura de Gauss."
        )

        self.add_subtitle("Formula")
        self.add_formula(
            "ke = integral_(-1)^(1) integral_(-1)^(1)\n"
            "     B^T * D * B * |det(J)| * t  d(xi) d(eta)\n\n"
            "   = SUM_i SUM_j  wi * wj * B^T * D * B * |det(J)| * t"
        )

        self.add_text(
            "Donde:\n"
            "  B = Matriz deformacion-desplazamiento\n"
            "  D = Matriz constitutiva\n"
            "  J = Jacobiano\n"
            "  t = Espesor del elemento\n"
            "  wi,wj = Pesos de Gauss"
        )

        self.add_separator()
        self.add_subtitle("Calculo para su elemento")
        self.add_value("Elemento", self.element_id)
        self.add_value("E", material.E, ".1f")
        self.add_value("v", material.nu, ".4f")
        self.add_value("Espesor t", self.element.thickness, ".4f")

        # Calcular
        ke, gauss_data = element_stiffness(
            self.node_coords, material.E, material.nu,
            self.element.thickness, self.project.analysis_type,
            self.project.element_type
        )

        self.add_separator()
        self.add_subtitle("Contribucion de cada punto de Gauss")
        for gd in gauss_data:
            self.add_text(
                f"PG{gd['index']+1}: (xi={gd['xi']:.4f}, eta={gd['eta']:.4f}), "
                f"w={gd['weight']:.4f}, det(J)={gd['det_J']:.4f}"
            )

        self.add_separator()
        n = ke.shape[0]
        self.add_text(f"Matriz ke ({n}x{n}):")
        self.add_matrix_display(ke, "ke", ".2f")

        # Verificar simetría
        sym_error = np.max(np.abs(ke - ke.T))
        self.add_value("Error de simetria", sym_error, ".2e")
        self.add_text("ke es simetrica: " + ("Si" if sym_error < 1e-10 else "No"))

    def _build_visualization(self):
        if not HAS_MATPLOTLIB:
            return

        fig, self.canvas = self.create_figure(figsize=(7, 6))
        material = list(self.project.materials.values())[0]

        ke, gauss_data = element_stiffness(
            self.node_coords, material.E, material.nu,
            self.element.thickness, self.project.analysis_type,
            self.project.element_type
        )

        # Heatmap de ke
        ax = fig.add_subplot(1, 1, 1)
        self.style_axis(ax, f"Matriz de Rigidez ke - Elemento {self.element_id}")

        im = ax.imshow(np.abs(ke), cmap='inferno', aspect='equal')
        fig.colorbar(im, ax=ax, shrink=0.8, label="Magnitud")

        n_nodes = len(self.element.node_ids)
        labels = []
        for i in range(n_nodes):
            nid = self.element.node_ids[i]
            labels.extend([f"u{nid}", f"v{nid}"])
        ax.set_xticks(range(ke.shape[0]))
        ax.set_xticklabels(labels, fontsize=7, rotation=45)
        ax.set_yticks(range(ke.shape[0]))
        ax.set_yticklabels(labels, fontsize=7)

        fig.tight_layout()
        self.canvas.draw()
