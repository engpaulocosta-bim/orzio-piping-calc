"""
Portable desktop launcher for SIDCT.

The executable starts Streamlit as an internal backend and shows it in a
native desktop window via pywebview. No browser tab is opened.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path


PORT = 8503
APP_TITLE = "SIDCT - Sistema Integrado de Dimensionamento de Tubagens"


if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(sys._MEIPASS)
    APP_ROOT = Path(sys.executable).parent
else:
    BUNDLE_DIR = Path(__file__).parent.parent
    APP_ROOT = BUNDLE_DIR

APP_PY = BUNDLE_DIR / "app.py"


def _debug(message: str) -> None:
    if os.environ.get("SIDCT_DEBUG") != "1":
        return
    log_path = Path(os.environ.get("TEMP", str(APP_ROOT))) / "sidct_portable_debug.log"
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")


def _port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _find_free_port(start: int = PORT, attempts: int = 20) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free local port found for SIDCT.")


def _wait_for_server(port: int, timeout: float = 45.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_is_open(port):
            return True
        time.sleep(0.5)
    return False


def _configure_environment() -> None:
    os.environ["PYTHONPATH"] = (
        str(BUNDLE_DIR / "src")
        + os.pathsep
        + os.environ.get("PYTHONPATH", "")
    )
    os.environ.setdefault("SIDCT_DESKTOP_EMBEDDED", "1")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")
    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", "127.0.0.1")
    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
    os.chdir(BUNDLE_DIR)


def _run_streamlit_server(port: int) -> None:
    _configure_environment()
    _debug(f"server start argv={sys.argv!r} bundle={BUNDLE_DIR} app={APP_PY} exists={APP_PY.exists()}")

    from streamlit.web import bootstrap

    flag_options = {
        "server_port": port,
        "server_address": "127.0.0.1",
        "server_headless": True,
        "server_fileWatcherType": "none",
        "browser_gatherUsageStats": False,
        "global_developmentMode": False,
    }
    bootstrap.load_config_options(flag_options)
    bootstrap.run(
        str(APP_PY),
        False,
        [],
        flag_options,
    )


def _server_command(port: int) -> list[str]:
    if getattr(sys, "frozen", False):
        return [str(Path(sys.executable)), "--sidct-server", str(port)]
    return [sys.executable, str(Path(__file__).resolve()), "--sidct-server", str(port)]


def _self_test() -> None:
    """Diagnóstico empacotado: corre o cálculo e regista resultado/erro.
    Uso: SIDCT.exe --sidct-selftest  (escreve em %TEMP%/sidct_selftest.log)"""
    _configure_environment()
    sys.path.insert(0, str(BUNDLE_DIR / "src"))
    out = Path(os.environ.get("TEMP", str(APP_ROOT))) / "sidct_selftest.log"
    with open(out, "w", encoding="utf-8") as log:
        def w(m):
            log.write(str(m) + "\n"); log.flush()
        try:
            w("importing CoolProp...")
            import CoolProp.CoolProp as CP
            w("CoolProp imported; calling PropsSI...")
            rho = CP.PropsSI("D", "T", 298.15, "P", 700000.0, "Air")
            w(f"PropsSI OK rho={rho}")
        except BaseException as exc:
            w(f"CoolProp FAILED: {exc!r}")
        try:
            w("running full calculation...")
            from sidct.models import LineInput, FittingItem, ValveItem
            from sidct.engines.selector import run_full_calculation
            inp = LineInput(
                project_name="PROJ-001", line_tag="L-001", service="compressed_air",
                project_profile="glass_factory_industrial_eu", jurisdiction="EU",
                fluid_name="Ar Comprimido", P_oper_bar=7.0, T_oper_c=25.0,
                P_design_bar=10.0, T_design_c=60.0, flow_rate=300.0,
                flow_rate_basis="Nm3/h", line_length_m=50.0, elevation_delta_m=0.0,
                material="A106 GrB", dimensional_catalog="B36.10M",
                corrosion_allowance_mm=1.5, insulation_thickness_mm=50.0,
                insulation_density_kgm3=100.0,
                fittings=[FittingItem(fitting_type="90_LR_ELBOW", quantity=4)],
                valves=[ValveItem(valve_type="GATE_VALVE_FULL_OPEN", quantity=1)],
                allowable_pressure_drop_bar=0.5, required_residual_pressure_bar=None,
                DN_received_mm=None, schedule_or_wall_received=None, slope_mm_m=None,
                vacuum_target_mbara=None, design_notes="", operation_mode="calculate_new",
            )
            run_full_calculation(inp)
            w("CALC OK")
        except BaseException as exc:
            import traceback
            w("CALC FAILED:")
            w(traceback.format_exc())


def main() -> None:
    _debug(f"main start argv={sys.argv!r} frozen={getattr(sys, 'frozen', False)} exe={sys.executable}")
    _configure_environment()

    if "--sidct-server" in sys.argv:
        index = sys.argv.index("--sidct-server")
        port = int(sys.argv[index + 1])
        _run_streamlit_server(port)
        return

    if "--sidct-selftest" in sys.argv:
        _self_test()
        return

    port = _find_free_port()

    log_dir = Path(os.environ.get("TEMP", str(APP_ROOT)))
    if os.environ.get("SIDCT_DEBUG") == "1":
        stdout_dest = open(log_dir / "sidct_server_stdout.log", "a", encoding="utf-8")
        stderr_dest = open(log_dir / "sidct_server_stderr.log", "a", encoding="utf-8")
    else:
        stdout_dest = subprocess.DEVNULL
        stderr_dest = subprocess.DEVNULL

    server = subprocess.Popen(
        _server_command(port),
        cwd=str(BUNDLE_DIR),
        stdout=stdout_dest,
        stderr=stderr_dest,
    )

    if not _wait_for_server(port):
        server.terminate()
        raise RuntimeError("SIDCT backend did not start within 45 seconds.")

    import webview

    window = webview.create_window(
        APP_TITLE,
        f"http://127.0.0.1:{port}",
        width=1400,
        height=900,
        min_size=(1024, 700),
        confirm_close=False,
    )

    try:
        webview.start(private_mode=False)
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        _debug(traceback.format_exc())
        raise
