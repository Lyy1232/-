"""成本竞争力分析 — 三基地视角 · 200km辐射圈 · 运输方式比选 · 销售场景"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from utils.data_loader import load_sites, load_stations_from_db
from utils.geo_utils import haversine_km
from utils.ui import render_module_header
from config.constants import (
    TECH_ZH, ECONOMIC_RADIUS_KM,
    TRANSPORT_MODES, SALES_SCENARIOS, CITY_SUBSIDIES, GUOHUA_BASES_COST, REFERENCE_DATA,
)

TEAL = "#0d9488"; RED = "#ef4444"; GREEN = "#10b981"; AMBER = "#f59e0b"; BLUE = "#2563eb"

BASE_COORDS = {
    "赤城": (40.91, 115.83), "如东": (32.33, 121.18),
    "宁东": (38.15, 106.57), "沧州": (38.30, 116.84),
    "鄂尔多斯": (39.60, 109.80),
}


def compute_landed(base_cost, distance_km, transport_mode="长管拖车20MPa"):
    """计算到站成本"""
    mode = TRANSPORT_MODES.get(transport_mode, TRANSPORT_MODES["长管拖车20MPa"])
    transport_fee = distance_km * mode["cost_per_100km"] / 100
    return round(base_cost + transport_fee, 1), round(transport_fee, 1)


def render():
    render_module_header("成本竞争力", "三基地200km辐射分析 · 运输方式比选 · 销售场景", badge="COST")

    stations = load_stations_from_db(year=4)
    if not stations:
        st.warning("请先运行 python utils/build_sqlite.py")
        return

    # ── 参数配置栏 ──
    with st.expander("⚙️ 参数配置", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_mode = st.selectbox("运输方式", list(TRANSPORT_MODES.keys()), index=0)
            mode_info = TRANSPORT_MODES[sel_mode]
            st.caption(f"📌 {mode_info['note']} · {mode_info['cost_per_100km']}元/100km·kg")
        with c2:
            sel_radius = st.slider("分析半径 (km)", 50, 500, 200, 50)
        with c3:
            show_subsidy = st.checkbox("叠加城市群补贴", value=False)
            if show_subsidy:
                st.caption("已勾选补贴的城市群将显示补贴后价格")

    tab1, tab2, tab3 = st.tabs(["📍 基地成本竞争力", "🚛 运输比选与场景", "📊 对标分析"])

    # ═══════════ TAB 1 ═══════════
    with tab1:
        # Select base
        base_names = ["赤城", "如东", "宁东", "沧州"]
        cols = st.columns(4)
        sel_base = None
        for i, (col, name) in enumerate(zip(cols, base_names)):
            with col:
                cost = GUOHUA_BASES_COST.get(name, 15.2)
                coords = BASE_COORDS.get(name)
                if st.button(f"🏭 {name}\n{cost}元/kg", key=f"base_{name}", use_container_width=True,
                             type="primary" if i == 0 else "secondary"):
                    sel_base = name

        if sel_base is None:
            sel_base = "赤城"

        base_cost = GUOHUA_BASES_COST.get(sel_base, 15.2)
        base_lat, base_lon = BASE_COORDS.get(sel_base, (40.91, 115.83))

        # Calculate matches
        matches = []
        for s in stations:
            lat, lon = s.get("lat"), s.get("lon")
            if not lat or not lon:
                continue
            dist = haversine_km(base_lat, base_lon, lat, lon)
            if dist > sel_radius:
                continue
            landed, trans_fee = compute_landed(base_cost, dist, sel_mode)
            retail = s.get("purchase_price_low") or s.get("retail_price")
            cluster = s.get("city_cluster", "")
            # Apply subsidy
            effective_retail = retail
            if show_subsidy and retail:
                for city_key, subsidy in CITY_SUBSIDIES.items():
                    if city_key in cluster or cluster in city_key:
                        effective_retail = retail - subsidy
                        break
            gap = (effective_retail - landed) if effective_retail and effective_retail > 0 else None
            matches.append({
                "name": s.get("name", "")[:25], "cluster": cluster, "city": s.get("province", ""),
                "distance": round(dist, 1), "transport_fee": trans_fee,
                "landed": landed, "retail": retail, "gap": gap,
                "competitive": gap is not None and gap > 0,
            })

        matches.sort(key=lambda x: x["distance"])

        # Stats
        competitive = [m for m in matches if m.get("competitive")]
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("圈内站点", f"{len(matches)} 座")
        with c2: st.metric("成本优势站", f"{len(competitive)} 座",
                          delta=f"{len(competitive)/max(len(matches),1)*100:.0f}%")
        with c3: st.metric("平均到站成本", f"{np.mean([m['landed'] for m in matches]):.1f} 元/kg" if matches else "—")
        with c4: st.metric("平均价差",
                          f"{np.mean([m['gap'] for m in competitive]):+.1f} 元/kg" if competitive else "—")

        # Scatter: distance vs landed cost
        fig = go.Figure()
        colors = [GREEN if m["competitive"] else RED if m.get("gap") is not None else "#94a3b8" for m in matches]
        fig.add_trace(go.Scatter(
            x=[m["distance"] for m in matches], y=[m["landed"] for m in matches],
            mode="markers", marker=dict(size=9, color=colors, opacity=0.75, line=dict(width=1, color="white")),
            text=[f"<b>{m['name']}</b><br>{m['cluster']}<br>距离:{m['distance']}km<br>到站:{m['landed']}元/kg<br>零售:{m['retail']}<br>价差:{m['gap']:+.1f}" if m['gap'] else "" for m in matches],
            hoverinfo="text",
        ))
        # Add horizontal line for base cost
        fig.add_hline(y=base_cost, line_dash="dash", line_color=TEAL,
                      annotation=dict(text=f"出厂成本{base_cost}元/kg", font_size=10, font_color=TEAL))
        fig.add_hline(y=30, line_dash="dot", line_color=RED,
                      annotation=dict(text="市场均价参考30元", font_size=10, font_color=RED))
        fig.update_layout(
            title=f"{sel_base}基地 · {sel_mode} · {sel_radius}km圈内成本竞争力",
            xaxis_title="运输距离 (km)", yaxis_title="到站成本 (元/kg)", height=450,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Table of top matches
        st.caption(f"最近 {min(15, len(matches))} 个加氢站")
        df = pd.DataFrame([{
            "加氢站": m["name"], "城市群": m["cluster"], "距离km": m["distance"],
            "运输费": f"¥{m['transport_fee']}", "到站价": f"¥{m['landed']}",
            "零售价": f"¥{m['retail']}" if m['retail'] else "—",
            "价差": f"{m['gap']:+.1f}" if m['gap'] else "—",
            "竞争力": "✅" if m['competitive'] else ("—" if m['gap'] is not None else "无价格"),
        } for m in matches[:15]])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ═══════════ TAB 2 ═══════════
    with tab2:
        st.subheader("运输方式比选")

        # Transport mode cost comparison chart
        fig = go.Figure()
        dists = list(range(0, 501, 50))
        for mode_name, mode_info in TRANSPORT_MODES.items():
            costs = [d * mode_info["cost_per_100km"] / 100 for d in dists]
            dash = "solid" if "气态" in mode_name else "dot" if "液氢" in mode_name else "dash"
            fig.add_trace(go.Scatter(x=dists, y=costs, name=mode_name, mode="lines",
                                    line=dict(width=2.5, dash=dash)))
        fig.update_layout(
            title="运输成本随距离变化 · 四种方式对比", height=380,
            xaxis_title="运输距离 (km)", yaxis_title="运输成本 (元/kg)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Mode comparison table
        mode_table = [{"运输方式": k, "成本(元/100km·kg)": v["cost_per_100km"],
                       "适用半径(km)": v["max_radius"], "说明": v["note"]} for k, v in TRANSPORT_MODES.items()]
        st.dataframe(pd.DataFrame(mode_table), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("预置销售场景")

        for i, sc in enumerate(SALES_SCENARIOS):
            with st.expander(f"📐 场景{i+1}: {sc['name']} — {sc['note']}"):
                base_cost = GUOHUA_BASES_COST.get(sc["base"], 15.2)
                landed, trans_fee = compute_landed(base_cost, sc["distance"], sc["mode"])
                gap = sc["retail"] - landed
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("出厂成本", f"{base_cost} 元/kg")
                with c2: st.metric(f"运输费({sc['mode']})", f"{trans_fee} 元/kg")
                with c3: st.metric("到站成本", f"{landed} 元/kg")
                with c4: st.metric("vs零售价", f"{sc['retail']} 元/kg",
                                  delta=f"{gap:+.1f} 元/kg" if gap > 0 else f"{gap:.1f}")
                st.caption(f"📍 {sc['base']} → {sc['dest']} · {sc['distance']}km · {sc['mode']}")

    # ═══════════ TAB 3 ═══════════
    with tab3:
        st.subheader("国华基地 vs 市场零售价")

        # PIN-aware cost display
        pin_unlocked = st.session_state.get("show_exact_costs", False)

        # Bar chart comparing all bases
        fig = go.Figure()
        base_names_all = list(GUOHUA_BASES_COST.keys())
        if pin_unlocked:
            base_costs_all = [GUOHUA_BASES_COST[n] for n in base_names_all]
            fig.add_trace(go.Bar(name="出厂成本(精确)", x=base_names_all, y=base_costs_all,
                                marker_color=TEAL, text=[f"{c}元" for c in base_costs_all],
                                textposition="outside", textfont_size=10))
        else:
            # Show ranges when locked
            base_costs_mid = [GUOHUA_BASES_COST.get(n, 15) for n in base_names_all]
            fig.add_trace(go.Bar(name="出厂成本(区间)", x=base_names_all, y=base_costs_mid,
                                marker_color=TEAL, text=["~15元" if n != "沧州" else "~10元" for n in base_names_all],
                                textposition="outside", textfont_size=10))

        landed_200 = []
        for name in base_names_all:
            cost = GUOHUA_BASES_COST.get(name, 15.2)
            l200 = cost + 200 * TRANSPORT_MODES["长管拖车30MPa"]["cost_per_100km"] / 100
            landed_200.append(round(l200, 1))
        fig.add_trace(go.Bar(name="200km到站(30MPa)", x=base_names_all, y=landed_200,
                            marker_color=BLUE, marker_opacity=0.5,
                            text=[f"{c}元" for c in landed_200], textposition="outside", textfont_size=9))

        fig.add_hline(y=30, line_dash="dash", line_color=RED, line_width=1.2,
                      annotation=dict(text="市场均价参考30元/kg", font_size=9, font_color=RED))
        fig.add_hline(y=25, line_dash="dot", line_color=GREEN, line_width=1,
                      annotation=dict(text="2030目标25元/kg", font_size=9, font_color=GREEN))

        fig.update_layout(
            title="国华基地成本对标" + ("（精确值已解锁）" if pin_unlocked else "（锁定中，显示区间）"),
            height=400, yaxis_title="元/kg",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 城市群零售价与补贴")
        sub_tbl = [{"城市群": k, "补贴标准(元/kg)": v, "补贴后估算零售价": f"{30-v:.0f}元/kg（参考）"}
                   for k, v in CITY_SUBSIDIES.items()]
        st.dataframe(pd.DataFrame(sub_tbl), use_container_width=True, hide_index=True)

        # ── 行业参考数据 ──
        st.markdown("### 行业参考数据（Argus/BNEF/公开报告）")
        ref_tbl = [{"指标": k, "数值": v["value"], "来源": v["source"]} for k, v in REFERENCE_DATA.items()]
        st.dataframe(pd.DataFrame(ref_tbl), use_container_width=True, hide_index=True,
                    column_config={"来源": st.column_config.TextColumn(width="large")})
        st.caption("💡 数据来源包括中国产业发展促进会氢能分会、全国碳市场、国家能源局、隆众资讯、IEA、model.xlsx等。部分数据为2025-2026年公开值，实际以最新行情为准。")
