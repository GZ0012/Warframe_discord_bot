import discord
from discord import app_commands
from wf_market.market_api import client_v2

# 统一使用绿色风格
COLOR_MARKET_GREEN = 0x2ECC71 

def setup(tree: app_commands.CommandTree):
    @tree.command(name="市场", description="Warframe Market V2 实时查询 (支持MOD/赋能等级)")
    @app_commands.describe(
        物品="输入中文或英文物品名称", 
        等级="如果是MOD或赋能可选填等级 (0-max)，非此类物品请勿填写"
    )
    async def market(interaction: discord.Interaction, 物品: str, 等级: int = None):
        await interaction.response.defer(thinking=True)
        
        # 1. 扫描匹配物品并获取类型
        item_info = client_v2.find_item_slug(物品)
        if not item_info:
            await interaction.followup.send(f"❌ 查不到 “{物品}”，请尝试输入更准确的名称。")
            return

        # 2. 等级逻辑处理
        # 如果不是 MOD/赋能 却填了等级，直接拦截
        if 等级 is not None and not item_info.get('is_rankable'):
            await interaction.followup.send(f"⚠️ **{item_info['name']}** 没有等级概念，无法指定等级查询。")
            return

        # 如果是 MOD/赋能 且没填等级，默认查 0 级
        target_rank = 等级
        if item_info.get('is_rankable') and 等级 is None:
            target_rank = 0

        # 3. 获取数据 (带入 rank 参数)
        data = client_v2.get_market_data(item_info['slug'], rank=target_rank)
        if not data:
            await interaction.followup.send(f"⚠️ 无法获取 **{item_info['name']}** 的价格数据。")
            return

        # 4. 构造 Embed
        # 如果有等级，在标题中显示
        title_rank = f" (Rank {target_rank})" if target_rank is not None else ""
        embed = discord.Embed(
            title=f"📊 {item_info['name']}{title_rank}",
            url=f"https://warframe.market/zh-hant/items/{item_info['slug']}",
            color=COLOR_MARKET_GREEN
        )

        # 辅助函数：将状态转换为简洁文字
        def get_status_text(status):
            if status == 'ingame':
                return " (游戏中)"
            elif status == 'online':
                return " (在线)"
            return ""

        # 5. 卖家展示 (Sell - 上方)
        sell_text = ""
        for o in data['sell']:
            user = o['user']
            status = get_status_text(user['status'])
            # 格式：价格 | **名字** (状态)
            sell_text += f"{o['platinum']} Pt | **{user['ingameName']}**{status}\n"
        
        if sell_text:
            embed.add_field(name="💰 卖家报价 (低价优先)", value=sell_text, inline=False)

        # 6. 买家展示 (Buy - 下方)
        buy_text = ""
        for o in data['buy']:
            user = o['user']
            status = get_status_text(user['status'])
            buy_text += f"{o['platinum']} Pt | **{user['ingameName']}**{status}\n"
            
        if buy_text:
            # 使用 inline=False 确保上下堆叠布局
            embed.add_field(name="🛒 买家求购 (高价优先)", value=buy_text, inline=False)

        embed.set_footer(text="数据源：Warframe Market V2")
        await interaction.followup.send(embed=embed)