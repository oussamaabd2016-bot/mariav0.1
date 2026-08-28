"""Order models: Order and OrderItem.

Orders snapshot the cart at checkout time — product name, SKU, variant label
and unit price are copied onto OrderItem so the record stays accurate even
if the catalogue changes later. Only Cash on Delivery and Bank Transfer are
offered at launch (see spec Section 0).
"""
from decimal import Decimal
from urllib.parse import quote

from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.core.models import TimeStampedModel
from apps.products.models import Product, ProductVariant


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


class PaymentMethod(models.TextChoices):
    CASH_ON_DELIVERY = "cod", "Cash on Delivery"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"


class Order(TimeStampedModel):
    """A customer's order, placed at checkout."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    order_number = models.CharField(max_length=20, unique=True, editable=False)

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
    )

    # Shipping details (snapshot of the checkout form).
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10, blank=True)
    notes = models.TextField(blank=True)

    # Money (snapshot of the totals computed at checkout).
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(
        "cart.Coupon",
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True,
    )
    coupon_code = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("orders:confirmation", kwargs={"pk": self.pk})

    @property
    def item_count(self):
        return sum(self.items.values_list("quantity", flat=True))

    def whatsapp_text(self):
        lines = [
            f"Hello Maira Bijouterie, I confirm my order {self.order_number}:",
            "",
        ]
        for item in self.items.all():
            label = item.product_name
            if item.variant_label:
                label += f" ({item.variant_label})"
            lines.append(f"- {item.quantity} × {label} = {item.line_total:.2f} MAD")
        lines.extend(
            [
                "",
                f"Subtotal: {self.subtotal:.2f} MAD",
                f"Coupon ({self.coupon_code}): -{self.discount:.2f} MAD"
                if self.coupon_code
                else f"Discount: -{self.discount:.2f} MAD",
                f"Shipping: {self.shipping:.2f} MAD",
                f"Total: {self.total:.2f} MAD",
                f"Payment: {self.get_payment_method_display()}",
                "",
                f"Deliver to {self.full_name}, {self.address}, {self.city} {self.postal_code}",
                f"Phone: {self.phone}",
            ]
        )
        return "\n".join(lines)

    def whatsapp_link(self):
        return (
            f"https://wa.me/{settings.WHATSAPP_NUMBER}"
            f"?text={quote(self.whatsapp_text())}"
        )


class OrderItem(TimeStampedModel):
    """A single line from the cart, snapshotted at order time."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        related_name="order_items",
        null=True,
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        related_name="order_items",
        null=True,
        blank=True,
    )
    # Snapshot fields.
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, blank=True)
    variant_label = models.CharField(max_length=200, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"

    @property
    def line_total(self):
        # unit_price is only None on unsaved (empty) admin inline rows.
        return (self.unit_price or Decimal("0")) * self.quantity


def generate_order_number():
    """Return the next sequential order number for the current year.

    Format: MB-<YYYY>-<six-digit sequence>, e.g. MB-2026-000042.
    """
    from django.utils import timezone

    prefix = f"MB-{timezone.now():%Y}-"
    last = (
        Order.objects.filter(order_number__startswith=prefix)
        .order_by("-order_number")
        .first()
    )
    sequence = 1
    if last:
        try:
            seq_part = last.order_number.rsplit("-", 1)[-1]
            sequence = int(seq_part) + 1
        except (ValueError, IndexError):
            sequence = 1

    candidate = f"{prefix}{sequence:06d}"
    while Order.objects.filter(order_number=candidate).exists():
        sequence += 1
        candidate = f"{prefix}{sequence:06d}"
    return candidate
