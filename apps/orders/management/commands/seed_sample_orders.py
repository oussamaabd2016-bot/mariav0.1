"""Seed sample orders for the orders app.

Usage: python manage.py seed_sample_orders

Creates a handful of realistic orders (COD and bank transfer, a couple of
statuses) using the same ``place_order`` service the checkout view uses.
Requires products and a customer to exist (run ``seed_sample_products`` and
``seed_sample_accounts`` first). Orders are created directly against carts
so stock is decremented exactly like a real checkout.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.cart.models import Cart
from apps.cart.services import add_item
from apps.orders.models import Order, OrderStatus, PaymentMethod
from apps.orders.services import place_order
from apps.products.models import Product, ProductVariant

SAMPLES = [
    {
        "email": "salma.elamrani@example.com",
        "status": OrderStatus.PENDING,
        "payment": PaymentMethod.CASH_ON_DELIVERY,
        "phone": "0612345678",
        "address": "12 Rue des Fleurs, Maârif",
        "city": "Casablanca",
        "postal_code": "20100",
        "items": [("Gold Plated Chain Bracelet", 1), ("Hoop Earrings 24k Gold", 2)],
    },
    {
        "email": "youssef.bennani@example.com",
        "status": OrderStatus.PROCESSING,
        "payment": PaymentMethod.BANK_TRANSFER,
        "phone": "0698765432",
        "address": "5 Avenue Hassan II",
        "city": "Rabat",
        "postal_code": "10000",
        "items": [("Layered Pearl Necklace", 1)],
    },
    {
        "email": "salma.elamrani@example.com",
        "status": OrderStatus.DELIVERED,
        "payment": PaymentMethod.CASH_ON_DELIVERY,
        "phone": "0612345678",
        "address": "12 Rue des Fleurs, Maârif",
        "city": "Casablanca",
        "postal_code": "20100",
        "items": [("Minimal Bar Necklace", 1), ("Drop Pearl Earrings", 1)],
    },
    {
        "email": "imane.berrada@example.com",
        "status": OrderStatus.PROCESSING,
        "payment": PaymentMethod.BANK_TRANSFER,
        "phone": "0665554433",
        "address": "3 Rue de la Menara",
        "city": "Marrakech",
        "postal_code": "40000",
        "items": [("Hoop Earrings 24k Gold", 2), ("Gold Infinity Pendant Necklace", 1)],
    },
    {
        "email": "omar.tazi@example.com",
        "status": OrderStatus.CANCELLED,
        "payment": PaymentMethod.CASH_ON_DELIVERY,
        "phone": "0650001111",
        "address": "8 Avenue des Fes",
        "city": "Fes",
        "postal_code": "30000",
        "items": [("Stainless Steel Tennis Bracelet", 1)],
    },
]


class Command(BaseCommand):
    help = "Seed sample orders via the same service used by checkout."

    def handle(self, *args, **options):
        existing = Order.objects.count()
        created = 0

        for spec in SAMPLES:
            user = User.objects.filter(email=spec["email"]).first()
            if user is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping: no user '{spec['email']}'. "
                        "Run seed_sample_accounts first."
                    )
                )
                continue

            cart, _ = Cart.objects.get_or_create(user=user)
            cart.items.all().delete()
            cart.coupon = None
            cart.save(update_fields=("coupon", "updated_at"))
            missing = False
            for name, quantity in spec["items"]:
                product = Product.objects.filter(
                    name=name, is_active=True
                ).first()
                if product is None:
                    missing = True
                    break
                add_item(cart, product, quantity=quantity)
            if missing or not cart.items.exists():
                cart.delete()
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping sample for '{spec['email']}': product missing. "
                        "Run seed_sample_products first."
                    )
                )
                continue

            order = place_order(
                user,
                cart,
                full_name=user.get_full_name() or user.email,
                phone=spec["phone"],
                address=spec["address"],
                city=spec["city"],
                postal_code=spec["postal_code"],
                payment_method=spec["payment"],
                notes="Seeded sample order.",
            )
            order.status = spec["status"]
            order.save(update_fields=("status",))
            created += 1

        # Give the staff dashboard a low-stock alert to display.
        demo = ProductVariant.objects.filter(
            product__name="Stainless Steel Tennis Bracelet", is_active=True
        ).first()
        if demo:
            demo.stock = 2
            demo.save(update_fields=("stock",))

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created} order(s). Total orders now: {existing + created}."
            )
        )
