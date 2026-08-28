"""Reusable template tags and filters shared across the whole project.

Load in any template with ``{% load core_tags %}``.
"""
from django import template

register = template.Library()


from decimal import Decimal, InvalidOperation

@register.filter
def multiply(value, arg):
    """Multiply a value by an argument (e.g. unit price x quantity)."""
    if value is None or arg is None:
        return 0
    try:
        val_dec = Decimal(str(value))
        arg_dec = Decimal(str(arg))
        return val_dec * arg_dec
    except (InvalidOperation, ValueError, TypeError):
        return 0


@register.simple_tag(takes_context=True)
def active_nav(context, url_name):
    """Return the ``active`` class when the given URL name is the current page.

    Usage in templates::

        <li class="nav-item {% active_nav 'products:list' %}">...</li>
    """
    request = context.get("request")
    if request is None:
        return ""
    resolver = getattr(request, "resolver_match", None)
    if resolver is not None and resolver.url_name == url_name:
        return "active"
    return ""


@register.filter
def status_badge_class(status):
    """Map an order/status string to a Bootstrap badge colour class."""
    mapping = {
        "pending": "bg-warning text-dark",
        "processing": "bg-info text-dark",
        "delivered": "bg-success",
        "cancelled": "bg-danger",
        "shipped": "bg-primary",
    }
    return mapping.get(status, "bg-secondary")
