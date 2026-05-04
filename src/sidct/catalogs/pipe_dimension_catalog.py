"""Catálogo dimensional de tubagens — ASME B36.10M e B36.19M.

Dados reproduzíveis de domínio público.
Fonte: ASME B36.10M-2015 e ASME B36.19M-2004(R2015).
"""
from __future__ import annotations
import logging
from pathlib import Path
import sys
from typing import Optional

import yaml

from ..models import PipeDimension
from ..exceptions import DatasetMissingError, ValidationError, CodeMismatchError

logger = logging.getLogger("sidct.catalogs")

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
PVC_DENSITY_KGM3 = 1400.0


def _pipe_weight_kgm(OD_mm: float, wt_mm: float) -> float:
    """Peso por metro de tubo de aço [kg/m]."""
    return _pipe_weight_for_density_kgm(OD_mm, wt_mm, STEEL_DENSITY_KGM3)


def _pipe_weight_for_density_kgm(OD_mm: float, wt_mm: float, density_kgm3: float) -> float:
    """Peso por metro de tubo [kg/m] para uma densidade de material."""
    import math
    OD_m = OD_mm / 1000.0
    ID_m = (OD_mm - 2 * wt_mm) / 1000.0
    area_m2 = math.pi / 4.0 * (OD_m**2 - ID_m**2)
    return area_m2 * density_kgm3


PVC_EN1452_OD: dict[float, float] = {
    15: 20.0, 20: 25.0, 25: 32.0, 32: 40.0, 40: 50.0, 50: 63.0,
    65: 75.0, 80: 90.0, 100: 110.0, 125: 140.0, 150: 160.0,
    200: 200.0, 250: 250.0, 300: 315.0,
}

PVC_EN1452_NPS: dict[float, float] = {dn: od / 25.4 for dn, od in PVC_EN1452_OD.items()}

PVC_EN1452_WALLS: dict[float, dict[str, float]] = {
    15: {"PN10": 1.5, "PN16": 1.9},
    20: {"PN10": 1.9, "PN16": 2.3},
    25: {"PN10": 2.4, "PN16": 3.0},
    32: {"PN10": 3.0, "PN16": 3.7},
    40: {"PN10": 3.7, "PN16": 4.6},
    50: {"PN10": 4.7, "PN16": 5.8},
    65: {"PN10": 5.6, "PN16": 6.8},
    80: {"PN10": 6.7, "PN16": 8.2},
    100: {"PN10": 6.6, "PN16": 10.0},
    125: {"PN10": 8.3, "PN16": 12.7},
    150: {"PN10": 9.5, "PN16": 14.6},
    200: {"PN10": 11.9, "PN16": 18.2},
    250: {"PN10": 14.8, "PN16": 22.7},
    300: {"PN10": 18.7, "PN16": 28.6},
}

PVC_ASTMD1785_OD: dict[float, float] = {
    15: 21.34, 20: 26.67, 25: 33.40, 32: 42.16, 40: 48.26, 50: 60.33,
    65: 73.03, 80: 88.90, 100: 114.30, 150: 168.28, 200: 219.08,
    250: 273.05, 300: 323.85,
}

PVC_ASTMD1785_NPS: dict[float, float] = {
    15: 0.5, 20: 0.75, 25: 1.0, 32: 1.25, 40: 1.5, 50: 2.0, 65: 2.5,
    80: 3.0, 100: 4.0, 150: 6.0, 200: 8.0, 250: 10.0, 300: 12.0,
}

PVC_ASTMD1785_WALLS: dict[float, dict[str, float]] = {
    15: {"SCH40": 2.77, "SCH80": 3.73},
    20: {"SCH40": 2.87, "SCH80": 3.91},
    25: {"SCH40": 3.38, "SCH80": 4.55},
    32: {"SCH40": 3.56, "SCH80": 4.85},
    40: {"SCH40": 3.68, "SCH80": 5.08},
    50: {"SCH40": 3.91, "SCH80": 5.54},
    65: {"SCH40": 5.16, "SCH80": 7.01},
    80: {"SCH40": 5.49, "SCH80": 7.62},
    100: {"SCH40": 6.02, "SCH80": 8.56},
    150: {"SCH40": 7.11, "SCH80": 10.97},
    200: {"SCH40": 8.18, "SCH80": 12.70},
    250: {"SCH40": 9.27, "SCH80": 15.09},
    300: {"SCH40": 10.31, "SCH80": 17.48},
}


# ─── PE 100 — EN 12201-2 / ISO 4427-2 — SDR series ─────────────────────────────
# OD per ISO 161-1 d-series (DN = OD nominal in mm)
# Wall thickness = OD / SDR (rounded up per standard)
# SDR17 ≈ PN10, SDR13.6 ≈ PN12.5, SDR11 ≈ PN16 (at 20°C for PE100)
PE_DENSITY_KGM3 = 960.0

