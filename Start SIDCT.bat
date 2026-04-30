@echo off
setlocal
cd /d "%~dp0"

set "LOG=%~dp0Start SIDCT.log"
echo [%date% %time%] Starting SIDCT > "%LOG%"

if exist "dist_desktop_adaptive_v5\SIDCT\SIDCT.exe" (
    echo Using dist_desktop_adaptive_v5\SIDCT\SIDCT.exe >> "%LOG%"
    start "SIDCT" "%~dp0dist_desktop_adaptive_v5\SIDCT\SIDCT.exe"
    exit /b 0
)

if exist "dist_desktop_adaptive_v4\SIDCT\SIDCT.exe" (
    echo Using dist_desktop_adaptive_v4\SIDCT\SIDCT.exe >> "%LOG%"
    start "SIDCT" "%~dp0dist_desktop_adaptive_v4\SIDCT\SIDCT.exe"
    exit /b 0
)

if exist "dist_desktop_adaptive_v3\SIDCT\SIDCT.exe" (
    echo Using dist_desktop_adaptive_v3\SIDCT\SIDCT.exe >> "%LOG%"
    start "SIDCT" "%~dp0dist_desktop_adaptive_v3\SIDCT\SIDCT.exe"
    exit /b 0
)

where python >nul 2>nul
if %errorlevel%==0 (
    python -c "import PySide6" >nul 2>>"%LOG%"
    if not errorlevel 1 (
        echo Using system Python with app.py >> "%LOG%"
        start "SIDCT" python "%~dp0app.py"
        exit /b 0
    )
    echo System Python found, but PySide6 is missing. >> "%LOG%"
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import PySide6" >nul 2>>"%LOG%"
    if not errorlevel 1 (
        echo Using .venv Python with app.py >> "%LOG%"
        start "SIDCT" "%~dp0.venv\Scripts\python.exe" "%~dp0app.py"
        exit /b 0
    )
    echo .venv Python found, but PySide6 is missing. >> "%LOG%"
)

if exist "dist_desktop_adaptive_v2\SIDCT\SIDCT.exe" (
    echo Using fallback dist_desktop_adaptive_v2\SIDCT\SIDCT.exe >> "%LOG%"
    start "SIDCT" "%~dp0dist_desktop_adaptive_v2\SIDCT\SIDCT.exe"
    exit /b 0
)

if exist "dist_desktop_adaptive\SIDCT\SIDCT.exe" (
    echo Using fallback dist_desktop_adaptive\SIDCT\SIDCT.exe >> "%LOG%"
    start "SIDCT" "%~dp0dist_desktop_adaptive\SIDCT\SIDCT.exe"
    exit /b 0
)

if exist "dist_desktop_light\SIDCT\SIDCT.exe" (
    echo Using fallback dist_desktop_light\SIDCT\SIDCT.exe >> "%LOG%"
    start "SIDCT" "%~dp0dist_desktop_light\SIDCT\SIDCT.exe"
    exit /b 0
)

if exist "dist_desktop_current\SIDCT\SIDCT.exe" (
    echo Using fallback dist_desktop_current\SIDCT\SIDCT.exe >> "%LOG%"
    start "SIDCT" "%~dp0dist_desktop_current\SIDCT\SIDCT.exe"
    exit /b 0
)

echo No runnable SIDCT target found. >> "%LOG%"
echo Python/PySide6 nao encontrado e nenhum executavel SIDCT disponivel.
echo Veja o ficheiro: "%LOG%"
pause
