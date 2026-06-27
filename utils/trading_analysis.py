"""交易撮合分析引擎 — 供需余缺计算、产能利用率、异常标记、API数据聚合"""
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TRANSPORT_COST_PER_100KM_KG = 10
FLAG_ABNORMAL_THRESHOLD = 0.90


def load_trading_snapshot() -> list[dict]:
    """加载交易快照数据"""
    with open(DATA_DIR / "trading_snapshot.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_stations() -> list[dict]:
    with open(DATA_DIR / "city_cluster_stations.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_supply() -> list[dict]:
    with open(DATA_DIR / "city_cluster_supply.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_demo_data() -> dict:
    with open(DATA_DIR / "demo_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ═══════════════════════════════════
# API: /api/dashboard/overview
# ═══════════════════════════════════
def get_dashboard_overview() -> dict:
    """返回各城市群总加注量、平均氢价、站数、总余量、总缺口"""
    snapshots = load_trading_snapshot()
    clusters: dict[str, dict] = {}

    for s in snapshots:
        c = s["cluster"]
        if c not in clusters:
            clusters[c] = {
                "cluster": c,
                "station_count": 0,
                "total_refuel_kg": 0,
                "total_surplus_kg": 0,
                "total_shortage_kg": 0,
                "prices": [],
                "daily_capacity_total": 0,
                "abnormal_count": 0,
            }
        cc = clusters[c]
        cc["station_count"] += 1
        cc["total_refuel_kg"] += s.get("total_refuel_kg") or 0
        cc["total_surplus_kg"] += s.get("surplus_kg") or 0
        cc["total_shortage_kg"] += s.get("shortage_kg") or 0
        rp = s.get("retail_price")
        if rp and rp == rp and rp > 0:  # 排除 None, NaN, 0
            cc["prices"].append(rp)
        cc["daily_capacity_total"] += s.get("daily_capacity_kg") or 0
        if s.get("flag_abnormal"):
            cc["abnormal_count"] += 1

    result = []
    for c, cc in clusters.items():
        avg_price = sum(cc["prices"]) / len(cc["prices"]) if cc["prices"] else 0
        result.append({
            "cluster": c,
            "station_count": cc["station_count"],
            "total_refuel_tons": round(cc["total_refuel_kg"] / 1000, 1),
            "total_surplus_tons": round(cc["total_surplus_kg"] / 1000, 1),
            "total_shortage_tons": round(cc["total_shortage_kg"] / 1000, 1),
            "avg_retail_price": round(avg_price, 1),
            "total_daily_capacity_kg": cc["daily_capacity_total"],
            "avg_utilization_pct": round(
                (cc["total_refuel_kg"] / 365 / cc["daily_capacity_total"] * 100) if cc["daily_capacity_total"] > 0 else 0, 1
            ),
            "abnormal_count": cc["abnormal_count"],
        })

    # Sort by station count desc
    result.sort(key=lambda x: x["station_count"], reverse=True)

    return {
        "update_time": "2026-06-27",
        "data_period": "第四年度（2024.8-2025.12）",
        "clusters": result,
        "global_summary": {
            "total_stations": sum(r["station_count"] for r in result),
            "total_refuel_tons": round(sum(r["total_refuel_tons"] for r in result), 1),
            "total_surplus_tons": round(sum(r["total_surplus_tons"] for r in result), 1),
            "total_shortage_tons": round(sum(r["total_shortage_tons"] for r in result), 1),
        },
    }


# ═══════════════════════════════════
# API: /api/trading/supply-list
# ═══════════════════════════════════
def get_supply_list(min_surplus_kg: float = 0, exclude_abnormal: bool = True) -> list[dict]:
    """返回余量>0的站点列表（可售供给端）"""
    snapshots = load_trading_snapshot()
    result = []
    for s in snapshots:
        surplus = s.get("surplus_kg")
        if not surplus or surplus <= min_surplus_kg:
            continue
        if exclude_abnormal and s.get("flag_abnormal"):
            continue
        result.append({
            "station_name": s["station_name"],
            "cluster": s["cluster"],
            "city": s.get("city", ""),
            "surplus_kg": round(surplus, 2),
            "retail_price": s.get("retail_price"),
            "daily_capacity_kg": s.get("daily_capacity_kg"),
            "avg_transport_radius_km": s.get("avg_transport_radius_km"),
            "transport_cost_estimate": s.get("transport_cost_estimate"),
            "utilization_rate": s.get("utilization_rate"),
        })
    result.sort(key=lambda x: x["surplus_kg"], reverse=True)
    return result


# ═══════════════════════════════════
# API: /api/trading/demand-list
# ═══════════════════════════════════
def get_demand_list(min_shortage_kg: float = 0, exclude_abnormal: bool = True) -> list[dict]:
    """返回缺口>0的站点列表（需采购需求端）"""
    snapshots = load_trading_snapshot()
    result = []
    for s in snapshots:
        shortage = s.get("shortage_kg")
        if not shortage or shortage <= min_shortage_kg:
            continue
        if exclude_abnormal and s.get("flag_abnormal"):
            continue
        result.append({
            "station_name": s["station_name"],
            "cluster": s["cluster"],
            "city": s.get("city", ""),
            "shortage_kg": round(shortage, 2),
            "retail_price": s.get("retail_price"),
            "daily_capacity_kg": s.get("daily_capacity_kg"),
            "utilization_rate": s.get("utilization_rate"),
        })
    result.sort(key=lambda x: x["shortage_kg"], reverse=True)
    return result


# ═══════════════════════════════════
# API: /api/enterprise/idle-capacity
# ═══════════════════════════════════
def get_idle_capacity() -> list[dict]:
    """返回头部制氢企业闲置产能（需结合外部产能数据）"""
    demo = load_demo_data()
    producers = demo.get("producers_capacity", [])
    result = []
    for p in producers:
        result.append({
            "enterprise_name": p["name"],
            "annual_capacity_tons": p["capacity_tons"],
            "demonstration_procurement_tons": p["procurement_tons"],
            "utilization_pct": p["utilization"],
            "idle_capacity_tons": p["idle_tons"],
            "hydrogen_type": p["type"],
            "region": p["region"],
        })
    return result


# ═══════════════════════════════════
# API: /api/trading/matching
# ═══════════════════════════════════
def get_matching_suggestions(max_transport_km: float = 100) -> list[dict]:
    """简单撮合建议：同城市群内余量→缺口配对"""
    supply = get_supply_list(exclude_abnormal=True)
    demand = get_demand_list(exclude_abnormal=True)

    matches = []
    for sup in supply:
        for dem in demand:
            if sup["cluster"] == dem["cluster"]:
                # 同群匹配，假设运距在可接受范围
                match_qty = min(sup["surplus_kg"], dem["shortage_kg"])
                matches.append({
                    "supply_station": sup["station_name"],
                    "supply_cluster": sup["cluster"],
                    "supply_surplus_kg": sup["surplus_kg"],
                    "demand_station": dem["station_name"],
                    "demand_cluster": dem["cluster"],
                    "demand_shortage_kg": dem["shortage_kg"],
                    "matchable_kg": round(match_qty, 2),
                    "priority": "P0",
                    "match_logic": f"同城群内撮合",
                })

    # Sort by matchable quantity desc
    matches.sort(key=lambda x: x["matchable_kg"], reverse=True)
    return matches[:10]


# ═══════════════════════════════════
# 聚合（供Streamlit直接使用）
# ═══════════════════════════════════
def get_all_trading_data() -> dict:
    """一次性返回所有交易数据，供Streamlit页面渲染"""
    return {
        "overview": get_dashboard_overview(),
        "supply_list": get_supply_list(),
        "demand_list": get_demand_list(),
        "idle_capacity": get_idle_capacity(),
        "matching": get_matching_suggestions(),
    }
