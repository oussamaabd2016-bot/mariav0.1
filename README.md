# Maira Bijouterie

An e-commerce store for Maira Bijouterie, a Moroccan jewellery brand selling gold-plated, stainless steel and fashion jewellery online. Built as a full Django storefront to replace WhatsApp and Instagram DM-based sales with a proper catalogue, cart and checkout flow.

---

## What it does

- **Product catalogue** — browseable by category, filterable by material, price and availability
- **Packages** — curated bundles with combined pricing and a 3D carousel on the homepage
- **Cart & Wishlist** — session-based cart with quantity controls, coupon codes, and a saved wishlist for registered users
- **Checkout** — Cash on Delivery and Bank Transfer at launch, with WhatsApp confirmation flow
- **Customer accounts** — email-based registration, order history, profile management
- **Reviews** — star ratings and text reviews per product, with admin approval
- **Admin panel** — custom sidebar layout with quick actions and full model management
- **Staff dashboard** — order overview, best sellers, low-stock alerts, revenue stats

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.1 |
| Database | SQLite (dev) → PostgreSQL (production) |
| Frontend | Bootstrap 5 + vanilla JavaScript |
| Forms | django-crispy-forms + crispy-bootstrap5 |
| Static files | WhiteNoise |
| Images | Pillow |
| Auth | Custom email-based User model |
| Deployment | Gunicorn + any Unix host |

---

## Getting started

**Requirements:** Python 3.12+

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd mariav0.1

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt


# 5. Run migrations
python manage.py migrate

# 6. Create an admin user
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000` for the storefront and `http://127.0.0.1:8000/admin` for the admin panel.

---

## Environment variables

See [`.env.example`](.env.example) for the full list. The important ones:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret key — use a long random string in production |
| `DEBUG` | Yes | `True` for local dev, `False` in production |
| `ALLOWED_HOSTS` | Yes | Comma-separated list of your domain(s) |
| `DATABASE_URL` | Yes | `sqlite:///db.sqlite3` locally, Postgres URL in production |
| `CSRF_TRUSTED_ORIGINS` | Prod | Your `https://` origin(s) |
| `WHATSAPP_NUMBER` | No | Phone number for WhatsApp order confirmation links |

---

## Project layout

```
mariav0.1/
├── apps/
│   ├── accounts/       # Custom user model, login, register, profile
│   ├── cart/           # Session cart + coupon codes
│   ├── dashboard/      # Customer order history + staff analytics
│   ├── home/           # Homepage, about, contact, sitemap
│   ├── orders/         # Checkout, order creation, confirmation
│   ├── packages/       # Curated jewellery bundles
│   ├── payments/       # Payment stub (COD + bank transfer)
│   ├── products/       # Catalogue, categories, filters
│   ├── reviews/        # Star ratings and text reviews
│   └── wishlist/       # Saved products per user
├── config/
│   └── settings/
│       ├── base.py     # Shared settings
│       ├── dev.py      # Local development overrides
│       └── prod.py     # Production overrides
├── static/
│   ├── css/base.css    # Main stylesheet
│   └── js/             # Cart, filters, homepage carousel, etc.
├── templates/          # Global templates including admin overrides
└── .env.example        # Environment variable reference
```

---

## Running in production

1. Set `DEBUG=False` and a strong `SECRET_KEY` in your `.env`
2. Set `DATABASE_URL` to your PostgreSQL connection string
3. Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to your domain
4. Run `python manage.py collectstatic`
5. Serve with Gunicorn behind Nginx or any reverse proxy

The `prod.py` settings file already has HTTPS enforcement, HSTS, secure cookies, MIME-sniff protection and referrer policy configured. You just need to point it at a real domain with a valid SSL certificate.

---

