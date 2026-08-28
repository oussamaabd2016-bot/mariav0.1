"""Custom error handlers for Maira Bijouterie.

Wired up in config/urls.py via ``handler404`` / ``handler500`` so users see
branded error pages instead of Django's defaults.
"""
from django.shortcuts import render


def handler404(request, exception):
    """Render a branded 404 page for any request that matches no URL."""
    return render(request, "errors/404.html", status=404)


def handler500(request):
    """Render a branded 500 page when an unhandled exception occurs."""
    return render(request, "errors/500.html", status=500)
