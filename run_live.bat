@echo off
setlocal EnableDelayedExpansion
title Maira Bijouterie — Live Launcher
color 0A
cd /d "%~dp0"

echo.
echo  =========================================================
echo     TOTAL  Live Launcher
echo  =========================================================
echo.

set "PYTHON="
if exist "%~dp0.venv\Scripts\python.exe"      set "PYTHON=%~dp0.venv\Scripts\python.exe"
if exist "%~dp0.venv_linux\Scripts\python.exe" set "PYTHON=%~dp0.venv_linux\Scripts\python.exe"
if "%PYTHON%"=="" (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "delims=" %%i in ('where python') do set "PYTHON=%%i" & goto :found_python
    )
    echo  [ERROR] Python not found. Please install Python 3.12 from https://python.org its easy dont worry.
    echo  [ERROR] Or create a virtual environment in this folder with: python -m venv .venv
    echo  [ERROR] Then run this script again.
    pause & exit /b 1
)
:found_python
echo  [OK] Python: %PYTHON%

echo.
echo  =========================================================
echo   [1/4] Installing python dependencies...
echo  =========================================================
echo.
"%PYTHON%" -m pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  [ERROR] pip install failed. Check requirements.txt and your internet.
    pause & exit /b 1
)
echo  [OK] All dependencies installed.

echo.
echo  =========================================================
echo   [2/4] Checking Cloudflare Tunnel...
echo  =========================================================
echo.

set "CF_BIN=cloudflared"
where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%~dp0cloudflared.exe" (
        set "CF_BIN=%~dp0cloudflared.exe"
        echo  [OK] cloudflared found in project folder.
        goto :start_server
    )

    echo  [!] cloudflared not found. Installing...

    where winget >nul 2>&1
    if %errorlevel% equ 0 (
        echo  [*] Installing via winget...
        winget install --id Cloudflare.cloudflared -e --accept-package-agreements --accept-source-agreements >nul 2>&1
        where cloudflared >nul 2>&1
        if %errorlevel% equ 0 goto :start_server
    )

    echo  [*] Downloading cloudflared from GitHub...
    if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
        set "CF_URL=https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    ) else (
        set "CF_URL=https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-386.exe"
    )
    powershell -Command "Invoke-WebRequest -Uri '!CF_URL!' -OutFile '%~dp0cloudflared.exe' -UseBasicParsing"
    if %errorlevel% neq 0 (
        echo  [ERROR] Download failed. Check your internet connection.
        pause & exit /b 1
    )
    set "CF_BIN=%~dp0cloudflared.exe"
    echo  [OK] cloudflared downloaded.
) else (
    echo  [OK] cloudflared already installed.
)

:start_server
echo.
echo  =========================================================
echo   [3/4] Starting Django server...
echo  =========================================================
echo.

set "LOG_FILE=%TEMP%\maira_cf.log"
if exist "%LOG_FILE%" del "%LOG_FILE%"

start "Maira Bijouterie — Server" cmd /k ""%PYTHON%" manage.py runserver 127.0.0.1:8000"
timeout /t 3 /nobreak >nul
echo  [OK] Server started at http://127.0.0.1:8000

echo.
echo  =========================================================
echo   [4/4] Creating Cloudflare Tunnel + Opening Browser...
echo  =========================================================
echo.
echo  Waiting for your live URL...
echo.

:: Start cloudflared in background, write logs to temp file
start /B %CF_BIN% tunnel --url http://127.0.0.1:8000 > "%LOG_FILE%" 2>&1

:: Poll the log file until the URL appears, then open it
:wait_for_url
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command ^
  "if(Test-Path '%LOG_FILE%'){$c=Get-Content '%LOG_FILE%' -Raw;if($c -match 'https://[a-zA-Z0-9\-]+\.trycloudflare\.com'){$c -match 'https://[a-zA-Z0-9\-]+\.trycloudflare\.com'|Out-Null;Write-Output $matches[0]}}" > "%TEMP%\maira_url.txt" 2>nul

set /p LIVE_URL= < "%TEMP%\maira_url.txt"
if "!LIVE_URL!"=="" goto :wait_for_url

echo  =========================================================
echo   YOUR LIVE URL: !LIVE_URL! directly in your browser.
echo  =========================================================
echo.
start "" "!LIVE_URL!"
echo  [OK] Opened in your browser!
echo.
echo  Press Ctrl+C to stop the tunnel and server.
echo.

:: Keep the window alive so tunnel stays running
:keep_alive
timeout /t 60 /nobreak >nul
goto :keep_alive
