"""Provenance — rastreabilidade de dados técnicos."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DataSource:
    id: str
    title: str
    edition: str
    status: str   # public, licensed_required, public_reference, dataset_external
    notes: str = ""


@dataclass
class ProvenanceRecord:
    parameter: str
    value: object
    source: DataSource
    equation: str = ""
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "parameter": self.parameter,
            "value": self.value,
            "source_id": self.source.id,
            "source_title": self.source.title,
            "source_edition": self.source.edition,
            "equation": self.equation,
            "assumptions": self.assumptions,
        }


# Fontes conhecidas (subset público)
SOURCES = {
    "COOLPROP": DataSource(
        "COOLPROP", "CoolProp Property Library", "6.x",
        "public", "Open-source thermodynamic library"
    ),
    "DARCY_WEISBACH": DataSource(
        "DARCY_WEISBACH", "Darcy-Weisbach (domínio público)", "—",
        "public", "Equação fundamental de escoamento em pressão"
    ),
    "COLEBROOK_WHITE": DataSource(
        "COLEBROOK_WHITE", "Colebrook-White (domínio público)", "—",
        "public", "Factor de atrito Darcy para escoamento turbulento"
    ),
    "MANNING": DataSource(
        "MANNING", "Equação de Manning (domínio público)", "—",
        "public", "Escoamento gravitário em secção parcialmente cheia"
    ),
    "ASME_B36_10M": DataSource(
        "ASME_B36_10M", "ASME B36.10M", "2015",
        "public", "Catálogo dimensional tubos aço carbono — dados reproduzíveis"
    ),
    "ASME_B36_19M": DataSource(
        "ASME_B36_19M", "ASME B36.19M", "2004(R2015)",
        "public", "Catálogo dimensional tubos inox — dados reproduzíveis"
    ),
    "ASME_B31_3": DataSource(
        "ASME_B31_3", "ASME B31.3 Process Piping", "2022",
        "licensed_required",
        "Tensões admissíveis: subset de publicações públicas"
    ),
    "ASME_B31_9": DataSource(
        "ASME_B31_9", "ASME B31.9 Building Services Piping", "2022",
        "licensed_required",
        "Fórmula de espessura: equação pública. Tensões: subset público"
    ),
    "EN_13480": DataSource(
        "EN_13480", "EN 13480 Metallic Industrial Piping", "2017+A1:2020",
        "licensed_required",
        "Fórmula de espessura: equação pública. Tensões: subset público"
    ),
    "CRANE_TP410": DataSource(
        "CRANE_TP410", "Crane Technical Paper 410", "2013",
        "public_reference", "K-values para fittings e válvulas"
    ),
    "LITERATURE_STRESS": DataSource(
        "LITERATURE_STRESS", "Tensões admissíveis — literatura pública",
        "—", "public",
        "A106 GrB, A53 GrB, A312 TP304/316 — valores de referência pública"
    ),
}
