"""Tests for the dashboard app: customer hub, order history and staff KPIs."""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.cart.models import Cart
from apps.cart.services import add_item
from apps.orders.models import Order, OrderItem, OrderStatus, PaymentMethod
from apps.products.models import Brand, Category, Material, Product

from .services import staff_metrics


class DashboardTestMixin:
    """Shared setup: two customers, a product and helper to create orders."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="cust@example.com", password="TestPass123!"
        )
        self.other = User.objects.create_user(
            email="other@example.com", password="OtherPass123!"
        )
        self.category = Category.objects.create(name="Bracelets")
        self.brand = Brand.objects.create(name="Maira Signature")
        self.material = Material.objects.create(name="Gold Plated")
        self.product = Product.objects.create(
            name="Bracelet",
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=100,
            quantity=10,
        )
        self.client.login(email="cust@example.com", password="TestPass123!")

    def _make_order(self, user, quantity=1, status=OrderStatus.PENDING, total=None):
        order = Order.objects.create(
            user=user,
            full_name="Jane Customer",
            phone="0612345678",
            address="12 Rue X",
            city="Casablanca",
            payment_method=PaymentMethod.CASH_ON_DELIVERY,
            subtotal=Decimal("100.00"),
            shipping=Decimal("30.00"),
            total=total or Decimal("130.00"),
            status=status,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            sku=self.product.sku,
            unit_price=Decimal("100.00"),
            quantity=quantity,
        )
        return order


class CustomerDashboardTests(DashboardTestMixin, TestCase):
    def test_home_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)

    def test_home_shows_summary_and_recent_orders(self):
        self._make_order(self.user, status=OrderStatus.PENDING)
        self._make_order(self.user, status=OrderStatus.DELIVERED)
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total orders")
        self.assertContains(response, "2")
        self.assertContains(response, "Recent orders")

    def test_home_empty_state(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertContains(response, "You have no orders yet")

    def test_orders_lists_own_orders_only(self):
        self._make_order(self.user)
        self._make_order(self.other)
        response = self.client.get(reverse("dashboard:orders"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["orders"].count(), 1)

    def test_orders_filter_by_status(self):
        pending = self._make_order(self.user, status=OrderStatus.PENDING)
        self._make_order(self.user, status=OrderStatus.DELIVERED)
        response = self.client.get(
            reverse("dashboard:orders"), {"status": "delivered"}
        )
        self.assertEqual(response.context["orders"].count(), 1)
        self.assertNotContains(response, pending.order_number)

    def test_orders_invalid_status_ignored(self):
        self._make_order(self.user, status=OrderStatus.PENDING)
        response = self.client.get(reverse("dashboard:orders"), {"status": "bogus"})
        self.assertEqual(response.context["orders"].count(), 1)

    def test_order_detail_shows_items(self):
        order = self._make_order(self.user, quantity=2)
        response = self.client.get(
            reverse("dashboard:order_detail", args=[order.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.order_number)
        self.assertContains(response, self.product.name)

    def test_order_detail_ownership(self):
        order = self._make_order(self.other)
        response = self.client.get(
            reverse("dashboard:order_detail", args=[order.pk])
        )
        self.assertEqual(response.status_code, 404)


class StaffDashboardTests(DashboardTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.staff = User.objects.create_user(
            email="staff@maira.ma",
            password="StaffPass123!",
            is_staff=True,
        )

    def test_admin_dashboard_blocked_for_customer(self):
        self.client.login(email=self.user.email, password="Pass123!")
        response = self.client.get(reverse("dashboard:admin"))
        self.assertEqual(response.status_code, 403)

    def test_admin_dashboard_anonymous_redirects_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:admin"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_admin_dashboard_ok_for_staff(self):
        self.client.login(email="staff@maira.ma", password="StaffPass123!")
        response = self.client.get(reverse("dashboard:admin"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff dashboard")

    def test_metrics_revenue_excludes_cancelled(self):
        self._make_order(self.user, total=Decimal("200.00"))
        self._make_order(self.user, status=OrderStatus.CANCELLED, total=Decimal("999.00"))
        metrics = staff_metrics()
        self.assertEqual(metrics["revenue_total"], Decimal("200.00"))
        self.assertEqual(metrics["orders_total"], 1)

    def test_metrics_average_order_value(self):
        self._make_order(self.user, total=Decimal("100.00"))
        self._make_order(self.user, total=Decimal("300.00"))
        metrics = staff_metrics()
        self.assertEqual(metrics["average_order_value"], Decimal("200.00"))

    def test_metrics_best_sellers_by_units(self):
        self._make_order(self.user, quantity=3)
        self._make_order(self.user, quantity=1)
        metrics = staff_metrics()
        self.assertEqual(metrics["best_sellers"][0]["product__name"], "Bracelet")
        self.assertEqual(metrics["best_sellers"][0]["units"], 4)

    def test_metrics_low_stock_alerts(self):
        low = Product.objects.create(
            name="Almost Gone", category=self.category, brand=self.brand,
            material=self.material, price=50, quantity=2,
        )
        metrics = staff_metrics()
        self.assertIn(low, metrics["low_stock_products"])
        self.assertNotIn(self.product, metrics["low_stock_products"])

    def test_metrics_new_customers(self):
        User.objects.create_user(email="fresh@example.com", password="x12345!")
        metrics = staff_metrics()
        self.assertGreaterEqual(metrics["new_customers"], 1)

    def test_metrics_status_breakdown(self):
        self._make_order(self.user, status=OrderStatus.PENDING)
        self._make_order(self.user, status=OrderStatus.DELIVERED)
        metrics = staff_metrics()
        by_status = {item["value"]: item["count"] for item in metrics["status_breakdown"]}
        self.assertEqual(by_status["pending"], 1)
        self.assertEqual(by_status["delivered"], 1)

    def test_metrics_revenue_from_order_items(self):
        # OrderItem revenue (unit_price * quantity) aggregates correctly.
        self._make_order(self.user, quantity=2)
        metrics = staff_metrics()
        self.assertEqual(metrics["best_sellers"][0]["revenue"], Decimal("200.00"))


class CartIntegrationTests(DashboardTestMixin, TestCase):
    def test_dashboard_home_shows_cart_count_without_creating_cart(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.context["cart_item_count"], 0)
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    def test_dashboard_home_shows_wishlist_and_cart_counts(self):
        from apps.wishlist.models import WishlistItem

        WishlistItem.objects.create(user=self.user, product=self.product)
        cart = Cart.objects.create(user=self.user)
        add_item(cart, self.product, quantity=2)
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.context["wishlist_count"], 1)
        self.assertEqual(response.context["cart_item_count"], 2)
