import discord
from discord.ext import tasks
import requests
import re
from datetime import datetime
from reminder.reminder_core import load_items, save_items
from fissure.fissure_core import TRANSLATION
from fissure.fissure_core import PLANETS

class FissureMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.check_fissures.start()

    @tasks.loop(minutes=1)
    async def check_fissures(self):
        if not self.bot.is_ready(): return

        all_items = load_items()
        active_tasks = [it for it in all_items if it.enabled and it.reminder_type == 3]
        if not active_tasks: return

        try:
            r = requests.get("https://api.warframestat.us/pc/fissures", timeout=10)
            if r.status_code != 200: return
            current_fissures = r.json()
        except Exception as e:
            print(f"裂缝 API 异常: {e}")
            return

        triggered = False
        for item in active_tasks:
            match = None
            # 从指令存入的 trade_type 中读取难度限制
            target_diff = getattr(item, 'trade_type', 'all')
            
            for f in current_fissures:
                # 1. 任务类型匹配
                if f.get('missionType', '').lower() != item.target_mission.lower():
                    continue
                
                # 2. 难度逻辑过滤
                f_is_hard = f.get('isHard', False)
                f_is_storm = f.get('isStorm', False)
                
                if target_diff == "normal" and (f_is_hard or f_is_storm): continue
                if target_diff == "hard" and not f_is_hard: continue
                if target_diff == "storm" and not f_is_storm: continue
                
                if not f.get('expired'):
                    match = f
                    break
            
            if match:
                channel = self.bot.get_channel(item.channel_id)
                if channel:
                    # --- 节点翻译：星球在前 - 节点在后 ---
                    raw_node = match.get('node', 'Unknown')
                    node_zh = raw_node
                    
                    # 使用正则提取括号里的星球，例如 "Uriel (Uranus)" -> Uranus
                    planet_match = re.search(r'\((.*?)\)', raw_node)
                    if planet_match:
                        en_planet = planet_match.group(1)
                        zh_planet = PLANETS.get(en_planet, en_planet) # 翻译星球
                        loc_name = raw_node.split('(')[0].strip() # 提取 Uriel
                        node_zh = f"{zh_planet} - {loc_name}"
                    
                    # --- 其他信息展示 ---
                    difficulty_zh = "钢铁之路" if match.get('isHard') else ("虚空风暴" if match.get('isStorm') else "普通")
                    tier_zh = TRANSLATION.get(match.get('tier'), match.get('tier'))
                    mission_zh = TRANSLATION.get(match.get('missionType'), match.get('missionType'))
                    
                    expiry_str = match.get('expiry')
                    ts_display = "未知"
                    if expiry_str:
                        try:
                            dt = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                            ts_display = f"<t:{int(dt.timestamp())}:R>" 
                        except: pass

                    embed = discord.Embed(title="🌀 目标虚空裂缝出现", color=0xE74C3C)
                    embed.add_field(name="🔹 难度", value=f"`{difficulty_zh}`", inline=True)
                    embed.add_field(name="🔹 核桃", value=f"`{tier_zh}`", inline=True)
                    embed.add_field(name="🔹 类型", value=f"`{mission_zh}`", inline=True)
                    embed.add_field(name="📍 节点", value=f"`{node_zh}`", inline=False)
                    embed.add_field(name="⏳ 剩余时间", value=ts_display, inline=False)
                    
                    try:
                        await channel.send(content=f"🔔 <@{item.user_id}> 匹配裂缝出现！", embed=embed)
                        item.enabled = False 
                        triggered = True
                    except: pass

        if triggered:
            save_items(all_items)

def setup_fissure_monitor(bot):
    return FissureMonitor(bot)