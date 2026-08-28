"""Tests for the cart app: service logic, views, coupons and login merge."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.products.models import Brand, Category, Color, Material, Product, Size

from .models import Cart, Coupon
from .services import add_item, cart_totals, get_or_create_cart, validate_item


class CartTestMixin:
    """Shared setup: category, brand, material and a plain product."""

    def setUp(self):
        self.category = Category.objects.create(name="Bracelets")
        self.brand = Brand.objects.create(name="Maira Signature")
        self.material = Material.objects.create(name="Gold Plated")
        self.product = self._make_product("Bracelet", price=100, quantity=10)

    def _make_product(self, name, price, quantity=10):
        return Product.objects.create(
            name=name,
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=price,
            quantity=quantity,
        )

    def _add_to_cart(self, product, quantity=1, color_id=None, size_id=None):
        data = {"product_id": product.id, "quantity": quantity}
        if color_id:
            data["color"] = color_id
        if size_id:
            data["size"] = size_id
        return self.client.post(reverse("cart:add"), data)

    def _cart(self):
        """The Cart belonging to the test client's current state."""
        factory = RequestFactory()
        request = factory.get("/")
        request.session = self.client.session
        request.user = getattr(self.client, "_login_user", None) or AnonymousUser()
        return get_or_create_cart(request)


class CartServiceTests(CartTestMixin, TestCase):
    def test_add_item_creates_and_merges(self):
        cart = Cart.objects.create(session_key="abc123")
        add_item(cart, self.product, quantity=2)
        add_item(cart, self.product, quantity=3)
        item = cart.items.get()
        self.assertEqual(item.quantity, 5)

    def test_add_item_caps_at_stock(self):
        cart = Cart.objects.create(session_key="abc123")
        add_item(cart, self.product, quantity=50)
        self.assertEqual(cart.items.get().quantity, 10)

    def test_validate_rejects_inactive_product(self):
        product = self._make_product("Gone", price=10)
        product.is_active = False
        product.save()
        ok, _ = validate_item(product)
        self.assertFalse(ok)

    def test_validate_rejects_out_of_stock_plain_product(self):
        product = self._make_product("Empty", price=10, quantity=0)
        ok, _ = validate_item(product)
        self.assertFalse(ok)

    def test_validate_requires_variant_for_variant_product(self):
        color = Color.objects.create(name="Gold")
        size = Size.objects.create(name="M")
        product = self._make_product("Varied", price=50, quantity=0)
        variant = product.variants.create(color=color, size=size, stock=3)
        ok, _ = validate_item(product, variant=None)
        self.assertFalse(ok)
        ok, _ = validate_item(product, variant=variant)
        self.assertTrue(ok)

    def test_line_total_uses_variant_price(self):
        color = Color.objects.create(name="Gold")
        size = Size.objects.create(name="M")
        product = self._make_product("Varied", price=50, quantity=0)
        variant = product.variants.create(
            color=color, size=size, stock=3, price_override=70
        )
        cart = Cart.objects.create(session_key="abc123")
        item = add_item(cart, product, variant=variant, quantity=2)
        self.assertEqual(item.line_total, Decimal("140.00"))

    def test_cart_totals_with_coupon_and_shipping(self):
        cart = Cart.objects.create(session_key="abc123")
        add_item(cart, self.product, quantity=2)  # subtotal 200
        coupon = Coupon.objects.create(code="SAVE10", discount_percentage=10)
        cart.coupon = coupon
        cart.save()
        totals = cart_totals(cart)
        self.assertEqual(totals["subtotal"], Decimal("200.00"))
        self.assertEqual(totals["coupon_discount"], Decimal("20.00"))
        # Below free-shipping threshold -> flat shipping.
        self.assertEqual(totals["shipping"], Decimal("30.00"))
        self.assertEqual(totals["total"], Decimal("210.00"))

    def test_free_shipping_over_threshold(self):
        cart = Cart.objects.create(session_key="abc123")
        add_item(cart, self.product, quantity=5)  # subtotal 500
        totals = cart_totals(cart)
        self.assertEqual(totals["shipping"], Decimal("0.00"))
        self.assertEqual(totals["total"], Decimal("500.00"))

    def test_empty_cart_has_no_shipping(self):
        cart = Cart.objects.create(session_key="abc123")
        totals = cart_totals(cart)
        self.assertEqual(totals["total"], Decimal("0.00"))
        self.assertEqual(totals["shipping"], Decimal("0.00"))

    def test_coupon_invalid_below_minimum(self):
        cart = Cart.objects.create(session_key="abc123")
        add_item(cart, self.product, quantity=1)  # subtotal 100
        coupon = Coupon.objects.create(
            code="MIN200", discount_percentage=10, min_order_amount=200
        )
        cart.coupon = coupon
        cart.save()
        totals = cart_totals(cart)
        self.assertFalse(totals["coupon_valid"])
        self.assertEqual(totals["coupon_discount"], Decimal("0.00"))

    def test_coupon_expired(self):
        cart = Cart.objects.create(session_key="abc123")
        add_item(cart, self.product, quantity=5)
        coupon = Coupon.objects.create(
            code="OLD",
            discount_percentage=10,
            valid_until=timezone.now() - timedelta(days=1),
        )
        cart.coupon = coupon
        cart.save()
        self.assertFalse(cart_totals(cart)["coupon_valid"])


