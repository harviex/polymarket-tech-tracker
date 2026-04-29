# Tech Predictions Tracker

A modern web dashboard for tracking technology prediction markets from Polymarket with AI-powered news analysis.

## ✨ Features

- 📊 **Real-time Polymarket Data**: Automatically fetches active tech-related prediction markets
- 📰 **Smart News Aggregation**: Pulls relevant news from authoritative tech sources (TechCrunch, The Verge, WIRED, etc.)
- 🎨 **Dual Theme**: Light (default) and dark theme support
- 🌏 **Multi-language**: English, 中文, 日本語 support with auto-translation
- 📱 **Responsive Design**: Works on desktop and mobile
- 🔄 **Auto-update**: Hourly data refresh via GitHub Actions
- 📦 **Archive Page**: Historical view of completed predictions

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- API Keys (stored in GitHub Secrets):
  - Twitter API Bearer Token
  - OpenAI API Key (for translations)

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/harviex/polymarket-tech-tracker.git
cd polymarket-tech-tracker
```

2. Create credentials file:
```bash
mkdir -p ~/.hermes/credentials
cat > ~/.hermes/credentials/polymarket-tracker.env << EOF
TWITTER_API_TOKEN=your_twitter_token
OPENAI_API_KEY=your_openai_key
EOF
chmod 600 ~/.hermes/credentials/polymarket-tracker.env
```

3. Install dependencies:
```bash
pip install requests python-dotenv
```

4. Fetch initial data:
```bash
python scripts/fetch_polymarket.py
python scripts/fetch_twitter_news.py
```

5. Start local server:
```bash
python -m http.server 8000
```

6. Visit `http://localhost:8000`

## 📂 Project Structure

```
polymarket-tech-tracker/
├── index.html              # Main dashboard page
├── archive.html            # Archive of closed markets
├── style.css               # Styles (light/dark themes)
├── script.js               # Frontend logic (i18n, cards, news)
├── data/
│   ├── markets.json        # Active markets data (auto-generated)
│   └── archive.json        # Closed markets (manual)
├── scripts/
│   ├── fetch_polymarket.py # Fetch Polymarket API data
│   └── fetch_twitter_news.py # Fetch news from Twitter
└── .github/
    └── workflows/
        └── update-data.yml # GitHub Actions automation
```

## 🔧 Configuration

### GitHub Secrets

Add these secrets to your GitHub repository:

- `TWITTER_API_TOKEN`: Twitter API Bearer Token
- `OPENAI_API_KEY`: OpenAI API Key for translations

### Customization

- **Max Markets Display**: Edit `fetch_polymarket.py` line with `return tech_markets[:20]`
- **News Sources**: Edit `fetch_twitter_news.py` `TECH_ACCOUNTS` list
- **Update Frequency**: Edit `.github/workflows/update-data.yml` cron schedule

## 📊 Data Format

### markets.json
```json
{
  "last_updated": "2026-04-29 10:00:00 UTC",
  "total_markets": 20,
  "markets": [
    {
      "id": "market_123",
      "question": "Will Anthropic release Claude 5 before June 2026?",
      "volume": "$3,000,000",
      "endDate": "2026-06-30",
      "outcomes": [
        {"label": "Yes", "probability": 0.19},
        {"label": "No", "probability": 0.81}
      ],
      "news": [...],
      "prediction": {
        "direction": "No",
        "confidence": 0.75,
        "reasoning": "Recent news indicates delays"
      }
    }
  ]
}
```

## 🎯 Roadmap

- [ ] Add more prediction market sources (Metaculus, Manifold)
- [ ] Enhance AI prediction with GPT-4 analysis
- [ ] User accounts and favorite markets
- [ ] Email/Telegram notifications for market changes
- [ ] Expand to other categories (politics, sports, crypto)

## 📝 License

MIT License - feel free to fork and modify!

## 🤝 Contributing

Issues and PRs welcome! This project was built by [小爱玛 (Hermes Agent)](https://hermes-agent.nousresearch.com/).

---

**Live Demo**: https://harviex.github.io/polymarket-tech-tracker/
