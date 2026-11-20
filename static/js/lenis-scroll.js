(() => {
    const page = document.querySelector(".lexique-page, .conlang-documentation");
    if (!page) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const cdnUrl = "https://cdn.jsdelivr.net/npm/lenis@1.3.27/dist/lenis.min.js";
    let lenis;
    let loadingScript;
    let animationFrame = 0;
    let gsapTick;

    const updateAtmosphere = ({ scroll, limit }) => {
        const progress = limit > 0 ? Math.min(1, Math.max(0, scroll / limit)) : 0;
        const root = document.documentElement;
        root.style.setProperty("--reading-leaf-opacity", (0.62 + progress * 0.33).toFixed(3));
        root.style.setProperty("--reading-leaf-shift", `${-progress * 8}vh`);
        root.style.setProperty("--reading-copper-opacity", (1 - progress * 0.78).toFixed(3));
        root.style.setProperty("--reading-copper-shift", `${-progress * 12}vh`);
    };

    const clearAtmosphere = () => {
        const root = document.documentElement;
        root.classList.remove("aenor-reading-atmosphere");
        root.style.removeProperty("--reading-leaf-opacity");
        root.style.removeProperty("--reading-leaf-shift");
        root.style.removeProperty("--reading-copper-opacity");
        root.style.removeProperty("--reading-copper-shift");
    };

    const runFrame = (time) => {
        if (!lenis) return;
        lenis.raf(time);
        animationFrame = window.requestAnimationFrame(runFrame);
    };

    const stop = () => {
        if (animationFrame) {
            window.cancelAnimationFrame(animationFrame);
            animationFrame = 0;
        }
        if (gsapTick && window.gsap?.ticker) {
            window.gsap.ticker.remove(gsapTick);
            gsapTick = undefined;
        }
        if (lenis) {
            lenis.off("scroll", updateAtmosphere);
            lenis.destroy();
            lenis = undefined;
        }
        clearAtmosphere();
    };

    const initialize = () => {
        if (lenis || reducedMotion.matches || typeof window.Lenis !== "function") return;

        lenis = new window.Lenis({
            autoRaf: false,
            anchors: true,
            lerp: 0.085,
            smoothWheel: true,
            prevent: (node) => node.hasAttribute("data-lenis-prevent")
        });

        document.documentElement.classList.add("aenor-reading-atmosphere");
        updateAtmosphere({ scroll: lenis.scroll, limit: lenis.limit });
        lenis.on("scroll", updateAtmosphere);

        if (window.gsap?.ticker && window.ScrollTrigger) {
            window.gsap.registerPlugin(window.ScrollTrigger);
            lenis.on("scroll", window.ScrollTrigger.update);
            gsapTick = (time) => lenis?.raf(time * 1000);
            window.gsap.ticker.add(gsapTick);
        } else {
            animationFrame = window.requestAnimationFrame(runFrame);
        }
    };

    const loadLenis = () => {
        if (lenis || loadingScript || reducedMotion.matches) return;
        if (typeof window.Lenis === "function") {
            initialize();
            return;
        }

        loadingScript = document.createElement("script");
        loadingScript.src = cdnUrl;
        loadingScript.async = true;
        loadingScript.onload = () => {
            loadingScript = undefined;
            if (typeof window.Lenis !== "function") {
                console.warn("Lenis loaded without exposing its constructor; native scrolling remains active.");
                return;
            }
            initialize();
        };
        loadingScript.onerror = () => {
            loadingScript = undefined;
            console.warn("Lenis could not load; native scrolling remains active.");
        };
        document.head.appendChild(loadingScript);
    };

    const onMotionPreferenceChange = () => {
        if (reducedMotion.matches) stop();
        else loadLenis();
    };
    const onPageHide = () => stop();
    const onPageShow = (event) => {
        if (event.persisted) loadLenis();
    };

    reducedMotion.addEventListener("change", onMotionPreferenceChange);
    window.addEventListener("pagehide", onPageHide);
    window.addEventListener("pageshow", onPageShow);
    loadLenis();
})();
