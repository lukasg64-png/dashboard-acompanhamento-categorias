@echo off
chcp 65001 > nul
echo ======================================================================
echo   DASHBOARD 360 - ATUALIZACAO AUTOMATICA D-1 (QLIK SENSE)
echo ======================================================================
cd /d "%~dp0"
python etl\daily_refresh.py
echo ======================================================================
echo   Processo finalizado. Link: https://lukasg64-png.github.io/dashboard-acompanhamento-categorias/
echo ======================================================================
pause
