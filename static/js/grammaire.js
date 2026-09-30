document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.cours-accordion').forEach(function (details) {
        details.open = false;
        const summary = details.querySelector(':scope > .cours-summary');
        const chevron = details.querySelector(':scope > .cours-summary .cours-chevron');

        if (summary) {
            summary.addEventListener('click', function (event) {
                event.preventDefault();
                details.open = !details.open;
            });
        }

        const syncState = function () {
            const isOpen = details.open;
            details.setAttribute('aria-expanded', String(isOpen));
            if (chevron) {
                chevron.textContent = isOpen ? '▼' : '▶';
            }
        };

        details.addEventListener('toggle', syncState);
        syncState();
    });
});