#!/usr/bin/env python3
"""
Fetch Polymarket events and generate categorized data
Supports: new entries, exited entries, long-term aggregation
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "docs" / "data"
HISTORY_DIR = DATA_DIR / "history"
TECH_DIR = DATA_DIR / "technology"
CONFIG_FILE = DATA_DIR / "config.json"

# API
GAMMA_API = "https://gamma-api.polymarket.com/events"
HIGH_THRESHOLD = 0.70
STABLE_HOURS = 3
DISPLAY_DAYS = 3

def load_config():
    """Load configuration"""
    with open(CONFIG_FILE) as f:
        return json.load(f)

def fetch_events(limit=1000):
    """Fetch active events from Polymarket Gamma API"""
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
        
        # Get the first market's outcome prices
        market = event['markets'][0]
        outcome_prices = json.loads(market.get('outcomePrices', '["0", "0"]'))
        
        # outcomePrices[1] is YES probability
        return float(outcome_prices[1])
    except:
        return None

def filter_tech_events(events, tech_tags):
    """Filter events by technology tags"""
    filtered = []
    for event in events:
        event_tags = [t['slug'] for t in event.get('tags', [])]
        
        # Check if any tech tag matches (strict match)
        if any(tag in event_tags for tag in tech_tags):
            prob = get_probability(event)
            if prob is not None and 0 < prob < 1:  # Filter out resolved events
                filtered.append({
                    'id': event['id'],
                    'title': event.get('title', ''),
                    'probability': prob,
                    'tags': [t['slug'] for t in event.get('tags', [])],
                    'polymarket_url': f"https://polymarket.com/event/{event.get('slug', '')}"
                })
    
    return filtered

def load_history():
    """Load historical data for comparison"""
    history = {}
    
    # Load last 3 hours of snapshots
    now = datetime.now()
    for hours_ago in [0, 1, 2, 3]:
        snapshot_time = now - timedelta(hours=hours_ago)
        snapshot_file = HISTORY_DIR / f"{snapshot_time.strftime('%Y-%m-%d-%H')}.json"
        
        if snapshot_file.exists():
            with open(snapshot_file) as f:
                data = json.load(f)
                for event in data.get('events', []):
                    history[event['id']] = event
    
    return history

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

def categorize_events(current_events, history):
    """Categorize events into new/exited/long-term"""
    new_entries = []
    exited_entries = []
    long_term = {}
    
    now = datetime.now()
    
    for event in current_events:
        event_id = event['id']
        prob = event['probability']
        is_high = prob >= HIGH_THRESHOLD
        
        # Get historical data
        hist = history.get(event_id, {})
        hist_high = hist.get('is_high', False)
        hist_time = datetime.fromisoformat(hist.get('timestamp', '2000-01-01T00:00:00'))
        
        # Calculate hours in current state
        hours_in_state = (now - hist_time).total_seconds() / 3600 if hist else 999
        
        # New entry: just crossed 70% threshold
        if is_high and not hist_high and hours_in_state <= STABLE_HOURS:
            new_entries.append({
                **event,
                'hours_ago': int(hours_in_state),
                'is_high': True
            })
        
        # Exited: just fell below 70%
        elif not is_high and hist_high and hours_in_state <= STABLE_HOURS:
            exited_entries.append({
                **event,
                'hours_ago': int(hours_in_state),
                'is_high': False
            })
        
        # Long-term: high probability for >3 hours
        elif is_high and hours_in_state > STABLE_HOURS:
            # Group by tags
            for tag in event.get('tags', []):
                if tag not in long_term:
                    long_term[tag] = []
                
                long_term[tag].append({
                    'id': event['id'],
                    'title': event['title'],
                    'probability': event['probability'],
                    'days_in_high': int(hours_in_state / 24)
                })
        
        # Update history
        history[event_id] = {
            'id': event_id,
            'is_high': is_high,
            'timestamp': now.isoformat(),
            'probability': prob
        }
    
    return new_entries, exited_entries, long_term

def generate_output(new_entries, exited_entries, long_term):
    """Generate output JSON"""
    return {
        'category': 'technology',
        'updated_at': datetime.now().isoformat(),
        'new_entries': sorted(new_entries, key=lambda x: x['hours_ago']),
        'exited_entries': sorted(exited_entries, key=lambda x: x['hours_ago']),
        'long_term': long_term,
        'archived': []
    }

def main():
    print("🚀 Starting fetch_events.py...")
    
    # Load config
    config = load_config()
    tech_tags = config['categories']['technology']['tags']
    
    # Fetch events
    print("📡 Fetching events from Polymarket...")
    events = fetch_events()
    print(f"   Fetched {len(events)} total events")
    
    # Filter tech events
    tech_events = filter_tech_events(events, tech_tags)
    print(f"   Filtered {len(tech_events)} technology events")
    
    # Load history
    history = load_history()
    print(f"   Loaded {len(history)} historical records")
    
    # Categorize
    new_entries, exited_entries, long_term = categorize_events(tech_events, history)
    print(f"   New entries: {len(new_entries)}")
    print(f"   Exited entries: {len(exited_entries)}")
    print(f"   Long-term groups: {len(long_term)}")
    
    # Generate output
    output = generate_output(new_entries, exited_entries, long_term)
    
    # Save output
    TECH_DIR.mkdir(parents=True, exist_ok=True)
    output_file = TECH_DIR / "events.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved to {output_file}")
    
    # Save snapshot
    save_snapshot(tech_events)
    print("✅ Snapshot saved")
    
    print("\n🎉 Done!")

if __name__ == '__main__':
    main()
