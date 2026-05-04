"""Project-level PDF report for multi-line SIDCT projects."""
from __future__ import annotations

import io
from pathlib import Path

from ..project import Project
from .exports import RESULT_LABELS, format_export_value, project_rows

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


def _fmt(field: str, value: object) -> str:
    return str(format_export_value(field, value))


def _status_counts(project: Project) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in project.all_lines():
        status = line.validation_state.status
        counts[status] = counts.get(status, 0) + 1
    return counts


def generate_project_pdf(project: Project, output_path: str | Path | None = None) -> bytes:
    """Generate a compact multi-line project report and optionally write it."""
    if not REPORTLAB_OK:
        raise ImportError("ReportLab is required for project PDF export")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"SIDCT Project Report - {project.name}",
        author="SIDCT",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("SIDCTH1", parent=styles["Heading1"], fontSize=15, spaceAfter=6)
    h2 = ParagraphStyle("SIDCTH2", parent=styles["Heading2"], fontSize=10, spaceAfter=4)
    normal = ParagraphStyle("SIDCTNormal", parent=styles["Normal"], fontSize=8, spaceAfter=2)
    small = ParagraphStyle("SIDCTSmall", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#555555"))

    def table(data, header=True, col_widths=None):
        tbl = Table(data, repeatRows=1 if header else 0, colWidths=col_widths)
        style = [
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ]
        if header:
            style.extend([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24455F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ])
        tbl.setStyle(TableStyle(style))
        return tbl

    story = [
        Paragraph("SIDCT - Project Calculation Report", h1),
        HRFlowable(width="100%", thickness=0.5, color=colors.grey),
        table([
            ["Project", project.name],
            ["Client", project.client or "N/A"],
            ["Site", project.site or "N/A"],
            ["Revision", project.revision],
            ["Updated", project.updated_at],
            ["Routes", str(len(project.routes))],
            ["Lines", str(len(project.all_lines()))],
        ], header=False),
        Spacer(1, 4 * mm),
        Paragraph("Status Summary", h2),
    ]

    counts = _status_counts(project)
    summary = [["Status", "Count"]] + [[status, str(count)] for status, count in sorted(counts.items())]
    story.append(table(summary))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Line Results", h2))
    wanted = [
        "route_name",
        "line_tag",
        "service",
        "material",
        "catalog",
        "DN_governing_mm",
        "governing_criterion",
        "velocity_ms",
        "dp_total_bar",
        "flow_depth_ratio",
        "selected_schedule",
        "checker_status",
        "governing_issue",
    ]
    rows = project_rows(project)
    data = [[RESULT_LABELS.get(field, field) for field in wanted]]
    for row in rows:
        data.append([_fmt(field, row.get(field)) for field in wanted])
    story.append(table(data, col_widths=[22*mm, 20*mm, 28*mm, 22*mm, 27*mm, 20*mm, 24*mm, 22*mm, 22*mm, 24*mm, 24*mm, 40*mm]))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Warnings and Dataset Gaps", h2))
    warning_rows = [["Line", "Status", "Warnings", "Dataset missing", "Out of scope"]]
    for line in project.all_lines():
        if any([line.validation_state.warnings, line.validation_state.dataset_missing, line.validation_state.out_of_scope]):
            warning_rows.append([
                line.tag,
                line.validation_state.status,
                "; ".join(line.validation_state.warnings[:4]) or "N/A",
                "; ".join(line.validation_state.dataset_missing) or "N/A",
                "; ".join(line.validation_state.out_of_scope) or "N/A",
            ])
    if len(warning_rows) == 1:
        warning_rows.append(["N/A", "N/A", "No warnings or dataset gaps recorded.", "N/A", "N/A"])
    story.append(table(warning_rows))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Scope", h2))
    story.append(Paragraph(
        "Project report aggregates SIDCT line calculations. It does not replace final "
        "engineering review, licensed normative datasets, manufacturer derating tables, "
        "external pressure chart checks, support/flexibility stress analysis, or authority approval.",
        small,
    ))
    story.append(Paragraph(f"Audit events: {len(project.audit_log)}", normal))

    doc.build(story)
    pdf = buffer.getvalue()
    if output_path:
        Path(output_path).write_bytes(pdf)
    return pdf
