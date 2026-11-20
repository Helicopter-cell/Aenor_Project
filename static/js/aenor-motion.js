(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion) return;

    const atroposInstances = [];
    const initializeAtropos = () => {
        const targets = document.querySelectorAll("[data-atropos]");
        if (!targets.length || !window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
        if (typeof window.Atropos !== "function") {
            console.warn("Atropos could not load; interactive cards remain static.");
            return;
        }

        targets.forEach((target) => {
            if (target.__atropos__) return;

            const originalNodes = Array.from(target.childNodes);
            const scale = document.createElement("div");
            const rotate = document.createElement("div");
            const inner = document.createElement("div");
            scale.className = "atropos-scale";
            rotate.className = "atropos-rotate";
            inner.className = "atropos-inner";
            originalNodes.forEach((node) => inner.appendChild(node));
            rotate.appendChild(inner);
            scale.appendChild(rotate);
            target.appendChild(scale);
            target.classList.add("atropos");

            target.querySelectorAll(".card-icon").forEach((icon) => {
                icon.dataset.atroposOffset = "5";
            });
            target.querySelectorAll(".card-content").forEach((content) => {
                content.dataset.atroposOffset = "2";
            });

            const instance = window.Atropos({
                el: target,
                activeOffset: 12,
                duration: 450,
                rotateXMax: 4,
                rotateYMax: 4,
                rotateTouch: "scroll-y",
                shadow: true,
                shadowOffset: 16,
                shadowScale: 1.04,
                highlight: true
            });
            atroposInstances.push({ target, instance, originalNodes });
        });

        if (atroposInstances.length) {
            document.documentElement.classList.add("atropos-enabled");
        }
    };

    const destroyAtropos = () => {
        atroposInstances.forEach(({ target, instance, originalNodes }) => {
            instance.destroy();
            const scale = target.querySelector(":scope > .atropos-scale");
            if (scale) {
                originalNodes.forEach((node) => target.insertBefore(node, scale));
                scale.remove();
            }
            target.classList.remove("atropos");
        });
        atroposInstances.length = 0;
        document.documentElement.classList.remove("atropos-enabled");
    };

    initializeAtropos();
    window.addEventListener("pagehide", destroyAtropos);
    window.addEventListener("pageshow", (event) => {
        if (event.persisted && !reducedMotion) initializeAtropos();
    });

    const gsap = window.gsap;
    if (!gsap) {
        console.warn("Aënor animations are unavailable because GSAP did not load.");
        return;
    }

    const splitResults = new Map();
    const splitTargets = document.querySelectorAll("[data-split]");
    if (typeof window.SplitType === "function") {
        splitTargets.forEach((element) => {
            const split = new window.SplitType(element, {
                types: element.dataset.split || "words"
            });
            element.classList.add("split-reveal");
            splitResults.set(element, split);
        });
    } else if (splitTargets.length) {
        console.warn("SplitType could not load; titles will use the standard reveal.");
    }

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

        const revealWords = (element, vars, position) => {
            const words = splitResults.get(element)?.words;
            timeline.from(words?.length ? words : element, {
                ...vars,
                ...(words?.length ? { stagger: 0.045, transformOrigin: "50% 100%" } : {})
            }, position);
        };

        if (seal) timeline.from(seal, { autoAlpha: 0, scale: 0.84, duration: 0.48 });
        if (eyebrow) revealWords(eyebrow, { autoAlpha: 0, yPercent: 55, duration: 0.34 }, "-=0.2");
        if (title) revealWords(title, { autoAlpha: 0, yPercent: 75, rotateX: -16, duration: 0.48 }, "-=0.14");
        if (lede) revealWords(lede, { autoAlpha: 0, yPercent: 40, duration: 0.35 }, "-=0.18");
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
    } else {
        splitTargets.forEach((element) => {
            const words = splitResults.get(element)?.words;
            gsap.from(words?.length ? words : element, {
                autoAlpha: 0,
                yPercent: 60,
                rotateX: -12,
                transformOrigin: "50% 100%",
                duration: 0.42,
                stagger: words?.length ? 0.035 : 0,
                ease: "power2.out",
                delay: 0.08
            });
        });
    }

    const aenorGlyphs = document.querySelectorAll(".lexique-page .lexique-aenor");
    if (aenorGlyphs.length && typeof window.SplitType === "function" && "IntersectionObserver" in window) {
        const glyphObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                observer.unobserve(entry.target);

                const split = new window.SplitType(entry.target, { types: "chars" });
                entry.target.classList.add("split-reveal");
                gsap.from(split.chars, {
                    autoAlpha: 0,
                    y: 5,
                    duration: 0.28,
                    stagger: 0.018,
                    ease: "power2.out",
                    onComplete: () => {
                        split.revert();
                        entry.target.classList.remove("split-reveal");
                    }
                });
            });
        }, { rootMargin: "0px 0px -12% 0px" });

        aenorGlyphs.forEach((glyph) => glyphObserver.observe(glyph));
        window.addEventListener("pagehide", () => glyphObserver.disconnect(), { once: true });
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
