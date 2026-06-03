# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for SIDCT portable desktop build.

Build:
    pyinstaller build_desktop/SIDCT.spec --noconfirm

Output:
    dist/SIDCT.exe  (single portable executable)
"""
from pathlib import Path
import site

from PyInstaller.utils.hooks import (
    collect_data_files, collect_submodules, copy_metadata,
    collect_all, collect_dynamic_libs,
)


ROOT      = Path(SPECPATH).parent
SRC_DIR   = ROOT / "src"
DATA_DIR  = ROOT / "data"
ICON_PATH = ROOT / "build_desktop" / "sidct.ico"

# Regenera sempre o .ico a partir do PNG transparente antes de empacotar, para
# o executável nunca embutir uma versão antiga/com fundo branco do ícone.
import runpy
runpy.run_path(str(ROOT / "build_desktop" / "make_icon.py"), run_name="__main__")

SITE_PKGS = Path(site.getsitepackages()[0])
PY311_PKGS = Path("C:/Users/Paulo Costa/AppData/Local/Programs/Python/Python311/Lib/site-packages")
if PY311_PKGS.exists():
    SITE_PKGS = PY311_PKGS

datas = [
    (str(SRC_DIR / "sidct"), "sidct"),
    (str(ROOT / "app.py"), "."),
    # YAML configs
    (str(ROOT / "project_profiles.yaml"),    "."),
    (str(ROOT / "service_matrix.yaml"),      "."),
    (str(ROOT / "standards_registry.yaml"),  "."),
    (str(ROOT / "assumptions.yaml"),         "."),
    (str(ROOT / "system_pipe_mapping.yaml"), "."),
    (str(ROOT / "form_behavior_matrix.yaml"),"."),
    # Data catalogs and templates
    (str(DATA_DIR / "catalogs"),  "data/catalogs"),
    (str(DATA_DIR / "templates"), "data/templates"),
    # Streamlit assets (must be bundled explicitly)
    (str(SITE_PKGS / "streamlit"), "streamlit"),
]

if (SITE_PKGS / "altair").exists():
    datas.append((str(SITE_PKGS / "altair"), "altair"))

datas += collect_data_files("webview")
datas += copy_metadata("streamlit")

# CoolProp é uma extensão C++ (.pyd) usada nos cálculos de fluido. Sem coletar
# os binários + dados o exe importa mas crasha (access violation) ao chamar
# PropsSI — o que derruba o servidor e deixa a página em branco no "Calcular".
cp_datas, cp_binaries, cp_hidden = collect_all("CoolProp")
datas += cp_datas

binaries = list(cp_binaries)
binaries += collect_dynamic_libs("scipy")

hiddenimports = [
    # sidct package — all submodules explicit to avoid missed imports
    "sidct",
    "sidct.enums",
    "sidct.models",
    "sidct.units",
    "sidct.config",
    "sidct.validators",
    "sidct.exceptions",
    "sidct.materials",
    "sidct.project",
    "sidct.provenance",
    "sidct.system_pipe_mapping",
    "sidct.logging_config",
    "sidct.catalogs",
    "sidct.catalogs.pipe_dimension_catalog",
    "sidct.catalogs.material_stress_catalog",
    "sidct.catalogs.fitting_k_catalog",
    "sidct.catalogs.fluid_properties",
    "sidct.data_access",
    "sidct.data_access.external_datasets",
    "sidct.data_access.loaders",
    "sidct.engines",
    "sidct.engines.selector",
    "sidct.engines.checker",
    "sidct.engines.colebrook",
    "sidct.engines.hydraulic_incompressible",
    "sidct.engines.hydraulic_compressible",
    "sidct.engines.hydraulic_gravity",
    "sidct.engines.thickness_internal",
    "sidct.engines.thickness_external",
    "sidct.engines.vacuum",
    "sidct.engines.supports",
    "sidct.batch",
    "sidct.batch.csv_runner",
    "sidct.reports",
    "sidct.reports.memorial_pdf",
    "sidct.reports.exports",
    "sidct.reports.project_pdf",
    "sidct.ui",
    "sidct.ui.streamlit_app",
    "sidct.ui.form_behavior",
    # Streamlit internals
    "streamlit",
    "streamlit.web",
    "streamlit.web.bootstrap",
    "streamlit.runtime",
    "streamlit.runtime.scriptrunner",
    "streamlit.components.v1",
    # Scientific stack
    "numpy",
    "scipy",
    "scipy.optimize",
    "scipy.interpolate",
    "CoolProp",
    "CoolProp.CoolProp",
    # Data / reporting
    "pydantic",
    "pydantic.v1",
    "yaml",
    "reportlab",
    "reportlab.lib",
    "reportlab.platypus",
    "openpyxl",
    "pandas",
    "structlog",
    # Visualisation / web
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "altair",
    "plotly",
    "click",
    "tornado",
    "importlib.metadata",
    "importlib.resources",
    # pywebview (native desktop window)
    "webview",
    "pythonnet",
    "clr_loader",
    "cffi",
]
hiddenimports += collect_submodules("webview")
hiddenimports += collect_submodules("clr_loader")
hiddenimports += cp_hidden

a = Analysis(
    [str(ROOT / "build_desktop" / "launcher.py")],
    pathex=[str(SRC_DIR), str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "PyQt5",
        "PyQt6",
        "PySide6",
        "matplotlib",
        "IPython",
        "jupyter",
        "pytest",
        "setuptools",
        "pip",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SIDCT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_PATH),
    version_file=None,
)
