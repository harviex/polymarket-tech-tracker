#!/usr/bin/env python3
"""
测试 Polymarket 各 tag 的事件数量
统计：API返回总数、符合筛选条件的事件数
筛选条件：70%-99%概率、交易量>=10K、结束日期>=今日、未关闭
"""
import json
import sys
import subprocess
from datetime import datetime

API_BASE = "https://gamma-api.polymarket.com/events"

def fetch_events(tag, end_date_min=None, volume_min=None, limit=1000):
    """用 curl 获取事件"""
    url = f"{API_BASE}?tag_slug={tag}"
    if end_date_min:
        url += f"&end_date_min={end_date_min}"
    if volume_min:
        url += f"&volume_min={volume_min}"
    url += f"&limit={limit}"
    
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '15', '-H', 'User-Agent: Mozilla/5.0', url],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0 and result.stdout:
            events = json.loads(result.stdout)
            return events if isinstance(events, list) else []
        else:
            print(f"  ❌ curl 失败: {result.stderr[:100]}", file=sys.stderr)
            return []
    except Exception as e:
        print(f"  ❌ 错误: {e}", file=sys.stderr)
        return []

def filter_events(events, min_prob=0.70, max_prob=0.99, min_volume=10000):
    """过滤事件：概率70%-99%、交易量>=10K、结束日期>=今日、未关闭"""
    today = datetime.now().strftime('%Y-%m-%d')
    filtered = []
    
    for event in events:
        # 检查是否关闭
        if event.get('closed', False):
            continue
        
        # 检查结束日期
        end_date = event.get('endDate', '')
        if end_date:
            event_date = end_date[:10]  # 取 YYYY-MM-DD 部分
            if event_date < today:
                continue  # 结束日期已过
        
        # 检查交易量
        volume = event.get('volume', 0)
        if volume < min_volume:
            continue
        
        # 检查概率
        markets = event.get('markets', [])
        if not markets:
            continue
        
        try:
            market = markets[0]
            outcome_prices = json.loads(market.get('outcomePrices', '["0", "0"]'))
            yes_prob = float(outcome_prices[0]) if len(outcome_prices) > 0 else 0
            
            if min_prob <= yes_prob <= max_prob:
                filtered.append(event)
        except:
            continue
    
    return filtered

def test_tag(tag, today):
    """测试一个 tag，返回 (总数, 筛选后数量)"""
    print(f"\n测试 tag: {tag}")
    print("="*70)
    
    # 获取事件
    events = fetch_events(tag, end_date_min=today, volume_min=10000)
    total = len(events)
    print(f"API 返回事件数: {total}")
    
    if total == 0:
        print("  ❌ 无事件返回")
        return 0, 0
    
    # 过滤
    filtered = filter_events(events)
    filtered_count = len(filtered)
    print(f"筛选后事件数: {filtered_count}")
    
    # 显示前几个事件
    if filtered:
        print("\n前3个事件：")
        for i, e in enumerate(filtered[:3]):
            title = e.get('title', '')[:50]
            prob = 0
            try:
                market = e['markets'][0]
                prices = json.loads(market.get('outcomePrices', '["0"]'))
                prob = float(prices[0])
            except:
                pass
            print(f"  {i+1}. [{prob:.1%}] {title}...")
    
    return total, filtered_count

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"测试日期: {today}")
    print("筛选条件: 70%-99%概率、交易量>=10K、结束日期>=今日、未关闭")
    print("="*70)
    
    results = {}
    
    # 测试 pop-culture
    results['pop-culture'] = test_tag('pop-culture', today)
    
    # 测试 business
    results['business'] = test_tag('business', today)
    
    # 测试 economy
    results['economy'] = test_tag('economy', today)
    
    # 总结
    print("\n\n" + "="*70)
    print("总结：")
    print("="*70)
    print(f"{'Tag':<20} {'API返回':>10} {'筛选后':>10}")
    print("-"*70)
    for tag, (total, filtered) in results.items():
        print(f"{tag:<20} {total:>10} {filtered:>10}")
