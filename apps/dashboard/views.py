"""Dashboard views: customer hub + order history and the staff dashboard."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from apps.cart.context_processors import cart_context
from apps.orders.models import Order, OrderStatus

from .services import staff_metrics


@login_required
def home(request):
    """Customer dashboard hub: summary cards and recent orders."""
    orders = request.user.orders.order_by("-created_at")
    context = {
        "orders": orders[:5],
        "orders_count": orders.count(),
        "pending_count": orders.filter(status=OrderStatus.PENDING).count(),
        "wishlist_count": request.user.wishlist_items.count(),
        **cart_context(request),
    }
    return render(request, "dashboard/dashboard_home.html", context)


@login_required
def orders(request):
    """Customer order history, filterable by status."""
    status = request.GET.get("status", "")
    queryset = request.user.orders.order_by("-created_at")
    if status in OrderStatus.values:
        queryset = queryset.filter(status=status)
    context = {
        "orders": queryset,
        "statuses": OrderStatus.choices,
        "current_status": status,
    }
    return render(request, "dashboard/orders_list.html", context)


@login_required
def order_detail(request, pk):
    """Full detail for one of the customer's own orders."""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "dashboard/order_detail.html", {"order": order})


def staff_required(view):
    """Login-gate, then forbid (403) authenticated users who are not staff."""

    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


@staff_required
def admin_dashboard(request):
    """Staff-only business metrics overview."""
    return render(request, "dashboard/admin_dashboard.html", staff_metrics())
