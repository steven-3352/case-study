@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

REM MVStudio . Web Service Startup Script (Windows)
REM Usage:  start.bat [port]
REM         set MV_PORT=9000 ^&^& start.bat

cd /d "%~dp0"

REM -- config --------------------------------------------------------
set "HOST=127.0.0.1"
set "VENV_DIR=.venv"
if not "%~1"=="" (
  set "PORT=%~1"
) else if not "%MV_PORT%"=="" (
  set "PORT=%MV_PORT%"
) else (
  set "PORT=8787"
)

echo ==================================================
echo   MVStudio Web Service  .  %DATE% %TIME%
echo ==================================================

REM -- 1. Python 3.9+ ------------------------------------------------
echo.
echo [ Python ]
set "PYTHON_CMD="
for %%P in (python python3 py) do (
  if not defined PYTHON_CMD (
    where %%P >nul 2>&1
    if !errorlevel! equ 0 (
      %%P -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1
      if !errorlevel! equ 0 (
        set "PYTHON_CMD=%%P"
        for /f "tokens=*" %%V in ('%%P --version 2^>^&1') do echo [OK]   %%V
      )
    )
  )
)
if not defined PYTHON_CMD (
  echo [FAIL] Python 3.9+ not found. Download: https://www.python.org/downloads/
  exit /b 1
)

REM -- 2. Virtual environment ----------------------------------------
echo.
echo [ Virtual environment ]
if not exist "%VENV_DIR%\Scripts\activate.bat" (
  echo [WARN] .venv not found - creating ^(first-time setup^)...
  !PYTHON_CMD! -m venv "%VENV_DIR%"
  if !errorlevel! neq 0 ( echo [FAIL] venv creation failed & exit /b 1 )
  echo [OK]   Created %VENV_DIR%
) else (
  echo [OK]   .venv exists
)
call "%VENV_DIR%\Scripts\activate.bat"
if !errorlevel! neq 0 ( echo [FAIL] Failed to activate .venv & exit /b 1 )

REM -- 3. Python packages --------------------------------------------
echo.
echo [ Python packages ]
python -c "import uvicorn, fastapi, dotenv, pydantic, PIL, yaml" >nul 2>&1
if !errorlevel! neq 0 (
  echo [WARN] Missing packages - installing from requirements.txt...
  pip install -r requirements.txt -q
  if !errorlevel! neq 0 ( echo [FAIL] pip install failed & exit /b 1 )
  echo [OK]   Packages installed
) else (
  echo [OK]   Core packages present
)

REM -- 4. Playwright chromium ----------------------------------------
echo.
echo [ Playwright ]
python -c "import playwright" >nul 2>&1
if !errorlevel! neq 0 (
  echo [WARN] playwright not installed - installing...
  pip install playwright -q
)
python -m playwright install --dry-run 2>&1 | findstr /C:"chromium" >nul 2>&1
if !errorlevel! neq 0 (
  echo [WARN] Chromium not found - installing ^(one-time ~150 MB^)...
  python -m playwright install chromium
) else (
  echo [OK]   Playwright + Chromium ready
)

REM -- 5. ffmpeg -----------------------------------------------------
echo.
echo [ System: ffmpeg ]
where ffmpeg >nul 2>&1
if !errorlevel! neq 0 (
  echo [WARN] ffmpeg not found - video rendering will fail
  echo        Download: https://www.gyan.dev/ffmpeg/builds/  ^(add bin\ to PATH^)
) else (
  for /f "tokens=*" %%F in ('ffmpeg -version 2^>^&1 ^| findstr /B "ffmpeg version"') do echo [OK]   %%F
)

REM -- 6. .env file & key checks -------------------------------------
echo.
echo [ Environment ^(.env^) ]
if not exist ".env" (
  echo [WARN] .env not found - run: copy .env.example .env  then fill in API keys
  echo        Service will start but API-dependent features will fail
) else (
  echo [OK]   .env found
  for %%K in (LLM_API_KEY GPT_IMAGE_API_KEY TTS_API_KEY SEEDANCE_API_KEY GROK_API_KEY MINIMAX_API_KEY) do (
    set "FOUND="
    for /f "tokens=1,* delims==" %%A in ('findstr /B "%%K=" .env 2^>nul') do (
      set "FOUND=1"
      if "%%B"=="" echo [WARN]   .env: %%K is empty
    )
    if not defined FOUND echo [WARN]   .env: %%K is missing
  )
)

REM -- 7. Port availability ------------------------------------------
echo.
echo [ Port %PORT% ]
set "PORT_BUSY="
set "KILL_PID="
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr /R /C:":%PORT% .*LISTENING"') do (
  set "PORT_BUSY=1"
  set "KILL_PID=%%P"
)
if defined PORT_BUSY (
  if defined KILL_PID (
    echo [WARN] Port %PORT% busy - killing PID %KILL_PID%...
    taskkill /PID %KILL_PID% /F >nul 2>&1
    timeout /t 1 /nobreak >nul
  )
)
echo [OK]   Port %PORT% ready

REM -- 8. Launch -----------------------------------------------------
echo.
echo ==================================================
echo   http://%HOST%:%PORT%   ^(Ctrl-C to stop^)
echo ==================================================
echo.

set "PYTHONPATH=%~dp0"
set "MV_HOST=%HOST%"
set "MV_PORT=%PORT%"

python -m uvicorn apps.mv_api:create_app --factory --host %HOST% --port %PORT%

endlocal
