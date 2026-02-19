import asyncio
import time
import discord
from discord.ext import tasks
from reminder.reminder_core import pop_due_items, ts_full

def setup_time_monitor(client: discord.Client):
    """
    专门的时间监控器：独立存储和运行 Type 1 提醒的轮询逻辑
    """
    
    @tasks.loop(seconds=1.0)
    async def time_checker():
        # 确保 Bot 准备就绪后再执行，防止找不到频道
        if not client.is_ready():
            return
            
        current_ts = int(time.time())
        # 从 reminders.json 取出到期的任务
        due_items = pop_due_items(current_ts)
        
        for item in due_items:
            channel = client.get_channel(item.channel_id)
            if channel:
                # 构造艾特提醒的 UI
                embed = discord.Embed(
                    title="⏰ 定时提醒触发", 
                    description=f"您预设的提醒时间已到：**{item.item_name}**", 
                    color=0xE74C3C # 红色提醒
                )
                
                # 如果 meta 里有具体的开始时间，展示出来
                start_ts = item.meta.get("start_ts")
                if start_ts:
                    embed.add_field(name="目标事件时间", value=ts_full(int(start_ts)))
                
                embed.set_footer(text="提示：该提醒已触发并自动从活跃列表中移除。")

                try:
                    # 发送艾特消息
                    await channel.send(content=f"<@{item.user_id}>", embed=embed)
                except Exception as e:
                    print(f"发送提醒失败: {e}")

    # 启动循环任务
    time_checker.start()
    return time_checker