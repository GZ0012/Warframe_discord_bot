from __future__ import annotations
import json
import uuid
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

DB_PATH = Path("reminders.json")

def ts_full(unix: int) -> str: return f"<t:{int(unix)}:f>"
def ts_relative(unix: int) -> str: return f"<t:{int(unix)}:R>"

@dataclass
class ReminderItem:
    user_id: int
    channel_id: int
    item_name: str
    reminder_type: int 
    type: str = "custom"            
    trigger_ts: Optional[int] = 0   
    target_price: Optional[int] = 0 
    rank: Optional[int] = None      
    trade_type: Optional[str] = None 
    slug: Optional[str] = None
    
    # --- Type 3 裂缝提醒新增字段 ---
    target_mission: Optional[str] = None    # 存储任务英文名, 如 Excavation
    target_is_storm: bool = False           # 是否仅限九重天 (虚空风暴)
    
    id: str = ""
    meta: dict = None
    enabled: bool = True

    def __post_init__(self):
        if not self.id: self.id = uuid.uuid4().hex[:10]
        if self.meta is None: self.meta = {}

def load_items() -> List[ReminderItem]:
    if not DB_PATH.exists(): return []
    try:
        raw = json.loads(DB_PATH.read_text(encoding="utf-8"))
        # 因为使用了 **x 解包，JSON 中缺失的新字段会自动使用 dataclass 定义的默认值
        return [ReminderItem(**x) for x in raw]
    except: return []

def save_items(items: List[ReminderItem]) -> None:
    # asdict 会自动把新字段 target_mission 等也序列化进 JSON
    data = [asdict(x) for x in items]
    DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def add_item(item: ReminderItem) -> None:
    items = load_items()
    items.append(item)
    save_items(items)

def list_items(user_id: int, only_enabled: bool = True) -> List[ReminderItem]:
    items = load_items()
    out = [x for x in items if x.user_id == user_id]
    if only_enabled: out = [x for x in out if x.enabled]
    out.sort(key=lambda r: (r.reminder_type, r.trigger_ts or 0))
    return out

def get_item_by_index(user_id: int, idx_1based: int) -> Optional[ReminderItem]:
    lst = list_items(user_id, only_enabled=True)
    if 1 <= idx_1based <= len(lst): return lst[idx_1based - 1]
    return None

def disable_item(item_id: str) -> bool:
    items = load_items()
    changed = False
    for it in items:
        if it.id == item_id and it.enabled:
            it.enabled = False
            changed = True
            break
    if changed: save_items(items)
    return changed

def pop_due_items(now_ts: int) -> List[ReminderItem]:
    items = load_items()
    due, active, changed = [], [], False
    for it in items:
        if it.reminder_type == 1 and it.enabled and it.trigger_ts <= now_ts:
            it.enabled = False
            due.append(it)
            changed = True
        active.append(it)
    if changed: save_items(active)
    return due