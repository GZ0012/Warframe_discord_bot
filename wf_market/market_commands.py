# wf_market/market_commands.py
import discord
from discord import app_commands
from wf_market.market_api import find_best_matches, get_market_prices

COLOR_MARKET = 0x3498DB
COLOR_WARN = 0xF1C40F

def setup(tree: app_commands.CommandTree):
    @tree.command(name="市场", description="查询物品价格（支持中文模糊匹配）")
    @app_commands.describe(物品="输入中文或英文物品名称")
    async def market(interaction: discord.Interaction, 物品: str):
        await interaction.response.defer(thinking=True)
        
        best_match, recommendations = find_best_matches(物品)
        
        # 情况 1: 完美匹配成功
        if best_match:
            orders = get_market_prices(best_match['url_name'])
            if not orders:
                await interaction.followup.send(f"✅ 找到物品 **{best_match['item_name']}**，但目前没有在线玩家出售。")
                return

            embed = discord.Embed(
                title=f"市场查询: {best_match['item_name']}",
                url=f"https://warframe.market/zh-hant/items/{best_match['url_name']}",
                color=COLOR_MARKET
            )
            for i, o in enumerate(orders, 1):
                val = f"价格: **{o['platinum']}** Pt | 数量: {o['quantity']}\n指令: `/w {o['user']['ingame_name']} Hi! I want to buy...`"
                embed.add_field(name=f"Top {i} 卖家", value=val, inline=False)
            await interaction.followup.send(embed=embed)

        # 情况 2: 匹配失败，显示推荐列表
        elif recommendations:
            embed = discord.Embed(
                title="搜索不到你要的物品",
                description=f"没有直接找到 “{物品}”，但是有类似的是你要的吗？",
                color=COLOR_WARN
            )
            rec_text = ""
            for i, item in enumerate(recommendations, 1):
                rec_text += f"**{i}. {item['item_name']}**\n"
            
            embed.add_field(name="建议搜索:", value=rec_text)
            embed.set_footer(text="请尝试重新输入更完整的名称")
            await interaction.followup.send(embed=embed)
            
        # 情况 3: 彻底没找到
        else:
            await interaction.followup.send(f"❌ 搜不到你要的“{物品}”，也没有类似的建议。")