from django.urls import path

from . import views

app_name = "wishlist"

urlpatterns = [
    path("", views.index, name="index"),
    path("add/<int:product_id>/", views.add, name="add"),
    path("remove/<int:item_id>/", views.remove, name="remove"),
    path("move-to-cart/<int:item_id>/", views.move_to_cart, name="move_to_cart"),
]
