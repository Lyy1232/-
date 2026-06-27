"""构建 SQLite 数据库 — 从 Excel 解析并导入全部示范城市群数据"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3, json, re, numpy as np
from pathlib import Path
from utils.city_cluster_parser import (
    parse_all, flatten_to_stations, flatten_to_supply_sources, safe_float,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "city_cluster.db"

# ── 城市坐标（用于地图展示，基于城市名近似定位）──
CITY_COORDS = {
    "北京": (39.90, 116.40), "北京市大兴区": (39.73, 116.33), "北京市延庆区": (40.46, 115.97),
    "北京市房山区": (39.74, 116.14), "北京市昌平区": (40.22, 116.23), "北京市朝阳区": (39.92, 116.44),
    "北京市海淀区": (39.96, 116.30), "北京市通州区": (39.90, 116.66), "天津": (39.13, 117.20),
    "天津市": (39.13, 117.20), "石家庄": (38.04, 114.51), "保定": (38.87, 115.47),
    "保定市": (38.87, 115.47), "唐山": (39.63, 118.18), "唐山市": (39.63, 118.18),
    "张家口": (40.77, 114.88), "张家口市": (40.77, 114.88), "沧州": (38.30, 116.84),
    "沧州市": (38.30, 116.84), "沧州市泊头市": (38.08, 116.58), "沧州市黄骅港": (38.33, 117.86),
    "邯郸": (36.63, 114.54), "邯郸市武安市": (36.70, 114.20), "定州": (38.52, 114.99),
    "定州市": (38.52, 114.99), "辛集": (37.94, 115.22), "河北省辛集市": (37.94, 115.22),
    "郑州": (34.75, 113.62), "郑州市": (34.75, 113.62), "洛阳": (34.62, 112.45),
    "洛阳市": (34.62, 112.45), "新乡": (35.30, 113.93), "新乡市": (35.30, 113.93),
    "焦作": (35.22, 113.24), "焦作市": (35.22, 113.24), "济源": (35.07, 112.60),
    "济源市": (35.07, 112.60), "安阳": (36.10, 114.39), "安阳市": (36.10, 114.39),
    "濮阳": (35.76, 114.96), "濮阳市": (35.76, 114.96), "上海": (31.23, 121.47),
    "广州": (23.13, 113.26), "广州市": (23.13, 113.26), "佛山": (23.02, 113.12),
    "佛山市": (23.02, 113.12), "大连": (38.91, 121.61), "吕梁": (37.52, 111.14),
    "六安": (31.74, 116.52), "六安市": (31.74, 116.52), "包头": (40.66, 109.84),
    "哈密": (42.83, 93.51), "哈密市": (42.83, 93.51), "嘉兴": (30.77, 120.75),
    "嘉兴市": (30.77, 120.75), "嘉": (30.77, 120.75), "苏州": (31.30, 120.62),
    "鄂尔多斯": (39.61, 109.78), "宁东": (38.15, 106.60),
    "山东省淄博市": (36.81, 118.05), "山东省滨州市": (37.38, 118.02),
    "河北省唐山市": (39.63, 118.18),
    "乌海": (39.66, 106.82), "乌海市": (39.66, 106.82),
    "深圳": (22.54, 114.06), "中山": (22.52, 113.38),
    "云浮": (22.92, 112.04), "福州": (26.07, 119.30),
    "福州市": (26.07, 119.30),
}

CHINA_CENTER = (35.86, 104.20)  # 默认中心


def geocode(city_name: str) -> tuple[float, float]:
    """城市名→经纬度近似值"""
    if not city_name:
        return CHINA_CENTER
    city = str(city_name).strip().replace("\n", "").replace("　", "").replace(" ", "")
    # 精确匹配
    if city in CITY_COORDS:
        return CITY_COORDS[city]
    # 模糊匹配
    for k, v in CITY_COORDS.items():
        if k in city or city in k:
            return v
    # 按省份前缀匹配
    if "北京" in city:
        return (39.90, 116.40)
    if "天津" in city:
        return (39.13, 117.20)
    if "上海" in city:
        return (31.23, 121.47)
    print(f"  ⚠️ 未匹配坐标: {city}")
    return CHINA_CENTER


def build_database(excel_path: str):
    """主流程：解析Excel → 建表 → 导入SQLite"""
    print(f"Reading: {excel_path}")
    all_data = parse_all(excel_path, years=[3, 4])

    # 删除旧库
    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # ═══════════ 建表 ═══════════
    conn.executescript("""
    CREATE TABLE station (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_name TEXT NOT NULL,
        year INTEGER NOT NULL,
        city TEXT,
        station_name TEXT NOT NULL,
        type TEXT,
        address TEXT,
        daily_capacity_kg REAL,
        operator TEXT,
        is_highway INTEGER DEFAULT 0,
        total_refueling_kg REAL,
        retail_price REAL,
        quality_ok TEXT,
        lat REAL,
        lon REAL,
        status TEXT DEFAULT '运营中',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE supply_source (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id INTEGER NOT NULL,
        enterprise_name TEXT NOT NULL,
        enterprise_address TEXT,
        purchase_kg REAL,
        transport_radius_km REAL,
        FOREIGN KEY (station_id) REFERENCES station(id)
    );

    CREATE TABLE enterprise (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        address TEXT,
        annual_capacity_tons REAL,
        hydrogen_type TEXT,
        region TEXT
    );

    CREATE TABLE trading_snapshot (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id INTEGER NOT NULL UNIQUE,
        total_procurement_kg REAL,
        total_refuel_kg REAL,
        surplus_kg REAL,
        shortage_kg REAL,
        utilization_rate REAL,
        avg_transport_radius_km REAL,
        transport_cost_estimate REAL,
        flag_abnormal INTEGER DEFAULT 0,
        source_count INTEGER DEFAULT 0,
        FOREIGN KEY (station_id) REFERENCES station(id)
    );

    CREATE INDEX idx_station_cluster ON station(cluster_name, year);
    CREATE INDEX idx_station_city ON station(city);
    CREATE INDEX idx_supply_station ON supply_source(station_id);
    CREATE INDEX idx_supply_enterprise ON supply_source(enterprise_name);
    """)

    # ═══════════ 插入站数据 ═══════════
    station_count = 0
    station_id_map = {}  # (cluster, year, seq) → sqlite id

    for cluster, years in all_data.items():
        for year, stations in years.items():
            for s in stations:
                city = s.get("city", "")
                lat, lon = geocode(city)

                cur = conn.execute("""
                    INSERT INTO station (cluster_name, year, city, station_name, type, address,
                        daily_capacity_kg, operator, is_highway, total_refueling_kg, retail_price,
                        quality_ok, lat, lon)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    cluster, year, city, s.get("name", ""), s.get("type", ""),
                    s.get("address", ""), safe_float(s.get("daily_capacity_kg")),
                    s.get("operator", ""),
                    1 if "是" in str(s.get("is_highway", "")) else 0,
                    safe_float(s.get("total_refuel_kg")),
                    safe_float(s.get("retail_price")),
                    s.get("quality_ok", ""), lat, lon,
                ))
                sid = cur.lastrowid
                key = (cluster, year, s.get("seq", 0))
                station_id_map[key] = sid
                station_count += 1

                # 插入氢源明细
                for src in s.get("sources", []):
                    company = src.get("company", "").strip()
                    if not company or company in ("NaN", ""):
                        continue
                    conn.execute("""
                        INSERT INTO supply_source (station_id, enterprise_name, enterprise_address,
                            purchase_kg, transport_radius_km)
                        VALUES (?,?,?,?,?)
                    """, (
                        sid, company, src.get("address", ""),
                        safe_float(src.get("purchase_kg")),
                        safe_float(src.get("transport_radius_km")),
                    ))

                    # 企业去重插入
                    conn.execute("""
                        INSERT OR IGNORE INTO enterprise (name, address)
                        VALUES (?,?)
                    """, (company, src.get("address", "")))

    print(f"  Station: {station_count} records")

    # ═══════════ 计算交易快照 ═══════════
    conn.execute("""
        INSERT INTO trading_snapshot (station_id, total_procurement_kg, total_refuel_kg,
            surplus_kg, shortage_kg, utilization_rate, avg_transport_radius_km,
            transport_cost_estimate, flag_abnormal, source_count)
        SELECT
            s.id,
            COALESCE(ss.total_proc, 0) AS total_procurement_kg,
            s.total_refueling_kg,
            CASE WHEN COALESCE(ss.total_proc, 0) > COALESCE(s.total_refueling_kg, 0)
                 THEN COALESCE(ss.total_proc, 0) - COALESCE(s.total_refueling_kg, 0) END AS surplus_kg,
            CASE WHEN COALESCE(s.total_refueling_kg, 0) > COALESCE(ss.total_proc, 0)
                 THEN COALESCE(s.total_refueling_kg, 0) - COALESCE(ss.total_proc, 0) END AS shortage_kg,
            CASE WHEN s.daily_capacity_kg > 0
                 THEN ROUND(COALESCE(s.total_refueling_kg, 0) / 365.0 / s.daily_capacity_kg * 100, 1)
                 END AS utilization_rate,
            ss.avg_radius,
            CASE WHEN ss.avg_radius > 0 THEN ROUND(ss.avg_radius * 10.0 / 100, 2) END AS transport_cost_estimate,
            CASE WHEN COALESCE(ss.total_proc, 0) > 0
                 AND ABS(COALESCE(ss.total_proc, 0) - COALESCE(s.total_refueling_kg, 0))
                     / COALESCE(ss.total_proc, 0) > 0.90 THEN 1 ELSE 0 END AS flag_abnormal,
            ss.src_count
        FROM station s
        LEFT JOIN (
            SELECT station_id,
                   SUM(purchase_kg) AS total_proc,
                   AVG(CASE WHEN transport_radius_km > 0 AND transport_radius_km < 1000
                            THEN transport_radius_km END) AS avg_radius,
                   COUNT(*) AS src_count
            FROM supply_source
            WHERE purchase_kg > 0
            GROUP BY station_id
        ) ss ON s.id = ss.station_id
    """)

    # ═══════════ 更新企业表（补产能数据）═══
    enterprise_capacity = {
        "天津新源氢能": (6500, "工业副产氢（清洁氢认证）", "京津冀"),
        "天津新源氢能发展有限公司": (6500, "工业副产氢（清洁氢认证）", "京津冀"),
        "唐山中溶科技": (7200, "焦炉煤气制氢（~18元/kg）", "京津冀/河北"),
        "唐山中溶科技有限公司": (7200, "焦炉煤气制氢（~18元/kg）", "京津冀/河北"),
        "定州旭阳氢能": (5110, "焦炉煤气制氢", "京津冀/河北"),
        "定州旭阳氢能有限公司": (5110, "焦炉煤气制氢", "京津冀/河北"),
        "河北欣国氢能": (3150, "工业副产氢（提纯）", "京津冀"),
        "河北欣国氢能科技有限公司": (3150, "工业副产氢（提纯）", "京津冀"),
        "国华（赤城）风电": (1428, "可再生能源制氢（绿氢 35元/kg）", "河北"),
        "中国石化北京燕山分公司": (8000, "工业副产氢", "京津冀"),
        "中国石油化工股份有限公司北京燕山分公司": (8000, "工业副产氢", "京津冀"),
    }
    for name, (cap, htype, region) in enterprise_capacity.items():
        conn.execute("""
            UPDATE enterprise SET annual_capacity_tons=?, hydrogen_type=?, region=?
            WHERE name LIKE ?
        """, (cap, htype, region, f"%{name}%"))

    # 补空地址
    conn.execute("UPDATE enterprise SET address='' WHERE address IS NULL")

    conn.commit()

    # ═══════════ 统计 ═══════════
    counts = {}
    for tbl in ["station", "supply_source", "enterprise", "trading_snapshot"]:
        counts[tbl] = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]

    surplus_n = conn.execute("SELECT COUNT(*) FROM trading_snapshot WHERE surplus_kg > 0").fetchone()[0]
    deficit_n = conn.execute("SELECT COUNT(*) FROM trading_snapshot WHERE shortage_kg > 0").fetchone()[0]
    abnormal_n = conn.execute("SELECT COUNT(*) FROM trading_snapshot WHERE flag_abnormal=1").fetchone()[0]

    conn.close()

    print(f"  supply_source: {counts['supply_source']}, enterprise: {counts['enterprise']}")
    print(f"  trading_snapshot: {counts['trading_snapshot']} (余量:{surplus_n} 缺口:{deficit_n} 异常:{abnormal_n})")
    print(f"\n✅ SQLite 数据库构建完成: {DB_PATH}")
    return counts


