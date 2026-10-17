@echo off
cd /d "%~dp0"
title Fechamento Tarvo
echo.
echo   ============================================
echo     FECHAMENTO DO MES - TARVO PAGAMENTOS
echo   ============================================
echo.

py -3 --version >nul 2>nul
if not errorlevel 1 goto :compy
python --version >nul 2>nul
if not errorlevel 1 goto :compython
goto :sempython

:compy
set PY=py -3
goto :rodar

:compython
set PY=python
goto :rodar

:rodar
echo   Lendo os arquivos de entrada...
echo.
%PY% fechar.py
if errorlevel 1 goto :deuerro

echo.
echo   ============================================
echo     PRONTO. Os arquivos estao na pasta saida.
echo   ============================================
echo.
start "" "%~dp0saida"
echo   Pode fechar esta janela.
pause >nul
goto :fim

:deuerro
echo.
echo   ============================================
echo     NAO FECHOU. Nada foi gravado.
echo   ============================================
echo.
echo   O motivo esta escrito acima, nesta janela.
echo   Se falou em "pasta de entrada", confira se os arquivos
echo   do mes estao em  entrada\AAAA-MM  (ex.: entrada\2026-10).
echo.
pause
goto :fim

:sempython
echo   O Python nao esta instalado nesta maquina.
echo.
echo   Baixe em  https://python.org/downloads  e, na primeira tela
echo   do instalador, marque "Add Python to PATH".
echo   Depois e so clicar neste arquivo de novo.
echo.
pause

:fim
