#!/usr/bin/env python3
"""
统计Polymarket中所有科技事件
通过分页获取所有事件，按标题关键词过滤
"""
import json
import time
from collections import Counter

GAMMA_API = "https://gamma-api.polymarket.com/events"

# 科技相关关键词
TECH_KEYWORDS = [
    'ai', 'artificial intelligence', 'machine learning', 'deep learning',
    'tech', 'technology', 'software', 'hardware', 'computer', 'internet',
    'crypto', 'blockchain', 'bitcoin', 'ethereum', 'nft', 'web3',
    'spacex', 'tesla', 'apple', 'google', 'microsoft', 'amazon', 'meta',
    'nvidia', 'amd', 'intel', 'quantum', 'robot', 'automation',
    'data', 'cloud', 'mobile', 'smartphone', 'cyber', 'security',
    'elon musk', 'openai', 'anthropic', 'claude', 'gpt', 'gemini',
    'ipo', 'startup', 'unicorn', 'venture', 'silicon valley',
    'science', 'research', 'innovation', 'digital', 'algorithm'
]

def fetch_events(offset=0, limit=1000):
    """获取事件数据"""
    import urllib.request
    
    url = f"{GAMMA_API}?offset={offset}&limit={limit}"
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; PolymarketTracker/1.0)')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error fetching offset={offset}: {e}")
        return []

def is_tech_event(event):
    """判断是否为科技事件（通过标题关键词）"""
    title = event.get('title', '').lower()
    
    # 检查标题是否包含科技关键词
    for keyword in TECH_KEYWORDS:
        if keyword in title:
            return True
    
    # 检查category
    category = event.get('category', '').lower()
    if any(kw in category for kw in ['tech', 'crypto', 'science']):
        return True
    
    return False

def get_probability(event):
    """获取事件概率"""
    try:
        if not event.get('markets'):
            return None
        
        market = event['markets'][0]
        outcome_prices = json.loads(market.get('outcomePrices', '["0", "0"]'))
        return float(outcome_prices[0])
    except:
        return None

def main():
    print("🚀 开始统计Polymarket科技事件...")
    print("=" * 60)
    
    all_events = {}
    offset = 0
    batch_size = 500
    max_empty = 3  # 连续3次返回空则停止
    
    empty_count = 0
    
    while empty_count < max_empty:
        print(f"📡 获取 offset={offset} 的事件...")
        events = fetch_events(offset, batch_size)
        
        if not events:
            empty_count += 1
            print(f"  返回空结果 ({empty_count}/{max_empty})")
            offset += batch_size
            time.sleep(1)
            continue
        
        empty_count = 0  # 重置
        
        for event in events:
            event_id = event['id']
            if event_id not in all_events:
                all_events[event_id] = event
        
        print(f"  获取 {len(events)} 个事件，总计 {len(all_events)} 个唯一事件")
        
        offset += batch_size
        time.sleep(0.5)  # 避免请求过快
    
    print(f"\n✅ 共获取 {len(all_events)} 个唯一事件")
    print("=" * 60)
    
    # 过滤科技事件
    tech_events = []
    for event_id, event in all_events.items():
        if is_tech_event(event):
            prob = get_probability(event)
            tech_events.append({
                'id': event_id,
                'title': event.get('title', ''),
                'probability': prob,
                'category': event.get('category'),
                'seriesSlug': event.get('seriesSlug')
            })
    
    print(f"\n📊 科技事件统计：")
    print(f"=" * 60)
    print(f"科技事件总数: {len(tech_events)}")
    
    # 统计概率>60%的
    over_60 = [e for e in tech_events if e['probability'] and e['probability'] >= 0.60]
    print(f"概率≥60%: {len(over_60)} ({len(over_60)/len(tech_events)*100:.1f}%)")
    
    over_70 = [e for e in tech_events if e['probability'] and e['probability'] >= 0.70]
    print(f"概率≥70%: {len(over_70)} ({len(over_70)/len(tech_events)*100:.1f}%)")
    
    over_80 = [e for e in tech_events if e['probability'] and e['probability'] >= 0.80]
    print(f"概率≥80%: {len(over_80)} ({len(over_80)/len(tech_events)*100:.1f}%)")
    
    over_90 = [e for e in tech_events if e['probability'] and e['probability'] >= 0.90]
    print(f"概率≥90%: {len(over_90)} ({len(over_90)/len(tech_events)*100:.1f}%)")
    
    # 按category统计
    cat_counter = Counter(e['category'] for e in tech_events if e['category'])
    print(f"\n按category统计（TOP 20）:")
    for cat, cnt in cat_counter.most_common(20):
        print(f"  {cat}: {cnt}个")
    
    # 显示概率最高的科技事件
    print(f"\n🏆 概率最高的科技事件（TOP 20）:")
    print("=" * 60)
    sorted_events = sorted([e for e in tech_events if e['probability']], 
                         key=lambda x: x['probability'], reverse=True)[:20]
    
    for i, e in enumerate(sorted_events, 1):
        print(f"{i}. {e['title'][:70]}... ({e['probability']:.1%})")
        print(f"   ID: {e['id']}, Category: {e['category']}")
    
    # 保存结果到文件
    output_file = '/tmp/tech_events.json'
    with open(output_file, 'w') as f:
        json.dump(tech_events, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 结果已保存到: {output_file}")

if __name__ == '__main__':
    main()
