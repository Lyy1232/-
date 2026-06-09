"""Geographic utilities: distance, bearing, radius checks, formatting."""
import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in km between two points (Haversine formula)."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate initial bearing (degrees) from point 1 to point 2."""
    dlon = math.radians(lon2 - lon1)
    rlat1 = math.radians(lat1)
    rlat2 = math.radians(lat2)
    y = math.sin(dlon) * math.cos(rlat2)
    x = math.cos(rlat1) * math.sin(rlat2) - math.sin(rlat1) * math.cos(rlat2) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def bearing_direction(bearing: float) -> str:
    """Convert bearing to compass direction."""
    dirs = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
    idx = round(bearing / 45) % 8
    return dirs[idx]


def point_in_radius(lat: float, lon: float, center_lat: float, center_lon: float, radius_km: float = 200) -> bool:
    """Check if a point is within given radius of center."""
    return haversine_km(lat, lon, center_lat, center_lon) <= radius_km


def format_distance(km: float) -> str:
    """Format distance for human-readable display."""
    if km < 1:
        return f"{int(km * 1000)}m"
    if km < 10:
        return f"{km:.1f}km"
    return f"{km:.0f}km"
