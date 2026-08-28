"""Tests for the reviews app: model, purchase verification and views."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.orders.models import Order, OrderItem, OrderStatus, PaymentMethod
from apps.products.models import Brand, Category, Material, Product

from .models import Review
from .services import user_can_review, user_purchased_product


class ReviewTestMixin:
    """Shared setup: a product, two users and an order helper."""

    def setUp(self):
        self.buyer = User.objects.create_user(
            email="buyer@example.com", password="Pass123!"
        )
        self.other = User.objects.create_user(
            email="other@example.com", password="Pass123!"
        )
        self.category = Category.objects.create(name="Necklaces")
        self.brand = Brand.objects.create(name="Maira Signature")
        self.material = Material.objects.create(name="Gold Plated")
        self.product = Product.objects.create(
            name="Pendant",
            category=self.category,
            brand=self.brand,
            material=self.material,
            price=120,
            quantity=5,
        )
        self.client.login(email="buyer@example.com", password="Pass123!")

    def _place_order(self, user, product, status=OrderStatus.PENDING):
        order = Order.objects.create(
            user=user,
            full_name="Test Buyer",
            phone="0612345678",
            address="1 Test St",
            city="Casablanca",
            payment_method=PaymentMethod.CASH_ON_DELIVERY,
            subtotal=product.price,
            shipping=0,
            total=product.price,
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            sku=product.sku,
            unit_price=product.price,
            quantity=1,
        )
        order.status = status
        order.save(update_fields=("status",))
        return order


class ReviewModelTests(ReviewTestMixin, TestCase):
    def test_str(self):
        review = Review.objects.create(
            product=self.product, user=self.buyer, rating=5, comment="Great"
        )
        self.assertIn("5", str(review))
        self.assertIn(self.product.name, str(review))

    def test_unique_review_per_user_per_product(self):
        Review.objects.create(
            product=self.product, user=self.buyer, rating=4, comment="Nice"
        )
        duplicate = Review(
            product=self.product, user=self.buyer, rating=2, comment="Again"
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_rating_validators(self):
        review = Review(product=self.product, user=self.buyer, rating=6)
        with self.assertRaises(ValidationError):
            review.full_clean()

    def test_rating_helpers(self):
        Review.objects.create(product=self.product, user=self.buyer, rating=5)
        self.assertEqual(self.product.rating_count, 1)
        self.assertEqual(self.product.rating_average, 5)


class PurchaseVerificationTests(ReviewTestMixin, TestCase):
    def test_purchase_required(self):
        self.assertFalse(user_purchased_product(self.buyer, self.product))
        self._place_order(self.buyer, self.product)
        self.assertTrue(user_purchased_product(self.buyer, self.product))

    def test_cancelled_order_does_not_qualify(self):
        self._place_order(
            self.buyer, self.product, status=OrderStatus.CANCELLED
        )
        self.assertFalse(user_purchased_product(self.buyer, self.product))

    def test_anonymous_cannot_review(self):
        self.assertFalse(user_can_review(None, self.product))

    def test_non_buyer_cannot_review(self):
        self._place_order(self.buyer, self.product)
        self.assertFalse(user_can_review(self.other, self.product))


class ReviewViewTests(ReviewTestMixin, TestCase):
    def _review_url(self):
        return reverse("reviews:add")

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        response = self.client.post(
            self._review_url(),
            {"product_id": self.product.id, "rating": 5, "comment": "Nice"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_non_purchaser_blocked(self):
        response = self.client.post(
            self._review_url(),
            {"product_id": self.product.id, "rating": 5, "comment": "Nice"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.product.slug, response.url)
        self.assertEqual(Review.objects.count(), 0)

    def test_purchaser_creates_review(self):
        self._place_order(self.buyer, self.product)
        response = self.client.post(
            self._review_url(),
            {"product_id": self.product.id, "rating": 5, "comment": "Great"},
        )
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(user=self.buyer, product=self.product)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Great")

    def test_duplicate_submission_updates(self):
        self._place_order(self.buyer, self.product)
        Review.objects.create(
            product=self.product, user=self.buyer, rating=3, comment="Old"
        )
        self.client.post(
            self._review_url(),
            {"product_id": self.product.id, "rating": 5, "comment": "New"},
        )
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.get(user=self.buyer, product=self.product)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "New")

    def test_invalid_rating_rejected(self):
        self._place_order(self.buyer, self.product)
        response = self.client.post(
            self._review_url(),
            {"product_id": self.product.id, "rating": 9, "comment": "Bad"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.count(), 0)


class ProductDetailReviewTests(ReviewTestMixin, TestCase):
    def _detail_url(self):
        return reverse("products:detail", args=[self.product.slug])

    def test_detail_shows_reviews_and_rating(self):
        Review.objects.create(
            product=self.product, user=self.buyer, rating=5, comment="Lovely"
        )
        response = self.client.get(self._detail_url())
        self.assertContains(response, "Customer reviews")
        self.assertContains(response, "Lovely")
        self.assertContains(response, "5.0")

    def test_unapproved_review_hidden(self):
        Review.objects.create(
            product=self.product,
            user=self.buyer,
            rating=5,
            comment="Hidden",
            is_approved=False,
        )
        response = self.client.get(self._detail_url())
        self.assertNotContains(response, "Hidden")
        self.assertEqual(response.context["rating_count"], 0)
