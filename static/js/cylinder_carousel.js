/**
 * 3D Curved Cylindrical Carousel for Maira Bijouterie Packages.
 * Wide landscape rectangular cards with wide circular geometry and slow luxury rotation.
 */

document.addEventListener("DOMContentLoaded", function () {
    init3DCylinderCarousel();
});

function init3DCylinderCarousel() {
    const stage = document.getElementById("cylinder3DStage");
    const ring = document.getElementById("cylinder3DRing");
    if (!stage || !ring) return;

    const cards = Array.from(ring.querySelectorAll(".cylinder-card"));
    if (cards.length === 0) return;

    const prevBtn = document.getElementById("cylinderPrevBtn");
    const nextBtn = document.getElementById("cylinderNextBtn");
    const dotsContainer = document.getElementById("cylinderDots");

    const totalCards = cards.length;
    const angleStep = 360 / totalCards;
    
    let cardWidth = 440;
    let radius = 580;

    let currentAngle = 0;
    let targetAngle = 0;
    let isDragging = false;
    let startX = 0;
    let startAngle = 0;
    let velocity = 0;
    let lastX = 0;
    let lastTime = 0;
    let animationFrameId = null;
    let autoRotateTimer = null;
    let isHovered = false;

    function getActiveIndex() {
        let normalized = ((-targetAngle % 360) + 360) % 360;
        let index = Math.round(normalized / angleStep) % totalCards;
        return index;
    }

    // Build dot indicators
    if (dotsContainer) {
        dotsContainer.innerHTML = "";
        cards.forEach((_, i) => {
            const dot = document.createElement("button");
            dot.type = "button";
            dot.className = `cylinder-dot ${i === 0 ? "active" : ""}`;
            dot.setAttribute("aria-label", `Go to package ${i + 1}`);
            dot.addEventListener("click", () => {
                goToIndex(i);
                resetAutoPlay();
            });
            dotsContainer.appendChild(dot);
        });
    }

    function updateDots() {
        if (!dotsContainer) return;
        const activeIdx = getActiveIndex();
        const dots = dotsContainer.querySelectorAll(".cylinder-dot");
        dots.forEach((dot, i) => {
            dot.classList.toggle("active", i === activeIdx);
        });
    }

    function layoutCards() {
        const stageWidth = stage.clientWidth;
        if (stageWidth < 576) {
            cardWidth = 280;
            radius = 290;
        } else if (stageWidth < 992) {
            cardWidth = 330;
            radius = 400;
        } else {
            cardWidth = 380;
            radius = 500;
        }

        cards.forEach((card, i) => {
            const cardAngle = i * angleStep;
            card.style.transform = `rotateY(${cardAngle}deg) translateZ(${radius}px)`;
        });
    }

    layoutCards();
    window.addEventListener("resize", () => {
        layoutCards();
        render();
    });

    function render() {
        // Slow, buttery smooth lerp easing (0.055 for calm luxury movement)
        currentAngle += (targetAngle - currentAngle) * 0.055;
        ring.style.transform = `rotateY(${currentAngle}deg)`;

        // Calculate visibility, scale, and interactivity for each card
        cards.forEach((card, i) => {
            const baseAngle = i * angleStep;
            let relativeAngle = (baseAngle + currentAngle) % 360;
            if (relativeAngle > 180) relativeAngle -= 360;
            if (relativeAngle < -180) relativeAngle += 360;

            const absAngle = Math.abs(relativeAngle);
            const isFacing = absAngle < 32;

            // Opacity & depth styling
            if (isFacing) {
                card.classList.add("is-active-card");
                card.style.opacity = "1";
                card.style.zIndex = "10";
                card.style.filter = "none";
                card.style.pointerEvents = "auto";
            } else {
                card.classList.remove("is-active-card");
                const opacity = Math.max(0.32, 1 - (absAngle / 150));
                card.style.opacity = opacity.toFixed(2);
                card.style.zIndex = Math.round(10 - absAngle / 20).toString();
                card.style.filter = absAngle > 80 ? "blur(1.5px) brightness(0.88)" : "blur(0.4px)";
                card.style.pointerEvents = "none";
            }
        });

        updateDots();

        if (Math.abs(targetAngle - currentAngle) > 0.04 || isDragging) {
            animationFrameId = requestAnimationFrame(render);
        } else {
            currentAngle = targetAngle;
            ring.style.transform = `rotateY(${currentAngle}deg)`;
            animationFrameId = null;
        }
    }

    function startAnimation() {
        if (!animationFrameId) {
            animationFrameId = requestAnimationFrame(render);
        }
    }

    function snapToNearest() {
        const snapped = Math.round(targetAngle / angleStep) * angleStep;
        targetAngle = snapped;
        startAnimation();
    }

    function goToIndex(index) {
        const currentActive = getActiveIndex();
        let diff = index - currentActive;
        if (diff > totalCards / 2) diff -= totalCards;
        if (diff < -totalCards / 2) diff += totalCards;

        targetAngle -= diff * angleStep;
        startAnimation();
    }

    // Drag / Touch Handling
    function onPointerDown(e) {
        isDragging = true;
        startX = e.touches ? e.touches[0].clientX : e.clientX;
        startAngle = targetAngle;
        lastX = startX;
        lastTime = performance.now();
        velocity = 0;
        stage.classList.add("is-dragging");
        clearInterval(autoRotateTimer);
        startAnimation();
    }

    function onPointerMove(e) {
        if (!isDragging) return;
        const x = e.touches ? e.touches[0].clientX : e.clientX;
        const now = performance.now();
        const dt = now - lastTime || 16;
        const dx = x - lastX;

        velocity = (dx / dt) * 10;
        lastX = x;
        lastTime = now;

        const totalDx = x - startX;
        // Gentler 0.18 degrees rotation per pixel dragged for slow, steady control
        targetAngle = startAngle + totalDx * 0.18;
        startAnimation();
    }

    function onPointerUp() {
        if (!isDragging) return;
        isDragging = false;
        stage.classList.remove("is-dragging");

        // Apply gentle momentum velocity
        if (Math.abs(velocity) > 0.4) {
            targetAngle += velocity * 2.5;
        }

        snapToNearest();
        resetAutoPlay();
    }

    stage.addEventListener("mousedown", onPointerDown);
    window.addEventListener("mousemove", onPointerMove);
    window.addEventListener("mouseup", onPointerUp);

    stage.addEventListener("touchstart", onPointerDown, { passive: true });
    window.addEventListener("touchmove", onPointerMove, { passive: true });
    window.addEventListener("touchend", onPointerUp);

    // Mouse wheel support (gentle step)
    stage.addEventListener("wheel", (e) => {
        e.preventDefault();
        const delta = e.deltaY || e.deltaX;
        targetAngle += (delta > 0 ? -1 : 1) * (angleStep * 0.5);
        snapToNearest();
        startAnimation();
        resetAutoPlay();
    }, { passive: false });

    // Buttons
    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            targetAngle += angleStep;
            snapToNearest();
            startAnimation();
            resetAutoPlay();
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            targetAngle -= angleStep;
            snapToNearest();
            startAnimation();
            resetAutoPlay();
        });
    }

    // Slow luxury auto-play timer (8.5s interval)
    function startAutoPlay() {
        clearInterval(autoRotateTimer);
        autoRotateTimer = setInterval(() => {
            if (!isDragging && !isHovered) {
                targetAngle -= angleStep;
                snapToNearest();
                startAnimation();
            }
        }, 8500);
    }

    function resetAutoPlay() {
        clearInterval(autoRotateTimer);
        startAutoPlay();
    }

    stage.addEventListener("mouseenter", () => { isHovered = true; });
    stage.addEventListener("mouseleave", () => { isHovered = false; });

    // Initial render
    render();
    startAutoPlay();
}
