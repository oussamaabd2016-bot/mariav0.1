"""Template context processors for the home app."""
from django.conf import settings

from apps.products.models import Category


def categories_nav(request):
    """Provide the category list for the navbar mega menu.

    A cheap, single query reused on every page that renders the navbar.
    """
    return {"nav_categories": Category.objects.prefetch_related("products").all()[:8]}


def site_settings(request):
    """Expose a few shop-wide settings to every template."""
    return {
        "whatsapp_number": settings.WHATSAPP_NUMBER,
        "free_shipping_threshold": int(float(settings.FREE_SHIPPING_THRESHOLD)),
        "free_shipping_threshold_display": f"{int(float(settings.FREE_SHIPPING_THRESHOLD))} MAD",
    }
