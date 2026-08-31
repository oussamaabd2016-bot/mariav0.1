# Maira Bijouterie

An e-commerce store for e.g Maira Bijouterie, a Moroccan jewellery brand selling gold-plated, stainless steel and fashion jewellery online. Built as a full Django .

---

## What it does

- **Product catalogue** — browseable by category, filterable by material, price and availability
- **Packages** — curated bundles with combined pricing and a 3D carousel on the homepage
- **Cart & Wishlist** — session-based cart with quantity controls, coupon codes, and a saved wishlist for registered users
- **Checkout** — Cash on Delivery and Bank Transfer at launch, with WhatsApp confirmation flow
- **Customer accounts** — email-based registration, order history, profile management
- **Reviews** — star ratings and text reviews per product .
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

# 1. Install dependencies
pip install -r requirements.txt


# 2. Run migrations
python manage.py migrate

# 3. Create an admin user
python manage.py createsuperuser

# 4. Start the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000` for the storefront and `http://127.0.0.1:8000/admin` for the admin panel.

---


---

## Project layout

```
mariav0.1/
├── apps/
│   ├── accounts/       # Custom user model, login, register, profile
│   ├── cart/           # Session cart + coupon 
│   ├── dashboard/      # Customer order history + staff/admin analytic
│   ├── home/           # Homepage, about, contact, sitemap ...
│   ├── orders/         # Checkout, order creation, confirmation
│   ├── packages/       # Curated jewellery bundles (used plain picture for ex)
│   ├── payments/       # Payment stub (COD + bank transfer)
│   ├── products/       # Catalogue, categories, filters
│   ├── reviews/        # Star ratings and text reviews
│   └── wishlist/       # Saved products per user
├── config/
│   └── settings/
│       ├── base.py     
│       ├── dev.py       
│       └── prod.py     
├── static/
│   ├── css/base.css    # Main stylesheet
│   └── js/             # Cart, filters, homepage carousel, etc.
├── templates/          # Global templates including admin overrides
└── .env.example        # Environment variable reference
```

---


### On Windows:
1. Install Cloudflare CLI (one-time setup in PowerShell):
   ```powershell
   winget install Cloudflare.cloudflared
   ```
   .....or its automaticly install after this command if u dont have it .
2. Run the launcher:
   ```cmd
   run_live.bat
   ```
---

## Running in production (Custom Domain / VPS)

1. Set `DEBUG=False` and a strong `SECRET_KEY` in your `.env`
2. Set `DATABASE_URL` to your PostgreSQL connection string
3. Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to your domain
4. Run `python manage.py collectstatic`
5. Serve with Gunicorn behind Nginx, Caddy, or Cloudflare Tunnel

The `prod.py` settings file already has HTTPS enforcement, HSTS, secure cookies, MIME-sniff protection and referrer policy configured. You just need to point it at a real domain with a valid SSL certificate.

