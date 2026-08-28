"""Admin configuration for the packages app."""
from django.contrib import admin

from .models import Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "original_price",
        "discount_percentage",
        "final_price",
        "product_count",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("products",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Original price")
    def original_price(self, obj):
        return f"{obj.original_price:.2f} MAD"

    @admin.display(description="Final price")
    def final_price(self, obj):
        return f"{obj.final_price:.2f} MAD"

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()
