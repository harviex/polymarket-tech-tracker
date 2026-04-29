// app.js - Main Application Logic (With News Display)
const App = (() => {
    let eventsData = { new_entries: [], exited_entries: [], long_term: {} };
    let currentFilter = 'all';
    
    async function init() {
        await loadEvents();
        renderEvents();
        setupSearch();
        setupFilters();
    }
    
    async function loadEvents() {
        try {
            const response = await fetch('data/technology/events.json');
            if (response.ok) {
                eventsData = await response.json();
            }
        } catch (error) {
            console.error('Failed to load events:', error);
        }
    }
    
    function renderEvents() {
        renderNewEntries();
        renderExitedEntries();
        renderLongTerm();
        updateCounts();
    }
    
    function renderNewEntries() {
        const container = document.getElementById('new-entries-list');
        if (!container) return;
        
        const filtered = filterEvents(eventsData.new_entries);
        
        if (filtered.length === 0) {
            container.innerHTML = '<p class="no-results">No events found</p>';
            return;
        }
        
        container.innerHTML = filtered.map(event => `
            <div class="event-card scroll-animate" data-tags="${event.tags?.join(',') || ''}">
                <div class="event-header">
                    <div class="event-title">${event.title}</div>
                    <div class="event-probability">${(event.probability * 100).toFixed(1)}%</div>
                </div>
                <div class="event-meta">
                    <span class="label-new">NEW</span>
                    <span>${event.hours_ago} hours ago</span>
                    ${event.news ? '<span class="badge-news">📰 News</span>' : ''}
                </div>
                ${event.tags ? `<div class="event-tags">${event.tags.map(t => `<span class="tag">${t}</span>`).join('')}</div>` : ''}
                
                ${event.news ? `
                <div class="news-preview">
                    <div class="news-source">📰 ${event.news.source} • ${new Date(event.news.timestamp).toLocaleDateString()}</div>
                    <div class="news-title">${event.news.title}</div>
                    <div class="news-content">${event.news.content.substring(0, 150)}...</div>
                    <a href="${event.news.url}" target="_blank" class="news-link">Read more →</a>
                </div>
                ` : ''}
            </div>
        `).join('');
    }
    
    function renderExitedEntries() {
        const container = document.getElementById('exited-entries-list');
        if (!container) return;
        
        const filtered = filterEvents(eventsData.exited_entries);
        
        if (filtered.length === 0) {
            container.innerHTML = '<p class="no-results">No events found</p>';
            return;
        }
        
        container.innerHTML = filtered.map(event => `
            <div class="event-card scroll-animate">
                <div class="event-header">
                    <div class="event-title">${event.title}</div>
                    <div class="event-probability">${(event.probability * 100).toFixed(1)}%</div>
                </div>
                <div class="event-meta">
                    <span>${event.hours_ago} hours ago</span>
                    ${event.news ? '<span class="badge-news">📰 News</span>' : ''}
                </div>
                
                ${event.news ? `
                <div class="news-preview news-exited">
                    <div class="news-source">📰 ${event.news.source} • ${new Date(event.news.timestamp).toLocaleDateString()}</div>
                    <div class="news-title">${event.news.title}</div>
                    <div class="news-content">${event.news.content.substring(0, 150)}...</div>
                    <a href="${event.news.url}" target="_blank" class="news-link">Read more →</a>
                </div>
                ` : ''}
            </div>
        `).join('');
    }
    
    function renderLongTerm() {
        const container = document.getElementById('long-term-groups');
        if (!container) return;
        
        const longTerm = eventsData.long_term || {};
        const tags = Object.keys(longTerm);
        
        if (tags.length === 0) {
            container.innerHTML = '<p class="no-results">No long-term events</p>';
            return;
        }
        
        container.innerHTML = tags.map(tag => `
            <div class="tag-group">
                <h3>${tag.toUpperCase()} (${longTerm[tag].length})</h3>
                ${longTerm[tag].map(event => `
                    <div class="event-card" style="margin-bottom: 0.5rem; padding: 1rem;">
                        <div class="event-header">
                            <div class="event-title" style="font-size: 0.875rem;">${event.title}</div>
                            <div class="event-probability" style="font-size: 1rem;">${(event.probability * 100).toFixed(1)}%</div>
                        </div>
                        ${event.days_in_high ? `<div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.5rem;">${event.days_in_high} days in high</div>` : ''}
                    </div>
                `).join('')}
            </div>
        `).join('');
    }
    
    function filterEvents(events) {
        if (currentFilter === 'all') return events;
        return events.filter(e => e.tags?.includes(currentFilter));
    }
    
    function updateCounts() {
        const newCount = document.getElementById('new-count');
        const exitedCount = document.getElementById('exited-count');
        if (newCount) newCount.textContent = eventsData.new_entries.length;
        if (exitedCount) exitedCount.textContent = eventsData.exited_entries.length;
    }
    
    function setupSearch() {
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;
        
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.event-card').forEach(card => {
                const title = card.querySelector('.event-title')?.textContent.toLowerCase() || '';
                card.style.display = title.includes(query) ? 'block' : 'none';
            });
        });
    }
    
    function setupFilters() {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                renderEvents();
            });
        });
    }
    
    return {
        init,
        loadEvents,
        renderEvents
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
