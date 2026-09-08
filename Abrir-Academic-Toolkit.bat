@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 start_gui.py
  goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
  python start_gui.py
  goto :end
)
echo Python no esta instalado o no esta disponible en PATH.
echo Instala Python desde Microsoft Store o python.org y vuelve a abrir este archivo.
pause
:end
endlocal