class CartAdminTests(TestCase):
    """Admin change pages must render, incl. the empty inline row."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="admin@maira.ma", password="AdminPass123!"
        )
        self.client.force_login(self.superuser)

    def test_cart_change_page_renders(self):
        cart = Cart.objects.create(user=self.superuser)
        response = self.client.get(f"/admin/cart/cart/{cart.pk}/change/")
        self.assertEqual(response.status_code, 200)

    def test_coupon_admin_page_renders(self):
        Coupon.objects.create(code="TEST10", discount_percentage=10)
        response = self.client.get("/admin/cart/coupon/")
        self.assertEqual(response.status_code, 200)


class CartViewTests(CartTestMixin, TestCase):
    def test_guest_adds_to_cart(self):
        response = self._add_to_cart(self.product, quantity=2)
        self.assertRedirects(response, reverse("cart:index"))
        cart = self._cart()
        self.assertEqual(self._count(cart), 2)

    def test_index_shows_item_and_totals(self):
        self._add_to_cart(self.product, quantity=2)
        response = self.client.get(reverse("cart:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, "200.00")

    def test_update_quantity(self):
        self._add_to_cart(self.product, quantity=2)
        cart = self._cart()
        item = cart.items.get()
        self.client.post(reverse("cart:update"), {"item_id": item.id, "quantity": 5})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    def test_update_zero_removes_item(self):
        self._add_to_cart(self.product)
        cart = self._cart()
        item = cart.items.get()
        self.client.post(reverse("cart:update"), {"item_id": item.id, "quantity": 0})
        self.assertFalse(cart.items.exists())

    def test_remove_item(self):
        self._add_to_cart(self.product)
        cart = self._cart()
        item = cart.items.get()
        self.client.post(reverse("cart:remove"), {"item_id": item.id})
        self.assertFalse(cart.items.exists())

    def test_update_partial_returns_rendered_cart(self):
        self._add_to_cart(self.product)
        cart = self._cart()
        item = cart.items.get()
        response = self.client.post(
            reverse("cart:update") + "?partial=1",
            {"item_id": item.id, "quantity": 3},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cart-content")

    def test_apply_valid_coupon(self):
        Coupon.objects.create(code="SAVE10", discount_percentage=10)
        self._add_to_cart(self.product, quantity=5)  # subtotal 500
        response = self.client.post(
            reverse("cart:apply_coupon"), {"code": "save10"}
        )
        self.assertRedirects(response, reverse("cart:index"))
        cart = self._cart()
        self.assertEqual(cart.coupon.code, "SAVE10")

    def test_apply_unknown_coupon(self):
        self._add_to_cart(self.product)
        self.client.post(reverse("cart:apply_coupon"), {"code": "NOPE"})
        cart = self._cart()
        self.assertIsNone(cart.coupon)

    def test_remove_coupon(self):
        coupon = Coupon.objects.create(code="SAVE10", discount_percentage=10)
        self._add_to_cart(self.product, quantity=5)
        cart = self._cart()
        cart.coupon = coupon
        cart.save()
        self.client.post(reverse("cart:remove_coupon"))
        cart.refresh_from_db()
        self.assertIsNone(cart.coupon)

    def test_add_out_of_stock_plain_product(self):
        product = self._make_product("Empty", price=10, quantity=0)
        response = self._add_to_cart(product)
        self.assertRedirects(response, product.get_absolute_url())
        cart = self._cart()
        self.assertFalse(cart.items.exists())

    def test_variant_product_requires_variant(self):
        color = Color.objects.create(name="Gold")
        size = Size.objects.create(name="M")
        product = self._make_product("Varied", price=50, quantity=0)
        product.variants.create(color=color, size=size, stock=3)
        response = self._add_to_cart(product)
        self.assertRedirects(response, product.get_absolute_url())
        cart = self._cart()
        self.assertFalse(cart.items.exists())

    def test_authenticated_user_keeps_persistent_cart(self):
        User.objects.create_user(email="cust@example.com", password="TestPass123!")
        self.client.login(email="cust@example.com", password="TestPass123!")
        self._add_to_cart(self.product, quantity=3)
        self.client.logout()
        self.client.login(email="cust@example.com", password="TestPass123!")
        cart = Cart.objects.get(user__email="cust@example.com")
        self.assertEqual(cart.items.get().quantity, 3)

    def test_guest_cart_merges_on_login(self):
        user = User.objects.create_user(
            email="cust@example.com", password="TestPass123!"
        )
        other = self._make_product("Other", price=60)
        self._add_to_cart(self.product, quantity=2)
        self._add_to_cart(other, quantity=1)

        guest_cart = Cart.objects.filter(
            session_key=self.client.session.session_key
        )
        self.assertTrue(guest_cart.exists())

        self.client.login(email="cust@example.com", password="TestPass123!")

        user_cart = Cart.objects.get(user=user)
        self.assertEqual(self._count(user_cart), 3)
        self.assertFalse(guest_cart.exists())

    def _count(self, cart):
        from .services import cart_count

        return cart_count(cart)
