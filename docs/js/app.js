// app.js - Main Application Logic
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
            } else {
                // Fallback to sample data
                eventsData = generateSampleData();
            }
        } catch (error) {
            console.error('Failed to load events:', error);
            eventsData = generateSampleData();
        }
    }
    
    function generateSampleData() {
        return {
            new_entries: [
                {
                    id: '1',
                    title: 'AI will surpass human intelligence by 2027',
                    probability: 0.72,
                    hours_ago: 2,
                    tags: ['ai', 'technology']
                },
                {
                    id: '2',
                    title: 'Bitcoin reaches $100k in 2026',
                    probability: 0.75,
                    hours_ago: 1,
                    tags: ['crypto']
                }
            ],
            exited_entries: [
                {
                    id: '3',
                    title: 'Metaverse adoption hits 50% by 2026',
                    probability: 0.65,
                    hours_ago: 2
                }
            ],
            long_term: {
                'ai': [
                    { id: '4', title: 'GPT-5 releases in 2026', probability: 0.85 },
                    { id: '5', title: 'AI writes 50% of code by 2027', probability: 0.78 }
                ],
                'crypto': [
                    { id: '6', title: 'Ethereum 3.0 launches', probability: 0.71 }
                ]
            }
        };
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
            container.innerHTML = '<p class="no-results" data-i18n="no_results">No events found</p>';
            return;
        }
        
        container.innerHTML = filtered.map(event => `
            <div class="event-card scroll-animate" data-tags="\${event.tags?.join(',') || ''}">
                <div class="event-header">
                    <div class="event-title">\${event.title}</div>
                    <div class="event-probability">\${(event.probability * 100).toFixed(1)}%</div>
                </div>
                <div class="event-meta">
                    <span class="label-new">NEW</span>
                    <span>\${event.hours_ago} \${I18n.t('label_hours')}</span>
                </div>
                \${event.tags ? \`<div class="event-tags">\${event.tags.map(t => \`<span class="tag">\${t}</span>\`).join('')}</div>\` : ''}
            </div>
        `).join('');
    }
    
    function renderExitedEntries() {
        const container = document.getElementById('exited-entries-list');
        if (!container) return;
        
        if (eventsData.exited_entries.length === 0) {
            container.innerHTML = '<p class="no-results" data-i18n="no_results">No events found</p>';
            return;
        }
        
        container.innerHTML = eventsData.exited_entries.map(event => `
            <div class="event-card scroll-animate">
                <div class="event-header">
                    <div class="event-title">\${event.title}</div>
                    <div class="event-probability">\${(event.probability * 100).toFixed(1)}%</div>
                </div>
                <div class="event-meta">
                    <span>\${event.hours_ago} \${I18n.t('label_hours')}</span>
                </div>
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
                <h3>\${tag.toUpperCase()} (\${longTerm[tag].length})</h3>
                \${longTerm[tag].map(event => `
                    <div class="event-card" style="margin-bottom: 0.5rem; padding: 1rem;">
                        <div class="event-header">
                            <div class="event-title" style="font-size: 0.875rem;">\${event.title}</div>
                            <div class="event-probability" style="font-size: 1rem;">\${(event.probability * 100).toFixed(1)}%</div>
                        </div>
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

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
