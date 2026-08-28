"""Admin for the home app."""
from django.contrib import admin

from .models import NewsletterSubscriber


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Manage newsletter signups and opt-outs."""

    list_display = ("email", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    list_editable = ("is_active",)
    search_fields = ("email",)
    readonly_fields = ("created_at", "updated_at")
