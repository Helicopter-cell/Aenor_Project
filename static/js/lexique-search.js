(function () {
    'use strict';

    function normalizeText(value) {
        return value
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLocaleLowerCase('fr-FR');
    }

    function initializeLexique() {
        const searchInput = document.querySelector('#lexique-search');
        const lexique = document.querySelector('.lexique-page');
        const accordions = document.querySelectorAll('.cours-accordion');
        const entries = document.querySelectorAll('.lexique-entry');

        if (!searchInput || !lexique) {
            return;
        }

        const noResults = document.querySelector('#lexique-no-results');
        accordions.forEach(function (details) {
            details.open = false;
        });

        const entryRecords = Array.from(entries).map(function (entry) {
            return {
                element: entry,
                searchableText: normalizeText(entry.textContent)
            };
        });

        function restoreDefaultState() {
            entryRecords.forEach(function (record) {
                record.element.hidden = false;
            });

            accordions.forEach(function (details) {
                details.hidden = false;
                details.open = false;
            });

            if (noResults) {
                noResults.hidden = true;
            }
        }

        function filterLexique() {
            const query = normalizeText(searchInput.value.trim());

            if (!query) {
                restoreDefaultState();
                return;
            }

            let matchCount = 0;
            entryRecords.forEach(function (record) {
                const matches = record.searchableText.includes(query);
                record.element.hidden = !matches;
                if (matches) {
                    matchCount += 1;
                }
            });

            accordions.forEach(function (details) {
                const hasVisibleEntry = details.querySelector('.lexique-entry:not([hidden])');
                details.hidden = !hasVisibleEntry;
                if (hasVisibleEntry) {
                    details.open = true;
                }
            });

            if (noResults) {
                noResults.hidden = matchCount !== 0;
            }
        }

        searchInput.addEventListener('input', filterLexique);
        restoreDefaultState();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeLexique);
    } else {
        initializeLexique();
    }
}());
