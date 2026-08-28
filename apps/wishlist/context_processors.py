"""Template context processor exposing the wishlist count for the navbar."""
from .models import WishlistItem


def wishlist_context(request):
    if not request.user.is_authenticated:
        return {"wishlist_count": 0}
    return {
        "wishlist_count": WishlistItem.objects.filter(
            user=request.user
        ).count()
    }
