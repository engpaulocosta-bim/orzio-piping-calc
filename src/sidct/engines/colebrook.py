"""Colebrook-White — módulo partilhado para factor de atrito Darcy.

Usado por: hydraulic_incompressible, hydraulic_compressible.
Fonte: Colebrook & White (1937) — equação de domínio público.
"""
from __future__ import annotations
import math
from ..exceptions import ConvergenceError

_MAX_ITER = 200
_TOL = 1e-8


def colebrook_white(Re: float, eps_D: float) -> float:
    """Resolve Colebrook-White para f (factor Darcy). Iteração Newton-Raphson.

    Retorna factor de atrito de Darcy.
    Lança ConvergenceError se não convergir em _MAX_ITER iterações.
    """
    if Re <= 0:
        raise ValueError(f"Reynolds deve ser > 0, recebido Re={Re}")

    if Re < 2300:
        return 64.0 / Re  # Hagen-Poiseuille (laminar)

    # Estimativa inicial Swamee-Jain
    f = 0.25 / (math.log10(eps_D / 3.7 + 5.74 / Re**0.9))**2

    for _ in range(_MAX_ITER):
        lhs = -2.0 * math.log10(eps_D / 3.7 + 2.51 / (Re * math.sqrt(f)))
        f_new = (1.0 / lhs)**2
        if abs(f_new - f) < _TOL:
            return f_new
        f = f_new

    raise ConvergenceError("Colebrook-White", _MAX_ITER, _TOL)
