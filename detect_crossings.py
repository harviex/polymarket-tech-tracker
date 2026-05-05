#!/usr/bin/env python3
"""
Polymarket Tech Tracker - 通用阈值跨越检测器
支持多分类：technology, pop-culture, economy
用法：
  python3 detect_crossings.py --category tech        # 检测tech分类
  python3 detect_crossings.py --category culture     # 检测culture分类 (pop-culture tag)
  python3 detect_crossings.py --category economy     # 检测economy分类 (合并business+economy)
  python3 detect_crossings.py --category tech --reset  # 重置并创建基准
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
import urllib.request
import urllib.error

BASE_DIR = Path(__file__).parent
GAMMA_API = "https://gamma-api.polymarket.com/events"

# 阈值线
THRESHOLDS = [0.70, 0.80, 0.90]

# 分类配置
CATEGORY_CONFIG = {
    'tech': {
        'tags': ['tech'],
        'label': 'Technology'
    },
    'culture': {
        'tags': ['pop-culture'],
        'label': 'Culture (Pop-Culture)'
    },
    'economy': {
        'tags': ['business', 'economy'],
        'label': 'Economy (Business + Economy)'
    }
}

def get_category_dir(category):
    """获取分类数据目录"""
    return BASE_DIR / "docs" / "data" / category

def fetch_all_events_by_tag(tag, max_retries=3):
    """从API抓取指定标签的所有事件"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"{GAMMA_API}?tag_slug={tag}&end_date_min={today}&volume_min=10000&limit=1000"
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (compatible; PolymarketTracker/1.0)')
            req.add_header('Accept', 'application/json')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                events = json.loads(response.read())
                return events if isinstance(events, list) else []
        except Exception as e:
            print(f"  Attempt {attempt+1}/{max_retries} failed for tag '{tag}': {e}", file=sys.stderr)
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
    
    print(f"❌ All {max_retries} attempts failed for tag '{tag}'", file=sys.stderr)
    return []

def fetch_all_events(category, config):
    """抓取指定分类的所有事件（可能合并多个tag）"""
    tags = config['tags']
    
    if len(tags) == 1:
        # 单个tag
        return fetch_all_events_by_tag(tags[0])
    else:
        # 多个tag：合并去重
        print(f"  Fetching events from multiple tags: {', '.join(tags)}")
        all_events = {}
        for tag in tags:
            events = fetch_all_events_by_tag(tag)
            print(f"    {tag}: {len(events)} events")
            for event in events:
                event_id = event.get('id')
                if event_id and event_id not in all_events:
                    all_events[event_id] = event
        
        merged = list(all_events.values())
        print(f"    Merged: {len(merged)} unique events")
        return merged

def get_event_probability(event):
    """获取事件的概率（Yes的概率）"""
    try:
        if not event.get('markets'):
            return None
        
        market = event['markets'][0]
        outcome_prices = json.loads(market.get('outcomePrices', '["0", "0"]'))
        
        if len(outcome_prices) >= 2:
            return float(outcome_prices[0])  # Yes 的概率
        return None
    except Exception as e:
        print(f"⚠️  Error getting probability for {event.get('id')}: {e}", file=sys.stderr)
        return None

def load_previous_snapshot(category_dir):
    """加载上一小时的状态"""
    snapshot_file = category_dir / "previous_snapshot.json"
    
    if not snapshot_file.exists():
        return {}
    
    try:
        with open(snapshot_file) as f:
            snapshot = json.load(f)
        
        # 检查是否是新的一天
        snapshot_time = datetime.fromisoformat(snapshot.get('timestamp', ''))
        now = datetime.now()
        
        if snapshot_time.date() < now.date():
            # 前一天的数据，删除
            snapshot_file.unlink()
            print(f"🗑️  Previous day snapshot deleted (storage optimization)")
            return {}
        
        return snapshot.get('events', {})
    except Exception as e:
        print(f"⚠️  Error loading snapshot: {e}", file=sys.stderr)
        return {}

def save_snapshot(category_dir, events):
    """保存当前状态为下一小时的参考"""
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'events': {str(e['id']): {'prob': e['prob']} for e in events}
    }
    
    category_dir.mkdir(parents=True, exist_ok=True)
    snapshot_file = category_dir / "previous_snapshot.json"
    with open(snapshot_file, 'w') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Snapshot saved: {len(events)} events")

def detect_crossings(current_events, previous_snapshot):
    """检测阈值跨越"""
    crossings = []
    now_str = datetime.now().strftime('%H:%M')
    
    for event in current_events:
        event_id = str(event['id'])
        current_prob = event['prob']
        
        # 如果没有上一小时数据，跳过
        if event_id not in previous_snapshot:
            continue
        
        prev_prob = previous_snapshot[event_id]['prob']
        
        # 检测是否跨越任意阈值
        crossed = None
        direction = None
        
        for threshold in sorted(THRESHOLDS, reverse=True):
            prev_above = prev_prob >= threshold
            curr_above = current_prob >= threshold
            
            if not prev_above and curr_above:
                # 向上跨越
                crossed = threshold
                direction = 'up'
                break
            elif prev_above and not curr_above:
                # 向下跨越
                crossed = threshold
                direction = 'down'
                break
        
        if crossed:
            crossings.append({
                'event_id': event['id'],
                'title': event['title'],
                'slug': event.get('slug', ''),
                'prev_prob': prev_prob,
                'curr_prob': current_prob,
                'threshold': crossed,
                'direction': direction,
                'time': now_str,
                'timestamp': datetime.now().isoformat()
            })
            
            arrow = '⬆️' if direction == 'up' else '⬇️'
            print(f"  {arrow} {event['title'][:50]}... {prev_prob:.1%} → {current_prob:.1%} (跨越 {crossed:.0%})")
    
    return crossings

