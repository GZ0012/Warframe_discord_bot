import discord
from discord import app_commands
from fissure.fissure_core import get_fissure_data

def setup(tree: app_commands.CommandTree):
    @tree.command(name="裂缝", description="查看当前虚空裂缝")
    @app_commands.describe(mode="选择查看特定的裂缝类型")
    @app_commands.choices(mode=[
        app_commands.Choice(name="普通", value="normal"),
        app_commands.Choice(name="钢铁", value="hard"),
        app_commands.Choice(name="虚空风暴", value="storm")
    ])
    async def fissure(interaction: discord.Interaction, mode: str = None):
        await interaction.response.defer()
        
        data = get_fissure_data()
        if not data:
            await interaction.followup.send("无法获取裂缝数据")
            return

        embeds = []

        def create_emb(title, items, color):
            if not items: return None
            emb = discord.Embed(title=title, color=color)
            for f in items:
                # 将 inline 设置为 True，使任务横向排列
                # 注意：Discord 限制一行最多显示 3 个 inline 字段
                emb.add_field(
                    name=f"{f['tier']} - {f['mission']}",
                    # 为了进一步压缩空间，我们将地点和时间放在同一行
                    value=f"{f['node']}\n{f['eta']}",
                    inline=True
                )
            return emb

        # 逻辑分发
        if mode is None or mode == "normal":
            e = create_emb("普通虚空裂缝", data["normal"], 0x3498DB)
            if e: embeds.append(e)
            
        if mode is None or mode == "hard":
            e = create_emb("钢铁之路裂缝", data["hard"], 0xE74C3C)
            if e: embeds.append(e)
            
        if mode is None or mode == "storm":
            e = create_emb("虚空风暴", data["storm"], 0xF1C40F)
            if e: embeds.append(e)

        if embeds:
            await interaction.followup.send(embeds=embeds)
        else:
            await interaction.followup.send("当前无匹配的裂缝任务")