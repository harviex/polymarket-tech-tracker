// Tech Predictions Tracker - Main JavaScript

let currentLang = 'en';
let marketsData = null;

// i18n translations
const translations = {
    en: {
        title: 'Tech Predictions Tracker',
        last_updated: 'Last updated',
        total_markets: 'Total markets',
        view_archive: 'View Archive',
        volume: 'Volume',
        ends: 'Ends',
        view_details: 'View Details',
        news: 'Related News',
        prediction: 'Our Prediction',
        confidence: 'Confidence',
        reasoning: 'Reasoning',
        no_news: 'No news available yet',
        read_more: 'Read more'
    },
    zh: {
        title: '科技预测追踪器',
        last_updated: '最后更新',
        total_markets: '市场总数',
        view_archive: '查看档案',
        volume: '交易量',
        ends: '截止日期',
        view_details: '查看详情',
        news: '相关新闻',
        prediction: '我们的预测',
        confidence: '信心指数',
        reasoning: '分析理由',
        no_news: '暂无新闻',
        read_more: '阅读更多'
    },
    ja: {
        title: 'テック予測トラッカー',
        last_updated: '最終更新',
        total_markets: '市場総数',
        view_archive: 'アーカイブを見る',
        volume: '取引量',
        ends: '終了日',
        view_details: '詳細を見る',
        news: '関連ニュース',
        prediction: '予測',
        confidence: '信頼度',
        reasoning: '分析理由',
        no_news: 'ニュースはまだありません',
        read_more: '続きを読む'
    }
};

// Theme toggle
function toggleTheme() {
    const body = document.body;
    const btn = document.getElementById('themeBtn');
    
    if (body.classList.contains('light-theme')) {
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        btn.textContent = '☀️';
        localStorage.setItem('theme', 'dark');
    } else {
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        btn.textContent: '🌙';
        localStorage.setItem('theme', 'light');
    }
}

// Initialize theme
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    const body = document.body;
    const btn = document.getElementById('themeBtn');
    
    if (savedTheme === 'dark') {
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        btn.textContent = '☀️';
    }
}

// Language switch
function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('lang', lang);
    
    // Update active button
    document.querySelectorAll('.lang-switch button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update UI text
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) {
            el.textContent = translations[lang][key];
        }
    });
    
    // Re-render markets with new language
    if (marketsData) {
        renderMarkets(marketsData);
    }
}

// Load markets data
async function loadMarkets() {
    try {
        const response = await fetch('data/markets.json?t=' + new Date().getTime());
        marketsData = await response.json();
        
        document.getElementById('lastUpdated').textContent = marketsData.last_updated || '-';
        document.getElementById('totalMarkets').textContent = marketsData.total_markets || 0;
        
        renderMarkets(marketsData);
    } catch (error) {
        console.error('Error loading markets:', error);
    }
}

// Render market cards
function renderMarkets(data) {
    const grid = document.getElementById('marketsGrid');
    grid.innerHTML = '';
    
    if (!data.markets || data.markets.length === 0) {
        grid.innerHTML = '<p style="text-align: center; grid-column: 1/-1;">No markets available</p>';
        return;
    }
    
    data.markets.forEach((market, index) => {
        const card = createMarketCard(market, index);
        grid.appendChild(card);
    });
}

// Create individual market card
function createMarketCard(market, index) {
    const card = document.createElement('div');
    card.className = 'market-card';
    card.onclick = () => toggleNews(index);
    
    let outcomesHTML = '';
    if (market.outcomes && market.outcomes.length > 0) {
        const totalProb = market.outcomes.reduce((sum, o) => sum + o.probability, 0);
        outcomesHTML = '<div class="outcome-bar">';
        market.outcomes.forEach(outcome => {
            const width = totalProb > 0 ? (outcome.probability / totalProb * 100) : 50;
            const className = outcome.label.toLowerCase().includes('yes') ? 'outcome-yes' : 'outcome-no';
            outcomesHTML += `<div class="outcome-segment ${className}" style="flex: ${width}">${outcome.label} (${(outcome.probability * 100).toFixed(1)}%)</div>`;
        });
        outcomesHTML += '</div>';
    }
    
    const t = translations[currentLang];
    card.innerHTML = `
        <div class="market-question">${market.question}</div>
        <div class="market-meta">
            <span>${t.volume}: ${market.volume}</span>
            <span>${t.ends}: ${market.endDate}</span>
        </div>
        ${outcomesHTML}
        <button class="expand-btn" onclick="event.stopPropagation(); toggleNews(${index})">${t.view_details} ↓</button>
        <div class="news-panel" id="news-${index}">
            <h4 style="margin: 15px 0 10px;">${t.news}</h4>
            ${renderNews(market.news, t)}
            <div class="prediction-box">
                <div class="prediction-label">${t.prediction}: ${market.prediction.direction}</div>
                <div style="font-size: 0.9rem; color: var(--text-secondary);">
                    ${t.confidence}: ${(market.prediction.confidence * 100).toFixed(0)}%<br>
                    ${t.reasoning}: ${market.prediction.reasoning}
                </div>
            </div>
        </div>
    `;
    
    return card;
}

// Render news items
function renderNews(news, t) {
    if (!news || news.length === 0) {
        return `<p style="color: var(--text-secondary);">${t.no_news}</p>`;
    }
    
    return news.map(item => `
        <div class="news-item">
            <div class="news-source">${item.source}</div>
            <div class="news-title">${item.title}</div>
            <div class="news-summary">${item.summary}</div>
            <a href="${item.url}" target="_blank" class="news-link">${t.read_more} →</a>
        </div>
    `).join('');
}

// Toggle news panel
function toggleNews(index) {
    const panel = document.getElementById(`news-${index}`);
    panel.classList.toggle('expanded');
    
    const btn = panel.previousElementSibling;
    if (panel.classList.contains('expanded')) {
        btn.textContent = translations[currentLang].view_details.replace('↓', '↑');
    } else {
        btn.textContent = translations[currentLang].view_details.replace('↑', '↓');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    
    // Set initial language
    const savedLang = localStorage.getItem('lang') || 'en';
    setLanguage(savedLang);
    
    // Load data
    loadMarkets();
    
    // Auto-refresh every 5 minutes
    setInterval(loadMarkets, 5 * 60 * 1000);
});
