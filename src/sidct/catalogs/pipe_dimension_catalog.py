"""Catálogo dimensional de tubagens — ASME B36.10M e B36.19M.

Dados reproduzíveis de domínio público.
Fonte: ASME B36.10M-2015 e ASME B36.19M-2004(R2015).
"""
from __future__ import annotations
from typing import Optional
from ..models import PipeDimension
from ..exceptions import DatasetMissingError, ValidationError, CodeMismatchError

# ─── ASME B36.10M — Aço Carbono ────────────────────────────────────────────────
# Formato: (DN_mm, NPS_inch, OD_mm): {schedule: wall_mm}
# OD fixo por NPS; wall varia por schedule.
# Valores de domínio público (reproduzíveis de publicações técnicas).

B36_10M_OD: dict[float, float] = {
    # DN_mm  : OD_mm
    6:    10.3,
    8:    13.7,
    10:   17.1,
    15:   21.3,
    20:   26.7,
    25:   33.4,
    32:   42.2,
    40:   48.3,
    50:   60.3,
    65:   73.0,
    80:   88.9,
    90:  101.6,
    100: 114.3,
    125: 141.3,
    150: 168.3,
    200: 219.1,
    250: 273.1,
    300: 323.9,
    350: 355.6,
    400: 406.4,
    450: 457.2,
    500: 508.0,
    600: 609.6,
    700: 711.2,
    750: 762.0,
    800: 812.8,
    900: 914.4,
    1000: 1016.0,
    1050: 1066.8,
    1200: 1219.2,
}

B36_10M_NPS: dict[float, float] = {
    # DN_mm: NPS_inch
    6: 0.125, 8: 0.25, 10: 0.375, 15: 0.5, 20: 0.75, 25: 1.0,
    32: 1.25, 40: 1.5, 50: 2.0, 65: 2.5, 80: 3.0, 90: 3.5, 100: 4.0,
    125: 5.0, 150: 6.0, 200: 8.0, 250: 10.0, 300: 12.0, 350: 14.0,
    400: 16.0, 450: 18.0, 500: 20.0, 600: 24.0, 700: 28.0, 750: 30.0,
    800: 32.0, 900: 36.0, 1000: 40.0, 1050: 42.0, 1200: 48.0,
}

# Wall thickness por DN e schedule (mm)
# Apenas schedules relevantes incluídos — dataset parcial de domínio público
B36_10M_WALLS: dict[float, dict[str, float]] = {
    15:  {"SCH10": 2.77, "SCH40": 2.77, "SCH80": 3.73, "STD": 2.77, "XS": 3.73, "XXS": 7.47},
    20:  {"SCH10": 2.87, "SCH40": 2.87, "SCH80": 3.91, "STD": 2.87, "XS": 3.91, "XXS": 7.82},
    25:  {"SCH10": 3.38, "SCH40": 3.38, "SCH80": 4.55, "STD": 3.38, "XS": 4.55, "XXS": 9.09},
    32:  {"SCH10": 3.56, "SCH40": 3.56, "SCH80": 4.85, "STD": 3.56, "XS": 4.85, "XXS": 9.70},
    40:  {"SCH10": 3.68, "SCH40": 3.68, "SCH80": 5.08, "STD": 3.68, "XS": 5.08, "XXS": 10.15},
    50:  {"SCH10": 3.91, "SCH40": 3.91, "SCH80": 5.54, "STD": 3.91, "XS": 5.54, "XXS": 11.07},
    65:  {"SCH10": 5.16, "SCH40": 5.16, "SCH80": 7.01, "STD": 5.16, "XS": 7.01, "XXS": 14.02},
    80:  {"SCH10": 5.49, "SCH40": 5.49, "SCH80": 7.62, "STD": 5.49, "XS": 7.62, "XXS": 15.24},
    90:  {"SCH10": 5.74, "SCH40": 5.74, "SCH80": 8.08, "STD": 5.74, "XS": 8.08},
    100: {"SCH10": 6.02, "SCH40": 6.02, "SCH80": 8.56, "STD": 6.02, "XS": 8.56, "XXS": 17.12},
    125: {"SCH10": 6.55, "SCH40": 6.55, "SCH80": 9.53, "STD": 6.55, "XS": 9.53, "XXS": 19.05},
    150: {"SCH10": 7.11, "SCH40": 7.11, "SCH80": 10.97, "STD": 7.11, "XS": 10.97, "XXS": 21.95},
    200: {"SCH10": 7.04, "SCH20": 8.18, "SCH30": 8.18, "SCH40": 8.18, "SCH60": 10.31,
           "SCH80": 12.70, "SCH100": 15.09, "SCH120": 18.26, "SCH140": 20.62, "SCH160": 23.01,
           "STD": 9.53, "XS": 12.70, "XXS": 23.01},
    250: {"SCH10": 7.80, "SCH20": 9.27, "SCH30": 9.27, "SCH40": 9.27, "SCH60": 12.70,
           "SCH80": 15.09, "SCH100": 18.26, "SCH120": 21.44, "SCH140": 25.40, "SCH160": 28.58,
           "STD": 9.27, "XS": 12.70},
    300: {"SCH10": 8.38, "SCH20": 9.53, "SCH30": 9.53, "SCH40": 10.31, "SCH60": 14.27,
           "SCH80": 17.48, "SCH100": 21.44, "SCH120": 25.40, "SCH140": 28.58, "SCH160": 33.32,
           "STD": 9.53, "XS": 12.70},
    350: {"SCH10": 9.53, "SCH20": 9.53, "SCH30": 11.13, "SCH40": 11.13, "SCH60": 15.09,
           "SCH80": 19.05, "SCH100": 23.83, "SCH120": 27.79, "SCH140": 31.75, "SCH160": 35.71,
           "STD": 9.53, "XS": 12.70},
    400: {"SCH10": 9.53, "SCH20": 9.53, "SCH30": 12.70, "SCH40": 12.70, "SCH60": 16.66,
           "SCH80": 21.44, "SCH100": 26.19, "SCH120": 30.96, "SCH140": 36.53, "SCH160": 40.49,
           "STD": 9.53, "XS": 12.70},
    450: {"SCH10": 9.53, "SCH20": 11.13, "SCH30": 12.70, "SCH40": 14.27, "SCH60": 19.05,
           "SCH80": 23.83, "SCH100": 29.36, "SCH120": 34.93, "SCH140": 39.67, "SCH160": 45.24,
           "STD": 9.53, "XS": 12.70},
    500: {"SCH10": 9.53, "SCH20": 12.70, "SCH30": 15.09, "SCH40": 15.09, "SCH60": 20.62,
           "SCH80": 26.19, "SCH100": 32.54, "SCH120": 38.10, "SCH140": 44.45, "SCH160": 50.01,
           "STD": 9.53, "XS": 12.70},
    600: {"SCH10": 9.53, "SCH20": 14.27, "SCH30": 17.48, "SCH40": 17.48,
           "STD": 9.53, "XS": 12.70},
}

