// app.js - Tag Summary Cards + Lazy Load Events
const App = (() => {
    let eventsData = { 
        new_entries: [], 
        exited_entries: [], 
        long_term_summaries: [],
        long_term_count: 0
    };
    let expandedTagIdx = null;
    
    async function init() {
        await loadEvents();
        renderEvents();
        setupSearch();
        setupScrollAnimations();
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
        renderLongTermSummaries();
        updateCounts();
    }
    
    function renderNewEntries() {
        const container = document.getElementById('new-entries-list');
        if (!container) return;
        
        const events = eventsData.new_entries;
        
        if (events.length === 0) {
            container.innerHTML = '<p class="no-results">No events found</p>';
            return;
        }
        
        container.innerHTML = events.map(event => `
            <div class="event-card" data-tags="${event.tags?.join(',') || ''}">
                <div class="event-header">
                    <div class="event-title">${event.title}</div>
                    <div class="event-probability">${(event.probability * 100).toFixed(1)}%</div>
                </div>
                <div class="event-meta">
                    <span class="label-new">NEW</span>
                    <span>↑ +${(event.change * 100).toFixed(1)}%</span>
                    ${event.crossed_threshold ? `<span class="badge-threshold">越过 ${(event.crossed_threshold * 100).toFixed(0)}% 线</span>` : ''}
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
        
        const events = eventsData.exited_entries;
        
        if (events.length === 0) {
            container.innerHTML = '<p class="no-results">No events found</p>';
            return;
        }
        
        container.innerHTML = events.map(event => `
            <div class="event-card">
                <div class="event-header">
                    <div class="event-title">${event.title}</div>
                    <div class="event-probability">${(event.probability * 100).toFixed(1)}%</div>
                </div>
                <div class="event-meta">
                    <span>↓ -${(event.change * 100).toFixed(1)}%</span>
                    ${event.crossed_threshold ? `<span class="badge-threshold">低过 ${(event.crossed_threshold * 100).toFixed(0)}% 线</span>` : ''}
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
    
    function renderLongTermSummaries() {
        const container = document.getElementById('long-term-groups');
        if (!container) return;
        
        const summaries = eventsData.long_term_summaries || [];
        
        if (summaries.length === 0) {
            container.innerHTML = '<p class="no-results">No long-term events</p>';
            return;
        }
        
        container.innerHTML = `
            <div class="summary-cards-grid">
                ${summaries.map((summary, idx) => `
                    <div class="summary-card glass-card" onclick="toggleTagSummary(${idx})">
                        <div class="summary-header">
                            <div class="summary-tag">${summary.tag_display || summary.tag.toUpperCase()}</div>
                            <div class="summary-toggle">
                                ${expandedTagIdx === idx ? '▼' : '▶'}
                            </div>
                        </div>
                        <div class="summary-stats">
                            <div class="stat">
                                <div class="stat-value">${summary.event_count}</div>
                                <div class="stat-label">Events</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${(summary.avg_probability * 100).toFixed(1)}%</div>
                                <div class="stat-label">Avg</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${(summary.max_probability * 100).toFixed(1)}%</div>
                                <div class="stat-label">Max</div>
                            </div>
                        </div>
                        <div class="summary-meta">
                            Min: ${(summary.min_probability * 100).toFixed(1)}% | Range: ${((summary.max_probability - summary.min_probability) * 100).toFixed(1)}%
                        </div>
                        
                        <div class="summary-events" id="summary-events-${idx}" style="display: ${expandedTagIdx === idx ? 'block' : 'none'};">
                            <!-- Lazy loaded events will appear here -->
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    function toggleTagSummary(idx) {
        if (expandedTagIdx === idx) {
            expandedTagIdx = null;
        } else {
            expandedTagIdx = idx;
            loadSummaryEvents(idx);
        }
        renderLongTermSummaries();
    }
    
    function loadSummaryEvents(idx) {
        const summary = eventsData.long_term_summaries[idx];
        if (!summary || !summary.events) return;
        
        const container = document.getElementById(`summary-events-${idx}`);
        if (!container || container.children.length > 0) return;
        
        container.innerHTML = `
            <div class="events-divider"></div>
            <div class="events-grid">
                ${summary.events.map(event => `
                    <div class="event-mini-card">
                        <div class="event-mini-title">${event.title}</div>
                        <div class="event-mini-probability">${(event.probability * 100).toFixed(1)}%</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    function updateCounts() {
        const newCount = document.getElementById('new-count');
        const exitedCount = document.getElementById('exited-count');
        if (newCount) newCount.textContent = eventsData.new_entries.length;
        if (exitedCount) exitedCount.textContent = eventsData.exited_entries.length;
        
        const longTermCount = document.getElementById('long-term-count');
        if (longTermCount) longTermCount.textContent = eventsData.long_term_count || 0;
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
    
    function setupScrollAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.1 });
        
        document.querySelectorAll('.scroll-animate').forEach(el => {
            observer.observe(el);
        });
    }
    
    return {
        init,
        toggleTagSummary,
        loadEvents,
        renderEvents
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
