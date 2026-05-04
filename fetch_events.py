#!/usr/bin/env python3
"""
Fetch Polymarket events - Two-Board System
每日榜 (Daily Watch) + 长期榜 (Long Term)

Logic:
- 每日榜: 保存所有当前活跃的科技事件（每小时更新）
- 长期榜: 每天01:00，昨日每日榜全部转入
- 变动检测: 长期榜事件大幅下跌（如90%→60%），退出并回到每日榜
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "docs" / "data"
TECH_DIR = DATA_DIR / "technology"
DAILY_WATCH_DIR = BASE_DIR / "docs" / "data" / "daily_watch"
LONG_TERM_DIR = BASE_DIR / "docs" / "data" / "long_term"

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
    
    url = f"https://gamma-api.polymarket.com/events?active=true&closed=false&limit={limit}"
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

def update_daily_watch(current_events, daily_data):
    """Update daily watch: add new events, update existing ones"""
    now_str = datetime.now().strftime('%H:%M')
    new_entries = []
    updated_count = 0
    
    for event in current_events:
        event_id = event['id']
        current_prob = event['probability']
        
        if event_id not in daily_data['events']:
            # New event - add to daily watch
            daily_data['events'][event_id] = {
                'id': event_id,
                'title': event['title'],
                'tags': event['tags'],
                'first_seen': datetime.now().isoformat(),
                'history': [{
                    'time': now_str,
                    'prob': current_prob,
                    'reason': 'First seen'
                }],
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
            new_entries.append(event)
        else:
            # Existing event - update probability and add history if significant change
            old_prob = daily_data['events'][event_id]['current_prob']
            daily_data['events'][event_id]['current_prob'] = current_prob
            
            # Add history entry if probability changed by more than 5%
            if abs(current_prob - old_prob) >= 0.05:
                daily_data['events'][event_id]['history'].append({
                    'time': now_str,
                    'prob': current_prob,
                    'reason': f'Change: {old_prob:.1%} → {current_prob:.1%}'
                })
            updated_count += 1
    
    return new_entries, updated_count

def check_long_term_changes(current_events):
    """
    检查长期榜事件是否发生变动
    如果事件从峰值大幅下跌，退出长期榜，回到每日榜
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
            
            # 添加到退出列表（需要回到每日榜）
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

def generate_output(daily_watch_summaries, long_term_data):
    """Generate output JSON with two boards (no hour watch)"""
    
    return {
        'category': 'technology',
        'updated_at': datetime.now().isoformat(),
        'daily_watch_summaries': daily_watch_summaries,
        'long_term_data': {
            'event_count': len(long_term_data.get('events', {})),
            'events': list(long_term_data.get('events', {}).values()),
            'updated_at': long_term_data.get('updated_at')
        }
    }

def main():
    print("🚀 Starting fetch_events.py (Two-Board System)...")
    
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
    
    # Load daily watch data
    daily_data = load_daily_watch()
    print(f"   Loaded {len(daily_data['events'])} events from daily watch")
    
    # Update daily watch (add new events, update existing)
    new_entries, updated_count = update_daily_watch(tech_events, daily_data)
    print(f"   New events: {len(new_entries)}")
    print(f"   Updated events: {updated_count}")
    print(f"   Total daily watch events: {len(daily_data['events'])}")
    
    # Generate daily watch summaries
    daily_watch_summaries = generate_daily_watch_summaries(daily_data)
    print(f"   Daily watch summaries: {len(daily_watch_summaries)} tag groups")
    
    # Save daily watch data
    save_daily_watch(daily_data)
    print(f"✅ Daily watch saved")
    
    # Load long-term board data for output
    long_term_data = load_long_term_board()
    print(f"   Long-term events: {len(long_term_data.get('events', {}))}")
    
    # Generate output (no hour watch)
    output = generate_output(daily_watch_summaries, long_term_data)
    
    TECH_DIR.mkdir(parents=True, exist_ok=True)
    output_file = TECH_DIR / "events.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved to {output_file}")
    
    # Handle exited events - add back to daily watch with history
    if long_term_exited:
        print(f"\n📋 Adding {len(long_term_exited)} exited events back to daily watch...")
        for exited_event in long_term_exited:
            event_id = exited_event['id']
            if event_id not in daily_data['events']:
                daily_data['events'][event_id] = {
                    'id': event_id,
                    'title': exited_event['title'],
                    'tags': exited_event['tags'],
                    'first_seen': datetime.now().isoformat(),
                    'history': [{
                        'time': datetime.now().strftime('%H:%M'),
                        'prob': exited_event['probability'],
                        'reason': exited_event.get('change_reason', 'Long-term exit')
                    }],
                    'current_prob': exited_event['probability'],
                    'markets': exited_event.get('markets', []),
                    'resolutionSource': exited_event.get('resolutionSource', ''),
                    'description': exited_event.get('description', ''),
                }
        save_daily_watch(daily_data)
        print(f"✅ Daily watch updated with exited events")
    
    print("\n🎉 Done!")

if __name__ == '__main__':
    main()
