"""Admin for the cart app: Coupon, Cart and CartItem."""
from django.contrib import admin

from .models import Cart, CartItem, Coupon


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("unit_price", "line_total")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_percentage",
        "min_order_amount",
        "is_active",
        "valid_from",
        "valid_until",
    )
    list_filter = ("is_active", "valid_from", "valid_until")
    search_fields = ("code",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "item_count", "subtotal", "coupon", "updated_at")
    list_filter = ("coupon",)
    search_fields = ("user__email", "session_key")
    inlines = [CartItemInline]
    readonly_fields = ("created_at", "updated_at")

    def owner(self, obj):
        return obj.user.email if obj.user_id else obj.session_key

    @admin.display(description="Items")
    def item_count(self, obj):
        return sum(obj.items.values_list("quantity", flat=True))

    @admin.display(description="Subtotal")
    def subtotal(self, obj):
        from .services import subtotal_of

        return f"{subtotal_of(obj):.2f} MAD"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "variant", "quantity", "line_total")
    list_filter = ("product__category",)
    search_fields = ("product__name", "product__sku")
    readonly_fields = ("unit_price", "line_total")
