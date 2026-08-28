// Maira Bijouterie — Product Pages JS
// Handles interactive filters sidebar animation, sort dropdown, and variant selection.

document.addEventListener("DOMContentLoaded", function () {
    // ----------------------------------------------------
    // 1. Interactive Filters Sidebar & Vertical Tab Toggle
    // ----------------------------------------------------
    const shopCatalogLayout = document.getElementById("shopCatalogLayout");
    const toggleFiltersBtn = document.getElementById("toggleFiltersBtn");
    const filtersVerticalTab = document.getElementById("filtersVerticalTab");
    const closeFiltersBtn = document.getElementById("closeFiltersBtn");

    if (shopCatalogLayout) {
        // Read saved preference, default to open on desktop
        const isDesktop = window.innerWidth >= 992;
        const savedState = sessionStorage.getItem("maira_filters_state");

        function setFiltersState(isOpen, animate) {
            if (isOpen) {
                shopCatalogLayout.classList.remove("is-filters-collapsed");
                shopCatalogLayout.classList.add("is-filters-open");
                if (toggleFiltersBtn) {
                    toggleFiltersBtn.setAttribute("aria-expanded", "true");
                    const label = toggleFiltersBtn.querySelector(".toggle-label");
                    if (label) label.textContent = "Hide Filters";
                }
                sessionStorage.setItem("maira_filters_state", "open");
            } else {
                shopCatalogLayout.classList.remove("is-filters-open");
                shopCatalogLayout.classList.add("is-filters-collapsed");
                if (toggleFiltersBtn) {
                    toggleFiltersBtn.setAttribute("aria-expanded", "false");
                    const label = toggleFiltersBtn.querySelector(".toggle-label");
                    if (label) label.textContent = "Show Filters";
                }
                sessionStorage.setItem("maira_filters_state", "collapsed");
            }
        }

        // Initialize state: always start hidden until clicked
        setFiltersState(false, false);

        // Toggle button in toolbar
        if (toggleFiltersBtn) {
            toggleFiltersBtn.addEventListener("click", function (e) {
                e.stopPropagation();
                const isCurrentlyOpen = shopCatalogLayout.classList.contains("is-filters-open");
                setFiltersState(!isCurrentlyOpen, true);
            });
        }

        // Vertical tab clicked -> Open filters smoothly
        if (filtersVerticalTab) {
            filtersVerticalTab.addEventListener("click", function (e) {
                e.stopPropagation();
                setFiltersState(true, true);
            });
        }

        // Close button inside filters card -> Collapse to vertical tab
        if (closeFiltersBtn) {
            closeFiltersBtn.addEventListener("click", function (e) {
                e.stopPropagation();
                setFiltersState(false, true);
            });
        }
    }

    // ----------------------------------------------------
    // 2. Sort Dropdown Auto-submit
    // ----------------------------------------------------
    const sortSelect = document.getElementById("sort");
    if (sortSelect) {
        sortSelect.addEventListener("change", function () {
            this.form.submit();
        });
    }

    // ----------------------------------------------------
    // 3. Filter Form Auto-submit on select change
    // ----------------------------------------------------
    const filterForm = document.getElementById("filter-form");
    if (filterForm) {
        const selects = filterForm.querySelectorAll("select[name]");
        selects.forEach(function (select) {
            select.addEventListener("change", function () {
                filterForm.submit();
            });
        });
    }

    // ----------------------------------------------------
    // 4. Validate variant on product detail page before cart add
    // ----------------------------------------------------
    const addToCartForm = document.getElementById("add-to-cart-form");
    if (addToCartForm && addToCartForm.querySelector(".variant-group")) {
        addToCartForm.addEventListener("submit", function (event) {
            const color = addToCartForm.querySelector('select[name="color"]');
            const size = addToCartForm.querySelector('select[name="size"]');
            if (color && !color.value) {
                event.preventDefault();
                color.focus();
                alert("Please choose a colour.");
                return;
            }
            if (size && !size.value) {
                event.preventDefault();
                size.focus();
                alert("Please choose a size.");
                return;
            }
        });
    }
});