# ─── ASME B36.19M — Inox ────────────────────────────────────────────────────────
B36_19M_OD: dict[float, float] = B36_10M_OD  # OD partilhado (igual B36.10M)

B36_19M_WALLS: dict[float, dict[str, float]] = {
    15:  {"SCH5S": 1.65, "SCH10S": 2.77, "SCH40S": 2.77, "SCH80S": 3.73},
    20:  {"SCH5S": 1.65, "SCH10S": 2.87, "SCH40S": 2.87, "SCH80S": 3.91},
    25:  {"SCH5S": 1.65, "SCH10S": 3.38, "SCH40S": 3.38, "SCH80S": 4.55},
    32:  {"SCH5S": 1.65, "SCH10S": 3.56, "SCH40S": 3.56, "SCH80S": 4.85},
    40:  {"SCH5S": 1.65, "SCH10S": 3.68, "SCH40S": 3.68, "SCH80S": 5.08},
    50:  {"SCH5S": 1.65, "SCH10S": 3.91, "SCH40S": 3.91, "SCH80S": 5.54},
    65:  {"SCH5S": 2.11, "SCH10S": 5.16, "SCH40S": 5.16, "SCH80S": 7.01},
    80:  {"SCH5S": 2.11, "SCH10S": 5.49, "SCH40S": 5.49, "SCH80S": 7.62},
    100: {"SCH5S": 2.77, "SCH10S": 3.05, "SCH40S": 6.02, "SCH80S": 8.56},
    125: {"SCH5S": 2.77, "SCH10S": 3.40, "SCH40S": 6.55, "SCH80S": 9.53},
    150: {"SCH5S": 2.77, "SCH10S": 3.40, "SCH40S": 7.11, "SCH80S": 10.97},
    200: {"SCH5S": 3.40, "SCH10S": 3.76, "SCH40S": 8.18, "SCH80S": 12.70},
    250: {"SCH5S": 3.96, "SCH10S": 4.19, "SCH40S": 9.27, "SCH80S": 15.09},
    300: {"SCH5S": 4.55, "SCH10S": 4.78, "SCH40S": 10.31, "SCH80S": 17.48},
}

# ─── Densidade do aço (para cálculo de peso) ────────────────────────────────────
STEEL_DENSITY_KGM3 = 7850.0


def _pipe_weight_kgm(OD_mm: float, wt_mm: float) -> float:
    """Peso por metro de tubo de aço [kg/m]."""
    import math
    OD_m = OD_mm / 1000.0
    ID_m = (OD_mm - 2 * wt_mm) / 1000.0
    area_m2 = math.pi / 4.0 * (OD_m**2 - ID_m**2)
    return area_m2 * STEEL_DENSITY_KGM3


