"""Admin for the wishlist app."""
from django.contrib import admin

from .models import WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "product__name", "product__sku")
    readonly_fields = ("created_at", "updated_at")
