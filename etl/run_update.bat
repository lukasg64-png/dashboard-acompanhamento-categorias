@echo off
REM Atualizacao Automatica Dashboard Categorias 360 (Qlik Sense D-1 + Deploy GitHub Pages)
cd /d " c:\Users\lucas.alves6\OneDrive - Farmacias Sao Joao\Documentos\ANTIGRAVITI\dashboard-acompanhamento-categorias\
echo [%date% %time%] Iniciando atualizacao... >> etl\update_log.txt
python -u etl\daily_refresh.py >> etl\update_log.txt 2>&1
echo [%date% %time%] Finalizado (code %ERRORLEVEL%) >> etl\update_log.txt
echo. >> etl\update_log.txt
