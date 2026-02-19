import requests
import re
import discord
from discord import app_commands
from datetime import datetime

# --- 你原有的对照表保持不变 ---
TRANSLATION = {
    "Lith": "古纪", "Meso": "前纪", "Neo": "中纪", "Axi": "后纪", "Requiem": "安魂", "Omnia": "全能",
    "Survival": "生存", "Defense": "防御", "Extermination": "歼灭", "Capture": "捕获",
    "Excavation": "挖掘", "Interception": "拦截", "Mobile Defense": "移动防御",
    "Spy": "间谍", "Rescue": "救援", "Sabotage": "破坏", "Disruption": "中断",
    "Skirmish": "前哨战", "Assault": "强袭", "Orphix": "奥影", "Volatile": "爆发",
    "Void Cascade": "虚空覆涌", "Void Flood": "虚空洪流", "Mirror Defense": "镜像防御",
    "Alchemy": "元素转换"
}

PLANETS = {
    "Mercury": "水星", "Venus": "金星", "Earth": "地球", "Mars": "火星", 
    "Jupiter": "木星", "Saturn": "土星", "Uranus": "天王星", "Neptune": "海王星", 
    "Pluto": "冥王星", "Ceres": "谷神星", "Eris": "阋神星", "Sedna": "赛德娜",
    "Lua": "月球", "Zariman": "扎里曼", "Void": "虚空", "Deimos": "火卫二", "Kuva Fortress": "赤毒要塞",
    "Phobos": "火卫二", "Europa": "欧罗巴", "Veil": "面纱"
}

# --- 你原有的逻辑保持不变 ---
def get_fissure_data():
    url = "https://api.warframestat.us/pc/fissures"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200: return None
        data = r.json()
        
        classified = {"normal": [], "hard": [], "storm": []}
        tier_weight = {"Lith": 1, "Meso": 2, "Neo": 3, "Axi": 4, "Requiem": 5, "Omnia": 6}

        for f in data:
            if f.get('expired'): continue
            
            node_raw = f.get('node', "Unknown")
            node_zh = node_raw
            match = re.search(r"(.+)\s\((.+)\)", node_raw)
            if match:
                place_en = match.group(1)
                planet_en = match.group(2)
                node_zh = f"{place_en} ({PLANETS.get(planet_en, planet_en)})"

            expiry_str = f.get('expiry')
            timestamp_str = "未知时间"
            if expiry_str:
                try:
                    dt = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                    unix_ts = int(dt.timestamp())
                    timestamp_str = f"<t:{unix_ts}:R>"
                except:
                    timestamp_str = f.get('eta', "即将结束")

            f_info = {
                "tier": TRANSLATION.get(f.get('tier'), f.get('tier')),
                "mission": TRANSLATION.get(f.get('missionType'), f.get('missionType')),
                "node": node_zh,
                "eta": timestamp_str,
                "tierNum": tier_weight.get(f.get('tier'), 99)
            }

            if f.get('isStorm'): classified["storm"].append(f_info)
            elif f.get('isHard'): classified["hard"].append(f_info)
            else: classified["normal"].append(f_info)
        
        for key in classified:
            classified[key].sort(key=lambda x: x['tierNum'])
        return classified
    except:
        return None

# --- 核心命令部分 (增加了交互延迟处理) ---
@app_commands.command(name="裂缝", description="获取虚空裂缝实时数据")
async def fissure(interaction: discord.Interaction):
    # 【核心修改点 1】立即回复 Discord：正在处理中。这解决了 3 秒超时导致的 404
    await interaction.response.defer(thinking=True)

    try:
        # 调用你之前写好的数据处理逻辑
        data = get_fissure_data()

        if not data:
            await interaction.followup.send("❌ 无法从 API 获取裂缝数据")
            return

        # 拼接输出字符串
        msg_parts = ["🌀 **虚空裂缝实时数据**"]
        
        # 类别显示名
        categories = [
            ("normal", "--- 常规裂缝 ---"),
            ("hard", "--- 钢铁路径 ---"),
            ("storm", "--- 虚空风暴 ---")
        ]

        for key, title in categories:
            if data[key]:
                msg_parts.append(f"\n**{title}**")
                for f in data[key]:
                    msg_parts.append(f"• `[{f['tier']}]` {f['mission']} - {f['node']} ({f['eta']})")

        # 【核心修改点 2】使用 followup.send 发送。因为已经执行了 defer
        final_msg = "\n".join(msg_parts)
        # 如果消息过长，Discord 会报错，简单截断一下
        await interaction.followup.send(final_msg[:2000])

    except Exception as e:
        print(f"Command Error: {e}")
        # 如果中间崩了，也要告诉用户，避免一直卡在“思考中”状态
        await interaction.followup.send("程序运行出错，请联系开发者查看日志。")