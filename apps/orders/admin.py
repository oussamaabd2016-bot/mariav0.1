"""Admin for the orders app."""
from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)


from django.db.models import Sum

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_select_related = ("user",)
    list_display = (
        "order_number",
        "user",
        "full_name",
        "payment_method",
        "status",
        "total",
        "item_count",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("order_number", "user__email", "full_name", "phone")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            annotated_item_count=Sum("items__quantity")
        )

    @admin.display(description="Items", ordering="annotated_item_count")
    def item_count(self, obj):
        return getattr(obj, "annotated_item_count", obj.item_count)
    readonly_fields = (
        "order_number",
        "subtotal",
        "discount",
        "shipping",
        "total",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("order_number", "user", "status", "payment_method")}),
        (
            "Shipping",
            {"fields": ("full_name", "phone", "address", "city", "postal_code")},
        ),
        (
            "Totals",
            {"fields": ("subtotal", "discount", "shipping", "total", "coupon_code")},
        ),
        ("Notes", {"fields": ("notes",)}),
    )
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "sku", "unit_price", "quantity", "line_total")
    search_fields = ("order__order_number", "product_name", "sku")
    readonly_fields = ("line_total",)
