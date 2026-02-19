import time
import requests
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# API 地址
COMMUNITY_API = "https://api.warframestat.us/pc"
OFFICIAL_API = "https://content.warframe.com/dynamic/worldState.php"
HEADERS = {"accept": "application/json", "User-Agent": "Mozilla/5.0"}

# 周期长度（秒）
CETUS_DAY, CETUS_NIGHT = 100 * 60, 50 * 60
VALLIS_WARM, VALLIS_COLD = 6 * 60 + 40, 20 * 60
CAMBION_FASS, CAMBION_VOME = 100 * 60, 50 * 60

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
    try:
        if dt_str.isdigit(): return int(dt_str) // 1000 
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except:
        return 0

# --- 核心：双源自愈获取函数 ---
def get_worldstate() -> Tuple[Optional[dict], str]:
    ts = now_ts()
    # 方案 A: 尝试社区 API
    try:
        url = f"{COMMUNITY_API}?_={ts}"
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            return r.json(), "community"
    except:
        pass

    # 方案 B: 尝试官方原始 API
    try:
        r = requests.get(OFFICIAL_API, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.json(), "official"
    except:
        pass
    
    return None, "none"

# --- 核心逻辑函数 (提醒模块必用) ---

def roll_to_future(expiry_ts: int, cur_key: str, pattern: Pattern):
    """滚动状态直到 expiry_ts 在未来"""
    if expiry_ts <= 0 or not pattern:
        return expiry_ts, cur_key
    idx = next((i for i, (k, _) in enumerate(pattern) if k == cur_key), 0)
    n, now = len(pattern), now_ts()
    while expiry_ts <= now:
        idx = (idx + 1) % n
        expiry_ts += pattern[idx][1]
        cur_key = pattern[idx][0]
    return expiry_ts, cur_key

def next_state_start_ts(now_key: str, now_change_ts: int, target_key: str, pattern: Pattern) -> int:
    """
    计算下一次 target_key 开始的时间戳
    这是提醒模块计算‘还有多久到夜晚’的核心逻辑
    """
    if now_change_ts <= 0 or not pattern: return 0
    idx = next((i for i, (k, _) in enumerate(pattern) if k == now_key), 0)
    n, t = len(pattern), now_change_ts
    for step in range(1, n + 1):
        j = (idx + step) % n
        k, dur = pattern[j]
        if k == target_key: return t
        t += dur
    return 0

# --- 官方解析逻辑 ---

def parse_official_cetus(data: dict) -> Optional[dict]:
    try:
        syndicates = data.get("SyndicateMissions", [])
        cetus = next((s for s in syndicates if s.get("Tag") == "CetusSyndicate"), None)
        if not cetus: return None
        expiry_ms = int(cetus["Expiry"]["$date"]["$numberLong"])
        expiry_ts = expiry_ms // 1000
        time_left = expiry_ts - now_ts()
        is_day = time_left > (50 * 60)
        return {"expiry": datetime.fromtimestamp(expiry_ts).isoformat(), "isDay": is_day}
    except:
        return None

# --- 各平原数据处理 ---

def get_cetus_status(data: dict, source: str) -> Optional[CycleStatus]:
    if source == "official":
        c = parse_official_cetus(data)
    else:
        c = data.get("cetusCycle", {})
    if not c or c.get("expiry") is None: return None
    pattern = [("day", CETUS_DAY), ("night", CETUS_NIGHT)]
    cur_key = "day" if c.get("isDay") else "night"
    expiry2, key2 = roll_to_future(iso_to_unix(c["expiry"]), cur_key, pattern)
    return CycleStatus("夜灵平原", pattern, key2, expiry2, c)

def get_vallis_status(data: dict, source: str) -> Optional[CycleStatus]:
    if source == "official": return None
    c = data.get("vallisCycle", {})
    if not c or c.get("expiry") is None: return None
    pattern = [("warm", VALLIS_WARM), ("cold", VALLIS_COLD)]
    expiry2, key2 = roll_to_future(iso_to_unix(c["expiry"]), "warm" if c.get("isWarm") else "cold", pattern)
    return CycleStatus("金星", pattern, key2, expiry2, c)

def get_cambion_status(data: dict, source: str) -> Optional[CycleStatus]:
    if source == "official": return None
    c = data.get("cambionCycle", {})
    state_raw = c.get("state") or c.get("active")
    if not c or c.get("expiry") is None or not state_raw: return None
    pattern = [("fass", CAMBION_FASS), ("vome", CAMBION_VOME)]
    cur_key = "fass" if str(state_raw).strip().lower() == "fass" else "vome"
    expiry2, key2 = roll_to_future(iso_to_unix(c["expiry"]), cur_key, pattern)
    return CycleStatus("火卫二", pattern, key2, expiry2, c)

def get_three_statuses() -> Dict[str, CycleStatus]:
    data, source = get_worldstate()
    out = {}
    if not data: return out
    s1 = get_cetus_status(data, source)
    if s1: out[s1.area] = s1
    s2 = get_vallis_status(data, source)
    if s2: out[s2.area] = s2
    s3 = get_cambion_status(data, source)
    if s3: out[s3.area] = s3
    return out