def save_daily_watch_crossings(category_dir, crossings):
    """保存跨越事件到Daily Watch（累加模式）"""
    today = datetime.now().strftime('%Y-%m-%d')
    daily_watch_dir = category_dir / "daily_watch"
    daily_watch_dir.mkdir(parents=True, exist_ok=True)
    watch_file = daily_watch_dir / f"{today}.json"
    
    # 加载现有数据
    if watch_file.exists():
        with open(watch_file) as f:
            daily_data = json.load(f)
    else:
        daily_data = {
            'date': today,
            'created_at': datetime.now().isoformat(),
            'crossings': []
        }
    
    # 添加新跨越事件
    daily_data['crossings'].extend(crossings)
    daily_data['last_updated'] = datetime.now().isoformat()
    daily_data['crossing_count'] = len(daily_data['crossings'])
    
    # 保存
    with open(watch_file, 'w') as f:
        json.dump(daily_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Daily Watch updated: {len(crossings)} new crossings (total: {daily_data['crossing_count']})")

def reset_daily_watch(category_dir, category, config):
    """重置Daily Watch（每天调用）"""
    today = datetime.now().strftime('%Y-%m-%d')
    daily_watch_dir = category_dir / "daily_watch"
    daily_watch_dir.mkdir(parents=True, exist_ok=True)
    watch_file = daily_watch_dir / f"{today}.json"
    
    # 创建空的Daily Watch
    daily_data = {
        'date': today,
        'created_at': datetime.now().isoformat(),
        'crossings': [],
        'crossing_count': 0
    }
    
    with open(watch_file, 'w') as f:
        json.dump(daily_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Daily Watch reset for {today}")
    
    # 同时重置快照
    snapshot_file = category_dir / "previous_snapshot.json"
    if snapshot_file.exists():
        snapshot_file.unlink()
        print("✅ Previous snapshot cleared (will rebuild on next run)")
    
    # 抓取事件并保存基准状态
    print(f"\n2️⃣  Fetching events for baseline ({config['label']})...")
    events = fetch_all_events(category, config)
    current_events = []
    for event in events:
        prob = get_event_probability(event)
        if prob is not None and 0 < prob < 1:
            current_events.append({
                'id': event['id'],
                'title': event.get('title', ''),
                'slug': event.get('slug', ''),
                'prob': prob
            })
    
    print(f"   Saving baseline ({len(current_events)} events)...\n")
    save_snapshot(category_dir, current_events)
    print(f"✅ Reset complete! Next hourly run will detect crossings.\n")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Polymarket Threshold Crossing Detector')
    parser.add_argument('--category', choices=['tech', 'culture', 'economy'], default='tech',
                        help='Category to process (default: tech)')
    parser.add_argument('--reset', action='store_true',
                        help='Reset Daily Watch and save baseline')
    
    args = parser.parse_args()
    
    category = args.category
    config = CATEGORY_CONFIG[category]
    category_dir = get_category_dir(category)
    
    print(f"\n{'='*60}")
    print(f"🔍 Threshold Crossing Detection - {config['label']}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if args.reset:
        print("🔄 RESET MODE: Clearing Daily Watch and saving baseline")
    print(f"{'='*60}\n")
    
    if args.reset:
        # 重置模式
        print("1️⃣  Resetting Daily Watch...")
        reset_daily_watch(category_dir, category, config)
        return
    
    # 正常检测流程
    print(f"1️⃣  Fetching all {category} events...")
    events = fetch_all_events(category, config)
    print(f"   Found {len(events)} events\n")
    
    # 提取概率
    print("2️⃣  Extracting probabilities...")
    current_events = []
    for event in events:
        prob = get_event_probability(event)
        if prob is not None and 0 < prob < 1:  # 排除已结束的事件
            current_events.append({
                'id': event['id'],
                'title': event.get('title', ''),
                'slug': event.get('slug', ''),
                'prob': prob
            })
    
    print(f"   Processing {len(current_events)} valid events\n")
    
    # 加载上一小时状态
    print("3️⃣  Loading previous snapshot...")
    previous_snapshot = load_previous_snapshot(category_dir)
    
    if not previous_snapshot:
        print("   ⚠️  No previous snapshot (first run after reset)")
        print("   Saving current state as baseline for next hour\n")
        save_snapshot(category_dir, current_events)
        return
    
    print(f"   Loaded {len(previous_snapshot)} events from previous hour\n")
    
    # 检测跨越
    print("4️⃣  Detecting threshold crossings...")
    crossings = detect_crossings(current_events, previous_snapshot)
    print(f"   Found {len(crossings)} crossings\n")
    
    # 保存结果
    if crossings:
        print("5️⃣  Saving to Daily Watch...")
        save_daily_watch_crossings(category_dir, crossings)
    else:
        print("5️⃣  No crossings detected - nothing to save")
    
    # 更新快照
    print("\n6️⃣  Updating snapshot for next hour...")
    save_snapshot(category_dir, current_events)
    
    print(f"\n{'='*60}")
    print(f"✅ Detection complete!")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
