// event-detail.js - Event Detail Page Logic

const POLYMARKET_API = 'https://gamma-api.polymarket.com/events';

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
        // Load local events data
        const response = await fetch('data/technology/events.json');
        if (!response.ok) throw new Error('Failed to load events data');
        
        const data = await response.json();
        
        // Find event in all summaries
        let event = findEventInData(data, eventId);
        
        if (!event) {
            showError('Event not found');
            return;
        }
        
        // Load additional details from Polymarket API
        const apiDetails = await loadPolymarketAPIDetail(eventId);
        if (apiDetails) {
            event.apiDetails = apiDetails;
        }
        
        renderEventDetail(event);
        
    } catch (error) {
        console.error('Error loading event:', error);
        showError('Failed to load event details');
    }
}

function findEventInData(data, eventId) {
    let event = null;
    
    // Check daily_watch_summaries
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
    
    // Check new_entries
    if (!event && data.new_entries) {
        event = data.new_entries.find(e => e.id === eventId);
    }
    
    // Check exited_entries
    if (!event && data.exited_entries) {
        event = data.exited_entries.find(e => e.id === eventId);
    }
    
    // Check long_term_summaries
    if (!event && data.long_term_summaries) {
        for (const summary of data.long_term_summaries) {
            if (summary.events) {
                event = summary.events.find(e => e.id === eventId);
                if (event) break;
            }
        }
    }
    
    return event;
}

async function loadPolymarketAPIDetail(eventId) {
    try {
        const url = `${POLYMARKET_API}?ids=${eventId}`;
        const response = await fetch(url);
        if (!response.ok) return null;
        
        const events = await response.json();
        if (events && events.length > 0) {
            return events[0];
        }
        return null;
    } catch (error) {
        console.error('Error loading Polymarket API:', error);
        return null;
    }
}

function renderEventDetail(event) {
    const container = document.getElementById('event-content');
    if (!container) return;
    
    const probability = event.current_prob || event.probability || 0;
    const historyHtml = event.history ? renderHistory(event.history) : '';
    const apiDetails = event.apiDetails;
    
    // Extract API fields
    const description = apiDetails?.description || '';
    const endDate = apiDetails?.endDate || '';
    const volume = apiDetails?.volume || 0;
    const liquidity = apiDetails?.liquidity || 0;
    const outcomePrices = apiDetails?.outcomePrices ? JSON.parse(apiDetails.outcomePrices) : null;
    
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
                ${endDate ? `
                    <div class="meta-item">
                        <span class="meta-label">End Date:</span>
                        <span>${new Date(endDate).toLocaleString('zh-CN')}</span>
                    </div>
                ` : ''}
                ${volume > 0 ? `
                    <div class="meta-item">
                        <span class="meta-label">Volume:</span>
                        <span>$${volume.toLocaleString()}</span>
                    </div>
                ` : ''}
                ${liquidity > 0 ? `
                    <div class="meta-item">
                        <span class="meta-label">Liquidity:</span>
                        <span>$${liquidity.toLocaleString()}</span>
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
            
            ${description ? `
                <div class="event-description">
                    <h3>📝 Description</h3>
                    <div class="description-content">${formatDescription(description)}</div>
                </div>
            ` : ''}
            
            ${outcomePrices && outcomePrices.length >= 2 ? `
                <div class="outcome-prices">
                    <h3>💰 Outcome Prices</h3>
                    <div class="outcome-grid">
                        <div class="outcome-item">
                            <div class="outcome-label">Yes</div>
                            <div class="outcome-value">${(parseFloat(outcomePrices[0]) * 100).toFixed(1)}%</div>
                        </div>
                        <div class="outcome-item">
                            <div class="outcome-label">No</div>
                            <div class="outcome-value">${(parseFloat(outcomePrices[1]) * 100).toFixed(1)}%</div>
                        </div>
                    </div>
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
            
            <div class="search-section">
                <h3>🔍 Search Related News</h3>
                <div class="search-buttons">
                    <a href="https://duckduckgo.com/?q=${encodeURIComponent(event.title)}&t=h_&ia=news" 
                       target="_blank" rel="noopener" class="search-btn ddg-btn">
                        DuckDuckGo News
                    </a>
                    <a href="https://www.google.com/search?q=${encodeURIComponent(event.title)}&tbm=nws" 
                       target="_blank" rel="noopener" class="search-btn google-btn">
                        Google News
                    </a>
                    <a href="https://polymarket.com/event/${event.id}" 
                       target="_blank" rel="noopener" class="search-btn polymarket-btn">
                        View on Polymarket
                    </a>
                </div>
            </div>
        </div>
    `;
}

function formatDescription(desc) {
    if (!desc) return '';
    // Convert newlines to <br> and preserve formatting
    return desc
        .replace(/\\n/g, '<br>')
        .replace(/\\r/g, '')
        .trim();
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
