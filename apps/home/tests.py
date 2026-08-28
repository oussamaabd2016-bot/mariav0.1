"""Tests for the home app: homepage sections, newsletter, static pages, sitemap."""
from django.test import TestCase
from django.urls import reverse

from apps.products.models import Brand, Category, Material, Product
from apps.reviews.models import Review
from apps.accounts.models import User

from .models import NewsletterSubscriber


class HomeTestMixin:
    def setUp(self):
        self.category = Category.objects.create(name="Necklaces")
        self.brand = Brand.objects.create(name="Maira Signature")
        self.material = Material.objects.create(name="Gold Plated")
        self.product = Product.objects.create(
            name="Pendant",
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=200,
            discount_price=150,
            quantity=5,
            is_new=True,
            best_seller=True,
            featured=True,
        )


class HomepageTests(HomeTestMixin, TestCase):
    def test_index_renders(self):
        response = self.client.get(reverse("home:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Luxury That Lives With You")
        self.assertContains(response, "Born in Casablanca")

    def test_index_shows_sections(self):
        response = self.client.get(reverse("home:index"))
        self.assertContains(response, "Curated Sets")
        self.assertContains(response, "Customers Favorites")
        self.assertContains(response, "Bridal Glow Set")
        self.assertContains(response, "Waterproof &amp; tarnish-resistant finishes")

    def test_index_links_to_product(self):
        response = self.client.get(reverse("home:index"))
        self.assertContains(response, self.product.get_absolute_url())

    def test_index_renders_empty_catalogue(self):
        Product.objects.all().delete()
        response = self.client.get(reverse("home:index"))
        self.assertEqual(response.status_code, 200)


class NewsletterTests(HomeTestMixin, TestCase):
    def _url(self):
        return reverse("home:newsletter_subscribe")

    def test_valid_subscribe_saves(self):
        response = self.client.post(
            self._url(), {"email": "Nadia@Example.com", "next": "/"}
        )
        self.assertRedirects(response, "/")
        self.assertTrue(
            NewsletterSubscriber.objects.filter(email="Nadia@Example.com").exists()
        )

    def test_duplicate_subscribe_is_gentle(self):
        NewsletterSubscriber.objects.create(email="a@example.com")
        response = self.client.post(
            self._url(), {"email": "a@example.com", "next": "/"}
        )
        self.assertRedirects(response, "/")
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)

    def test_invalid_email_rejected(self):
        response = self.client.post(self._url(), {"email": "not-an-email"})
        self.assertRedirects(response, "/")
        self.assertEqual(NewsletterSubscriber.objects.count(), 0)


class StaticPageTests(TestCase):
    def test_static_pages_render(self):
        for name in ("about", "contact", "privacy", "terms"):
            with self.subTest(page=name):
                response = self.client.get(reverse(f"home:{name}"))
                self.assertEqual(response.status_code, 200)


class SitemapTests(HomeTestMixin, TestCase):
    def test_sitemap_xml(self):
        response = self.client.get(reverse("home:sitemap"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertContains(response, "<urlset")
        self.assertContains(response, "/products/")
        self.assertContains(response, self.product.get_absolute_url())
        self.assertContains(response, "/about/")
