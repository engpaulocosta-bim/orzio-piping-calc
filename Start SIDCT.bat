@echo off
setlocal
cd /d "%~dp0"

if exist "dist_desktop_adaptive_v2\SIDCT\SIDCT.exe" (
    start "" "dist_desktop_adaptive_v2\SIDCT\SIDCT.exe"
    exit /b 0
)

if exist "dist_desktop_adaptive\SIDCT\SIDCT.exe" (
    start "" "dist_desktop_adaptive\SIDCT\SIDCT.exe"
    exit /b 0
)

if exist "dist_desktop_light\SIDCT\SIDCT.exe" (
    start "" "dist_desktop_light\SIDCT\SIDCT.exe"
    exit /b 0
)

if exist "dist_desktop_current\SIDCT\SIDCT.exe" (
    start "" "dist_desktop_current\SIDCT\SIDCT.exe"
    exit /b 0
)

if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" "app.py"
    exit /b 0
)

start "" python "app.py"
