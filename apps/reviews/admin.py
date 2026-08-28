"""Admin for the reviews app."""
from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Manage customer reviews, including approval and moderation."""

    list_display = (
        "product",
        "user",
        "rating",
        "is_approved",
        "created_at",
    )
    list_filter = ("rating", "is_approved", "created_at")
    list_editable = ("is_approved",)
    search_fields = (
        "product__name",
        "user__email",
        "comment",
    )
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("product", "user")
