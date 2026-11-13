(() => {
    const gsap = window.gsap;
    if (!gsap) {
        console.warn("Aënor animations are unavailable because GSAP did not load.");
        return;
    }

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion) return;

    const home = document.querySelector(".home-page");
    if (home) {
        const intro = home.querySelector(".home-intro");
        const seal = intro?.querySelector(".home-seal");
        const eyebrow = intro?.querySelector(".home-eyebrow");
        const title = intro?.querySelector(".Index-title");
        const lede = intro?.querySelector(".home-lede");
        const featuredCards = home.querySelectorAll(".home-paths > .card-link");
        const collection = home.querySelector(".home-section-heading");
        const secondaryCards = home.querySelectorAll(".home-grid > .card-link");
        const timeline = gsap.timeline({ defaults: { ease: "power2.out" } });

        if (seal) timeline.from(seal, { autoAlpha: 0, scale: 0.84, duration: 0.48 });
        if (eyebrow) timeline.from(eyebrow, { autoAlpha: 0, y: 10, duration: 0.34 }, "-=0.2");
        if (title) timeline.from(title, { autoAlpha: 0, y: 18, duration: 0.45 }, "-=0.14");
        if (lede) timeline.from(lede, { autoAlpha: 0, y: 12, duration: 0.35 }, "-=0.18");
        if (featuredCards.length) {
            timeline.from(featuredCards, {
                autoAlpha: 0,
                y: 18,
                duration: 0.4,
                stagger: 0.09
            }, "-=0.08");
        }
        if (collection) timeline.from(collection, { autoAlpha: 0, y: 12, duration: 0.3 }, "-=0.1");
        if (secondaryCards.length) {
            timeline.from(secondaryCards, {
                autoAlpha: 0,
                y: 12,
                duration: 0.32,
                stagger: 0.05
            }, "-=0.12");
        }
    }

    const ctas = document.querySelectorAll(".btn-primary, .btn-IA-trad, .btn");
    ctas.forEach((cta) => {
        const brighten = () => gsap.to(cta, {
            filter: "brightness(1.07) drop-shadow(0 0 7px rgb(179 137 78 / 0.26))",
            duration: 0.2,
            overwrite: true
        });
        const reset = () => gsap.to(cta, {
            filter: "none",
            duration: 0.22,
            overwrite: true
        });

        cta.addEventListener("pointerenter", brighten);
        cta.addEventListener("pointerleave", reset);
        cta.addEventListener("focus", brighten);
        cta.addEventListener("blur", reset);
    });

    document.querySelectorAll("details.cours-accordion > summary").forEach((summary) => {
        summary.addEventListener("click", (event) => {
            const accordion = summary.parentElement;
            const content = summary.nextElementSibling;
            if (!accordion || !content?.classList.contains("cours-content")) return;

            event.preventDefault();
            if (accordion.dataset.motionAnimating === "true") return;

            const shouldOpen = !accordion.open;
            accordion.dataset.motionAnimating = "true";
            window.requestAnimationFrame(() => {
                accordion.open = true;
                if (!shouldOpen) {
                    gsap.to(content, {
                        autoAlpha: 0,
                        y: -6,
                        duration: 0.18,
                        onComplete: () => {
                            accordion.open = false;
                            delete accordion.dataset.motionAnimating;
                            gsap.set(content, { clearProps: "opacity,visibility,transform" });
                        }
                    });
                    return;
                }

                gsap.fromTo(
                    content,
                    { autoAlpha: 0, y: -6 },
                    {
                        autoAlpha: 1,
                        y: 0,
                        duration: 0.28,
                        ease: "power2.out",
                        clearProps: "opacity,visibility,transform",
                        onComplete: () => delete accordion.dataset.motionAnimating
                    }
                );
            });
        });
    });
})();
