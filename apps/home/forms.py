"""Form for the newsletter signup."""
from django import forms

from .models import NewsletterSubscriber


class NewsletterForm(forms.ModelForm):
    """Capture an email address; validates and normalises it."""

    class Meta:
        model = NewsletterSubscriber
        fields = ("email",)
        widgets = {
            "email": forms.EmailInput(
                attrs={"placeholder": "Your email address", "aria-label": "Email"}
            )
        }
