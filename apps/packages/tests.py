"""Tests for the packages app: model pricing and list/detail views."""
from django.test import TestCase
from django.urls import reverse

from apps.products.models import Brand, Category, Material, Product

from .models import Package


class PackageModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Bracelets")
        self.brand = Brand.objects.create(name="Maira Signature")
        self.material = Material.objects.create(name="Gold Plated")

    def _make_product(self, name="Bracelet", price=200):
        return Product.objects.create(
            name=name,
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=price,
            quantity=10,
        )

    def test_original_price_sums_products(self):
        package = Package.objects.create(name="Bundle", discount_percentage=0)
        package.products.set(
            [self._make_product("A", 100), self._make_product("B", 200)]
        )
        self.assertEqual(package.original_price, 300)

    def test_final_price_applies_discount(self):
        package = Package.objects.create(name="Bundle", discount_percentage=20)
        package.products.set(
            [self._make_product("A", 100), self._make_product("B", 200)]
        )
        self.assertEqual(package.final_price, 240)
        self.assertEqual(package.savings, 60)

    def test_zero_products_price_is_zero(self):
        package = Package.objects.create(name="Empty", discount_percentage=10)
        self.assertEqual(package.original_price, 0)
        self.assertEqual(package.final_price, 0)

    def test_slug_auto_generated(self):
        package = Package.objects.create(name="Bridal Glow Set")
        self.assertEqual(package.slug, "bridal-glow-set")

    def test_uses_product_current_price_for_discounted_items(self):
        product = self._make_product("A", 200)
        product.discount_price = 150
        product.save()
        package = Package.objects.create(name="Bundle", discount_percentage=0)
        package.products.set([product])
        self.assertEqual(package.original_price, 150)


class PackageViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Bracelets")
        self.brand = Brand.objects.create(name="Maira Signature")
        self.material = Material.objects.create(name="Gold Plated")

    def _make_product(self, name="Bracelet", price=200):
        return Product.objects.create(
            name=name,
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=price,
            quantity=10,
        )

    def test_list_page_loads(self):
        response = self.client.get(reverse("packages:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "packages/package_list.html")

    def test_list_shows_only_active_packages(self):
        package = Package.objects.create(name="Visible Bundle")
        package.products.set([self._make_product()])
        Package.objects.create(name="Hidden Bundle", is_active=False)
        response = self.client.get(reverse("packages:list"))
        self.assertContains(response, "Visible Bundle")
        self.assertNotContains(response, "Hidden Bundle")

    def test_detail_page_loads_with_included_products(self):
        package = Package.objects.create(name="Detail Bundle", discount_percentage=10)
        package.products.set([self._make_product("Included Bracelet", 150)])
        response = self.client.get(package.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "packages/package_detail.html")
        self.assertContains(response, "Detail Bundle")
        self.assertContains(response, "Included Bracelet")
        self.assertContains(response, "What's included")

    def test_detail_404_for_inactive_package(self):
        package = Package.objects.create(name="Hidden", is_active=False)
        response = self.client.get(package.get_absolute_url())
        self.assertEqual(response.status_code, 404)
