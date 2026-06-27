"""示范城市群 Excel 解析器 — 处理5个城市群×2年度共10个Sheet的复杂格式"""
import pandas as pd
import numpy as np
import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# 运输成本配置（后期可调）
TRANSPORT_COST_PER_100KM_KG = 10  # 元/100km·kg
FLAG_ABNORMAL_THRESHOLD = 0.90   # 余量占比>90%标记异常


def safe_float(v: Any) -> float | None:
    """安全转换为 float，处理各种脏数据"""
    if v is None:
        return None
    try:
        if isinstance(v, str):
            v = v.replace(",", "").replace("—", "").replace("／", "").replace("(", "").replace(")", "").strip()
            if v in ("", "/", "自用", "\\"):
                return None
        return float(v)
    except (ValueError, TypeError):
        return None


def _find_header_row(df: pd.DataFrame, keyword: str = "序号") -> int | None:
    """定位表头行"""
    for idx, row in df.iterrows():
        for val in row:
            if pd.notna(val) and keyword in str(val):
                return idx
    return None


def _extract_cluster_name(df: pd.DataFrame, sheet_name: str) -> str:
    """从Sheet名或表头提取城市群名"""
    name_map = {
        "京津冀": "京津冀", "河北": "河北", "郑州": "郑州",
        "广州": "广东", "广东": "广东", "上海": "上海",
    }
    for k, v in name_map.items():
        if k in sheet_name:
            return v
    return sheet_name.replace("第四年", "").replace("第三年", "")


def _extract_year(sheet_name: str) -> int:
    """提取年度"""
    if "第四年" in sheet_name:
        return 4
    if "第三年" in sheet_name:
        return 3
    return 0


def _extract_h2_production(df: pd.DataFrame) -> float | None:
    """从表头提取车用氢产量"""
    for idx, row in df.iterrows():
        for val in row:
            if pd.notna(val) and "产量" in str(val) and "吨" in str(val):
                nums = re.findall(r"[\d.]+", str(val))
                if nums:
                    return safe_float(nums[-1])
    return None


def parse_jingjinji(df: pd.DataFrame) -> list[dict]:
    """解析京津冀格式（最复杂：主记录+多行来源+总计行）"""
    stations = []
    current = None
    source_keywords = {"制氢企业名称", "总计", "氢气来源", "NaN", ""}

    for idx in range(2, len(df)):
        row = df.iloc[idx]
        seq_val = row.iloc[0]
        name_val = row.iloc[2]

        # 新站点行（有序号+有站名）
        if pd.notna(seq_val) and pd.notna(name_val):
            try:
                seq = int(float(seq_val))
                current = {
                    "seq": seq,
                    "city": str(row.iloc[1]).strip().replace("　", "") if pd.notna(row.iloc[1]) else "",
                    "name": str(name_val).strip().replace("　", ""),
                    "type": str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "",
                    "address": str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else "",
                    "quality_ok": str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else "",
                    "daily_capacity_kg": safe_float(row.iloc[6]),
                    "operator": str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else "",
                    "is_highway": str(row.iloc[8]).strip() if pd.notna(row.iloc[8]) else "",
                    "total_refuel_kg": None,
                    "low_carbon_kg": None,
                    "clean_kg": None,
                    "retail_price": safe_float(row.iloc[16]) if len(row) > 16 else None,
                    "sources": [],
                }
                stations.append(current)
            except (ValueError, TypeError):
                continue

        # 来源行或总计行
        if current is not None:
            src_col = row.iloc[9]
            if pd.notna(src_col):
                src_str = str(src_col).strip()
                if src_str == "总计":
                    current["total_refuel_kg"] = safe_float(row.iloc[13])
                    current["low_carbon_kg"] = safe_float(row.iloc[14])
                    current["clean_kg"] = safe_float(row.iloc[15])
                elif src_str not in source_keywords:
                    current["sources"].append({
                        "company": src_str,
                        "address": str(row.iloc[10]).strip() if pd.notna(row.iloc[10]) else "",
                        "purchase_kg": safe_float(row.iloc[11]),
                        "transport_radius_km": safe_float(row.iloc[12]),
                    })

    return stations


