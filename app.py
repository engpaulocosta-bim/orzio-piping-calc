"""
Ponto de entrada SIDCT.

Desenvolvimento:
    streamlit run app.py

Executável portátil:
    O launcher.py (build_desktop/) invoca este ficheiro via Streamlit bootstrap.
"""
from __future__ import annotations
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_CANDIDATES = [ROOT / "src", ROOT]
APP_SCRIPT = next(
    (
        base / "sidct" / "ui" / "streamlit_app.py"
        for base in SRC_CANDIDATES
        if (base / "sidct" / "ui" / "streamlit_app.py").exists()
    ),
    SRC_CANDIDATES[0] / "sidct" / "ui" / "streamlit_app.py",
)

for src in reversed(SRC_CANDIDATES):
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))

# Este ficheiro é SEMPRE o script alvo do Streamlit (via `streamlit run app.py`
# ou via `bootstrap.run(app.py)` no launcher portátil). Importar a app com
# `from ... import *` é frágil porque o módulo pode ficar em cache entre reruns,
# deixando a sessão Streamlit sem deltas e a página em branco. Executar o ficheiro
# mantém o app.py como entrypoint, mas força a UI a correr em cada rerun.
runpy.run_path(str(APP_SCRIPT), run_name="__main__")
