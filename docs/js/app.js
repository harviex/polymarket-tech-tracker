// app.js - Daily Watch (Threshold Crossings) + Long-Term Board
const App = (() => {
    let dailyWatchData = { date: '', crossings: [], crossing_count: 0 };
    let longTermData = { events: {}, updated_at: null, event_count: 0 };

    async function init() {
        await Promise.all([loadDailyWatch(), loadLongTerm()]);
        renderAllBoards();
        setupSearch();
        setupScrollAnimations();
    }

    // ==================== 加载数据 ====================
    async function loadDailyWatch() {
        // 使用北京时间 (UTC+8)
        const now = new Date();
        const beijingTime = new Date(now.getTime() + 8 * 60 * 60 * 1000);
        const today = beijingTime.toISOString().split('T')[0];
        
        try {
            const response = await fetch(`data/daily_watch/${today}.json`);
            if (response.ok) {
                dailyWatchData = await response.json();
            }
        } catch (error) {
            console.error('Failed to load Daily Watch:', error);
        }
    }

    async function loadLongTerm() {
        try {
            const response = await fetch('data/long_term/long_term.json');
            if (response.ok) {
                longTermData = await response.json();
            }
        } catch (error) {
            console.error('Failed to load Long-Term data:', error);
        }
    }

    // ==================== 渲染所有板块 ====================
    function renderAllBoards() {
        renderDailyWatchBoard();
        renderLongTermBoard();
        updateMetaInfo();
    }

    // ==================== Daily Watch (阈值跨越) ====================
    function renderDailyWatchBoard() {
        const container = document.getElementById('daily-watch-crossings');
        if (!container) return;
        
        const crossings = dailyWatchData.crossings || [];
        
        if (crossings.length === 0) {
            container.innerHTML = '<p class="no-results">今天还没有阈值跨越事件</p>';
            return;
        }
        
        // 1a: 按event_id归并事件
        const mergedEvents = {};
        crossings.forEach(cross => {
            const id = cross.event_id;
            if (!mergedEvents[id]) {
                mergedEvents[id] = {
                    event_id: id,
                    title: cross.title,
                    slug: cross.slug,
                    history: [],  // 所有变动历史
                    latestCross: null  // 最新变动（用于颜色判断）
                };
            }
            
            // 添加历史记录
            mergedEvents[id].history.push({
                time: cross.time,
                prev_prob: cross.prev_prob,
                curr_prob: cross.curr_prob,
                threshold: cross.threshold,
                direction: cross.direction
            });
            
            // 更新最新变动（用于颜色）
            const newTime = cross.timestamp || `${cross.time}:00`;
            const oldTime = mergedEvents[id].latestCross ? 
                (mergedEvents[id].latestCross.timestamp || '00:00:00') : '00:00:00';
            
            if (newTime >= oldTime) {
                mergedEvents[id].latestCross = {
                    direction: cross.direction,
                    time: cross.time,
                    threshold: cross.threshold,
                    prev_prob: cross.prev_prob,
                    curr_prob: cross.curr_prob,
                    timestamp: cross.timestamp
                };
            }
        });
        
        // 按最新变动时间倒序
        const sorted = Object.values(mergedEvents).sort((a, b) => {
            const timeA = a.latestCross?.timestamp || '00:00:00';
            const timeB = b.latestCross?.timestamp || '00:00:00';
            return timeB.localeCompare(timeA);
        });
        
        container.innerHTML = `
            <div class="crossings-grid">
                ${sorted.map(event => renderMergedCrossing(event)).join('')}
            </div>
        `;
    }

    function renderMergedCrossing(event) {
        const latest = event.latestCross;
        if (!latest) return '';
        
        // 1b: 颜色逻辑 - 以最新变动为准
        const directionClass = latest.direction === 'up' ? 'cross-up' : 'cross-down';
        
        // 构建 URL
        const url = event.slug 
            ? `https://polymarket.com/event/${event.slug}`
            : `https://polymarket.com/event/${event.event_id}`;
        
        // 1d: 数值格式 - 时间 + 阈值符号 + 数值变化（同一行）
        // 格式：6:00 90% 70.5% → 74.0%
        const mainLine = `${latest.time} ${(latest.threshold * 100).toFixed(0)}% ${(latest.prev_prob * 100).toFixed(1)}% → ${(latest.curr_prob * 100).toFixed(1)}%`;
        
        // 1e: 多次变动历史 - 每个时间点换行显示
        const historyHtml = event.history.length > 1 ? `
            <div class="crossing-history">
                ${event.history.map(h => {
                    const arrow = h.direction === 'up' ? '↑' : '↓';
                    return `${h.time} ${(h.threshold * 100).toFixed(0)}% ${h.prev_prob * 100}%${arrow} → ${h.curr_prob * 100}%`;
                }).join('<br>')}
            </div>
        ` : '';
        
        return `
            <div class="crossing-card ${directionClass}" onclick="window.open('${url}', '_blank')" style="cursor: pointer;">
                <div class="crossing-title">${event.title}</div>
                <div class="crossing-meta">
                    ${mainLine}
                </div>
                ${historyHtml}
            </div>
        `;
    }

    // ==================== Long-Term Board ====================
    function renderLongTermBoard() {
        const container = document.getElementById('long-term-groups');
        if (!container) return;
        
        const events = Object.values(longTermData.events || {});
        
        if (events.length === 0) {
            container.innerHTML = '<p class="no-results">暂无长期高概率事件</p>';
            return;
        }
        
        // 按标签分组
        const tagGroups = {};
        events.forEach(event => {
            const tags = event.tags || [];
            let mainTag = tags[0] || 'other';
            
            // 2: 如果第一个标签是 "tech"，忽略它，用第二个标签
            if (mainTag.toLowerCase() === 'tech' && tags.length > 1) {
                mainTag = tags[1];
            }
            
            if (!tagGroups[mainTag]) {
                tagGroups[mainTag] = [];
            }
            tagGroups[mainTag].push(event);
        });
        
        // 渲染每个标签组
        container.innerHTML = Object.entries(tagGroups).map(([tag, events]) => `
            <div class="tag-group">
                <h3 class="tag-title">${tag.toUpperCase()}</h3>
                <div class="events-grid">
                    ${events.map(event => renderLongTermEvent(event)).join('')}
                </div>
            </div>
        `).join('');
    }

    function renderLongTermEvent(event) {
        // 格式化volume
        const formatVolume = (vol) => {
            if (vol >= 1000000) return (vol / 1000000).toFixed(1) + 'M';
            if (vol >= 1000) return (vol / 1000).toFixed(1) + 'K';
            return vol.toString();
        };
        
        // 2a & 2b: 结论选取 - 使用option_text，不显示重复内容
        const conclusion = event.option_text || 'Yes/No';
        
        // 使用验证后的URL
        const url = event.url || `https://polymarket.com/event/${event.id}`;
        
        return `
            <div class="event-mini-card" onclick="window.open('${url}', '_blank')" style="cursor: pointer;">
                <div class="event-mini-header">
                    <div class="event-mini-title">${event.title}</div>
                    <div class="event-mini-info">
                        ${(event.current_prob * 100).toFixed(1)}% 
                        | ${conclusion}
                        | Vol: ${formatVolume(event.volume || 0)}
                    </div>
                </div>
            </div>
        `;
    }

    // ==================== Meta Info ====================
    function updateMetaInfo() {
        const dailyCount = document.getElementById('daily-watch-count');
        if (dailyCount) {
            dailyCount.textContent = dailyWatchData.crossing_count || 0;
        }
        
        const longTermCount = document.getElementById('long-term-count');
        if (longTermCount) {
            longTermCount.textContent = longTermData.event_count || Object.keys(longTermData.events || {}).length;
        }
    }

    // ==================== Search ====================
    function setupSearch() {
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;
        
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            filterEvents(query);
        });
    }

    function filterEvents(query) {
        // 过滤 Daily Watch crossings
        const crossingItems = document.querySelectorAll('.crossing-card');
        crossingItems.forEach(item => {
            const title = item.querySelector('.crossing-title')?.textContent.toLowerCase() || '';
            item.style.display = title.includes(query) ? '' : 'none';
        });
        
        // 过滤 Long-Term events
        const eventCards = document.querySelectorAll('.event-mini-card');
        eventCards.forEach(card => {
            const title = card.querySelector('.event-mini-title')?.textContent.toLowerCase() || '';
            card.style.display = title.includes(query) ? '' : 'none';
        });
    }

    // ==================== Scroll Animations ====================
    function setupScrollAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.1 });
        
        document.querySelectorAll('.glass-card, .event-mini-card, .crossing-card').forEach(el => {
            observer.observe(el);
        });
    }

    return { init, renderAllBoards };
})();

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
