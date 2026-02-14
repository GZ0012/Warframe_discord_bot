# reminder/reminder_core.py
# 一次性提醒（One-shot）基础设施：存储、读取、删除、格式化时间戳

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

DB_PATH = Path("reminders.json")


def ts_full(unix: int) -> str:
    return f"<t:{unix}:f>"


def ts_relative(unix: int) -> str:
    return f"<t:{unix}:R>"


@dataclass
class ReminderItem:
    id: str
    kind: str              # e.g. "cycle"
    title: str

    user_id: int
    channel_id: int

    trigger_ts: int        # 触发时间（unix 秒）
    meta: dict             # 保存额外信息（area/target/min_before/start_ts等）
    enabled: bool = True


def _load_raw() -> list:
    if DB_PATH.exists():
        try:
            return json.loads(DB_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_raw(items: list) -> None:
    DB_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def load_items() -> List[ReminderItem]:
    raw = _load_raw()
    out: List[ReminderItem] = []
    for x in raw:
        try:
            out.append(ReminderItem(**x))
        except Exception:
            continue
    return out


def save_items(items: List[ReminderItem]) -> None:
    _save_raw([asdict(x) for x in items])


def new_id() -> str:
    return uuid.uuid4().hex[:10]


def add_item(item: ReminderItem) -> None:
    items = load_items()
    items.append(item)
    save_items(items)


def list_items(user_id: int, only_enabled: bool = True) -> List[ReminderItem]:
    items = load_items()
    out = [x for x in items if x.user_id == user_id]
    if only_enabled:
        out = [x for x in out if x.enabled]
    out.sort(key=lambda r: r.trigger_ts)
    return out


def get_item_by_index(user_id: int, idx_1based: int) -> Optional[ReminderItem]:
    lst = list_items(user_id, only_enabled=True)
    if 1 <= idx_1based <= len(lst):
        return lst[idx_1based - 1]
    return None


def disable_item(item_id: str) -> bool:
    items = load_items()
    changed = False
    for it in items:
        if it.id == item_id and it.enabled:
            it.enabled = False
            changed = True
            break
    if changed:
        save_items(items)
    return changed


def delete_item(item_id: str) -> bool:
    items = load_items()
    new_items = [x for x in items if x.id != item_id]
    if len(new_items) != len(items):
        save_items(new_items)
        return True
    return False


def pop_due_items(now_ts: int) -> List[ReminderItem]:
    """
    取出到期提醒（enabled 且 trigger_ts <= now），并在库里把它们标记为 disabled（一次性提醒）
    """
    items = load_items()
    due: List[ReminderItem] = []
    changed = False

    for it in items:
        if it.enabled and it.trigger_ts <= now_ts:
            it.enabled = False
            due.append(it)
            changed = True

    if changed:
        save_items(items)
    return due
