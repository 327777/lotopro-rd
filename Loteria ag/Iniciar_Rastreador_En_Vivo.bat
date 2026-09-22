@echo off
title LotoPro RD — Rastreador Automatico en Vivo
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo    LotoPro RD — RASTREADOR EN VIVO DE SORTEOS
echo ========================================================
echo.
echo Rastreo automatico activo cada 3 minutos.
echo Los resultados y los historiales se actualizan solos.
echo Puedes minimizar esta ventana mientras usas la PC.
echo.
python actualizador_automatico.py --bucle
pause
