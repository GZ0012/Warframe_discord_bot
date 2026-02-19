from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import requests


# -------------------------
# 配置
# -------------------------

WARFRAMESTAT_BASE = "https://api.warframestat.us/pc"
DB_PATH = Path("relic_check/warframe_relics.db")  # 你如果 db 在根目录就改成 Path("warframe_relics.db")

# 新闻关键词（你原本的）
NEWS_KEYWORDS = ["vault", "last chance", "retired", "prime access", "unvault"]


# -------------------------
# 工具
# -------------------------

def utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def utc_today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Accept": "application/json",
        "User-Agent": "wfhelpbot/1.0 (sync-jobs)",
    })
    return s


_RELIC_NAME_RE = re.compile(r"^(Lith|Meso|Neo|Axi|Requiem)\s+([A-Za-z]\d{1,3})\s+Relic$", re.IGNORECASE)

def normalize_relic_name(raw: str) -> Optional[str]:
    """
    把 warframestat vaultTrader inventory 里出现的 item 字符串标准化为：
      'Lith L7 Relic' 这种
    """
    if not raw:
        return None

    # 去掉括号内容： "Lith L7 Relic (Radiant)" -> "Lith L7 Relic"
    base = raw.split("(")[0].strip()

    # 必须包含 Relic
    if "Relic" not in base:
        return None

    # 压缩空格
    base = re.sub(r"\s+", " ", base)

    m = _RELIC_NAME_RE.match(base)
    if not m:
        # 有些源可能写成 "Lith L7" 或别的，这里做一次兜底解析
        parts = base.replace("Relic", "").strip().split()
        if len(parts) >= 2:
            era = parts[0].capitalize()
            code = parts[1].upper()
            if era.lower() in {"lith", "meso", "neo", "axi", "requiem"} and re.match(r"^[A-Z]\d{1,3}$", code):
                return f"{era} {code} Relic"
        return None

    era = m.group(1).capitalize()
    code = m.group(2).upper()
    return f"{era} {code} Relic"


def ensure_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news_seen (
            key TEXT PRIMARY KEY,
            seen_at TEXT NOT NULL
        )
    """)
    conn.commit()


def meta_get(conn: sqlite3.Connection, key: str) -> Optional[str]:
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = cur.fetchone()
    return row[0] if row else None


def meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    cur = conn.cursor()
    cur.execute("INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    conn.commit()


def should_run_today(conn: sqlite3.Connection) -> bool:
    """
    一天只跑一次（按 UTC 日期）
    """
    last = meta_get(conn, "last_daily_sync_utc")
    today = utc_today_key()
    return last != today


def mark_ran_today(conn: sqlite3.Connection) -> None:
    meta_set(conn, "last_daily_sync_utc", utc_today_key())


def news_was_seen(conn: sqlite3.Connection, key: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM news_seen WHERE key = ?", (key,))
    return cur.fetchone() is not None


def mark_news_seen(conn: sqlite3.Connection, key: str) -> None:
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO news_seen(key, seen_at) VALUES(?, ?)", (key, utc_now_str()))
    conn.commit()


# -------------------------
# 任务 1：同步 Prime Resurgence（vaultTrader）
# -------------------------

@dataclass
class SyncResurgenceStats:
    found: int
    updated: int


def sync_resurgence(conn: sqlite3.Connection, session: requests.Session) -> SyncResurgenceStats:
    """
    - 先把所有 is_vaulted=3 的核桃重置回 1（vaulted）
    - 再把 vaultTrader 当前售卖的 relic 标记为 3（resurgence）
    """
    url = f"{WARFRAMESTAT_BASE}/vaultTrader?language=en"
    print("🔄 [Resurgence] 正在从 vaultTrader 抓取当前回归核桃...")

    r = session.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    names: list[str] = []
    for item in data.get("inventory", []) or []:
        item_name = item.get("item", "")
        norm = normalize_relic_name(item_name)
        if norm:
            names.append(norm)

    if not names:
        print("ℹ️ [Resurgence] 当前 vaultTrader inventory 没检测到核桃。")
        return SyncResurgenceStats(found=0, updated=0)

    now = utc_now_str()
    cur = conn.cursor()

    # 重置旧的 resurgence
    cur.execute("UPDATE relics SET is_vaulted = 1, last_updated = ? WHERE is_vaulted = 3", (now,))

    updated = 0
    for relic_name in names:
        cur.execute(
            "UPDATE relics SET is_vaulted = 3, last_updated = ? WHERE name = ?",
            (now, relic_name)
        )
        if cur.rowcount > 0:
            updated += 1

    conn.commit()
    print(f"✅ [Resurgence] 同步完成：抓到 {len(names)} 个回归核桃，成功更新 {updated} 条数据库记录。")
    return SyncResurgenceStats(found=len(names), updated=updated)


# -------------------------
# 任务 2：扫描 News（可扩展成更新 DB 的触发器）
# -------------------------

def scan_news(conn: sqlite3.Connection, session: requests.Session, max_items: int = 10) -> int:
    url = f"{WARFRAMESTAT_BASE}/news?language=en"
    print("📰 [News] 正在扫描近期官方新闻...")

    r = session.get(url, timeout=10)
    r.raise_for_status()
    news_list = r.json() or []

    hits = 0
    for news in news_list[:max_items]:
        msg = (news.get("message") or "").strip()
        msg_l = msg.lower()
        link = (news.get("link") or "").strip()
        eta = (news.get("eta") or "").strip()

        # 去重 key：优先 link，没有就用 message+eta
        key = link or f"{eta}|{msg_l[:120]}"

        if not msg:
            continue
        if not any(k in msg_l for k in NEWS_KEYWORDS):
            continue
        if news_was_seen(conn, key):
            continue

        hits += 1
        mark_news_seen(conn, key)

        print("-" * 42)
        print("📢 发现变动预警:")
        print(msg)
        if link:
            print("🔗 详情:", link)
        if eta:
            print("⏰ 时间:", eta)

    if hits == 0:
        print("ℹ️ [News] 没发现新的关键词命中新闻（或都已看过）。")
    else:
        print(f"✅ [News] 本次新增命中 {hits} 条。")
    return hits


# -------------------------
# 统一入口：每日同步
# -------------------------

def run_daily_sync() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"❌ 找不到数据库：{DB_PATH.resolve()}")

    with sqlite3.connect(str(DB_PATH)) as conn:
        ensure_tables(conn)

        if not should_run_today(conn):
            print(f"⏭️ 今日（UTC {utc_today_key()}）已同步过，跳过。")
            return

        session = get_session()
        try:
            sync_resurgence(conn, session)
            scan_news(conn, session, max_items=10)

            # 标记今日已跑
            mark_ran_today(conn)
            print(f"✅ 今日同步完成（UTC {utc_today_key()}）。")

        finally:
            session.close()


if __name__ == "__main__":
    run_daily_sync()
