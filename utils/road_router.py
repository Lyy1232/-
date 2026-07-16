"""OSRM 公路路线引擎 — 免费、无需 API Key"""
import requests
import time
from functools import lru_cache

OSRM_URL = "https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"


@lru_cache(maxsize=512)
def _osrm_route(lon1: float, lat1: float, lon2: float, lat2: float) -> dict | None:
    """调用 OSRM 获取两点间公路距离和路线几何。结果缓存（同参数不重复请求）。"""
    url = OSRM_URL.format(lon1=lon1, lat1=lat1, lon2=lon2, lat2=lat2)
    params = {"overview": "full", "geometries": "geojson"}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                coords = route["geometry"]["coordinates"]  # [[lon,lat], ...]
                return {
                    "distance_m": route["distance"],
                    "distance_km": round(route["distance"] / 1000, 1),
                    "duration_min": round(route["duration"] / 60, 0),
                    "coords": coords,  # GeoJSON: [[lon,lat],...]
                    "polyline": [[lat, lon] for lon, lat in coords],  # Folium: [[lat,lon],...]
                }
    except Exception:
        pass
    return None


def road_distance_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float | None:
    """获取公路距离（km），失败返回 None。"""
    r = _osrm_route(lon1, lat1, lon2, lat2)
    return r["distance_km"] if r else None


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
