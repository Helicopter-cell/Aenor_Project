(() => {
    'use strict';

    window.AenorLexiqueControls?.destroy();

    const storageKey = 'aenor-lexique-visible-columns';
    const columns = ['aenor', 'audio', 'latin', 'phonetic', 'french'];

    function initialize() {
        window.AenorLexiqueControls?.destroy();

        const page = document.querySelector('.lexique-page');
        const toolbar = page?.querySelector('[data-lexique-toolbar]');
        const categories = page?.querySelector('#lexique-categories');
        const toggleButton = toolbar?.querySelector('[data-lexique-toggle-all]');
        const toggleIcon = toolbar?.querySelector('[data-lexique-toggle-icon]');
        const toggleLabel = toolbar?.querySelector('[data-lexique-toggle-label]');
        const status = toolbar?.querySelector('[data-lexique-toolbar-status]');
        const checkboxes = Array.from(toolbar?.querySelectorAll('[data-lexique-column]') || []);

        if (!page || !toolbar || !categories || !toggleButton || !toggleLabel || !toggleIcon) return;

        let refreshFrame = 0;
        let active = true;

        function visibleAccordions() {
            return Array.from(categories.querySelectorAll('details.cours-accordion'))
                .filter(details => !details.hidden);
        }

        function updateToggleState() {
            const details = visibleAccordions();
            const allOpen = details.length > 0 && details.every(item => item.open);
            toggleButton.setAttribute('aria-expanded', String(allOpen));
            toggleLabel.textContent = allOpen ? 'Tout fermer' : 'Tout ouvrir';
            toggleIcon.textContent = allOpen ? '−' : '＋';
        }

        function scheduleRefresh() {
            if (refreshFrame) return;
            refreshFrame = window.requestAnimationFrame(() => {
                refreshFrame = 0;
                if (!active) return;
                updateToggleState();
                window.AenorLenis?.resize?.();
            });
        }

        function persistColumns() {
            const preferences = Object.fromEntries(checkboxes.map(input => [
                input.dataset.lexiqueColumn,
                input.checked,
            ]));
            try {
                window.localStorage.setItem(storageKey, JSON.stringify(preferences));
            } catch (error) {
                console.warn('Les préférences du lexique ne peuvent pas être enregistrées.', error);
            }
        }

        function applyColumnPreferences() {
            checkboxes.forEach(input => {
                const column = input.dataset.lexiqueColumn;
                if (columns.includes(column)) {
                    page.dataset[`hide${column[0].toUpperCase()}${column.slice(1)}`] = String(!input.checked);
                }
            });
        }

        function restoreColumnPreferences() {
            let preferences;
            try {
                const stored = window.localStorage.getItem(storageKey);
                if (stored) {
                    preferences = JSON.parse(stored);
                    if (!preferences || typeof preferences !== 'object' || Array.isArray(preferences)) {
                        throw new TypeError('Format de préférences invalide.');
                    }
                }
            } catch (error) {
                console.warn('Les préférences du lexique sont invalides; les valeurs par défaut sont utilisées.', error);
                preferences = undefined;
            }

            if (preferences) {
                checkboxes.forEach(input => {
                    const column = input.dataset.lexiqueColumn;
                    if (columns.includes(column) && typeof preferences[column] === 'boolean') {
                        input.checked = preferences[column];
                    }
                });
            }

            if (!checkboxes.some(input => input.checked)) {
                checkboxes[0].checked = true;
            }
            applyColumnPreferences();
        }

        function onColumnChange(event) {
            const input = event.target;
            if (!(input instanceof HTMLInputElement) || !input.matches('[data-lexique-column]')) return;

            if (!checkboxes.some(checkbox => checkbox.checked)) {
                input.checked = true;
                if (status) status.textContent = 'Au moins une information doit rester visible.';
                return;
            }
            if (status) status.textContent = '';
            applyColumnPreferences();
            persistColumns();
        }

        function onToggleAll() {
            const details = visibleAccordions();
            const shouldOpen = !details.length || !details.every(item => item.open);
            details.forEach(item => {
                item.open = shouldOpen;
            });
            updateToggleState();
            scheduleRefresh();
        }

        function onDetailsToggle(event) {
            if (event.target instanceof HTMLDetailsElement && categories.contains(event.target)) {
                scheduleRefresh();
            }
        }

        function onSearchInput() {
            scheduleRefresh();
        }

        function destroy() {
            if (!active) return;
            active = false;
            if (refreshFrame) window.cancelAnimationFrame(refreshFrame);
            document.removeEventListener('toggle', onDetailsToggle, true);
            toolbar.removeEventListener('click', onToolbarClick);
            toolbar.removeEventListener('change', onColumnChange);
            document.querySelector('#lexique-search')?.removeEventListener('input', onSearchInput);
        }

        function onToolbarClick(event) {
            if (event.target instanceof Element && event.target.closest('[data-lexique-toggle-all]')) {
                onToggleAll();
            }
        }

        toolbar.addEventListener('click', onToolbarClick);
        toolbar.addEventListener('change', onColumnChange);
        document.addEventListener('toggle', onDetailsToggle, true);
        document.querySelector('#lexique-search')?.addEventListener('input', onSearchInput);
        restoreColumnPreferences();
        updateToggleState();

        window.AenorLexiqueControls = { init: initialize, destroy };
    }

    initialize();
})();
