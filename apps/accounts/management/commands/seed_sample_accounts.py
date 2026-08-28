"""Seed realistic sample accounts data.

Usage: python manage.py seed_sample_accounts [--count N]

Creates demo customers (with profiles) plus a demo staff user, so every phase
after this one has realistic data to work with.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import Profile

User = get_user_model()

MOROCCAN_NAMES = [
    ("Salma", "El Amrani", "Casablanca", "20000"),
    ("Youssef", "Bennani", "Rabat", "10000"),
    ("Imane", "Berrada", "Marrakech", "40000"),
    ("Omar", "Tazi", "Fes", "30000"),
    ("Nadia", "Chraibi", "Tangier", "90000"),
]


class Command(BaseCommand):
    help = "Seed sample customers, staff user and profiles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=len(MOROCCAN_NAMES),
            help="Number of sample customers to create.",
        )

    def handle(self, *args, **options):
        password = "Maira@2026!Demo"
        count = min(options["count"], len(MOROCCAN_NAMES))
        created = 0

        for i in range(count):
            first, last, city, postal = MOROCCAN_NAMES[i]
            email = f"{first.lower()}.{last.lower().replace(' ', '')}@example.com"
            if User.objects.filter(email=email).exists():
                continue

            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first,
                last_name=last,
            )
            Profile.objects.create(
                user=user,
                phone=f"06{i+1:02d}000000",
                address=f"{12 + i} Rue Hassan II",
                city=city,
                postal_code=postal,
            )
            created += 1

        # Demo staff user with admin access.
        if not User.objects.filter(email="staff@maira.ma").exists():
            User.objects.create_user(
                email="staff@maira.ma",
                password=password,
                first_name="Maira",
                last_name="Staff",
                is_staff=True,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} sample user(s)."))
        self.stdout.write(
            self.style.WARNING(
                "Demo password for all sample users: Maira@2026!Demo"
            )
        )
