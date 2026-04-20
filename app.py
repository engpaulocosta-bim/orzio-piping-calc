"""SIDCT — Entry point. Launches the Streamlit application."""
import sys
from pathlib import Path

# Adicionar pasta src ao PYTHONPATH para que 'sidct' seja importável
src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Caminho real para a aplicação Streamlit
app_path = src_path / "sidct" / "ui" / "streamlit_app.py"

# Customizar o namespace para que __file__ aponte para o app interno
namespace = globals().copy()
namespace["__file__"] = str(app_path)

# Executar o script do Streamlit no namespace preparado
with open(app_path, "rb") as f:
    exec(compile(f.read(), str(app_path), "exec"), namespace)
