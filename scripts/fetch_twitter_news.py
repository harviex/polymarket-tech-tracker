#!/usr/bin/env python3
"""
Fetch tech news from RSS feeds for Polymarket markets
Uses RSS feeds from authoritative tech news sources (no API key needed)
"""
import requests
import json
import os
import time
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET
from dotenv import load_dotenv

# Load OpenAI API key for translations
env_paths = [
    '/home/c1/.hermes/credentials/polymarket-tracker.env',
    '/home/c1/.hermes/.env'
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded credentials from {env_path}")
        break

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# RSS feeds from authoritative tech news sources
RSS_FEEDS = [
    ('TechCrunch', 'https://techcrunch.com/feed/'),
    ('The Verge', 'https://www.theverge.com/rss/index.xml'),
    ('WIRED', 'https://www.wired.com/feed/rss'),
    ('Ars Technica', 'https://feeds.arstechnica.com/arstechnica/technology-lab'),
    ('CNET', 'https://www.cnet.com/rss/news/'),
    ('Engadget', 'https://www.engadget.com/rss.xml')
]

def fetch_rss(url, source_name):
    """Fetch and parse RSS feed"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"{source_name} RSS error: {response.status_code}")
            return []
        
        root = ET.fromstring(response.content)
        items = []
        
        # Handle both RSS and Atom formats
        if root.tag.endswith('rss'):
            for item in root.findall('.//item')[:10]:  # Latest 10 items
                title = item.findtext('title', '')
                description = item.findtext('description', '')
                link = item.findtext('link', '')
                pub_date = item.findtext('pubDate', '')[:16]
                
                items.append({
                    'title': title,
                    'summary': description[:200] + '...' if len(description) > 200 else description,
                    'url': link,
                    'published_at': pub_date,
                    'source': source_name
                })
        elif root.tag.endswith('feed'):  # Atom format
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry')[:10]:
                title = entry.findtext('{http://www.w3.org/2005/Atom}title', '')
                summary = entry.findtext('{http://www.w3.org/2005/Atom}summary', '') or \
                         entry.findtext('{http://www.w3.org/2005/Atom}content', '')
                link = entry.find('{http://www.w3.org/2005/Atom}link')
                link_href = link.get('href') if link is not None else ''
                updated = entry.findtext('{http://www.w3.org/2005/Atom}updated', '')[:10]
                
                items.append({
                    'title': title,
                    'summary': summary[:200] + '...' if len(summary) > 200 else summary,
                    'url': link_href,
                    'published_at': updated,
                    'source': source_name
                })
        
        print(f"Fetched {len(items)} items from {source_name}")
        return items
        
    except Exception as e:
        print(f"Error fetching {source_name} RSS: {e}")
        return []

def search_news(keywords, max_results=5):
    """Search news from RSS feeds matching keywords"""
    all_news = []
    
    for source_name, url in RSS_FEEDS:
        items = fetch_rss(url, source_name)
        
        for item in items:
            # Check if any keyword matches title or summary
            text = (item['title'] + ' ' + item['summary']).lower()
            if any(kw.lower() in text for kw in keywords):
                all_news.append(item)
                
        if len(all_news) >= max_results:
            break
            
    return all_news[:max_results]

def get_news_for_market(market_question):
    """Get relevant news for a specific market"""
    keywords = extract_keywords(market_question)
    if not keywords:
        return []
    
    print(f"  Keywords: {keywords[:3]}")
    news = search_news(keywords[:3], max_results=5)
    return news

def extract_keywords(question):
    """Extract relevant keywords from market question"""
    import re
    words = re.findall(r'\b\w+\b', question.lower())
    stopwords = ['will', 'the', 'a', 'an', 'before', 'after', 'by', 'in', 'on', 'at', 'to', 'for', 
                 'of', 'is', 'be', 'are', 'this', 'that', 'with', 'hit', 'reach', 'dip']
    keywords = [w for w in words if w not in stopwords and len(w) > 3]
    return list(set(keywords[:5]))  # Remove duplicates

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
    except Exception as e:
        print(f"Translation error: {e}")
    
    return text

def main():
    print("Fetching news for markets from RSS feeds...")
    
    markets_path = '/home/c1/polymarket-tech-tracker/data/markets.json'
    if not os.path.exists(markets_path):
        print("Markets file not found. Run fetch_polymarket.py first.")
        return
    
    with open(markets_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Fetch news for each market (limit to avoid long runtime)
    for i, market in enumerate(data['markets'][:10]):  # First 10 markets
        print(f"\n[{i+1}/10] Fetching news for: {market['question'][:50]}...")
        news = get_news_for_market(market['question'])
        market['news'] = news
        time.sleep(2)  # Rate limiting between sources
    
    # Save updated data
    with open(markets_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\nUpdated {min(10, len(data['markets']))} markets with news from RSS feeds")

if __name__ == "__main__":
    main()
