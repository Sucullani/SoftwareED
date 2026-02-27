"""
Generación de reportes PDF profesionales con resultados del análisis FEM.
Usa reportlab para crear documentos con tablas, imágenes y datos del modelo.
"""

import os
import io
import tempfile
from datetime import datetime

import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak, HRFlowable
)
from reportlab.platypus.flowables import KeepTogether


def generate_pdf_report(project, solution, nodal_stresses, filepath,
                        contour_figure=None):
    """
    Genera un reporte PDF profesional con los resultados del análisis FEM.

    Parámetros:
        project: ProjectModel con datos del modelo.
        solution: dict con resultados del solver (u, K, F, reactions, etc.).
        nodal_stresses: dict {node_id: {sigma_x, sigma_y, ...}} con esfuerzos.
        filepath: ruta donde guardar el PDF.
        contour_figure: matplotlib Figure opcional para incluir como imagen.
    """
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title=f"Reporte FEM - {project.project_name}",
        author="EduFEM - Software Educativo",
    )

    # ─── Estilos ─────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontSize=20,
        spaceAfter=6,
        textColor=colors.HexColor('#1a237e'),
        fontName='Helvetica-Bold',
    )

    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=16,
        textColor=colors.HexColor('#283593'),
        fontName='Helvetica-Bold',
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=6,
        spaceBefore=12,
        textColor=colors.HexColor('#3949ab'),
        fontName='Helvetica-Bold',
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        leading=14,
        fontName='Helvetica',
    )

    small_style = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        fontName='Helvetica',
    )

    center_style = ParagraphStyle(
        'CenterText',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        fontName='Helvetica',
    )

    # ─── Elementos del documento ─────────────────────────────────────────
    story = []

    # ═══════════════════════════════════════════════════════════════════
    # PORTADA
    # ═══════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("REPORTE DE ANÁLISIS", title_style))
    story.append(Paragraph("MÉTODO DE ELEMENTOS FINITOS", title_style))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(
        width="80%", thickness=2, color=colors.HexColor('#1a237e'),
        spaceAfter=0.5 * cm, spaceBefore=0.3 * cm
    ))

    # Info del proyecto
    info_data = [
        ["Proyecto:", project.project_name],
        ["Fecha:", datetime.now().strftime("%d/%m/%Y  %H:%M")],
        ["Tipo de Análisis:", project.analysis_type],
        ["Tipo de Elemento:", project.element_type],
        ["Sistema de Unidades:", project.unit_system],
        ["Nodos:", str(project.num_nodes)],
        ["Elementos:", str(project.num_elements)],
        ["GDL Totales:", str(project.total_dof)],
    ]

    info_table = Table(info_data, colWidths=[4 * cm, 10 * cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#555')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(info_table)
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph(
        "<i>Generado por EduFEM — Software Educativo de Elementos Finitos</i>",
        small_style
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # DATOS DEL MODELO
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("1. DATOS DEL MODELO", subtitle_style))

    # ─── Material ────────────────────────────────────────────────────
    story.append(Paragraph("1.1 Propiedades del Material", section_style))

    mat_data = [["Material", "E (Módulo)", "ν (Poisson)", "ρ (Densidad)"]]
    for name, mat in project.materials.items():
        mat_data.append([
            name,
            f"{mat.E:.2f}",
            f"{mat.nu:.4f}",
            f"{mat.density:.4f}" if hasattr(mat, 'density') else "—"
        ])

    mat_table = Table(mat_data, colWidths=[4 * cm, 3.5 * cm, 3 * cm, 3 * cm])
    mat_table.setStyle(_table_style())
    story.append(mat_table)
    story.append(Spacer(1, 0.3 * cm))

    # ─── Nodos ───────────────────────────────────────────────────────
    story.append(Paragraph("1.2 Coordenadas de Nodos", section_style))

    node_data = [["ID", "X", "Y"]]
    for nid in sorted(project.nodes.keys()):
        node = project.nodes[nid]
        node_data.append([str(nid), f"{node.x:.4f}", f"{node.y:.4f}"])

    node_table = Table(node_data, colWidths=[2 * cm, 4 * cm, 4 * cm])
    node_table.setStyle(_table_style())
    story.append(node_table)
    story.append(Spacer(1, 0.3 * cm))

    # ─── Elementos ───────────────────────────────────────────────────
    story.append(Paragraph("1.3 Conectividad de Elementos", section_style))

    elem_data = [["Elem", "N1", "N2", "N3", "N4", "Espesor", "Material"]]
    for eid in sorted(project.elements.keys()):
        elem = project.elements[eid]
        nids = list(elem.node_ids)
        while len(nids) < 4:
            nids.append("—")
        elem_data.append([
            str(eid), str(nids[0]), str(nids[1]),
            str(nids[2]), str(nids[3]),
            f"{elem.thickness:.4f}", elem.material_name
        ])

    elem_table = Table(
        elem_data,
        colWidths=[1.5 * cm, 1.5 * cm, 1.5 * cm, 1.5 * cm, 1.5 * cm, 2.5 * cm, 3.5 * cm]
    )
    elem_table.setStyle(_table_style())
    story.append(elem_table)
    story.append(Spacer(1, 0.3 * cm))

    # ─── Cargas ──────────────────────────────────────────────────────
    story.append(Paragraph("1.4 Cargas Nodales", section_style))

    if project.nodal_loads:
        load_data = [["Nodo", "Fx", "Fy"]]
        for nid in sorted(project.nodal_loads.keys()):
            load = project.nodal_loads[nid]
            load_data.append([
                str(nid), f"{load.fx:.4f}", f"{load.fy:.4f}"
            ])
        load_table = Table(load_data, colWidths=[2 * cm, 4 * cm, 4 * cm])
        load_table.setStyle(_table_style())
        story.append(load_table)
    else:
        story.append(Paragraph("Sin cargas nodales definidas.", body_style))

    story.append(Spacer(1, 0.3 * cm))

    # ─── Restricciones ───────────────────────────────────────────────
    story.append(Paragraph("1.5 Condiciones de Contorno", section_style))

    if project.boundary_conditions:
        bc_data = [["Nodo", "Restringir X", "Restringir Y"]]
        for nid in sorted(project.boundary_conditions.keys()):
            bc = project.boundary_conditions[nid]
            bc_data.append([
                str(nid),
                "Sí" if bc.restrain_x else "No",
                "Sí" if bc.restrain_y else "No"
            ])
        bc_table = Table(bc_data, colWidths=[2 * cm, 4 * cm, 4 * cm])
        bc_table.setStyle(_table_style())
        story.append(bc_table)
    else:
        story.append(Paragraph("Sin restricciones definidas.", body_style))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # RESULTADOS
    # ═══════════════════════════════════════════════════════════════════
    if solution is not None:
        story.append(Paragraph("2. RESULTADOS DEL ANÁLISIS", subtitle_style))

        u = solution["u"]
        R = solution["reactions"]
        restrained = solution["restrained_dofs"]

        # ─── Info general ────────────────────────────────────────────
        story.append(Paragraph("2.1 Información del Sistema", section_style))

        sys_data = [
            ["GDL Totales:", str(len(u))],
            ["GDL Libres:", str(len(solution['free_dofs']))],
            ["GDL Restringidos:", str(len(restrained))],
        ]
        sys_table = Table(sys_data, colWidths=[4 * cm, 6 * cm])
        sys_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(sys_table)
        story.append(Spacer(1, 0.3 * cm))

        # ─── Desplazamientos ─────────────────────────────────────────
        story.append(Paragraph("2.2 Desplazamientos Nodales", section_style))

        disp_data = [["Nodo", "Ux", "Uy", "|U|"]]
        for nid in sorted(project.nodes.keys()):
            ux = u[2 * (nid - 1)]
            uy = u[2 * (nid - 1) + 1]
            umag = np.sqrt(ux**2 + uy**2)
            disp_data.append([
                str(nid), f"{ux:.6e}", f"{uy:.6e}", f"{umag:.6e}"
            ])

        disp_table = Table(
            disp_data,
            colWidths=[2 * cm, 4 * cm, 4 * cm, 4 * cm]
        )
        disp_table.setStyle(_table_style())
        story.append(disp_table)
        story.append(Spacer(1, 0.3 * cm))

        # ─── Reacciones ──────────────────────────────────────────────
        story.append(Paragraph("2.3 Reacciones en Apoyos", section_style))

        reac_data = [["Nodo", "Rx", "Ry"]]
        for bc in sorted(project.boundary_conditions.values(), key=lambda b: b.node_id):
            nid = bc.node_id
            rx = R[2 * (nid - 1)] if bc.restrain_x else 0.0
            ry = R[2 * (nid - 1) + 1] if bc.restrain_y else 0.0
            reac_data.append([
                str(nid), f"{rx:.4f}", f"{ry:.4f}"
            ])

        # Verificar equilibrio
        sum_rx = sum(
            R[2 * (bc.node_id - 1)]
            for bc in project.boundary_conditions.values()
            if bc.restrain_x
        )
        sum_ry = sum(
            R[2 * (bc.node_id - 1) + 1]
            for bc in project.boundary_conditions.values()
            if bc.restrain_y
        )
        reac_data.append(["SUMA", f"{sum_rx:.4f}", f"{sum_ry:.4f}"])

        reac_table = Table(reac_data, colWidths=[2 * cm, 5 * cm, 5 * cm])
        reac_style = _table_style()
        # Resaltar fila de suma
        reac_style.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e3f2fd'))
        reac_style.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        reac_table.setStyle(reac_style)
        story.append(reac_table)
        story.append(Spacer(1, 0.3 * cm))

        # ─── Esfuerzos ───────────────────────────────────────────────
        if nodal_stresses:
            story.append(Paragraph("2.4 Esfuerzos Nodales (Promediados)", section_style))

            stress_data = [["Nodo", "σx", "σy", "τxy", "σ1", "σ2", "Von Mises"]]
            for nid in sorted(nodal_stresses.keys()):
                s = nodal_stresses[nid]
                stress_data.append([
                    str(nid),
                    f"{s['sigma_x']:.2f}",
                    f"{s['sigma_y']:.2f}",
                    f"{s['tau_xy']:.2f}",
                    f"{s['sigma_1']:.2f}",
                    f"{s['sigma_2']:.2f}",
                    f"{s['von_mises']:.2f}",
                ])

            stress_table = Table(
                stress_data,
                colWidths=[1.5 * cm, 2.3 * cm, 2.3 * cm, 2.3 * cm, 2.3 * cm, 2.3 * cm, 2.5 * cm]
            )
            stress_table.setStyle(_table_style(fontsize=8))
            story.append(stress_table)

        story.append(PageBreak())

        # ═══════════════════════════════════════════════════════════════
        # IMAGEN DE CONTORNOS
        # ═══════════════════════════════════════════════════════════════
        if contour_figure is not None:
            story.append(Paragraph("3. VISUALIZACIÓN DE RESULTADOS", subtitle_style))
            story.append(Spacer(1, 0.3 * cm))

            try:
                # Guardar figura a imagen temporal
                img_buffer = io.BytesIO()
                contour_figure.savefig(
                    img_buffer, format='png', dpi=200,
                    bbox_inches='tight', facecolor='white',
                    edgecolor='none'
                )
                img_buffer.seek(0)

                # Calcular tamaño que quepa en la página
                page_width = A4[0] - 4 * cm
                img = RLImage(img_buffer, width=page_width, height=page_width * 0.7)
                story.append(img)
                story.append(Spacer(1, 0.3 * cm))
                story.append(Paragraph(
                    "<i>Figura: Mapa de contornos del resultado seleccionado.</i>",
                    center_style
                ))
            except Exception as e:
                story.append(Paragraph(
                    f"Error al generar imagen: {str(e)}", body_style
                ))

    # ─── Pie de página info ──────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(
        width="100%", thickness=1, color=colors.grey,
        spaceAfter=0.3 * cm
    ))
    story.append(Paragraph(
        f"<i>Reporte generado por EduFEM v1.0.0 — "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
        small_style
    ))

    # ─── Generar PDF ─────────────────────────────────────────────────
    doc.build(story)
    return filepath


def _table_style(fontsize=9):
    """Retorna un estilo de tabla profesional reutilizable."""
    return TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#283593')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), fontsize),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        # Cuerpo
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), fontsize),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        # Bordes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ccc')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#283593')),
        # Alineación
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Filas alternadas
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#f5f5f5')]),
    ])
