@echo off
title Informes Instantaneos - Policia de Tucuman
cd /d "%~dp0"

set "INFORMES_DEBUG_DIAGNOSTICS="
set "INFORMES_DEBUG_DIAGNOSTICS_PATH="

if /I "%~1"=="debug" (
    set "INFORMES_DEBUG_DIAGNOSTICS=1"
    set "INFORMES_DEBUG_DIAGNOSTICS_PATH=diagnostics\reporte_diagnostico_carga.json"
)

echo.
echo  =========================================
echo   INFORMES INSTANTANEOS - Policia Tucuman
echo  =========================================
echo.
if defined INFORMES_DEBUG_DIAGNOSTICS (
    echo  Modo tecnico activado: se exportara diagnostico de carga.
    echo  Ruta diagnostico: %INFORMES_DEBUG_DIAGNOSTICS_PATH%
    echo.
)
echo  Liberando puerto 8501...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8501" ^| find "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo.
echo  Iniciando aplicacion en http://localhost:8501
echo  Cierra esta ventana para detener la app.
echo.
timeout /t 2 /nobreak >nul
start "" http://localhost:8501
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m streamlit run app/main.py --server.port 8501 --server.headless false
) else (
    python -m streamlit run app/main.py --server.port 8501 --server.headless false
)
pause
