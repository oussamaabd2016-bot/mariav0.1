"""Tests for the orders app: model, checkout flow and guest blocking."""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.cart.models import Cart, Coupon
from apps.cart.services import add_item, get_or_create_cart
from apps.products.models import Brand, Category, Material, Product

from .models import Order, OrderItem, OrderStatus, PaymentMethod
from .services import place_order


class OrderTestMixin:
    """Shared setup: user, category/brand/material and a plain product."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="cust@example.com", password="TestPass123!"
        )
        self.category = Category.objects.create(name="Bracelets")
        self.brand = Brand.objects.create(name="Maira Signature")
        self.material = Material.objects.create(name="Gold Plated")
        self.product = self._make_product("Bracelet", price=100, quantity=10)
        self.client.login(email="cust@example.com", password="TestPass123!")

    def _make_product(self, name, price, quantity=10):
        return Product.objects.create(
            name=name,
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=price,
            quantity=quantity,
        )

    def _cart(self):
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/")
        request.session = self.client.session
        request.user = self.user
        return get_or_create_cart(request)

    def _add(self, product, quantity=1):
        add_item(self._cart(), product, quantity=quantity)

    def _checkout_data(self, **overrides):
        data = {
            "full_name": "Jane Customer",
            "phone": "0612345678",
            "address": "12 Rue des Fleurs",
            "city": "Casablanca",
            "postal_code": "20000",
            "payment_method": PaymentMethod.CASH_ON_DELIVERY,
            "notes": "",
        }
        data.update(overrides)
        return data


class OrderModelTests(OrderTestMixin, TestCase):
    def test_order_number_generated(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Jane",
            phone="0612345678",
            address="Addr",
            city="Casablanca",
            payment_method=PaymentMethod.CASH_ON_DELIVERY,
            subtotal=Decimal("100.00"),
            total=Decimal("130.00"),
        )
        self.assertTrue(order.order_number.startswith("MB-2026-"))
        self.assertTrue(order.order_number.endswith("000001"))

    def test_order_number_sequential(self):
        Order.objects.create(
            user=self.user, full_name="A", phone="1", address="X", city="C",
            payment_method=PaymentMethod.CASH_ON_DELIVERY,
            subtotal=Decimal("0"), total=Decimal("0"),
        )
        second = Order.objects.create(
            user=self.user, full_name="B", phone="2", address="Y", city="C",
            payment_method=PaymentMethod.CASH_ON_DELIVERY,
            subtotal=Decimal("0"), total=Decimal("0"),
        )
        self.assertEqual(second.order_number[-6:], "000002")

    def test_whatsapp_link_contains_summary(self):
        order = Order.objects.create(
            user=self.user, full_name="Jane", phone="0612345678", address="X",
            city="Casablanca", payment_method=PaymentMethod.CASH_ON_DELIVERY,
            subtotal=Decimal("100.00"), total=Decimal("130.00"),
        )
        OrderItem.objects.create(
            order=order, product=self.product,
            product_name=self.product.name, sku=self.product.sku,
            unit_price=Decimal("100.00"), quantity=1,
        )
        link = order.whatsapp_link()
        self.assertTrue(link.startswith("https://wa.me/"))
        self.assertIn(order.order_number, link)
        self.assertIn("Total", link)

    def test_order_status_choices(self):
        statuses = [choice[0] for choice in OrderStatus.choices]
        self.assertEqual(
            statuses, ["pending", "processing", "delivered", "cancelled"]
        )


class CheckoutViewTests(OrderTestMixin, TestCase):
    def test_checkout_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 302)

    def test_checkout_with_empty_cart_redirects(self):
        response = self.client.get(reverse("orders:checkout"))
        self.assertRedirects(response, reverse("cart:index"))

    def test_checkout_page_renders_form_and_summary(self):
        self._add(self.product, quantity=2)
        response = self.client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shipping details")
        self.assertContains(response, self.product.name)
        self.assertContains(response, "200.00")

    def test_checkout_prefills_from_profile(self):
        from apps.accounts.models import Profile

        Profile.objects.create(
            user=self.user,
            phone="0600000000",
            address="Rue X",
            city="Rabat",
            postal_code="10000",
        )
        self._add(self.product)
        response = self.client.get(reverse("orders:checkout"))
        self.assertContains(response, "0600000000")
        self.assertContains(response, "Rabat")

    def test_place_order_creates_order_and_clears_cart(self):
        self._add(self.product, quantity=2)
        response = self.client.post(
            reverse("orders:checkout"), self._checkout_data()
        )
        order = Order.objects.get()
        self.assertRedirects(response, order.get_absolute_url())
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total, Decimal("230.00"))  # 200 + 30 shipping
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.get().quantity, 2)
        self.assertFalse(self._cart().items.exists())

    def test_place_order_snapshots_product(self):
        self._add(self.product, quantity=1)
        self.client.post(reverse("orders:checkout"), self._checkout_data())
        item = OrderItem.objects.get()
        self.assertEqual(item.product_name, self.product.name)
        self.assertEqual(item.sku, self.product.sku)
        self.assertEqual(item.unit_price, Decimal("100.00"))

    def test_place_order_decrements_stock(self):
        self._add(self.product, quantity=3)
        self.client.post(reverse("orders:checkout"), self._checkout_data())
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 7)

    def test_place_order_records_coupon(self):
        coupon = Coupon.objects.create(code="SAVE10", discount_percentage=10)
        self._add(self.product, quantity=5)  # subtotal 500
        cart = self._cart()
        cart.coupon = coupon
        cart.save()
        self.client.post(reverse("orders:checkout"), self._checkout_data())
        order = Order.objects.get()
        self.assertEqual(order.coupon, coupon)
        self.assertEqual(order.coupon_code, "SAVE10")
        self.assertEqual(order.discount, Decimal("50.00"))
        self.assertEqual(order.total, Decimal("450.00"))  # free shipping > 400

    def test_insufficient_stock_blocks_order(self):
        self._add(self.product, quantity=10)
        # Reduce stock below the cart quantity after adding.
        Product.objects.filter(pk=self.product.pk).update(quantity=3)
        response = self.client.post(
            reverse("orders:checkout"), self._checkout_data()
        )
        self.assertRedirects(response, reverse("cart:index"))
        self.assertFalse(Order.objects.exists())

    def test_bank_transfer_order_confirmation_shows_details(self):
        self._add(self.product, quantity=1)
        self.client.post(
            reverse("orders:checkout"),
            self._checkout_data(
                payment_method=PaymentMethod.BANK_TRANSFER
            ),
        )
        order = Order.objects.get()
        response = self.client.get(order.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bank transfer details")
        self.assertContains(response, order.order_number)
        self.assertContains(response, "https://wa.me/")

    def test_confirmation_requires_login_and_ownership(self):
        order = Order.objects.create(
            user=self.user, full_name="Jane", phone="1", address="X", city="C",
            payment_method=PaymentMethod.CASH_ON_DELIVERY,
            subtotal=Decimal("0"), total=Decimal("0"),
        )
        other = User.objects.create_user(
            email="other@example.com", password="OtherPass123!"
        )
        self.client.logout()
        self.client.login(email="other@example.com", password="OtherPass123!")
        response = self.client.get(order.get_absolute_url())
        self.assertEqual(response.status_code, 404)


class OrderAdminTests(TestCase):
    """Admin change pages must render, incl. the empty inline row."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="admin@maira.ma", password="AdminPass123!"
        )
        self.client.force_login(self.superuser)

    def test_order_change_page_renders(self):
        order = Order.objects.create(
            user=self.superuser,
            full_name="A",
            phone="1",
            address="X",
            city="C",
            payment_method=PaymentMethod.CASH_ON_DELIVERY,
            subtotal=Decimal("100.00"),
            total=Decimal("130.00"),
        )
        OrderItem.objects.create(
            order=order, product=None, product_name="Bracelet",
            sku="MB-BRACELET", unit_price=Decimal("100.00"), quantity=1,
        )
        response = self.client.get(
            f"/admin/orders/order/{order.pk}/change/"
        )
        self.assertEqual(response.status_code, 200)

    def test_orderitem_admin_page_renders(self):
        response = self.client.get("/admin/orders/orderitem/")
        self.assertEqual(response.status_code, 200)


class PlaceOrderServiceTests(OrderTestMixin, TestCase):
    def test_place_order_raises_on_empty_cart(self):
        with self.assertRaises(ValueError):
            place_order(
                self.user,
                Cart.objects.create(session_key="x"),
                full_name="A", phone="1", address="X", city="C",
                postal_code="", payment_method=PaymentMethod.CASH_ON_DELIVERY,
            )

    def test_variant_order_decrements_variant_stock(self):
        from apps.products.models import Color, Size

        color = Color.objects.create(name="Gold")
        size = Size.objects.create(name="M")
        product = self._make_product("Varied", price=50, quantity=0)
        variant = product.variants.create(color=color, size=size, stock=4)
        cart = Cart.objects.create(session_key="y")
        add_item(cart, product, variant=variant, quantity=2)
        place_order(
            self.user, cart,
            full_name="A", phone="1", address="X", city="C",
            postal_code="", payment_method=PaymentMethod.CASH_ON_DELIVERY,
        )
        variant.refresh_from_db()
        self.assertEqual(variant.stock, 2)
