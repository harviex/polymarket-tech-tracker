#!/usr/bin/env python3
"""
Polymarket 榜单迁移脚本 - 正确版本
逻辑：
1. 每小时: 1小时榜自动更新 (在 fetch_events.py 中)
2. 每小时: 1小时榜的事件下一个小时自动进入每日榜
3. 每天01:00: 昨日每日榜全部转入长期榜
4. 每次更新: 检查长期榜，变动事件退出并回到1小时榜
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

# 长期榜变动阈值：如果事件从高点跌落到低点，视为变动
# 例如：从90%跌到60%，或者从80%跌到60%
LONG_TERM_CHANGE_THRESHOLD = 0.30  # 下跌超过30%视为变动

def load_json(file_path):
    """加载JSON文件"""
    if not file_path.exists():
        return None
    try:
        with open(file_path) as f:
            return json.load(f)
    except:
        return None

def save_json(file_path, data):
    """保存JSON文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def migrate_hour_to_daily():
    """
    每小时执行: 将1小时榜事件转入每日榜
    这个逻辑实际上在 fetch_events.py 的 update_watch_events() 中已经实现
    每日榜就是 daily_watch/YYYY-MM-DD.json 的累积
    """
    print("ℹ️  Hour→Daily migration happens automatically in fetch_events.py")
    pass

def migrate_daily_to_long_term():
    """
    每天01:00执行: 将昨天的每日榜全部转入长期榜
    """
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 加载昨天的每日榜
    daily_file = DAILY_WATCH_DIR / f"{yesterday}.json"
    if not daily_file.exists():
        print(f"⚠️  No daily watch data for {yesterday}")
        return
    
    daily_data = load_json(daily_file)
    if not daily_data:
        return
    
    # 加载长期榜
    LONG_TERM_DIR.mkdir(parents=True, exist_ok=True)
    long_term_file = LONG_TERM_DIR / "long_term.json"
    long_term_data = load_json(long_term_file) or {
        'events': {},
        'updated_at': None
    }
    
    migrated_count = 0
    
    # 将昨天每日榜的所有事件转入长期榜
    for event_id, event in daily_data.get('events', {}).items():
        if event_id not in long_term_data['events']:
            long_term_data['events'][event_id] = {
                'id': event_id,
                'title': event.get('title'),
                'tags': event.get('tags', []),
                'added_at': datetime.now().isoformat(),
                'first_seen': event.get('first_seen'),
                'history': event.get('history', []),
                'current_prob': event.get('current_prob'),
                'peak_prob': max((h['prob'] for h in event.get('history', [])), default=event.get('current_prob', 0)),
                'source_date': yesterday
            }
            migrated_count += 1
            print(f"  ➡️  Added to long-term: {event.get('title')} (prob: {event.get('current_prob', 0):.1%})")
    
    # 更新长期榜
    long_term_data['updated_at'] = datetime.now().isoformat()
    long_term_data['last_migration'] = yesterday
    save_json(long_term_file, long_term_data)
    
    print(f"✅ Long-term board updated: {migrated_count} events migrated from {yesterday}")
    print(f"   Total long-term events: {len(long_term_data['events'])}")

def check_long_term_changes(current_events):
    """
    每次更新时执行: 检查长期榜事件是否发生变动
    如果事件从高点大幅下跌（如90%→60%），退出长期榜，回到1小时榜
    返回需要退出长期榜的事件列表
    """
    LONG_TERM_DIR.mkdir(parents=True, exist_ok=True)
    long_term_file = LONG_TERM_DIR / "long_term.json"
    long_term_data = load_json(long_term_file)
    
    if not long_term_data:
        return []
    
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
            
            # 标记为需要退出
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
        save_json(long_term_file, long_term_data)
        print(f"✅ Removed {len(events_to_remove)} events from long-term board")
    
    return exited_events

def main():
    print("🚀 Starting board migration script...")
    
    # 根据当前时间决定执行哪个操作
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    
    # 每天01:00执行长期榜迁移
    if current_hour == 1 and current_minute < 5:
        print("\n📋 Migrating daily → long-term (01:00)...")
        migrate_daily_to_long_term()
    else:
        print(f"⏸️  No migration needed at {current_hour:02d}:{current_minute:02d}")
        print("   Daily→Long-term migration runs at 01:00")
    
    print("\n💡 Note: Hour→Daily migration happens automatically in fetch_events.py")
    print("💡 Note: Long-term change detection happens in fetch_events.py")
    
    print("\n🎉 Done!")

if __name__ == '__main__':
    main()
