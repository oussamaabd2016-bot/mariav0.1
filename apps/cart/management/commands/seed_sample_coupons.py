"""Seed sample coupon codes.

Usage: python manage.py seed_sample_coupons

Creates a few realistic launch coupons so the cart's coupon feature has
something to exercise in dev.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.cart.models import Coupon

COUPONS = [
    {
        "code": "WELCOME10",
        "discount_percentage": 10,
        "min_order_amount": "200.00",
        "days_valid": 180,
    },
    {
        "code": "MAIRA15",
        "discount_percentage": 15,
        "min_order_amount": "300.00",
        "days_valid": 90,
    },
    {
        "code": "BRIDAL20",
        "discount_percentage": 20,
        "min_order_amount": "600.00",
        "days_valid": 60,
    },
]


class Command(BaseCommand):
    help = "Seed sample coupon codes."

    def handle(self, *args, **options):
        created = 0
        for spec in COUPONS:
            coupon, was_created = Coupon.objects.get_or_create(
                code=spec["code"],
                defaults={
                    "discount_percentage": spec["discount_percentage"],
                    "min_order_amount": spec["min_order_amount"],
                    "is_active": True,
                    "valid_from": timezone.now(),
                    "valid_until": timezone.now()
                    + timedelta(days=spec["days_valid"]),
                },
            )
            if was_created:
                created += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Coupons ready ({created} new, {len(COUPONS)} total)."
            )
        )
