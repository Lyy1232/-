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

# ── 运输方式参数 ──
TRANSPORT_MODES = {
    "长管拖车20MPa": {"cost_per_100km": 10.0, "max_radius": 150, "note": "行业经验值，单次运量~250kg"},
    "长管拖车30MPa": {"cost_per_100km": 7.5, "max_radius": 200, "note": "燕山石化实测，单次运量~650kg"},
    "液氢槽车":       {"cost_per_100km": 1.5,  "max_radius": 500, "note": "行业经验值，适合中长途"},
    "铁路液氨→裂解":   {"cost_per_100km": 0.03, "max_radius": 2000, "note": "model.xlsx 0.025$/t/km折氢"},
}

# ── 预置销售场景 ──
SALES_SCENARIOS = [
    {"name": "赤城→北京公交", "base": "赤城", "dest": "北京延庆", "distance": 51, "mode": "长管拖车30MPa",
     "retail": 30, "note": "51km气态，到站20.3元/kg，vs零售30元，优势明显"},
    {"name": "如东→上海化工区", "base": "如东", "dest": "上海化学工业区", "distance": 150, "mode": "液氢槽车",
     "retail": 36, "note": "150km液氢，到站17.5元/kg，vs零售36元，利润空间大"},
    {"name": "宁东→银川物流", "base": "宁东", "dest": "银川市区", "distance": 30, "mode": "长管拖车20MPa",
     "retail": 28, "note": "30km气态，到站18.2元/kg，vs零售28元"},
    {"name": "赤城→长三角(远期)", "base": "赤城", "dest": "上海/如东", "distance": 1100, "mode": "铁路液氨→裂解",
     "retail": 36, "note": "铁路液氨1100km+裂解，到站~15.5元/kg，远期竞争力极强"},
    {"name": "鄂尔多斯→北京(规划)", "base": "鄂尔多斯", "dest": "北京", "distance": 500, "mode": "液氢槽车",
     "retail": 30, "note": "500km液氢圈，鄂尔多斯液氢工厂规划中"},
]

# ── 城市群补贴标准（元/kg，可配置）──
CITY_SUBSIDIES = {
    "广东(佛山)": 18.0,
    "上海": 0.0,
    "京津冀": 0.0,
    "河北": 0.0,
    "郑州": 0.0,
}

# ── 国华基地成本（来源：model.xlsx）──
GUOHUA_BASES_COST = {
    "赤城": 15.2,
    "如东": 15.2,
    "宁东": 15.2,
    "沧州": 9.6,
    "鄂尔多斯": 11.2,
}
