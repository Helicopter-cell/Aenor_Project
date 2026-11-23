(() => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const atroposInstances = [];
    const splitInstances = new Set();
    const animations = new Set();
    const cleanups = [];
    let glyphObserver;
    let initialized = false;
    let gsap;

    function trackAnimation(animation) {
        if (animation) animations.add(animation);
        return animation;
    }

    function revertSplit(split) {
        if (!splitInstances.delete(split)) return;
        split.revert();
    }

    function initializeAccordions() {
        document.querySelectorAll('details.cours-accordion').forEach(details => {
            const summary = details.querySelector(':scope > summary');
            const chevron = summary?.querySelector('.cours-chevron');
            if (!summary) return;

            const syncState = () => {
                details.setAttribute('aria-expanded', String(details.open));
                if (chevron) chevron.textContent = details.open ? '▼' : '▶';
            };
            details.addEventListener('toggle', syncState);
            syncState();
            cleanups.push(() => details.removeEventListener('toggle', syncState));
        });
    }

    function initializeAtropos() {
        const targets = document.querySelectorAll('[data-atropos]');
        if (!targets.length || !window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
        if (typeof window.Atropos !== 'function') {
            console.warn('Atropos could not load; interactive cards remain static.');
            return;
        }

        targets.forEach(target => {
            if (target.__atropos__) return;

            const originalNodes = Array.from(target.childNodes);
            const scale = document.createElement('div');
            const rotate = document.createElement('div');
            const inner = document.createElement('div');
            scale.className = 'atropos-scale';
            rotate.className = 'atropos-rotate';
            inner.className = 'atropos-inner';
            originalNodes.forEach(node => inner.appendChild(node));
            rotate.appendChild(inner);
            scale.appendChild(rotate);
            target.appendChild(scale);
            target.classList.add('atropos');

            target.querySelectorAll('.card-icon').forEach(icon => {
                icon.dataset.atroposOffset = '5';
            });
            target.querySelectorAll('.card-content').forEach(content => {
                content.dataset.atroposOffset = '2';
            });

            const instance = window.Atropos({
                el: target,
                activeOffset: 12,
                duration: 450,
                rotateXMax: 4,
                rotateYMax: 4,
                rotateTouch: 'scroll-y',
                shadow: true,
                shadowOffset: 16,
                shadowScale: 1.04,
                highlight: true,
            });
            atroposInstances.push({ target, instance, originalNodes });
        });

        if (atroposInstances.length) document.documentElement.classList.add('atropos-enabled');
    }

    function initialize() {
        if (initialized) return;
        initialized = true;
        gsap = window.gsap;
        initializeAccordions();
        if (reducedMotion.matches) return;

        initializeAtropos();
        if (!gsap) {
            console.warn('Aënor animations are unavailable because GSAP did not load.');
            return;
        }

        const splitResults = new Map();
        const splitTargets = document.querySelectorAll('[data-split]');
        if (typeof window.SplitType === 'function') {
            splitTargets.forEach(element => {
                const split = new window.SplitType(element, {
                    types: element.dataset.split || 'words',
                });
                element.classList.add('split-reveal');
                splitInstances.add(split);
                splitResults.set(element, split);
            });
        } else if (splitTargets.length) {
            console.warn('SplitType could not load; titles will use the standard reveal.');
        }

        const home = document.querySelector('.home-page');
        if (home) {
            const intro = home.querySelector('.home-intro');
            const seal = intro?.querySelector('.home-seal');
            const eyebrow = intro?.querySelector('.home-eyebrow');
            const title = intro?.querySelector('.Index-title');
            const lede = intro?.querySelector('.home-lede');
            const featuredCards = home.querySelectorAll('.home-paths > .card-link');
            const collection = home.querySelector('.home-section-heading');
            const secondaryCards = home.querySelectorAll('.home-grid > .card-link');
            const timeline = gsap.timeline({ defaults: { ease: 'power2.out' } });

            const revealWords = (element, vars, position) => {
                const words = splitResults.get(element)?.words;
                timeline.from(words?.length ? words : element, {
                    ...vars,
                    ...(words?.length ? { stagger: 0.045, transformOrigin: '50% 100%' } : {}),
                }, position);
            };

            if (seal) timeline.from(seal, { autoAlpha: 0, scale: 0.84, duration: 0.48 });
            if (eyebrow) revealWords(eyebrow, { autoAlpha: 0, yPercent: 55, duration: 0.34 }, '-=0.2');
            if (title) revealWords(title, { autoAlpha: 0, yPercent: 75, rotateX: -16, duration: 0.48 }, '-=0.14');
            if (lede) revealWords(lede, { autoAlpha: 0, yPercent: 40, duration: 0.35 }, '-=0.18');
            if (featuredCards.length) {
                timeline.from(featuredCards, {
                    autoAlpha: 0,
                    y: 18,
                    duration: 0.4,
                    stagger: 0.09,
                }, '-=0.08');
            }
            if (collection) timeline.from(collection, { autoAlpha: 0, y: 12, duration: 0.3 }, '-=0.1');
            if (secondaryCards.length) {
                timeline.from(secondaryCards, {
                    autoAlpha: 0,
                    y: 12,
                    duration: 0.32,
                    stagger: 0.05,
                }, '-=0.12');
            }
            trackAnimation(timeline);
        } else {
            splitTargets.forEach(element => {
                const words = splitResults.get(element)?.words;
                trackAnimation(gsap.from(words?.length ? words : element, {
                    autoAlpha: 0,
                    yPercent: 60,
                    rotateX: -12,
                    transformOrigin: '50% 100%',
                    duration: 0.42,
                    stagger: words?.length ? 0.035 : 0,
                    ease: 'power2.out',
                    delay: 0.08,
                }));
            });
        }

        const aenorGlyphs = document.querySelectorAll('.lexique-page .lexique-aenor');
        if (aenorGlyphs.length && typeof window.SplitType === 'function' && 'IntersectionObserver' in window) {
            glyphObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (!entry.isIntersecting) return;
                    observer.unobserve(entry.target);

                    const split = new window.SplitType(entry.target, { types: 'chars' });
                    entry.target.classList.add('split-reveal');
                    splitInstances.add(split);
                    trackAnimation(gsap.from(split.chars, {
                        autoAlpha: 0,
                        y: 5,
                        duration: 0.28,
                        stagger: 0.018,
                        ease: 'power2.out',
                        onComplete: () => {
                            revertSplit(split);
                            entry.target.classList.remove('split-reveal');
                        },
                    }));
                });
            }, { rootMargin: '0px 0px -12% 0px' });

            aenorGlyphs.forEach(glyph => glyphObserver.observe(glyph));
        }
    }

    function destroy() {
        if (!initialized) return;
        initialized = false;
        glyphObserver?.disconnect();
        glyphObserver = undefined;
        animations.forEach(animation => animation.kill());
        animations.clear();
        cleanups.splice(0).reverse().forEach(cleanup => cleanup());
        document.querySelectorAll('.split-reveal').forEach(element => {
            element.classList.remove('split-reveal');
        });
        splitInstances.forEach(split => split.revert());
        splitInstances.clear();

        atroposInstances.splice(0).forEach(({ target, instance, originalNodes }) => {
            instance.destroy();
            const scale = target.querySelector(':scope > .atropos-scale');
            if (scale) {
                originalNodes.forEach(node => target.insertBefore(node, scale));
                scale.remove();
            }
            target.classList.remove('atropos');
        });
        document.documentElement.classList.remove('atropos-enabled');
        gsap = undefined;
    }

    const onMotionPreferenceChange = () => {
        destroy();
        initialize();
    };
    reducedMotion.addEventListener('change', onMotionPreferenceChange);
    window.addEventListener('pagehide', destroy);
    window.addEventListener('pageshow', event => {
        if (event.persisted) initialize();
    });

    window.AenorMotion = { init: initialize, destroy };
    initialize();
})();
