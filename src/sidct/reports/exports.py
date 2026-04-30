"""Tabular exports for SIDCT projects and calculation contexts."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from ..models import ReportContext
from ..project import Project


def context_to_row(ctx: ReportContext) -> dict[str, object]:
    inp = ctx.line_input
    hyd = ctx.hydraulic_result
    thick = ctx.thickness_result
    check = ctx.checker_result
    audit = (ctx.dataset_provenance or {}).get("audit", {})
    return {
        "project_name": ctx.project_name,
        "line_tag": ctx.line_tag,
        "service": inp.service if inp else "",
        "material": inp.material if inp else "",
        "catalog": inp.dimensional_catalog if inp else "",
        "DN_governing_mm": hyd.DN_governing_mm if hyd else None,
        "velocity_ms": hyd.velocity_ms if hyd else None,
        "dp_total_bar": hyd.dp_total_bar if hyd else None,
        "selected_schedule": thick.selected_schedule if thick else None,
        "selected_wall_mm": thick.selected_wall_mm if thick else None,
        "checker_status": check.overall_status if check else "",
        "governing_issue": check.governing_issue if check else "",
        "calculated_at": audit.get("calculated_at", ""),
        "schema_version": audit.get("schema_version", ""),
    }


def project_rows(project: Project) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for route in project.routes:
        for line in route.lines:
            if line.last_report_context is None:
                rows.append({
                    "project_name": project.name,
                    "line_tag": line.tag,
                    "service": line.line_input.service,
                    "material": line.line_input.material,
                    "catalog": line.line_input.dimensional_catalog,
                    "DN_governing_mm": None,
                    "velocity_ms": None,
                    "dp_total_bar": None,
                    "selected_schedule": None,
                    "selected_wall_mm": None,
                    "checker_status": line.validation_state.status,
                    "governing_issue": "",
                    "calculated_at": "",
                    "schema_version": project.schema_version,
                })
            else:
                rows.append(context_to_row(line.last_report_context))
    return rows


def export_rows_csv(rows: Iterable[dict[str, object]], path: str | Path) -> None:
    rows = list(rows)
    fieldnames = list(rows[0].keys()) if rows else ["project_name", "line_tag", "checker_status"]
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_project_csv(project: Project, path: str | Path) -> None:
    export_rows_csv(project_rows(project), path)


def export_project_xlsx(project: Project, path: str | Path) -> None:
    rows = project_rows(project)
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise ImportError("openpyxl is required for XLSX export") from exc

    wb = Workbook()
    ws = wb.active
    ws.title = "SIDCT Results"
    fieldnames = list(rows[0].keys()) if rows else ["project_name", "line_tag", "checker_status"]
    ws.append(fieldnames)
    for row in rows:
        ws.append([row.get(field) for field in fieldnames])

    for column in ws.columns:
        max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column)
        ws.column_dimensions[column[0].column_letter].width = min(max(max_len + 2, 12), 32)

    wb.save(path)
