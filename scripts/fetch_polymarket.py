#!/usr/bin/env python3
"""
Fetch Polymarket technology markets and save to JSON
"""
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv('/root/.hermes/credentials/polymarket-tracker.env')

def fetch_tech_markets(limit=50):
    """Fetch technology markets from Polymarket API"""
    url = "https://gamma-api.polymarket.com/markets"
    
    params = {
        "limit": limit,
        "closed": "false",
        "order": "volume24hr",
        "ascending": "false"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        markets = response.json()
        
        # Filter for tech-related markets
        tech_keywords = ['ai', 'tech', 'software', 'hardware', 'apple', 'google', 'microsoft', 
                        'amazon', 'meta', 'openai', 'anthropic', 'spacex', 'tesla', 'elon',
                        'iphone', 'android', 'chip', 'semiconductor', 'cloud', 'data']
        
        tech_markets = []
        for market in markets:
            question = market.get('question', '').lower()
            if any(keyword in question for keyword in tech_keywords):
                tech_markets.append(market)
        
        return tech_markets[:20]
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return []

def process_market(market):
    """Process raw market data into simplified format"""
    try:
        outcomes = []
        if market.get('outcomes'):
            try:
                outcomes_data = json.loads(market['outcomes']) if isinstance(market['outcomes'], str) else market['outcomes']
                for outcome in outcomes_data:
                    outcomes.append({
                        "label": outcome.get('outcome', ''),
                        "probability": float(outcome.get('price', 0))
                    })
            except:
                pass
        
        return {
            "id": market.get('id'),
            "question": market.get('question'),
            "volume": f"${float(market.get('volume', 0)):,.0f}",
            "endDate": market.get('endDate', '')[:10] if market.get('endDate') else '',
            "outcomes": outcomes,
            "slug": market.get('slug', ''),
            "news": [],
            "prediction": {
                "direction": outcomes[0]['label'] if outcomes else "TBD",
                "confidence": 0.5,
                "reasoning": "Analysis pending news data"
            }
        }
    except Exception as e:
        print(f"Error processing market: {e}")
        return None

def main():
    print("Fetching Polymarket tech markets...")
    markets = fetch_tech_markets(50)
    
    if not markets:
        print("No markets fetched.")
        return
    
    processed = [process_market(m) for m in markets]
    processed = [m for m in processed if m is not None]
    
    markets_data = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_markets": len(processed),
        "markets": processed[:20]
    }
    
    output_path = '/home/c1/polymarket-tech-tracker/data/markets.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(markets_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(processed)} markets to {output_path}")

if __name__ == "__main__":
    main()
