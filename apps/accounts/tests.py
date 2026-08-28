"""Tests for the accounts app: models, registration, login, profile."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Profile

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(email="test@example.com", password="StrongPass123!")
        self.assertEqual(user.email, "test@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email=None, password="StrongPass123!")

    def test_create_superuser(self):
        user = User.objects.create_superuser(email="admin@example.com", password="StrongPass123!")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_string_representation(self):
        user = User.objects.create_user(email="test@example.com", password="StrongPass123!")
        self.assertEqual(str(user), "test@example.com")

    def test_profile_created_automatically_with_related_name(self):
        user = User.objects.create_user(email="test@example.com", password="StrongPass123!")
        profile = Profile.objects.create(user=user)
        self.assertEqual(profile.user, user)
        self.assertEqual(user.profile, profile)


class RegisterViewTests(TestCase):
    def test_register_page_loads(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "new@example.com",
                "first_name": "Salma",
                "last_name": "El Amrani",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())
        user = User.objects.get(email="new@example.com")
        self.assertTrue(Profile.objects.filter(user=user).exists())
        # User should be logged in after registration.
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(email="dup@example.com", password="StrongPass123!")
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "dup@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "email", "A user with this email already exists.")


class LoginViewTests(TestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(email="login@example.com", password=self.password)

    def test_login_page_loads(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "login@example.com", "password": self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_redirects_customer_to_hub(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "login@example.com", "password": self.password},
        )
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_login_redirects_staff_to_staff_dashboard(self):
        staff = User.objects.create_user(
            email="stafflogin@example.com", password=self.password, is_staff=True
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": staff.email, "password": self.password},
        )
        self.assertRedirects(response, reverse("dashboard:admin"))

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)


class ProfileViewTests(TestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(email="profile@example.com", password=self.password)
        Profile.objects.create(user=self.user)

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_profile_updates_user_and_contact_details(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "first_name": "Yasmine",
                "last_name": "Bennani",
                "phone": "0600000000",
                "address": "12 Rue Hassan II",
                "city": "Casablanca",
                "postal_code": "20000",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Yasmine")
        profile = self.user.profile
        self.assertEqual(profile.phone, "0600000000")
        self.assertEqual(profile.city, "Casablanca")


class GoogleOAuthTests(TestCase):
    def test_google_login_redirects_without_client_id(self):
        with self.settings(GOOGLE_CLIENT_ID=""):
            response = self.client.get(reverse("accounts:google_login"))
            self.assertRedirects(response, reverse("accounts:login"))

    def test_google_login_redirects_to_google_with_client_id(self):
        with self.settings(GOOGLE_CLIENT_ID="mock-client-id.apps.googleusercontent.com"):
            response = self.client.get(reverse("accounts:google_login"))
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith("https://accounts.google.com/o/oauth2/v2/auth"))
            self.assertIn("mock-client-id", response.url)
            self.assertIn("google_oauth_state", self.client.session)

    def test_google_callback_rejects_mismatched_state(self):
        session = self.client.session
        session["google_oauth_state"] = "valid_state_token"
        session.save()

        response = self.client.get(reverse("accounts:google_callback"), {"code": "mock_code", "state": "wrong_state"})
        self.assertRedirects(response, reverse("accounts:login"))

