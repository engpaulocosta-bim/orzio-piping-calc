@echo off
setlocal
cd /d "%~dp0"

set "LOG=%~dp0Start SIDCT.log"
echo [%date% %time%] Starting SIDCT > "%LOG%"

if exist "dist_desktop_adaptive_v7\SIDCT\SIDCT.exe" (
    echo Using dist_desktop_adaptive_v7\SIDCT\SIDCT.exe >> "%LOG%"
    start "SIDCT" "%~dp0dist_desktop_adaptive_v7\SIDCT\SIDCT.exe"
    exit /b 0
)

if exist "dist_desktop_adaptive_v6\SIDCT\SIDCT.exe" (
    echo Using dist_desktop_adaptive_v6\SIDCT\SIDCT.exe >> "%LOG%"
    start "SIDCT" "%~dp0dist_desktop_adaptive_v6\SIDCT\SIDCT.exe"
    exit /b 0
)

if exist "dist_desktop_adaptive_v5\SIDCT\SIDCT.exe" (
    echo Using dist_desktop_adaptive_v5\SIDCT\SIDCT.exe >> "%LOG%"
    start "SIDCT" "%~dp0dist_desktop_adaptive_v5\SIDCT\SIDCT.exe"
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

echo No runnable SIDCT target found. >> "%LOG%"
echo Python/PySide6 nao encontrado e nenhum executavel SIDCT disponivel.
echo Veja o ficheiro: "%LOG%"
pause
