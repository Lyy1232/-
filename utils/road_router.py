"""OSRM 公路路线引擎 — 免费、无需 API Key · 含无路段的 fallback"""
import requests
import math
import time
from functools import lru_cache

OSRM_URL = "https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
OSRM_NEAREST = "https://router.project-osrm.org/nearest/v1/driving/{lon},{lat}"


@lru_cache(maxsize=1024)
def _osrm_route(lon1: float, lat1: float, lon2: float, lat2: float) -> dict | None:
    """调用 OSRM 获取两点间公路距离和路线几何。结果缓存。"""
    url = OSRM_URL.format(lon1=lon1, lat1=lat1, lon2=lon2, lat2=lat2)
    params = {"overview": "full", "geometries": "geojson"}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                coords = route["geometry"]["coordinates"]
                return {
                    "distance_m": route["distance"],
                    "distance_km": round(route["distance"] / 1000, 1),
                    "duration_min": round(route["duration"] / 60, 0),
                    "coords": coords,
                    "polyline": [[lat, lon] for lon, lat in coords],
                }
    except Exception:
        pass
    return None


@lru_cache(maxsize=512)
def _osrm_nearest_road(lon: float, lat: float) -> tuple[float, float] | None:
    """找到离给定坐标最近的公路点，返回 (lon, lat)。"""
    try:
        r = requests.get(OSRM_NEAREST.format(lon=lon, lat=lat), params={"number": 1}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == "Ok" and data.get("waypoints"):
                wp = data["waypoints"][0]["location"]
                return (wp[0], wp[1])
    except Exception:
        pass
    return None


def _straight_km(lon1, lat1, lon2, lat2):
    """直线距离 (km)。"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def road_distance_with_fallback(base_lon, base_lat, target_lon, target_lat) -> tuple[float, str]:
    """
    获取公路距离，失败时用 fallback。
    fallback = 基地到目标最近公路点的公路距离 + 公路点到目标的直线距离。
    返回 (距离_km, 方法说明)。
    """
    # 尝试直连
    route = _osrm_route(base_lon, base_lat, target_lon, target_lat)
    if route:
        return route["distance_km"], f"公路 {route['distance_km']}km"

    # Fallback: 找目标最近的公路点
    nearest = _osrm_nearest_road(target_lon, target_lat)
    if nearest:
        nr_lon, nr_lat = nearest
        straight_to_target = _straight_km(nr_lon, nr_lat, target_lon, target_lat)
        route2 = _osrm_route(base_lon, base_lat, nr_lon, nr_lat)
        if route2:
            total = round(route2["distance_km"] + straight_to_target, 1)
            return total, f"公路{route2['distance_km']}km+直线{straight_to_target:.1f}km={total}km"

    # 最后兜底：直线距离 × 1.4
    straight = _straight_km(base_lon, base_lat, target_lon, target_lat)
    return round(straight * 1.4, 1), f"直线{straight:.0f}km×1.4≈{round(straight*1.4)}km"


def compute_road_radius(base: dict, stations: list[dict], radius_km: float) -> list[dict]:
    """
    计算基地的公路经济半径覆盖。
    对每个站计算公路距离（含fallback），返回 road_km ≤ radius_km 的站列表。
    base: {"name", "lat", "lon", "cost_avg"}
    stations: [{"name","lat","lon","prov",...},...]
    返回: [{"name","road_km","method","straight_km",...},...]
    """
    results = []
    for s in stations:
        rd, method = road_distance_with_fallback(base["lon"], base["lat"], s["lon"], s["lat"])
        straight = _straight_km(base["lon"], base["lat"], s["lon"], s["lat"])
        if rd <= radius_km:
            results.append({
                "name": s["name"], "road_km": rd, "straight_km": round(straight, 1),
                "method": method, "lat": s["lat"], "lon": s["lon"],
                "prov": s.get("prov",""), "city": s.get("city",""),
            })
    results.sort(key=lambda x: x["road_km"])
    return results


def road_spider_routes(base: dict, stations: list[dict], radius_km: float = 200) -> list[dict]:
    """
    生成基地的路网蜘蛛图：取不同方向的代表性路线。
    返回最多 8 条路线（N/NE/E/SE/S/SW/W/NW），每条含 polyline 和 road_km。
    """
    # 先用直线距离筛选候选站，再算公路距离
    candidates = []
    for s in stations:
        d = _straight_km(base["lon"], base["lat"], s["lon"], s["lat"])
        if d < radius_km * 1.8:  # 留足够余量
            candidates.append(s)

    if not candidates:
        return []

    # 按方向分桶
    buckets = {k: [] for k in range(8)}  # 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW
    for s in candidates:
        dx = s["lon"] - base["lon"]
        dy = s["lat"] - base["lat"]
        angle = (math.degrees(math.atan2(dx, dy)) + 360) % 360
        bucket = int(angle / 45) % 8
        straight = _straight_km(base["lon"], base["lat"], s["lon"], s["lat"])
        buckets[bucket].append((straight, s))

    # 每个方向取最近的1-3个站，计算公路路线
    routes = []
    for bucket, cands in buckets.items():
        cands.sort(key=lambda x: x[0])  # 按直线距离排序
        for _, s in cands[:3]:  # 每方向最多3条
            route = _osrm_route(base["lon"], base["lat"], s["lon"], s["lat"])
            if route and route["distance_km"] < radius_km * 1.3:
                routes.append({
                    "station_name": s["name"],
                    "road_km": route["distance_km"],
                    "polyline": route["polyline"],
                    "direction": bucket,
                })
                break  # 每方向只取最近的一条

    return routes


def road_route_from_bases(bases: list[dict], target_lon: float, target_lat: float) -> list[dict]:
    """计算所有基地到目标点的公路路线，返回按距离排序的列表。"""
    results = []
    for b in bases:
        route = _osrm_route(b["lon"], b["lat"], target_lon, target_lat)
        if route:
            results.append({
                "base_name": b["name"],
                "base_lon": b["lon"], "base_lat": b["lat"],
                "base_cost": b.get("cost_avg", 27.0),
                "road_km": route["distance_km"],
                "duration_min": route["duration_min"],
                "polyline": route["polyline"],
            })
    results.sort(key=lambda x: x["road_km"])
    return results
