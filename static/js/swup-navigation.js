(() => {
    const normalizePath = path => path.replace(/\/+$/, '') || '/';

    function updateActiveNavigation() {
        const token = document.querySelector('#swup')?.dataset.csrfToken;
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (token && csrfMeta) csrfMeta.content = token;

        const currentPath = normalizePath(window.location.pathname);
        document.querySelectorAll('.site-header .nav-element').forEach(link => {
            const linkPath = normalizePath(new URL(link.href, window.location.origin).pathname);
            const isCurrent = linkPath === currentPath
                || (linkPath === '/admin' && currentPath.startsWith('/stats'));
            if (isCurrent) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
        });
    }

    document.addEventListener('click', event => {
        if (!(event.target instanceof Element)) return;
        const toggle = event.target.closest('.mobile-menu-toggle');
        if (!toggle) return;

        const navigation = document.getElementById(toggle.getAttribute('aria-controls'));
        if (!navigation) return;
        const isOpen = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', String(!isOpen));
        toggle.classList.toggle('open', !isOpen);
        navigation.classList.toggle('open', !isOpen);
    });

    function disposePage() {
        window.AenorLexiqueControls?.destroy();
        window.AenorMotion?.destroy();
        window.AenorLenis?.destroy();
        window.AenorSpeech?.destroy();
        window.AenorTranslator?.destroy();
        window.AenorHomeOrb?.destroy();
        window.AenorScenario?.destroy();
    }

    function initializePage() {
        updateActiveNavigation();
        window.AenorLexiqueControls?.init();
        window.AenorMotion?.init();
        document.querySelector('#main-content')?.focus({ preventScroll: true });
        window.AenorAmbientCurves?.refresh();
    }

    updateActiveNavigation();
    if (typeof window.Swup !== 'function' || typeof window.SwupScriptsPlugin !== 'function') {
        console.warn('Swup could not be initialized; native page navigation remains active.');
        return;
    }

    const swup = new window.Swup({
        containers: ['#swup'],
        plugins: [new window.SwupScriptsPlugin({ head: false, body: true })],
    });
    swup.hooks.before('content:replace', disposePage);
    swup.hooks.on('page:view', initializePage);
    window.AenorSwup = swup;
})();
