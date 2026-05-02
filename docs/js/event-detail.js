// event-detail.js - Event Detail Page Logic

const SEARXNG_URL = 'http://192.168.123.101:8000'; // Your local SearXNG instance

async function init() {
    const eventId = getEventIdFromURL();
    if (!eventId) {
        showError('No event ID provided');
        return;
    }

    await loadEventDetail(eventId);
}

function getEventIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

async function loadEventDetail(eventId) {
    try {
        // Load events data
        const response = await fetch('data/technology/events.json');
        if (!response.ok) throw new Error('Failed to load events data');
        
        const data = await response.json();
        
        // Find event in daily_watch_summaries
        let event = null;
        if (data.daily_watch_summaries) {
            for (const summary of data.daily_watch_summaries) {
                if (summary.events) {
                    event = summary.events.find(e => e.id === eventId);
                    if (event) {
                        event.tag = summary.tag;
                        event.tag_display = summary.tag_display;
                        break;
                    }
                }
            }
        }
        
        // Also check new_entries and exited_entries
        if (!event) {
            event = data.new_entries?.find(e => e.id === eventId);
        }
        if (!event) {
            event = data.exited_entries?.find(e => e.id === eventId);
        }
        
        // Also check long_term_summaries
        if (!event && data.long_term_summaries) {
            for (const summary of data.long_term_summaries) {
                if (summary.events) {
                    event = summary.events.find(e => e.id === eventId);
                    if (event) break;
                }
            }
        }
        
        if (!event) {
            showError('Event not found');
            return;
        }
        
        renderEventDetail(event);
        loadRelatedNews(event.title, event.tags);
        
    } catch (error) {
        console.error('Error loading event:', error);
        showError('Failed to load event details');
    }
}

function renderEventDetail(event) {
    const container = document.getElementById('event-content');
    if (!container) return;
    
    const probability = event.current_prob || event.probability || 0;
    const historyHtml = event.history ? renderHistory(event.history) : '';
    
    container.innerHTML = `
        <div class="event-detail-card">
            <div class="event-detail-header">
                <div class="event-detail-title">${event.title}</div>
                <div class="event-detail-probability">${(probability * 100).toFixed(1)}%</div>
            </div>
            
            <div class="event-meta">
                ${event.id ? `
                    <div class="meta-item">
                        <span class="meta-label">ID:</span>
                        <span>${event.id}</span>
                    </div>
                ` : ''}
                ${event.tag ? `
                    <div class="meta-item">
                        <span class="meta-label">Category:</span>
                        <span>${event.tag_display || event.tag.toUpperCase()}</span>
                    </div>
                ` : ''}
                ${event.first_seen ? `
                    <div class="meta-item">
                        <span class="meta-label">First Seen:</span>
                        <span>${new Date(event.first_seen).toLocaleString('zh-CN')}</span>
                    </div>
                ` : ''}
            </div>
            
            ${event.tags ? `
                <div class="event-tags">
                    ${event.tags.map(tag => `<span class="event-tag">${tag}</span>`).join('')}
                </div>
            ` : ''}
            
            ${historyHtml ? `
                <div class="history-section">
                    <div class="history-title">📈 Probability History</div>
                    <div class="history-timeline">
                        ${historyHtml}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

function renderHistory(history) {
    return history.map(h => {
        const directionClass = h.direction === 'up' ? 'up' : 'down';
        const arrow = h.direction === 'up' ? '↑' : '↓';
        const thresholdText = h.threshold ? 
            ` (${h.direction === 'up' ? '越过' : '低过'} ${(h.threshold * 100).toFixed(0)}%线)` : '';
        
        return `
            <div class="history-item">
                <div class="history-time">${h.time}</div>
                <div class="history-prob">${(h.prob * 100).toFixed(1)}% ${arrow}</div>
                <div class="history-direction ${directionClass}">${thresholdText}</div>
            </div>
        `;
    }).join('');
}

async function loadRelatedNews(title, tags) {
    const container = document.getElementById('news-content');
    if (!container) return;
    
    try {
        // Construct search query from title and tags
        const query = `${title} ${tags ? tags.slice(0, 3).join(' ') : ''}`;
        
        // Search using SearXNG
        const searchUrl = `${SEARXNG_URL}/search?q=${encodeURIComponent(query)}&format=json&categories=news&language=zh`;
        
        const response = await fetch(searchUrl);
        if (!response.ok) throw new Error('Search failed');
        
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            // Get the first news item
            const news = data.results[0];
            renderNews(news);
        } else {
            container.innerHTML = '<p class="no-results">No related news found</p>';
        }
        
    } catch (error) {
        console.error('Error searching news:', error);
        container.innerHTML = '<p class="no-results">Failed to load news. Make sure SearXNG is running at ' + SEARXNG_URL + '</p>';
    }
}

function renderNews(news) {
    const container = document.getElementById('news-content');
    if (!container) return;
    
    container.innerHTML = `
        <div class="news-card">
            <div class="news-title">
                <a href="${news.url}" target="_blank" rel="noopener">${news.title}</a>
            </div>
            <div class="news-meta">
                ${news.publishedDate ? `<span>📅 ${new Date(news.publishedDate).toLocaleString('zh-CN')}</span>` : ''}
                ${news.engine ? `<span>🔍 ${news.engine}</span>` : ''}
            </div>
            ${news.content ? `
                <div class="news-content">${news.content.substring(0, 300)}${news.content.length > 300 ? '...' : ''}</div>
            ` : ''}
        </div>
    `;
}

function showError(message) {
    const container = document.getElementById('event-content');
    if (container) {
        container.innerHTML = `
            <div class="error-message" style="text-align: center; padding: 2rem; color: #ef4444;">
                <p>❌ ${message}</p>
            </div>
        `;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
