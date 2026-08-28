"""Business metrics for the staff dashboard.

All numbers are computed on demand from live data. Cancelled orders are
excluded from revenue and best-seller calculations.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import F, Sum
from django.utils import timezone

from apps.accounts.models import User
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.products.models import Product, ProductVariant

LOW_STOCK_THRESHOLD = 3
NEW_CUSTOMER_DAYS = 30


def staff_metrics():
    """Return a dict of KPIs for the staff dashboard."""
    now = timezone.now()
    since = now - timedelta(days=NEW_CUSTOMER_DAYS)

    active_orders = Order.objects.exclude(status=OrderStatus.CANCELLED)
    revenue_total = active_orders.aggregate(total=Sum("total"))["total"] or Decimal("0")
    orders_total = active_orders.count()
    average_order_value = (
        revenue_total / orders_total if orders_total else Decimal("0")
    )

    revenue_30d = (
        Order.objects.filter(created_at__gte=since)
        .exclude(status=OrderStatus.CANCELLED)
        .aggregate(total=Sum("total"))["total"]
        or Decimal("0")
    )

    status_breakdown = [
        {
            "value": status,
            "label": OrderStatus(status).label,
            "count": Order.objects.filter(status=status).count(),
        }
        for status in OrderStatus.values
    ]

    best_sellers = list(
        OrderItem.objects.exclude(order__status=OrderStatus.CANCELLED)
        .values("product_id", "product__name")
        .annotate(
            units=Sum("quantity"),
            revenue=Sum(F("unit_price") * F("quantity")),
        )
        .filter(product_id__isnull=False)
        .order_by("-units")[:5]
    )

    low_stock_products = Product.objects.filter(
        is_active=True,
        variants__isnull=True,
        quantity__lte=LOW_STOCK_THRESHOLD
    )
    low_stock_variants = ProductVariant.objects.filter(
        is_active=True, stock__lte=LOW_STOCK_THRESHOLD
    ).select_related("product", "color", "size")

    return {
        "revenue_total": revenue_total,
        "orders_total": orders_total,
        "average_order_value": average_order_value,
        "revenue_30d": revenue_30d,
        "status_breakdown": status_breakdown,
        "best_sellers": best_sellers,
        "low_stock_products": low_stock_products,
        "low_stock_variants": low_stock_variants,
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
        "new_customers": User.objects.filter(date_joined__gte=since).count(),
        "latest_orders": Order.objects.order_by("-created_at")[:10],
    }
