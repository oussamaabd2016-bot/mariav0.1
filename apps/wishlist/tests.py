"""Tests for the wishlist app: add, index, remove and move-to-cart."""
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.products.models import Brand, Category, Material, Product

from .models import WishlistItem


class WishlistTestMixin:
    def setUp(self):
        self.user = User.objects.create_user(
            email="cust@example.com", password="TestPass123!"
        )
        self.category = Category.objects.create(name="Rings")
        self.brand = Brand.objects.create(name="Maira Signature")
        self.material = Material.objects.create(name="Stainless Steel")
        self.product = Product.objects.create(
            name="Rose Gold Twisted Ring",
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=150,
            quantity=5,
        )
        self.client.login(email="cust@example.com", password="TestPass123!")


class WishlistViewTests(WishlistTestMixin, TestCase):
    def test_index_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("wishlist:index"))
        self.assertRedirects(
            response, f"{reverse('accounts:login')}?next={reverse('wishlist:index')}"
        )

    def test_add_requires_login(self):
        self.client.logout()
        response = self.client.post(
            reverse("wishlist:add", args=[self.product.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_add_product_to_wishlist(self):
        response = self.client.post(
            reverse("wishlist:add", args=[self.product.id])
        )
        self.assertRedirects(response, self.product.get_absolute_url())
        self.assertTrue(
            WishlistItem.objects.filter(
                user=self.user, product=self.product
            ).exists()
        )

    def test_add_duplicate_is_idempotent(self):
        WishlistItem.objects.create(user=self.user, product=self.product)
        self.client.post(reverse("wishlist:add", args=[self.product.id]))
        self.assertEqual(
            WishlistItem.objects.filter(
                user=self.user, product=self.product
            ).count(),
            1,
        )

    def test_index_lists_items(self):
        WishlistItem.objects.create(user=self.user, product=self.product)
        response = self.client.get(reverse("wishlist:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_index_empty(self):
        response = self.client.get(reverse("wishlist:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your wishlist is empty")

    def test_remove_item(self):
        item = WishlistItem.objects.create(user=self.user, product=self.product)
        response = self.client.post(reverse("wishlist:remove", args=[item.id]))
        self.assertRedirects(response, reverse("wishlist:index"))
        self.assertFalse(WishlistItem.objects.filter(pk=item.pk).exists())

    def test_remove_does_not_touch_other_users_items(self):
        other = User.objects.create_user(
            email="other@example.com", password="OtherPass123!"
        )
        item = WishlistItem.objects.create(user=other, product=self.product)
        response = self.client.post(reverse("wishlist:remove", args=[item.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(WishlistItem.objects.filter(pk=item.pk).exists())

    def test_move_to_cart(self):
        item = WishlistItem.objects.create(user=self.user, product=self.product)
        response = self.client.post(
            reverse("wishlist:move_to_cart", args=[item.id])
        )
        self.assertRedirects(response, reverse("cart:index"))
        self.assertFalse(WishlistItem.objects.filter(pk=item.pk).exists())
        cart = self.user.cart
        self.assertEqual(cart.items.get().product, self.product)


class WishlistModelTests(WishlistTestMixin, TestCase):
    def test_unique_together(self):
        WishlistItem.objects.create(user=self.user, product=self.product)
        duplicate = WishlistItem(
            user=self.user, product=self.product
        )
        with self.assertRaises(Exception):
            duplicate.save()

    def test_str(self):
        item = WishlistItem.objects.create(user=self.user, product=self.product)
        self.assertEqual(str(item), "cust@example.com → Rose Gold Twisted Ring")
