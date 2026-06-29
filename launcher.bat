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

for /f %%i in ('".venv\Scripts\python.exe" -c "import hashlib, pathlib; print(hashlib.sha256(pathlib.Path(\"requirements.txt\").read_bytes()).hexdigest())"') do set "REQ_HASH=%%i"

set "STAMP_FILE=.venv\requirements.sha256"
set "STAMP_HASH="
if exist "%STAMP_FILE%" (
  set /p STAMP_HASH=<"%STAMP_FILE%"
)

if /i not "%REQ_HASH%"=="%STAMP_HASH%" (
  echo Installing/updating dependencies...
  call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Dependency install failed.
    pause
    exit /b 1
  )
  >"%STAMP_FILE%" echo %REQ_HASH%
) else (
  echo Dependencies unchanged; skipping pip install.
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
