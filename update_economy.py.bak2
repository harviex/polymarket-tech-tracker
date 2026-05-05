#!/usr/bin/env python3
"""
Polymarket Tech Tracker - Economy Long-Term Updater
每天00:00运行：抓取高概率economy+business事件（70%-99%）并更新Long-Term数据
合并 business 和 economy 两个标签的事件，去重后处理
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from collections import OrderedDict

BASE_DIR = Path(__file__).parent
ECONOMY_DIR = BASE_DIR / "docs" / "data" / "economy"
LONG_TERM_DIR = ECONOMY_DIR / "long_term"

GAMMA_API = "https://gamma-api.polymarket.com/events"

def fetch_events_by_tag(tag, max_retries=3):
    """用curl抓取指定标签的事件"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"{GAMMA_API}?tag_slug={tag}&end_date_min={today}&volume_min=10000&limit=1000"
    
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ['curl', '-s', '--max-time', '10', 
                 '-H', 'User-Agent: Mozilla/5.0 (compatible; PolymarketTracker/1.0)', 
                 '-H', 'Accept: application/json', 
                 url],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and result.stdout:
                events = json.loads(result.stdout)
                return events if isinstance(events, list) else []
            else:
                raise Exception(f"curl failed: {result.stderr}")
        except Exception as e:
            print(f"  Attempt {attempt+1}/{max_retries} failed for tag '{tag}': {e}", file=sys.stderr)
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
    
    print(f"❌ All {max_retries} attempts failed for tag '{tag}'", file=sys.stderr)
    return []

def fetch_high_prob_events(max_retries=3):
    """抓取并合并 business 和 economy 两个标签的事件"""
    print("  Fetching events from 'business' tag...")
    business_events = fetch_events_by_tag('business', max_retries)
    print(f"    Found {len(business_events)} business events")
    
    print("  Fetching events from 'economy' tag...")
    economy_events = fetch_events_by_tag('economy', max_retries)
    print(f"    Found {len(economy_events)} economy events")
    
    # 合并并去重（按 event id）
    merged = OrderedDict()
    for event in business_events + economy_events:
        event_id = event.get('id')
        if event_id and event_id not in merged:
            merged[event_id] = event
    
    print(f"  Merged: {len(merged)} unique events (removed {len(business_events) + len(economy_events) - len(merged)} duplicates)")
    return list(merged.values())

def extract_option_text(event, yes_prob=None):
    """提取概率对应的选项文字"""
    import re, json
    
    markets = event.get('markets', [])
    if not markets:
        return None
    
    main_market = markets[0]
    title = event.get('title', '')
    question = main_market.get('question', '')
    description = event.get('description', '')
    
    outcome_names = json.loads(main_market.get('outcomeNames', '[]'))
    outcome_prices = json.loads(main_market.get('outcomePrices', '[]'))
    
    if yes_prob is None:
        yes_prob = float(outcome_prices[0]) if len(outcome_prices) > 0 else 0
    
    if outcome_names == ["Yes", "No"] or outcome_names == ["No", "Yes"]:
        return "Yes" if yes_prob > 0.5 else "No"
    
    if len(outcome_names) > 0 and len(outcome_prices) == len(outcome_names):
        prices = [float(p) for p in outcome_prices]
        max_idx = prices.index(max(prices))
        return outcome_names[max_idx]
    
    if ' or ' in question and '?' in question:
        resolve_matches = re.findall(r'resolve to "([^"]+)"', description, re.IGNORECASE)
        if len(resolve_matches) >= 2:
            return resolve_matches[0] if yes_prob > 0.5 else resolve_matches[1]
    
    if 'above' in question.lower():
        amount_match = re.search(r'above\s+([0-9,.]+[BMKTm]?)', question, re.IGNORECASE)
        if amount_match:
            value = amount_match.group(1)
            if '$' not in value and any(c.isdigit() for c in value):
                return value.upper()
            return value
        amount_match = re.search(r'\$([0-9,.]+[BMKT]?)', description, re.IGNORECASE)
        if amount_match:
            return '$' + amount_match.group(1)
        return "Yes" if yes_prob > 0.5 else "No"
    
    match = re.search(r'\$[0-9.]+[BMKT]?', question)
    if match:
        return match.group(0)
    
    match = re.search(r'[0-9]+%', question)
    if match:
        return match.group(0)
    
    if 'Which ' in title or 'Which ' in question:
        import re
        match = re.search(r'Will ([A-Za-z]+) ', question)
        if match:
            return match.group(1)
        return "Choice"
    
    return "Yes" if yes_prob > 0.5 else "No"

def filter_and_process_events(events, min_prob=0.70, max_prob=0.99, required_tags=None):
    """过滤并处理高概率事件（70%-99%，不含100%）"""
    # 对于 economy，不强制要求特定标签（因为已经通过 tag_slug 过滤了）
    # 但我们可以检查是否至少包含 business 或 economy
    if required_tags is None:
        required_tags = ['business', 'economy']
    
    filtered = []
    for event in events:
        if not event.get('markets'):
            continue
        
        event_tags = [t.get('slug', '') for t in event.get('tags', [])]
        # 不强制要求标签，因为API已经按tag过滤了
        # if required_tags and not any(tag in event_tags for tag in required_tags):
        #     continue
        
        try:
            market = event['markets'][0]
            outcome_prices = json.loads(market.get('outcomePrices', '["0", "0"]'))
            yes_prob = float(outcome_prices[0]) if len(outcome_prices) > 0 else 0
            
            if min_prob <= yes_prob <= max_prob:
                option_text = extract_option_text(event, yes_prob=yes_prob)
                event_id = event['id']
                slug = event.get('slug', '')
                
                url = f"https://polymarket.com/event/{slug}" if slug else f"https://polymarket.com/event/{event_id}"
                
                volume = event.get('volume', 0)
                if volume < 10000:
                    continue
                
                filtered.append({
                    'id': event_id,
                    'title': event.get('title', ''),
                    'slug': slug,
                    'url': url,
                    'probability': yes_prob,
                    'option_text': option_text,
                    'tags': event_tags,
                    'volume': volume,
                    'liquidity': event.get('liquidity', 0),
                })
        except Exception as e:
            print(f"⚠️  Error processing event {event.get('id')}: {e}", file=sys.stderr)
            continue
    
    return filtered

