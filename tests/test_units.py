"""Testes unitários — conversão de unidades."""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sidct.units import (
    bar_to_pa, pa_to_bar, celsius_to_kelvin, kelvin_to_celsius,
    barg_to_pa_abs, inch_to_mm, m3h_to_m3s, ls_to_m3s, gpm_to_m3s,
    nm3h_to_m3s_at_tp, P_ATM_PA
)


def test_bar_to_pa():
    assert abs(bar_to_pa(1.0) - 1e5) < 1.0

def test_pa_to_bar():
    assert abs(pa_to_bar(1e5) - 1.0) < 1e-6

def test_celsius_to_kelvin():
    assert abs(celsius_to_kelvin(0.0) - 273.15) < 1e-6
    assert abs(celsius_to_kelvin(100.0) - 373.15) < 1e-6

def test_kelvin_to_celsius():
    assert abs(kelvin_to_celsius(273.15) - 0.0) < 1e-6

def test_barg_to_pa_abs():
    # 0 barg = P_atm
    assert abs(barg_to_pa_abs(0.0) - P_ATM_PA) < 1.0

def test_inch_to_mm():
    assert abs(inch_to_mm(1.0) - 25.4) < 1e-6

def test_m3h_to_m3s():
    assert abs(m3h_to_m3s(3600.0) - 1.0) < 1e-6

def test_ls_to_m3s():
    assert abs(ls_to_m3s(1000.0) - 1.0) < 1e-6

def test_gpm_to_m3s():
    # 1 gpm ≈ 6.309e-5 m³/s
    assert abs(gpm_to_m3s(1.0) - 6.30902e-5) < 1e-8

def test_nm3h_to_m3s():
    # 3600 Nm³/h @ 0°C, 1 atm = 1 m³/s (condições normais)
    v = nm3h_to_m3s_at_tp(3600.0, 273.15, 101325.0)
    assert abs(v - 1.0) < 1e-4

def test_roundtrip_pressure():
    for p in [0.1, 1.0, 10.0, 100.0]:
        assert abs(pa_to_bar(bar_to_pa(p)) - p) < 1e-9