PE_EN12201_OD: dict[float, float] = {
    20: 20.0, 25: 25.0, 32: 32.0, 40: 40.0, 50: 50.0, 63: 63.0,
    75: 75.0, 90: 90.0, 110: 110.0, 125: 125.0, 140: 140.0,
    160: 160.0, 180: 180.0, 200: 200.0, 225: 225.0, 250: 250.0,
    280: 280.0, 315: 315.0, 355: 355.0, 400: 400.0, 450: 450.0,
    500: 500.0, 560: 560.0, 630: 630.0,
}

PE_EN12201_NPS: dict[float, float] = {dn: od / 25.4 for dn, od in PE_EN12201_OD.items()}

# Wall = round(OD / SDR, 1) per EN 12201 — "e" values from standard tables
PE_EN12201_WALLS: dict[float, dict[str, float]] = {
    20:  {"SDR17": 1.2, "SDR13.6": 1.5, "SDR11": 1.9},
    25:  {"SDR17": 1.5, "SDR13.6": 1.9, "SDR11": 2.3},
    32:  {"SDR17": 1.9, "SDR13.6": 2.4, "SDR11": 2.9},
    40:  {"SDR17": 2.4, "SDR13.6": 3.0, "SDR11": 3.7},
    50:  {"SDR17": 3.0, "SDR13.6": 3.7, "SDR11": 4.6},
    63:  {"SDR17": 3.8, "SDR13.6": 4.7, "SDR11": 5.8},
    75:  {"SDR17": 4.5, "SDR13.6": 5.6, "SDR11": 6.8},
    90:  {"SDR17": 5.4, "SDR13.6": 6.7, "SDR11": 8.2},
    110: {"SDR17": 6.6, "SDR13.6": 8.1, "SDR11": 10.0},
    125: {"SDR17": 7.4, "SDR13.6": 9.2, "SDR11": 11.4},
    140: {"SDR17": 8.3, "SDR13.6": 10.3, "SDR11": 12.7},
    160: {"SDR17": 9.5, "SDR13.6": 11.8, "SDR11": 14.6},
    180: {"SDR17": 10.7, "SDR13.6": 13.3, "SDR11": 16.4},
    200: {"SDR17": 11.9, "SDR13.6": 14.7, "SDR11": 18.2},
    225: {"SDR17": 13.4, "SDR13.6": 16.6, "SDR11": 20.5},
    250: {"SDR17": 14.8, "SDR13.6": 18.4, "SDR11": 22.7},
    280: {"SDR17": 16.6, "SDR13.6": 20.6, "SDR11": 25.4},
    315: {"SDR17": 18.7, "SDR13.6": 23.2, "SDR11": 28.6},
    355: {"SDR17": 21.1, "SDR13.6": 26.1, "SDR11": 32.2},
    400: {"SDR17": 23.7, "SDR13.6": 29.4, "SDR11": 36.3},
    450: {"SDR17": 26.7, "SDR13.6": 33.1, "SDR11": 40.9},
    500: {"SDR17": 29.7, "SDR13.6": 36.8, "SDR11": 45.4},
    560: {"SDR17": 33.2, "SDR13.6": 41.2, "SDR11": 50.8},
    630: {"SDR17": 37.4, "SDR13.6": 46.3, "SDR11": 57.2},
}

# ─── PP-R — ISO 15874-2 / Class C — SDR series ────────────────────────────
# OD per ISO 161-1 (same series as PE) — common PP-R range DN15-DN110
# SDR11 ≈ PN10@70°C, SDR7.4 ≈ PN16@70°C, SDR6 ≈ PN20@70°C for Class C
PPR_DENSITY_KGM3 = 900.0

PPR_ISO15874_OD: dict[float, float] = {
    15: 20.0, 20: 25.0, 25: 32.0, 32: 40.0, 40: 50.0, 50: 63.0,
    65: 75.0, 80: 90.0, 100: 110.0, 110: 125.0,
}

PPR_ISO15874_NPS: dict[float, float] = {dn: od / 25.4 for dn, od in PPR_ISO15874_OD.items()}

PPR_ISO15874_WALLS: dict[float, dict[str, float]] = {
    15:  {"SDR11": 1.9, "SDR7.4": 2.8, "SDR6": 3.4},
    20:  {"SDR11": 2.3, "SDR7.4": 3.5, "SDR6": 4.2},
    25:  {"SDR11": 2.9, "SDR7.4": 4.4, "SDR6": 5.4},
    32:  {"SDR11": 3.7, "SDR7.4": 5.5, "SDR6": 6.7},
    40:  {"SDR11": 4.6, "SDR7.4": 6.9, "SDR6": 8.4},
    50:  {"SDR11": 5.8, "SDR7.4": 8.6, "SDR6": 10.5},
    65:  {"SDR11": 6.8, "SDR7.4": 10.2, "SDR6": 12.5},
    80:  {"SDR11": 8.2, "SDR7.4": 12.3, "SDR6": 15.0},
    100: {"SDR11": 10.0, "SDR7.4": 15.1, "SDR6": 18.3},
    110: {"SDR11": 11.4, "SDR7.4": 17.1, "SDR6": 20.8},
}


