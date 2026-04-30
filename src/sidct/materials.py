"""Material specifications and application rules for SIDCT."""
from __future__ import annotations

from dataclasses import dataclass, field

from .exceptions import DatasetMissingError, ValidationError, OutOfScopeError


@dataclass(frozen=True)
class MaterialSpec:
    key: str
    family: str
    grade: str
    region: str
    dimensional_catalog: str
    roughness_m: float
    density_kgm3: float
    temperature_min_c: float
    temperature_max_c: float
    pressure_rating_bar: float | None
    service_allowlist: tuple[str, ...]
    limitations: tuple[str, ...] = field(default_factory=tuple)


WATER_SERVICES = (
    "potable_water",
    "service_water",
    "osmotized_water",
    "chilled_water",
    "condenser_water",
    "sanitary_drainage",
    "rainwater",
)

METAL_SERVICES = (
    "compressed_air",
    "natural_gas",
    "potable_water",
    "service_water",
    "osmotized_water",
    "chilled_water",
    "condenser_water",
    "vacuum_utility",
    "sanitary_drainage",
    "rainwater",
    "fire_water",
)

MATERIAL_SPECS: dict[str, MaterialSpec] = {
    "A106GRB": MaterialSpec(
        key="A106GRB",
        family="carbon_steel",
        grade="ASTM A106 Grade B",
        region="global",
        dimensional_catalog="ASME_B36_10M",
        roughness_m=0.046e-3,
        density_kgm3=7850.0,
        temperature_min_c=-29.0,
        temperature_max_c=538.0,
        pressure_rating_bar=None,
        service_allowlist=METAL_SERVICES,
    ),
    "A53GRB": MaterialSpec(
        key="A53GRB",
        family="carbon_steel",
        grade="ASTM A53 Grade B",
        region="global",
        dimensional_catalog="ASME_B36_10M",
        roughness_m=0.046e-3,
        density_kgm3=7850.0,
        temperature_min_c=-20.0,
        temperature_max_c=370.0,
        pressure_rating_bar=None,
        service_allowlist=METAL_SERVICES,
    ),
    "A312TP304": MaterialSpec(
        key="A312TP304",
        family="stainless_steel",
        grade="ASTM A312 TP304",
        region="global",
        dimensional_catalog="ASME_B36_19M",
        roughness_m=0.015e-3,
        density_kgm3=8000.0,
        temperature_min_c=-196.0,
        temperature_max_c=540.0,
        pressure_rating_bar=None,
        service_allowlist=METAL_SERVICES,
    ),
    "A312TP316": MaterialSpec(
        key="A312TP316",
        family="stainless_steel",
        grade="ASTM A312 TP316",
        region="global",
        dimensional_catalog="ASME_B36_19M",
        roughness_m=0.015e-3,
        density_kgm3=8000.0,
        temperature_min_c=-196.0,
        temperature_max_c=540.0,
        pressure_rating_bar=None,
        service_allowlist=METAL_SERVICES,
    ),
    "PVCU_EU": MaterialSpec(
        key="PVCU_EU",
        family="pvc",
        grade="PVC-U EN/ISO pressure pipe",
        region="EU",
        dimensional_catalog="PVC_EN1452",
        roughness_m=0.0015e-3,
        density_kgm3=1400.0,
        temperature_min_c=0.0,
        temperature_max_c=60.0,
        pressure_rating_bar=16.0,
        service_allowlist=WATER_SERVICES,
        limitations=(
            "PVC-U dataset is for water and drainage services only.",
            "Do not use for compressed air, natural gas, vacuum or fire-water approval.",
            "Temperature derating must be checked for final design above 20 C.",
        ),
    ),
    "PVCU_US": MaterialSpec(
        key="PVCU_US",
        family="pvc",
        grade="PVC-U ASTM D1785",
        region="US",
        dimensional_catalog="PVC_ASTMD1785",
        roughness_m=0.0015e-3,
        density_kgm3=1400.0,
        temperature_min_c=0.0,
        temperature_max_c=60.0,
        pressure_rating_bar=16.0,
        service_allowlist=WATER_SERVICES,
        limitations=(
            "PVC-U dataset is for water and drainage services only.",
            "ASTM schedule pressure rating varies with DN and temperature.",
            "Do not use for compressed air, natural gas, vacuum or fire-water approval.",
        ),
    ),
}