def export_json_from_db():
    """从 SQLite 导出 JSON 供 Streamlit 直接加载（兼容现有架构）"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # 导出 stations.json 兼容格式
    stations = []
    for row in conn.execute("SELECT * FROM station ORDER BY cluster_name, year, id"):
        stations.append({
            "name": row["station_name"],
            "city_cluster": row["cluster_name"],
            "province": row["city"],
            "lat": row["lat"],
            "lon": row["lon"],
            "owner": row["operator"],
            "daily_capacity_kg": row["daily_capacity_kg"],
            "actual_throughput_kg": round((row["total_refueling_kg"] or 0) / 365, 1),
            "purchase_price_low": row["retail_price"],
            "purchase_price_high": row["retail_price"],
            "h2_source": "",
            "is_guohua": "国华" in str(row["operator"] or ""),
            "status": "运营中",
            "is_highway": bool(row["is_highway"]),
            "year": row["year"],
        })

    with open(PROJECT_ROOT / "data" / "stations_from_db.json", "w", encoding="utf-8") as f:
        json.dump(stations, f, ensure_ascii=False, indent=2)

    # 导出 trading 快照
    snapshots = []
    for row in conn.execute("""
        SELECT ts.*, s.station_name, s.cluster_name, s.city, s.retail_price, s.daily_capacity_kg
        FROM trading_snapshot ts JOIN station s ON ts.station_id = s.id
        ORDER BY s.cluster_name, ts.surplus_kg DESC
    """):
        snapshots.append(dict(row))

    with open(PROJECT_ROOT / "data" / "trading_snapshot_from_db.json", "w", encoding="utf-8") as f:
        json.dump(snapshots, f, ensure_ascii=False, indent=2)

    conn.close()
    print(f"  JSON exported: {len(stations)} stations, {len(snapshots)} snapshots")


if __name__ == "__main__":
    excel_path = Path.home() / "Downloads" / "工作簿1(1).xlsx"
    build_database(str(excel_path))
    export_json_from_db()
