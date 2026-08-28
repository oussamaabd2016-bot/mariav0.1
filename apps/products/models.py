"""Product catalogue models for Maira Bijouterie.

The catalogue uses a variant system (ProductVariant) so the same product
can exist in multiple colour/size combinations with per-variant stock and
an optional price override. This scales across bracelets, rings, necklaces
etc. without special-casing each category.
"""
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    """Product category such as Bracelets, Rings, Necklaces."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/categories/", blank=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:list") + f"?category={self.slug}"


class Brand(TimeStampedModel):
    """Jewellery brand (Maira Signature, Xuping, etc.)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Material(TimeStampedModel):
    """Material a product is made from (gold-plated, stainless steel...)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Color(TimeStampedModel):
    """Colour option available for a product."""

    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, blank=True, help_text="e.g. #D4AF37")
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Size(TimeStampedModel):
    """Size option such as S/M/L, ring size 16-20, or One Size."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(TimeStampedModel):
    """A single sellable product in the catalogue."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=230, unique=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=255, blank=True)

    sku = models.CharField("SKU", max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(default=0)
    main_image = models.ImageField(upload_to="products/", blank=True)

    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )

    # Attribute flags
    gold_plated = models.BooleanField(default=False)
    stainless_steel = models.BooleanField(default=False)
    waterproof = models.BooleanField(default=False)
    tarnish_resistant = models.BooleanField(default=False)
    xuping = models.BooleanField(default=False)

    # Merchandising flags
    featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    best_seller = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "product"
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if not self.sku:
            base_sku = f"MB-{slugify(self.name).upper()[:10]}" or "MB-ITEM"
            sku = base_sku
            counter = 1
            while Product.objects.filter(sku=sku).exclude(pk=self.pk).exists():
                sku = f"{base_sku}-{counter}"
                counter += 1
            self.sku = sku
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:detail", kwargs={"slug": self.slug})

    # --- Pricing helpers ---------------------------------------------------

    @property
    def has_discount(self):
        return (
            self.discount_price is not None and self.discount_price < self.price
        )

    @property
    def current_price(self):
        """Effective selling price (discounted when available)."""
        return self.discount_price if self.has_discount else self.price

    @property
    def discount_percentage(self):
        if self.has_discount and self.price:
            return int(round((1 - self.discount_price / self.price) * 100))
        return 0

    # --- Stock helpers ------------------------------------------------------

    def variant_count(self):
        return self.variants.count()

    def total_stock(self):
        """Sum variant stock if variants exist, otherwise product quantity."""
        if self.variant_count():
            return sum(
                v.stock for v in self.variants.all() if v.is_active
            )
        return self.quantity

    def in_stock(self):
        return self.total_stock() > 0

    def related_products(self, limit=4):
        """Other products in the same category, excluding this product."""
        return (
            Product.objects.filter(
                category=self.category, is_active=True
            )
            .exclude(pk=self.pk)
            .distinct()[:limit]
        )

    # --- Rating helpers ------------------------------------------------------

    @property
    def rating_average(self):
        """Mean rating across approved reviews, or None when unreviewed."""
        from django.db.models import Avg

        return self.reviews.filter(is_approved=True).aggregate(
            avg=Avg("rating")
        )["avg"]

    @property
    def rating_count(self):
        """Number of approved reviews for this product."""
        return self.reviews.filter(is_approved=True).count()

    def rating_distribution(self):
        """Count of approved reviews per star (1..5), highest star first."""
        from django.db.models import Count

        counts = dict(
            self.reviews.filter(is_approved=True)
            .values_list("rating")
            .annotate(total=Count("id"))
        )
        return [
            {"stars": stars, "count": counts.get(stars, 0)}
            for stars in range(5, 0, -1)
        ]


class ProductVariant(TimeStampedModel):
    """A concrete colour/size combination of a product with its own stock."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.CASCADE,
        related_name="variants",
        null=True,
        blank=True,
    )
    size = models.ForeignKey(
        Size,
        on_delete=models.CASCADE,
        related_name="variants",
        null=True,
        blank=True,
    )
    stock = models.PositiveIntegerField(default=0)
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional price differing from the base product price.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("id",)
        unique_together = ("product", "color", "size")

    def __str__(self):
        label = self.product.name
        parts = []
        if self.color:
            parts.append(self.color.name)
        if self.size:
            parts.append(self.size.name)
        return f"{label} ({', '.join(parts)})" if parts else label

    @property
    def price(self):
        return self.price_override or self.product.current_price

    def in_stock(self):
        return self.is_active and self.stock > 0


class ProductImage(TimeStampedModel):
    """Additional gallery image belonging to a product."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_main = models.BooleanField(
        default=False,
        help_text="Mark one image as the primary gallery image.",
    )

    class Meta:
        ordering = ("-is_main", "id")

    def __str__(self):
        return f"{self.product.name} image #{self.id}"

    @property
    def url(self):
        return self.image.url if self.image else ""
