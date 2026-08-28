"""Cart service — the single place where cart logic lives.

Both guests and authenticated customers are backed by a DB ``Cart``: guests
are keyed by their session key, customers by their user. Totals (subtotal,
coupon discount, shipping, total) are computed on demand so they always
reflect the current product, variant and coupon state.
"""
from decimal import Decimal

from django.conf import settings

from apps.products.models import Product, ProductVariant

from .models import Cart, CartItem, Coupon


def get_or_create_cart(request):
    """Return the Cart belonging to the current request.

    Authenticated users get (or create) their persistent cart; anonymous
    users get a cart tied to their session (creating a session key when
    needed). The guest cart's id is stashed in the session so it survives
    the session-key rotation that happens on login — see signals.py.
    """
    if request.user.is_authenticated:
        return Cart.objects.get_or_create(user=request.user)[0]
    if not request.session.session_key:
        request.session.create()
    cart = Cart.objects.get_or_create(session_key=request.session.session_key)[0]
    request.session["guest_cart_id"] = cart.pk
    return cart


def get_cart_items(cart):
    """Items with related objects preloaded for rendering."""
    return cart.items.select_related(
        "product",
        "product__category",
        "variant",
    )


def cart_count(cart):
    """Total number of units in the cart (for the navbar badge)."""
    return sum(cart.items.values_list("quantity", flat=True))


# --- Items ---------------------------------------------------------------

def available_stock(product, variant=None):
    """Maximum sellable quantity for a product/variant (0 if unknown/empty)."""
    if product.variant_count():
        if not variant:
            return 0
        return variant.stock if variant.is_active else 0
    return product.quantity


def validate_item(product, variant=None):
    """Return (ok, error_message) for adding ``product`` to a cart."""
    if not product.is_active:
        return False, "This product is no longer available."
    if product.variant_count():
        if not variant:
            return False, "Please choose a colour and size for this product."
        if variant.product_id != product.id:
            return False, "That combination is not valid for this product."
        if not variant.in_stock():
            return False, "That colour/size combination is out of stock."
    elif product.quantity <= 0:
        return False, "This product is out of stock."
    return True, ""


def resolve_variant(product, color_id=None, size_id=None):
    """Find the exact variant matching the chosen colour/size ids."""
    queryset = ProductVariant.objects.filter(product=product)
    if color_id:
        queryset = queryset.filter(color_id=color_id)
    else:
        queryset = queryset.filter(color__isnull=True)
    if size_id:
        queryset = queryset.filter(size_id=size_id)
    else:
        queryset = queryset.filter(size__isnull=True)
    return queryset.first()


def add_item(cart, product, variant=None, quantity=1):
    """Add ``quantity`` of a product (optionally a variant) to the cart.

    Adding an item that is already present increments its quantity, capped
    at the available stock. Returns the CartItem (or None if out of stock).
    """
    quantity = max(int(quantity), 1)
    stock = available_stock(product, variant)
    if stock is not None and stock <= 0:
        return None

    existing = _find_item(cart, product, variant)
    if existing:
        new_quantity = existing.quantity + quantity
        if stock is not None:
            new_quantity = min(new_quantity, stock)
        existing.quantity = new_quantity
        existing.save(update_fields=("quantity", "updated_at"))
        return existing

    if stock is not None:
        quantity = min(quantity, stock)

    return CartItem.objects.create(
        cart=cart,
        product=product,
        variant=variant,
        quantity=quantity,
    )


def update_quantity(cart, item_id, quantity):
    """Set an item's quantity, removing it when quantity is 0 or negative."""
    item = cart.items.select_related("product", "variant").get(pk=item_id)
    quantity = int(quantity)
    if quantity <= 0:
        item.delete()
        return None
    stock = available_stock(item.product, item.variant)
    if stock is not None:
        if stock <= 0:
            item.delete()
            return None
        quantity = min(quantity, stock)
    item.quantity = quantity
    item.save(update_fields=("quantity", "updated_at"))
    return item


def remove_item(cart, item_id):
    cart.items.filter(pk=item_id).delete()


def _find_item(cart, product, variant):
    queryset = cart.items.filter(product=product)
    if variant:
        return queryset.filter(variant=variant).first()
    return queryset.filter(variant__isnull=True).first()


# --- Coupons -------------------------------------------------------------

def apply_coupon(cart, code):
    """Attach a coupon to the cart if it is valid for the current subtotal.

    Returns (ok, message).
    """
    code = (code or "").strip().upper()
    subtotal = subtotal_of(cart)
    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        return False, f"Coupon '{code}' does not exist."
    if not coupon.is_valid_for(subtotal):
        if subtotal < coupon.min_order_amount:
            return False, (
                f"Coupon '{code}' requires a minimum order of "
                f"{coupon.min_order_amount:.2f} MAD."
            )
        return False, f"Coupon '{code}' is no longer valid."
    cart.coupon = coupon
    cart.save(update_fields=("coupon", "updated_at"))
    return True, f"Coupon '{code}' applied."


def remove_coupon(cart):
    if cart.coupon_id:
        cart.coupon = None
        cart.save(update_fields=("coupon", "updated_at"))


# --- Totals --------------------------------------------------------------

def subtotal_of(cart):
    items = get_cart_items(cart)
    return sum((item.line_total for item in items), Decimal("0"))


def cart_totals(cart, items=None):
    """Compute subtotal, coupon discount, shipping and total.

    Shipping is a flat rate for orders below the free-shipping threshold and
    free above it. Only a non-empty cart can be charged shipping.
    """
    items = items if items is not None else get_cart_items(cart)
    subtotal = sum((item.line_total for item in items), Decimal("0"))

    coupon_discount = Decimal("0")
    coupon_valid = False
    if cart.coupon_id and cart.coupon.is_valid_for(subtotal):
        coupon_discount = (
            subtotal * Decimal(cart.coupon.discount_percentage) / 100
        )
        coupon_valid = True

    flat_rate = Decimal(str(settings.SHIPPING_FLAT_RATE))
    threshold = Decimal(str(settings.FREE_SHIPPING_THRESHOLD))
    shipping = Decimal("0")
    if subtotal > 0 and subtotal < threshold:
        shipping = flat_rate

    total = subtotal - coupon_discount + shipping
    return {
        "subtotal": subtotal,
        "coupon_discount": coupon_discount,
        "coupon_valid": coupon_valid,
        "shipping": shipping,
        "total": total,
        "free_shipping_threshold": threshold,
        "free_shipping_remaining": max(threshold - subtotal, Decimal("0")),
        "shipping_flat_rate": flat_rate,
    }
