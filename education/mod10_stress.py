"""
Módulo 10: Esfuerzos y Extrapolación
Cálculo de esfuerzos en puntos de Gauss y extrapolación a nodos.
"""

import numpy as np
from education.base_module import BaseEducationalModule, HAS_MATPLOTLIB
from fem.solver import solve_system
from fem.stress import compute_all_stresses, compute_element_stresses


class StressModule(BaseEducationalModule):
    """Módulo educativo: Esfuerzos y Extrapolación."""

    def __init__(self, parent, project, element_id):
        super().__init__(parent, project, element_id,
                         "Esfuerzos y Extrapolacion", width=1200, height=800)

        self._build_explanation()
        self._build_visualization()

    def _build_explanation(self):
        self.add_title("Esfuerzos y Extrapolacion", "⑩")

        self.add_text(
            "Una vez resuelto el sistema y obtenidos los desplazamientos, "
            "los esfuerzos se calculan como:\n\n"
            "  sigma = D * epsilon = D * B * u_e\n\n"
            "Los esfuerzos se evaluan en los puntos de Gauss (donde "
            "son mas precisos) y luego se extrapolan a los nodos."
        )

        self.add_subtitle("Componentes de esfuerzo")
        self.add_formula(
            "sigma_x  = Esfuerzo normal en x\n"
            "sigma_y  = Esfuerzo normal en y\n"
            "tau_xy   = Esfuerzo cortante\n"
            "sigma_1  = Esfuerzo principal maximo\n"
            "sigma_2  = Esfuerzo principal minimo\n"
            "sigma_VM = Von Mises"
        )

        self.add_subtitle("Esfuerzos principales")
        self.add_formula(
            "sigma_1,2 = (sx+sy)/2 +/- sqrt(((sx-sy)/2)^2 + txy^2)"
        )

        self.add_subtitle("Criterio de Von Mises")
        self.add_formula(
            "sigma_VM = sqrt(s1^2 - s1*s2 + s2^2)"
        )

        self.add_separator()

        # Resolver y calcular esfuerzos
        try:
            solution = solve_system(self.project)
            elem_stresses, nodal_stresses = compute_all_stresses(
                self.project, solution
            )

            self.add_subtitle(f"Esfuerzos en Elem {self.element_id}")
            if self.element_id in elem_stresses:
                gs = elem_stresses[self.element_id]["gauss_stresses"]
                for i, s in enumerate(gs):
                    self.add_text(
                        f"  PG{i+1} (xi={s['xi']:.3f}, eta={s['eta']:.3f}):"
                    )
                    self.add_formula(
                        f"    sx={s['sigma_x']:.4f}  sy={s['sigma_y']:.4f}"
                        f"  txy={s['tau_xy']:.4f}  VM={s['von_mises']:.4f}"
                    )

            self.add_separator()
            self.add_subtitle("Esfuerzos nodales promedio (todo el modelo)")
            for nid in sorted(nodal_stresses.keys()):
                s = nodal_stresses[nid]
                self.add_text(
                    f"  Nodo {nid}: sx={s['sigma_x']:.3f}  "
                    f"sy={s['sigma_y']:.3f}  txy={s['tau_xy']:.3f}  "
                    f"VM={s['von_mises']:.3f}"
                )

        except Exception as e:
            self.add_text(f"Error: {str(e)}")

    def _build_visualization(self):
        if not HAS_MATPLOTLIB:
            return

        fig, self.canvas = self.create_figure(figsize=(7, 6))

        try:
            solution = solve_system(self.project)
            _, nodal_stresses = compute_all_stresses(self.project, solution)

            node_ids = sorted(nodal_stresses.keys())
            vm_values = [nodal_stresses[nid]["von_mises"] for nid in node_ids]

            # Colormap de Von Mises sobre la malla
            ax = fig.add_subplot(1, 1, 1)
            self.style_axis(ax, "Von Mises - Valor en Nodos")

            from matplotlib.collections import PolyCollection
            from matplotlib.cm import ScalarMappable
            from matplotlib.colors import Normalize

            vm_min = min(vm_values) if vm_values else 0
            vm_max = max(vm_values) if vm_values else 1
            norm = Normalize(vmin=vm_min, vmax=vm_max)
            cmap = 'jet'

            for elem in self.project.elements.values():
                nids = elem.node_ids[:4]
                coords = np.array([
                    [self.project.nodes[n].x, self.project.nodes[n].y]
                    for n in nids
                ])

                # Color promedio del elemento
                vm_elem = np.mean([
                    nodal_stresses.get(n, {}).get("von_mises", 0)
                    for n in nids
                ])

                import matplotlib.pyplot as plt
                color = plt.cm.jet(norm(vm_elem))
                polygon = plt.Polygon(coords, facecolor=color, edgecolor='white',
                                       linewidth=1.5, alpha=0.85)
                ax.add_patch(polygon)

            # Nodos con valores
            for nid in node_ids:
                n = self.project.nodes[nid]
                vm = nodal_stresses[nid]["von_mises"]
                ax.annotate(
                    f"N{nid}\n{vm:.1f}",
                    xy=(n.x, n.y), fontsize=7, color='white',
                    ha='center', va='bottom',
                    textcoords="offset points", xytext=(0, 5),
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.6)
                )

            ax.set_xlabel("x", color='white')
            ax.set_ylabel("y", color='white')
            ax.set_aspect('equal')
            ax.autoscale()

            # Colorbar
            sm = ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, shrink=0.8)
            cbar.set_label("Von Mises", color='white')
            cbar.ax.tick_params(colors='white')

        except Exception as e:
            ax = fig.add_subplot(1, 1, 1)
            ax.text(0.5, 0.5, f"Error: {str(e)}", ha='center', va='center',
                    color='red', fontsize=12, transform=ax.transAxes)

        fig.tight_layout()
        self.canvas.draw()
