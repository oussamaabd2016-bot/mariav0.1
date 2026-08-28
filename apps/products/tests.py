"""Tests for the products app: models, list/detail/search views."""
from django.test import TestCase
from django.urls import reverse

from .models import (
    Brand,
    Category,
    Color,
    Material,
    Product,
    ProductImage,
    ProductVariant,
    Size,
)


class ProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Rings")
        self.brand = Brand.objects.create(name="Maira Signature")
        self.material = Material.objects.create(name="Gold Plated")
        self.color = Color.objects.create(name="Gold", hex_code="#D4AF37")
        self.size = Size.objects.create(name="17")

    def _make_product(self, price=200, discount=None, **kwargs):
        defaults = {"name": "Test Ring", "quantity": 10}
        defaults.update(kwargs)
        return Product.objects.create(
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=price,
            discount_price=discount,
            **defaults,
        )

    def test_product_slug_auto_generated(self):
        product = self._make_product(name="Test Ring")
        self.assertEqual(product.slug, "test-ring")

    def test_current_price_returns_discount_when_available(self):
        product = self._make_product(price=200, discount=150)
        self.assertTrue(product.has_discount)
        self.assertEqual(product.current_price, 150)
        self.assertEqual(product.discount_percentage, 25)

    def test_current_price_returns_base_price_without_discount(self):
        product = self._make_product(price=200)
        self.assertFalse(product.has_discount)
        self.assertEqual(product.current_price, 200)

    def test_in_stock_from_product_quantity(self):
        product = self._make_product(quantity=5)
        self.assertTrue(product.in_stock())
        product.quantity = 0
        product.save()
        self.assertFalse(product.in_stock())

    def test_variant_price_uses_override(self):
        product = self._make_product(price=200)
        variant = ProductVariant.objects.create(
            product=product,
            color=self.color,
            size=self.size,
            stock=3,
            price_override=180,
        )
        self.assertEqual(variant.price, 180)
        self.assertTrue(variant.in_stock())

    def test_total_stock_sums_variants(self):
        product = self._make_product(quantity=1)
        ProductVariant.objects.create(product=product, size=self.size, stock=2)
        ProductVariant.objects.create(product=product, size=self.size, stock=3)
        self.assertEqual(product.total_stock(), 5)

    def test_related_products_same_category(self):
        other_category = Category.objects.create(name="Bracelets")
        related = self._make_product(name="Another Ring")
        unrelated = Product.objects.create(
            name="Bracelet",
            category=other_category,
            brand=self.brand,
            material=self.material,
            price=100,
            quantity=5,
        )
        product = self._make_product(name="Main Ring")
        result = product.related_products()
        self.assertIn(related, result)
        self.assertNotIn(unrelated, result)
        self.assertNotIn(product, result)

    def test_product_variant_unique_together(self):
        product = self._make_product()
        ProductVariant.objects.create(product=product, color=self.color, size=self.size)
        with self.assertRaises(Exception):
            ProductVariant.objects.create(product=product, color=self.color, size=self.size)

    def test_product_image_str(self):
        product = self._make_product()
        img = ProductImage(product=product, alt_text="gallery")
        self.assertIn("Test Ring", str(img))


class ProductListViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Rings")
        self.brand = Brand.objects.create(name="Maira Signature")
        self.material = Material.objects.create(name="Gold Plated")
        self.color = Color.objects.create(name="Gold")
        self.size = Size.objects.create(name="17")

    def _make_product(self, name="Ring", price=200, active=True, **kwargs):
        defaults = {"quantity": 5}
        defaults.update(kwargs)
        return Product.objects.create(
            name=name,
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=price,
            is_active=active,
            **defaults,
        )

    def test_list_page_loads(self):
        self._make_product()
        response = self.client.get(reverse("products:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_list.html")
        self.assertContains(response, "Ring")

    def test_list_excludes_inactive_products(self):
        self._make_product(name="Active Ring")
        self._make_product(name="Hidden Ring", active=False)
        response = self.client.get(reverse("products:list"))
        self.assertContains(response, "Active Ring")
        self.assertNotContains(response, "Hidden Ring")

    def test_filter_by_category(self):
        self._make_product(name="Ring A")
        other = Category.objects.create(name="Bracelets")
        Product.objects.create(
            name="Bracelet",
            category=other,
            brand=self.brand,
            material=self.material,
            price=100,
            quantity=5,
        )
        response = self.client.get(reverse("products:list"), {"category": "rings"})
        self.assertContains(response, "Ring A")
        self.assertNotContains(response, "/products/bracelet/")

    def test_filter_by_price_range(self):
        self._make_product(name="Cheap Ring", price=100)
        self._make_product(name="Pricey Ring", price=500)
        response = self.client.get(reverse("products:list"), {"min_price": 200, "max_price": 600})
        self.assertContains(response, "Pricey Ring")
        self.assertNotContains(response, "Cheap Ring")

    def test_filter_by_color_variant(self):
        product = self._make_product(name="Colored Ring")
        ProductVariant.objects.create(product=product, color=self.color, size=self.size, stock=2)
        response = self.client.get(reverse("products:list"), {"color": "gold"})
        self.assertContains(response, "Colored Ring")

    def test_sort_by_price_ascending(self):
        self._make_product(name="Expensive", price=500)
        self._make_product(name="Cheap", price=100)
        response = self.client.get(reverse("products:list"), {"sort": "price_asc"})
        html = response.content.decode()
        self.assertLess(html.find("Cheap"), html.find("Expensive"))


class ProductDetailViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Rings")
        self.brand = Brand.objects.create(name="Maira Signature")
        self.material = Material.objects.create(name="Gold Plated")
        self.color = Color.objects.create(name="Gold")
        self.size = Size.objects.create(name="17")

    def test_detail_page_loads_with_variant_selector(self):
        product = Product.objects.create(
            name="Detail Ring",
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=250,
            quantity=5,
        )
        ProductVariant.objects.create(
            product=product, color=self.color, size=self.size, stock=3
        )
        response = self.client.get(product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_detail.html")
        self.assertContains(response, "Detail Ring")
        self.assertContains(response, "variant-color")
        self.assertContains(response, "Colour")

    def test_detail_tracks_recently_viewed(self):
        product = Product.objects.create(
            name="Viewed Ring",
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=100,
            quantity=5,
        )
        self.client.get(product.get_absolute_url())
        session = self.client.session
        self.assertIn(product.pk, session.get("recently_viewed_products", []))

    def test_detail_404_for_inactive_product(self):
        product = Product.objects.create(
            name="Hidden",
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=100,
            quantity=5,
            is_active=False,
        )
        response = self.client.get(product.get_absolute_url())
        self.assertEqual(response.status_code, 404)


class ProductSearchTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Necklaces")
        self.brand = Brand.objects.create(name="Xuping")
        self.material = Material.objects.create(name="Stainless Steel")

    def test_search_by_name(self):
        Product.objects.create(
            name="Gold Chain Necklace",
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=300,
            quantity=5,
        )
        response = self.client.get(reverse("products:search"), {"q": "chain"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gold Chain Necklace")

    def test_search_no_results(self):
        response = self.client.get(reverse("products:search"), {"q": "nonexistent"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No products match")

    def test_search_orders_url(self):
        response = self.client.get(reverse("products:search"), {"q": "gold"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_list.html")
