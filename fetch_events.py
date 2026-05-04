#!/usr/bin/env python3
"""
Fetch Polymarket events - Three-Board System
1小时榜 (Hour Watch) → 每日榜 (Daily Watch) → 长期榜 (Long Term)

Logic:
- 1小时榜: 每小时更新，进入/退出 60%/70%/80%/90% 的事件
- 每日榜: 1小时榜事件自动累积（下一个小时进入）
- 长期榜: 第二天01:00，昨日每日榜全部转入
- 变动检测: 长期榜事件大幅下跌（如90%→60%），退出并回到1小时榜
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "docs" / "data"
TECH_DIR = DATA_DIR / "technology"
HISTORY_DIR = DATA_DIR / "history"
DAILY_WATCH_DIR = BASE_DIR / "docs" / "data" / "daily_watch"
LONG_TERM_DIR = BASE_DIR / "docs" / "data" / "long_term"

GAMMA_API = "https://gamma-api.polymarket.com/events"
THRESHOLDS = [0.60, 0.70, 0.80, 0.90]

# 长期榜变动阈值：从峰值下跌超过30%视为变动
LONG_TERM_CHANGE_THRESHOLD = 0.30

def load_config():
    config_file = DATA_DIR / "config.json"
    try:
        with open(config_file) as f:
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
        return float(outcome_prices[0])
    except:
        return None

def filter_tech_events(events, tech_tags):
    """Filter technology events - save complete market info"""
    filtered = []
    for event in events:
        event_tags = [t['slug'] for t in event.get('tags', [])]
        
        if any(tag in event_tags for tag in tech_tags):
            prob = get_probability(event)
            if prob is not None and 0 < prob < 1:
                # Save complete event info including markets
                filtered.append({
                    'id': event['id'],
                    'title': event.get('title', ''),
                    'probability': prob,
                    'tags': [t['slug'] for t in event.get('tags', [])],
                    # Save complete markets array
                    'markets': event.get('markets', []),
                    # Save additional fields for detail page
                    'resolutionSource': event.get('resolutionSource', ''),
                    'description': event.get('description', ''),
                    'volume': event.get('volume', 0),
                    'liquidity': event.get('liquidity', 0),
                    'startDate': event.get('startDate', ''),
                    'endDate': event.get('endDate', ''),
                    'active': event.get('active', False),
                    'closed': event.get('closed', False)
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

def check_long_term_changes(current_events):
    """
    检查长期榜事件是否发生变动
    如果事件从峰值大幅下跌，退出长期榜，回到1小时榜
    返回: (需要退出的事件列表, 更新后的长期榜数据)
    """
    LONG_TERM_DIR.mkdir(parents=True, exist_ok=True)
    long_term_file = LONG_TERM_DIR / "long_term.json"
    
    if not long_term_file.exists():
        return [], None
    
    with open(long_term_file) as f:
        long_term_data = json.load(f)
    
    # 构建当前事件查找表
    current_lookup = {e['id']: e for e in current_events}
    
    exited_events = []
    events_to_remove = []
    
    for event_id, lt_event in long_term_data.get('events', {}).items():
        # 如果事件不在当前列表中（已关闭），跳过
        if event_id not in current_lookup:
            continue
        
        current_event = current_lookup[event_id]
        current_prob = current_event.get('probability', 0)
        peak_prob = lt_event.get('peak_prob', current_prob)
        
        # 检查是否发生大幅下跌
        if peak_prob - current_prob >= LONG_TERM_CHANGE_THRESHOLD:
            print(f"  ⚠️  Long-term event changed: {lt_event.get('title')}")
            print(f"      Peak: {peak_prob:.1%} → Current: {current_prob:.1%} (drop: {peak_prob-current_prob:.1%})")
            
            # 添加到退出列表（需要回到1小时榜）
            exited_events.append({
                **current_event,
                'change_reason': f"Long-term exit: {peak_prob:.1%} → {current_prob:.1%}"
            })
            events_to_remove.append(event_id)
    
    # 移除退出的事件
    for event_id in events_to_remove:
        del long_term_data['events'][event_id]
    
    if events_to_remove:
        long_term_data['updated_at'] = datetime.now().isoformat()
        with open(long_term_file, 'w') as f:
            json.dump(long_term_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Removed {len(events_to_remove)} events from long-term board")
    
    return exited_events, long_term_data

def update_watch_events(current_events, last_hour_events, daily_data, long_term_exited):
    """Update hour watch and daily watch events"""
    hour_watch = []
    now_str = datetime.now().strftime('%H:%M')
    
    # 将长期榜退出的事件加入 hour_watch
    for exited_event in long_term_exited:
        hour_watch.append({
            **exited_event,
            'history': [{
                'time': now_str,
                'prob': exited_event['probability'],
                'reason': exited_event.get('change_reason', 'Long-term exit')
            }]
        })
    
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
                    'current_prob': current_prob,
                    # Save complete market info
                    'markets': event.get('markets', []),
                    'resolutionSource': event.get('resolutionSource', ''),
                    'description': event.get('description', ''),
                    'volume': event.get('volume', 0),
                    'liquidity': event.get('liquidity', 0),
                    'startDate': event.get('startDate', ''),
                    'endDate': event.get('endDate', ''),
                    'active': event.get('active', False),
                    'closed': event.get('closed', False)
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

def load_long_term_board():
    """Load long-term board data for output"""
    LONG_TERM_DIR.mkdir(parents=True, exist_ok=True)
    long_term_file = LONG_TERM_DIR / "long_term.json"
    
    if not long_term_file.exists():
        return {'events': {}, 'updated_at': None}
    
    with open(long_term_file) as f:
        return json.load(f)

def generate_output(hour_watch, daily_watch_summaries, long_term_data):
    """Generate output JSON with three boards"""
    # Also generate tag summaries for long-term events (if any in daily watch but not in hour_watch)
    # This is for the "long_term_summaries" section which shows events above thresholds but not crossing
    
    return {
        'category': 'technology',
        'updated_at': datetime.now().isoformat(),
        'hour_watch_summaries': generate_watch_summaries(hour_watch),
        'daily_watch_summaries': daily_watch_summaries,
        'long_term_data': {
            'event_count': len(long_term_data.get('events', {})),
            'events': list(long_term_data.get('events', {}).values()),
            'updated_at': long_term_data.get('updated_at')
        }
    }

def main():
    print("🚀 Starting fetch_events.py (Three-Board System)...")
    
    config = load_config()
    tech_tags = config.get('categories', {}).get('technology', {}).get('tags', ['tech', 'ai'])
    
    print("📡 Fetching events from Polymarket...")
    events = fetch_events()
    print(f"   Fetched {len(events)} total events")
    
    tech_events = filter_tech_events(events, tech_tags)
    print(f"   Filtered {len(tech_events)} technology events")
    
    # 检查长期榜变动（必须在更新 daily_watch 之前）
    print("\n🔍 Checking long-term board for changes...")
    long_term_exited, _ = check_long_term_changes(tech_events)
    if long_term_exited:
        print(f"   {len(long_term_exited)} events exited long-term board")
    
    last_hour = load_last_hour_data()
    print(f"   Loaded {len(last_hour)} records from last hour")
    
    # Load daily watch data
    daily_data = load_daily_watch()
    print(f"   Loaded {len(daily_data['events'])} events from daily watch")
    
    # Update watch events (includes long-term exited events)
    hour_watch, daily_data = update_watch_events(tech_events, last_hour, daily_data, long_term_exited)
    print(f"   Hour watch events: {len(hour_watch)}")
    print(f"   Daily watch events: {len(daily_data['events'])}")
    
    # Generate daily watch summaries
    daily_watch_summaries = generate_daily_watch_summaries(daily_data)
    print(f"   Daily watch summaries: {len(daily_watch_summaries)} tag groups")
    
    # Save daily watch data
    save_daily_watch(daily_data)
    print(f"✅ Daily watch saved")
    
    # Load long-term board data for output
    long_term_data = load_long_term_board()
    print(f"   Long-term events: {len(long_term_data.get('events', {}))}")
    
    # Generate output
    output = generate_output(hour_watch, daily_watch_summaries, long_term_data)
    
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