def get_pipe_dimension(
    catalog: str,
    DN_mm: float,
    schedule: str,
) -> PipeDimension:
    """Retorna dimensões do tubo para o catálogo, DN e schedule especificados."""
    schedule_upper = schedule.upper().replace(" ", "").replace("-", "")
    catalog_upper = catalog.upper().replace(".", "").replace("-", "").replace("_", "")

    if catalog_upper in ("ASMEB3610M", "B3610M", "B36_10M"):
        walls = B36_10M_WALLS
        od_map = B36_10M_OD
        nps_map = B36_10M_NPS
        cat_name = "ASME_B36_10M"
    elif catalog_upper in ("ASMEB3619M", "B3619M", "B36_19M"):
        walls = B36_19M_WALLS
        od_map = B36_19M_OD
        nps_map = B36_10M_NPS
        cat_name = "ASME_B36_19M"
    else:
        raise DatasetMissingError(catalog, "Catálogo não suportado nesta versão")

    if DN_mm not in od_map:
        available = sorted(od_map.keys())
        raise ValidationError(
            f"DN {DN_mm} mm não disponível no catálogo {cat_name}. "
            f"DNs disponíveis: {available}", "DN_mm"
        )
    if DN_mm not in walls:
        raise DatasetMissingError(
            f"{cat_name}:DN{DN_mm}",
            f"Schedules para DN {DN_mm} não disponíveis no dataset embutido. "
            f"Fornecer WT em /data/user_supplied/"
        )
    sch_map = walls[DN_mm]
    if schedule_upper not in sch_map:
        available_sch = list(sch_map.keys())
        raise ValidationError(
            f"Schedule '{schedule_upper}' não disponível para DN {DN_mm} em {cat_name}. "
            f"Schedules disponíveis: {available_sch}", "schedule"
        )

    OD_mm = od_map[DN_mm]
    wt_mm = sch_map[schedule_upper]
    ID_mm = OD_mm - 2.0 * wt_mm
    nps = nps_map.get(DN_mm, DN_mm / 25.4)
    weight = _pipe_weight_kgm(OD_mm, wt_mm)

    return PipeDimension(
        catalog=cat_name,
        DN_mm=DN_mm,
        NPS_inch=nps,
        OD_mm=OD_mm,
        wall_thickness_mm=wt_mm,
        schedule=schedule_upper,
        ID_mm=ID_mm,
        weight_kgm=weight,
    )


def get_available_schedules(catalog: str, DN_mm: float) -> list[str]:
    cat_upper = catalog.upper().replace(".", "").replace("-", "").replace("_", "")
    if cat_upper in ("ASMEB3610M", "B3610M", "B36_10M"):
        walls = B36_10M_WALLS
    elif cat_upper in ("ASMEB3619M", "B3619M", "B36_19M"):
        walls = B36_19M_WALLS
    else:
        return []
    return list(walls.get(DN_mm, {}).keys())


def get_available_dns(catalog: str) -> list[float]:
    cat_upper = catalog.upper().replace(".", "").replace("-", "").replace("_", "")
    if cat_upper in ("ASMEB3610M", "B3610M", "B36_10M"):
        return sorted(B36_10M_OD.keys())
    elif cat_upper in ("ASMEB3619M", "B3619M", "B36_19M"):
        return sorted(B36_19M_OD.keys())
    return []


def find_minimum_schedule(
    catalog: str,
    DN_mm: float,
    min_wall_mm: float,
) -> Optional[PipeDimension]:
    """Encontra o schedule mais leve que satisfaz a espessura mínima requerida."""
    cat_upper = catalog.upper().replace(".", "").replace("-", "").replace("_", "")
    if cat_upper in ("ASMEB3610M", "B3610M", "B36_10M"):
        walls_db = B36_10M_WALLS
        od_map = B36_10M_OD
        nps_map = B36_10M_NPS
        cat_name = "ASME_B36_10M"
    elif cat_upper in ("ASMEB3619M", "B3619M", "B36_19M"):
        walls_db = B36_19M_WALLS
        od_map = B36_19M_OD
        nps_map = B36_10M_NPS
        cat_name = "ASME_B36_19M"
    else:
        return None

    if DN_mm not in walls_db:
        return None

    sch_map = walls_db[DN_mm]
    OD_mm = od_map[DN_mm]

    # Ordenar por espessura crescente → pegar o primeiro que satisfaz
    sorted_schedules = sorted(sch_map.items(), key=lambda x: x[1])
    for sch_name, wt_mm in sorted_schedules:
        if wt_mm >= min_wall_mm:
            ID_mm = OD_mm - 2.0 * wt_mm
            nps = nps_map.get(DN_mm, DN_mm / 25.4)
            weight = _pipe_weight_kgm(OD_mm, wt_mm)
            return PipeDimension(
                catalog=cat_name,
                DN_mm=DN_mm,
                NPS_inch=nps,
                OD_mm=OD_mm,
                wall_thickness_mm=wt_mm,
                schedule=sch_name,
                ID_mm=ID_mm,
                weight_kgm=weight,
            )
    return None


def find_dn_for_id(catalog: str, min_ID_mm: float, schedule: str) -> Optional[float]:
    """Encontra o DN mais pequeno cujo ID (no schedule dado) seja >= min_ID_mm."""
    dns = get_available_dns(catalog)
    for dn in sorted(dns):
        try:
            dim = get_pipe_dimension(catalog, dn, schedule)
            if dim.ID_mm >= min_ID_mm:
                return dn
        except Exception:
            continue
    return None
