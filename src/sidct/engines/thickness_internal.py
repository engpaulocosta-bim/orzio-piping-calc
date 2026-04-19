"""Cálculo de espessura mínima por pressão interna.

Códigos suportados: ASME B31.3, ASME B31.9, EN 13480.
Catálogos: B36.10M (carbono), B36.19M (inox).

Fórmulas de domínio público:
- ASME B31.3 Eq. (3a): t = P*D / (2*(S*E + P*Y))
- ASME B31.9 Eq. (5): similar a B31.3 com limites de pressão
- EN 13480-3 Eq. (6.1): e = P*do / (2*f + P)  [sem E, usa factor f]

AVISO: Tensões admissíveis usadas são de literatura pública (subset).
Para projeto real: usar Appendix A da norma com a edição contratual.
"""
from __future__ import annotations
import math
import logging
from ..models import LineInput, ThicknessResult, PipeDimension
from ..catalogs.material_stress_catalog import get_allowable_stress, is_material_supported
from ..catalogs.pipe_dimension_catalog import (
    get_available_dns, find_minimum_schedule, get_pipe_dimension
)
from ..exceptions import (DatasetMissingError, MaterialNotFoundError, ValidationError,
                           OutOfScopeError, CodeMismatchError)
from ..units import bar_to_pa, pa_to_bar, mpa_to_pa, pa_to_mpa

logger = logging.getLogger("sidct.thickness_internal")

MILL_TOLERANCE_PCT = 0.125  # 12.5% ASME B36.10M / B36.19M


def _get_corrosion_allowance(inp: LineInput, profile: dict) -> float:
    """Resolve corrosion allowance: entrada do utilizador > default do perfil."""
    if inp.corrosion_allowance_mm is not None:
        return inp.corrosion_allowance_mm
    mat_lower = inp.material.lower()
    ca_defaults = profile.get("corrosion_allowance_defaults", {})
    is_stainless = any(k in mat_lower for k in ("316", "304", "tp3", "inox"))
    if is_stainless:
        return ca_defaults.get("stainless_steel", 0.0)
    if inp.service in ("compressed_air", "natural_gas"):
        return ca_defaults.get("carbon_steel_gas", 1.0)
    return ca_defaults.get("carbon_steel_water", 1.5)


def _thickness_asme_b31_3(
    P_design_bar: float,
    T_design_c: float,
    OD_mm: float,
    S_MPa: float,
    E: float,
    Y: float,
    ca_mm: float,
    mill_tol_pct: float,
) -> dict:
    """ASME B31.3 Eq. (3a): t = P*D / (2*(S*E + P*Y))"""
    P_mpa = P_design_bar / 10.0  # bar → MPa (1 bar ≈ 0.1 MPa)
    D_mm = OD_mm

    # t_min (pressão apenas, sem CA, sem mill tolerance)
    denom = 2.0 * (S_MPa * E + P_mpa * Y)
    if denom <= 0:
        raise ValidationError("Denominador ≤ 0 em fórmula B31.3 — verificar S, E, Y", "S_MPa")

    t_p = P_mpa * D_mm / denom  # mm
    t_ca = t_p + ca_mm          # com corrosion allowance
    t_mill = t_ca / (1.0 - mill_tol_pct)  # com mill tolerance

    clause = "ASME B31.3 — Eq. (3a) — Clause 304.1.2"
    equation = "t = P·D / (2·(S·E + P·Y))"
    return {
        "t_pressure_only_mm": t_p,
        "t_plus_ca_mm": t_ca,
        "t_after_mill_tolerance_mm": t_mill,
        "governing_code": "ASME B31.3",
        "governing_clause": clause,
        "equation": equation,
    }


def _thickness_asme_b31_9(
    P_design_bar: float,
    T_design_c: float,
    OD_mm: float,
    S_MPa: float,
    E: float,
    Y: float,
    ca_mm: float,
    mill_tol_pct: float,
) -> dict:
    """ASME B31.9 — usa mesma fórmula que B31.3 com limites de pressão."""
    if P_design_bar > 20.7:
        raise OutOfScopeError(
            f"P_design {P_design_bar} barg excede limite B31.9 (20.7 barg)",
            "P_design_bar", P_design_bar, 20.7
        )
    result = _thickness_asme_b31_3(P_design_bar, T_design_c, OD_mm, S_MPa, E, Y, ca_mm, mill_tol_pct)
    result["governing_code"] = "ASME B31.9"
    result["governing_clause"] = "ASME B31.9 — Eq. (5) — similar B31.3 Eq. (3a)"
    return result


def _thickness_en_13480(
    P_design_bar: float,
    T_design_c: float,
    OD_mm: float,
    f_MPa: float,   # tensão admissível EN (notação f em EN 13480)
    ca_mm: float,
    mill_tol_pct: float,
) -> dict:
    """EN 13480-3 Eq. (6.1-1): e_n = (P·d_o) / (2·f + P)

    Simplificação: sem factor de junta z (z=1 para seamless),
    sem factor de reforço de curvatura.
    """
    P_mpa = P_design_bar / 10.0
    d_o = OD_mm

    # e = P * do / (2f + P)  — espessura de projecto (sem tolerâncias)
    denom = 2.0 * f_MPa + P_mpa
    if denom <= 0:
        raise ValidationError("Denominador ≤ 0 em fórmula EN 13480 — verificar f, P", "f_MPa")

    e_p = (P_mpa * d_o) / denom  # mm
    e_ca = e_p + ca_mm
    e_mill = e_ca / (1.0 - mill_tol_pct)

    return {
        "t_pressure_only_mm": e_p,
        "t_plus_ca_mm": e_ca,
        "t_after_mill_tolerance_mm": e_mill,
        "governing_code": "EN 13480",
        "governing_clause": "EN 13480-3 — Eq. (6.1-1) — Clause 6.1",
        "equation": "e = P·do / (2·f + P)",
    }