ALIASES: dict[str, str] = {
    "A106B": "A106GRB",
    "A106GRB": "A106GRB",
    "A106GR.B": "A106GRB",
    "A53B": "A53GRB",
    "A53GRB": "A53GRB",
    "A53GR.B": "A53GRB",
    "TP304": "A312TP304",
    "304": "A312TP304",
    "A312TP304": "A312TP304",
    "TP316": "A312TP316",
    "316": "A312TP316",
    "316L": "A312TP316",
    "A312TP316": "A312TP316",
    "PVC": "PVCU_EU",
    "PVCU": "PVCU_EU",
    "PVC-U": "PVCU_EU",
    "PVCUEU": "PVCU_EU",
    "PVCUS": "PVCU_US",
    "PVCUUS": "PVCU_US",
}


def normalize_jurisdiction(jurisdiction: str = "EU") -> str:
    value = (jurisdiction or "EU").strip().upper().replace(" ", "_").replace("-", "_")
    if value in {"US", "USA", "UNITED_STATES", "UNITED_STATES_OF_AMERICA"}:
        return "US"
    if value in {"BR", "BRAZIL", "BRASIL"}:
        return "BRAZIL"
    if value in {"EU", "EUROPE", "EN", "CEE"}:
        return "EU"
    if value in {"INT", "INTERNATIONAL", "GLOBAL"}:
        return "INTERNATIONAL"
    return value


def normalize_material_key(material: str, jurisdiction: str = "EU") -> str:
    raw = material.strip().upper()
    compact = raw.replace(" ", "").replace("-", "").replace(".", "").replace("_", "")
    region = normalize_jurisdiction(jurisdiction)
    if compact in ("PVC", "PVCU") and region == "US":
        return "PVCU_US"
    if compact in ("PVC", "PVCU") and region in {"BRAZIL", "INTERNATIONAL"}:
        return "PVCU_UNSUPPORTED"
    return ALIASES.get(raw, ALIASES.get(compact, compact))


def get_material_spec(material: str, jurisdiction: str = "EU") -> MaterialSpec | None:
    return MATERIAL_SPECS.get(normalize_material_key(material, jurisdiction))


def is_pvc_material(material: str) -> bool:
    return normalize_material_key(material).startswith("PVCU")


def catalog_region(catalog: str) -> str:
    normalized = (catalog or "").upper().replace(".", "").replace("-", "").replace("_", "")
    if normalized in {"PVCEN1452", "EN1452", "PVCUEN1452"}:
        return "EU"
    if normalized in {"PVCASTMD1785", "ASTMD1785", "PVCD1785"}:
        return "US"
    if normalized in {"NBR5580"}:
        return "BRAZIL"
    if normalized in {"ASMEB3610M", "B3610M", "B36_10M", "ASMEB3619M", "B3619M", "B36_19M"}:
        return "GLOBAL"
    return "UNKNOWN"


def available_catalogs_for_material(material: str, jurisdiction: str = "EU") -> list[str]:
    spec = get_material_spec(material, jurisdiction)
    if spec is None:
        return []
    if spec.family == "pvc":
        return [spec.dimensional_catalog]
    if spec.family == "stainless_steel":
        return ["ASME_B36_19M"]
    if spec.family == "carbon_steel":
        return ["ASME_B36_10M"]
    return [spec.dimensional_catalog]


def default_catalog_for_material(material: str, jurisdiction: str = "EU") -> str | None:
    spec = get_material_spec(material, jurisdiction)
    return spec.dimensional_catalog if spec else None


