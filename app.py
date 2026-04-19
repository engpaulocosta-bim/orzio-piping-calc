"""SIDCT — Entry point. Launches the Streamlit application."""
import sys
import subprocess
from pathlib import Path


def main() -> None:
    app_path = Path(__file__).parent / "src" / "sidct" / "ui" / "streamlit_app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path)],
        check=True,
    )


if __name__ == "__main__":
    main()
