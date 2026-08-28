"""Wishlist views: index, add, remove and move-to-cart (login required)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.cart.services import add_item, get_or_create_cart
from apps.products.models import Product

from .models import WishlistItem


@login_required
def index(request):
    items = request.user.wishlist_items.select_related(
        "product", "product__category"
    ).all()
    return render(request, "wishlist/wishlist_index.html", {"items": items})


@login_required
@require_http_methods(["POST"])
def add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    _, created = WishlistItem.objects.get_or_create(
        user=request.user, product=product
    )
    if created:
        messages.success(request, f"{product.name} added to your wishlist.")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")
    return redirect(request.POST.get("next") or product.get_absolute_url())


@login_required
@require_http_methods(["POST"])
def remove(request, item_id):
    item = get_object_or_404(WishlistItem, pk=item_id, user=request.user)
    item.delete()
    messages.success(request, "Item removed from your wishlist.")
    return redirect("wishlist:index")


@login_required
@require_http_methods(["POST"])
def move_to_cart(request, item_id):
    item = get_object_or_404(WishlistItem, pk=item_id, user=request.user)
    product = item.product
    if not product.is_active:
        messages.error(request, f"{product.name} is no longer available.")
        return redirect("wishlist:index")

    if product.variant_count() > 0:
        messages.info(request, f"Please select your preferred colour/size for {product.name}.")
        return redirect(product.get_absolute_url())

    if product.quantity <= 0:
        messages.error(request, f"{product.name} is currently out of stock.")
        return redirect("wishlist:index")

    cart = get_or_create_cart(request)
    cart_item = add_item(cart, product)
    if cart_item:
        item.delete()
        messages.success(request, f"{product.name} moved to your cart.")
    else:
        messages.error(request, f"Could not add {product.name} to cart.")
    return redirect("cart:index")
