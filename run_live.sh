#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLOUDFLARED="$HOME/.local/bin/cloudflared"
LOG_FILE="/tmp/maira_cf.log"

echo ""
echo " ========================================================="
echo "    Maira Bijouterie — Live Launcher"
echo " ========================================================="
echo ""

# ── STEP 1: Find Python venv ──────────────────────────────────────────────
PYTHON=""
for venv in "$HOME/.venvs/mariav0.1" "$SCRIPT_DIR/.venv" "$SCRIPT_DIR/.venv_linux"; do
    if [ -f "$venv/bin/python" ]; then
        PYTHON="$venv/bin/python"
        PIP="$venv/bin/pip"
        GUNICORN="$venv/bin/gunicorn"
        echo " [OK] Using venv: $venv"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    PYTHON="$(command -v python3 || command -v python)"
    PIP="$(command -v pip3 || command -v pip)"
    GUNICORN="$(command -v gunicorn 2>/dev/null || true)"
fi

# ── STEP 2: Install requirements ──────────────────────────────────────────
echo ""
echo " [1/4] Installing Python dependencies..."
"$PIP" install -r "$SCRIPT_DIR/requirements.txt" --quiet --disable-pip-version-check
echo " [OK] Dependencies installed."

# ── STEP 3: Auto-install cloudflared if missing ───────────────────────────
echo ""
echo " [2/4] Checking Cloudflare Tunnel..."

if ! command -v cloudflared &>/dev/null && [ ! -f "$CLOUDFLARED" ]; then
    echo " [!] cloudflared not found. Downloading..."
    mkdir -p "$HOME/.local/bin"
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64)  CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" ;;
        aarch64|arm64) CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64" ;;
        *)       CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-386" ;;
    esac
    curl -fsSL "$CF_URL" -o "$CLOUDFLARED"
    chmod +x "$CLOUDFLARED"
    echo " [OK] cloudflared installed."
else
    echo " [OK] cloudflared already installed."
fi

! command -v cloudflared &>/dev/null && export PATH="$HOME/.local/bin:$PATH"

# ── STEP 4: Start Django / Gunicorn ──────────────────────────────────────
echo ""
echo " [3/4] Starting Django server on http://127.0.0.1:8000..."
pkill -f "gunicorn config.wsgi" 2>/dev/null || true
pkill -f "manage.py runserver" 2>/dev/null || true

if [ -n "$GUNICORN" ]; then
    "$GUNICORN" config.wsgi:application \
        --bind 127.0.0.1:8000 \
        --chdir "$SCRIPT_DIR" \
        --daemon \
        --log-file "$SCRIPT_DIR/gunicorn.log"
else
    "$PYTHON" "$SCRIPT_DIR/manage.py" runserver 127.0.0.1:8000 &>/dev/null &
fi
sleep 2
echo " [OK] Server started."

# ── STEP 5: Tunnel + auto-open browser ───────────────────────────────────
echo ""
echo " [4/4] Creating Cloudflare Tunnel..."
echo " Waiting for your live URL..."
echo ""

rm -f "$LOG_FILE"
cloudflared tunnel --url http://127.0.0.1:8000 >"$LOG_FILE" 2>&1 &
CF_PID=$!

# Poll log file for URL
while true; do
    sleep 2
    LIVE_URL=$(grep -oP 'https://[a-zA-Z0-9\-]+\.trycloudflare\.com' "$LOG_FILE" 2>/dev/null | head -1 || true)
    if [ -n "$LIVE_URL" ]; then
        break
    fi
done

echo " ========================================================="
echo "  YOUR LIVE URL: $LIVE_URL"
echo " ========================================================="
echo ""

# Open in browser (Linux / WSL)
if command -v xdg-open &>/dev/null; then
    xdg-open "$LIVE_URL" 2>/dev/null &
elif command -v wslview &>/dev/null; then
    wslview "$LIVE_URL" &
elif command -v cmd.exe &>/dev/null; then
    cmd.exe /c start "$LIVE_URL" 2>/dev/null &
fi

echo " [OK] Opened in your browser!"
echo ""
echo " Press Ctrl+C to stop the tunnel and server."
echo ""

# Keep alive — show tunnel output
tail -f "$LOG_FILE" &
wait $CF_PID

echo ""
echo " Tunnel stopped. To stop server: pkill -f gunicorn"
