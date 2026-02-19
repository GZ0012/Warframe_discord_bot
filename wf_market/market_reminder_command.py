import discord
from discord import app_commands
import json
import os
from wf_market.market_api import client_v2
from reminder.reminder_core import ReminderItem, add_item

# 统一绿色风格
COLOR_MARKET_GREEN = 0x2ECC71 

def setup(tree: app_commands.CommandTree):
    @tree.command(name="提醒_买卖", description="设置市场价格预警 (支持MOD/赋能等级)")
    @app_commands.describe(
        类型="选择监控类型：'买入' (监控卖家低价) 或 '卖出' (监控买家高价)",
        物品="输入中文或英文物品名称", 
        价格="设定的目标 Pt 价格",
        等级="如果是MOD或赋能可选填等级 (0-max)"
    )
    @app_commands.choices(类型=[
        app_commands.Choice(name="买入 (监控卖家报价)", value="sell"),
        app_commands.Choice(name="卖出 (监控买家求购)", value="buy")
    ])
    async def market_alert(interaction: discord.Interaction, 类型: str, 物品: str, 价格: int, 等级: int = None):
        await interaction.response.defer(thinking=True)
        
        # 1. 获取物品信息并检查等级合法性
        item_info = client_v2.find_item_slug(物品)
        if not item_info:
            await interaction.followup.send(f"❌ 查不到 “{物品}”，无法设置提醒。")
            return

        if 等级 is not None and not item_info.get('is_rankable'):
            await interaction.followup.send(f"⚠️ **{item_info['name']}** 没有等级概念，请勿填写等级。")
            return

        # 默认等级处理：如果是可升级物品但没填等级，默认 Rank 0
        target_rank = 等级
        if item_info.get('is_rankable') and 等级 is None:
            target_rank = 0

        # 2. 构造符合 ReminderItem 模型的数据
        # 注意：这里必须包含 item_name 和 reminder_type=2
        new_item = ReminderItem(
            user_id=interaction.user.id,
            channel_id=interaction.channel_id,
            item_name=item_info['name'],    # 用于列表显示
            reminder_type=2,                # 市场提醒标识
            type="market",
            target_price=价格,
            rank=target_rank,
            trade_type=类型,
            slug=item_info['slug'],
            meta={
                "item_full_name": item_info['name'],
                "rank": target_rank
            }
        )

        # 3. 写入 reminders.json
        try:
            add_item(new_item)
        except Exception as e:
            await interaction.followup.send(f"❌ 数据库写入失败: {e}")
            return

        # 4. 反馈 UI
        type_text = "买入 (监控卖家低价)" if 类型 == "sell" else "卖出 (监控买家高价)"
        rank_text = f" (Rank {target_rank})" if target_rank is not None else ""
        
        embed = discord.Embed(
            title="✅ 市场价格预警设置成功",
            description=(
                f"监控目标：**{item_info['name']}**{rank_text}\n"
                f"监控类型：**{type_text}**\n"
                f"触发条件：价格 {'≤' if 类型 == 'sell' else '≥'} **{价格} Pt**"
            ),
            color=COLOR_MARKET_GREEN
        )
        embed.set_footer(text="提示：后台将持续监控，达到目标价后会自动艾特你。")
        await interaction.followup.send(embed=embed)