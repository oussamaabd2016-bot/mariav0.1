"""Tests for the core app: abstract models, template tags, error handlers."""
from django.test import RequestFactory, TestCase

from apps.core.templatetags.core_tags import active_nav, multiply, status_badge_class


class CoreModelTests(TestCase):
    """TimeStampedModel is abstract and provides timestamps."""

    def test_time_stamped_model_is_abstract(self):
        from django.db.models.base import ModelBase

        from apps.core.models import TimeStampedModel

        self.assertIsInstance(TimeStampedModel, ModelBase)
        self.assertTrue(TimeStampedModel._meta.abstract)

    def test_time_stamped_model_fields_exist(self):
        from apps.core.models import TimeStampedModel

        fields = TimeStampedModel._meta.fields
        field_names = {f.name for f in fields}
        self.assertIn("created_at", field_names)
        self.assertIn("updated_at", field_names)


class TemplateTagTests(TestCase):
    def test_multiply(self):
        self.assertEqual(multiply(10, 3), 30)
        self.assertEqual(multiply("bad", 3), 0)

    def test_status_badge_class_mapping(self):
        self.assertEqual(status_badge_class("pending"), "bg-warning text-dark")
        self.assertEqual(status_badge_class("delivered"), "bg-success")
        self.assertEqual(status_badge_class("unknown"), "bg-secondary")

    def test_active_nav_returns_active_for_current_page(self):
        from django.template import Context
        from django.urls import resolve

        request = RequestFactory().get("/")
        request.resolver_match = resolve("/")
        context = Context({"request": request})
        self.assertEqual(active_nav(context, "index"), "active")

    def test_active_nav_empty_without_match(self):
        from django.template import Context
        from django.urls import resolve

        request = RequestFactory().get("/")
        request.resolver_match = resolve("/")
        context = Context({"request": request})
        self.assertEqual(active_nav(context, "nonexistent"), "")


class ErrorHandlerTests(TestCase):
    def test_handler404_renders_error_template(self):
        response = self.client.get("/missing/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "errors/404.html")
        self.assertContains(response, "Shop jewelry", status_code=404)

    def test_handler500_returns_500_with_error_template(self):
        from apps.core.views import handler500

        response = handler500(self.client.get("/").wsgi_request)
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Something went wrong", status_code=500)
