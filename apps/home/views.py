"""Views for the home app: homepage, static pages, newsletter and sitemap.

The homepage pulls catalogue highlights (collections, flash sale, new
arrivals, best sellers, trending) so the storefront always reflects the
real database. Testimonials, brand story, Instagram grid and benefits are
curated static content in the template (Instagram grid uses product images, not a live API).
"""
from django.contrib import messages
from django.db.models import Avg, F, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from xml.sax.saxutils import escape as xml_escape

from apps.packages.models import Package
from apps.products.models import Category, Product

from .forms import NewsletterForm
from .models import NewsletterSubscriber


def index(request):
    """Homepage: hero, collections, flash sale, arrivals, best sellers,
    trending, brand story, benefits, Instagram grid and testimonials."""
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category", "brand", "material")
        .prefetch_related("reviews")
        .annotate(
            avg_rating=Avg(
                "reviews__rating",
                filter=Q(reviews__is_approved=True),
            )
        )
    )

    collections = []
    for category in Category.objects.all()[:4]:
        category_products = list(products.filter(category=category)[:1])
        image = category_products[0].main_image if category_products else None
        collections.append({"category": category, "image": image})

    top_rated_products = (
        products.order_by(
            F("avg_rating").desc(nulls_last=True),
            "-best_seller",
            "-created_at",
        )[:4]
    )

    packages = Package.objects.filter(is_active=True).prefetch_related("products")[:4]

    context = {
        "collections": collections,
        "packages": packages,
        "top_rated_products": top_rated_products,
        "flash_sale_products": top_rated_products,
        "best_sellers": products.filter(best_seller=True)[:8],
        "instagram_images": _instagram_images(products),
        "newsletter_form": NewsletterForm(),
    }
    return render(request, "home/index.html", context)


def _instagram_images(products, limit=6):
    """Curated static Instagram-style grid from the catalogue imagery."""
    images = []
    for product in products:
        if product.main_image:
            images.append(product)
        if len(images) >= limit:
            break
    return images


@require_POST
def newsletter_subscribe(request):
    """Subscribe an email from the footer form. Handles duplicates gently."""
    form = NewsletterForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data["email"]
        _, created = NewsletterSubscriber.objects.get_or_create(
            email__iexact=email,
            defaults={"email": email},
        )
        if created:
            messages.success(
                request, "Welcome! You're subscribed to our newsletter."
            )
        else:
            messages.info(request, "You're already on the list.")
    else:
        for _field, errors in form.errors.items():
            for error in errors:
                messages.error(request, str(error))

    next_url = request.POST.get("next") or "home:index"
    return redirect(next_url)


def about(request):
    """About page — brand story and values."""
    return render(request, "home/about.html")


def contact(request):
    """Contact page — show the team's contact channels."""
    return render(request, "home/contact.html")


def privacy(request):
    """Privacy policy page."""
    return render(request, "home/privacy.html")


def terms(request):
    """Terms & conditions page."""
    return render(request, "home/terms.html")


def sitemap_xml(request):
    """A lightweight XML sitemap without the sites framework.

    Lists the static pages plus every active product and package so search
    engines can crawl the catalogue.
    """
    static_pages = [
        ("", "1.0", "daily"),
        ("products/", "0.9", "daily"),
        ("packages/", "0.9", "weekly"),
        ("about/", "0.5", "monthly"),
        ("contact/", "0.5", "monthly"),
    ]

    urls = []
    for path, priority, freq in static_pages:
        urls.append((f"/{path}", priority, freq))

    for product in Product.objects.filter(is_active=True):
        urls.append((product.get_absolute_url(), "0.8", "weekly"))
    for package in Package.objects.filter(is_active=True):
        urls.append((package.get_absolute_url(), "0.8", "weekly"))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, priority, freq in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>https://maira.ma{xml_escape(loc)}</loc>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append("  </url>")
    lines.append("</urlset>")

    return HttpResponse("\n".join(lines), content_type="application/xml")
