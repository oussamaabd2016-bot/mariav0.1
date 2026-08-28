"""Order views: checkout (guest-blocked) and order confirmation."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import Profile
from apps.cart.services import (
    cart_count,
    cart_totals,
    get_cart_items,
    get_or_create_cart,
)

from .forms import CheckoutForm
from .models import Order
from .services import place_order


@login_required
def checkout(request):
    """Collect shipping details and place the order from the current cart."""
    cart = get_or_create_cart(request)
    items = get_cart_items(cart)
    if not items:
        messages.warning(request, "Your cart is empty — add something first.")
        return redirect("cart:index")

    totals = cart_totals(cart, items)

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = place_order(
                    request.user,
                    cart,
                    **form.cleaned_data,
                )
            except ValueError as exc:
                messages.error(request, str(exc))
                return redirect("cart:index")
            messages.success(request, "Thank you! Your order has been placed.")
            return redirect(order.get_absolute_url())
    else:
        form = CheckoutForm(initial=_initial_from_profile(request.user))

    context = {
        "form": form,
        "items": items,
        "cart_count": cart_count(cart),
        **totals,
    }
    return render(request, "orders/checkout.html", context)


@login_required
def confirmation(request, pk):
    """Order confirmation page with a pre-filled WhatsApp link."""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    context = {
        "order": order,
        "BANK_TRANSFER_DETAILS": settings.BANK_TRANSFER_DETAILS,
    }
    return render(request, "orders/order_confirmation.html", context)


def _initial_from_profile(user):
    """Pre-fill the checkout form from the user's saved profile, if any."""
    profile = Profile.objects.filter(user=user).first()
    if not profile:
        return {"full_name": user.get_full_name()}
    return {
        "full_name": user.get_full_name() or "",
        "phone": profile.phone,
        "address": profile.address,
        "city": profile.city,
        "postal_code": profile.postal_code,
    }