def parse_generic(df: pd.DataFrame) -> list[dict]:
    """解析通用格式（郑州/广州/上海/广东/河北 第三/四年度）"""
    header_row = _find_header_row(df, "序号")
    if header_row is None:
        return []

    stations = []
    current = None
    source_keywords = {"制氢企业名称", "总计", "氢气来源", "氢气来源（制氢企业名称）", "氢气来源信息", "NaN", ""}

    for idx in range(header_row + 1, len(df)):
        row = df.iloc[idx]
        seq_val = row.iloc[0]

        if pd.notna(seq_val):
            try:
                seq = int(float(seq_val))
                current = {
                    "seq": seq,
                    "city": str(row.iloc[1]).strip().replace("\n", "").replace("　", "") if pd.notna(row.iloc[1]) else "",
                    "name": str(row.iloc[2]).strip().replace("　", "") if pd.notna(row.iloc[2]) else "",
                    "type": str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "",
                    "address": str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else "",
                    "quality_ok": str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else "",
                    "daily_capacity_kg": safe_float(row.iloc[6]),
                    "operator": str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else "",
                    "is_highway": str(row.iloc[8]).strip() if pd.notna(row.iloc[8]) else "",
                    "total_refuel_kg": safe_float(row.iloc[13]) if len(row) > 13 else None,
                    "low_carbon_kg": safe_float(row.iloc[14]) if len(row) > 14 else None,
                    "clean_kg": safe_float(row.iloc[15]) if len(row) > 15 else None,
                    "retail_price": safe_float(row.iloc[16]) if len(row) > 16 else None,
                    "sources": [],
                }
                stations.append(current)
            except (ValueError, TypeError):
                current = None
                continue

        if current is not None and not pd.notna(seq_val):
            for src_col in [9]:
                if len(row) > src_col and pd.notna(row.iloc[src_col]):
                    src_str = str(row.iloc[src_col]).strip()
                    if src_str and src_str not in source_keywords:
                        current["sources"].append({
                            "company": src_str,
                            "address": str(row.iloc[src_col + 1]).strip() if len(row) > src_col + 1 and pd.notna(row.iloc[src_col + 1]) else "",
                            "purchase_kg": safe_float(row.iloc[src_col + 2]),
                            "transport_radius_km": safe_float(row.iloc[src_col + 3]),
                        })
                        break

    return stations


def parse_hebei_y4(df: pd.DataFrame) -> list[dict]:
    """解析河北第四年特殊格式（多了建设状态列，来源信息在col8+，加注信息在col14+）
    注意：河北Y4的"序号"是列名而非cell值，header_row为None，直接从row 0开始扫描"""
    header_row = _find_header_row(df, "序号")
    start_row = 0 if header_row is None else header_row + 1

    stations = []
    current = None

    for idx in range(start_row, len(df)):
        row = df.iloc[idx]
        seq_val = row.iloc[0]

        if pd.notna(seq_val):
            try:
                seq = int(float(seq_val))
                current = {
                    "seq": seq,
                    "city": str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else "",
                    "name": str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "",
                    "status": str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "",
                    "type": str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else "",
                    "quality_ok": str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else "",
                    "daily_capacity_kg": safe_float(row.iloc[6]),
                    "total_refuel_kg": safe_float(row.iloc[15]) if len(row) > 15 else None,
                    "low_carbon_kg": safe_float(row.iloc[16]) if len(row) > 16 else None,
                    "clean_kg": safe_float(row.iloc[17]) if len(row) > 17 else None,
                    "retail_price": safe_float(row.iloc[18]) if len(row) > 18 else None,
                    "address": "",
                    "operator": "",
                    "is_highway": "",
                    "sources": [],
                }
                stations.append(current)
            except (ValueError, TypeError):
                current = None
                continue

        if current is not None and not pd.notna(seq_val):
            if len(row) > 8 and pd.notna(row.iloc[8]):
                src_str = str(row.iloc[8]).strip()
                if src_str and src_str not in ("NaN", "", "氢气来源（制氢企业名称）"):
                    current["sources"].append({
                        "company": src_str,
                        "address": "",
                        "purchase_kg": safe_float(row.iloc[10]),
                        "transport_radius_km": safe_float(row.iloc[9]),
                    })

    return stations


def parse_all(excel_path: str, years: list[int] | None = None) -> dict:
    """
    解析全部Sheet，返回 {cluster_name: {year: [stations]}}
    若 years=None 则解析所有年度
    """
    xls = pd.ExcelFile(excel_path)
    all_data: dict[str, dict[int, list[dict]]] = {}

    parser_map = {
        "京津冀": parse_jingjinji,
    }

    for sheet in xls.sheet_names:
        cluster = _extract_cluster_name(sheet, sheet)
        year = _extract_year(sheet)
        if years and year not in years:
            continue

        if cluster not in all_data:
            all_data[cluster] = {}

        df = pd.read_excel(xls, sheet)

        # 选择解析器
        if "京津冀" in sheet and year == 4:
            parser = parse_jingjinji
        elif "河北" in sheet and year == 4:
            parser = parse_hebei_y4
        elif "京津冀" in sheet and year == 3:
            parser = parse_jingjinji  # 京津冀Y3格式类似
        else:
            parser = parse_generic

        stations = parser(df)
        # 注入元数据
        for s in stations:
            s["cluster"] = cluster
            s["year"] = year

        all_data[cluster][year] = stations
        print(f"  [{cluster} Y{year}] {len(stations)} stations parsed")

    return all_data


def flatten_to_stations(all_data: dict) -> list[dict]:
    """展平为 station 表记录"""
    records = []
    for cluster, years in all_data.items():
        for year, stations in years.items():
            for s in stations:
                records.append({
                    "cluster_name": cluster,
                    "year": year,
                    "city": s.get("city", ""),
                    "station_name": s.get("name", ""),
                    "type": s.get("type", ""),
                    "address": s.get("address", ""),
                    "daily_capacity_kg": s.get("daily_capacity_kg"),
                    "operator": s.get("operator", ""),
                    "is_highway": s.get("is_highway", "").replace("是", "true").replace("否", "false"),
                    "total_refueling_kg": s.get("total_refuel_kg"),
                    "retail_price": s.get("retail_price"),
                    "quality_ok": s.get("quality_ok", ""),
                })
    return records


