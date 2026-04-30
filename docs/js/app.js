// app.js - Optimized for Speed + Lazy Load
const App = (() => {
    let eventsData = { 
        new_entries: [], 
        exited_entries: [], 
        long_term_news: [],
        long_term_count: 0
    };
    let currentFilter = 'all';
    let expandedNews = null;
    
    async function init() {
        await loadEvents();
        renderEvents();
        setupSearch();
        setupFilters();
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
        renderLongTermNews();
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
            <div class="event-card" data-tags="${event.tags?.join(',') || ''}">
                <div class="event-header">
                    <div class="event-title">${event.title}</div>
                    <div class="event-probability">${(event.probability * 100).toFixed(1)}%</div>
                </div>
                <div class="event-meta">
                    <span class="label-new">NEW</span>
                    <span>↑ +${(event.change * 100).toFixed(1)}%</span>
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
            <div class="event-card">
                <div class="event-header">
                    <div class="event-title">${event.title}</div>
                    <div class="event-probability">${(event.probability * 100).toFixed(1)}%</div>
                </div>
                <div class="event-meta">
                    <span>↓ -${(event.change * 100).toFixed(1)}%</span>
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
    
    function renderLongTermNews() {
        const container = document.getElementById('long-term-groups');
        if (!container) return;
        
        const newsList = eventsData.long_term_news || [];
        
        if (newsList.length === 0) {
            container.innerHTML = '<p class="no-results">No long-term events</p>';
            return;
        }
        
        container.innerHTML = `
            <div class="news-list">
                ${newsList.map((news, idx) => `
                    <div class="news-list-item" data-index="${idx}">
                        <div class="news-list-header" onclick="App.toggleNews(${idx})">
                            <div class="news-list-title">
                                <span class="news-icon">📊</span>
                                ${news.title}
                                <span class="event-count">(${news.event_count} events)</span>
                            </div>
                            <div class="news-list-toggle">
                                ${expandedNews === idx ? '▼' : '▶'}
                            </div>
                        </div>
                        <div class="news-list-body" id="news-body-${idx}" style="display: ${expandedNews === idx ? 'block' : 'none'};">
                            <div class="news-summary">${news.summary}</div>
                            <div class="event-cards-container" id="event-cards-${idx}">
                                <!-- Lazy loaded event cards will appear here -->
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    function toggleNews(idx) {
        if (expandedNews === idx) {
            expandedNews = null;
        } else {
            expandedNews = idx;
            // Lazy load event cards
            loadEventCards(idx);
        }
        renderLongTermNews();
    }
    
    function loadEventCards(idx) {
        const news = eventsData.long_term_news[idx];
        if (!news || !news.events) return;
        
        const container = document.getElementById(`event-cards-${idx}`);
        if (!container || container.children.length > 0) return; // Already loaded
        
        container.innerHTML = news.events.map(event => `
            <div class="event-card" style="margin: 0.5rem 0; padding: 1rem;">
                <div class="event-header">
                    <div class="event-title" style="font-size: 0.875rem;">${event.title}</div>
                    <div class="event-probability" style="font-size: 1rem;">${(event.probability * 100).toFixed(1)}%</div>
                </div>
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
    
    function setupScrollAnimations() {
        // Simple scroll animation using Intersection Observer
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
        toggleNews,
        loadEvents,
        renderEvents
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
