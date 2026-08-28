// Maira Bijouterie — global JS helpers.
// Toast notifications, image skeleton loading, alert polish.

document.addEventListener("DOMContentLoaded", function () {
    initToasts();
    initSkeletons();
});

// Show Bootstrap toasts rendered server-side from Django messages.
function initToasts() {
    document.querySelectorAll(".message-toast").forEach(function (toastEl) {
        const toast = new bootstrap.Toast(toastEl, { delay: 4500 });
        toast.show();
    });
}

// Shimmer skeletons on images: add .skeleton to the wrapping link while the
// image loads, remove it once the image is ready.
function initSkeletons() {
    var selectors = [
        ".product-card-img-wrap img",
        ".package-card-img-wrap img",
        ".collection-card img",
        ".ig-tile img",
    ];
    document.querySelectorAll(selectors.join(",")).forEach(function (img) {
        var wrap = img.closest("a") || img.parentElement;
        if (img.complete && img.naturalWidth > 0) {
            return; // already loaded
        }
        wrap.classList.add("skeleton");
        img.addEventListener("load", function () {
            wrap.classList.remove("skeleton");
        });
        img.addEventListener("error", function () {
            wrap.classList.remove("skeleton");
        });
    });
}
