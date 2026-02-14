# bot.py
import os
import discord
from dotenv import load_dotenv

load_dotenv()

from timecheck.Plains import setup as setup_plains
from reminder.cycle_reminder import setup as setup_cycle_reminder
from reminder.reminder_cancel import setup as setup_reminder_cancel
from wf_market.market_commands import setup as setup_market
from relic_check.relic_commands import setup as setup_relic

class Client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        setup_plains(self.tree)
        setup_cycle_reminder(self.tree, self)
        setup_reminder_cancel(self.tree)
        setup_market(self.tree)
        setup_relic(self.tree)

        print("正在强制同步命令菜单到 Discord...")
        await self.tree.sync()
        print("同步成功！")

    async def on_ready(self):
        print(f"✅ Bot 已就绪：{self.user}")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    Client().run(token)