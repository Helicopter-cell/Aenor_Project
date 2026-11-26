(() => {
    window.AenorLenis?.destroy();

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const cdnUrl = 'https://cdn.jsdelivr.net/npm/lenis@1.3.27/dist/lenis.min.js';
    let lenis;
    let loadingScript;
    let animationFrame = 0;
    let gsapTick;
    let scrollTriggerUpdate;
    let generation = 0;
    let listenersAttached = false;

    const updateAtmosphere = ({ scroll, limit, velocity = 0 }) => {
        const progress = limit > 0 ? Math.min(1, Math.max(0, scroll / limit)) : 0;
        const root = document.documentElement;
        root.style.setProperty('--reading-leaf-opacity', (0.62 + progress * 0.33).toFixed(3));
        root.style.setProperty('--reading-leaf-shift', `${-progress * 8}vh`);
        root.style.setProperty('--reading-copper-opacity', (1 - progress * 0.78).toFixed(3));
        root.style.setProperty('--reading-copper-shift', `${-progress * 12}vh`);
        window.AenorAmbientCurves?.onLenisScroll({ scroll, limit, progress, velocity });
    };

    const clearAtmosphere = () => {
        const root = document.documentElement;
        root.classList.remove('aenor-reading-atmosphere');
        root.style.removeProperty('--reading-leaf-opacity');
        root.style.removeProperty('--reading-leaf-shift');
        root.style.removeProperty('--reading-copper-opacity');
        root.style.removeProperty('--reading-copper-shift');
    };

    const runFrame = time => {
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
            lenis.off('scroll', updateAtmosphere);
            if (scrollTriggerUpdate) lenis.off('scroll', scrollTriggerUpdate);
            lenis.destroy();
            lenis = undefined;
        }
        scrollTriggerUpdate = undefined;
        clearAtmosphere();
    };

    const initialize = () => {
        const page = document.querySelector('.lexique-page, .conlang-documentation, [data-lexicographer-game]');
        if (lenis || loadingScript || reducedMotion.matches || !page) return;
        if (typeof window.Lenis === 'function') {
            startLenis();
            return;
        }

        const currentGeneration = generation;
        loadingScript = document.createElement('script');
        loadingScript.src = cdnUrl;
        loadingScript.async = true;
        loadingScript.onload = () => {
            if (generation !== currentGeneration) return;
            loadingScript = undefined;
            if (typeof window.Lenis !== 'function') {
                console.warn('Lenis loaded without exposing its constructor; native scrolling remains active.');
                return;
            }
            startLenis();
        };
        loadingScript.onerror = () => {
            if (generation !== currentGeneration) return;
            loadingScript = undefined;
            console.warn('Lenis could not load; native scrolling remains active.');
        };
        document.head.appendChild(loadingScript);
    };

    const startLenis = () => {
        if (lenis || reducedMotion.matches) return;
        lenis = new window.Lenis({
            autoRaf: false,
            anchors: true,
            lerp: 0.085,
            smoothWheel: true,
            prevent: node => node.hasAttribute('data-lenis-prevent'),
        });

        document.documentElement.classList.add('aenor-reading-atmosphere');
        updateAtmosphere({ scroll: lenis.scroll, limit: lenis.limit });
        lenis.on('scroll', updateAtmosphere);

        if (window.gsap?.ticker && window.ScrollTrigger) {
            window.gsap.registerPlugin(window.ScrollTrigger);
            scrollTriggerUpdate = window.ScrollTrigger.update;
            lenis.on('scroll', scrollTriggerUpdate);
            gsapTick = time => lenis?.raf(time * 1000);
            window.gsap.ticker.add(gsapTick);
        } else {
            animationFrame = window.requestAnimationFrame(runFrame);
        }
    };

    const onMotionPreferenceChange = () => {
        if (reducedMotion.matches) stop();
        else initialize();
    };
    const onPageHide = () => stop();
    const onPageShow = event => {
        if (event.persisted) initialize();
    };

    const attachListeners = () => {
        if (listenersAttached) return;
        listenersAttached = true;
        reducedMotion.addEventListener('change', onMotionPreferenceChange);
        window.addEventListener('pagehide', onPageHide);
        window.addEventListener('pageshow', onPageShow);
    };

    const destroy = () => {
        generation += 1;
        if (loadingScript) {
            loadingScript.onload = null;
            loadingScript.onerror = null;
            loadingScript.remove();
            loadingScript = undefined;
        }
        stop();
        if (!listenersAttached) return;
        listenersAttached = false;
        reducedMotion.removeEventListener('change', onMotionPreferenceChange);
        window.removeEventListener('pagehide', onPageHide);
        window.removeEventListener('pageshow', onPageShow);
    };

    const controller = {
        init: initialize,
        resize: () => lenis?.resize(),
        destroy,
    };
    window.AenorLenis = controller;
    attachListeners();
    initialize();
})();
