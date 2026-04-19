"""Conversão de unidades — todas as conversões rastreáveis e nomeadas."""
from __future__ import annotations


# ──── Pressão ─────────────────────────────────────────────────────────────────
def bar_to_pa(bar: float) -> float:
    return bar * 1e5

def pa_to_bar(pa: float) -> float:
    return pa / 1e5

def barg_to_pa_abs(barg: float, p_atm_bar: float = 1.01325) -> float:
    return bar_to_pa(barg + p_atm_bar)

def pa_abs_to_barg(pa_abs: float, p_atm_bar: float = 1.01325) -> float:
    return pa_to_bar(pa_abs) - p_atm_bar

def psi_to_pa(psi: float) -> float:
    return psi * 6894.757

def pa_to_psi(pa: float) -> float:
    return pa / 6894.757

def psig_to_pa_abs(psig: float, p_atm_bar: float = 1.01325) -> float:
    return psi_to_pa(psig) + bar_to_pa(p_atm_bar)

def mpa_to_pa(mpa: float) -> float:
    return mpa * 1e6

def pa_to_mpa(pa: float) -> float:
    return pa / 1e6

def kpa_to_pa(kpa: float) -> float:
    return kpa * 1e3

def pa_to_kpa(pa: float) -> float:
    return pa / 1e3


# ──── Temperatura ──────────────────────────────────────────────────────────────
def celsius_to_kelvin(tc: float) -> float:
    return tc + 273.15

def kelvin_to_celsius(tk: float) -> float:
    return tk - 273.15

def fahrenheit_to_kelvin(tf: float) -> float:
    return (tf - 32) * 5 / 9 + 273.15

def kelvin_to_fahrenheit(tk: float) -> float:
    return (tk - 273.15) * 9 / 5 + 32


# ──── Comprimento / Diâmetro ──────────────────────────────────────────────────
def mm_to_m(mm: float) -> float:
    return mm / 1000.0

def m_to_mm(m: float) -> float:
    return m * 1000.0

def inch_to_m(inch: float) -> float:
    return inch * 0.0254

def m_to_inch(m: float) -> float:
    return m / 0.0254

def inch_to_mm(inch: float) -> float:
    return inch * 25.4

def mm_to_inch(mm: float) -> float:
    return mm / 25.4


# ──── Caudal volumétrico ───────────────────────────────────────────────────────
def m3h_to_m3s(m3h: float) -> float:
    return m3h / 3600.0

def m3s_to_m3h(m3s: float) -> float:
    return m3s * 3600.0

def ls_to_m3s(ls: float) -> float:
    return ls / 1000.0

def m3s_to_ls(m3s: float) -> float:
    return m3s * 1000.0

def gpm_to_m3s(gpm: float) -> float:
    return gpm * 6.30902e-5

def m3s_to_gpm(m3s: float) -> float:
    return m3s / 6.30902e-5

def nm3h_to_m3s_at_tp(nm3h: float, T_K: float, P_pa: float,
                       T_n_K: float = 273.15, P_n_pa: float = 101325.0) -> float:
    """Converte Nm³/h (0°C, 1 atm) para m³/s às condições (T_K, P_pa)."""
    if P_pa <= 0:
        raise ValueError(f"P_pa deve ser > 0 para conversão Nm³/h, recebido {P_pa}")
    if T_K <= 0:
        raise ValueError(f"T_K deve ser > 0 para conversão Nm³/h, recebido {T_K}")
    m3s_normal = nm3h / 3600.0
    return m3s_normal * (T_K / T_n_K) * (P_n_pa / P_pa)

def sm3h_to_m3s_at_tp(sm3h: float, T_K: float, P_pa: float,
                       T_s_K: float = 288.15, P_s_pa: float = 101325.0) -> float:
    """Converte Sm³/h (15°C, 1 atm) para m³/s às condições (T_K, P_pa)."""
    if P_pa <= 0:
        raise ValueError(f"P_pa deve ser > 0 para conversão Sm³/h, recebido {P_pa}")
    if T_K <= 0:
        raise ValueError(f"T_K deve ser > 0 para conversão Sm³/h, recebido {T_K}")
    m3s_standard = sm3h / 3600.0
    return m3s_standard * (T_K / T_s_K) * (P_s_pa / P_pa)


# ──── Massa ────────────────────────────────────────────────────────────────────
def kg_to_lb(kg: float) -> float:
    return kg * 2.20462

def lb_to_kg(lb: float) -> float:
    return lb / 2.20462


# ──── Velocidade ───────────────────────────────────────────────────────────────
def fts_to_ms(fts: float) -> float:
    return fts * 0.3048

def ms_to_fts(ms: float) -> float:
    return ms / 0.3048


# ──── Tensão / Stress ──────────────────────────────────────────────────────────
def ksi_to_pa(ksi: float) -> float:
    return ksi * 6.89476e6

def pa_to_ksi(pa: float) -> float:
    return pa / 6.89476e6

def mpa_to_ksi(mpa: float) -> float:
    return mpa / 6.89476

def ksi_to_mpa(ksi: float) -> float:
    return ksi * 6.89476


# ──── Constantes ────────────────────────────────────────────────────────────────
P_ATM_PA: float = 101325.0    # Pa
P_ATM_BAR: float = 1.01325    # bar
T_0_K: float = 273.15         # K (0°C)
T_STD_K: float = 288.15       # K (15°C)
G_GRAVITY: float = 9.80665    # m/s²
R_UNIVERSAL: float = 8.31446  # J/(mol·K)
