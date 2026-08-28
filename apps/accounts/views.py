"""Views for registration, authentication and profile management."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from .forms import (
    ProfileForm,
    UserLoginForm,
    UserPasswordChangeForm,
    UserPasswordResetForm,
    UserRegistrationForm,
    UserSetPasswordForm,
)
from .models import Profile


class UserLoginView(LoginView):
    """Login using the email-based custom user model."""

    template_name = "accounts/login.html"
    authentication_form = UserLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        # Staff land on their business dashboard; everyone else on the hub.
        if self.request.user.is_staff:
            return reverse("dashboard:admin")
        return reverse("dashboard:home")


class UserLogoutView(LogoutView):
    """Logout redirects home."""

    next_page = reverse_lazy("home:index")


class UserPasswordChangeView(PasswordChangeView):
    """Password change for authenticated users."""

    template_name = "accounts/password_change.html"
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("accounts:password_change_done")


class UserPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"


class UserPasswordResetView(PasswordResetView):
    """Request a password reset link."""

    template_name = "accounts/password_reset.html"
    form_class = UserPasswordResetForm
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = UserSetPasswordForm
    success_url = reverse_lazy("accounts:password_reset_complete")


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


def register(request):
    """Create a new account, log the user in and redirect home."""
    if request.user.is_authenticated:
        return redirect("home:index")

    form = UserRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        # Auto-create a profile for the new customer.
        Profile.objects.create(user=user)
        login(request, user)
        messages.success(request, "Welcome to Maira Bijouterie!")
        return redirect("home:index")

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    """View and edit the current user's account and contact details."""
    profile = get_object_or_404(Profile, user=request.user)
    form = ProfileForm(request.POST or None, instance=profile, user=request.user)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile")

    return render(request, "accounts/profile.html", {"form": form})


def google_login(request):
    """Initiates the Google OAuth2 authentication flow."""
    import secrets
    import urllib.parse
    from django.conf import settings

    if request.user.is_authenticated:
        return redirect("home:index")

    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    if not client_id:
        messages.error(
            request,
            "Google Sign-In is not configured yet. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file.",
        )
        return redirect("accounts:login")

    # Generate random state token for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session["google_oauth_state"] = state

    # Store optional next URL for redirect after login
    next_url = request.GET.get("next")
    if next_url:
        request.session["google_oauth_next"] = next_url

    redirect_uri = request.build_absolute_uri(reverse("accounts:google_callback"))

    params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": redirect_uri,
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


def google_callback(request):
    """Handles the OAuth2 redirect callback from Google."""
    import json
    import urllib.parse
    import urllib.request
    from django.conf import settings
    from .models import User, Profile

    if request.user.is_authenticated:
        return redirect("home:index")

    error = request.GET.get("error")
    if error:
        messages.warning(request, "Google sign-in was cancelled.")
        return redirect("accounts:login")

    code = request.GET.get("code")
    state = request.GET.get("state")
    saved_state = request.session.pop("google_oauth_state", None)

    if not code or not state or state != saved_state:
        messages.error(request, "Invalid authentication session. Please try signing in again.")
        return redirect("accounts:login")

    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "")
    redirect_uri = request.build_absolute_uri(reverse("accounts:google_callback"))

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    try:
        req = urllib.request.Request(
            token_url,
            data=urllib.parse.urlencode(token_data).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_json = json.loads(resp.read().decode("utf-8"))
        access_token = token_json.get("access_token")

        if not access_token:
            messages.error(request, "Could not authenticate with Google. Please check your credentials.")
            return redirect("accounts:login")

        # Fetch user info with access token
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        req_user = urllib.request.Request(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req_user, timeout=10) as resp:
            user_data = json.loads(resp.read().decode("utf-8"))

        email = user_data.get("email")
        is_verified = user_data.get("verified_email", False) or user_data.get("email_verified", False)
        if not email or not is_verified:
            messages.error(request, "Google did not provide a verified email address.")
            return redirect("accounts:login")

        email = email.lower().strip()
        first_name = user_data.get("given_name") or user_data.get("name", "")
        last_name = user_data.get("family_name", "")

        # Look up or create user by normalized email
        user = User.objects.filter(email__iexact=email).first()
        created = False
        if not user:
            user = User.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            created = True

        # Ensure user profile exists
        Profile.objects.get_or_create(user=user)

        # Update name if previously blank
        if not user.first_name and first_name:
            user.first_name = first_name
            user.last_name = last_name
            user.save(update_fields=["first_name", "last_name"])

        # Specify backend explicitly and log the user in
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)

        if created:
            messages.success(request, f"Welcome to Maira Bijouterie, {first_name or user.email}!")
        else:
            messages.success(request, f"Welcome back, {user.first_name or user.email}!")

        next_url = request.session.pop("google_oauth_next", None)
        if next_url:
            return redirect(next_url)
        if user.is_staff:
            return redirect("dashboard:admin")
        return redirect("dashboard:home")

    except Exception as exc:
        messages.error(request, "An unexpected error occurred during Google sign in. Please try again.")
        return redirect("accounts:login")

