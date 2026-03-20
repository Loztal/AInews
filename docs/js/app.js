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
        chrome_extension:  { label: 'Chrome Extension',   icon: '#ef4444' },
        twitter:           { label: 'Twitter',            icon: '#1d9bf0' }
    };

    var CATEGORY_ORDER = [
        'claude_code', 'twitter', 'anthropic_blog', 'ai_models',
        'desktop', 'office_plugins', 'chrome_extension'
    ];

    var COLLAPSE_KEY = 'collapsed-sections';
    var LAST_VISIT_KEY = 'last-visit-ts';

    // Get last visit time for "NEW" badges, then update it
    var lastVisit = localStorage.getItem(LAST_VISIT_KEY);
    var lastVisitDate = lastVisit ? new Date(lastVisit) : null;
    localStorage.setItem(LAST_VISIT_KEY, new Date().toISOString());

    function getCollapsedSections() {
        try {
            return JSON.parse(localStorage.getItem(COLLAPSE_KEY)) || {};
        } catch (e) {
            return {};
        }
    }

    function setCollapsedSection(key, collapsed) {
        var state = getCollapsedSections();
        state[key] = collapsed;
        localStorage.setItem(COLLAPSE_KEY, JSON.stringify(state));
    }

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
            var footer = document.getElementById('footer-updated');
            if (footer) {
                footer.innerHTML = 'Updated ' + formatLocalTime(date);
            }
        }

        // Search input
        var searchWrap = document.getElementById('search-wrap');
        if (searchWrap) {
            searchWrap.innerHTML =
                '<input type="search" id="search-input" class="search-input" placeholder="Filter articles..." aria-label="Filter articles">';
            var searchInput = document.getElementById('search-input');
            searchInput.addEventListener('input', function () {
                filterCards(this.value.trim().toLowerCase());
            });
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
        var collapsedState = getCollapsedSections();

        CATEGORY_ORDER.forEach(function (key) {
            var items = (data.categories && data.categories[key]) || [];
            var meta = CATEGORY_META[key];

            var section = document.createElement('section');
            section.className = 'category-section cat-' + key;

            // Accessible collapsible header
            var header = document.createElement('button');
            header.className = 'category-header';
            header.setAttribute('aria-expanded', collapsedState[key] ? 'false' : 'true');
            header.innerHTML =
                '<div class="category-title">' +
                    '<span class="category-dot"></span>' +
                    '<h2>' + meta.label + '</h2>' +
                '</div>' +
                '<span class="category-badge">' + items.length + ' items</span>';

            var itemsDiv = document.createElement('div');
            itemsDiv.className = 'category-items';
            itemsDiv.setAttribute('role', 'region');
            itemsDiv.setAttribute('aria-label', meta.label + ' items');

            // Restore collapsed state
            if (collapsedState[key]) {
                itemsDiv.classList.add('collapsed');
            }

            header.addEventListener('click', function () {
                var isCollapsed = itemsDiv.classList.toggle('collapsed');
                header.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
                setCollapsedSection(key, isCollapsed);
            });

            if (items.length === 0) {
                itemsDiv.innerHTML = '<div class="empty-state">No new updates</div>';
            } else {
                // Split model spec items from regular news items
                var specItems = items.filter(function (i) { return i.tiers; });
                var newsItems = items.filter(function (i) { return !i.tiers; });

                specItems.forEach(function (item) {
                    itemsDiv.appendChild(createModelCard(item));
                });
                newsItems.forEach(function (item) {
                    itemsDiv.appendChild(createCard(item));
                });
            }

            section.appendChild(header);
            section.appendChild(itemsDiv);
            container.appendChild(section);
        });
    }

    function isNewItem(item) {
        if (!lastVisitDate || !item.date) return false;
        return new Date(item.date) > lastVisitDate;
    }

    function createCard(item) {
        var card;
        if (item.url) {
            card = document.createElement('a');
            card.href = item.url;
            card.target = '_blank';
            card.rel = 'noopener';
            card.className = 'card card-link';
        } else {
            card = document.createElement('div');
            card.className = 'card';
        }

        var dateStr = item.date ? relativeTime(new Date(item.date)) : '';
        var newBadge = isNewItem(item) ? '<span class="badge-new">NEW</span>' : '';

        card.innerHTML =
            '<div class="card-title">' + newBadge + escapeHtml(item.title) + '</div>' +
            '<div class="card-meta"><span class="card-date">' + escapeHtml(dateStr) + '</span></div>' +
            (item.summary ? '<div class="card-summary">' + escapeHtml(item.summary) + '</div>' : '');

        return card;
    }

    function createModelCard(item) {
        var card = document.createElement('div');
        card.className = 'card model-card';

        var tiersHtml = '';
        if (item.tiers) {
            var tierOrder = ['Free', 'Pro', 'Max 5x', 'Max 20x', 'Team Std', 'Team Prem', 'Enterprise', 'API'];
            tierOrder.forEach(function (tier) {
                var val = item.tiers[tier] || '-';
                var cls = val === '-' ? 'tier-badge tier-unavailable' : 'tier-badge tier-available';
                tiersHtml += '<div class="' + cls + '">' +
                    '<span class="tier-name">' + escapeHtml(tier) + '</span>' +
                    '<span class="tier-value">' + escapeHtml(val) + '</span>' +
                    '</div>';
            });
        }

        card.innerHTML =
            '<div class="model-header">' +
                '<div class="card-title">' + escapeHtml(item.title) + '</div>' +
                '<div class="model-context">' + escapeHtml(item.context_window || '') + '</div>' +
            '</div>' +
            '<div class="model-info">' +
                '<span>Max output: ' + escapeHtml(item.max_output || '') + '</span>' +
                '<span>API: ' + escapeHtml(item.pricing_input || '') + ' in / ' + escapeHtml(item.pricing_output || '') + ' out</span>' +
            '</div>' +
            '<div class="model-tiers">' + tiersHtml + '</div>';

        return card;
    }

    function filterCards(query) {
        var sections = document.querySelectorAll('.category-section');
        sections.forEach(function (section) {
            var cards = section.querySelectorAll('.card');
            var anyVisible = false;
            cards.forEach(function (card) {
                var text = card.textContent.toLowerCase();
                var match = !query || text.indexOf(query) !== -1;
                card.style.display = match ? '' : 'none';
                if (match) anyVisible = true;
            });
            section.style.display = anyVisible || !query ? '' : 'none';
        });
    }

    function formatLocalTime(date) {
        try {
            return date.toLocaleString(undefined, {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                timeZoneName: 'short'
            });
        } catch (e) {
            return date.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
        }
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
})();
