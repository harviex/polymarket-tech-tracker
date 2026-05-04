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
        
        // Check if a specific market is requested
        const urlParams = new URLSearchParams(window.location.search);
        const marketId = urlParams.get('marketId');
        
        if (marketId && apiDetails && apiDetails.markets) {
            const market = apiDetails.markets.find(m => m.id === marketId);
            if (market) {
                event.selectedMarket = market;
            }
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
    
    // Check long_term_data.events (for Long-Term board)
    if (!event && data.long_term_data && data.long_term_data.events) {
        event = data.long_term_data.events[eventId];
        if (event) {
            // Add tag info from the event itself
            if (event.tags && event.tags.length > 0) {
                event.tag = event.tags[0];
                event.tag_display = event.tags[0].toUpperCase();
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
    
    // Get real-time probability from Polymarket API (main market)
    let probability = 0;
    const apiDetails = event.apiDetails;
    
    if (apiDetails && apiDetails.markets && apiDetails.markets.length > 0) {
        const mainMarket = apiDetails.markets[0];
        if (mainMarket.outcomePrices) {
            try {
                const prices = JSON.parse(mainMarket.outcomePrices);
                probability = parseFloat(prices[0]); // Yes probability
            } catch (e) {
                console.error('Error parsing outcomePrices:', e);
            }
        }
    }
    
    // Fallback to local data if API doesn't have it
    if (probability === 0) {
        probability = event.current_prob || event.probability || 0;
    }
    
    const historyHtml = event.history ? renderHistory(event.history) : '';
    
    // Extract fields from local data first, then API as fallback
    const description = event.description || apiDetails?.description || '';
    const resolutionSource = event.resolutionSource || apiDetails?.resolutionSource || '';
    const startDate = event.startDate || apiDetails?.startDate || '';
    const endDate = event.endDate || apiDetails?.endDate || '';
    const volume = event.volume || apiDetails?.volume || 0;
    const liquidity = event.liquidity || apiDetails?.liquidity || 0;
    const openInterest = apiDetails?.openInterest || 0; // Not saved locally
    const volume24hr = event.volume24hr || apiDetails?.volume24hr || 0;
    const volume1wk = event.volume1wk || apiDetails?.volume1wk || 0;
    const active = event.active || apiDetails?.active || false;
    const closed = event.closed || apiDetails?.closed || false;
    const commentCount = apiDetails?.commentCount || 0; // Not saved locally
    
    // Use markets from local data first, then API
    const markets = (event.markets && event.markets.length > 0) ? event.markets : (apiDetails?.markets || []);
    
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
                ${!closed && active ? `
                    <div class="meta-item" style="color: #10b981;">
                        <span class="meta-label">Status:</span>
                        <span>🟢 Active</span>
                    </div>
                ` : ''}
                ${closed ? `
                    <div class="meta-item" style="color: #ef4444;">
                        <span class="meta-label">Status:</span>
                        <span>🔴 Closed</span>
                    </div>
                ` : ''}
                ${startDate ? `
                    <div class="meta-item">
                        <span class="meta-label">Start Date:</span>
                        <span>${new Date(startDate).toLocaleString('zh-CN')}</span>
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
                        <span class="meta-label">Total Volume:</span>
                        <span>$${formatNumber(volume)}</span>
                    </div>
                ` : ''}
                ${volume24hr > 0 ? `
                    <div class="meta-item">
                        <span class="meta-label">24h Volume:</span>
                        <span>$${formatNumber(volume24hr)}</span>
                    </div>
                ` : ''}
                ${volume1wk > 0 ? `
                    <div class="meta-item">
                        <span class="meta-label">7d Volume:</span>
                        <span>$${formatNumber(volume1wk)}</span>
                    </div>
                ` : ''}
                ${liquidity > 0 ? `
                    <div class="meta-item">
                        <span class="meta-label">Liquidity:</span>
                        <span>$${formatNumber(liquidity)}</span>
                    </div>
                ` : ''}
                ${openInterest > 0 ? `
                    <div class="meta-item">
                        <span class="meta-label">Open Interest:</span>
                        <span>$${formatNumber(openInterest)}</span>
                    </div>
                ` : ''}
                ${commentCount > 0 ? `
                    <div class="meta-item">
                        <span class="meta-label">Comments:</span>
                        <span>💬 ${commentCount}</span>
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
            
            ${resolutionSource ? `
                <div class="event-resolution-source">
                    <h3>📋 Resolution Source</h3>
                    <div class="resolution-content">${resolutionSource}</div>
                </div>
            ` : ''}
            
            ${markets && markets.length > 0 ? renderSubMarkets(markets, probability) : ''}
            
            ${historyHtml ? `
                <div class="history-section">
                    <div class="history-title">📈 Probability History</div>
                    <div class="history-timeline">
                        ${historyHtml}
                    </div>
                </div>
            ` : ''}
            
            <div class="search-section">
                <h3>🔍 View on Polymarket</h3>
                <div class="search-buttons">
                    <a href="https://polymarket.com/event/${event.id}" 
                       target="_blank" rel="noopener" class="search-btn polymarket-btn">
                        View Main Event on Polymarket
                    </a>
                    ${markets && markets.length > 0 ? markets.map(market => `
                        <a href="https://polymarket.com/market/${market.id}" 
                           target="_blank" rel="noopener" class="search-btn polymarket-btn">
                            ${market.groupItemTitle || market.question.substring(0, 30)}...
                        </a>
                    `).join('') : ''}
                </div>
            </div>
        </div>
    `;
}

function renderSubMarkets(markets) {
    return `
        <div class="submarkets-section">
            <h3>📊 Sub-Markets (${markets.length})</h3>
            <div class="submarkets-grid">
                ${markets.map(market => {
                    const outcomePrices = market.outcomePrices ? JSON.parse(market.outcomePrices) : null;
                    const yesProb = outcomePrices && outcomePrices[0] ? (parseFloat(outcomePrices[0]) * 100).toFixed(1) : 'N/A';
                    const noProb = outcomePrices && outcomePrices[1] ? (parseFloat(outcomePrices[1]) * 100).toFixed(1) : 'N/A';
                    const volume = market.volume ? formatNumber(market.volume) : '0';
                    const endDate = market.endDate ? new Date(market.endDate).toLocaleString('zh-CN') : 'N/A';
                    
                    return `
                        <div class="submarket-card">
                            <div class="submarket-header">
                                <div class="submarket-question">${market.question}</div>
                                <a href="https://polymarket.com/market/${market.id}" target="_blank" rel="noopener" class="submarket-link">
                                    ↗️
                                </a>
                            </div>
                            <div class="submarket-outcomes">
                                <div class="submarket-outcome">
                                    <span class="outcome-label">Yes</span>
                                    <span class="outcome-value">${yesProb}%</span>
                                </div>
                                <div class="submarket-outcome">
                                    <span class="outcome-label">No</span>
                                    <span class="outcome-value">${noProb}%</span>
                                </div>
                            </div>
                            <div class="submarket-meta">
                                <div class="meta-item">
                                    <span class="meta-label">Volume:</span>
                                    <span>$${volume}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">End:</span>
                                    <span>${endDate}</span>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(2) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(2) + 'K';
    }
    return num.toFixed(2);
}

function formatDescription(desc) {
    if (!desc) return '';
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
