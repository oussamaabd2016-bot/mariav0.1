"""Forms for the reviews app."""
from django import forms

from apps.products.models import Product

from .models import Review

# Django's integer widget default min/max cover 1..5 via the model validators.
RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]


class ReviewForm(forms.ModelForm):
    """Rate and optionally comment on a purchased product."""

    class Meta:
        model = Review
        fields = ("rating", "comment", "image")
        widgets = {
            "rating": forms.Select(choices=RATING_CHOICES),
            "comment": forms.Textarea(attrs={"rows": 4}),
        }

    product_id = forms.IntegerField(widget=forms.HiddenInput())

    def clean_product_id(self):
        product_id = self.cleaned_data["product_id"]
        product = Product.objects.filter(pk=product_id, is_active=True).first()
        if product is None:
            raise forms.ValidationError("Unknown product.")
        return product
