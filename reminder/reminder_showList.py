import discord
from discord import app_commands
import reminder.reminder_core as core

# 统一使用市场绿色风格
COLOR_MARKET_GREEN = 0x2ECC71 

def setup(tree: app_commands.CommandTree):
    @tree.command(name="提醒列表", description="查看我当前设置的所有提醒（平原/时间/市场/裂缝）")
    async def show_list(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        
        user_id = interaction.user.id
        # 获取该用户所有已启用的提醒
        active_reminders = core.list_items(user_id, only_enabled=True)

        if not active_reminders:
            await interaction.followup.send("💡 你目前没有设置任何提醒任务。")
            return

        embed = discord.Embed(
            title="🔔 我的提醒清单",
            description="你可以通过编号来取消不需要的提醒。",
            color=COLOR_MARKET_GREEN
        )

        # 分类整理显示内容
        type1_text = ""  # 时间/平原/周期类
        type2_text = ""  # 市场价格类
        type3_text = ""  # 核桃裂缝类
        other_text = ""  # 其他

        for i, item in enumerate(active_reminders, 1):
            if item.reminder_type == 1:
                # Type 1：时间戳提醒
                type1_text += f"{i}. **{item.item_name}**\n预计：{core.ts_full(item.trigger_ts)}\n"
            
            elif item.reminder_type == 2:
                # Type 2：市场价格提醒
                rank_str = f" (Rank {item.rank})" if item.rank is not None else ""
                trade_str = "买入" if item.trade_type == "sell" else "卖出"
                type2_text += f"{i}. **{item.item_name}**{rank_str}\n类型：{trade_str} | 目标：{item.target_price} Pt\n"
            
            elif item.reminder_type == 3:
                # --- 修改部分：Type 3 裂缝提醒解析 ---
                storm_tag = " (仅限九重天)" if getattr(item, 'target_is_storm', False) else ""
                type3_text += f"{i}. **{item.item_name}**{storm_tag}\n监控中：出现即艾特提醒\n"
                
            else:
                other_text += f"{i}. **{item.item_name}** (未知类型)\n"

        # 按照分类添加到 Embed 字段
        if type1_text:
            embed.add_field(name="⏰ 时间/平原提醒", value=type1_text, inline=False)
        
        if type2_text:
            embed.add_field(name="💰 市场价格监控", value=type2_text, inline=False)
            
        if type3_text:
            # 新增裂缝展示板块
            embed.add_field(name="🌀 虚空裂缝监控", value=type3_text, inline=False)
            
        if other_text:
            embed.add_field(name="❓ 其他提醒", value=other_text, inline=False)

        embed.set_footer(text="使用 /取消提醒 [编号] 可以移除对应条目")
        await interaction.followup.send(embed=embed)