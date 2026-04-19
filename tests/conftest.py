"""Configuração pytest — SIDCT."""
import sys
from pathlib import Path

# Garante que src está no path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
