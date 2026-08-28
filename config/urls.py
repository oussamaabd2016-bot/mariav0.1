"""Root URL configuration for Maira Bijouterie."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

# Branded error pages (see apps/core/views.py)
handler404 = "apps.core.views.handler404"
handler500 = "apps.core.views.handler500"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.home.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("products/", include("apps.products.urls")),
    path("packages/", include("apps.packages.urls")),
    path("cart/", include("apps.cart.urls")),
    path("orders/", include("apps.orders.urls")),
    path("payments/", include("apps.payments.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("wishlist/", include("apps.wishlist.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/img/favicon.svg", permanent=True),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
