# wf_market/market_api.py
import requests
import difflib

BASE_URL = "https://api.warframe.market/v1"
_items_cache = []  

def load_item_cache():
    global _items_cache
    if _items_cache: return
    try:
        r = requests.get(f"{BASE_URL}/items", timeout=10)
        _items_cache = r.json()['payload']['items']
    except Exception as e:
        print(f"加载市场清单失败: {e}")

def find_best_matches(query: str, limit: int = 3):
    load_item_cache()
    query = query.strip().lower()
    
    all_names = [item['item_name'] for item in _items_cache]
    
    for item in _items_cache:
        if query == item['item_name'].lower():
            return item, []

    matches = difflib.get_close_matches(query, all_names, n=limit, cutoff=0.3)
    
    recommend_items = []
    for m in matches:
        for item in _items_cache:
            if item['item_name'] == m:
                recommend_items.append(item)
                break
    
    return None, recommend_items

def get_market_prices(url_name: str):
    url = f"{BASE_URL}/items/{url_name}/orders"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        orders = [
            o for o in data['payload']['orders'] 
            if o['order_type'] == 'sell' and o['user']['status'] in ['ingame', 'online']
        ]
        orders.sort(key=lambda x: x['platinum'])
        return orders[:3]
    except:
        return []