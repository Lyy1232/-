"""Geographic utilities: distance calculation, 200km radius, coordinate helpers."""
import math


def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance in km between two points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def point_in_radius(lat, lon, center_lat, center_lon, radius_km=200):
    """Check if a point is within given radius of center."""
    return haversine_km(lat, lon, center_lat, center_lon) <= radius_km


def format_distance(km):
    """Format distance for display."""
    if km < 1:
        return f"{int(km * 1000)}m"
    return f"{km:.0f}km"