def validate_catalog_for_material(material: str, catalog: str, jurisdiction: str = "EU") -> list[str]:
    """Validate that a dimensional catalog belongs to the selected jurisdiction."""
    warnings: list[str] = []
    region = normalize_jurisdiction(jurisdiction)
    material_key = normalize_material_key(material, jurisdiction)
    spec = MATERIAL_SPECS.get(material_key)
    cat_region = catalog_region(catalog)

    if material_key == "PVCU_UNSUPPORTED":
        raise DatasetMissingError(
            f"PVC-U:{region}",
            f"PVC-U catalog for jurisdiction '{jurisdiction}' is not implemented in SIDCT. "
            "Use a project-approved local catalog or choose a supported region/material.",
        )
    if spec is None:
        return warnings

    if cat_region == "UNKNOWN":
        return warnings
    if spec.family == "pvc" and cat_region == "GLOBAL":
        warnings.append(
            f"Material PVC selected with steel catalog '{catalog}'; SIDCT will use "
            f"'{spec.dimensional_catalog}' for jurisdiction '{jurisdiction}' during calculation."
        )
        return warnings
    if spec.family == "pvc" and cat_region != spec.region:
        raise ValidationError(
            f"Catalog '{catalog}' belongs to region '{cat_region}' and cannot be used with "
            f"PVC material '{material}' in jurisdiction '{jurisdiction}'.",
            "dimensional_catalog",
        )
    if cat_region != "GLOBAL" and cat_region != region:
        raise ValidationError(
            f"Catalog '{catalog}' is restricted to region '{cat_region}' and cannot be used "
            f"for jurisdiction '{jurisdiction}'.",
            "dimensional_catalog",
        )
    if region in {"EU", "BRAZIL", "INTERNATIONAL"} and cat_region == "GLOBAL":
        warnings.append(
            f"Catalog '{catalog}' is a global/ASME dimensional dataset in SIDCT; verify the "
            f"project specification and local acceptance for jurisdiction '{jurisdiction}'."
        )
    return warnings


def resolve_catalog(material: str, requested_catalog: str, jurisdiction: str = "EU") -> tuple[str, list[str]]:
    """Return the catalog to use and warnings about any automatic correction."""
    warnings: list[str] = []
    spec = get_material_spec(material, jurisdiction)
    if spec is None:
        material_key = normalize_material_key(material, jurisdiction)
        if material_key == "PVCU_UNSUPPORTED":
            validate_catalog_for_material(material, requested_catalog, jurisdiction)
        return requested_catalog, warnings

    requested = requested_catalog.upper()
    if spec.family == "pvc" and requested in {"ASME_B36_10M", "ASME_B36_19M", "B36_10M", "B36_19M"}:
        warnings.append(
            f"Material PVC selected with steel catalog '{requested_catalog}'. "
            f"Using '{spec.dimensional_catalog}' for jurisdiction {jurisdiction}."
        )
        return spec.dimensional_catalog, warnings
    warnings.extend(validate_catalog_for_material(material, requested_catalog, jurisdiction))
    return requested_catalog, warnings


def validate_material_application(
    material: str,
    service: str,
    T_design_c: float,
    P_design_bar: float,
    jurisdiction: str = "EU",
) -> list[str]:
    spec = get_material_spec(material, jurisdiction)
    if spec is None:
        if normalize_material_key(material, jurisdiction) == "PVCU_UNSUPPORTED":
            raise DatasetMissingError(
                f"PVC-U:{normalize_jurisdiction(jurisdiction)}",
                f"PVC-U catalog for jurisdiction '{jurisdiction}' is not implemented in SIDCT.",
            )
        return []

    warnings: list[str] = []
    warnings.extend(validate_catalog_for_material(material, spec.dimensional_catalog, jurisdiction))
    if service not in spec.service_allowlist:
        raise ValidationError(
            f"Material '{material}' is not suitable for service '{service}' in the current SIDCT dataset.",
            "material",
        )
    if T_design_c < spec.temperature_min_c or T_design_c > spec.temperature_max_c:
        raise OutOfScopeError(
            f"Material '{material}' outside supported temperature envelope "
            f"[{spec.temperature_min_c}, {spec.temperature_max_c}] C",
            "T_design_c",
            T_design_c,
            f"[{spec.temperature_min_c}, {spec.temperature_max_c}]",
        )
    if spec.pressure_rating_bar is not None and P_design_bar > spec.pressure_rating_bar:
        raise OutOfScopeError(
            f"P_design {P_design_bar} barg exceeds dataset pressure rating "
            f"{spec.pressure_rating_bar} barg for material '{material}'",
            "P_design_bar",
            P_design_bar,
            spec.pressure_rating_bar,
        )
    if spec.family == "pvc" and T_design_c > 20.0:
        warnings.append(
            "PVC pressure rating requires temperature derating above 20 C; "
            "verify manufacturer table for final design."
        )
    warnings.extend(spec.limitations)
    return warnings


def list_material_specs() -> list[MaterialSpec]:
    return sorted(MATERIAL_SPECS.values(), key=lambda item: (item.family, item.key))
