/**
 * Briefing modal — shows AI-generated summary on app open (session prompt).
 */
(function () {
    'use strict';

    const modal = document.getElementById('briefing-modal');
    const modalDate = document.getElementById('modal-date');
    const modalSummary = document.getElementById('modal-summary');
    const dismissBtn = document.getElementById('modal-dismiss');
    const dashboard = document.getElementById('dashboard');

    dismissBtn.addEventListener('click', function () {
        modal.classList.add('hidden');
        dashboard.classList.remove('hidden');
        sessionStorage.setItem('briefing-dismissed', 'true');
    });

    // If already dismissed this session, skip modal
    if (sessionStorage.getItem('briefing-dismissed') === 'true') {
        modal.classList.add('hidden');
        dashboard.classList.remove('hidden');
    }

    window.setBriefingSummary = function (data) {
        var date = data.generated ? new Date(data.generated) : new Date();
        modalDate.textContent = date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        if (data.briefing_summary) {
            modalSummary.innerHTML = '<p>' + escapeHtml(data.briefing_summary) + '</p>';
        } else {
            modalSummary.innerHTML = '<p class="empty-state">No briefing available yet.</p>';
        }
    };

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();
