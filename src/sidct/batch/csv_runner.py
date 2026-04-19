"""Batch CSV Runner — processa múltiplas linhas sem abortar por erro de linha única."""
from __future__ import annotations
import csv
import io
import logging
from typing import Iterator

from ..models import LineInput, FittingItem, ValveItem, BatchRowResult
from ..engines.selector import run_full_calculation

logger = logging.getLogger("sidct.batch")

# Colunas obrigatórias mínimas
REQUIRED_COLS = [
    "project_name", "line_tag", "service", "project_profile",
    "material", "P_oper_bar", "T_oper_c", "P_design_bar", "T_design_c",
    "flow_rate", "flow_rate_basis", "line_length_m",
]


def _parse_float(val: str, default: float | None = None) -> float | None:
    if val is None or str(val).strip() in ("", "N/A", "n/a", "NA"):
        return default
    try:
        return float(str(val).strip())
    except ValueError:
        return default


def _parse_row(row: dict, idx: int) -> LineInput:
    """Converte linha CSV em LineInput."""
    fittings: list[FittingItem] = []
    # Formato simplificado: fittings_90lr=4 na coluna 'fittings'
    if row.get("n_90lr_elbows"):
        n = int(_parse_float(row.get("n_90lr_elbows", "0")) or 0)
        if n:
            fittings.append(FittingItem(fitting_type="90_LR_ELBOW", quantity=n))

    return LineInput(
        project_name=row.get("project_name", f"PROJ-{idx}"),
        line_tag=row.get("line_tag", f"L-{idx:03d}"),
        service=row["service"].strip(),
        project_profile=row["project_profile"].strip(),
        jurisdiction=row.get("jurisdiction", "EU"),
        fluid_name=row.get("fluid_name", row["service"]),
        P_oper_bar=float(row["P_oper_bar"]),
        T_oper_c=float(row["T_oper_c"]),
        P_design_bar=float(row["P_design_bar"]),
        T_design_c=float(row["T_design_c"]),
        flow_rate=float(row["flow_rate"]),
        flow_rate_basis=row.get("flow_rate_basis", "m3/h"),
        line_length_m=float(row["line_length_m"]),
        elevation_delta_m=_parse_float(row.get("elevation_delta_m"), 0.0) or 0.0,
        material=row["material"].strip(),
        dimensional_catalog=row.get("dimensional_catalog", "ASME_B36_10M").strip(),
        design_code=row.get("design_code") or None,
        corrosion_allowance_mm=_parse_float(row.get("corrosion_allowance_mm")),
        insulation_thickness_mm=_parse_float(row.get("insulation_thickness_mm"), 0.0) or 0.0,
        insulation_density_kgm3=_parse_float(row.get("insulation_density_kgm3"), 100.0) or 100.0,
        fittings=fittings,
        valves=[],
        allowable_pressure_drop_bar=_parse_float(row.get("allowable_pressure_drop_bar")),
        DN_received_mm=_parse_float(row.get("DN_received_mm")),
        schedule_or_wall_received=row.get("schedule_or_wall_received") or None,
        slope_mm_m=_parse_float(row.get("slope_mm_m")),
        vacuum_target_mbara=_parse_float(row.get("vacuum_target_mbara")),
        design_notes=row.get("design_notes", ""),
        operation_mode=row.get("operation_mode", "calculate_new"),
    )


def run_batch(
    rows: list[dict],
) -> tuple[list[BatchRowResult], list[dict]]:
    """
    Processa lista de dicionários (linhas CSV).

    Returns:
        (results, errors)
        - results: BatchRowResult para cada linha processada
        - errors: linhas que falharam com mensagem
    """
    results: list[BatchRowResult] = []
    errors: list[dict] = []

    for idx, row in enumerate(rows):
        line_tag = row.get("line_tag", f"L-{idx:03d}")
        try:
            inp = _parse_row(row, idx)
            ctx = run_full_calculation(inp)
            cr = ctx.checker_result

            all_warnings: list[str] = []
            for src in [ctx.fluid_properties, ctx.hydraulic_result,
                        ctx.thickness_result, ctx.external_pressure_result,
                        ctx.checker_result]:
                if src and hasattr(src, "warnings") and src.warnings:
                    all_warnings.extend(src.warnings)

            results.append(BatchRowResult(
                row_index=idx,
                line_tag=line_tag,
                status=cr.overall_status if cr else "DATASET_MISSING",
                governing_issue=cr.governing_issue if cr else None,
                dataset_missing=cr.dataset_missing_items if cr else [],
                out_of_scope=cr.out_of_scope_items if cr else [],
                warnings_count=len(all_warnings),
                report_context=ctx,
            ))

        except Exception as e:
            logger.error(f"Linha {idx} ({line_tag}): {e}")
            errors.append({"row_index": idx, "line_tag": line_tag, "error": str(e)})
            results.append(BatchRowResult(
                row_index=idx,
                line_tag=line_tag,
                status="ERROR",
                error_message=str(e),
            ))

    return results, errors


