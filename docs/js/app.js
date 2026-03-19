/**
 * Dashboard — fetches briefing.json and renders categorized cards.
 */
(function () {
    'use strict';

    var DATA_URL = 'data/briefing.json';

    var CATEGORY_META = {
        anthropic_blog:    { label: 'Anthropic Blog',     icon: '#6B4CE6' },
        ai_models:         { label: 'AI Models',          icon: '#ec4899' },
        claude_code:       { label: 'Claude Code',        icon: '#10b981' },
        desktop:           { label: 'Desktop App',        icon: '#3b82f6' },
        office_plugins:    { label: 'Office Plugins',     icon: '#f59e0b' },
        chrome_extension:  { label: 'Chrome Extension',   icon: '#ef4444' }
    };

    var CATEGORY_ORDER = [
        'anthropic_blog', 'ai_models', 'claude_code',
        'desktop', 'office_plugins', 'chrome_extension'
    ];

    // Fetch data
    fetch(DATA_URL)
        .then(function (res) {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.json();
        })
        .then(render)
        .catch(function (err) {
            console.error('Failed to load briefing data:', err);
            document.getElementById('categories').innerHTML =
                '<div class="empty-state">Could not load briefing data. Try refreshing.</div>';
        });

    function render(data) {
        // Set briefing modal summary
        if (window.setBriefingSummary) {
            window.setBriefingSummary(data);
        }

        // Last updated
        if (data.generated) {
            var date = new Date(data.generated);
            document.getElementById('last-updated').textContent = relativeTime(date);
        }

        // Summary bar chips
        var summaryBar = document.getElementById('summary-bar');
        summaryBar.innerHTML = '';
        CATEGORY_ORDER.forEach(function (key) {
            var items = (data.categories && data.categories[key]) || [];
            var meta = CATEGORY_META[key];
            var chip = document.createElement('div');
            chip.className = 'summary-chip';
            chip.innerHTML =
                '<span class="chip-count" style="background:' + meta.icon + '">' + items.length + '</span>' +
                meta.label;
            chip.addEventListener('click', function () {
                var section = document.querySelector('.cat-' + key);
                if (section) section.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
            summaryBar.appendChild(chip);
        });

        // Category sections
        var container = document.getElementById('categories');
        container.innerHTML = '';
        CATEGORY_ORDER.forEach(function (key) {
            var items = (data.categories && data.categories[key]) || [];
            var meta = CATEGORY_META[key];

            var section = document.createElement('section');
            section.className = 'category-section cat-' + key;

            var header = document.createElement('div');
            header.className = 'category-header';
            header.innerHTML =
                '<div class="category-title">' +
                    '<span class="category-dot"></span>' +
                    '<h2>' + meta.label + '</h2>' +
                '</div>' +
                '<span class="category-badge">' + items.length + ' items</span>';

            var itemsDiv = document.createElement('div');
            itemsDiv.className = 'category-items';

            header.addEventListener('click', function () {
                itemsDiv.classList.toggle('collapsed');
            });

            if (items.length === 0) {
                itemsDiv.innerHTML = '<div class="empty-state">No new updates</div>';
            } else {
                items.forEach(function (item) {
                    itemsDiv.appendChild(createCard(item));
                });
            }

            section.appendChild(header);
            section.appendChild(itemsDiv);
            container.appendChild(section);
        });
    }

    function createCard(item) {
        var card = document.createElement('div');
        card.className = 'card';

        var dateStr = item.date ? relativeTime(new Date(item.date)) : '';
        var titleHtml = item.url
            ? '<a href="' + escapeAttr(item.url) + '" target="_blank" rel="noopener">' + escapeHtml(item.title) + '</a>'
            : escapeHtml(item.title);

        card.innerHTML =
            '<div class="card-title">' + titleHtml + '</div>' +
            '<div class="card-meta"><span class="card-date">' + escapeHtml(dateStr) + '</span></div>' +
            (item.summary ? '<div class="card-summary">' + escapeHtml(item.summary) + '</div>' : '');

        return card;
    }

    function relativeTime(date) {
        var now = new Date();
        var diff = now - date;
        var minutes = Math.floor(diff / 60000);
        var hours = Math.floor(diff / 3600000);
        var days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'just now';
        if (minutes < 60) return minutes + 'm ago';
        if (hours < 24) return hours + 'h ago';
        if (days < 7) return days + 'd ago';
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    function escapeAttr(text) {
        return (text || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
})();
