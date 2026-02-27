"""
Módulo 8: Ensamblaje Global
Formación de la matriz de rigidez global K ensamblando ke de cada elemento.
"""

import numpy as np
from education.base_module import BaseEducationalModule, HAS_MATPLOTLIB
from fem.assembly import assemble_global_system


class AssemblyModule(BaseEducationalModule):
    """Módulo educativo: Ensamblaje Global."""

    def __init__(self, parent, project, element_id):
        super().__init__(parent, project, element_id,
                         "Ensamblaje Global", width=1200, height=800)

        self._build_explanation()
        self._build_visualization()

    def _build_explanation(self):
        self.add_title("Ensamblaje Global K", "⑧")

        self.add_text(
            "La matriz de rigidez global K se forma ensamblando "
            "las matrices de rigidez de cada elemento ke en sus "
            "posiciones correspondientes segun la numeracion de "
            "grados de libertad (GDL)."
        )

        self.add_subtitle("Proceso de ensamblaje")
        self.add_formula(
            "Para cada elemento e:\n"
            "  Para i = 1..n_dof_elem:\n"
            "    Para j = 1..n_dof_elem:\n"
            "      K[gdl_global[i], gdl_global[j]] += ke[i,j]"
        )

        self.add_text(
            "Los indices globales se obtienen de la conectividad:\n"
            "  Nodo k -> GDL 2*(k-1) (horizontal) y 2*(k-1)+1 (vertical)"
        )

        self.add_separator()
        self.add_subtitle("Mapa de GDL del modelo")

        for elem_id, elem in sorted(self.project.elements.items()):
            dofs = elem.get_dof_indices()
            self.add_text(
                f"  Elem {elem_id}: Nodos {elem.node_ids} -> GDL {dofs}"
            )

        self.add_separator()
        # Ensamblar
        K, F, elem_data = assemble_global_system(self.project)

        self.add_subtitle("Matriz K global")
        self.add_value("Dimension", f"{K.shape[0]}x{K.shape[1]}")
        self.add_value("No-ceros", int(np.count_nonzero(K)))

        total = K.shape[0] * K.shape[1]
        density = np.count_nonzero(K) / total * 100
        self.add_value("Densidad", f"{density:.1f}%")

        sym_err = np.max(np.abs(K - K.T))
        self.add_value("Simetria (max error)", sym_err, ".2e")

    def _build_visualization(self):
        if not HAS_MATPLOTLIB:
            return

        fig, self.canvas = self.create_figure(figsize=(7, 6))
        K, F, _ = assemble_global_system(self.project)

        # Patrón de dispersión (sparsity)
        ax1 = fig.add_subplot(1, 2, 1)
        self.style_axis(ax1, "Patron de K (no-ceros)")
        ax1.spy(np.abs(K) > 1e-10, markersize=3, color='#4fc3f7')
        ax1.set_xlabel("GDL", color='white')
        ax1.set_ylabel("GDL", color='white')

        # Heatmap de |K|
        ax2 = fig.add_subplot(1, 2, 2)
        self.style_axis(ax2, "|K| - Magnitud")
        K_log = np.log10(np.abs(K) + 1)
        im = ax2.imshow(K_log, cmap='inferno', aspect='equal')
        fig.colorbar(im, ax=ax2, shrink=0.7, label="log10(|K|+1)")

        fig.suptitle(
            f"Matriz de Rigidez Global ({K.shape[0]}x{K.shape[1]})",
            color="white", fontsize=11, fontweight="bold"
        )
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        self.canvas.draw()
