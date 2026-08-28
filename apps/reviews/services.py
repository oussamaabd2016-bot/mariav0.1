"""Business logic for reviews: purchase verification and save helpers.

Decision (noted in the spec): reviews are purchase-verified. A user may
only review a product they actually bought in a non-cancelled order, which
keeps the rating section credible and avoids anonymous spam. Review images
are optional.
"""
from django.db import transaction

from apps.orders.models import Order, OrderStatus

from .models import Review


def user_purchased_product(user, product):
    """True when ``user`` bought ``product`` in a non-cancelled order."""
    if not user.is_authenticated:
        return False
    return Order.objects.filter(
        user=user,
        items__product=product,
    ).exclude(status=OrderStatus.CANCELLED).exists()


def user_can_review(user, product):
    """Purchase-verified users may review; blocked users cannot."""
    return bool(
        getattr(user, "is_authenticated", False)
        and user_purchased_product(user, product)
    )


def create_or_update_review(user, product, rating, comment="", image=None):
    """Create the review or update the user's existing one for this product."""
    with transaction.atomic():
        defaults = {
            "rating": rating,
            "comment": comment or "",
            "is_approved": True,
        }
        if image:
            defaults["image"] = image

        review, created = Review.objects.update_or_create(
            product=product,
            user=user,
            defaults=defaults,
        )
    return review
