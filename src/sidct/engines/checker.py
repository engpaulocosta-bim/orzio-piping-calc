"""Checker — compara projecto recebido vs calculado.

Status:
- APPROVED: dentro dos critérios
- CONSERVATIVE: dimensão recebida > requerida (margem positiva)
- INSUFFICIENT: dimensão recebida < requerida
- CRITICAL: insuficiência com margem negativa > 10%
- CODE_MISMATCH: código ou catálogo incompatível
- DATASET_MISSING: dados críticos ausentes
- OUT_OF_SCOPE: fora do envelope
"""
from __future__ import annotations
import logging
from ..models import (LineInput, HydraulicResult, ThicknessResult,
                       ExternalPressureResult, CheckerResult)

logger = logging.getLogger("sidct.checker")

CRITICAL_DEFICIT_PCT = 10.0  # margem de défice para status CRITICAL


def _margin_pct(required: float, received: float) -> float:
    if required <= 0:
        return float("inf")
    return (received - required) / required * 100.0


def run_checker(
    inp: LineInput,
    hydraulic: HydraulicResult | None = None,
    thickness: ThicknessResult | None = None,
    external: ExternalPressureResult | None = None,
) -> CheckerResult:
    """Executa verificação completa."""
    warnings: list[str] = []
    dataset_missing: list[str] = []
    out_of_scope: list[str] = []

    # ── Verificação hidráulica ─────────────────────────────────────────────────
    hyd_status = None
    hyd_margin = None
    DN_required = None
    DN_received = inp.DN_received_mm

    if hydraulic is not None:
        DN_required = hydraulic.DN_governing_mm

        if hydraulic.status == "DATASET_MISSING":
            hyd_status = "DATASET_MISSING"
            dataset_missing.append("hydraulic_engine")
        elif hydraulic.status == "OUT_OF_SCOPE":
            hyd_status = "OUT_OF_SCOPE"
            out_of_scope.append("hydraulic_calculation")
        elif DN_required is not None and DN_received is not None:
            hyd_margin = _margin_pct(DN_required, DN_received)
            if hyd_margin >= 0:
                hyd_status = "APPROVED" if abs(hyd_margin) < 5.0 else "CONSERVATIVE"
            else:
                hyd_status = "CRITICAL" if abs(hyd_margin) > CRITICAL_DEFICIT_PCT else "INSUFFICIENT"
        else:
            # Sem DN_received: apenas status calculado
            hyd_status = "CALCULATED" if hydraulic.status == "CALCULATED" else hydraulic.status
            warnings.append("DN_received não fornecido — verificação hidráulica parcial")

        warnings.extend(hydraulic.warnings or [])

    # ── Verificação de espessura ───────────────────────────────────────────────
    thick_status = None
    thick_margin = None
    wall_required = None
    wall_received_mm = None

    if inp.schedule_or_wall_received:
        # Tentar interpretar como número (mm)
        try:
            wall_received_mm = float(inp.schedule_or_wall_received)
        except ValueError:
            # É um schedule — resolver dimensão
            if DN_received is not None:
                try:
                    from ..catalogs.pipe_dimension_catalog import get_pipe_dimension
                    p = get_pipe_dimension(inp.dimensional_catalog, DN_received,
                                          inp.schedule_or_wall_received)
                    wall_received_mm = p.wall_thickness_mm
                except Exception:
                    pass

    if thickness is not None:
        wall_required = thickness.t_after_mill_tolerance_mm

        if thickness.status == "DATASET_MISSING":
            thick_status = "DATASET_MISSING"
            dataset_missing.append(f"material_stress:{inp.material}")
        elif thickness.status == "OUT_OF_SCOPE":
            thick_status = "OUT_OF_SCOPE"
            out_of_scope.append("thickness_calculation")
        elif wall_required is not None and wall_received_mm is not None:
            thick_margin = _margin_pct(wall_required, wall_received_mm)
            if thick_margin >= 0:
                thick_status = "APPROVED" if abs(thick_margin) < 5.0 else "CONSERVATIVE"
            else:
                thick_status = "CRITICAL" if abs(thick_margin) > CRITICAL_DEFICIT_PCT else "INSUFFICIENT"
        else:
            thick_status = thickness.status
            if wall_received_mm is None:
                warnings.append("schedule_or_wall_received não fornecido — verificação de espessura parcial")

        warnings.extend(thickness.warnings or [])

    # ── Verificação pressão externa ────────────────────────────────────────────
    ext_status = None
    ext_margin = None

    if inp.service == "vacuum_utility":
        if external is None:
            ext_status = "DATASET_MISSING"
            dataset_missing.append("external_pressure_check_not_performed")
            warnings.append(
                "CRÍTICO: Linha de vácuo sem verificação de pressão externa. "
                "Nunca aprovar sem external_pressure_check."
            )
        elif external.method_status == "DATASET_MISSING":
            ext_status = "DATASET_MISSING"
            dataset_missing.append("external_pressure_charts")
        elif external.utilization_ratio is not None:
            ur = external.utilization_ratio
            ext_margin = (1.0 - ur) * 100.0
            if ur > 1.0:
                ext_status = "CRITICAL"
            elif ur > 0.8:
                ext_status = "WARNING"
            else:
                ext_status = "APPROVED"

    # ── Status global ──────────────────────────────────────────────────────────
    all_statuses = [s for s in [hyd_status, thick_status, ext_status] if s is not None]

    def _severity(s: str) -> int:
        order = {"CRITICAL": 6, "DATASET_MISSING": 5, "OUT_OF_SCOPE": 4,
                 "INSUFFICIENT": 3, "CODE_MISMATCH": 3, "WARNING": 2,
                 "CONSERVATIVE": 1, "APPROVED": 0, "CALCULATED": 0}
        return order.get(s, 0)

    if all_statuses:
        overall = max(all_statuses, key=_severity)
    else:
        overall = "DATASET_MISSING" if (hydraulic is None and thickness is None) else "CALCULATED"

    # Nunca aprovar se DATASET_MISSING em campo crítico
    if dataset_missing:
        if overall in ("APPROVED", "CONSERVATIVE", "CALCULATED"):
            overall = "DATASET_MISSING"

    # Determinar governing issue
    governing_issue = None
    if overall == "CRITICAL":
        if ext_status == "CRITICAL":
            governing_issue = "external_pressure_collapse"
        elif thick_status == "CRITICAL":
            governing_issue = "wall_thickness_insufficient"
        elif hyd_status == "CRITICAL":
            governing_issue = "hydraulic_dn_insufficient"
    elif overall == "INSUFFICIENT":
        governing_issue = "thickness_or_dn_insufficient"
    elif overall == "DATASET_MISSING":
        governing_issue = "missing_datasets: " + ", ".join(dataset_missing)

    # Margem global (mínima das margens positivas ou maior défice)
    margins = [m for m in [hyd_margin, thick_margin, ext_margin] if m is not None]
    overall_margin = min(margins) if margins else None

    return CheckerResult(
        line_tag=inp.line_tag,
        operation_mode=inp.operation_mode,
        overall_status=overall,
        hydraulic_status=hyd_status,
        thickness_status=thick_status,
        external_pressure_status=ext_status,
        hydraulic_margin_pct=hyd_margin,
        thickness_margin_pct=thick_margin,
        external_margin_pct=ext_margin,
        overall_governing_margin_pct=overall_margin,
        governing_issue=governing_issue,
        DN_required_mm=DN_required,
        DN_received_mm=DN_received,
        wall_required_mm=wall_required,
        wall_received_mm=wall_received_mm,
        dataset_missing_items=dataset_missing,
        out_of_scope_items=out_of_scope,
        warnings=warnings,
    )
