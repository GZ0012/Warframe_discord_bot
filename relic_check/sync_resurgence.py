import requests
import sqlite3
import datetime

def sync_resurgence():
    # 修正后的 API 地址：获取瓦齐娅（Vault Trader）的数据
    url = "https://api.warframestat.us/pc/vaultTrader?language=en"
    db_path = 'warframe_relics.db'
    
    print("🔄 正在从瓦齐娅商店抓取当前回归核桃...")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            print(f"❌ 接口请求失败，状态码: {r.status_code}")
            return
            
        data = r.json()
        
        # 提取当前在售的核桃名单
        resurgence_relics = []
        # 注意：vaultTrader 的结构里，清单在 'inventory' 字段
        for item in data.get('inventory', []):
            item_name = item.get('item', '')
            # 只要名字里带 Relic 的都抓出来
            if 'Relic' in item_name:
                # 格式化一下名字，确保匹配数据库（例如 "Lith L7 Relic"）
                clean_name = item_name.split('(')[0].strip().title()
                if not clean_name.endswith("Relic"):
                    clean_name += " Relic"
                resurgence_relics.append(clean_name)

        if not resurgence_relics:
            print("ℹ️ 当前瓦齐娅商店似乎没有核桃在售（或接口数据为空）。")
            return

        # 写入数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 先把数据库里所有原本是 3 的重置为 1 (因为它们可能已经下架变回普通入库了)
        cursor.execute("UPDATE relics SET is_vaulted = 1 WHERE is_vaulted = 3")
        
        # 标记新的回归核桃
        success_count = 0
        for name in resurgence_relics:
            cursor.execute("UPDATE relics SET is_vaulted = 3, last_updated = ? WHERE name = ?", (now, name))
            if cursor.rowcount > 0:
                success_count += 1
        
        conn.commit()
        conn.close()
        print(f"✅ 同步完成！共发现 {len(resurgence_relics)} 个回归项，已成功更新数据库中 {success_count} 个核桃。")
        
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")

if __name__ == "__main__":
    sync_resurgence()