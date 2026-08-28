from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView

from apps.cart import services as cart_services
from apps.wishlist.models import WishlistItem
from .models import Package


import json

class PackageListView(ListView):
    """List all active bundles."""

    model = Package
    template_name = "packages/package_list.html"
    context_object_name = "packages"
    paginate_by = 4

    def get_queryset(self):
        return Package.objects.filter(is_active=True).prefetch_related("products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_pkgs = Package.objects.filter(is_active=True).prefetch_related("products")
        items = []
        for pkg in all_pkgs:
            img = pkg.display_image.url if pkg.display_image else "/static/img/packages_gift_box.png"
            items.append({
                "image": img,
                "text": pkg.name,
                "slug": pkg.slug,
                "url": pkg.get_absolute_url(),
                "price": float(pkg.final_price),
                "original_price": float(pkg.original_price),
                "discount": pkg.discount_percentage,
                "count": pkg.products.count(),
                "description": pkg.description,
            })
        
        # For circular 3D panoramic depth, cycle real packages if fewer than 6
        if items:
            orig_len = len(items)
            while len(items) < 6:
                items.append(items[len(items) % orig_len])

        context["carousel_cards"] = items
        context["gallery_items_json"] = json.dumps(items)
        return context


class PackageDetailView(DetailView):
    """A single bundle with its included products."""

    model = Package
    template_name = "packages/package_detail.html"
    context_object_name = "package"

    def get_queryset(self):
        return Package.objects.filter(is_active=True).prefetch_related("products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["included_products"] = self.object.products.all()
        return context


@require_http_methods(["POST"])
def add_package_to_cart(request, slug):
    """Add all active products included in a package to the user's cart."""
    package = get_object_or_404(Package, slug=slug, is_active=True)
    cart = cart_services.get_or_create_cart(request)
    added_count = 0
    for product in package.products.filter(is_active=True):
        variant = product.variants.filter(is_active=True).first()
        item = cart_services.add_item(cart, product, variant=variant, quantity=1)
        if item:
            added_count += 1

    # Apply the package discount to the cart if no higher coupon is already present
    if package.discount_percentage > 0 and (not cart.coupon or cart.coupon.discount_percentage < package.discount_percentage):
        from apps.cart.models import Coupon
        from django.utils import timezone
        coupon_code = f"BUNDLE-{package.discount_percentage}"
        coupon, _ = Coupon.objects.get_or_create(
            code=coupon_code,
            defaults={
                "discount_percentage": package.discount_percentage,
                "is_active": True,
                "valid_from": timezone.now(),
            },
        )
        cart.coupon = coupon
        cart.save(update_fields=("coupon", "updated_at"))

    messages.success(request, f"Added all {added_count} pieces from {package.name} with {package.discount_percentage}% bundle savings!")
    return redirect("cart:index")


@require_http_methods(["POST"])
def add_package_to_wishlist(request, slug):
    """Add all active products included in a package to the user's wishlist."""
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in to save sets to your wishlist.")
        return redirect("accounts:login")
    package = get_object_or_404(Package, slug=slug, is_active=True)
    added_count = 0
    for product in package.products.filter(is_active=True):
        WishlistItem.objects.get_or_create(user=request.user, product=product)
        added_count += 1
    messages.success(request, f"Saved all {added_count} items from {package.name} to your wishlist!")
    return redirect(package.get_absolute_url())