def _load_catalog_yaml(catalog_key: str) -> tuple[dict[float, dict[str, float]], dict[float, float], dict[float, float], str, float] | None:
    """Attempt to load a catalog from its external YAML file."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
    base_dir = root / "data" / "catalogs"
    yaml_path = base_dir / f"{catalog_key.lower()}.yaml"
    if not yaml_path.exists():
        return None
    try:
        with yaml_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        density = float(data.get("density_kgm3", 7850.0))
        od_map = {float(k): float(v) for k, v in data.get("od", {}).items()}
        nps_map = {float(k): float(v) for k, v in data.get("nps", {}).items()}
        walls_map = {}
        for dn, sch_dict in data.get("walls", {}).items():
            walls_map[float(dn)] = {str(k): float(v) for k, v in sch_dict.items()}
        return walls_map, od_map, nps_map, catalog_key, density
    except Exception as exc:
        logger.warning("Failed to load catalog %s from YAML: %s", catalog_key, exc)
        return None


def _catalog_maps(catalog: str) -> tuple[dict[float, dict[str, float]], dict[float, float], dict[float, float], str, float]:
    catalog_upper = catalog.upper().replace(".", "").replace("-", "").replace("_", "")
    
    # Map raw input to standard key
    key_map = {
        "ASMEB3610M": "ASME_B36_10M", "B3610M": "ASME_B36_10M", "B36_10M": "ASME_B36_10M",
        "ASMEB3619M": "ASME_B36_19M", "B3619M": "ASME_B36_19M", "B36_19M": "ASME_B36_19M",
        "PVCEN1452": "PVC_EN1452", "EN1452": "PVC_EN1452", "PVCUEN1452": "PVC_EN1452",
        "PVCASTMD1785": "PVC_ASTMD1785", "ASTMD1785": "PVC_ASTMD1785", "PVCD1785": "PVC_ASTMD1785",
        "PEEN12201": "PE_EN12201", "EN12201": "PE_EN12201", "PE_EN12201": "PE_EN12201", "ISO4427": "PE_EN12201",
        "PPRISO15874": "PPR_ISO15874", "ISO15874": "PPR_ISO15874", "PPR_ISO15874": "PPR_ISO15874", "PPRC_EU": "PPR_ISO15874",
    }
    std_key = key_map.get(catalog_upper)
    if not std_key:
        raise DatasetMissingError(catalog, "Catalog not supported in this version")

    # Try YAML first
    yaml_data = _load_catalog_yaml(std_key)
    if yaml_data:
        return yaml_data

    # Fallback to hardcoded
    if std_key == "ASME_B36_10M":
        return B36_10M_WALLS, B36_10M_OD, B36_10M_NPS, "ASME_B36_10M", STEEL_DENSITY_KGM3
    if std_key == "ASME_B36_19M":
        return B36_19M_WALLS, B36_19M_OD, B36_10M_NPS, "ASME_B36_19M", STEEL_DENSITY_KGM3
    if std_key == "PVC_EN1452":
        return PVC_EN1452_WALLS, PVC_EN1452_OD, PVC_EN1452_NPS, "PVC_EN1452", PVC_DENSITY_KGM3
    if std_key == "PVC_ASTMD1785":
        return PVC_ASTMD1785_WALLS, PVC_ASTMD1785_OD, PVC_ASTMD1785_NPS, "PVC_ASTMD1785", PVC_DENSITY_KGM3
    if std_key == "PE_EN12201":
        return PE_EN12201_WALLS, PE_EN12201_OD, PE_EN12201_NPS, "PE_EN12201", PE_DENSITY_KGM3
    if std_key == "PPR_ISO15874":
        return PPR_ISO15874_WALLS, PPR_ISO15874_OD, PPR_ISO15874_NPS, "PPR_ISO15874", PPR_DENSITY_KGM3
        
    raise DatasetMissingError(catalog, "Catalog not supported in this version")


def get_pipe_dimension(
    catalog: str,
    DN_mm: float,
    schedule: str,
) -> PipeDimension:
    """Retorna dimensões do tubo para o catálogo, DN e schedule especificados."""
    schedule_upper = schedule.upper().replace(" ", "").replace("-", "")
    walls, od_map, nps_map, cat_name, density = _catalog_maps(catalog)

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
    weight = _pipe_weight_for_density_kgm(OD_mm, wt_mm, density)

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
    try:
        walls, _, _, _, _ = _catalog_maps(catalog)
    except DatasetMissingError:
        return []
    return list(walls.get(DN_mm, {}).keys())


def get_available_dns(catalog: str) -> list[float]:
    try:
        _, od_map, _, _, _ = _catalog_maps(catalog)
        return sorted(od_map.keys())
    except DatasetMissingError:
        pass
    return []


def find_minimum_schedule(
    catalog: str,
    DN_mm: float,
    min_wall_mm: float,
) -> Optional[PipeDimension]:
    """Encontra o schedule mais leve que satisfaz a espessura mínima requerida."""
    try:
        walls_db, od_map, nps_map, cat_name, density = _catalog_maps(catalog)
    except DatasetMissingError:
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
            weight = _pipe_weight_for_density_kgm(OD_mm, wt_mm, density)
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
