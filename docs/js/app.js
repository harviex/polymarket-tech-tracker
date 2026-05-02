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
        renderHourWatchSummaries();
        renderDailyWatchSummaries();
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
                    <div class="summary-card glass-card" onclick="App.toggleTagSummary(${idx})">
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
                            ${expandedTagIdx === idx && summary.events ? renderLongTermEventsList(summary.events) : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    

    
    // 1-Hour Watch Events
    let expandedHourWatchIdx = null;
    
    function renderHourWatchSummaries() {
        const container = document.getElementById('hour-watch-groups');
        if (!container) return;
        
        const summaries = eventsData.hour_watch_summaries || [];
        
        if (summaries.length === 0) {
            container.innerHTML = '<p class="no-results">No 1-hour watch events</p>';
            return;
        }
        
        container.innerHTML = `
            <div class="summary-cards-grid">
                ${summaries.map((summary, idx) => `
                    <div class="summary-card glass-card" onclick="App.toggleHourWatchSummary(${idx})">
                        <div class="summary-header">
                            <div class="summary-tag">${summary.tag_display || summary.tag.toUpperCase()}</div>
                            <div class="summary-toggle">
                                ${expandedHourWatchIdx === idx ? '▼' : '▶'}
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
                        
                        <div class="summary-events" id="hour-watch-events-${idx}" style="display: ${expandedHourWatchIdx === idx ? 'block' : 'none'}">
                            ${expandedHourWatchIdx === idx && summary.events ? renderHourWatchEventsList(summary.events) : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    function formatHistory(history) {
        if (!history || history.length === 0) return '';
        return history.map(h => {
            const arrow = h.direction === 'up' ? '↑' : '↓';
            const threshold_text = h.threshold ? ` (${h.direction === 'up' ? '越过' : '低过'}${(h.threshold * 100).toFixed(0)}%线)` : '';
            return `${h.time}: ${(h.prob * 100).toFixed(1)}% ${arrow}${threshold_text}`;
        }).join('<br>');
    }
    
    function toggleHourWatchSummary(idx) {
        if (expandedHourWatchIdx === idx) {
            expandedHourWatchIdx = null;
        } else {
            expandedHourWatchIdx = idx;
        }
        renderHourWatchSummaries();
    }
    
    function renderHourWatchEventsList(events) {
        if (!events || events.length === 0) return '';
        
        return `
            <div class="events-divider"></div>
            <div class="events-grid">
                ${events.map(event => `
                    <div class="event-mini-card" onclick="window.location.href='event-detail.html?id=${event.id}'" style="cursor: pointer;">
                        <div class="event-mini-header">
                            <div class="event-mini-title">${event.title}</div>
                            <div class="event-mini-probability">${(event.current_prob * 100).toFixed(1)}%</div>
                        </div>
                        ${event.history ? `
                            <div class="event-history">
                                <small>${formatHistory(event.history)}</small>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Daily Watch Events
    let expandedDailyWatchIdx = null;
    
    function renderDailyWatchSummaries() {
        const container = document.getElementById('daily-watch-groups');
        if (!container) return;
        
        const summaries = eventsData.daily_watch_summaries || [];
        
        if (summaries.length === 0) {
            container.innerHTML = '<p class="no-results">No daily watch events</p>';
            return;
        }
        
        container.innerHTML = `
            <div class="summary-cards-grid">
                ${summaries.map((summary, idx) => `
                    <div class="summary-card glass-card" onclick="App.toggleDailyWatchSummary(${idx})">
                        <div class="summary-header">
                            <div class="summary-tag">${summary.tag_display || summary.tag.toUpperCase()}</div>
                            <div class="summary-toggle">
                                ${expandedDailyWatchIdx === idx ? '▼' : '▶'}
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
                        
                        <div class="summary-events" id="daily-watch-events-${idx}" style="display: ${expandedDailyWatchIdx === idx ? 'block' : 'none'}">
                            ${expandedDailyWatchIdx === idx && summary.events ? renderDailyWatchEventsList(summary.events) : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    function toggleDailyWatchSummary(idx) {
        if (expandedDailyWatchIdx === idx) {
            expandedDailyWatchIdx = null;
        } else {
            expandedDailyWatchIdx = idx;
        }
        renderDailyWatchSummaries();
    }
    
    function renderDailyWatchEventsList(events) {
        if (!events || events.length === 0) return '';
        
        return `
            <div class="events-divider"></div>
            <div class="events-grid">
                ${events.map(event => `
                    <div class="event-mini-card" onclick="window.location.href='event-detail.html?id=${event.id}'" style="cursor: pointer;">
                        <div class="event-mini-header">
                            <div class="event-mini-title">${event.title}</div>
                            <div class="event-mini-probability">${(event.current_prob * 100).toFixed(1)}%</div>
                        </div>
                        ${event.history ? `
                            <div class="event-history">
                                <small>${formatHistory(event.history)}</small>
                            </div>
                        ` : ''}
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
        }
        renderLongTermSummaries();
    }
    
    function renderLongTermEventsList(events) {
        if (!events || events.length === 0) return '';
        
        return `
            <div class="events-divider"></div>
            <div class="events-grid">
                ${events.map(event => `
                    <div class="event-mini-card" onclick="window.location.href='event-detail.html?id=${event.id}'" style="cursor: pointer;">
                        <div class="event-mini-header">
                            <div class="event-mini-title">${event.title}</div>
                            <div class="event-mini-probability">${(event.probability * 100).toFixed(1)}%</div>
                        </div>
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
        toggleHourWatchSummary,
        toggleDailyWatchSummary,
        loadEvents,
        renderEvents
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
