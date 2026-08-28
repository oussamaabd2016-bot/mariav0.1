"""Views for the reviews app.

Reviews are created from a POST form on the product detail page. The view
re-validates purchase eligibility server-side (never trust the form alone)
and redirects back to the product, anchoring on the reviews section.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.products.models import Product

from .forms import ReviewForm
from .services import create_or_update_review, user_can_review


@login_required
@require_POST
def review_add(request):
    """Create or update a review for a product the user has purchased."""
    form = ReviewForm(request.POST, request.FILES)

    product = None
    if form.is_valid():
        product = form.cleaned_data["product_id"]
    else:
        # Fall back to the raw id so we can still redirect somewhere sane.
        product_id = request.POST.get("product_id")
        product = (
            Product.objects.filter(pk=product_id, is_active=True).first()
            if product_id
            else None
        )

    if product is None:
        messages.error(request, "We couldn't find that product.")
        return redirect("products:list")

    if not user_can_review(request.user, product):
        messages.error(
            request,
            "You can only review products you've purchased.",
        )
        return redirect(product.get_absolute_url() + "#reviews")

    if form.is_valid():
        create_or_update_review(
            request.user,
            product,
            rating=form.cleaned_data["rating"],
            comment=form.cleaned_data["comment"],
            image=request.FILES.get("image"),
        )
        messages.success(request, "Thank you! Your review has been saved.")
    else:
        for _field, errors in form.errors.items():
            for error in errors:
                messages.error(request, str(error))

    return redirect(product.get_absolute_url() + "#reviews")