def flatten_to_supply_sources(all_data: dict) -> list[dict]:
    """展平为 supply_source 表记录"""
    records = []
    station_id = 0
    for cluster, years in all_data.items():
        for year, stations in years.items():
            for s in stations:
                station_id += 1
                for src in s.get("sources", []):
                    records.append({
                        "station_id": station_id,
                        "station_name": s.get("name", ""),
                        "cluster": cluster,
                        "year": year,
                        "enterprise_name": src.get("company", ""),
                        "enterprise_address": src.get("address", ""),
                        "purchase_kg": src.get("purchase_kg"),
                        "transport_radius_km": src.get("transport_radius_km"),
                    })
    return records


def compute_trading_snapshot(stations: list[dict]) -> list[dict]:
    """计算交易快照：余量/缺口/利用率/异常标记"""
    snapshots = []
    for s in stations:
        total_proc = sum(
            safe_float(src.get("purchase_kg")) or 0
            for src in s.get("sources", [])
        )
        refuel = safe_float(s.get("total_refuel_kg")) or 0
        daily_cap = safe_float(s.get("daily_capacity_kg")) or 0

        surplus = total_proc - refuel if total_proc > 0 and refuel > 0 else None
        shortage = refuel - total_proc if total_proc > 0 and refuel > 0 else None
        utilization = (refuel / daily_cap * 100) if daily_cap > 0 else None

        # 异常标记
        flag_abnormal = False
        if surplus is not None and total_proc > 0:
            if abs(surplus) / total_proc > FLAG_ABNORMAL_THRESHOLD:
                flag_abnormal = True

        # 运输成本估算
        avg_radius = None
        radii = []
        for src in s.get("sources", []):
            r = safe_float(src.get("transport_radius_km"))
            if r and 0 < r < 1000:
                radii.append(r)
        if radii:
            avg_radius = sum(radii) / len(radii)

        snapshots.append({
            "station_name": s.get("name", ""),
            "cluster": s.get("cluster", ""),
            "year": s.get("year", 0),
            "city": s.get("city", ""),
            "total_procurement_kg": round(total_proc, 2) if total_proc > 0 else None,
            "total_refuel_kg": refuel if refuel > 0 else None,
            "surplus_kg": round(surplus, 2) if surplus is not None and surplus > 0 else None,
            "shortage_kg": round(shortage, 2) if shortage is not None and shortage > 0 else None,
            "utilization_rate": round(utilization, 1) if utilization is not None else None,
            "daily_capacity_kg": daily_cap if daily_cap > 0 else None,
            "retail_price": safe_float(s.get("retail_price")),
            "avg_transport_radius_km": round(avg_radius, 1) if avg_radius else None,
            "transport_cost_estimate": round(avg_radius * TRANSPORT_COST_PER_100KM_KG / 100, 2) if avg_radius else None,
            "flag_abnormal": flag_abnormal,
            "source_count": len(s.get("sources", [])),
        })

    return snapshots


# ═══════════════════════════════════
# Main entry
# ═══════════════════════════════════
if __name__ == "__main__":
    excel_path = PROJECT_ROOT.parent.parent / "Downloads" / "工作簿1(1).xlsx"
    if not excel_path.exists():
        excel_path = Path.home() / "Downloads" / "工作簿1(1).xlsx"
    print(f"Reading: {excel_path}")

    all_data = parse_all(str(excel_path), years=[4])

    # Flatten
    stations = flatten_to_stations(all_data)
    supply = flatten_to_supply_sources(all_data)

    # Trading snapshot (from raw parsed data)
    all_y4_stations = []
    for cluster, years in all_data.items():
        for year, sts in years.items():
            all_y4_stations.extend(sts)
    snapshots = compute_trading_snapshot(all_y4_stations)

    # Save
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATA_DIR / "city_cluster_stations.json", "w", encoding="utf-8") as f:
        json.dump(stations, f, ensure_ascii=False, indent=2)

    with open(DATA_DIR / "city_cluster_supply.json", "w", encoding="utf-8") as f:
        json.dump(supply, f, ensure_ascii=False, indent=2)

    with open(DATA_DIR / "trading_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snapshots, f, ensure_ascii=False, indent=2)

    # Summary
    surplus_count = sum(1 for s in snapshots if s["surplus_kg"])
    deficit_count = sum(1 for s in snapshots if s["shortage_kg"])
    abnormal_count = sum(1 for s in snapshots if s["flag_abnormal"])

    print(f"\n{'='*50}")
    print(f"解析完成：")
    print(f"  Station 记录: {len(stations)}")
    print(f"  Supply Source 记录: {len(supply)}")
    print(f"  Trading Snapshot: {len(snapshots)}")
    print(f"  余量站点: {surplus_count}, 缺口站点: {deficit_count}")
    print(f"  异常标记站点: {abnormal_count}")
    print(f"  数据已保存到: {DATA_DIR}")
