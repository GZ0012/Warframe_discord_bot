
import asyncio
import time
import discord
from discord import app_commands
from typing import List


from timecheck.cycle_core import get_three_statuses, next_state_start_ts, CycleStatus
from reminder.reminder_core import (
    ReminderItem, new_id, add_item,
    list_items, pop_due_items,
    ts_full, ts_relative
)

COLOR_OK = 0x2ECC71
COLOR_ALERT = 0xE74C3C

def now_ts() -> int:
    return int(time.time())

AREA_MAP = {
    "夜灵平原": [("夜晚 🌙", "night"), ("白天 🌞", "day")],
    "金星": [("寒冷 ❄", "cold"), ("温暖 🔥", "warm")],
    "火卫二": [("Vome", "vome"), ("Fass", "fass")]
}

def display_target(area: str, key: str) -> str:
    for name, k in AREA_MAP.get(area, []):
        if k == key: return name
    return key

def compute_cycle_times(status: CycleStatus, target_key: str, minutes_before: int) -> tuple[int, int]:
    start_ts = next_state_start_ts(
        now_key=status.state_key,
        now_change_ts=status.next_change_ts,
        target_key=target_key,
        pattern=status.pattern
    )
    if start_ts <= 0: return (0, 0)

    now = now_ts()
    cycle_len = sum(d for _, d in status.pattern)
    trigger_ts = start_ts - max(0, minutes_before) * 60

    while trigger_ts <= (now + 2):
        start_ts += cycle_len
        trigger_ts = start_ts - max(0, minutes_before) * 60

    return (start_ts, trigger_ts)

async def scheduler_loop(client: discord.Client):
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            due = pop_due_items(now_ts())
            for it in due:
                ch = client.get_channel(int(it.channel_id))
                if not ch: continue
                meta = it.meta or {}
                embed = discord.Embed(title="⏰ 提醒触发", color=COLOR_ALERT)
                embed.description = f"<@{it.user_id}> 预定时间已到！"
                embed.add_field(name="区域", value=f"**{meta.get('area')}**", inline=True)
                embed.add_field(name="目标", value=f"**{meta.get('target_text')}**", inline=True)
                st = int(meta.get('start_ts', 0))
                embed.add_field(name="目标开始时间", value=f"{ts_full(st)}\n{ts_relative(st)}", inline=False)
                await ch.send(content=f"<@{it.user_id}>", embed=embed)
        except: pass
        await asyncio.sleep(1)

# -------- 命令与自动补全 --------
def setup(tree: app_commands.CommandTree, client: discord.Client):
    if not getattr(client, "_cycle_reminder_loop_started", False):
        client._cycle_reminder_loop_started = True
        client.loop.create_task(scheduler_loop(client))

    @tree.command(name="提醒", description="设置平原提醒（根据区域自动过滤状态）")
    @app_commands.describe(区域="选择开放世界", 状态="根据区域选择对应状态", 提前分钟="提前多少分钟提醒")
    @app_commands.choices(区域=[
        app_commands.Choice(name="夜灵平原 (Cetus)", value="夜灵平原"),
        app_commands.Choice(name="奥布山谷 (金星)", value="金星"),
        app_commands.Choice(name="魔方提灯 (火卫二)", value="火卫二"),
    ])
    async def remind(interaction: discord.Interaction, 区域: app_commands.Choice[str], 状态: str, 提前分钟: int = 0):
        await interaction.response.defer()
        
        area = 区域.value
        statuses = get_three_statuses()
        status = statuses.get(area)
        
        if not status:
            await interaction.followup.send("❌ 无法获取 API 数据。")
            return

        start_ts, trigger_ts = compute_cycle_times(status, 状态, 提前分钟)
        target_text = display_target(area, 状态)

        add_item(ReminderItem(
            id=new_id(), kind="cycle", title=f"{area}-{target_text}",
            user_id=interaction.user.id, channel_id=interaction.channel_id,
            trigger_ts=trigger_ts,
            meta={"area": area, "target_text": target_text, "start_ts": start_ts, "minutes_before": 提前分钟}
        ))

        embed = discord.Embed(title="✅ 提醒设置成功", color=COLOR_OK)
        embed.add_field(name="目标", value=f"**{area} - {target_text}**", inline=False)
        embed.add_field(name="开始时间", value=f"{ts_full(start_ts)}\n{ts_relative(start_ts)}", inline=False)
        embed.add_field(name="提醒时间", value=f"{ts_full(trigger_ts)}\n{ts_relative(trigger_ts)}", inline=False)
        await interaction.followup.send(embed=embed)


    @remind.autocomplete("状态")
    async def remind_status_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    
        area_choice = interaction.namespace.区域
        if not area_choice:
            return [app_commands.Choice(name="请先选择区域", value="none")]
        
    
        options = AREA_MAP.get(area_choice, [])
        return [
            app_commands.Choice(name=name, value=value) 
            for name, value in options if current.lower() in name.lower()
        ]


    @tree.command(name="提醒列表", description="查看已设置的提醒")
    async def remind_list(interaction: discord.Interaction):
        lst = list_items(interaction.user.id, only_enabled=True)
        if not lst:
            await interaction.response.send_message("目前没有提醒。")
            return
        embed = discord.Embed(title="提醒清单", color=COLOR_OK)
        for i, it in enumerate(lst, 1):
            meta = it.meta or {}
            embed.add_field(name=f"{i}. {it.title}", value=f"触发：{ts_full(it.trigger_ts)}", inline=False)
        await interaction.response.send_message(embed=embed)