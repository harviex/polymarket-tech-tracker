#!/usr/bin/env python3
"""
Fetch Polymarket events - Daily Watch Version
60%/70%/80%/90% thresholds + 1-hour comparison + Daily Watch tracking
Generates tag summary cards for long-term and watch events
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "docs" / "data"
HISTORY_DIR = DATA_DIR / "history"
TECH_DIR = DATA_DIR / "technology"
CONFIG_FILE = DATA_DIR / "config.json"
DAILY_WATCH_DIR = DATA_DIR / "daily_watch"

GAMMA_API = "https://gamma-api.polymarket.com/events"
THRESHOLDS = [0.60, 0.70, 0.80, 0.90]  # Multi-threshold detection

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except:
        return {"categories": {"technology": {"tags": ["tech", "ai", "crypto"]}}}

def fetch_events(limit=1000):
    """Fetch active events from Polymarket"""
    import urllib.request
    
    url = f"{GAMMA_API}?active=true&closed=false&limit={limit}"
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; PolymarketTracker/1.0)')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error fetching events: {e}", file=sys.stderr)
        return []

def get_probability(event):
    """Extract probability from event's markets - returns YES probability"""
    try:
        if not event.get('markets'):
            return None
        
        market = event['markets'][0]
        outcome_prices = json.loads(market.get('outcomePrices', '["0", "0"]'))
        # Return YES probability (index 0), not NO (index 1)
        return float(outcome_prices[0])
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
                    'tags': [t['slug'] for t in event.get('tags', [])]
                })
    
    return filtered

def load_last_hour_data():
    """Load last hour's snapshot"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    now = datetime.now()
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

def load_daily_watch():
    """Load today's daily watch events"""
    DAILY_WATCH_DIR.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime('%Y-%m-%d')
    watch_file = DAILY_WATCH_DIR / f"{today}.json"
    
    if watch_file.exists():
        with open(watch_file) as f:
            return json.load(f)
    
    return {
        'date': today,
        'events': {}  # event_id -> event data with history
    }

def save_daily_watch(daily_data):
    """Save today's daily watch events"""
    DAILY_WATCH_DIR.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime('%Y-%m-%d')
    watch_file = DAILY_WATCH_DIR / f"{today}.json"
    
    with open(watch_file, 'w') as f:
        json.dump(daily_data, f, indent=2, ensure_ascii=False)

def categorize_events(current_events, last_hour_events):
    """Categorize based on crossing any threshold (60%/70%/80%/90%)"""
    new_entries = []
    exited_entries = []
    long_term = []
    
    for event in current_events:
        event_id = event['id']
        current_prob = event['probability']
        
        # Get last hour data
        last_data = last_hour_events.get(event_id, {})
        last_prob = last_data.get('probability', current_prob)
        
        # Check which thresholds were crossed
        crossed_up = None  # Highest threshold crossed going up
        crossed_down = None  # Highest threshold crossed going down
        
        for threshold in sorted(THRESHOLDS, reverse=True):  # Check from high to low
            last_above = last_prob >= threshold
            current_above = current_prob >= threshold
            
            if not last_above and current_above:
                # Crossed UP across this threshold
                crossed_up = threshold
                break  # Found highest threshold crossed up
            elif last_above and not current_above:
                # Crossed DOWN across this threshold
                crossed_down = threshold
                break  # Found highest threshold crossed down
        
        # Categorize
        if crossed_up:
            new_entries.append({
                **event,
                'hours_ago': 1,
                'change': current_prob - last_prob,
                'crossed_threshold': crossed_up
            })
        elif crossed_down:
            exited_entries.append({
                **event,
                'hours_ago': 1,
                'change': last_prob - current_prob,  # Positive value for display
                'crossed_threshold': crossed_down
            })
        elif current_prob >= min(THRESHOLDS):
            # Currently above lowest threshold but didn't just cross
            long_term.append(event)
    
    return new_entries, exited_entries, long_term

def update_watch_events(current_events, last_hour_events, daily_data):
    """Update hour watch and daily watch events"""
    hour_watch = []  # Events that crossed thresholds this hour
    now_str = datetime.now().strftime('%H:%M')
    
    for event in current_events:
        event_id = event['id']
        current_prob = event['probability']
        
        # Always update current_prob in daily_data if event exists
        if event_id in daily_data['events']:
            daily_data['events'][event_id]['current_prob'] = current_prob
        
        # Get last hour data
        last_data = last_hour_events.get(event_id, {})
        last_prob = last_data.get('probability', current_prob)
        
        # Check if crossed any threshold
        crossed_threshold = None
        direction = None
        
        for threshold in sorted(THRESHOLDS, reverse=True):
            last_above = last_prob >= threshold
            current_above = current_prob >= threshold
            
            if not last_above and current_above:
                crossed_threshold = threshold
                direction = 'up'
                break
            elif last_above and not current_above:
                crossed_threshold = threshold
                direction = 'down'
                break
        
        # If crossed a threshold, add to hour watch and daily watch
        if crossed_threshold:
            history_entry = {
                'time': now_str,
                'prob': current_prob,
                'threshold': crossed_threshold,
                'direction': direction
            }
            
            # Add to hour watch (current hour only)
            hour_watch.append({
                **event,
                'history': [history_entry]
            })
            
            # Add to daily watch (accumulate)
            if event_id not in daily_data['events']:
                daily_data['events'][event_id] = {
                    'id': event_id,
                    'title': event['title'],
                    'tags': event['tags'],
                    'first_seen': datetime.now().isoformat(),
                    'history': [],
                    'current_prob': current_prob
                }
            
            daily_data['events'][event_id]['history'].append(history_entry)
            daily_data['events'][event_id]['current_prob'] = current_prob
    
    return hour_watch, daily_data

