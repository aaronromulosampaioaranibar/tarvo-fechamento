@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Fechamento Tarvo
echo.
echo   ============================================
echo     FECHAMENTO TARVO
echo   ============================================
echo.
echo   Deixe esta janela aberta enquanto usa a tela.
echo.

py -3 --version >nul 2>nul
if not errorlevel 1 goto :compy

python --version >nul 2>nul
if not errorlevel 1 goto :compython

goto :sempython

:compy
echo   Conferindo a biblioteca que o motor usa...
py -3 -m pip install --quiet --disable-pip-version-check openpyxl
echo.
py -3 abrir.py
goto :fim

:compython
echo   Conferindo a biblioteca que o motor usa...
python -m pip install --quiet --disable-pip-version-check openpyxl
echo.
python abrir.py
goto :fim

:sempython
echo   Python nao foi encontrado neste computador.
echo.
echo   Instale em  https://python.org/downloads
echo   IMPORTANTE: na primeira tela da instalacao, marque
echo   a caixa "Add Python to PATH" antes de clicar em Install.
echo.
echo   Depois feche esta janela e clique de novo em rodar.bat.
echo.
pause
exit /b 1

:fim
echo.
echo   O fechamento foi encerrado.
echo   Se apareceu algum erro acima, mande um print dele.
echo.
pause
