from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
from typing import Optional, Tuple

import discord
from discord import app_commands


DB_PATH = Path("relic_check/warframe_relics.db")

ERA_CHOICES = [
    app_commands.Choice(name="古纪 (Lith)", value="Lith"),
    app_commands.Choice(name="前纪 (Meso)", value="Meso"),
    app_commands.Choice(name="中纪 (Neo)", value="Neo"),
    app_commands.Choice(name="后纪 (Axi)", value="Axi"),
    app_commands.Choice(name="安魂 (Requiem)", value="Requiem"),
]

RELIC_CONFIG = {
    0: {"label": "正常掉落 (Available)", "color": 0x2ECC71, "icon": "🟢"},
    1: {"label": "已入库 (Vaulted)", "color": 0xE74C3C, "icon": "🔴"},
    2: {"label": "奸商特供 (Baro Only)", "color": 0xF1C40F, "icon": "🟡"},
    3: {"label": "回归中 (Resurgence)", "color": 0x3498DB, "icon": "🔵"},
}

COLOR_ERR = 0xE74C3C
COLOR_INFO = 0x2ECC71




@dataclass(frozen=True)
class RelicRow:
    status_code: int
    last_updated: str



_CODE_RE = re.compile(r"^[A-Z]\d{1,3}$")  # L7 / B8 / A10 / etc.

def normalize_code(raw: str) -> Optional[str]:
    s = raw.strip().upper()
    s = s.replace("核桃", "").replace("RELIC", "").strip()
    s = re.sub(r"\s+", "", s)
    if _CODE_RE.match(s):
        return s
    return None


def full_relic_name(era: str, code: str) -> str:
    return f"{era} {code} Relic"


def db_query_relic(name: str, db_path: Path = DB_PATH) -> Optional[RelicRow]:
    if not db_path.exists():
        raise FileNotFoundError(f"找不到数据库文件：{db_path}")

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute(
            "SELECT is_vaulted, last_updated FROM relics WHERE name = ?",
            (name,)
        )
        row = cur.fetchone()

    if not row:
        return None

    return RelicRow(status_code=int(row["is_vaulted"]), last_updated=str(row["last_updated"]))


def build_embed(era: str, code: str, result: RelicRow) -> discord.Embed:
    cfg = RELIC_CONFIG.get(result.status_code, {"label": "未知", "color": 0x95A5A6, "icon": "❓"})

    embed = discord.Embed(
        title=f"{cfg['icon']} {era} {code} 核桃",
        color=cfg["color"],
        description="（数据来自本地数据库缓存）",
    )

    embed.add_field(name="判定结果", value=f"**{cfg['label']}**", inline=False)

    if result.status_code == 3:
        embed.set_footer(text="提示：当前该核桃可通过阿娅换取（Prime Resurgence）。")
    elif result.status_code == 1:
        embed.set_footer(text="提示：该核桃已入库（Vaulted），主要通过玩家交易/历史库存获取。")
    elif result.status_code == 2:
        embed.set_footer(text=f"提示：该核桃主要来源于虚空商人/特殊轮换。最后核查：{result.last_updated}")
    else:
        embed.set_footer(text=f"最后核查时间：{result.last_updated}")

    return embed


def build_error(title: str, msg: str) -> discord.Embed:
    e = discord.Embed(title=title, description=msg, color=COLOR_ERR)
    return e




def setup(tree: app_commands.CommandTree):
    @tree.command(name="核桃", description="查询核桃是否入库/回归/奸商")
    @app_commands.choices(era=ERA_CHOICES)
    @app_commands.describe(era="选择核桃的纪元", name="输入核桃代号（例如: L7, B8）")
    async def relic_check(
        interaction: discord.Interaction,
        era: app_commands.Choice[str],
        name: str
    ):
        await interaction.response.defer(thinking=False)

        selected_era = era.value
        code = normalize_code(name)
        if not code:
            embed = build_error(
                "核桃查询失败",
                "输入格式不对。\n示例：`L7`、`B8`、`A10`（不需要加 Relic）。"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        relic_name = full_relic_name(selected_era, code)

        try:
            row = db_query_relic(relic_name, DB_PATH)
            if row is None:
                embed = discord.Embed(
                    title="⚪ 未找到记录",
                    color=COLOR_INFO,
                    description=f"数据库中未找到 **{relic_name}**。\n请确认纪元和代号是否正确。"
                )
                embed.set_footer(text="提示：你可以尝试换一个纪元或检查拼写。")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            embed = build_embed(selected_era, code, row)
            await interaction.followup.send(embed=embed)

        except FileNotFoundError as e:
            embed = build_error("核桃查询失败", str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)

        except sqlite3.OperationalError as e:
            # 比如表不存在
            embed = build_error("核桃查询失败", f"数据库结构错误：{e}")
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            embed = build_error("核桃查询失败", f"系统查询故障：{e}")
            await interaction.followup.send(embed=embed, ephemeral=True)