def calculate_thickness(
    inp: LineInput,
    pipe: PipeDimension,
    design_code: str | None = None,
    weld_joint: str = "seamless",
    profile: dict | None = None,
) -> ThicknessResult:
    """Calcula espessura requerida e selecciona schedule."""
    code = design_code or inp.design_code
    if code is None:
        if profile:
            code = profile.get("primary_design_code", "ASME_B31_3")
        else:
            code = "ASME_B31_3"

    code_upper = code.upper().replace("_", "").replace(".", "").replace(" ", "")
    ca_mm = inp.corrosion_allowance_mm if inp.corrosion_allowance_mm is not None else (
        _get_corrosion_allowance(inp, profile or {})
    )
    warnings: list[str] = []
    assumptions: list[str] = ["A-TI-003", "A-TI-004"]

    # Verificar dataset de tensões
    if not is_material_supported(inp.material):
        return ThicknessResult(
            line_tag=inp.line_tag,
            design_code=code,
            material=inp.material,
            status="DATASET_MISSING",
            corrosion_allowance_mm=ca_mm,
            warnings=[
                f"Material '{inp.material}' não encontrado no dataset de tensões. "
                "Fornecer S (allowable stress) via /data/user_supplied/ "
                "ou usar material suportado: A106GrB, A53GrB, A312TP304, A312TP316."
            ],
        )

    try:
        S_MPa, E, Y, mat_key = get_allowable_stress(inp.material, inp.T_design_c, weld_joint)
    except MaterialNotFoundError as e:
        return ThicknessResult(
            line_tag=inp.line_tag,
            design_code=code,
            material=inp.material,
            status="DATASET_MISSING",
            corrosion_allowance_mm=ca_mm,
            warnings=[str(e)],
        )

    assumptions.append("A-TI-001")
    assumptions.append("A-TI-002")
    assumptions.append("A-MAT-001")

    OD_mm = pipe.OD_mm

    try:
        if "B313" in code_upper or "B31_3" in code_upper:
            res = _thickness_asme_b31_3(
                inp.P_design_bar, inp.T_design_c, OD_mm, S_MPa, E, Y,
                ca_mm, MILL_TOLERANCE_PCT
            )
        elif "B319" in code_upper or "B31_9" in code_upper:
            res = _thickness_asme_b31_9(
                inp.P_design_bar, inp.T_design_c, OD_mm, S_MPa, E, Y,
                ca_mm, MILL_TOLERANCE_PCT
            )
        elif "EN13480" in code_upper or "EN_13480" in code_upper:
            res = _thickness_en_13480(
                inp.P_design_bar, inp.T_design_c, OD_mm,
                S_MPa,  # EN usa f = allowable stress
                ca_mm, MILL_TOLERANCE_PCT
            )
        else:
            return ThicknessResult(
                line_tag=inp.line_tag,
                design_code=code,
                material=inp.material,
                status="DATASET_MISSING",
                warnings=[f"Código '{code}' não implementado. Suportados: ASME_B31_3, ASME_B31_9, EN_13480"],
            )
    except OutOfScopeError as e:
        return ThicknessResult(
            line_tag=inp.line_tag,
            design_code=code,
            material=inp.material,
            status="OUT_OF_SCOPE",
            warnings=[str(e)],
        )

    t_req = res["t_after_mill_tolerance_mm"]

    # Seleccionar schedule mais leve que satisfaz t_req
    pipe_sel = find_minimum_schedule(inp.dimensional_catalog, pipe.DN_mm, t_req)
    if pipe_sel is None:
        warnings.append(
            f"Nenhum schedule disponível para DN {pipe.DN_mm} e t_req = {t_req:.2f} mm. "
            "Verificar DN maior ou material com S mais elevado."
        )
        sel_wall = None
        sel_sch = None
    else:
        sel_wall = pipe_sel.wall_thickness_mm
        sel_sch = pipe_sel.schedule

    if E < 1.0:
        warnings.append(
            f"E = {E:.2f} (tubo não-seamless) — espessura aumentada. "
            "Considerar tubo seamless para reduzir espessura."
        )
    if ca_mm == 0.0:
        mat_lower = inp.material.lower()
        is_ss = any(k in mat_lower for k in ("316", "304", "tp3"))
        if not is_ss:
            warnings.append("CA = 0 para material não-inox — confirmar política de corrosão")

    return ThicknessResult(
        line_tag=inp.line_tag,
        design_code=code,
        material=inp.material,
        t_pressure_only_mm=res["t_pressure_only_mm"],
        t_plus_ca_mm=res["t_plus_ca_mm"],
        t_after_mill_tolerance_mm=t_req,
        selected_wall_mm=sel_wall,
        selected_schedule=sel_sch,
        allowable_stress_mpa=S_MPa,
        E_factor=E,
        Y_factor=Y,
        corrosion_allowance_mm=ca_mm,
        mill_tolerance_pct=MILL_TOLERANCE_PCT * 100.0,
        governing_code=res["governing_code"],
        governing_clause=res["governing_clause"],
        status="CALCULATED",
        warnings=warnings,
        assumptions_used=assumptions,
    )
