"""供需匹配引擎 — 国华+竞品制氢厂 → 加氢站 距离/运输成本/到站价格"""
import json
from pathlib import Path
from utils.geo_utils import haversine_km
from config.constants import ECONOMIC_RADIUS_KM, TRANSPORT_COST_PER_100KM_KG, TECH_ZH

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_origins() -> list[dict]:
    """加载所有供给点（国华基地+竞品工厂）"""
    origins = []
    # 国华基地
    with open(PROJECT_ROOT / "config" / "sites.json", "r") as f:
        sites = json.load(f)
    for s in sites:
        origins.append({
            "name": s["name"],
            "type": "国华基地",
            "type_icon": "🏭",
            "lat": s["lat"],
            "lon": s["lon"],
            "cost_avg": s.get("cost_avg", 0),
            "cost_low": s.get("cost_low", 0),
            "cost_high": s.get("cost_high", 0),
            "tech": s.get("tech", ""),
            "capacity": s.get("capacity", 0),
            "province": s.get("province", ""),
            "color": "#0d9488",
        })
    # 竞品
    with open(PROJECT_ROOT / "config" / "competitors.json", "r") as f:
        competitors = json.load(f)
    for c in competitors:
        origins.append({
            "name": c["name"],
            "type": "竞品",
            "type_icon": "⚠️",
            "lat": c["lat"],
            "lon": c["lon"],
            "cost_avg": c.get("cost_est", 0),
            "cost_low": c.get("cost_est", 0),
            "cost_high": c.get("cost_est", 0),
            "tech": c.get("tech", ""),
            "capacity": c.get("capacity", 0),
            "province": c.get("province", ""),
            "color": "#ef4444",
        })
    return origins


def load_destinations() -> list[dict]:
    """加载所有需求点（加氢站）"""
    with open(PROJECT_ROOT / "data" / "stations_from_db.json", "r") as f:
        stations = json.load(f)
    # Filter Y4 only
    stations = [s for s in stations if s.get("year") == 4]
    destinations = []
    for s in stations:
        destinations.append({
            "name": s.get("name", ""),
            "city_cluster": s.get("city_cluster", ""),
            "city": s.get("province", ""),
            "lat": s.get("lat"),
            "lon": s.get("lon"),
            "daily_capacity": s.get("daily_capacity_kg") or 0,
            "throughput": s.get("actual_throughput_kg") or 0,
            "retail_price": s.get("purchase_price_low") or s.get("retail_price"),
            "owner": s.get("owner", ""),
            "is_highway": s.get("is_highway", False),
        })
    return destinations


def match(origin: dict, destinations: list[dict],
          max_radius: float = ECONOMIC_RADIUS_KM,
          transport_rate: float = TRANSPORT_COST_PER_100KM_KG) -> list[dict]:
    """计算单个供给点到所有需求点的匹配结果"""
    results = []
    for dest in destinations:
        dist = haversine_km(origin["lat"], origin["lon"], dest["lat"], dest["lon"])
        if dist > max_radius:
            continue
        transport_cost = dist * transport_rate / 100
        landed_cost = origin["cost_avg"] + transport_cost
        price_gap = (dest["retail_price"] - landed_cost) if dest["retail_price"] else None

        results.append({
            **dest,
            "distance_km": round(dist, 1),
            "transport_cost": round(transport_cost, 1),
            "landed_cost": round(landed_cost, 1),
            "price_gap": round(price_gap, 1) if price_gap else None,
            "competitive": price_gap is not None and price_gap > 0,
        })

    results.sort(key=lambda x: x["distance_km"])
    return results


def match_best(destinations: list[dict],
               origins: list[dict] | None = None,
               max_radius: float = 500.0) -> list[dict]:
    """为每个需求点找到最优供给点"""
    if origins is None:
        origins = load_origins()

    results = []
    for dest in destinations:
        best = None
        best_cost = float("inf")
        for org in origins:
            dist = haversine_km(org["lat"], org["lon"], dest["lat"], dest["lon"])
            transport = dist * TRANSPORT_COST_PER_100KM_KG / 100
            landed = org["cost_avg"] + transport
            if landed < best_cost:
                best_cost = landed
                best = {
                    "station": dest["name"],
                    "cluster": dest["city_cluster"],
                    "city": dest["city"],
                    "best_origin": org["name"],
                    "origin_type": org["type"],
                    "distance_km": round(dist, 1),
                    "transport_cost": round(transport, 1),
                    "landed_cost": round(landed, 1),
                    "retail_price": dest["retail_price"],
                    "price_gap": round(dest["retail_price"] - landed, 1) if dest["retail_price"] else None,
                    "in_economic_radius": dist <= ECONOMIC_RADIUS_KM,
                }
        if best:
            results.append(best)

    results.sort(key=lambda x: x["distance_km"])
    return results


def get_summary_stats(matches: list[dict]) -> dict:
    """汇总统计数据"""
    if not matches:
        return {}
    in_radius = [m for m in matches if m.get("in_economic_radius", False)]
    competitive = [m for m in matches if m.get("price_gap") is not None and m["price_gap"] > 0]
    return {
        "total_matches": len(matches),
        "in_economic_radius": len(in_radius),
        "competitive_count": len(competitive),
        "avg_distance": round(sum(m["distance_km"] for m in matches) / len(matches), 1),
        "avg_landed_cost": round(sum(m["landed_cost"] for m in matches) / len(matches), 1),
        "avg_price_gap": round(sum(m["price_gap"] for m in competitive) / len(competitive), 1) if competitive else 0,
    }
