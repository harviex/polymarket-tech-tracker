#!/usr/bin/env python3
"""
Fetch Polymarket events - Optimized Logic
1-hour comparison + 3% change threshold
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "docs" / "data"
HISTORY_DIR = DATA_DIR / "history"
TECH_DIR = DATA_DIR / "technology"
CONFIG_FILE = DATA_DIR / "config.json"

GAMMA_API = "https://gamma-api.polymarket.com/events"
HIGH_THRESHOLD = 0.70
CHANGE_THRESHOLD = 0.03  # 3% change

def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

def fetch_events(limit=1000):
    """Fetch active events from Polymarket"""
    import urllib.request
    
    url = f"{GAMMA_API}?active=true&closed=false&limit={limit}"
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; SciencePredictionTracker/1.0)')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error fetching events: {e}", file=sys.stderr)
        return []

def get_probability(event):
    """Extract probability from event's markets"""
    try:
        if not event.get('markets'):
            return None
        
        market = event['markets'][0]
        outcome_prices = json.loads(market.get('outcomePrices', '["0", "0"]'))
        return float(outcome_prices[1])
    except:
        return None

def filter_tech_events(events, tech_tags):
    """Filter technology events"""
    filtered = []
    for event in events:
        event_tags = [t['slug'] for t in event.get('tags', [])]
        
        if any(tag in event_tags for tag in tech_tags):
            prob = get_probability(event)
            if prob is not None and 0 < prob < 1:
                filtered.append({
                    'id': event['id'],
                    'title': event.get('title', ''),
                    'probability': prob,
                    'tags': [t['slug'] for t in event.get('tags', [])],
                    'polymarket_url': f"https://polymarket.com/event/{event.get('slug', '')}"
                })
    
    return filtered

def load_last_hour_data():
    """Load last hour's snapshot"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    now = datetime.now()
    # Look for snapshot from 55-65 minutes ago
    for minutes_ago in range(55, 65):
        time = now - timedelta(minutes=minutes_ago)
        snapshot_file = HISTORY_DIR / f"{time.strftime('%Y-%m-%d-%H')}.json"
        
        if snapshot_file.exists():
            with open(snapshot_file) as f:
                data = json.load(f)
                return {e['id']: e for e in data.get('events', [])}
    
    return {}

def save_snapshot(events):
    """Save current snapshot"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'events': events
    }
    
    snapshot_file = HISTORY_DIR / f"{datetime.now().strftime('%Y-%m-%d-%H')}.json"
    with open(snapshot_file, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    # Clean old snapshots (>90 days)
    cutoff = datetime.now() - timedelta(days=90)
    for f in HISTORY_DIR.glob('*.json'):
        try:
            file_date = datetime.strptime(f.stem, '%Y-%m-%d-%H')
            if file_date < cutoff:
                f.unlink()
        except:
            pass

def categorize_events(current_events, last_hour_events):
    """Categorize based on 1-hour comparison + 3% threshold"""
    new_entries = []
    exited_entries = []
    long_term = []
    
    for event in current_events:
        event_id = event['id']
        current_prob = event['probability']
        current_high = current_prob >= HIGH_THRESHOLD
        
        # Get last hour data
        last_data = last_hour_events.get(event_id, {})
        last_prob = last_data.get('probability', current_prob)
        last_high = last_prob >= HIGH_THRESHOLD
        
        # Calculate change
        prob_change = abs(current_prob - last_prob)
        
        # Check if crossed threshold with >3% change
        crossed_to_high = (not last_high) and current_high and prob_change >= CHANGE_THRESHOLD
        crossed_from_high = last_high and (not current_high) and prob_change >= CHANGE_THRESHOLD
        
        if crossed_to_high:
            # New entry
            new_entries.append({
                **event,
                'hours_ago': 1,
                'change': prob_change
            })
        elif crossed_from_high:
            # Exited entry
            exited_entries.append({
                **event,
                'hours_ago': 1,
                'change': prob_change
            })
        elif current_high:
            # Long-term (stable high)
            long_term.append({
                'id': event['id'],
                'title': event['title'],
                'probability': event['probability'],
                'tags': event.get('tags', [])
            })
    
    return new_entries, exited_entries, long_term

def generate_news_from_long_term(long_term_events):
    """Generate aggregated news from long-term events"""
    if not long_term_events:
        return []
    
    # Simple aggregation by first tag
    tag_groups = {}
    for event in long_term_events:
        main_tag = event.get('tags', ['other'])[0]
        if main_tag not in tag_groups:
            tag_groups[main_tag] = []
        tag_groups[main_tag].append(event)
    
    # Generate news
    news_list = []
    for tag, events in tag_groups.items():
        avg_prob = sum(e['probability'] for e in events) / len(events)
        news_list.append({
            'title': f"{tag.upper()}: {len(events)} events with avg {avg_prob*100:.1f}% probability",
            'summary': f"Stable high-probability events in {tag}",
            'event_count': len(events),
            'avg_probability': avg_prob,
            'tag': tag,
            'events': events  # Will be lazy-loaded in frontend
        })
    
    return news_list

def generate_output(new_entries, exited_entries, long_term_events):
    """Generate output JSON"""
    long_term_news = generate_news_from_long_term(long_term_events)
    
    return {
        'category': 'technology',
        'updated_at': datetime.now().isoformat(),
        'new_entries': sorted(new_entries, key=lambda x: x['hours_ago']),
        'exited_entries': sorted(exited_entries, key=lambda x: x['hours_ago']),
        'long_term_news': long_term_news,  # News list (not cards)
        'long_term_count': len(long_term_events)
    }

def main():
    print("🚀 Starting fetch_events.py (optimized)...")
    
    config = load_config()
    tech_tags = config['categories']['technology']['tags']
    
    print("📡 Fetching events from Polymarket...")
    events = fetch_events()
    print(f"   Fetched {len(events)} total events")
    
    tech_events = filter_tech_events(events, tech_tags)
    print(f"   Filtered {len(tech_events)} technology events")
    
    last_hour = load_last_hour_data()
    print(f"   Loaded {len(last_hour)} records from last hour")
    
    new_entries, exited_entries, long_term = categorize_events(tech_events, last_hour)
    print(f"   New entries: {len(new_entries)}")
    print(f"   Exited entries: {len(exited_entries)}")
    print(f"   Long-term events: {len(long_term)}")
    
    output = generate_output(new_entries, exited_entries, long_term)
    
    TECH_DIR.mkdir(parents=True, exist_ok=True)
    output_file = TECH_DIR / "events.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved to {output_file}")
    
    save_snapshot(tech_events)
    print("✅ Snapshot saved")
    
    print("\n🎉 Done!")

if __name__ == '__main__':
    main()
