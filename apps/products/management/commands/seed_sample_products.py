"""Seed realistic sample catalogue data.

Usage: python manage.py seed_sample_products

Creates categories, brands, materials, colours, sizes and a set of sample
jewellery products with variants and generated placeholder images.
"""
import io
import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from apps.products.models import (
    Brand,
    Category,
    Color,
    Material,
    Product,
    ProductImage,
    ProductVariant,
    Size,
)

# Catalogue building blocks.
CATEGORIES = [
    ("Bracelets", "Gold-plated and stainless steel bracelets for every day."),
    ("Rings", "Elegant rings in gold, silver and rose tones."),
    ("Necklaces", "Delicate necklaces and chains."),
    ("Earrings", "Hoop, stud and drop earrings."),
    ("Sets", "Matching jewellery sets."),
]
BRANDS = ["Maira Signature", "Xuping", "Fashion Jewelry", "Maira Luxe"]
MATERIALS = ["Gold Plated", "Stainless Steel", "Sterling Silver", "Brass"]
COLORS = [
    ("Gold", "#D4AF37"),
    ("Rose Gold", "#B76E79"),
    ("Silver", "#C0C0C0"),
    ("Black", "#111111"),
]
SIZES = ["One Size", "16", "17", "18", "19", "S", "M", "L"]

# (name, category, brand, material, base_price, discount, flags)
PRODUCTS = [
    ("Gold Plated Chain Bracelet", "Bracelets", "Maira Signature", "Gold Plated", 249, 199, {"gold_plated": True, "waterproof": True, "tarnish_resistant": True}),
    ("Stainless Steel Cuban Link Bracelet", "Bracelets", "Xuping", "Stainless Steel", 320, 0, {"stainless_steel": True, "waterproof": True}),
    ("Rose Gold Twisted Ring", "Rings", "Maira Signature", "Gold Plated", 180, 145, {"gold_plated": True, "tarnish_resistant": True}),
    ("S925 Sterling Silver Ring", "Rings", "Maira Luxe", "Sterling Silver", 260, 0, {"stainless_steel": False, "waterproof": False}),
    ("Layered Pearl Necklace", "Necklaces", "Fashion Jewelry", "Gold Plated", 390, 299, {"gold_plated": True, "featured": True}),
    ("Gold Infinity Pendant Necklace", "Necklaces", "Maira Signature", "Stainless Steel", 280, 0, {"stainless_steel": True, "waterproof": True}),
    ("Hoop Earrings 24k Gold", "Earrings", "Xuping", "Gold Plated", 150, 0, {"gold_plated": True, "waterproof": True}),
    ("Drop Pearl Earrings", "Earrings", "Maira Luxe", "Gold Plated", 170, 130, {"gold_plated": True}),
    ("Bridal Jewellery Set", "Sets", "Maira Luxe", "Gold Plated", 890, 690, {"gold_plated": True, "featured": True, "best_seller": True}),
    ("Everyday Hoop Set (3 pairs)", "Sets", "Fashion Jewelry", "Stainless Steel", 450, 350, {"stainless_steel": True, "waterproof": True, "best_seller": True}),
    ("Stainless Steel Tennis Bracelet", "Bracelets", "Xuping", "Stainless Steel", 510, 0, {"stainless_steel": True, "waterproof": True, "featured": True}),
    ("Minimal Bar Necklace", "Necklaces", "Maira Signature", "Stainless Steel", 220, 180, {"stainless_steel": True, "waterproof": True, "is_new": True}),
]


def _make_image(path, color_hex, label):
    """Generate a simple branded placeholder image using Pillow."""
    if default_storage.exists(path):
        return path
    img = Image.new("RGB", (600, 600), "#F7F7F7")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 599, 599], outline=color_hex, width=4)
    draw.ellipse([150, 150, 450, 450], outline=color_hex, width=6)
    try:
        draw.text((300, 560), label, fill=color_hex, anchor="mm")
    except TypeError:
        draw.text((300, 560), label, fill=color_hex)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    default_storage.save(path, ContentFile(buffer.getvalue()))
    return path


class Command(BaseCommand):
    help = "Seed the product catalogue with categories, brands and sample products."

    def handle(self, *args, **options):
        # Clear existing catalogue data to keep the seed idempotent.
        ProductVariant.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Brand.objects.all().delete()
        Material.objects.all().delete()
        Color.objects.all().delete()
        Size.objects.all().delete()

        categories = {
            name: Category.objects.create(name=name, description=desc)
            for name, desc in CATEGORIES
        }
        brands = {name: Brand.objects.create(name=name) for name in BRANDS}
        materials = {name: Material.objects.create(name=name) for name in MATERIALS}
        colors = {
            name: Color.objects.create(name=name, hex_code=hexc)
            for name, hexc in COLORS
        }
        sizes = {name: Size.objects.create(name=name) for name in SIZES}

        created = 0
        for idx, (name, cat, brand, mat, price, discount, flags) in enumerate(PRODUCTS):
            category = categories[cat]
            product = Product.objects.create(
                name=name,
                category=category,
                brand=brands[brand],
                material=materials[mat],
                price=price,
                discount_price=discount or None,
                quantity=10 + idx,
                short_description=f"{name} — {mat.lower()}.",
                description=(
                    f"The {name} is crafted from {mat.lower()} and finished with "
                    "care for a premium affordable-luxury look. Made for everyday "
                    "wear with a timeless design."
                ),
                featured=flags.get("featured", False),
                is_new=flags.get("is_new", False),
                best_seller=flags.get("best_seller", False),
                gold_plated=flags.get("gold_plated", False),
                stainless_steel=flags.get("stainless_steel", False),
                waterproof=flags.get("waterproof", False),
                tarnish_resistant=flags.get("tarnish_resistant", False),
                xuping=(brand == "Xuping"),
            )
            sku_base = f"MB-{idx + 1:04d}"
            product.sku = sku_base
            product.save()

            # Main placeholder image.
            color_hex = colors["Gold"].hex_code
            img_path = _make_image(
                f"products/{product.slug}.png", color_hex, product.name[:20]
            )
            product.main_image = img_path
            product.save()

            # Additional gallery image.
            gallery_path = _make_image(
                f"products/gallery/{product.slug}-2.png", "#8C6A1D", product.name[:20]
            )
            ProductImage.objects.create(
                product=product, image=gallery_path, alt_text=product.name
            )

            # Create variants for sized products.
            product_sizes = sizes["One Size"]
            if cat in ("Rings",):
                for size_name in ("16", "17", "18"):
                    ProductVariant.objects.create(
                        product=product,
                        color=colors["Gold"],
                        size=sizes[size_name],
                        stock=5,
                        price_override=None,
                    )
            elif cat in ("Bracelets", "Sets"):
                ProductVariant.objects.create(
                    product=product,
                    color=colors["Gold"],
                    size=sizes["One Size"],
                    stock=8,
                )
            else:
                ProductVariant.objects.create(
                    product=product,
                    color=colors["Gold"],
                    size=product_sizes,
                    stock=8,
                )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created} products, "
                f"{len(CATEGORIES)} categories, {len(BRANDS)} brands, "
                f"{len(MATERIALS)} materials, {len(COLORS)} colours, "
                f"{len(SIZES)} sizes."
            )
        )
