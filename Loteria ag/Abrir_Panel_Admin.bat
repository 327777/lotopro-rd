@echo off
title LotoPro RD — Panel de Administrador
chcp 65001 >nul
cd /d "%~dp0"
echo Abriendo Panel de Control de Administrador...
start "" "admin.html"
exit
