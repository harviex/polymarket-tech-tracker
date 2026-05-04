#!/usr/bin/env python3
"""
Polymarket Tech Tracker - Two-Board System
抓取策略：
1. 从API抓取：tag=tech, end_date_min=今天, volume_min=10000
2. 过滤概率在70%-99%之间的事件
3. 提取每个选项的关键信息（Yes/No 或选择题选项）
4. 存入 Long Term
5. 每小时检查：如果越过70%/80%/90%线，记录到Daily Watch
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import urllib.request
import urllib.error

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "docs" / "data"
TECH_DIR = DATA_DIR / "technology"
LONG_TERM_DIR = BASE_DIR / "docs" / "data" / "long_term"
DAILY_WATCH_DIR = BASE_DIR / "docs" / "data" / "daily_watch"

GAMMA_API = "https://gamma-api.polymarket.com/events"

# 阈值线
THRESHOLDS = [0.70, 0.80, 0.90]

# 长期榜变动阈值：从峰值下跌超过30%视为变动
LONG_TERM_CHANGE_THRESHOLD = 0.30

def verify_polymarket_url(event_id, slug=None):
    """
    验证 PolyMarket URL 是否可访问
    优先使用 ID，如果失败则尝试 slug
    返回可用的 URL 或 None
    """
    # 优先测试 ID
    url_by_id = f"https://polymarket.com/event/{event_id}"
    try:
        req = urllib.request.Request(url_by_id)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; PolymarketTracker/1.0)')
        req.add_header('Accept', 'text/html')
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return url_by_id
    except (urllib.error.HTTPError, urllib.error.URLError, Exception):
        pass  # ID 不行，尝试 slug
    
    # ID 失败，尝试 slug
    if slug:
        url_by_slug = f"https://polymarket.com/event/{slug}"
        try:
            req = urllib.request.Request(url_by_slug)
            req.add_header('User-Agent', 'Mozilla/5.0 (compatible; PolymarketTracker/1.0)')
            req.add_header('Accept', 'text/html')
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return url_by_slug
        except (urllib.error.HTTPError, urllib.error.URLError, Exception):
            pass  # slug 也不行
    
    # 都不行，返回使用 slug 的 URL（不过滤）
    if slug:
        return f"https://polymarket.com/event/{slug}"
    return url_by_id  # 返回 ID 的 URL（即使可能404）

def fetch_high_prob_events():
    """从API抓取高概率科技事件（70%-99%）"""
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
        print(f"Error fetching events: {e}", file=sys.stderr)
        return []

def get_market_info(market):
    """提取市场信息：概率和选项"""
    try:
        outcome_prices = json.loads(market.get('outcomePrices', '["0", "0"]'))
        outcomes = json.loads(market.get('outcomes', '["Yes", "No"]'))
        
        yes_prob = float(outcome_prices[0]) if len(outcome_prices) > 0 else 0
        no_prob = float(outcome_prices[1]) if len(outcome_prices) > 1 else 0
        
        return {
            'yes_prob': yes_prob,
            'no_prob': no_prob,
            'outcomes': outcomes,
            'question': market.get('question', '')
        }
    except Exception as e:
        print(f"Error parsing market: {e}", file=sys.stderr)
        return None

def extract_option_text(event):
    """提取事件的关键选项信息"""
    markets = event.get('markets', [])
    if not markets:
        return None
    
    # 如果有多个子市场（选择题），找概率最高的那个
    if len(markets) > 1:
        best_market = None
        best_prob = 0
        
        for market in markets:
            try:
                outcome_prices = json.loads(market.get('outcomePrices', '["0", "0"]'))
                yes_prob = float(outcome_prices[0])
                if yes_prob > best_prob:
                    best_prob = yes_prob
                    best_market = market
            except:
                pass
        
        if best_market:
            # 从问题的question中提取关键信息
            question = best_market.get('question', '')
            return extract_key_info(question)
    
    # 单个市场（Yes/No类型）
    # 检查是Yes概率高还是No概率高
    try:
        outcome_prices = json.loads(markets[0].get('outcomePrices', '["0", "0"]'))
        yes_prob = float(outcome_prices[0])
        no_prob = float(outcome_prices[1]) if len(outcome_prices) > 1 else 0
        
        if yes_prob > no_prob:
            return "Yes"
        else:
            return "No"
    except:
        return "Yes/No"

def extract_key_info(question):
    """从问题文本中提取关键信息"""
    # 去掉前缀，提取关键部分
    import re
    
    # 例如："SpaceX IPO closing market cap above $1T?" -> "$1T"
    # 或者："Will Google Gemini score at least 40% on..." -> "40%"
    
    # 尝试提取 $ 后面的数字和单位
    match = re.search(r'\$[\d.]+[BMKT]?', question)
    if match:
        return match.group(0)
    
    # 尝试提取百分比
    match = re.search(r'\d+%', question)
    if match:
        return match.group(0)
    
    # 尝试提取 "above XXX" 或 "below XXX"
    match = re.search(r'(?:above|below)\s+([\w\d\s$%.]+)\?', question, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # 默认返回问题本身（截断）
    return question[:50]

def filter_and_process_events(events, min_prob=0.70, max_prob=0.99):
    """过滤并处理高概率事件"""
    filtered = []
    for event in events:
        if not event.get('markets'):
            continue
        
        # 获取第一个市场的概率（主市场）
        info = get_market_info(event['markets'][0])
        if not info:
            continue
        
        prob = info['yes_prob']
        
        # 过滤概率范围
        if min_prob <= prob <= max_prob:
            # 提取选项信息
            option_text = extract_option_text(event)
            
            # 验证 PolyMarket URL
            event_id = event['id']
            slug = event.get('slug', '')
            verified_url = verify_polymarket_url(event_id, slug)
            
            filtered.append({
                'id': event_id,
                'title': event.get('title', ''),
                'slug': slug,
                'url': verified_url,  # 保存验证后的URL
                'probability': prob,
                'option_text': option_text,  # 新增：对应的选项内容
                'tags': [t['slug'] for t in event.get('tags', [])],
                'markets': event.get('markets', []),
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

def load_long_term_data():
    """加载Long Term数据"""
    LONG_TERM_DIR.mkdir(parents=True, exist_ok=True)
    long_term_file = LONG_TERM_DIR / "long_term.json"
    
    if not long_term_file.exists():
        return {'events': {}, 'updated_at': None}
    
    with open(long_term_file) as f:
        return json.load(f)

def save_long_term_data(long_term_data):
    """保存Long Term数据"""
    LONG_TERM_DIR.mkdir(parents=True, exist_ok=True)
    long_term_file = LONG_TERM_DIR / "long_term.json"
    
    long_term_data['updated_at'] = datetime.now().isoformat()
    with open(long_term_file, 'w') as f:
        json.dump(long_term_data, f, indent=2, ensure_ascii=False)

def update_long_term_events(new_events, long_term_data):
    """更新Long Term事件"""
    now = datetime.now()
    now_str = now.strftime('%H:%M')
    changed_events = []
    
    # 构建新事件查找表
    new_events_lookup = {e['id']: e for e in new_events}
    
    # 1. 添加新的高概率事件到Long Term
    for event in new_events:
        event_id = event['id']
        if event_id not in long_term_data['events']:
            # 新事件
            long_term_data['events'][event_id] = {
                **event,
                'current_prob': event['probability'],  # 添加 current_prob 字段
                'added_at': now.isoformat(),
                'first_seen': now.isoformat(),
                'peak_prob': event['probability'],
                'last_checked_prob': event['probability'],
                'history': [{
                    'time': now_str,
                    'prob': event['probability'],
                    'reason': 'Added to Long-Term (high probability)'
                }]
            }
            changed_events.append({
                'id': event_id,
                'title': event['title'],
                'probability': event['probability'],
                'change': 'added'
            })
            print(f"  ➕ Added to Long-Term: {event['title']} (prob: {event['probability']:.1%})")
    
    # 2. 更新已存在的事件
    for event_id, lt_event in list(long_term_data['events'].items()):
        if event_id in new_events_lookup:
            # 事件仍在高概率列表中
            new_event = new_events_lookup[event_id]
            old_prob = lt_event['current_prob']
            new_prob = new_event['probability']
            
            # 更新概率
            lt_event['current_prob'] = new_prob
            lt_event['probability'] = new_prob
            lt_event['last_checked_prob'] = new_prob
            
            # 更新峰值概率
            if new_prob > lt_event.get('peak_prob', 0):
                lt_event['peak_prob'] = new_prob
            
            # 更新选项文本（可能变化）
            lt_event['option_text'] = new_event.get('option_text')
            
            # 如果概率变化超过5%，记录历史
            if abs(new_prob - old_prob) >= 0.05:
                lt_event['history'].append({
                    'time': now_str,
                    'prob': new_prob,
                    'reason': f'Update: {old_prob:.1%} → {new_prob:.1%}'
                })
        else:
            # 事件不在高概率列表中（概率<70%）
            # 从Long Term删除，记录到Daily Watch
            print(f"  ➖ Removed from Long-Term (prob < 70%): {lt_event['title']}")
            changed_events.append({
                'id': event_id,
                'title': lt_event['title'],
                'probability': lt_event.get('current_prob', 0),
                'change': 'removed_low_prob'
            })
            del long_term_data['events'][event_id]
    
    return changed_events

def check_threshold_crossings(new_events, long_term_data):
    """检查是否越过阈值线（70%/80%/90%）"""
    crossings = []
    now_str = datetime.now().strftime('%H:%M')
    
    for event in new_events:
        event_id = event['id']
        current_prob = event['probability']
        
        # 如果这个事件在Long Term中
        if event_id in long_term_data['events']:
            lt_event = long_term_data['events'][event_id]
            
            # 检查是否越过任何阈值线
            for threshold in THRESHOLDS:
                # 获取上次概率
                last_prob = lt_event.get('last_checked_prob', current_prob)
                
                # 检查是否越过阈值
                last_above = last_prob >= threshold
                current_above = current_prob >= threshold
                
                if not last_above and current_above:
                    # 向上越过
                    crossings.append({
                        'event_id': event_id,
                        'title': event['title'],
                        'threshold': threshold,
                        'direction': 'up',
                        'prob': current_prob,
                        'time': now_str
                    })
                    print(f"  ⬆️  Crossed UP {threshold:.0%}: {event['title']} ({current_prob:.1%})")
                
                elif last_above and not current_above:
                    # 向下越过
                    crossings.append({
                        'event_id': event_id,
                        'title': event['title'],
                        'threshold': threshold,
                        'direction': 'down',
                        'prob': current_prob,
                        'time': now_str
                    })
                    print(f"  ⬇️  Crossed DOWN {threshold:.0%}: {event['title']} ({current_prob:.1%})")
                
                # 更新last_checked_prob
                lt_event['last_checked_prob'] = current_prob
    
    return crossings

def save_daily_watch_events(crossings, removed_events):
    """保存变动事件到Daily Watch"""
    today = datetime.now().strftime('%Y-%m-%d')
    DAILY_WATCH_DIR.mkdir(parents=True, exist_ok=True)
    watch_file = DAILY_WATCH_DIR / f"{today}.json"
    
    # 加载或创建Daily Watch
    if watch_file.exists():
        with open(watch_file) as f:
            daily_data = json.load(f)
    else:
        daily_data = {'date': today, 'events': {}}
    
    # 添加越过阈值的事件
    for crossing in crossings:
        event_id = crossing['event_id']
        if event_id not in daily_data['events']:
            daily_data['events'][event_id] = {
                'id': event_id,
                'title': crossing['title'],
                'tags': [],
                'first_seen': datetime.now().isoformat(),
                'history': [],
                'current_prob': crossing['prob']
            }
        
        daily_data['events'][event_id]['history'].append({
            'time': crossing['time'],
            'prob': crossing['prob'],
            'threshold': crossing['threshold'],
            'direction': crossing['direction'],
            'reason': f"Crossed {crossing['direction']} {crossing['threshold']:.0%}"
        })
    
    # 添加被移除的事件
    for event in removed_events:
        if event['change'] == 'removed_low_prob':
            event_id = event['id']
            if event_id not in daily_data['events']:
                daily_data['events'][event_id] = {
                    'id': event_id,
                    'title': event['title'],
                    'tags': [],
                    'first_seen': datetime.now().isoformat(),
                    'history': [],
                    'current_prob': event['probability']
                }
            
            daily_data['events'][event_id]['history'].append({
                'time': datetime.now().strftime('%H:%M'),
                'prob': event['probability'],
                'reason': 'Removed from Long-Term (prob < 70%)'
            })
    
    # 保存
    with open(watch_file, 'w') as f:
        json.dump(daily_data, f, indent=2, ensure_ascii=False)

def generate_output(long_term_data):
    """生成输出JSON"""
    # 生成Daily Watch summaries
    today = datetime.now().strftime('%Y-%m-%d')
    DAILY_WATCH_DIR.mkdir(parents=True, exist_ok=True)
    watch_file = DAILY_WATCH_DIR / f"{today}.json"
    
    daily_summaries = []
    if watch_file.exists():
        with open(watch_file) as f:
            daily_data = json.load(f)
            # 生成tag summaries（简化，实际应该按标签分组）
            events_list = list(daily_data['events'].values())
            daily_summaries = [{
                'tag': 'tech',
                'tag_display': 'TECH',
                'event_count': len(events_list),
                'events': events_list
            }]
    
    return {
        'category': 'technology',
        'updated_at': datetime.now().isoformat(),
        'daily_watch_summaries': daily_summaries,
        'long_term_data': {
            'event_count': len(long_term_data.get('events', {})),
            'events': list(long_term_data.get('events', {}).values()),
            'updated_at': long_term_data.get('updated_at')
        }
    }

def main():
    print("🚀 Starting fetch_events.py (Two-Board System)...")
    
    # 1. 从API抓取事件
    print("\n📡 Fetching high-probability events from Polymarket...")
    events = fetch_high_prob_events()
    print(f"   Fetched {len(events)} total events (after API filtering)")
    
    # 2. 过滤高概率事件（70%-99%）
    print("\n🔍 Filtering high-probability events (70%-99%)...")
    high_prob_events = filter_and_process_events(events)
    print(f"   Found {len(high_prob_events)} high-probability events")
    
    # 显示找到的事件
    print("\n📊 Events found:")
    for e in sorted(high_prob_events, key=lambda x: x['volume'], reverse=True):
        option = e.get('option_text') or 'Yes/No'
        print(f"   {e['probability']:.1%} | {option} | Vol: {e['volume']:,.0f} | {e['title'][:50]}")
    
    # 3. 加载Long Term数据
    print("\n📂 Loading Long-Term data...")
    long_term_data = load_long_term_data()
    print(f"   Current Long-Term events: {len(long_term_data.get('events', {}))}")
    
    # 4. 更新Long Term事件
    print("\n🔄 Updating Long-Term events...")
    changed_events = update_long_term_events(high_prob_events, long_term_data)
    
    # 5. 检查阈值跨越
    print("\n📊 Checking threshold crossings (70%/80%/90%)...")
    crossings = check_threshold_crossings(high_prob_events, long_term_data)
    
    # 6. 保存Long Term数据
    save_long_term_data(long_term_data)
    print(f"✅ Long-Term updated: {len(long_term_data['events'])} events")
    
    # 7. 保存变动到Daily Watch
    removed_events = [e for e in changed_events if e['change'] == 'removed_low_prob']
    if crossings or removed_events:
        print(f"\n📝 Saving changes to Daily Watch...")
        save_daily_watch_events(crossings, removed_events)
        print(f"   Crossings: {len(crossings)}, Removed: {len(removed_events)}")
    
    # 8. 生成输出
    print("\n📄 Generating output...")
    output = generate_output(long_term_data)
    
    TECH_DIR.mkdir(parents=True, exist_ok=True)
    output_file = TECH_DIR / "events.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved to {output_file}")
    
    print("\n🎉 Done!")

if __name__ == '__main__':
    main()
