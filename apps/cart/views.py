"""Cart views: add, view, update quantity, remove, apply/remove coupon."""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.products.models import Product

from . import services


def _redirect_back(request, fallback="cart:index"):
    return redirect(request.POST.get("next") or fallback)


@require_http_methods(["GET", "POST"])
def index(request):
    """Full cart page with line items and live totals."""
    cart = services.get_or_create_cart(request)
    items = services.get_cart_items(cart)
    totals = services.cart_totals(cart, items)
    context = {
        "cart": cart,
        "items": items,
        "cart_count": services.cart_count(cart),
        **totals,
    }
    return render(request, "cart/cart_index.html", context)


@require_http_methods(["POST"])
def add(request):
    """Add a product (optionally a specific variant) to the cart."""
    try:
        product = Product.objects.get(
            pk=request.POST.get("product_id"), is_active=True
        )
    except (Product.DoesNotExist, ValueError, TypeError):
        messages.error(request, "Product not found.")
        return redirect("products:list")

    try:
        quantity = int(request.POST.get("quantity", "1") or "1")
    except ValueError:
        quantity = 1

    variant = services.resolve_variant(
        product,
        color_id=request.POST.get("color") or None,
        size_id=request.POST.get("size") or None,
    )

    ok, error = services.validate_item(product, variant)
    if not ok:
        messages.error(request, error)
        return redirect(product.get_absolute_url())

    cart = services.get_or_create_cart(request)
    services.add_item(cart, product, variant, quantity)
    messages.success(request, f"{product.name} added to your cart.")
    return redirect("cart:index")


@require_http_methods(["POST"])
def update(request):
    """Update an item's quantity (removes it when quantity <= 0).

    With ``?partial=1`` the whole cart content is re-rendered so the page's
    totals update without a full navigation (see static/js/cart.js).
    """
    cart = services.get_or_create_cart(request)
    try:
        item_id = int(request.POST.get("item_id"))
    except (TypeError, ValueError):
        messages.error(request, "Invalid cart item.")
        return redirect("cart:index")
    if not cart.items.filter(pk=item_id).exists():
        messages.error(request, "Item not found in your cart.")
        return redirect("cart:index")

    try:
        quantity = int(request.POST.get("quantity", "1") or "1")
    except ValueError:
        quantity = 1

    services.update_quantity(cart, item_id, quantity)
    messages.success(request, "Cart updated.")

    if request.GET.get("partial"):
        return _render_cart_content(request, cart)
    return redirect("cart:index")


@require_http_methods(["POST"])
def remove(request):
    """Remove a single item from the cart."""
    cart = services.get_or_create_cart(request)
    try:
        item_id = int(request.POST.get("item_id"))
    except (TypeError, ValueError):
        item_id = None
    if item_id and cart.items.filter(pk=item_id).exists():
        services.remove_item(cart, item_id)
        messages.success(request, "Item removed from your cart.")
    else:
        messages.error(request, "Item not found in your cart.")

    if request.GET.get("partial"):
        return _render_cart_content(request, cart)
    return redirect("cart:index")


@require_http_methods(["POST"])
def apply_coupon(request):
    cart = services.get_or_create_cart(request)
    ok, message = services.apply_coupon(cart, request.POST.get("code"))
    if ok:
        messages.success(request, message)
    else:
        messages.error(request, message)
    if request.GET.get("partial"):
        return _render_cart_content(request, cart)
    return redirect("cart:index")


@require_http_methods(["POST"])
def remove_coupon(request):
    cart = services.get_or_create_cart(request)
    services.remove_coupon(cart)
    messages.success(request, "Coupon removed.")
    if request.GET.get("partial"):
        return _render_cart_content(request, cart)
    return redirect("cart:index")


def _render_cart_content(request, cart):
    """Re-render the cart page body for an AJAX refresh of the totals."""
    items = services.get_cart_items(cart)
    totals = services.cart_totals(cart, items)
    context = {
        "cart": cart,
        "items": items,
        "cart_count": services.cart_count(cart),
        **totals,
    }
    return render(request, "cart/cart_index.html", context)
