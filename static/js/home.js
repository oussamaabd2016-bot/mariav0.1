// Maira Bijouterie — homepage interactions.
// 3D Interactive Tilt Card Animation

document.addEventListener("DOMContentLoaded", function () {
    initInteractive3DTilt();
    initPackagesCarousel();
});

// 3D Interactive Card Tilt Animation (Perspective rotation on mousemove & smooth reset on mouseleave)
function initInteractive3DTilt() {
    var cards = document.querySelectorAll(".hover-reveal-card, .interactive-tilt-card");

    cards.forEach(function (card) {
        card.addEventListener("mousemove", function (e) {
            var rect = card.getBoundingClientRect();
            var x = e.clientX - rect.left;
            var y = e.clientY - rect.top;

            // Invert tilt direction if card has .tilt-invert
            var isInvert = card.classList.contains("tilt-invert");
            var multiplier = isInvert ? -1 : 1;

            // Compute -8deg to +8deg dynamic tilt relative to cursor center
            var rotateX = ((y - rect.height / 2) / (rect.height / 2)) * -8 * multiplier;
            var rotateY = ((x - rect.width / 2) / (rect.width / 2)) * 8 * multiplier;

            card.style.transform = "perspective(1000px) rotateX(" + rotateX.toFixed(2) + "deg) rotateY(" + rotateY.toFixed(2) + "deg) scale3d(1.04, 1.04, 1.04)";
            card.style.transition = "transform 0.08s ease-out";
        });

        card.addEventListener("mouseleave", function () {
            card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
            card.style.transition = "transform 0.4s ease-in-out";
        });
    });
}

// 3D Packages Carousel — rotational flip with dynamic left-panel text
function initPackagesCarousel() {
    var stage = document.getElementById("packages-stage");
    if (!stage) return;

    var cards   = Array.from(stage.querySelectorAll(".pkg-card"));
    var prevBtn  = document.getElementById("pkg-prev");
    var nextBtn  = document.getElementById("pkg-next");

    if (!cards.length) return;

    // ── Per-slide data extracted dynamically from DOM cards ──
    var pkgData = cards.map(function (card) {
        var featuresRaw = card.dataset.features || "";
        var features = featuresRaw ? featuresRaw.split("|") : [];
        return {
            name: card.dataset.name || "Curated Set",
            desc: card.dataset.desc || "Curated luxury package with matching jewellery.",
            features: features.length ? features.map(function (f) {
                return f.indexOf("·") !== -1 ? f : f + " · signature piece";
            }) : ["Curated jewellery combination", "Exclusive matching set", "Luxury gift box included"],
            price: card.dataset.price || "",
            original: card.dataset.original || ""
        };
    });

    var current = 0;
    var animating = false;
    var timer = null;

    // Apply 3D coverflow deck positions to cards
    function applyDeckPositions(activeIdx) {
        cards.forEach(function (card, i) {
            card.classList.remove("pkg-pos-active", "pkg-pos-left", "pkg-pos-right", "pkg-pos-hidden");

            if (i === activeIdx) {
                card.classList.add("pkg-pos-active");
            } else if (cards.length === 2 ? (i === 1 && activeIdx === 0) : (i === (activeIdx + 1) % cards.length)) {
                card.classList.add("pkg-pos-right");
            } else if (cards.length === 2 ? (i === 0 && activeIdx === 1) : (i === (activeIdx - 1 + cards.length) % cards.length)) {
                card.classList.add("pkg-pos-left");
            } else {
                card.classList.add("pkg-pos-hidden");
            }
        });
    }

    // Populate left text for given index
    function updateText(index, instant) {
        var data = pkgData[index] || pkgData[0];
        var nameEl     = document.getElementById("pkg-name");
        var descEl     = document.getElementById("pkg-desc");
        var featuresEl = document.getElementById("pkg-features");
        var priceLabel = document.getElementById("pkg-price-label");
        var priceOrig  = document.getElementById("pkg-price-original");
        var infoBlock  = document.getElementById("pkg-info");

        if (!nameEl) return;

        if (instant) {
            nameEl.textContent = data.name;
            descEl.textContent = data.desc;
            featuresEl.innerHTML = data.features.map(function (f) {
                return '<li><span class="bullet">✦</span><span>' + f + '</span></li>';
            }).join("");
            priceLabel.textContent = data.price;
            priceOrig.textContent  = data.original;
            return;
        }

        // Fade text in place smoothly
        infoBlock.style.transition = "opacity 0.24s ease";
        infoBlock.style.opacity    = "0";

        setTimeout(function () {
            nameEl.textContent = data.name;
            descEl.textContent = data.desc;
            featuresEl.innerHTML = data.features.map(function (f) {
                return '<li><span class="bullet">✦</span><span>' + f + '</span></li>';
            }).join("");
            priceLabel.textContent = data.price;
            priceOrig.textContent  = data.original;

            infoBlock.style.opacity = "1";
        }, 240);
    }

    // Initialize deck & text
    applyDeckPositions(0);
    updateText(0, true);

    // Click on background card brings it forward
    cards.forEach(function (card, i) {
        card.addEventListener("click", function (e) {
            if (i !== current) {
                e.preventDefault();
                goTo(i);
                resetTimer();
            }
        });
    });

    function goTo(next) {
        if (animating) return;
        if (next < 0) next = cards.length - 1;
        if (next >= cards.length) next = 0;
        if (next === current) return;

        animating = true;
        current = next;

        applyDeckPositions(current);
        updateText(current, false);

        setTimeout(function () {
            animating = false;
        }, 650);
    }

    if (prevBtn) {
        prevBtn.addEventListener("click", function () {
            goTo(current - 1);
            resetTimer();
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener("click", function () {
            goTo(current + 1);
            resetTimer();
        });
    }

    function startTimer() {
        timer = setInterval(function () { goTo(current + 1); }, 7000);
    }
    function resetTimer() {
        clearInterval(timer);
        startTimer();
    }

    stage.addEventListener("mouseenter", function () { clearInterval(timer); });
    stage.addEventListener("mouseleave", startTimer);

    startTimer();
}
