#!/usr/bin/env python3
"""
Polymarket Tech Tracker - 阈值跨越检测器
每天12点清空Daily Watch，每小时检测是否跨越70%/80%/90%阈值线
只记录跨越事件，没有变化不记录
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import urllib.request
import urllib.error

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "docs" / "data"
DAILY_WATCH_DIR = DATA_DIR / "daily_watch"
SNAPSHOT_FILE = DATA_DIR / "previous_snapshot.json"

GAMMA_API = "https://gamma-api.polymarket.com/events"

# 阈值线
THRESHOLDS = [0.70, 0.80, 0.90]

def fetch_all_tech_events():
    """从API抓取所有科技事件（不过滤概率）"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"{GAMMA_API}?tag_slug=tech&end_date_min={today}&volume_min=10000&limit=1000"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; PolymarketTracker/1.0)')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            events = json.loads(response.read())
            return events if isinstance(events, list) else []
    except Exception as e:
        print(f"❌ Error fetching events: {e}", file=sys.stderr)
        return []

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

def load_previous_snapshot():
    """加载上一小时的状态（只返回events部分）"""
    if not SNAPSHOT_FILE.exists():
        return {}
    
    try:
        with open(SNAPSHOT_FILE) as f:
            snapshot = json.load(f)
            return snapshot.get('events', {})
    except Exception as e:
        print(f"⚠️  Error loading snapshot: {e}", file=sys.stderr)
        return {}

def save_snapshot(events):
    """保存当前状态为下一小时的参考"""
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'events': {str(e['id']): {'prob': e['prob']} for e in events}
    }
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_FILE, 'w') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Snapshot saved: {len(events)} events")

def detect_crossings(current_events, previous_snapshot):
    """
    检测阈值跨越
    返回：crossings 列表
    """
    crossings = []
    now_str = datetime.now().strftime('%H:%M')
    
    for event in current_events:
        event_id = str(event['id'])
        current_prob = event['prob']
        
        # 如果没有上一小时数据，跳过（首次运行或12点重置后）
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

def save_daily_watch_crossings(crossings):
    """保存跨越事件到Daily Watch（累加模式）"""
    today = datetime.now().strftime('%Y-%m-%d')
    DAILY_WATCH_DIR.mkdir(parents=True, exist_ok=True)
    watch_file = DAILY_WATCH_DIR / f"{today}.json"
    
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

def reset_daily_watch():
    """重置Daily Watch（每天12点调用）"""
    today = datetime.now().strftime('%Y-%m-%d')
    DAILY_WATCH_DIR.mkdir(parents=True, exist_ok=True)
    watch_file = DAILY_WATCH_DIR / f"{today}.json"
    
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
    
    # 同时重置快照（12点后首次运行需要重新建立基准）
    if SNAPSHOT_FILE.exists():
        SNAPSHOT_FILE.unlink()
        print("✅ Previous snapshot cleared (will rebuild on next run)")

def main():
    """主函数"""
    # 检查是否有 --reset 参数
    reset_mode = '--reset' in sys.argv
    
    print(f"\n{'='*60}")
    print(f"🔍 Threshold Crossing Detection - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if reset_mode:
        print("🔄 RESET MODE: Clearing Daily Watch and saving baseline")
    print(f"{'='*60}\n")
    
    if reset_mode:
        # 重置模式：清空Daily Watch + 保存基准状态
        print("1️⃣  Resetting Daily Watch...")
        reset_daily_watch()
        
        print("\n2️⃣  Fetching events for baseline...")
        events = fetch_all_tech_events()
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
        save_snapshot(current_events)
        print("✅ Reset complete! Next hourly run will detect crossings.\n")
        return
    
    # 正常检测流程
    print("1️⃣  Fetching all tech events...")
    events = fetch_all_tech_events()
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
    previous_snapshot = load_previous_snapshot()
    
    if not previous_snapshot:
        print("   ⚠️  No previous snapshot (first run after reset)")
        print("   Saving current state as baseline for next hour\n")
        save_snapshot(current_events)
        return
    
    print(f"   Loaded {len(previous_snapshot)} events from previous hour\n")
    
    # 检测跨越
    print("4️⃣  Detecting threshold crossings...")
    crossings = detect_crossings(current_events, previous_snapshot)
    print(f"   Found {len(crossings)} crossings\n")
    
    # 保存结果
    if crossings:
        print("5️⃣  Saving to Daily Watch...")
        save_daily_watch_crossings(crossings)
    else:
        print("5️⃣  No crossings detected - nothing to save")
    
    # 更新快照
    print("\n6️⃣  Updating snapshot for next hour...")
    save_snapshot(current_events)
    
    print(f"\n{'='*60}")
    print(f"✅ Detection complete!")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
