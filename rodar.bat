@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Abrindo o fechamento...
where py >nul 2>nul && (py -3 abrir.py & goto :fim)
where python >nul 2>nul && (python abrir.py & goto :fim)
echo.
echo Python nao encontrado. Instale em https://python.org/downloads
echo (marque "Add Python to PATH" na instalacao) e abra este arquivo de novo.
pause
:fim
