"""Views for the products catalogue: list, detail and search."""
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .models import Brand, Category, Color, Material, Product, Size

# Keys stored in the session for recently-viewed products.
RECENTLY_VIEWED_KEY = "recently_viewed_products"
RECENTLY_VIEWED_LIMIT = 8
PAGE_SIZE = 12
CATEGORY_TILES_LIMIT = 4


def _category_tiles(limit=CATEGORY_TILES_LIMIT):
    """Category image tiles for the shop page in 1-2 efficient queries."""
    categories = list(Category.objects.all()[:limit])
    if not categories:
        return []
    missing_cat_ids = [c.id for c in categories if not c.image]
    first_images = {}
    if missing_cat_ids:
        for p in (
            Product.objects.filter(is_active=True, category_id__in=missing_cat_ids)
            .exclude(main_image="")
            .order_by("category_id", "-created_at")
        ):
            if p.category_id not in first_images:
                first_images[p.category_id] = p.main_image

    return [
        {"category": c, "image": c.image if c.image else first_images.get(c.id)}
        for c in categories
    ]


class ProductListView(ListView):
    """Product list with a wide range of filter options and keyword search.

    Filters are applied via GET query parameters so URLs are shareable:
    q, category, brand, material, color, size, min_price, max_price,
    waterproof, stainless_steel, in_stock and sort.
    """

    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related(
            "category", "brand", "material"
        )

        params = self.request.GET

        # Free-text search query.
        query = params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(short_description__icontains=query)
                | Q(description__icontains=query)
                | Q(sku__icontains=query)
                | Q(category__name__icontains=query)
                | Q(material__name__icontains=query)
                | Q(brand__name__icontains=query)
            )

        # Category filter (by slug).
        category_slug = params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Brand filter (by slug).
        brand_slug = params.get("brand")
        if brand_slug:
            queryset = queryset.filter(brand__slug=brand_slug)

        # Material filter (by slug).
        material_slug = params.get("material")
        if material_slug:
            queryset = queryset.filter(material__slug=material_slug)

        # Color filter (by slug) — matches variants of that colour.
        color_slug = params.get("color")
        if color_slug:
            queryset = queryset.filter(variants__color__slug=color_slug).distinct()

        # Size filter (by slug) — matches variants of that size.
        size_slug = params.get("size")
        if size_slug:
            queryset = queryset.filter(variants__size__slug=size_slug).distinct()

        # Price range filter.
        min_price = params.get("min_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        max_price = params.get("max_price")
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Attribute filters.
        if params.get("waterproof"):
            queryset = queryset.filter(waterproof=True)
        if params.get("stainless_steel"):
            queryset = queryset.filter(stainless_steel=True)
        if params.get("gold_plated"):
            queryset = queryset.filter(gold_plated=True)

        # Availability filter (in stock).
        if params.get("in_stock"):
            queryset = queryset.filter(quantity__gt=0)

        # Sorting.
        sort = params.get("sort")
        if sort == "price_asc":
            queryset = queryset.order_by("price")
        elif sort == "price_desc":
            queryset = queryset.order_by("-price")
        elif sort == "newest":
            queryset = queryset.order_by("-created_at")
        elif sort == "name":
            queryset = queryset.order_by("name")
        else:
            queryset = queryset.order_by("-featured", "-created_at")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET
        context["categories"] = Category.objects.all()
        context["brands"] = Brand.objects.all()
        context["materials"] = Material.objects.all()
        context["colors"] = Color.objects.all()
        context["sizes"] = Size.objects.all()
        context["category_tiles"] = _category_tiles()

        # Persist active filters for the sidebar highlighting.
        category_slug = params.get("category", "")
        context["query"] = params.get("q", "").strip()
        context["selected_category"] = (
            Category.objects.filter(slug=category_slug).first() if category_slug else None
        )
        context["active_filters"] = {
            "category": category_slug,
            "brand": params.get("brand", ""),
            "material": params.get("material", ""),
            "color": params.get("color", ""),
            "size": params.get("size", ""),
            "min_price": params.get("min_price", ""),
            "max_price": params.get("max_price", ""),
            "sort": params.get("sort", ""),
            "waterproof": params.get("waterproof", ""),
            "stainless_steel": params.get("stainless_steel", ""),
            "gold_plated": params.get("gold_plated", ""),
            "in_stock": params.get("in_stock", ""),
        }

        # Clean querystring (without the page param) for pagination links.
        qs = params.copy()
        qs.pop("page", None)
        context["qs"] = qs.urlencode()
        return context


class ProductDetailView(DetailView):
    """Product detail page with gallery, variant selector and related items."""

    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related(
            "category", "brand", "material"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Gallery: gallery images first, main image as a fallback.
        images = list(product.images.all())
        if product.main_image:
            images.insert(0, product.main_image)
        context["gallery"] = images

        # Variant grouping for the selector.
        context["variants"] = product.variants.select_related(
            "color", "size"
        ).filter(is_active=True)
        context["colors"] = []
        context["sizes"] = []
        for variant in context["variants"]:
            if variant.color and variant.color not in context["colors"]:
                context["colors"].append(variant.color)
            if variant.size and variant.size not in context["sizes"]:
                context["sizes"].append(variant.size)

        context["related_products"] = product.related_products()

        # Approved reviews + rating summary + whether the visitor may review.
        context["reviews"] = product.reviews.filter(is_approved=True).select_related(
            "user"
        )
        context["rating_average"] = product.rating_average
        context["rating_count"] = product.rating_count
        context["rating_distribution"] = product.rating_distribution()
        context["rating_full_stars"] = (
            int(round(product.rating_average)) if product.rating_average else 0
        )

        from apps.reviews.forms import ReviewForm
        from apps.reviews.services import user_can_review

        context["can_review"] = user_can_review(self.request.user, product)
        context["review_form"] = ReviewForm(initial={"product_id": product.pk})

        # Track recently viewed products in the session.
        self._record_recently_viewed(product)
        context["recently_viewed"] = self._get_recently_viewed()

        return context

    def _record_recently_viewed(self, product):
        recent = self.request.session.get(RECENTLY_VIEWED_KEY, [])
        if product.pk in recent:
            recent.remove(product.pk)
        recent.insert(0, product.pk)
        self.request.session[RECENTLY_VIEWED_KEY] = recent[:RECENTLY_VIEWED_LIMIT]
        self.request.session.modified = True

    def _get_recently_viewed(self):
        ids = self.request.session.get(RECENTLY_VIEWED_KEY, [])
        if not ids:
            return []
        products = list(
            Product.objects.filter(pk__in=ids, is_active=True).select_related(
                "category", "brand", "material"
            )
        )
        # Preserve session order
        prod_map = {p.pk: p for p in products}
        return [prod_map[pk] for pk in ids if pk in prod_map]


def product_search(request):
    """Search endpoint delegating directly to ProductListView."""
    return ProductListView.as_view()(request)
