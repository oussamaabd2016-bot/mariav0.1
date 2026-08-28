"""Cart models: Cart, CartItem and Coupon.

Both guests and logged-in customers get a DB-backed Cart. A guest cart is
keyed by ``session_key``; a customer cart is keyed by ``user``. On login the
guest cart is merged into the customer's cart (see signals.py). All pricing
is computed by the cart service (apps/cart/services.py) rather than stored,
so prices always reflect the current product/variant/coupon state.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.products.models import Product, ProductVariant


class Coupon(TimeStampedModel):
    """A code that applies a percentage discount off the cart subtotal."""

    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.PositiveIntegerField(
        default=0,
        help_text="Percentage discount off the subtotal (0-100).",
    )
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        help_text="Minimum subtotal for this coupon to apply.",
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.code

    def is_valid_for(self, subtotal):
        """A coupon is usable only when active, in date range and above the
        minimum order amount."""
        if not self.is_active:
            return False
        now = timezone.now()
        if now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if subtotal < self.min_order_amount:
            return False
        return True


class Cart(TimeStampedModel):
    """A shopping cart, owned by either a user or an anonymous session."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        related_name="carts",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        owner = self.user.email if self.user_id else self.session_key
        return f"Cart ({owner})"


class CartItem(TimeStampedModel):
    """One line in a cart: a product (optionally a specific variant)."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="cart_items",
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        label = str(self.variant) if self.variant_id else self.product.name
        return f"{self.quantity} × {label}"

    @property
    def unit_price(self):
        """Price per unit, preferring the variant's price override."""
        if self.variant_id:
            return self.variant.price
        if self.product_id:
            return self.product.current_price
        # Unsaved (empty) admin inline rows have no related objects yet.
        return Decimal("0")

    @property
    def line_total(self):
        return self.unit_price * self.quantity
