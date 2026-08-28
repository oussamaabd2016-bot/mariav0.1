"""Package/bundle models for Maira Bijouterie.

A Package groups several products into a discounted bundle (e.g. a
"Necklace + Bracelet + Earrings" gift set). The original price is derived
from the sum of the included products; the final price is computed from the
original price and the configured discount percentage.
"""
from decimal import Decimal
import json

from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from apps.core.models import TimeStampedModel
from apps.products.models import Product


class Package(TimeStampedModel):
    """A discounted bundle of products."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=230, unique=True, blank=True)
    description = models.TextField(blank=True)
    products = models.ManyToManyField(
        Product,
        related_name="packages",
        blank=True,
        help_text="Products included in this bundle.",
    )
    discount_percentage = models.PositiveIntegerField(
        default=0,
        help_text="Percentage discount applied to the bundle (0-100).",
    )
    image = models.ImageField(upload_to="packages/", blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("packages:detail", kwargs={"slug": self.slug})

    # --- Imagery ----------------------------------------------------------

    @property
    def display_image(self):
        """Package image, falling back to the first included product's photo."""
        if self.image:
            return self.image
        first = self.products.all().first()
        if first and first.main_image:
            return first.main_image
        return None

    @property
    def show_images(self):
        """Ordered, de-duplicated list of image URLs across the whole set."""
        urls = []
        if self.image:
            urls.append(self.image.url)
        for product in self.products.all():
            if product.main_image:
                urls.append(product.main_image.url)
        seen = set()
        unique = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique.append(url)
        return unique

    @property
    def show_images_json(self):
        """JSON-encoded show_images for the hover preview data attribute."""
        return json.dumps(self.show_images)

    # --- Pricing -----------------------------------------------------------

    @property
    def original_price(self):
        """Sum of the current prices of all included products."""
        return sum((p.current_price for p in self.products.all()), Decimal("0"))

    @property
    def discount_amount(self):
        if self.original_price:
            factor = Decimal(self.discount_percentage) / 100
            return self.original_price * factor
        return Decimal("0")

    @property
    def final_price(self):
        """Computed price after applying the bundle discount."""
        return self.original_price - self.discount_amount

    @property
    def savings(self):
        """Absolute amount the customer saves on the bundle."""
        return self.discount_amount
