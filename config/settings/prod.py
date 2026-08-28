"""Production settings for Maira Bijouterie.

Extends config.settings.base. Production values are injected via .env
(django-environ), so the database/secret/hosts switch is one env var away.
"""
import environ

from .base import *  # noqa: F403
from .base import BASE_DIR  # noqa: F401

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

DEBUG = False

# HTTPS security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Prevent MIME-type sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# Referrer policy
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Clickjacking protection — already in MIDDLEWARE via XFrameOptionsMiddleware
X_FRAME_OPTIONS = "DENY"

# Email backend for production (configure in .env before go-live)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True

# Static files served by whitenoise in production
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
