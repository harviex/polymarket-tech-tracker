#!/usr/bin/env python3
"""
News Fetcher: SearXNG only approach
Fetches news for new/exited events and caches them
"""
import json
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
NEWS_CACHE_DIR = BASE_DIR / "docs" / "data" / "news_cache"
TECH_DIR = BASE_DIR / "docs" / "data" / "technology"
SEARXNG_URL = "http://192.168.123.101:8000"

def search_searxng(query, max_results=3):
    """Search using local SearXNG instance"""
    import urllib.request
    import urllib.parse
    
    try:
        # SearXNG JSON format
        params = urllib.parse.urlencode({
            'q': query,
            'format': 'json',
            'categories': 'general',
            'language': 'en',
            'pageno': 1
        })
        
        url = f"{SEARXNG_URL}/search?{params}"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'SciencePredictionTracker/1.0')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            results = data.get('results', [])[:max_results]
            
            if results:
                return {
                    'title': results[0].get('title', ''),
                    'url': results[0].get('url', ''),
                    'content': results[0].get('content', '')[:300],
                    'source': 'SearXNG',
                    'timestamp': datetime.now().isoformat()
                }
    except Exception as e:
        print(f"   SearXNG search failed: {e}")
    
    return None

def fetch_news_for_event(event, event_type='new'):
    """Fetch news for a single event"""
    print(f"   Fetching news for: {event['title'][:50]}...")
    
    # Use SearXNG
    news = search_searxng(event['title'])
    
    if news:
        news['event_id'] = event['id']
        news['event_type'] = event_type
        print(f"   ✅ Found: {news['title'][:50]}...")
        return news
    else:
        print(f"   ❌ No news found")
        return None

def load_events():
    """Load current events data"""
    events_file = TECH_DIR / "events.json"
    with open(events_file) as f:
        return json.load(f)

def save_news_cache(news_items):
    """Save news to cache"""
    NEWS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save as one file per day
    date_str = datetime.now().strftime('%Y-%m-%d')
    cache_file = NEWS_CACHE_DIR / f"{date_str}.json"
    
    # Load existing cache
    if cache_file.exists():
        with open(cache_file) as f:
            cache = json.load(f)
    else:
        cache = []
    
    # Add new items
    cache.extend(news_items)
    
    # Remove duplicates (by event_id)
    seen = set()
    unique_cache = []
    for item in cache:
        if item['event_id'] not in seen:
            seen.add(item['event_id'])
            unique_cache.append(item)
    
    # Save
    with open(cache_file, 'w') as f:
        json.dump(unique_cache, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(unique_cache)} news items to {cache_file}")

def update_events_with_news(events_data, news_items):
    """Update events.json with associated news"""
    news_by_event = {item['event_id']: item for item in news_items}
    
    # Add news to new entries
    for event in events_data.get('new_entries', []):
        if event['id'] in news_by_event:
            event['news'] = news_by_event[event['id']]
    
    # Add news to exited entries
    for event in events_data.get('exited_entries', []):
        if event['id'] in news_by_event:
            event['news'] = news_by_event[event['id']]
    
    return events_data

def main():
    print("📰 Starting news_fetcher.py...")
    
    # Load events
    print("📡 Loading events data...")
    events_data = load_events()
    
    new_entries = events_data.get('new_entries', [])
    exited_entries = events_data.get('exited_entries', [])
    
    print(f"   New entries: {len(new_entries)}")
    print(f"   Exited entries: {len(exited_entries)}")
    
    # Fetch news for new entries
    news_items = []
    
    if new_entries:
        print("\n🆕 Fetching news for new entries...")
        for event in new_entries:
            news = fetch_news_for_event(event, 'new')
            if news:
                news_items.append(news)
    
    # Fetch news for exited entries
    if exited_entries:
        print("\n🚪 Fetching news for exited entries...")
        for event in exited_entries:
            news = fetch_news_for_event(event, 'exited')
            if news:
                news_items.append(news)
    
    # Save to cache
    if news_items:
        print(f"\n💾 Saving {len(news_items)} news items...")
        save_news_cache(news_items)
        
        # Update events.json with news
        print("🔄 Updating events.json with news...")
        updated_events = update_events_with_news(events_data, news_items)
        
        with open(TECH_DIR / "events.json", 'w') as f:
            json.dump(updated_events, f, indent=2, ensure_ascii=False)
        
        print("✅ events.json updated with news!")
    else:
        print("⚠️  No news items fetched")
    
    print("\n🎉 Done!")

if __name__ == '__main__':
    main()
