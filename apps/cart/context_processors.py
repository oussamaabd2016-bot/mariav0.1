"""Template context processor exposing the cart item count.

Used by the navbar badge. Reads existing carts only — it never creates a
Cart row just for a page view.
"""
from .models import CartItem


def cart_context(request):
    if request.user.is_authenticated:
        count = sum(
            CartItem.objects.filter(cart__user=request.user).values_list(
                "quantity", flat=True
            )
        )
    else:
        session_key = request.session.session_key
        if not session_key:
            return {"cart_item_count": 0}
        count = sum(
            CartItem.objects.filter(cart__session_key=session_key).values_list(
                "quantity", flat=True
            )
        )
    return {"cart_item_count": count}
