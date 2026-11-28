@echo off
setlocal
set "port=8007"
if "%~1"=="8008" set "port=8008"
set "project=%~dp0"
cd /d "%project%" || goto gagal
if not exist main.py goto gagal
if not exist alembic.ini goto gagal
set "pyexec=python"
if exist ".venv\Scripts\python.exe" set "pyexec=.venv\Scripts\python.exe"
"%pyexec%" -m alembic -c alembic.ini upgrade head
if errorlevel 1 goto gagal
if "%SEVIMA_PRESENTASI%"=="1" (
  "%pyexec%" data_presentasi.py
  if errorlevel 1 goto gagal
)
for /f %%K in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString()"') do set "PMB_ADMIN_KEY=%%K"
echo Folder aplikasi: "%CD%"
echo Kunci admin untuk demo ini: %PMB_ADMIN_KEY%
echo Biarkan jendela ini terbuka selama memakai Sevima Mini.
echo Buka http://127.0.0.1:%port%/admin setelah muncul "Uvicorn running".
"%pyexec%" -m uvicorn main:app --host 127.0.0.1 --port %port%
:gagal
pause

