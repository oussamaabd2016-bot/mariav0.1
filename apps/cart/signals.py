"""Signals for the cart app.

Merges a guest (session-keyed) cart into the customer's persistent cart
when they log in, so nothing is lost between "add to cart" and "log in".
"""
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import Cart, CartItem


@receiver(user_logged_in)
def merge_guest_cart_into_user_cart(sender, request, user, **kwargs):
    if request is None:
        return

    # The guest cart's id is recorded in the session by get_or_create_cart.
    # We can't look it up by session_key here because Django rotates the
    # session key during login (session-fixation protection) *before* this
    # signal fires — but the session data (including our marker) survives.
    guest_cart_id = request.session.get("guest_cart_id")
    if guest_cart_id is None:
        return

    guest_cart = Cart.objects.filter(pk=guest_cart_id).first()
    if guest_cart is None:
        return
    if guest_cart.user_id:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)

    # Carry over a coupon the guest had applied, if the user has none.
    if user_cart.coupon_id is None and guest_cart.coupon_id:
        user_cart.coupon = guest_cart.coupon
        user_cart.save(update_fields=("coupon", "updated_at"))

    from .services import available_stock

    for guest_item in guest_cart.items.select_related("product", "variant"):
        stock = available_stock(guest_item.product, guest_item.variant)
        if stock is not None and stock <= 0:
            continue

        existing = user_cart.items.filter(
            product=guest_item.product, variant=guest_item.variant
        ).first()
        if existing:
            new_qty = existing.quantity + guest_item.quantity
            if stock is not None:
                new_qty = min(new_qty, stock)
            existing.quantity = new_qty
            existing.save(update_fields=("quantity", "updated_at"))
        else:
            qty = guest_item.quantity
            if stock is not None:
                qty = min(qty, stock)
            CartItem.objects.create(
                cart=user_cart,
                product=guest_item.product,
                variant=guest_item.variant,
                quantity=qty,
            )

    guest_cart.delete()
    request.session.pop("guest_cart_id", None)
