"""Models for the home app.

Newsletter signups are captured straight to the database — no ESP
integration at launch (see spec Section 6). The homepage, static pages
(About / Contact / Privacy / Terms) and sitemap are template + view
concerns, so this app only needs this one model.
"""
from django.db import models

from apps.core.models import TimeStampedModel


class NewsletterSubscriber(TimeStampedModel):
    """An email captured from the footer newsletter form."""

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to stop sending to this address.",
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.email
