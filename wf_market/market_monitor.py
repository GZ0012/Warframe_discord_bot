import discord
import asyncio  # 必须导入
from discord.ext import tasks
from wf_market.market_api import client_v2
from reminder.reminder_core import load_items, save_items

class MarketMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.check_market_prices.start()

    @tasks.loop(minutes=1)
    async def check_market_prices(self):
        if not self.bot.is_ready():
            return

        all_items = load_items()
        triggered = False

        # 筛选出需要检查的市场提醒
        market_tasks = [it for it in all_items if it.enabled and it.reminder_type == 2]
        
        for item in market_tasks:
            # --- 核心频率控制：每秒最多2次访问，即间隔0.5秒 ---
            await asyncio.sleep(0.5) 

            try:
                # 调用 API
                order_data = client_v2.get_market_best_price(item.slug, item.trade_type, item.rank)
                
                if not order_data:
                    continue

                current_price = order_data['price']
                player_name = order_data['ingame_name']

                # 判断触发逻辑
                is_triggered = False
                if item.trade_type == "sell" and current_price <= item.target_price:
                    is_triggered = True
                elif item.trade_type == "buy" and current_price >= item.target_price:
                    is_triggered = True

                if is_triggered:
                    channel = self.bot.get_channel(item.channel_id)
                    if channel:
                        en_item_name = order_data['en_name']
                        rank_str = f" (rank {item.rank})" if item.rank is not None else ""
                        
                        # 构造纯英文交易指令
                        whisper_cmd = f"```/w {player_name} Hi! I want to buy: {en_item_name}{rank_str} for {current_price} platinum. (warframe.market)```"
                        
                        embed = discord.Embed(title="💰 市场价格预警触发", color=0xE74C3C)
                        embed.description = (
                            f"物品：**{item.item_name}** ({en_item_name}){rank_str}\n"
                            f"当前价格：**{current_price} Pt**\n"
                            f"在线玩家：**{player_name}**"
                        )
                        embed.add_field(name="复制下方指令至游戏内私聊", value=whisper_cmd, inline=False)
                        
                        try:
                            await channel.send(content=f"<@{item.user_id}>", embed=embed)
                        except:
                            pass
                    
                    # 触发后禁用
                    item.enabled = False
                    triggered = True
            except Exception as e:
                print(f"检查 {item.item_name} 时报错: {e}")

        # 如果有触发，统一保存一次
        if triggered:
            save_items(all_items)

def setup_monitor(bot):
    return MarketMonitor(bot)