import requests

BASE_URL = "https://api.warframe.market/v2"

class WFMV2Client:
    def __init__(self):
        self.headers = {
            'Language': 'zh-hans',
            'Accept': 'application/json',
            'Platform': 'pc'
        }
        self._items_cache = []

    def _load_items(self):
        if self._items_cache: return
        try:
            r = requests.get(f"{BASE_URL}/items", headers=self.headers, timeout=10)
            if r.status_code == 200:
                self._items_cache = r.json().get('data', [])
        except Exception as e:
            print(f"API 缓存加载失败: {e}")

    def find_item_slug(self, query):
        self._load_items()
        query = query.strip().lower()
        for item in self._items_cache:
            i18n = item.get('i18n', {})
            zh = i18n.get('zh-hans', {}).get('name', '').lower()
            en = i18n.get('en', {}).get('name', '').lower()
            slug = item.get('slug', '').lower()
            tags = item.get('tags', []) 
            if query == zh or query == en or query == slug or query in zh:
                is_rankable = any(t in tags for t in ["mod", "arcane_enhancement"])
                return {
                    "name": i18n.get('zh-hans', {}).get('name'), 
                    "slug": slug,
                    "is_rankable": is_rankable
                }
        return None

    # --- 方法一：为 /市场 指令设计，返回前 5 名列表 ---
    def get_market_data(self, slug, rank=None):
        """返回包含 sell 和 buy 两个列表的字典，每个列表包含前 5 个最优订单"""
        url = f"{BASE_URL}/orders/item/{slug}/top"
        params = {'rank': rank} if rank is not None else {}
        try:
            r = requests.get(url, headers=self.headers, params=params, timeout=10)
            if r.status_code == 200:
                raw_data = r.json().get('data', {})
                # 获取卖单并按价格升序排，取前5
                sell_orders = sorted(raw_data.get('sell', []), key=lambda x: x.get('platinum', 999999))[:5]
                # 获取买单并按价格降序排，取前5
                buy_orders = sorted(raw_data.get('buy', []), key=lambda x: x.get('platinum', 0), reverse=True)[:5]
                
                return {
                    'sell': sell_orders,
                    'buy': buy_orders
                }
        except Exception as e:
            print(f"get_market_data 失败: {e}")
        return None

    # --- 方法二：为 监控/提醒 设计，返回单一最佳订单字典 ---
    def get_market_best_price(self, slug, trade_type, rank=None):
        """返回单一字典，包含 price, ingame_name 等"""
        url = f"{BASE_URL}/orders/item/{slug}/top"
        params = {'rank': rank} if rank is not None else {}
        try:
            r = requests.get(url, headers=self.headers, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json().get('data', {}).get(trade_type, [])
                if not data: return None
                
                if trade_type == 'sell':
                    best_order = min(data, key=lambda x: x.get('platinum', 999999))
                else:
                    best_order = max(data, key=lambda x: x.get('platinum', 0))
    
                user_info = best_order.get('user', {})
                player_name = user_info.get('ingameName') or user_info.get('ingame_name') or "WFM_User"

                return {
                    'price': best_order.get('platinum'),
                    'ingame_name': player_name,
                    'en_name': slug.replace('_', ' ').title() 
                }
        except Exception as e:
            print(f"get_market_best_price 失败: {e}")
        return None

client_v2 = WFMV2Client()