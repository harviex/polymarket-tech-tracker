#!/usr/bin/env python3
"""
Polymarket Tech Tracker - Long-Term Updater (Simplified)
每天00:00运行：抓取高概率事件（70%-99%）并更新Long-Term数据
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
LONG_TERM_DIR = BASE_DIR / "docs" / "data" / "long_term"

GAMMA_API = "https://gamma-api.polymarket.com/events"

def fetch_high_prob_events(max_retries=3):
    """用curl抓取高概率科技事件（70%-99%）"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"{GAMMA_API}?tag_slug=tech&end_date_min={today}&volume_min=10000&limit=1000"
    
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
            print(f"  Attempt {attempt+1}/{max_retries} failed: {e}", file=sys.stderr)
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
    
    print(f"❌ All {max_retries} attempts failed", file=sys.stderr)
    return []

def extract_option_text(event):
    """提取事件的关键选项信息（简化版）"""
    markets = event.get('markets', [])
    if not markets:
        return None
    
    import re
    
    # 获取第一个市场
    main_market = markets[0]
    
    # 尝试提取 $金额
    question = main_market.get('question', '')
    match = re.search(r'\$[0-9.]+[BMKT]?', question)
    if match:
        return match.group(0)
    
    # 尝试提取百分比
    match = re.search(r'[0-9]+%', question)
    if match:
        return match.group(0)
    
    # 尝试提取 reach ___ Score
    match = re.search(r'reach\s+([0-9]+)', question, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # 默认返回前50字符
    return question[:50].strip()

def filter_and_process_events(events, min_prob=0.70, max_prob=1.0, required_tags=None):
    """过滤并处理高概率事件（包含100%已结束事件）
    
    Args:
        events: 原始事件列表
        min_prob: 最小概率（默认0.70）
        max_prob: 最大概率（默认1.0，即不过滤100%）
        required_tags: 必需的标签列表（如['tech']），None表示不检查标签
    """
    if required_tags is None:
        required_tags = ['tech']  # 默认要求tech标签
    
    filtered = []
    for event in events:
        if not event.get('markets'):
            continue
        
        # 检查是否包含必需标签
        event_tags = [t.get('slug', '') for t in event.get('tags', [])]
        if required_tags and not any(tag in event_tags for tag in required_tags):
            continue  # 不包含必需标签，跳过
        
        try:
            market = event['markets'][0]
            outcome_prices = json.loads(market.get('outcomePrices', '["0", "0"]'))
            yes_prob = float(outcome_prices[0]) if len(outcome_prices) > 0 else 0
            
            if min_prob <= yes_prob <= max_prob:
                option_text = extract_option_text(event)
                event_id = event['id']
                slug = event.get('slug', '')
                
                # 不验证URL，直接构建
                url = f"https://polymarket.com/event/{slug}" if slug else f"https://polymarket.com/event/{event_id}"
                
                filtered.append({
                    'id': event_id,
                    'title': event.get('title', ''),
                    'slug': slug,
                    'url': url,
                    'probability': yes_prob,
                    'option_text': option_text,
                    'tags': event_tags,
                    'volume': event.get('volume',0),
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
    
    # 构建新事件查找表
    new_events_lookup = {e['id']: e for e in new_events}
    
    # 统计
    added = 0
    updated = 0
    removed = 0
    
    # 1. 添加或更新事件
    for event in new_events:
        event_id = event['id']
        
        if event_id not in long_term_data['events']:
            # 新事件
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
            # 更新已存在的事件
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
    
    # 2. 移除不在新列表中的事件（概率<70%）
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
    print(f"🔄 Long-Term Daily Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # 1. 抓取高概率事件
    print("1️⃣  Fetching high-probability events (70%-99%)...")
    events = fetch_high_prob_events()
    print(f"   Found {len(events)} events from API\n")
    
    # 🔒 关键检查：如果API返回空，保留现有数据
    if len(events) == 0:
        print("⚠️  API returned 0 events - keeping existing Long-Term data")
        print("✅ No changes made (preserving data)\n")
        return
    
    # 2. 过滤和处理
    print("2️⃣  Filtering and processing events...")
    high_prob_events = filter_and_process_events(events)
    print(f"   {len(high_prob_events)} high-probability events\n")
    
    if high_prob_events:
        print("   Top events:")
        for e in sorted(high_prob_events, key=lambda x: x['volume'], reverse=True)[:5]:
            option = e.get('option_text') or 'Yes/No'
            print(f"   {e['probability']:.1%} | {option} | Vol: {e['volume']:,.0f} | {e['title'][:50]}")
        print()
    
    # 3. 加载现有Long-Term数据
    print("3️⃣  Loading existing Long-Term data...")
    long_term_data = load_long_term_data()
    print(f"   Current events: {len(long_term_data.get('events', {}))}\n")
    
    # 4. 更新事件
    print("4️⃣  Updating Long-Term events...")
    added, updated, removed = update_long_term_events(high_prob_events, long_term_data)
    print(f"   Added: {added}, Updated: {updated}, Removed: {removed}")
    print(f"   Total after update: {len(long_term_data['events'])}\n")
    
    # 5. 保存
    print("5️⃣  Saving Long-Term data...")
    save_long_term_data(long_term_data)
    print(f"✅ Saved to {LONG_TERM_DIR / 'long_term.json'}\n")
    
    print(f"{'='*60}")
    print(f"✅ Long-Term update complete!")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
