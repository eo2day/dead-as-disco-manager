@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON=py -3"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON=python"
  ) else (
    echo Python 3 was not found. Install Python, then try again.
    pause
    exit /b 1
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  call %PYTHON% -m venv .venv
  if errorlevel 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
  )
)

echo Installing/updating dependencies...
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency install failed.
  pause
  exit /b 1
)

echo Launching Dead as Disco Music Manager...
call ".venv\Scripts\python.exe" main.py
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
  echo.
  echo App exited with code %EXITCODE%.
  pause
)

exit /b %EXITCODE%