def load_long_term_data():
    """加载Long Term数据"""
    LONG_TERM_DIR.mkdir(parents=True, exist_ok=True)
    long_term_file = LONG_TERM_DIR / "long_term.json"
    
    if not long_term_file.exists():
        return {'events': {}, 'updated_at': None, 'event_count': 0}
    
    with open(long_term_file) as f:
        return json.load(f)

def save_long_term_data(long_term_data):
    """保存Long Term数据"""
    LONG_TERM_DIR.mkdir(parents=True, exist_ok=True)
    long_term_file = LONG_TERM_DIR / "long_term.json"
    
    long_term_data['updated_at'] = datetime.now().isoformat()
    long_term_data['event_count'] = len(long_term_data.get('events', {}))
    
    with open(long_term_file, 'w') as f:
        json.dump(long_term_data, f, indent=2, ensure_ascii=False)

def update_long_term_events(new_events, long_term_data):
    """更新Long Term事件"""
    now = datetime.now()
    now_str = now.strftime('%H:%M')
    
    new_events_lookup = {e['id']: e for e in new_events}
    
    added = 0
    updated = 0
    removed = 0
    
    for event in new_events:
        event_id = event['id']
        
        if event_id not in long_term_data['events']:
            long_term_data['events'][event_id] = {
                **event,
                'current_prob': event['probability'],
                'added_at': now.isoformat(),
                'first_seen': now.isoformat(),
                'peak_prob': event['probability'],
                'last_checked_prob': event['probability'],
                'history': [{
                    'time': now_str,
                    'prob': event['probability'],
                    'reason': 'Added to Long-Term (daily update)'
                }]
            }
            added += 1
            print(f"  ➕ Added: {event['title']} (prob: {event['probability']:.1%})")
        else:
            lt_event = long_term_data['events'][event_id]
            old_prob = lt_event.get('current_prob', event['probability'])
            new_prob = event['probability']
            
            lt_event['current_prob'] = new_prob
            lt_event['probability'] = new_prob
            lt_event['last_checked_prob'] = new_prob
            
            if new_prob > lt_event.get('peak_prob', 0):
                lt_event['peak_prob'] = new_prob
            
            lt_event['option_text'] = event.get('option_text')
            lt_event['url'] = event.get('url', lt_event.get('url'))
            
            if abs(new_prob - old_prob) >= 0.05:
                lt_event.setdefault('history', []).append({
                    'time': now_str,
                    'prob': new_prob,
                    'reason': f'Update: {old_prob:.1%} → {new_prob:.1%}'
                })
            
            updated += 1
    
    to_remove = []
    for event_id in long_term_data['events']:
        if event_id not in new_events_lookup:
            to_remove.append(event_id)
    
    for event_id in to_remove:
        lt_event = long_term_data['events'][event_id]
        print(f"  ➖ Removed (prob < 70%): {lt_event['title']}")
        del long_term_data['events'][event_id]
        removed += 1
    
    return added, updated, removed

def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"💰 Economy Long-Term Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    print("1️⃣  Fetching high-probability events from business + economy tags (70%-99%)...")
    events = fetch_high_prob_events()
    print(f"   Total unique events: {len(events)}\n")
    
    if len(events) == 0:
        print("⚠️  API returned 0 events - keeping existing Long-Term data")
        print("✅ No changes made (preserving data)\n")
        return
    
    print("2️⃣  Filtering and processing events...")
    high_prob_events = filter_and_process_events(events)
    print(f"   {len(high_prob_events)} high-probability events\n")
    
    if high_prob_events:
        print("   Top events:")
        for e in sorted(high_prob_events, key=lambda x: x['volume'], reverse=True)[:5]:
            option = e.get('option_text') or 'Yes/No'
            print(f"   {e['probability']:.1%} | {option} | Vol: {e['volume']:,.0f} | {e['title'][:50]}")
        print()
    
    print("3️⃣  Loading existing Long-Term data...")
    long_term_data = load_long_term_data()
    print(f"   Current events: {len(long_term_data.get('events', {}))}\n")
    
    print("4️⃣  Updating Long-Term events...")
    added, updated, removed = update_long_term_events(high_prob_events, long_term_data)
    print(f"   Added: {added}, Updated: {updated}, Removed: {removed}")
    print(f"   Total after update: {len(long_term_data['events'])}\n")
    
    print("5️⃣  Saving Long-Term data...")
    save_long_term_data(long_term_data)
    print(f"✅ Saved to {LONG_TERM_DIR / 'long_term.json'}\n")
    
    print(f"{'='*60}")
    print(f"✅ Economy Long-Term update complete!")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
