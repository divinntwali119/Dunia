document.addEventListener('DOMContentLoaded', function () {
    const filters = document.getElementById('filterContainer');
    const grid = document.querySelector('[data-catalog]');
    if (!filters || !grid) return;

    const cards = Array.from(grid.querySelectorAll('[data-category]'));
    const buttons = filters.querySelectorAll('[data-category]');
    const count = document.getElementById('resultCount');
    const label = document.getElementById('resultLabel');
    const empty = document.getElementById('noResults');
    const reset = document.getElementById('resetFilterBtn') || document.getElementById('resetSearchBtn');

    function filter(category) {
        let visible = 0;
        cards.forEach(function (card) {
            card.hidden = category !== 'all' && card.dataset.category !== category;
            if (!card.hidden) visible += 1;
        });
        buttons.forEach(function (button) {
            const active = button.dataset.category === category;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        });
        count.textContent = visible;
        label.textContent = visible === 1 ? grid.dataset.singular : grid.dataset.plural;
        empty.hidden = visible !== 0;
        window.dispatchEvent(new Event('scroll'));
    }

    buttons.forEach(function (button) {
        button.addEventListener('click', function () {
            filter(button.dataset.category);
        });
    });
    if (reset) reset.addEventListener('click', function () { filter('all'); });
    filter('all');
});
