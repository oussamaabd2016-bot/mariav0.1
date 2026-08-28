from django.urls import path

from . import views

app_name = "packages"

urlpatterns = [
    path("", views.PackageListView.as_view(), name="list"),
    path("", views.PackageListView.as_view(), name="index"),
    path("<slug:slug>/", views.PackageDetailView.as_view(), name="detail"),
    path("<slug:slug>/add-to-cart/", views.add_package_to_cart, name="add_to_cart"),
    path("<slug:slug>/add-to-wishlist/", views.add_package_to_wishlist, name="add_to_wishlist"),
]
