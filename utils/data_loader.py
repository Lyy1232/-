"""Centralized data loading, saving, validation with caching."""
from pathlib import Path
import json
from datetime import datetime, timezone
import streamlit as st
from config.constants import VALIDATION, VALID_TECH_ROUTES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SITES_FILE = PROJECT_ROOT / "config" / "sites.json"


@st.cache_data(ttl=30)
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
