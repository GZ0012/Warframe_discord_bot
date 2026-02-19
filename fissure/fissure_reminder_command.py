import discord
from discord import app_commands
from reminder.reminder_core import ReminderItem, add_item
from fissure.fissure_core import TRANSLATION

COLOR_MARKET_GREEN = 0x2ECC71 

def setup(tree: app_commands.CommandTree):
    @tree.command(name="提醒_裂缝", description="监控特定类型的虚空裂缝任务")
    @app_commands.describe(
        mission="选择要监控的任务类型",
        difficulty="选择难度限制 (默认: 全部)"
    )
    @app_commands.choices(
        mission=[
            app_commands.Choice(name="挖掘", value="Excavation"),
            app_commands.Choice(name="生存", value="Survival"),
            app_commands.Choice(name="捕获", value="Capture"),
            app_commands.Choice(name="中断", value="Disruption"),
            app_commands.Choice(name="间谍", value="Spy"),
            app_commands.Choice(name="歼灭", value="Extermination"),
            app_commands.Choice(name="前哨战 (九重天)", value="Skirmish"),
            app_commands.Choice(name="防御", value="Defense"),
            app_commands.Choice(name="救援", value="Rescue")
        ],
        difficulty=[
            app_commands.Choice(name="普通", value="normal"),
            app_commands.Choice(name="钢铁之路", value="hard"),
            app_commands.Choice(name="虚空风暴 (九重天)", value="storm"),
            app_commands.Choice(name="全部", value="all")
        ]
    )
    async def fissure_remind(interaction: discord.Interaction, mission: str, difficulty: str = "all"):
        user_id = interaction.user.id
        channel_id = interaction.channel_id
        
        # 1. 准备展示文本
        mission_zh = TRANSLATION.get(mission, mission)
        diff_map = {"normal": "普通", "hard": "钢铁", "storm": "虚空风暴", "all": "全部"}
        diff_zh = diff_map.get(difficulty)
        
        # 2. 创建条目 - 借用 trade_type 存储难度，避免 AttributeError
        new_item = ReminderItem(
            user_id=user_id,
            channel_id=channel_id,
            item_name=f"裂缝提醒: {mission_zh} ({diff_zh})",
            reminder_type=3,
            target_mission=mission,
            trade_type=difficulty,  # trade_type will be difficulty
            enabled=True
        )
        
        try:
            add_item(new_item)
            embed = discord.Embed(
                title="✅ 裂缝提醒任务已创建",
                color=COLOR_MARKET_GREEN
            )
            embed.add_field(name=" 任务类型", value=f"`{mission_zh}`", inline=True)
            embed.add_field(name=" 难度限制", value=f"`{diff_zh}`", inline=True)
        
            embed.set_footer(text="出现匹配裂缝时将在此艾特提醒")

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"创建提醒失败: {e}", ephemeral=True)