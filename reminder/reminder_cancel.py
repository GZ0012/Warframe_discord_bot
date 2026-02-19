import discord
from discord import app_commands
from reminder.reminder_core import list_items, disable_item, ts_full, ts_relative

# 颜色配置
COLOR_OK = 0x2ECC71
COLOR_ERR = 0xE74C3C

def setup(tree: app_commands.CommandTree):
    @tree.command(name="提醒取消", description="通过序号取消提醒（序号见 /提醒列表）")
    @app_commands.describe(序号="在 /提醒列表 中看到的数字编号")
    async def cancel_reminder(interaction: discord.Interaction, 序号: int):
        # 1. 统一 defer 处理，防止操作文件导致超时
        await interaction.response.defer(thinking=True)

        if 序号 <= 0:
            await interaction.followup.send(embed=discord.Embed(
                title="❌ 输入错误", description="序号必须从 1 开始。", color=COLOR_ERR
            ))
            return

        # 2. 获取当前用户所有活跃提醒，并根据序号提取条目
        user_list = list_items(interaction.user.id, only_enabled=True)
        item = user_list[序号 - 1] if 1 <= 序号 <= len(user_list) else None
        
        if not item:
            await interaction.followup.send(embed=discord.Embed(
                title="❌ 取消失败", 
                description="找不到对应的提醒。可能序号已变动，请重新查看 `/提醒列表`。", 
                color=COLOR_ERR
            ))
            return

        # 3. 执行禁用操作 (将 enabled 设为 False)
        ok = disable_item(item.id)
        if not ok:
            await interaction.followup.send(embed=discord.Embed(
                title="❌ 取消失败", description="该提醒可能已经触发或已被手动移除。", color=COLOR_ERR
            ))
            return

        # 4. 成功反馈 UI：根据 reminder_type 动态展示信息
        embed = discord.Embed(title="✅ 提醒已成功取消", color=COLOR_OK)
        
        # 统一加粗显示物品名字
        embed.add_field(name="取消项", value=f"**{item.item_name}**", inline=False)

        # 针对不同类型的提醒展示不同的原定信息
        if item.reminder_type == 1:
            # Type 1: 平原/时间类展示
            meta = item.meta or {}
            area = meta.get("area")
            target = meta.get("target_text")
            start_ts = meta.get("start_ts")
            
            if area and target:
                embed.add_field(name="原定目标", value=f"{area} · {target}", inline=True)
            if start_ts:
                embed.add_field(
                    name="原定开始时间", 
                    value=f"{ts_full(int(start_ts))}", 
                    inline=False
                )
        
        elif item.reminder_type == 2:
            # Type 2: 市场价格监控展示
            trade_str = "买入 (监控卖家)" if item.trade_type == "sell" else "卖出 (监控买家)"
            rank_str = f" (Rank {item.rank})" if item.rank is not None else ""
            embed.add_field(name="监控类型", value=f"{trade_str}{rank_str}", inline=True)
            embed.add_field(name="监控价格", value=f"{item.target_price} Pt", inline=True)

        embed.set_footer(text="提示：你可以随时重新设置新的提醒。")
        await interaction.followup.send(embed=embed)