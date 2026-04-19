"""Propriedades de fluidos — CoolProp + aproximações documentadas.

Hierarquia:
1. CoolProp quando disponível para o fluido e condições
2. Aproximações de literatura pública, com warning declarado
3. Erro com DATASET_MISSING se nem CoolProp nem aproximação válida
"""
from __future__ import annotations
import logging
from ..models import FluidProperties
from ..units import celsius_to_kelvin, bar_to_pa, barg_to_pa_abs, P_ATM_PA

logger = logging.getLogger("sidct.fluid_properties")

# Mapeamento serviço → nome CoolProp
_COOLPROP_MAP: dict[str, str] = {
    "compressed_air": "Air",
    "natural_gas": "Methane",  # aproximação CH4
    "potable_water": "Water",
    "service_water": "Water",
    "osmotized_water": "Water",
    "chilled_water": "Water",
    "condenser_water": "Water",
    "vacuum_utility": "Air",
    "sanitary_drainage": "Water",
    "rainwater": "Water",
    "fire_water": "Water",
}


def _get_coolprop_props(fluid_cp: str, T_K: float, P_pa: float) -> dict:
    """Tenta obter propriedades via CoolProp."""
    try:
        import CoolProp.CoolProp as CP
        rho = CP.PropsSI("D", "T", T_K, "P", P_pa, fluid_cp)
        mu = CP.PropsSI("V", "T", T_K, "P", P_pa, fluid_cp)
        cp = CP.PropsSI("C", "T", T_K, "P", P_pa, fluid_cp)
        k = CP.PropsSI("L", "T", T_K, "P", P_pa, fluid_cp)
        mw = CP.PropsSI("M", fluid_cp) * 1000.0  # kg/kmol
        gamma = None
        try:
            cp_val = CP.PropsSI("C", "T", T_K, "P", P_pa, fluid_cp)
            cv_val = CP.PropsSI("O", "T", T_K, "P", P_pa, fluid_cp)
            gamma = cp_val / cv_val if cv_val > 0 else None
        except Exception:
            pass
        return {
            "rho": rho, "mu": mu, "cp": cp, "k": k,
            "mw": mw, "gamma": gamma, "source": "CoolProp",
            "warnings": [],
        }
    except Exception as e:
        logger.debug(f"CoolProp falhou para {fluid_cp} @ T={T_K}K P={P_pa}Pa: {e}")
        return {}


def _water_approximation(T_K: float) -> dict:
    """Propriedades de água limpa — aproximação polinomial (erro < 2% em [0, 100]°C)."""
    T_c = T_K - 273.15
    T_c = max(1.0, min(T_c, 99.0))
    rho = 999.84 - 0.0623 * T_c - 0.003711 * T_c**2
    mu = 2.414e-5 * 10 ** (247.8 / (T_K - 140.0))
    cp = 4186.0
    k = 0.5918 + 1.5e-3 * T_c - 2.5e-6 * T_c**2
    return {
        "rho": rho, "mu": mu, "cp": cp, "k": k,
        "mw": 18.015, "gamma": None,
        "source": "polynomial_approximation",
        "warnings": ["Propriedades de água calculadas por aproximação polinomial (erro < 2% em [0,100]°C)"],
    }


def _air_approximation(T_K: float, P_pa: float) -> dict:
    """Propriedades de ar — gás ideal (adequado para P < 20 bar)."""
    R_air = 287.058  # J/(kg·K)
    gamma = 1.4
    cp = 1005.0
    rho = P_pa / (R_air * T_K)
    # Sutherland's law para viscosidade
    T_ref = 291.15
    mu_ref = 1.827e-5
    C = 120.0
    mu = mu_ref * (T_K / T_ref) ** 1.5 * (T_ref + C) / (T_K + C)
    k = 0.02624 * (T_K / 300.0) ** 0.8646
    return {
        "rho": rho, "mu": mu, "cp": cp, "k": k,
        "mw": 28.966, "gamma": gamma,
        "source": "ideal_gas_sutherland",
        "warnings": ["Ar modelado como gás ideal (lei de Sutherland para viscosidade)"],
    }