def generate_tag_summaries(events):
    """Generate tag summary cards from events list"""
    if not events:
        return []
    
    # Group by first tag
    tag_groups = {}
    for event in events:
        tags = event.get('tags', [])
        if tags and len(tags) > 0:
            main_tag = tags[0]
        else:
            main_tag = 'other'
        
        if main_tag not in tag_groups:
            tag_groups[main_tag] = []
        tag_groups[main_tag].append(event)
    
    # Generate summaries
    summaries = []
    for tag, tag_events in tag_groups.items():
        if not tag_events:
            continue
        try:
            avg_prob = sum(e['probability'] for e in tag_events) / len(tag_events)
            summaries.append({
                'tag': tag,
                'tag_display': tag.upper(),
                'event_count': len(tag_events),
                'avg_probability': avg_prob,
                'max_probability': max(e['probability'] for e in tag_events),
                'min_probability': min(e['probability'] for e in tag_events),
                'events': tag_events
            })
        except Exception as e:
            print(f"Error processing tag {tag}: {e}", file=sys.stderr)
    
    # Sort by event count (descending)
    return sorted(summaries, key=lambda x: x['event_count'], reverse=True)

def generate_watch_summaries(watch_events):
    """Generate tag summaries for watch events (with history)"""
    if not watch_events:
        return []
    
    # Group by first tag
    tag_groups = {}
    for event in watch_events:
        tags = event.get('tags', [])
        if tags and len(tags) > 0:
            main_tag = tags[0]
        else:
            main_tag = 'other'
        
        if main_tag not in tag_groups:
            tag_groups[main_tag] = []
        tag_groups[main_tag].append(event)
    
    # Generate summaries (include history in events)
    summaries = []
    for tag, events in tag_groups.items():
        if not events:
            continue
        try:
            avg_prob = sum(e['probability'] for e in events) / len(events)
            summaries.append({
                'tag': tag,
                'tag_display': tag.upper(),
                'event_count': len(events),
                'avg_probability': avg_prob,
                'max_probability': max(e['probability'] for e in events),
                'min_probability': min(e['probability'] for e in events),
                'events': events  # Contains history
            })
        except Exception as e:
            print(f"Error processing watch tag {tag}: {e}", file=sys.stderr)
    
    return sorted(summaries, key=lambda x: x['event_count'], reverse=True)

def generate_daily_watch_summaries(daily_data):
    """Generate tag summaries from daily watch data"""
    events_list = list(daily_data['events'].values())
    
    if not events_list:
        return []
    
    # Group by first tag
    tag_groups = {}
    for event in events_list:
        tags = event.get('tags', [])
        if tags and len(tags) > 0:
            main_tag = tags[0]
        else:
            main_tag = 'other'
        
        if main_tag not in tag_groups:
            tag_groups[main_tag] = []
        tag_groups[main_tag].append(event)
    
    # Generate summaries
    summaries = []
    for tag, events in tag_groups.items():
        if not events:
            continue
        try:
            probs = [e['current_prob'] for e in events]
            avg_prob = sum(probs) / len(probs)
            summaries.append({
                'tag': tag,
                'tag_display': tag.upper(),
                'event_count': len(events),
                'avg_probability': avg_prob,
                'max_probability': max(probs),
                'min_probability': min(probs),
                'events': events  # Contains full history
            })
        except Exception as e:
            print(f"Error processing daily watch tag {tag}: {e}", file=sys.stderr)
    
    return sorted(summaries, key=lambda x: x['event_count'], reverse=True)

def generate_output(new_entries, exited_entries, long_term_events, hour_watch, daily_watch_summaries):
    """Generate output JSON"""
    tag_summaries = generate_tag_summaries(long_term_events)
    hour_watch_summaries = generate_watch_summaries(hour_watch)
    
    return {
        'category': 'technology',
        'updated_at': datetime.now().isoformat(),
        'new_entries': sorted(new_entries, key=lambda x: x['hours_ago']),
        'exited_entries': sorted(exited_entries, key=lambda x: x['hours_ago']),
        'long_term_summaries': tag_summaries,
        'long_term_count': len(long_term_events),
        'hour_watch_summaries': hour_watch_summaries,
        'daily_watch_summaries': daily_watch_summaries
    }

def main():
    print("🚀 Starting fetch_events.py (Daily Watch Version)...")
    
    config = load_config()
    tech_tags = config.get('categories', {}).get('technology', {}).get('tags', ['tech', 'ai'])
    
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
    
    # Load daily watch data
    daily_data = load_daily_watch()
    print(f"   Loaded {len(daily_data['events'])} events from daily watch")
    
    # Update watch events
    hour_watch, daily_data = update_watch_events(tech_events, last_hour, daily_data)
    print(f"   Hour watch events: {len(hour_watch)}")
    print(f"   Daily watch events: {len(daily_data['events'])}")
    
    # Generate daily watch summaries
    daily_watch_summaries = generate_daily_watch_summaries(daily_data)
    print(f"   Daily watch summaries: {len(daily_watch_summaries)} tag groups")
    
    # Save daily watch data
    save_daily_watch(daily_data)
    print(f"✅ Daily watch saved")
    
    output = generate_output(new_entries, exited_entries, long_term, hour_watch, daily_watch_summaries)
    print(f"   Tag summaries: {len(output['long_term_summaries'])}")
    print(f"   Hour watch summaries: {len(output['hour_watch_summaries'])}")
    print(f"   Daily watch summaries: {len(output['daily_watch_summaries'])}")
    
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
