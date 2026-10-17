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

where py >nul 2>nul
if %errorlevel%==0 (set PY=py -3) else (
  where python >nul 2>nul
  if %errorlevel%==0 (set PY=python) else goto :sempython
)

echo   Conferindo a biblioteca que o motor usa...
%PY% -m pip install --quiet --disable-pip-version-check openpyxl 2>nul
echo.
%PY% abrir.py
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
echo.
pause
