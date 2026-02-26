@echo off
title Informes Instantaneos - Policia de Tucuman
cd /d "%~dp0"
echo.
echo  =========================================
echo   INFORMES INSTANTANEOS - Policia Tucuman
echo  =========================================
echo.
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
python -m streamlit run app/main.py --server.port 8501 --server.headless false
pause
