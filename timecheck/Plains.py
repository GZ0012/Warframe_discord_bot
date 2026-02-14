# timecheck/Plains.py

import discord
from discord import app_commands

from timecheck.cycle_core import get_three_statuses, CycleStatus

COLOR_OK = 0x2ECC71


def ts_relative(unix: int) -> str:
    return f"<t:{unix}:R>"


def state_display(area: str, key: str) -> str:
    if area == "夜灵平原":
        return "白天" if key == "day" else "夜晚"
    if area == "金星":
        return "温暖" if key == "warm" else "寒冷"
    if area == "火卫二":
        return "Fass" if key == "fass" else "Vome"
    return key


def build_value(s: CycleStatus) -> str:
    return (
        f"状态：**{state_display(s.area, s.state_key)}**\n"
        f"结束：{ts_relative(s.next_change_ts)}"
    )


def setup(tree: app_commands.CommandTree):

    @tree.command(name="平原", description="查询夜灵平原 / 金星 / 火卫二循环（按观看者本地时间显示）")
    async def overview(interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        statuses = get_three_statuses()

        embed = discord.Embed(
            title="开放世界循环",
            description="（时间自动本地化；已自动对齐到下一次切换）",
            color=COLOR_OK
        )

        #夜灵平原
        s = statuses.get("夜灵平原")
        embed.add_field(
            name="夜灵平原",
            value=build_value(s) if s else "数据不可用",
            inline=True
        )

        #金星
        s = statuses.get("金星")
        embed.add_field(
            name="❄ 奥布山谷（金星）",
            value=build_value(s) if s else "数据不可用",
            inline=True
        )

        #火卫二
        s = statuses.get("火卫二")
        embed.add_field(
            name="火卫二（德莫斯）",
            value=build_value(s) if s else "数据不可用",
            inline=True
        )

        await interaction.followup.send(embed=embed)

    @tree.command(name="夜灵平原", description="单独查询夜灵平原循环")
    async def cetus(interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        s = get_three_statuses().get("夜灵平原")
        if not s:
            await interaction.followup.send("夜灵平原数据不可用。")
            return
        embed = discord.Embed(title="夜灵平原", color=COLOR_OK)
        embed.add_field(name="信息", value=build_value(s), inline=False)
        await interaction.followup.send(embed=embed)

    @tree.command(name="金星", description="单独查询奥布山谷冷热")
    async def vallis(interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        s = get_three_statuses().get("金星")
        if not s:
            await interaction.followup.send("金星数据不可用。")
            return
        embed = discord.Embed(title="奥布山谷（金星）", color=COLOR_OK)
        embed.add_field(name="信息", value=build_value(s), inline=False)
        await interaction.followup.send(embed=embed)

    @tree.command(name="火卫二", description="单独查询德莫斯 Fass/Vome")
    async def cambion(interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        s = get_three_statuses().get("火卫二")
        if not s:
            await interaction.followup.send("火卫二数据不可用。")
            return
        embed = discord.Embed(title="火卫二（德莫斯）", color=COLOR_OK)
        embed.add_field(name="信息", value=build_value(s), inline=False)
        await interaction.followup.send(embed=embed)


