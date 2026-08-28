"""Seed sample newsletter subscribers.

Usage: python manage.py seed_sample_newsletter

Creates a handful of subscriber rows so the admin list has data.
"""
from django.core.management.base import BaseCommand

from apps.home.models import NewsletterSubscriber

EMAILS = [
    "laila.k@example.com",
    "mehdi.s@example.com",
    "kawtar.b@example.com",
]


class Command(BaseCommand):
    help = "Seed sample newsletter subscribers."

    def handle(self, *args, **options):
        created = 0
        for email in EMAILS:
            _, was_created = NewsletterSubscriber.objects.get_or_create(email=email)
            created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(f"Seeded {created} newsletter subscriber(s).")
        )
