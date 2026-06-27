"""Centralized data loading, saving, validation with caching — supports SQLite + JSON."""
from pathlib import Path
import json
import sqlite3
from datetime import datetime, timezone
import streamlit as st
from config.constants import VALIDATION, VALID_TECH_ROUTES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SITES_FILE = PROJECT_ROOT / "config" / "sites.json"
COMPETITORS_FILE = PROJECT_ROOT / "config" / "competitors.json"
STATIONS_FILE = PROJECT_ROOT / "config" / "stations.json"
DB_FILE = PROJECT_ROOT / "data" / "city_cluster.db"
STATIONS_DB_JSON = PROJECT_ROOT / "data" / "stations_from_db.json"
TRADING_SNAPSHOT_JSON = PROJECT_ROOT / "data" / "trading_snapshot_from_db.json"


@st.cache_data(ttl=300)
def load_sites() -> list[dict]:
    """Load production sites from JSON with cache (30s TTL)."""
    try:
        with open(SITES_FILE, "r", encoding="utf-8") as f:
            sites = json.load(f)
        if not isinstance(sites, list):
            return []
        return sites
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"基地数据加载失败: {e}")
        return []


def save_sites(sites: list[dict]) -> tuple[bool, str]:
    """Save sites to JSON with validation and timestamp. Returns (ok, message)."""
    # Validate
    errors = validate_sites(sites)
    if errors:
        return False, f"数据校验失败:\n" + "\n".join(f"  • {e}" for e in errors)

    # Add timestamp
    for site in sites:
        site["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    try:
        with open(SITES_FILE, "w", encoding="utf-8") as f:
            json.dump(sites, f, ensure_ascii=False, indent=2)
        load_sites.clear()  # Invalidate cache
        return True, f"已保存 {len(sites)} 个基地数据"
    except Exception as e:
        return False, f"保存失败: {e}"


def validate_sites(sites: list[dict]) -> list[str]:
    """Validate site data. Returns list of error messages (empty = valid)."""
    errors = []
    required = ["name", "province", "lat", "lon", "tech", "capacity", "cost_low", "cost_avg", "cost_high"]
    lat_range = VALIDATION["lat"]
    lon_range = VALIDATION["lon"]

    for i, site in enumerate(sites):
        prefix = f"第{i+1}行「{site.get('name', '?')}」"

        # Required fields
        for field in required:
            if field not in site or site[field] is None or site[field] == "":
                errors.append(f"{prefix}: 缺少「{field}」")

        # Coordinate range
        lat = site.get("lat")
        lon = site.get("lon")
        if isinstance(lat, (int, float)) and not (lat_range[0] <= lat <= lat_range[1]):
            errors.append(f"{prefix}: 纬度 {lat} 超出中国范围 ({lat_range[0]}-{lat_range[1]})")
        if isinstance(lon, (int, float)) and not (lon_range[0] <= lon <= lon_range[1]):
            errors.append(f"{prefix}: 经度 {lon} 超出中国范围 ({lon_range[0]}-{lon_range[1]})")

        # Capacity
        cap = site.get("capacity")
        if isinstance(cap, (int, float)) and cap <= VALIDATION["capacity_min"]:
            errors.append(f"{prefix}: 产能必须大于 0")

        # Cost ordering
        clo, cav, chi = site.get("cost_low"), site.get("cost_avg"), site.get("cost_high")
        if all(isinstance(v, (int, float)) for v in [clo, cav, chi]):
            if not (clo <= cav <= chi):
                errors.append(f"{prefix}: 成本必须满足 最低≤平均≤最高 (当前: {clo}>{cav} 或 {cav}>{chi})")

        # Tech route
        tech = site.get("tech", "")
        if tech and tech not in VALID_TECH_ROUTES:
            errors.append(f"{prefix}: 技术路线「{tech}」不在预设列表中，建议手动添加到 config/constants.py")

    return errors


def get_updated_time() -> str:
    """Get last update timestamp from sites file."""
    try:
        with open(SITES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = data[0].get("updated_at", "") if data else ""
        return ts or "未记录"
    except Exception:
        return "无法读取"


@st.cache_data(ttl=60)
def load_competitors() -> list[dict]:
    """Load competitor data from JSON with cache."""
    try:
        with open(COMPETITORS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


@st.cache_data(ttl=60)
def load_stations() -> list[dict]:
    """Load hydrogen station data from JSON with cache."""
    try:
        with open(STATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_station_stats(stations: list[dict]) -> dict:
    """Compute aggregate statistics for stations."""
    if not stations:
        return {"count": 0, "total_capacity": 0, "total_throughput": 0, "avg_load": 0, "guohua_count": 0}
    total_cap = sum(s.get("daily_capacity_kg") or 0 for s in stations)
    total_through = sum(s.get("actual_throughput_kg") or 0 for s in stations)
    guohua = sum(1 for s in stations if s.get("is_guohua", False))
    avg_load = (total_through / total_cap * 100) if total_cap > 0 else 0
    return {
        "count": len(stations),
        "total_capacity": total_cap,
        "total_throughput": total_through,
        "avg_load": round(avg_load, 1),
        "guohua_count": guohua,
    }


@st.cache_data(ttl=300)
def load_stations_from_db(year: int | None = 4) -> list[dict]:
    """从 SQLite 导出的 JSON 加载加氢站数据（优先）"""
    try:
        with open(STATIONS_DB_JSON, "r", encoding="utf-8") as f:
            stations = json.load(f)
        if year:
            stations = [s for s in stations if s.get("year") == year]
        return stations
    except Exception:
        return []


@st.cache_data(ttl=300)
def load_trading_snapshots() -> list[dict]:
    """加载交易快照数据"""
    try:
        with open(TRADING_SNAPSHOT_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


@st.cache_data(ttl=300)
def load_enterprise_capacity() -> list[dict]:
    """从 SQLite 加载制氢企业产能数据"""
    if not DB_FILE.exists():
        return []
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT name, address, annual_capacity_tons, hydrogen_type, region
        FROM enterprise
        WHERE annual_capacity_tons IS NOT NULL
        ORDER BY annual_capacity_tons DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@st.cache_data(ttl=300)
def query_db(query: str, params: tuple = ()) -> list[dict]:
    """通用 SQLite 查询"""
    if not DB_FILE.exists():
        return []
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_cluster_stats(stations: list[dict]) -> list[dict]:
    """Aggregate stations by city cluster."""
    clusters = {}
    for s in stations:
        c = s.get("city_cluster", "其他")
        if c not in clusters:
            clusters[c] = {"name": c, "count": 0, "capacity": 0, "throughput": 0, "guohua": 0, "operational": 0}
        clusters[c]["count"] += 1
        clusters[c]["capacity"] += s.get("daily_capacity_kg") or 0
        clusters[c]["throughput"] += s.get("actual_throughput_kg") or 0
        clusters[c]["guohua"] += 1 if s.get("is_guohua") else 0
        clusters[c]["operational"] += 1 if s.get("status") == "运营中" else 0
    return sorted(clusters.values(), key=lambda x: x["count"], reverse=True)
