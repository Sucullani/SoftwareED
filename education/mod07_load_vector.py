"""
Módulo 7: Vector de Cargas Equivalentes
Cargas nodales y cargas distribuidas equivalentes.
"""

import numpy as np
from education.base_module import BaseEducationalModule, HAS_MATPLOTLIB


class LoadVectorModule(BaseEducationalModule):
    """Módulo educativo: Vector de Cargas."""

    def __init__(self, parent, project, element_id):
        super().__init__(parent, project, element_id,
                         "Vector de Cargas", width=1100, height=750)

        self._build_explanation()
        self._build_visualization()

    def _build_explanation(self):
        self.add_title("Vector de Cargas", "⑦")

        self.add_text(
            "El vector de fuerzas F contiene todas las fuerzas externas "
            "aplicadas al modelo. En FEM, las cargas pueden ser:\n\n"
            "  1. Cargas nodales concentradas (directas)\n"
            "  2. Cargas distribuidas (convertidas a equivalentes nodales)\n"
            "  3. Fuerzas de cuerpo (gravedad, etc.)"
        )

        self.add_subtitle("Cargas nodales")
        self.add_text(
            "Las cargas puntuales se colocan directamente en la posicion "
            "del GDL correspondiente en el vector F."
        )
        self.add_formula(
            "F[2*i]   += Fx del nodo i+1\n"
            "F[2*i+1] += Fy del nodo i+1"
        )

        self.add_separator()
        self.add_subtitle("Vector F de su modelo")

        n_dof = self.project.total_dof
        F = np.zeros(n_dof)
        for load in self.project.nodal_loads.values():
            dof_x = 2 * (load.node_id - 1)
            dof_y = 2 * (load.node_id - 1) + 1
            F[dof_x] += load.fx
            F[dof_y] += load.fy

        self.add_text(f"Dimension del vector F: {n_dof}")
        self.add_text(f"Cargas nodales definidas: {len(self.project.nodal_loads)}")

        for load in self.project.nodal_loads.values():
            n = self.project.nodes[load.node_id]
            self.add_text(
                f"  Nodo {load.node_id} ({n.x}, {n.y}): "
                f"Fx = {load.fx:.2f}, Fy = {load.fy:.2f}"
            )

        self.add_separator()
        self.add_text("Vector F completo (componentes no nulas):")
        for i in range(n_dof):
            if abs(F[i]) > 1e-10:
                node_id = i // 2 + 1
                comp = "Fx" if i % 2 == 0 else "Fy"
                self.add_formula(f"  F[{i}] = {F[i]:10.2f}  (Nodo {node_id}, {comp})")

    def _build_visualization(self):
        if not HAS_MATPLOTLIB:
            return

        fig, self.canvas = self.create_figure(figsize=(7, 6))

        n_dof = self.project.total_dof
        F = np.zeros(n_dof)
        for load in self.project.nodal_loads.values():
            dof_x = 2 * (load.node_id - 1)
            dof_y = 2 * (load.node_id - 1) + 1
            F[dof_x] += load.fx
            F[dof_y] += load.fy

        # Gráfica de barras del vector F
        ax = fig.add_subplot(1, 1, 1)
        self.style_axis(ax, "Vector de Fuerzas Global F")

        colors = ['#4fc3f7' if f >= 0 else '#ef5350' for f in F]
        ax.barh(range(n_dof), F, color=colors, alpha=0.8)
        ax.set_yticks(range(n_dof))

        labels = []
        for i in range(n_dof):
            nid = i // 2 + 1
            comp = "Fx" if i % 2 == 0 else "Fy"
            labels.append(f"GDL {i} (N{nid} {comp})")
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlabel("Fuerza", color='white')
        ax.axvline(x=0, color='white', alpha=0.3)
        ax.grid(True, alpha=0.2, axis='x')
        ax.invert_yaxis()

        fig.tight_layout()
        self.canvas.draw()
