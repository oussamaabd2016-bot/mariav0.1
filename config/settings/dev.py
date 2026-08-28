"""Development settings for Maira Bijouterie.

Extends config.settings.base and enables debug-friendly behaviour.
"""
from .base import *  # noqa: F403
from .base import env  # noqa: F401

DEBUG = True

# Allow Django's test client ("testserver") during local development.
if "testserver" not in ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS.append("testserver")

# Allow Django to serve static/media directly during development.
STATIC_URL = "static/"

# Silence security warnings that are intentionally different in local dev.
# These settings are all correctly configured in config/settings/prod.py.
# Running `manage.py check --deploy` locally will show these warnings otherwise
# because DEBUG=True and HTTPS is not configured here — that's expected.
SILENCED_SYSTEM_CHECKS = [
    "security.W004",  # SECURE_HSTS_SECONDS — not applicable without HTTPS in dev
    "security.W008",  # SECURE_SSL_REDIRECT — no SSL in local dev
    "security.W012",  # SESSION_COOKIE_SECURE — no HTTPS in local dev
    "security.W016",  # CSRF_COOKIE_SECURE — no HTTPS in local dev
    "security.W018",  # DEBUG=True — intentional in dev
]
