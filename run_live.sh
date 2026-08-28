#!/usr/bin/env bash
echo "✦ Starting Maira Bijouterie on local port 8000..."
pkill -f "gunicorn config.wsgi:application" 2>/dev/null || true
~/.venvs/mariav0.1/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --daemon

echo "✦ Generating your live public Cloudflare HTTPS URL..."
~/.local/bin/cloudflared tunnel --url http://127.0.0.1:8000
