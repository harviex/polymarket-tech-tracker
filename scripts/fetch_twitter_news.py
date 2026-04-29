#!/usr/bin/env python3
"""
Fetch tech news from Twitter/X for Polymarket markets
"""
import requests
import json
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load credentials from multiple possible locations
env_paths = [
    '/root/.hermes/credentials/polymarket-tracker.env',
    '/home/c1/.hermes/credentials/polymarket-tracker.env',
    os.path.expanduser('~/.hermes/credentials/polymarket-tracker.env')
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded credentials from {env_path}")
        break

TWITTER_API_TOKEN = os.getenv('TWITTER_API_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Authoritative tech news accounts
TECH_ACCOUNTS = [
    'TechCrunch',
    'TheVerge',
    'WIRED',
    'arstechnica',
    'verge',
    'techreview',
    'CNET',
    'engadget',
    'mashable'
]

def search_tweets(query, max_results=10):
    """Search tweets using Twitter API v2"""
    if not TWITTER_API_TOKEN:
        print("Twitter API token not found")
        return []
    
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {
        "Authorization": f"Bearer {TWITTER_API_TOKEN}"
    }
    params = {
        "query": f"{query} (from:TechCrunch OR from:TheVerge OR from:WIRED) -is:retweet",
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics,author_id",
        "expansions": "author_id",
        "user.fields": "username"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            print(f"Twitter API error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error searching tweets: {e}")
        return []

def get_news_for_market(market_question):
    """Get relevant news for a specific market"""
    # Extract keywords from question
    keywords = extract_keywords(market_question)
    query = ' OR '.join(keywords[:3])  # Use top 3 keywords
    
    tweets = search_tweets(query, max_results=5)
    
    news_items = []
    for tweet in tweets:
        news_items.append({
            "source": "Twitter",
            "title": tweet.get('text', '')[:100] + '...',
            "summary": tweet.get('text', ''),
            "url": f"https://twitter.com/i/web/status/{tweet['id']}",
            "published_at": tweet.get('created_at', '')[:10],
            "sentiment": "neutral"
        })
    
    return news_items

def extract_keywords(question):
    """Extract relevant keywords from market question"""
    words = question.lower().replace('?', '').replace(',', '').split()
    # Filter out common words
    stopwords = ['will', 'the', 'a', 'an', 'before', 'after', 'by', 'in', 'on', 'at', 'to', 'for']
    keywords = [w for w in words if w not in stopwords and len(w) > 3]
    return keywords[:5]

def translate_text(text, target_lang):
    """Translate text using OpenAI API"""
    if not OPENAI_API_KEY or target_lang == 'en':
        return text
    
    lang_map = {'zh': 'Chinese', 'ja': 'Japanese'}
    if target_lang not in lang_map:
        return text
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": f"Translate the following to {lang_map[target_lang]}. Only return the translation."},
                {"role": "user", "content": text}
            ],
            "max_tokens": 200
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", 
                               json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except:
        pass
    
    return text

def main():
    print("Fetching news for markets...")
    
    # Load markets
    markets_path = '/home/c1/polymarket-tech-tracker/data/markets.json'
    if not os.path.exists(markets_path):
        print("Markets file not found. Run fetch_polymarket.py first.")
        return
    
    with open(markets_path, 'r') as f:
        data = json.load(f)
    
    # Fetch news for each market (limit to avoid API rate limits)
    for i, market in enumerate(data['markets'][:10]):  # First 10 markets
        print(f"Fetching news for: {market['question'][:50]}...")
        news = get_news_for_market(market['question'])
        market['news'] = news
        time.sleep(2)  # Rate limiting
    
    # Save updated data
    with open(markets_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Updated {min(10, len(data['markets']))} markets with news")

if __name__ == "__main__":
    main()
