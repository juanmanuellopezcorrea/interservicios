@echo off
echo ========================================
echo   Iniciando aplicacion de gestion...
echo ========================================
echo.
cd /d "%~dp0"

REM Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Iniciando servidor en http://127.0.0.1:5000
echo.
echo Abre tu navegador y visita: http://127.0.0.1:5000
echo.
echo IMPORTANTE: No cierres esta ventana mientras uses la aplicacion.
echo Para parar el servidor, cierra esta ventana o pulsa Ctrl+C
echo.
echo ========================================

python app.py

pause
