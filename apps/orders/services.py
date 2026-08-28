"""Order services: the single place that turns a cart into an Order.

``place_order`` snapshots the cart's state into an Order + OrderItems,
decrements stock, and clears the cart. It is shared by the checkout view and
the sample-data command so the two always behave identically.
"""
from django.db import transaction

from apps.cart.services import (
    available_stock,
    cart_totals,
    get_cart_items,
)
from apps.products.models import Product, ProductVariant

from .models import Order, OrderItem


@transaction.atomic
def place_order(
    user,
    cart,
    *,
    full_name,
    phone,
    address,
    city,
    postal_code,
    payment_method,
    notes="",
):
    """Create an Order from ``cart`` and empty the cart.

    Raises ValueError when the cart is empty or an item exceeds the
    available stock. Returns the newly created Order.
    """
    items = get_cart_items(cart)
    if not items:
        raise ValueError("Your cart is empty.")

    # Preliminary stock verification
    for item in items:
        stock = available_stock(item.product, item.variant)
        if stock is not None:
            if stock <= 0:
                raise ValueError(f"'{item.product.name}' is out of stock.")
            if item.quantity > stock:
                raise ValueError(
                    f"Not enough stock for '{item.product.name}' "
                    f"({stock} available)."
                )

    totals = cart_totals(cart, items)

    order = Order.objects.create(
        user=user,
        full_name=full_name,
        phone=phone,
        address=address,
        city=city,
        postal_code=postal_code,
        payment_method=payment_method,
        subtotal=totals["subtotal"],
        discount=totals["coupon_discount"],
        shipping=totals["shipping"],
        total=totals["total"],
        coupon=cart.coupon if totals["coupon_valid"] else None,
        coupon_code=cart.coupon.code if totals["coupon_valid"] else "",
        notes=notes,
    )

    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            variant=item.variant,
            product_name=item.product.name,
            sku=item.product.sku,
            variant_label=str(item.variant) if item.variant_id else "",
            unit_price=item.unit_price,
            quantity=item.quantity,
        )
        _decrement_stock(item)

    # Clear the cart (items and any applied coupon).
    cart.items.all().delete()
    cart.coupon = None
    cart.save(update_fields=("coupon", "updated_at"))
    return order


def _decrement_stock(item):
    """Reduce available stock by the purchased quantity with row-level locking."""
    if item.variant_id:
        variant = ProductVariant.objects.select_for_update().get(pk=item.variant_id)
        if variant.stock < item.quantity:
            raise ValueError(f"Not enough stock for variant '{variant}' ({variant.stock} left).")
        variant.stock = max(variant.stock - item.quantity, 0)
        variant.save(update_fields=("stock", "updated_at"))
    else:
        product = Product.objects.select_for_update().get(pk=item.product_id)
        if product.quantity < item.quantity:
            raise ValueError(f"Not enough stock for '{product.name}' ({product.quantity} left).")
        product.quantity = max(product.quantity - item.quantity, 0)
        product.save(update_fields=("quantity", "updated_at"))