def run_batch_from_csv(csv_path: str) -> tuple[list[BatchRowResult], list[dict]]:
    """Lê CSV do disco e executa batch."""
    rows: list[dict] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return run_batch(rows)


def run_batch_from_bytes(csv_bytes: bytes) -> tuple[bytes, bytes | None, str]:
    """Processa CSV bytes (Streamlit upload). Retorna (results_csv, errors_csv, summary)."""
    text = csv_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)

    results, errors = run_batch(rows)

    # Gerar results CSV
    result_buf = io.StringIO()
    fieldnames = ["row_index", "line_tag", "status", "governing_issue",
                  "dataset_missing", "out_of_scope", "warnings_count", "error_message"]
    w = csv.DictWriter(result_buf, fieldnames=fieldnames)
    w.writeheader()
    for r in results:
        w.writerow({
            "row_index": r.row_index,
            "line_tag": r.line_tag,
            "status": r.status,
            "governing_issue": r.governing_issue or "",
            "dataset_missing": "; ".join(r.dataset_missing),
            "out_of_scope": "; ".join(r.out_of_scope),
            "warnings_count": r.warnings_count,
            "error_message": r.error_message or "",
        })

    errors_bytes = None
    if errors:
        err_buf = io.StringIO()
        ew = csv.DictWriter(err_buf, fieldnames=["row_index", "line_tag", "error"])
        ew.writeheader()
        for e in errors:
            ew.writerow(e)
        errors_bytes = err_buf.getvalue().encode("utf-8")

    n_ok = sum(1 for r in results if r.status not in ("ERROR", "CRITICAL", "INSUFFICIENT"))
    n_err = len(errors)
    n_crit = sum(1 for r in results if r.status == "CRITICAL")
    summary = (f"{len(results)} linhas processadas | {n_ok} OK | "
               f"{n_crit} CRÍTICAS | {n_err} erros")

    return result_buf.getvalue().encode("utf-8"), errors_bytes, summary


def write_summary_log(results: list[BatchRowResult], errors: list[dict],
                      log_path: str) -> None:
    """Escreve summary.log para batch processado em disco."""
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=== SIDCT BATCH SUMMARY ===\n\n")
        f.write(f"Total linhas: {len(results)}\n")
        n_ok = sum(1 for r in results if r.status in ("APPROVED", "CONSERVATIVE", "CALCULATED"))
        n_warn = sum(1 for r in results if r.status == "WARNING")
        n_insuff = sum(1 for r in results if r.status == "INSUFFICIENT")
        n_crit = sum(1 for r in results if r.status == "CRITICAL")
        n_miss = sum(1 for r in results if r.status == "DATASET_MISSING")
        n_err = len(errors)
        f.write(f"APPROVED/CONSERVATIVE/CALCULATED: {n_ok}\n")
        f.write(f"WARNING: {n_warn}\n")
        f.write(f"INSUFFICIENT: {n_insuff}\n")
        f.write(f"CRITICAL: {n_crit}\n")
        f.write(f"DATASET_MISSING: {n_miss}\n")
        f.write(f"ERROR: {n_err}\n\n")
        f.write("=== DETALHES ===\n")
        for r in results:
            f.write(f"[{r.row_index:03d}] {r.line_tag:<20} {r.status:<20} "
                    f"issue={r.governing_issue or ''}\n")
        if errors:
            f.write("\n=== ERROS ===\n")
            for e in errors:
                f.write(f"[{e['row_index']:03d}] {e['line_tag']}: {e['error']}\n")
