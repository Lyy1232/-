"""Shared constants: colors, tech mapping, tile options, validation rules."""

# ── Technology → color mapping ──
TECH_COLORS = {
    "风电+光伏电解": "#00d4aa",
    "风电电解": "#00d4aa",
    "光伏电解": "#4da8da",
    "煤制氢+CCS": "#4da8da",
    "工业副产氢": "#f59e0b",
}
DEFAULT_COLOR = "#64748b"

# ── Technology → Chinese display name ──
TECH_ZH = {
    "风电+光伏电解": "风光制氢",
    "风电电解": "风电制氢",
    "光伏电解": "光伏制氢",
    "煤制氢+CCS": "煤制氢+CCS",
    "工业副产氢": "副产氢",
}

# ── Valid tech routes ──
VALID_TECH_ROUTES = list(TECH_COLORS.keys())

# ── Map tiles ──
TILE_OPTIONS = {
    "高德地图（推荐）": {
        "url": "https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
        "attr": "高德地图",
        "subdomains": "1234",
    },
    "CartoDB 浅色": {
        "url": "CartoDB positron",
        "attr": "CartoDB",
    },
    "OpenStreetMap": {
        "url": "OpenStreetMap",
        "attr": "OSM",
    },
}

# ── Validation ──
VALIDATION = {
    "lat": (18.0, 54.0),        # 中国纬度范围
    "lon": (73.0, 135.0),       # 中国经度范围
    "capacity_min": 0,
    "cost_order": True,          # cost_low ≤ cost_avg ≤ cost_high
}

# ── Radius ──
ECONOMIC_RADIUS_KM = 200
