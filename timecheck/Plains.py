# timecheck/Plains.py
# UI层：只负责把 cycle_core 的标准化结果（已滚动到未来）展示成 Altair 风格的中文 Embed

import discord
from discord import app_commands
from timecheck.cycle_core import get_three_statuses, CycleStatus

COLOR_OK = 0x2ECC71
COLOR_ERROR = 0xE74C3C  # 报错使用红色

def ts_relative(unix: int) -> str:
    # 增加安全性检查，如果时间戳为 0，返回未知
    if unix <= 0: return "未知"
    return f"<t:{unix}:R>"

def state_display(area: str, key: str) -> str:
    if area == "夜灵平原":
        return " 白天" if key == "day" else " 夜晚"
    if area == "金星":
        return " 温暖" if key == "warm" else " 寒冷"
    if area == "火卫二":
        return " Fass (发疯)" if key == "fass" else " Vome (沉睡)"
    return key

def build_value(s: CycleStatus) -> str:
    if not s:
        return "❌ 数据获取失败"
    return (
        f"状态：**{state_display(s.area, s.state_key)}**\n"
        f"切换：{ts_relative(s.next_change_ts)}"
    )

def setup(tree: app_commands.CommandTree):

    @tree.command(name="平原", description="查询夜灵平原 / 金星 / 火卫二循环（按观看者本地时间显示）")
    async def overview(interaction: discord.Interaction):
        # defer(thinking=True) 给 API 请求留出缓冲时间
        await interaction.response.defer(thinking=True)

        statuses = get_three_statuses()

        # 如果全部数据都拿不到，直接报错
        if not statuses:
            embed = discord.Embed(
                title="❌ 状态获取失败",
                description="无法连接到 Warframe API 服务器，请稍后再试。",
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(
            title="🪐 开放世界循环状态",
            description="时间已自动本地化；数据已对齐到下一次切换",
            color=COLOR_OK
        )

        # 封装一个内部函数来处理字段添加，保持代码整洁
        def add_area_field(display_name, internal_name):
            s_data = statuses.get(internal_name)
            embed.add_field(
                name=display_name,
                value=build_value(s_data),
                inline=True
            )

        add_area_field(" 夜灵平原 (地球)", "夜灵平原")
        add_area_field(" 奥布山谷 (金星)", "金星")
        add_area_field(" 坎比翁荒原 (火卫二)", "火卫二")

        embed.set_footer(text="数据源：WarframeStat | 自动更新")
        await interaction.followup.send(embed=embed)

    # --- 单独查询命令优化 ---

    async def single_area_response(interaction: discord.Interaction, area_name: str, title: str):
        await interaction.response.defer(thinking=True)
        s = get_three_statuses().get(area_name)
        if not s:
            await interaction.followup.send(f"❌ {area_name} 数据暂不可用，请稍后重试。")
            return
        
        embed = discord.Embed(title=title, color=COLOR_OK)
        embed.add_field(name="当前状态", value=build_value(s), inline=False)
        await interaction.followup.send(embed=embed)

    @tree.command(name="夜灵平原", description="单独查询夜灵平原循环")
    async def cetus(interaction: discord.Interaction):
        await single_area_response(interaction, "夜灵平原", " 夜灵平原 (地球)")

    @tree.command(name="金星", description="单独查询奥布山谷冷热")
    async def vallis(interaction: discord.Interaction):
        await single_area_response(interaction, "金星", " 奥布山谷 (金星)")

    @tree.command(name="火卫二", description="单独查询德莫斯 Fass/Vome")
    async def cambion(interaction: discord.Interaction):
        await single_area_response(interaction, "火卫二", " 坎比翁荒原 (火卫二)")