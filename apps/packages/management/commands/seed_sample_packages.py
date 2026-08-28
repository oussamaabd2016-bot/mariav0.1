"""Seed sample jewellery packages/bundles.

Usage: python manage.py seed_sample_packages

Creates a few curated bundles from existing products so the packages pages
have realistic content. Requires products to exist (run
``seed_sample_products`` first).
"""
from django.core.management.base import BaseCommand

from apps.packages.models import Package
from apps.products.models import Product

PACKAGES = [
    {
        "name": "Everyday Gold Essentials",
        "description": "The perfect starter bundle: a gold-plated chain bracelet "
        "paired with a minimal bar necklace for effortless everyday elegance.",
        "discount": 15,
        "product_names": [
            "Gold Plated Chain Bracelet",
            "Minimal Bar Necklace",
        ],
    },
    {
        "name": "Bridal Glow Set",
        "description": "A complete bridal look — layered pearl necklace, drop "
        "pearl earrings and the signature twisted ring.",
        "discount": 20,
        "product_names": [
            "Layered Pearl Necklace",
            "Drop Pearl Earrings",
            "Rose Gold Twisted Ring",
        ],
    },
    {
        "name": "Hoop Lover's Trio",
        "description": "Three hoop styles in one bundle for the hoop earring "
        "collector: gold hoops, drop hoops and a matching everyday set.",
        "discount": 10,
        "product_names": [
            "Hoop Earrings 24k Gold",
            "Everyday Hoop Set (3 pairs)",
            "Drop Pearl Earrings",
        ],
    },
    {
        "name": "Stainless Steel Power Pair",
        "description": "Waterproof stainless steel bracelet and necklace that "
        "never lose their shine — ideal for daily wear and sport.",
        "discount": 12,
        "product_names": [
            "Stainless Steel Tennis Bracelet",
            "Gold Infinity Pendant Necklace",
        ],
    },
]


class Command(BaseCommand):
    help = "Seed sample jewellery packages from existing products."

    def handle(self, *args, **options):
        Package.objects.all().delete()
        created = 0

        for spec in PACKAGES:
            products = list(
                Product.objects.filter(
                    name__in=spec["product_names"]
                ).distinct()
            )
            if len(products) != len(spec["product_names"]):
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping '{spec['name']}': some products are missing. "
                        "Run seed_sample_products first."
                    )
                )
                continue

            package = Package.objects.create(
                name=spec["name"],
                description=spec["description"],
                discount_percentage=spec["discount"],
            )
            package.products.set(products)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {created} package(s).")
        )
