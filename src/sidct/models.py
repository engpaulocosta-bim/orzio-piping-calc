"""Modelos de dados do sistema SIDCT (Pydantic v2)."""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator


class FittingItem(BaseModel):
    fitting_type: str
    quantity: int = 1
    k_value: Optional[float] = None   # None → usar catálogo


class ValveItem(BaseModel):
    valve_type: str
    quantity: int = 1
    k_value: Optional[float] = None


class LineInput(BaseModel):
    project_name: str
    line_tag: str
    service: str
    project_profile: str
    jurisdiction: str = "EU"
    fluid_name: str

    # Pressão e temperatura de operação
    P_oper_bar: float = Field(..., description="Pressão de operação [barg]")
    T_oper_c: float = Field(..., description="Temperatura de operação [°C]")
    P_design_bar: float = Field(..., description="Pressão de projeto [barg]")
    T_design_c: float = Field(..., description="Temperatura de projeto [°C]")

    # Caudal
    flow_rate: float = Field(..., description="Caudal de processo")
    flow_rate_basis: str = Field("m3/h", description="Unidade do caudal")

    # Geometria
    line_length_m: float = Field(..., description="Comprimento total [m]")
    elevation_delta_m: float = Field(0.0, description="Diferença de elevação [m] (positivo = subida)")

    # Material e catálogo
    material: str = Field(..., description="Material do tubo (ex: A106 GrB)")
    dimensional_catalog: str = Field("ASME_B36_10M")
    design_code: Optional[str] = None  # None → deriva do perfil

    # Corrosão e rugosidade
    corrosion_allowance_mm: Optional[float] = None  # None → default do perfil
    roughness_m: Optional[float] = None  # None → default do material

    # Isolação
    insulation_thickness_mm: float = 0.0
    insulation_density_kgm3: float = 100.0

    # Fittings e válvulas
    fittings: list[FittingItem] = Field(default_factory=list)
    valves: list[ValveItem] = Field(default_factory=list)

    # Critério de queda de pressão
    allowable_pressure_drop_bar: Optional[float] = None
    required_residual_pressure_bar: Optional[float] = None

    # Conferência (check mode)
    DN_received_mm: Optional[float] = None
    schedule_or_wall_received: Optional[str] = None

    # Gravidade
    slope_mm_m: Optional[float] = None  # mm/m (obrigatório para gravity)

    # Vácuo
    vacuum_target_mbara: Optional[float] = None  # mbar abs

    # Notas
    design_notes: str = ""
    operation_mode: str = "calculate_new"

    @model_validator(mode="after")
    def check_regime_requirements(self) -> "LineInput":
        from .enums import Service, ProjectProfile

        # Validar service contra enum (B5)
        valid_services = {e.value for e in Service}
        if self.service not in valid_services:
            raise ValueError(
                f"Serviço '{self.service}' inválido. "
                f"Serviços suportados: {sorted(valid_services)}"
            )

        # Validar project_profile contra enum (B5)
        valid_profiles = {e.value for e in ProjectProfile}
        if self.project_profile not in valid_profiles:
            raise ValueError(
                f"Perfil '{self.project_profile}' inválido. "
                f"Perfis suportados: {sorted(valid_profiles)}"
            )

        svc = self.service
        if svc in (Service.SANITARY_DRAINAGE, Service.RAINWATER):
            if self.slope_mm_m is None:
                raise ValueError(f"'slope_mm_m' é obrigatório para serviço gravitário '{svc}'")
        if svc == Service.VACUUM_UTILITY:
            if self.vacuum_target_mbara is None:
                raise ValueError("'vacuum_target_mbara' é obrigatório para vacuum_utility")
        return self


class FluidProperties(BaseModel):
    fluid_name: str
    T_K: float
    P_pa: float
    rho_kgm3: float
    mu_pas: float
    cp_jkgk: Optional[float] = None
    conductivity_wm_k: Optional[float] = None
    compressibility_z: float = 1.0
    molecular_weight_kgkmol: Optional[float] = None
    gamma: Optional[float] = None  # Cp/Cv
    source: str = "CoolProp"
    warnings: list[str] = Field(default_factory=list)
    assumptions_used: list[str] = Field(default_factory=list)


class PipeDimension(BaseModel):
    catalog: str
    DN_mm: float
    NPS_inch: float
    OD_mm: float
    wall_thickness_mm: float
    schedule: str
    ID_mm: float
    weight_kgm: float

    @property
    def OD_m(self) -> float:
        return self.OD_mm / 1000.0

    @property
    def ID_m(self) -> float:
        return self.ID_mm / 1000.0

    @property
    def wall_m(self) -> float:
        return self.wall_thickness_mm / 1000.0


