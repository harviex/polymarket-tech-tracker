// app.js - Three-Board System: 1小时榜 + 每日榜 + 长期榜
const App = (() => {
    let eventsData = {
        hour_watch_summaries: [],
        daily_watch_summaries: [],
        long_term_data: { events: {}, updated_at: null }
    };
    
    let expandedHourWatchIdx = null;
    let expandedDailyWatchIdx = null;
    let expandedLongTermIdx = null;
    
    async function init() {
        await loadEvents();
        renderAllBoards();
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
    
    function renderAllBoards() {
        renderHourWatchBoard();
        renderDailyWatchBoard();
        renderLongTermBoard();
        updateMetaInfo();
    }
    
    // ==================== 1小时榜 ====================
    function renderHourWatchBoard() {
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
                        
                        <div class="summary-events" id="hour-watch-events-${idx}" style="display: ${expandedHourWatchIdx === idx ? 'block' : 'none'};">
                            ${expandedHourWatchIdx === idx && summary.events ? renderHourWatchEventsList(summary.events) : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
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
    
    function toggleHourWatchSummary(idx) {
        expandedHourWatchIdx = expandedHourWatchIdx === idx ? null : idx;
        renderHourWatchBoard();
    }
    
    // ==================== 每日榜 ====================
    function renderDailyWatchBoard() {
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
                        
                        <div class="summary-events" id="daily-watch-events-${idx}" style="display: ${expandedDailyWatchIdx === idx ? 'block' : 'none'};">
                            ${expandedDailyWatchIdx === idx && summary.events ? renderDailyWatchEventsList(summary.events) : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
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
    
    function toggleDailyWatchSummary(idx) {
        expandedDailyWatchIdx = expandedDailyWatchIdx === idx ? null : idx;
        renderDailyWatchBoard();
    }
    
    // ==================== 长期榜 ====================
    function renderLongTermBoard() {
        const container = document.getElementById('long-term-groups');
        if (!container) return;
        
        const longTermData = eventsData.long_term_data || { events: {}, updated_at: null };
        const events = Object.values(longTermData.events || {});
        
        // 按标签分组
        const tagGroups = {};
        events.forEach(event => {
            const tags = event.tags || [];
            const mainTag = tags[0] || 'other';
            if (!tagGroups[mainTag]) {
                tagGroups[mainTag] = [];
            }
            tagGroups[mainTag].push(event);
        });
        
        const summaries = Object.entries(tagGroups).map(([tag, tagEvents]) => ({
            tag,
            tag_display: tag.toUpperCase(),
            event_count: tagEvents.length,
            avg_probability: tagEvents.reduce((sum, e) => sum + (e.current_prob || 0), 0) / tagEvents.length,
            max_probability: Math.max(...tagEvents.map(e => e.current_prob || 0)),
            min_probability: Math.min(...tagEvents.map(e => e.current_prob || 1)),
            events: tagEvents
        }));
        
        if (summaries.length === 0) {
            container.innerHTML = '<p class="no-results">No long-term events</p>';
            // 更新计数
            const longTermCount = document.getElementById('long-term-count');
            if (longTermCount) longTermCount.textContent = '0';
            return;
        }
        
        container.innerHTML = `
            <div class="summary-cards-grid">
                ${summaries.map((summary, idx) => `
                    <div class="summary-card glass-card">
                        <div class="summary-header">
                            <div class="summary-tag">${summary.tag_display || summary.tag.toUpperCase()}</div>
                        </div>
                        
                        <div class="summary-events">
                            ${renderLongTermEventsList(summary.events)}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        // 更新计数
        const longTermCount = document.getElementById('long-term-count');
        if (longTermCount) longTermCount.textContent = events.length;
    }
    
    function renderLongTermEventsList(events) {
        if (!events || events.length === 0) return '';
        
        // 格式化volume
        const formatVolume = (vol) => {
            if (vol >= 1000000) return (vol / 1000000).toFixed(1) + 'M';
            if (vol >= 1000) return (vol / 1000).toFixed(1) + 'K';
            return vol.toString();
        };
        
        return `
            <div class="events-divider"></div>
            <div class="events-grid">
                ${events.map(event => `
                    <div class="event-mini-card" onclick="window.location.href='event-detail.html?id=${event.id}'" style="cursor: pointer;">
                        <div class="event-mini-header">
                            <div class="event-mini-title">${event.title}</div>
                            <div class="event-mini-probability">${(event.current_prob * 100).toFixed(1)}% | Vol: ${formatVolume(event.volume || 0)}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    function toggleLongTermSummary(idx) {
        expandedLongTermIdx = expandedLongTermIdx === idx ? null : idx;
        renderLongTermBoard();
    }
    
    // ==================== 工具函数 ====================
    function formatHistory(history) {
        if (!history || history.length === 0) return '';
        return history.map(h => {
            const arrow = h.direction === 'up' ? '↑' : '↓';
            const thresholdText = h.threshold ? ` (${h.direction === 'up' ? 'crossed up' : 'dropped below'} ${(h.threshold * 100).toFixed(0)}%)` : '';
            return `${h.time}: ${(h.prob * 100).toFixed(1)}% ${arrow}${thresholdText}`;
        }).join('<br>');
    }
    
    function updateMetaInfo() {
        // 更新1小时榜元信息
        const hourWatchMeta = document.getElementById('hour-watch-meta');
        if (hourWatchMeta) {
            const summaries = eventsData.hour_watch_summaries || [];
            const totalEvents = summaries.reduce((sum, s) => sum + s.event_count, 0);
            hourWatchMeta.style.display = 'block';
            hourWatchMeta.innerHTML = `<p>Total ${totalEvents} events crossed thresholds in the last hour</p>`;
        }
        
        // 更新每日榜元信息
        const dailyWatchMeta = document.getElementById('daily-watch-meta');
        if (dailyWatchMeta) {
            const summaries = eventsData.daily_watch_summaries || [];
            const totalEvents = summaries.reduce((sum, s) => sum + s.event_count, 0);
            dailyWatchMeta.style.display = 'block';
            dailyWatchMeta.innerHTML = `<p>Total ${totalEvents} events tracked today</p>`;
        }
    }
    
    function setupSearch() {
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;
        
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.event-mini-card').forEach(card => {
                const title = card.querySelector('.event-mini-title')?.textContent.toLowerCase() || '';
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
        toggleHourWatchSummary,
        toggleDailyWatchSummary,
        toggleLongTermSummary,
        loadEvents,
        renderAllBoards
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
