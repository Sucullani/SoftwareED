"""
Módulo 9: Condiciones de Contorno
Aplicación de restricciones y resolución del sistema reducido.
"""

import numpy as np
from education.base_module import BaseEducationalModule, HAS_MATPLOTLIB
from fem.solver import solve_system


class BoundaryConditionsModule(BaseEducationalModule):
    """Módulo educativo: Condiciones de Contorno y Resolución."""

    def __init__(self, parent, project, element_id):
        super().__init__(parent, project, element_id,
                         "Condiciones de Contorno", width=1200, height=800)

        self._build_explanation()
        self._build_visualization()

    def _build_explanation(self):
        self.add_title("Condiciones de Contorno", "⑨")

        self.add_text(
            "Las condiciones de contorno son esenciales para que "
            "el sistema K*u = F tenga solucion unica. Sin ellas, "
            "la estructura tendria movimiento de cuerpo rigido "
            "y K seria singular."
        )

        self.add_subtitle("Metodo de eliminacion")
        self.add_text(
            "Se eliminan las filas y columnas de K correspondientes "
            "a los GDL restringidos (desplazamiento conocido = 0).\n\n"
            "K_reducida * u_libre = F_reducida"
        )

        self.add_separator()
        self.add_subtitle("Restricciones de su modelo")

        for bc in self.project.boundary_conditions.values():
            n = self.project.nodes[bc.node_id]
            rx = "Fijo" if bc.restrain_x else "Libre"
            ry = "Fijo" if bc.restrain_y else "Libre"
            self.add_text(
                f"  Nodo {bc.node_id} ({n.x}, {n.y}):"
                f" Dx={rx}, Dy={ry}"
            )

        restrained = self.project.get_restrained_dofs()
        free = self.project.get_free_dofs()
        self.add_value("GDL restringidos", str(restrained))
        self.add_value("GDL libres", str(free))

        self.add_separator()
        # Resolver para mostrar resultados
        try:
            solution = solve_system(self.project)
            u = solution["u"]
            R = solution["reactions"]

            self.add_subtitle("Solucion: Desplazamientos")
            for i in range(0, len(u), 2):
                nid = i // 2 + 1
                self.add_text(
                    f"  Nodo {nid}: Ux = {u[i]:.6e},  Uy = {u[i+1]:.6e}"
                )

            self.add_separator()
            self.add_subtitle("Reacciones en apoyos")
            for dof in restrained:
                nid = dof // 2 + 1
                comp = "Rx" if dof % 2 == 0 else "Ry"
                self.add_text(f"  Nodo {nid} ({comp}): {R[dof]:.4f}")

            # Verificar equilibrio
            sum_Rx = sum(R[d] for d in restrained if d % 2 == 0)
            sum_Ry = sum(R[d] for d in restrained if d % 2 == 1)
            sum_Fx = sum(l.fx for l in self.project.nodal_loads.values())
            sum_Fy = sum(l.fy for l in self.project.nodal_loads.values())

            self.add_separator()
            self.add_subtitle("Verificacion de equilibrio")
            self.add_value("Sum Rx + Sum Fx", sum_Rx + sum_Fx, ".4f")
            self.add_value("Sum Ry + Sum Fy", sum_Ry + sum_Fy, ".4f")
            self.add_text(
                "Ambas sumas deben ser ~0 (equilibrio estatico)."
            )
        except Exception as e:
            self.add_text(f"Error al resolver: {str(e)}")

    def _build_visualization(self):
        if not HAS_MATPLOTLIB:
            return

        fig, self.canvas = self.create_figure(figsize=(7, 6))

        try:
            solution = solve_system(self.project)
            u = solution["u"]

            # Dibujar malla original y deformada
            ax = fig.add_subplot(1, 1, 1)
            self.style_axis(ax, "Malla Original vs Deformada")

            # Determinar factor de escala
            max_disp = max(abs(u)) if max(abs(u)) > 0 else 1
            coords = np.array([
                [self.project.nodes[nid].x, self.project.nodes[nid].y]
                for nid in sorted(self.project.nodes.keys())
            ])
            model_size = max(
                coords[:, 0].max() - coords[:, 0].min(),
                coords[:, 1].max() - coords[:, 1].min()
            )
            scale = model_size * 0.1 / max_disp

            for elem in self.project.elements.values():
                # Original
                nids = elem.node_ids[:4]
                orig = np.array([
                    [self.project.nodes[n].x, self.project.nodes[n].y]
                    for n in nids
                ])
                orig_closed = np.vstack([orig, orig[0]])
                ax.plot(orig_closed[:, 0], orig_closed[:, 1],
                        '--', color='#555', lw=1)

                # Deformada
                deformed = np.array([
                    [self.project.nodes[n].x + scale * u[2*(n-1)],
                     self.project.nodes[n].y + scale * u[2*(n-1)+1]]
                    for n in nids
                ])
                def_closed = np.vstack([deformed, deformed[0]])
                ax.plot(def_closed[:, 0], def_closed[:, 1],
                        '-', color='#4fc3f7', lw=2)

            # Nodos
            for nid in sorted(self.project.nodes.keys()):
                n = self.project.nodes[nid]
                ax.plot(n.x, n.y, 'o', color='#666', ms=6)

                dx = scale * u[2*(nid-1)]
                dy = scale * u[2*(nid-1)+1]
                ax.plot(n.x + dx, n.y + dy, 'o', color='#4fc3f7', ms=6)

                # Restricciones
                if nid in self.project.boundary_conditions:
                    ax.plot(n.x, n.y, '^', color='#ffa726', ms=12)

            ax.set_xlabel("x", color='white')
            ax.set_ylabel("y", color='white')
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.2)
            ax.legend(
                ['Original', 'Deformada', '', 'Nodo orig.', 'Nodo def.', 'Restriccion'],
                fontsize=8, facecolor='#2a2a3e', edgecolor='#555',
                labelcolor='white', loc='best'
            )

        except Exception as e:
            ax = fig.add_subplot(1, 1, 1)
            ax.text(0.5, 0.5, f"Error: {str(e)}", ha='center', va='center',
                    color='red', fontsize=12, transform=ax.transAxes)

        fig.tight_layout()
        self.canvas.draw()