class HydraulicResult(BaseModel):
    regime: str
    service: str
    line_tag: str

    # Resultados principais
    velocity_ms: Optional[float] = None
    Re: Optional[float] = None
    friction_factor: Optional[float] = None
    dp_major_pa: Optional[float] = None
    dp_minor_pa: Optional[float] = None
    dp_total_pa: Optional[float] = None
    dp_total_bar: Optional[float] = None
    head_loss_m: Optional[float] = None

    # Seleção de DN
    DN_by_velocity_mm: Optional[float] = None
    DN_by_pressure_drop_mm: Optional[float] = None
    DN_governing_mm: Optional[float] = None
    governing_criterion: Optional[str] = None

    # Gravidade
    flow_depth_ratio: Optional[float] = None
    slope_adequacy: Optional[str] = None
    self_cleansing_ok: Optional[bool] = None

    # Compressível
    mach_number: Optional[float] = None
    pressure_ratio: Optional[float] = None
    compressible_model_valid: Optional[bool] = None

    # Vácuo
    conductance_result: Optional[dict] = None

    # Metadados
    status: str = "CALCULATED"
    warnings: list[str] = Field(default_factory=list)
    assumptions_used: list[str] = Field(default_factory=list)
    pipe_used: Optional[PipeDimension] = None


class ThicknessResult(BaseModel):
    line_tag: str
    design_code: str
    material: str

    t_pressure_only_mm: Optional[float] = None
    t_plus_ca_mm: Optional[float] = None
    t_after_mill_tolerance_mm: Optional[float] = None
    selected_wall_mm: Optional[float] = None
    selected_schedule: Optional[str] = None
    allowable_stress_mpa: Optional[float] = None
    E_factor: Optional[float] = None
    Y_factor: Optional[float] = None
    corrosion_allowance_mm: Optional[float] = None
    mill_tolerance_pct: Optional[float] = None
    governing_code: Optional[str] = None
    governing_clause: Optional[str] = None

    status: str = "CALCULATED"
    warnings: list[str] = Field(default_factory=list)
    assumptions_used: list[str] = Field(default_factory=list)


class ExternalPressureResult(BaseModel):
    line_tag: str
    P_external_design_bar: Optional[float] = None
    P_allow_bar: Optional[float] = None
    utilization_ratio: Optional[float] = None
    collapse_warning: Optional[str] = None
    method_status: str = "DATASET_MISSING"
    required_additional_data: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SupportResult(BaseModel):
    line_tag: str
    weight_pipe_kgm: Optional[float] = None
    weight_fluid_kgm: Optional[float] = None
    weight_insulation_kgm: Optional[float] = None
    total_weight_kgm: Optional[float] = None
    L_max_m: Optional[float] = None
    deflection_governing: Optional[str] = None
    seismic_horizontal_kN: Optional[float] = None
    classification_level: str = "PRELIMINARY"
    warnings: list[str] = Field(default_factory=list)
    assumptions_used: list[str] = Field(default_factory=list)


class CheckerResult(BaseModel):
    line_tag: str
    operation_mode: str

    overall_status: str = "DATASET_MISSING"
    hydraulic_status: Optional[str] = None
    thickness_status: Optional[str] = None
    external_pressure_status: Optional[str] = None

    hydraulic_margin_pct: Optional[float] = None
    thickness_margin_pct: Optional[float] = None
    external_margin_pct: Optional[float] = None
    overall_governing_margin_pct: Optional[float] = None
    governing_issue: Optional[str] = None

    DN_required_mm: Optional[float] = None
    DN_received_mm: Optional[float] = None
    wall_required_mm: Optional[float] = None
    wall_received_mm: Optional[float] = None

    dataset_missing_items: list[str] = Field(default_factory=list)
    out_of_scope_items: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CitationItem(BaseModel):
    standard_id: str
    edition: str
    clause: str
    description: str
    equation_used: Optional[str] = None


class WarningItem(BaseModel):
    code: str
    severity: str  # INFO, WARNING, CRITICAL
    message: str
    module: str
    assumption_id: Optional[str] = None


class ReportContext(BaseModel):
    project_name: str
    line_tag: str
    prepared_by: str = "SIDCT v1.0"
    date: str = ""
    revision: str = "A"

    line_input: Optional[LineInput] = None
    fluid_properties: Optional[FluidProperties] = None
    hydraulic_result: Optional[HydraulicResult] = None
    thickness_result: Optional[ThicknessResult] = None
    external_pressure_result: Optional[ExternalPressureResult] = None
    support_result: Optional[SupportResult] = None
    checker_result: Optional[CheckerResult] = None

    citations: list[CitationItem] = Field(default_factory=list)
    warnings: list[WarningItem] = Field(default_factory=list)
    assumptions_declared: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    dataset_provenance: dict[str, Any] = Field(default_factory=dict)
    profile_used: Optional[dict] = None


class BatchRowResult(BaseModel):
    row_index: int
    line_tag: str
    status: str
    governing_issue: Optional[str] = None
    dataset_missing: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    warnings_count: int = 0
    error_message: Optional[str] = None
    report_context: Optional[ReportContext] = None
