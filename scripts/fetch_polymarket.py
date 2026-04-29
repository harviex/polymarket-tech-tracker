#!/usr/bin/env python3
"""
Polymarket Science Events Tracker
抓取 Polymarket 上与科学相关的预测事件
参考 china-prediction-tracker 实现
"""
import json
import sys
from datetime import datetime
import os

try:
    import requests
except ImportError:
    print("请安装 requests: pip install requests")
    sys.exit(1)

def fetch_polymarket_events():
    """从 Polymarket API 获取科学相关事件（使用 tag_slug 过滤）"""
    # 方法1：使用 tag_slug 过滤（如果支持）
    # 科学相关标签可能包括：science, research, tech, ai, space 等
    science_tags = ['science', 'research', 'tech', 'ai', 'space', 'nasa', 'physics', 'biology']
    
    all_events = []
    
    for tag in science_tags[:3]:  # 先尝试前3个标签
        try:
            url = f"https://gamma-api.polymarket.com/events"
            params = {
                'active': 'true',
                'closed': 'false',
                'tag_slug': tag,
                'limit': 100
            }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            events = response.json()
            
            if isinstance(events, list):
                print(f"  标签 '{tag}': 找到 {len(events)} 个事件")
                all_events.extend(events)
        except Exception as e:
            print(f"  标签 '{tag}' 请求失败: {e}")
    
    # 方法2：如果 tag_slug 不工作，获取所有事件然后过滤
    if not all_events:
        print("  尝试获取所有事件并过滤...")
        try:
            url = "https://gamma-api.polymarket.com/events"
            params = {
                'active': 'true',
                'closed': 'false',
                'limit': 1000
            }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            events = response.json()
            
            if isinstance(events, list):
                print(f"  获取到 {len(events)} 个活跃事件，开始过滤...")
                science_events = [e for e in events if is_science_related(e)]
                print(f"  过滤出 {len(science_events)} 个科学相关事件")
                all_events = science_events
        except Exception as e:
            print(f"❌ API 请求失败: {e}")
            return []
    
    # 去重（基于事件ID）
    seen_ids = set()
    unique_events = []
    for event in all_events:
        eid = event.get('id')
        if eid and eid not in seen_ids:
            seen_ids.add(eid)
            unique_events.append(event)
    
    return unique_events

def is_science_related(event):
    """判断事件是否与科学相关"""
    science_keywords = [
        # 科学领域
        'science', 'research', 'study', 'experiment', 'discovery',
        'physics', 'chemistry', 'biology', 'mathematics', 'astronomy',
        # 科技
        'ai', 'artificial intelligence', 'machine learning', 'deep learning',
        'space', 'nasa', 'spacex', 'rocket', 'mars', 'moon', 'satellite',
        'quantum', 'computer', 'robot', 'automation',
        # 医学
        'medical', 'vaccine', 'drug', 'fda', 'clinical trial',
        'virus', 'pandemic', 'disease', 'cancer', 'alzheimer',
        # 环境
        'climate', 'global warming', 'carbon', 'renewable', 'solar', 'wind energy'
    ]
    
    # 检查事件描述
    text_to_check = ''
    if 'description' in event:
        text_to_check += event['description'].lower() + ' '
    
    # 检查关联的市场问题
    if 'markets' in event:
        for market in event['markets']:
            if 'question' in market:
                text_to_check += market['question'].lower() + ' '
    
    # 检查标签
    if 'tags' in event:
        for tag in event['tags']:
            if isinstance(tag, dict) and 'label' in tag:
                text_to_check += tag['label'].lower() + ' '
    
    # 匹配关键词
    for keyword in science_keywords:
        if keyword in text_to_check:
            return True
    
    return False

def extract_event_data(event):
    """提取事件关键数据（参考 china-prediction-tracker）"""
    event_data = {
        'id': event.get('id', ''),
        'slug': event.get('slug', ''),
        'title': event.get('description', 'Unknown Event'),
        'created_at': event.get('created_at', ''),
        'updated_at': event.get('updated_at', ''),
        'closed': event.get('closed', False),
        'active': event.get('active', False),
        'volume': float(event.get('volume', 0)),
        'liquidity': float(event.get('liquidity', 0)),
        'markets': []
    }
    
    # 提取市场数据
    if 'markets' in event:
        for market in event['markets']:
            market_data = {
                'question': market.get('question', ''),
                'outcomePrices': market.get('outcomePrices', '[]'),
                'volume': float(market.get('volume', 0)),
                'end_date': market.get('endDate', ''),
                'closed': market.get('closed', False)
            }
            
            # 解析概率
            try:
                prices = json.loads(market_data['outcomePrices'])
                if isinstance(prices, list) and len(prices) >= 2:
                    market_data['probability'] = float(prices[0]) * 100
                else:
                    market_data['probability'] = 0
            except:
                market_data['probability'] = 0
            
            event_data['markets'].append(market_data)
    
    return event_data

def main():
    print(f"🔬 Polymarket 科学事件抓取 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("   目标: https://gamma-api.polymarket.com/events")
    print("   筛选: 与科学相关的事件\n")
    
    # 获取科学相关事件
    print("📡 正在获取 Polymarket 事件...")
    events = fetch_polymarket_events()
    
    if not events:
        print("❌ 未获取到任何事件")
        sys.exit(1)
    
    print(f"   找到 {len(events)} 个科学相关事件\n")
    
    # 提取关键数据
    print("📊 正在提取事件数据...")
    event_data_list = []
    
    for event in events:
        data = extract_event_data(event)
        event_data_list.append(data)
    
    # 按交易量排序
    event_data_list.sort(key=lambda x: x['volume'], reverse=True)
    
    # 准备输出
    output = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M UTC'),
        'total_events': len(event_data_list),
        'events': event_data_list
    }
    
    # 保存到文件
    output_path = 'data/events.json'
    os.makedirs('data', exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 数据已保存到 {output_path}")
    print(f"   事件总数: {len(event_data_list)}")
    
    # 显示前几个事件
    if event_data_list:
        print("\n📋 前 5 个事件:")
        for i, event in enumerate(event_data_list[:5], 1):
            print(f"   {i}. {event['title'][:60]}...")
            if event['markets']:
                prob = event['markets'][0]['probability']
                vol = event['volume']
                print(f"      概率: {prob:.1f}% | 交易量: ${vol:,.0f}")
    
    print("\n✅ 完成!")

if __name__ == '__main__':
    main()
