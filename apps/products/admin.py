"""Admin configuration for the products app."""
from django.contrib import admin

from .models import (
    Brand,
    Category,
    Color,
    Material,
    Product,
    ProductImage,
    ProductVariant,
    Size,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "product_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            annotated_product_count=admin.models.Count("products")
        )

    @admin.display(description="Products", ordering="annotated_product_count")
    def product_count(self, obj):
        return getattr(obj, "annotated_product_count", obj.products.count())


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "hex_code", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ProductImageInline(admin.TabularInline):
    """Inline management of gallery images on the product page."""

    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    """Inline management of colour/size variants on the product page."""

    model = ProductVariant
    extra = 1
    autocomplete_fields = ("color", "size")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_select_related = ("category", "brand", "material")
    list_display = (
        "name",
        "category",
        "brand",
        "price",
        "discount_price",
        "current_price",
        "stock_display",
        "featured",
        "is_active",
    )
    list_filter = (
        "category",
        "brand",
        "material",
        "gold_plated",
        "stainless_steel",
        "waterproof",
        "tarnish_resistant",
        "xuping",
        "featured",
        "is_new",
        "best_seller",
        "is_active",
    )
    search_fields = ("name", "slug", "sku", "short_description", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Identification",
            {"fields": ("name", "slug", "sku", "category", "brand")},
        ),
        (
            "Description",
            {"fields": ("short_description", "description", "main_image")},
        ),
        (
            "Pricing & stock",
            {
                "fields": (
                    "price",
                    "discount_price",
                    "quantity",
                    "material",
                )
            },
        ),
        (
            "Material attributes",
            {
                "fields": (
                    "gold_plated",
                    "stainless_steel",
                    "waterproof",
                    "tarnish_resistant",
                    "xuping",
                )
            },
        ),
        (
            "Merchandising",
            {
                "fields": (
                    "featured",
                    "is_new",
                    "best_seller",
                    "is_active",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    inlines = (ProductImageInline, ProductVariantInline)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("variants")

    @admin.display(description="Current price")
    def current_price(self, obj):
        return obj.current_price

    @admin.display(description="Stock")
    def stock_display(self, obj):
        variants = list(obj.variants.all())
        if variants:
            total = sum(v.stock for v in variants if v.is_active)
            return f"{total} (variants)"
        return obj.quantity
