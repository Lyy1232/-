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

# ── Trading ──
TRANSPORT_COST_PER_100KM_KG = 10       # 高压气态运氢成本（元/100km·kg）
FLAG_ABNORMAL_THRESHOLD = 0.90          # 余量/缺口占比>90%标记异常

# ── 制氢成本参数（来源：绿氨竞争力模型 model.xlsx）──
ELECTROLYSIS_EFFICIENCY = 45            # 电解效率 kWh/kgH2（模型值，优于行业典型55）
CHINA_GREEN_ELEC_PRICE = 0.20           # 中国绿电PPA电价 元/kWh（28$/MWh≈0.20元）
MENGXI_GREEN_ELEC_PRICE = 0.14          # 蒙西低电价 元/kWh（20$/MWh≈0.14元）
GREEN_H2_COST_CHINA = 15.2              # 沧州绿氢制取成本（元/kg，电价28$/MWh+电解45kWh+利用5000h）
GREEN_H2_COST_MENGXI = 11.2             # 蒙西绿氢制取成本（元/kg，电价20$/MWh+电解45kWh+利用4500h）
BLUE_H2_COST_CHINA = 9.6                # 中国蓝氨折氢成本（元/kg，天然气8.5$/MMBtu+CCS）
GREEN_H2_COST = GREEN_H2_COST_CHINA      # 默认绿氢成本（保持向后兼容）