def _methane_approximation(T_K: float, P_pa: float) -> dict:
    """CH4 puro — gás ideal (aproximação para gás natural sem composição)."""
    R_ch4 = 518.28  # J/(kg·K)
    gamma = 1.31
    cp = 2220.0
    rho = P_pa / (R_ch4 * T_K)
    mu = 1.1e-5 * (T_K / 293.15) ** 0.8
    k = 0.034 * (T_K / 293.15) ** 0.85
    return {
        "rho": rho, "mu": mu, "cp": cp, "k": k,
        "mw": 16.043, "gamma": gamma,
        "source": "ideal_gas_ch4_approximation",
        "warnings": [
            "Gás natural modelado como CH4 puro (ideal gas) — composição não fornecida",
            "Para gas com C2+ > 5% ou alto conteúdo de inerte: fornecer propriedades reais",
        ],
    }


def get_fluid_properties(
    service: str,
    T_oper_c: float,
    P_oper_barg: float,
    fluid_name: str | None = None,
) -> FluidProperties:
    """Retorna propriedades do fluido para o serviço e condições de operação."""
    T_K = celsius_to_kelvin(T_oper_c)
    P_pa = barg_to_pa_abs(P_oper_barg)

    cp_fluid = _COOLPROP_MAP.get(service)
    warnings: list[str] = []
    assumptions: list[str] = []
    props: dict = {}

    # 1. Tentar CoolProp
    if cp_fluid:
        props = _get_coolprop_props(cp_fluid, T_K, P_pa)

    # 2. Fallback por serviço
    if not props:
        if service in ("potable_water", "service_water", "osmotized_water",
                       "chilled_water", "condenser_water", "sanitary_drainage",
                       "rainwater", "fire_water"):
            props = _water_approximation(T_K)
            assumptions.append("A-HG-003")
        elif service == "compressed_air":
            props = _air_approximation(T_K, P_pa)
            assumptions.append("A-HC-003")
        elif service == "natural_gas":
            props = _methane_approximation(T_K, P_pa)
            assumptions.append("A-HC-002")
        elif service == "vacuum_utility":
            props = _air_approximation(T_K, P_pa)
        else:
            from ..exceptions import DatasetMissingError
            raise DatasetMissingError(
                f"fluid_properties:{service}",
                f"Sem propriedades disponíveis para serviço '{service}'"
            )

    warnings.extend(props.get("warnings", []))

    # Natural gas: sempre emitir warning de CH4 (independente da fonte)
    if service == "natural_gas":
        if not any("CH4" in w for w in warnings):
            warnings.append(
                "Gás natural modelado como CH4 puro — composição não fornecida. "
                "Para gas com C2+ > 5% ou alto conteúdo de inerte: fornecer propriedades reais."
            )
        assumptions.append("A-HC-002")

    # Warnings adicionais
    if service == "chilled_water" and T_oper_c < 4.0:
        warnings.append(f"T_oper {T_oper_c}°C próxima do ponto de congelamento — verificar solução anticongelante")
    if service == "compressed_air" and P_oper_barg > 20.0:
        warnings.append("P_oper > 20 barg — verificar validade de gás ideal para ar comprimido")

    # Compressibilidade
    z = 1.0
    if service in ("compressed_air", "natural_gas"):
        z_note = "Z ≈ 1.0 (gás ideal)"
        if P_oper_barg > 50:
            z_note = "Z ≈ 1.0 (assumido — a P > 50 barg z pode diferir de 1)"
            warnings.append("P > 50 barg — factor de compressibilidade Z assumido 1.0 (pode requerer Peng-Robinson)")
    else:
        z_note = "N/A (líquido)"

    return FluidProperties(
        fluid_name=fluid_name or service,
        T_K=T_K,
        P_pa=P_pa,
        rho_kgm3=props["rho"],
        mu_pas=props["mu"],
        cp_jkgk=props.get("cp"),
        conductivity_wm_k=props.get("k"),
        compressibility_z=z,
        molecular_weight_kgkmol=props.get("mw"),
        gamma=props.get("gamma"),
        source=props["source"],
        warnings=warnings,
        assumptions_used=assumptions,
    )
