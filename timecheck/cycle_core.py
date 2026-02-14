
from __future__ import annotations
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

import requests

API_BASE = "https://api.warframestat.us/pc"
HEADERS = {"accept": "application/json"}


CETUS_DAY = 100 * 60
CETUS_NIGHT = 50 * 60

VALLIS_WARM = 6 * 60 + 40   # 6m40s
VALLIS_COLD = 20 * 60       # 20m

CAMBION_FASS = 100 * 60
CAMBION_VOME = 50 * 60

Pattern = List[Tuple[str, int]] 


@dataclass
class CycleStatus:
    area: str
    pattern: Pattern
    state_key: str        
    next_change_ts: int   
    raw: Dict[str, Any]   


def now_ts() -> int:
    return int(time.time())


def iso_to_unix(dt_str: str) -> int:
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return int(dt.timestamp())


def get_worldstate() -> dict:
    ts = now_ts()
    url = f"{API_BASE}?_={ts}"

    headers = dict(HEADERS)
    headers["Cache-Control"] = "no-cache"
    headers["Pragma"] = "no-cache"

    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()



def roll_to_future(expiry_ts: int, cur_key: str, pattern: Pattern):
    if expiry_ts <= 0 or not pattern:
        return expiry_ts, cur_key

    idx = next((i for i, (k, _) in enumerate(pattern) if k == cur_key), 0)
    n = len(pattern)
    now = now_ts()

    while expiry_ts <= now:
        idx = (idx + 1) % n
        expiry_ts += pattern[idx][1]
        cur_key = pattern[idx][0]

    return expiry_ts, cur_key




def next_state_start_ts(now_key: str, now_change_ts: int, target_key: str, pattern: Pattern) -> int:

    if now_change_ts <= 0 or not pattern:
        return 0

    idx = next((i for i, (k, _) in enumerate(pattern) if k == now_key), 0)
    n = len(pattern)

    t = now_change_ts  
    for step in range(1, n + 1):
        j = (idx + step) % n
        k, dur = pattern[j]
        if k == target_key:
            return t
        t += dur
    return 0


def get_cetus_status(data: dict) -> Optional[CycleStatus]:
    c = data.get("cetusCycle", {})
    if c.get("expiry") is None or c.get("isDay") is None:
        return None

    pattern: Pattern = [("day", CETUS_DAY), ("night", CETUS_NIGHT)]
    cur_key = "day" if c["isDay"] else "night"
    expiry = iso_to_unix(c["expiry"])
    expiry2, key2 = roll_to_future(expiry, cur_key, pattern)

    return CycleStatus(area="夜灵平原", pattern=pattern, state_key=key2, next_change_ts=expiry2, raw=c)


def get_vallis_status(data: dict) -> Optional[CycleStatus]:
    c = data.get("vallisCycle", {})
    if c.get("expiry") is None or c.get("isWarm") is None:
        return None

    pattern: Pattern = [("warm", VALLIS_WARM), ("cold", VALLIS_COLD)]
    cur_key = "warm" if c["isWarm"] else "cold"
    expiry = iso_to_unix(c["expiry"])
    expiry2, key2 = roll_to_future(expiry, cur_key, pattern)

    return CycleStatus(area="金星", pattern=pattern, state_key=key2, next_change_ts=expiry2, raw=c)


def get_cambion_status(data: dict) -> Optional[CycleStatus]:
    c = data.get("cambionCycle", {})
    state_raw = c.get("state") or c.get("active")
    if c.get("expiry") is None or not state_raw:
        return None

    pattern: Pattern = [("fass", CAMBION_FASS), ("vome", CAMBION_VOME)]
    s = str(state_raw).strip().lower()
    cur_key = "fass" if s == "fass" else "vome"
    expiry = iso_to_unix(c["expiry"])
    expiry2, key2 = roll_to_future(expiry, cur_key, pattern)

    return CycleStatus(area="火卫二", pattern=pattern, state_key=key2, next_change_ts=expiry2, raw=c)


def get_three_statuses() -> Dict[str, CycleStatus]:
    data = get_worldstate()
    out: Dict[str, CycleStatus] = {}

    s1 = get_cetus_status(data)
    s2 = get_vallis_status(data)
    s3 = get_cambion_status(data)

    if s1:
        out[s1.area] = s1
    if s2:
        out[s2.area] = s2
    if s3:
        out[s3.area] = s3

    return out


