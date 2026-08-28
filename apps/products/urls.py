from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="list"),
    path("search/", views.product_search, name="search"),
    path("<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
]
