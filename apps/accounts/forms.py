"""Forms for registration, login and profile editing."""
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)

from .models import Profile, User


class UserRegistrationForm(UserCreationForm):
    """Registration form: email + password + optional personal details."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"autofocus": True}),
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    """Login form using the custom email-based user model."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True}),
    )


class UserPasswordChangeForm(PasswordChangeForm):
    """Password change form (default behaviour, custom label styling)."""


class UserPasswordResetForm(PasswordResetForm):
    """Password reset request form."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"autofocus": True}),
    )


class UserSetPasswordForm(SetPasswordForm):
    """Password reset confirmation form."""


class ProfileForm(forms.ModelForm):
    """Combined editable account + contact details."""

    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    class Meta:
        model = Profile
        fields = ("phone", "address", "city", "postal_code")
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["first_name"].initial = self.user.first_name
            self.fields["last_name"].initial = self.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
        if self.user:
            self.user.first_name = self.cleaned_data.get("first_name", "")
            self.user.last_name = self.cleaned_data.get("last_name", "")
            self.user.save()
        return profile
