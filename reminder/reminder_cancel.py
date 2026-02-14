# reminder/reminder_cancel.py
# /提醒取消 <序号>
# 说明：序号来自 /提醒列表（只看启用中的提醒）

import discord
from discord import app_commands
from reminder.reminder_core import get_item_by_index, disable_item, ts_full, ts_relative

COLOR_OK = 0x2ECC71
COLOR_ERR = 0xE74C3C

def setup(tree: app_commands.CommandTree):
    @tree.command(name="提醒取消", description="取消一个提醒：/提醒取消 1（序号来自 /提醒列表）")
    @app_commands.describe(序号="在 /提醒列表 里看到的序号（从 1 开始）")
    async def cancel_reminder(interaction: discord.Interaction, 序号: int):
        # 统一使用 defer，避免操作文件过慢导致超时
        await interaction.response.defer(thinking=False)

        if 序号 <= 0:
            embed = discord.Embed(title="❌ 取消失败", color=COLOR_ERR)
            embed.description = "序号必须是正整数（从 1 开始）。"
            await interaction.followup.send(embed=embed)
            return

        # 从数据库获取该用户的指定序号提醒
        item = get_item_by_index(interaction.user.id, 序号)
        
        if not item:
            embed = discord.Embed(title="❌ 取消失败", color=COLOR_ERR)
            embed.description = "找不到对应的提醒。可能该提醒已经触发完成，或者序号已改变。\n请通过 `/提醒列表` 重新确认。"
            await interaction.followup.send(embed=embed)
            return

        # 执行禁用操作
        ok = disable_item(item.id)
        if not ok:
            embed = discord.Embed(title="❌ 取消失败", color=COLOR_ERR)
            embed.description = "该提醒状态异常，可能已被处理。"
            await interaction.followup.send(embed=embed)
            return

        # ✅ 成功反馈 UI
        embed = discord.Embed(title="✅ 提醒已成功取消", color=COLOR_OK)
        embed.add_field(name="提醒项", value=f"**{item.title}**", inline=False)

        # 解析 meta 信息用于展示
        meta = item.meta or {}
        area = meta.get("area")
        target_text = meta.get("target_text")
        start_ts = meta.get("start_ts")

        if area and target_text:
            embed.add_field(name="原定目标", value=f"{area} · {target_text}", inline=True)
        
        if start_ts:
            # 使用 reminder_core 提供的统一时间格式
            embed.add_field(
                name="原定开始时间", 
                value=f"{ts_full(int(start_ts))}\n{ts_relative(int(start_ts))}", 
                inline=False
            )

        embed.set_footer(text="提示：你可以随时重新设置新的提醒。")
        await interaction.followup.send(embed=embed)