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
def is_tech_market(question):
    """Check if a market question is tech-related"""
    question_lower = question.lower()
    
    # Strong tech indicators (must have at least one)
    tech_strong = ['ai ', 'artificial intelligence', 'machine learning', 'deep learning',
                   'openai', 'anthropic', 'claude', 'gpt-', 'llm',
                   'apple', 'google', 'microsoft', 'amazon', 'meta', 'facebook',
                   'tesla', 'spacex', 'elon musk',
                   'iphone', 'android', 'smartphone', 'laptop', 'computer',
                   'nvidia', 'amd', 'intel', 'chip', 'semiconductor', 'cpu', 'gpu',
                   'cloud', 'aws', 'azure', 'google cloud',
                   'cryptocurrency', 'bitcoin', 'ethereum', 'blockchain',
                   'quantum computing', 'robot', 'automation',
                   '5g', '6g', 'telecom', 'network',
                   'software', 'hardware', 'app store', 'play store']
    
    # Exclude non-tech (sports, politics, etc.)
    exclude = ['nba', 'nfl', 'world cup', 'fifa', 'trail blazers', 'spurs', 'lakers', 'warriors',
               'f1', 'formula 1', 'grand prix', 'drivers championship',
               'cricket', 'ipl', 'premier league', 'football', 'soccer', 'baseball', 'tennis',
               'trump', 'biden', 'election', 'president', 'harris', 'kamala',
               'iran', 'israel', 'ukraine', 'russia', 'china invade', 'taiwan',
               'fed chair', 'interest rate', 'powell', 'jerome',
               'strait of hormuz', 'military operation', 'war',
               'tweet', 'post', 'twitter', 'x.com', 'musk post']  # Exclude tweet count markets
    
    # Must not contain excluded terms
    if any(excl in question_lower for excl in exclude):
        return False
    
    # Must contain at least one strong tech indicator
    return any(tech in question_lower for tech in tech_strong)

def fetch_tech_markets(limit=100):
    """Fetch technology markets from Polymarket API"""
    url = "https://gamma-api.polymarket.com/markets"
    
    try:
        all_markets = []
        
        # Fetch multiple pages to get enough tech markets
        for offset in [0, 100, 200, 300]:
            params = {
                "limit": 100,
                "closed": "false",
                "order": "volume24hr",
                "ascending": "false",
                "offset": offset
            }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            markets = response.json()
            
            if not markets:
                break
                
            # Filter for tech
            for market in markets:
                question = market.get('question', '')
                if is_tech_market(question):
                    all_markets.append(market)
            
            if len(all_markets) >= 20:
                break
        
        print(f"Found {len(all_markets)} tech-related markets")
        return all_markets[:20]
        
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
    
    output_path = 'data/markets.json'
    # Ensure data directory exists
    import os
    os.makedirs('data', exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(markets_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(processed)} markets to {output_path}")

if __name__ == "__main__":
    main()
