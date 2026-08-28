"""Product review model for Maira Bijouterie.

Reviews are purchase-verified: only authenticated users who bought the
product (in a non-cancelled order) can rate and comment. One review per
user per product, enforced by a database constraint — re-submitting
updates the existing review instead of creating a duplicate.
"""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.products.models import Product


class Review(TimeStampedModel):
    """A customer's rating + optional comment + optional photo on a product."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    image = models.ImageField(upload_to="reviews/", blank=True)
    is_approved = models.BooleanField(
        default=True,
        help_text="Uncheck to hide the review from the product page.",
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("product", "user"),
                name="unique_review_per_product_user",
            )
        ]

    def __str__(self):
        return f"{self.user.email} — {self.rating}★ on {self.product.name}"
