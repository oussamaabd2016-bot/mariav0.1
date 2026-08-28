// Maira Bijouterie — cart page JS.
// Live totals: quantity changes are submitted in the background and the
// whole cart region is re-rendered with the server, so subtotal, shipping,
// coupon discount and total stay accurate without a full page reload.
// Falls back gracefully to normal form submission when JS is disabled.

document.addEventListener("DOMContentLoaded", function () {
    var cartContent = document.getElementById("cart-content");
    if (!cartContent) {
        return;
    }

    function csrfToken() {
        var el = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return el ? el.value : "";
    }

    function refreshCart(form, onSuccess) {
        var url = form.action;
        var separator = url.indexOf("?") === -1 ? "?" : "&";
        fetch(url + separator + "partial=1", {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": csrfToken()
            },
            body: new FormData(form)
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Request failed");
                }
                return response.text();
            })
            .then(function (html) {
                var wrapper = document.createElement("div");
                wrapper.innerHTML = html;
                var fresh = wrapper.querySelector("#cart-content");
                if (fresh) {
                    cartContent.innerHTML = fresh.innerHTML;
                    if (onSuccess) {
                        onSuccess();
                    }
                }
            })
            .catch(function () {
                form.submit();
            });
    }

    // Quantity inputs: submit the line form when the value changes.
    cartContent.addEventListener("change", function (event) {
        var input = event.target;
        if (!input.classList.contains("cart-qty-input")) {
            return;
        }
        var form = input.closest("form.cart-qty-form");
        if (form) {
            refreshCart(form);
        }
    });

    // The "apply coupon" and "remove coupon" forms post through the same partial refresh.
    cartContent.addEventListener("submit", function (event) {
        var form = event.target;
        if (form && (form.action.indexOf("coupon/apply") !== -1 || form.action.indexOf("coupon/remove") !== -1)) {
            event.preventDefault();
            refreshCart(form);
        }
    });
});
