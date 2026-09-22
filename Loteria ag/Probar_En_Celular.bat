@echo off
title LotoPro RD — Servidor de Prueba para Celular
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================================
echo    PRUEBA DE LOTOPRO RD EN TU CELULAR (MISMO WI-FI)
echo ==========================================================
echo.
echo Para ver la pagina en tu telefono celular ahora mismo:
echo.
echo  1. Asegurate de que tu celular este conectado al mismo Wi-Fi.
echo  2. Abre el navegador de tu celular (Chrome o Safari).
echo  3. Escribe esta direccion exactamente:
echo.
echo         http://192.168.10.57:8080
echo.
echo ==========================================================
echo Dejando servidor activo... (Presiona Ctrl + C para cerrar)
echo ==========================================================
echo.
python -m http.server 8080 --bind 0.0.0.0
pause
