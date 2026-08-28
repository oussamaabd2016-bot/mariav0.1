"""Seed sample reviews for the reviews app.

Usage: python manage.py seed_sample_reviews

Creates reviews for products the sample customers actually purchased
(run seed_sample_accounts + seed_sample_products + seed_sample_orders
first) so the review list, rating summary and staff dashboard all have
realistic data. One review gets a generated photo.
"""
import io

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from apps.accounts.models import User
from apps.orders.models import Order, OrderStatus
from apps.products.models import Product
from apps.reviews.models import Review

# (email, product, rating, comment) — purchases guaranteed by seed_sample_orders.
SAMPLES = [
    (
        "salma.elamrani@example.com",
        "Gold Plated Chain Bracelet",
        5,
        "Lovely finish, exactly like the photos. It hasn't tarnished at all in daily wear.",
    ),
    (
        "salma.elamrani@example.com",
        "Hoop Earrings 24k Gold",
        4,
        "Beautiful and lightweight. The gold looks rich under the light.",
    ),
    (
        "youssef.bennani@example.com",
        "Layered Pearl Necklace",
        5,
        "Stunning piece, great packaging and fast delivery.",
    ),
    (
        "imane.berrada@example.com",
        "Gold Infinity Pendant Necklace",
        4,
        "Elegant and waterproof — exactly what I wanted for everyday wear.",
    ),
]


class Command(BaseCommand):
    help = "Seed sample product reviews for purchased items."

    def _review_photo(self):
        """Generate a small placeholder review photo."""
        image = Image.new("RGB", (360, 360), "#FFF8E7")
        draw = ImageDraw.Draw(image)
        draw.ellipse((130, 120, 230, 220), fill="#D4AF37")
        draw.text((30, 300), "Maira Review", fill="#8C6A1D")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        return ContentFile(buffer.getvalue())

    def handle(self, *args, **options):
        created = 0
        updated = 0
        photo = self._review_photo()

        for email, product_name, rating, comment in SAMPLES:
            user = User.objects.filter(email=email).first()
            product = Product.objects.filter(name=product_name).first()
            if user is None or product is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping review for '{email}' / '{product_name}': "
                        "missing user or product. Run the seed commands first."
                    )
                )
                continue

            # Skip if the user has no non-cancelled order with this product.
            purchased = Order.objects.filter(
                user=user, items__product=product
            ).exclude(status=OrderStatus.CANCELLED).exists()
            if not purchased:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping review for '{email}' on '{product_name}': "
                        "no matching purchased order."
                    )
                )
                continue

            review, was_created = Review.objects.update_or_create(
                user=user,
                product=product,
                defaults={"rating": rating, "comment": comment},
            )
            if was_created:
                created += 1
            else:
                updated += 1

            # Give the first review a photo.
            if not review.image:
                name = f"review-{review.product.slug}.jpg"
                review.image.save(name, photo, save=True)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created} review(s), updated {updated}."
            )
        )
