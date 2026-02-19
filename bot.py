import os
import discord
from dotenv import load_dotenv

load_dotenv()

# 1. 基础功能模块
from timecheck.Plains import setup as setup_plains
from wf_market.market_commands import setup as setup_market
from relic_check.relic_commands import setup as setup_relic

# 2. 提醒/管理模块
from reminder.cycle_reminder import setup as setup_cycle_reminder
from reminder.reminder_cancel import setup as setup_reminder_cancel
from reminder.reminder_showList import setup as setup_show_list
from wf_market.market_reminder_command import setup as setup_market_reminder

# 3. 后台监控模块
from reminder.cycle_monitor import setup_time_monitor  # 监控 Type 1
from wf_market.market_monitor import setup_monitor        # 监控 Type 2

from fissure.fissure_commands import setup as setup_fissure
from fissure.fissure_reminder_command import setup as setup_fissure_remind
from fissure.fissure_monitor import setup_fissure_monitor

class Client(discord.Client):
    def __init__(self):
        # 默认 intents，确保可以正常运行指令
        super().__init__(intents=discord.Intents.default())
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        # --- 挂载业务命令 ---
        setup_plains(self.tree)
        setup_relic(self.tree)
        setup_market(self.tree)
        
        # --- 挂载提醒系列功能 ---
        setup_cycle_reminder(self.tree, self)    # 设置平原提醒 (Type 1)
        setup_market_reminder(self.tree)         # 设置市场提醒 (Type 2)
        setup_show_list(self.tree)               # 查看提醒列表
        setup_reminder_cancel(self.tree)         # 取消提醒
        
        setup_fissure(self.tree)
        setup_fissure_remind(self.tree)

        # --- 启动并行监控任务 ---
        # 启动时间轮询监控 (Type 1)
        self.time_monitor = setup_time_monitor(self)
        
        # 启动市场价格监控 (Type 2)
        self.market_monitor = setup_monitor(self)
        
        self.fissure_monitor = setup_fissure_monitor(self)

        print("🚀 正在同步 Discord 命令菜单...")
        await self.tree.sync()
        print("✅ 所有功能加载完毕，监控服务已上线！")

    async def on_ready(self):
        print(f"✅ Bot 已就绪：{self.user}")

if __name__ == "__main__":
    # 从 .env 读取 Token
    token = os.getenv("DISCORD_TOKEN")
    if token:
        # 启动机器人
        Client().run(token)
    else:
        print("❌ 错误：未在 .env 文件中找到 DISCORD_TOKEN")