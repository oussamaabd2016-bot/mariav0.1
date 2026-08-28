from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.add, name="add"),
    path("update/", views.update, name="update"),
    path("remove/", views.remove, name="remove"),
    path("coupon/apply/", views.apply_coupon, name="apply_coupon"),
    path("coupon/remove/", views.remove_coupon, name="remove_coupon"),
]
