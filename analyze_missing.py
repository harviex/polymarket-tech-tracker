#!/usr/bin/env python3
"""
分析：符合Long-Term规则的事件，哪些没被收录？
规则：70%-99%概率、交易量≥10K、结束时间≥今日、有tech标签
"""
import json
import subprocess
from datetime import datetime

def fetch_all_events():
    """从API获取所有科技事件"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://gamma-api.polymarket.com/events?tag_slug=tech&end_date_min={today}&volume_min=10000&limit=1000"
    
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '10', url],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"❌ API调用失败: {e}")
    return []

def load_long_term():
    """加载当前Long-Term数据"""
    try:
        with open('docs/data/long_term/long_term.json') as f:
            return json.load(f)
    except:
        return {}

def analyze():
    print(f"\n{'='*60}")
    print(f"🔍 分析符合规则但未被收录的事件")
    print(f"{'='*60}\n")
    
    # 1. 获取API数据
    print("1️⃣ 从API获取事件...")
    api_events = fetch_all_events()
    print(f"   API返回: {len(api_events)} 个事件\n")
    
    # 2. 加载当前Long-Term
    print("2️⃣ 加载当前Long-Term数据...")
    lt_data = load_long_term()
    lt_events = lt_data.get('events', {})
    print(f"   当前收录: {len(lt_events)} 个事件\n")
    
    # 3. 筛选符合条件的事件
    print("3️⃣ 筛选符合规则的事件...")
    print(f"   规则: 70%-99%概率、交易量≥10K、结束时间≥今日、有tech标签\n")
    
    today = datetime.now().strftime('%Y-%m-%d')
    qualified = []
    lt_ids = set(lt_events.keys())
    
    for event in api_events:
        try:
            # 检查tech标签
            tags = [t.get('slug', '') for t in event.get('tags', [])]
            if 'tech' not in tags:
                continue
            
            # 检查市场数据
            markets = event.get('markets', [])
            if not markets:
                continue
            market = markets[0]
            
            # 检查概率
            prices = json.loads(market.get('outcomePrices', '[0,0]'))
            if len(prices) < 2:
                continue
            prob = float(prices[0])
            if not (0.70 <= prob < 1.0):  # 70%-99%，排除100%
                continue
            
            # 检查交易量
            volume = float(market.get('volume', 0))
            if volume < 10000:
                continue
            
            # 检查结束时间
            end_date = market.get('endDate', '')[:10]
            if end_date < today:
                continue
            
            qualified.append({
                'id': event['id'],
                'title': event.get('title', ''),
                'slug': event.get('slug', ''),
                'prob': prob,
                'volume': volume,
                'end_date': end_date,
                'in_long_term': str(event['id']) in lt_ids
            })
        except Exception as e:
            print(f"   ⚠️ 处理事件 {event.get('id')} 失败: {e}")
    
    print(f"   符合条件的事件: {len(qualified)} 个\n")
    
    # 4. 分析差异
    print("4️⃣ 分析结果:\n")
    
    # 4a. 在Long-Term中
    in_lt = [e for e in qualified if e['in_long_term']]
    print(f"   ✅ 已在Long-Term中: {len(in_lt)} 个")
    for e in sorted(in_lt, key=lambda x: x['prob'], reverse=True)[:5]:
        print(f"      {e['prob']:.1%} | Vol: {e['volume']:,.0f} | {e['title'][:50]}...")
    
    # 4b. 不在Long-Term中（遗漏的）
    missing = [e for e in qualified if not e['in_long_term']]
    print(f"\n   ❌ 遗漏的事件: {len(missing)} 个")
    if missing:
        for e in sorted(missing, key=lambda x: x['prob'], reverse=True):
            print(f"      {e['prob']:.1%} | Vol: {e['volume']:,.0f} | End: {e['end_date']}")
            print(f"         ID: {e['id']} | {e['title']}")
    
    # 5. 检查"排名第一"事件
    print(f"\n{'='*60}")
    print("5️⃣ 检查特定事件: 'best' 或 'top' 或 '#1'")
    print(f"{'='*60}\n")
    
    for event in api_events:
        title = event.get('title', '').lower()
        if any(kw in title for kw in ['best', 'top', '#1', 'first', 'ranking']):
            try:
                markets = event.get('markets', [])
                if not markets:
                    continue
                market = markets[0]
                prices = json.loads(market.get('outcomePrices', '[0,0]'))
                prob = float(prices[0])
                volume = float(market.get('volume', 0))
                end_date = market.get('endDate', '')[:10]
                
                print(f"   ID: {event['id']}")
                print(f"   标题: {event.get('title')}")
                print(f"   概率: {prob:.1%} | 交易量: {volume:,.0f} | 结束: {end_date}")
                print(f"   已在Long-Term: {str(event['id']) in lt_ids}")
                print()
            except:
                pass
    
    print(f"{'='*60}")
    print("✅ 分析完成!")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    analyze()
