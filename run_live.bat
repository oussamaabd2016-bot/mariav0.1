@echo off
echo ===================================================
echo   Starting Maira Bijouterie on http://127.0.0.1:8000
echo ===================================================

start /b python manage.py runserver 127.0.0.1:8000

echo.
echo ===================================================
echo   Generating Live Public Cloudflare HTTPS URL...
echo ===================================================
cloudflared tunnel --url http://127.0.0.1:8000
