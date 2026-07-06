"""成本竞争力分析 — 三基地视角 · 200km辐射圈 · 运输比选 · 销售场景 · 导出"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import io
from utils.data_loader import load_sites, load_stations_from_db
from utils.geo_utils import haversine_km
from utils.ui import render_module_header
from config.constants import (
    TECH_ZH, ECONOMIC_RADIUS_KM,
    TRANSPORT_MODES, SALES_SCENARIOS, CITY_SUBSIDIES, GUOHUA_BASES_COST, REFERENCE_DATA,
)

BRAND = "#0d9488"; RED = "#ef4444"; GREEN = "#10b981"; AMBER = "#f59e0b"; BLUE = "#2563eb"

BASE_COORDS = {
    "赤城": (40.91, 115.83), "如东": (32.33, 121.18),
    "宁东": (38.15, 106.57), "沧州": (38.30, 116.84),
    "鄂尔多斯": (39.60, 109.80),
}

def compute_landed(base_cost, distance_km, transport_mode="长管拖车20MPa"):
    mode = TRANSPORT_MODES.get(transport_mode, TRANSPORT_MODES["长管拖车20MPa"])
    transport_fee = distance_km * mode["cost_per_100km"] / 100
    return round(base_cost + transport_fee, 1), round(transport_fee, 1)

def build_match_dataframe(matches):
    return pd.DataFrame([{
        "加氢站": m["name"], "城市群": m["cluster"], "距离(km)": m["distance"],
        "运输费(元/kg)": m["transport_fee"], "到站价(元/kg)": m["landed"],
        "零售价(元/kg)": m["retail"] if m["retail"] else None,
        "价差(元/kg)": m["gap"], "竞争力": "✅" if m["competitive"] else ("—" if m.get("gap") is not None else "无价格"),
    } for m in matches])

def render():
    render_module_header("成本竞争力", "三基地200km辐射分析 · 运输方式比选 · 销售场景 · 导出Excel", badge="COST")

    stations = load_stations_from_db(year=4)
    if not stations:
        st.warning("请先运行 python utils/build_sqlite.py")
        return

    # ── 参数配置 ──
    with st.expander("⚙️ 参数配置", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sel_mode = st.selectbox("运输方式", list(TRANSPORT_MODES.keys()), index=0)
            mode_info = TRANSPORT_MODES[sel_mode]
            st.caption(f"{mode_info['note']} · {mode_info['cost_per_100km']}元/100km·kg")
        with c2:
            sel_radius = st.slider("分析半径 (km)", 50, 500, 200, 50)
        with c3:
            show_subsidy = st.checkbox("叠加城市群补贴", value=False)
        with c4:
            compare_mode = st.checkbox("多基地对比模式", value=False)

    tab1, tab2, tab3 = st.tabs(["📍 基地成本竞争力", "🚛 运输比选与场景", "📊 对标分析"])

    # ═══════════ TAB 1 ═══════════
    with tab1:
        if compare_mode:
            # ── 多基地对比模式 ──
            selected_bases = st.multiselect("选择对比基地", list(GUOHUA_BASES_COST.keys()),
                                           default=["赤城", "如东", "宁东"])
            if selected_bases:
                all_matches = []
                for base_name in selected_bases:
                    base_cost = GUOHUA_BASES_COST.get(base_name, 15.2)
                    blat, blon = BASE_COORDS.get(base_name, (40.91, 115.83))
                    for s in stations:
                        lat, lon = s.get("lat"), s.get("lon")
                        if not lat or not lon: continue
                        dist = haversine_km(blat, blon, lat, lon)
                        if dist > sel_radius: continue
                        landed, trans_fee = compute_landed(base_cost, dist, sel_mode)
                        retail = s.get("purchase_price_low") or s.get("retail_price")
                        gap = (retail - landed) if retail and retail > 0 else None
                        all_matches.append({
                            "基地": base_name, "name": s.get("name", "")[:25],
                            "cluster": s.get("city_cluster", ""),
                            "distance": round(dist, 1), "transport_fee": trans_fee,
                            "landed": landed, "retail": retail, "gap": gap,
                            "competitive": gap is not None and gap > 0,
                        })

                df_all = pd.DataFrame(all_matches)
                if not df_all.empty:
                    # Pivot: each base's landed cost per station
                    pivot = df_all.pivot_table(index=["name", "cluster", "retail"], columns="基地",
                                              values="landed", aggfunc="first").reset_index()
                    st.dataframe(pivot, use_container_width=True, hide_index=True)
                    st.caption(f"💡 对比 {len(selected_bases)} 个基地在 {sel_radius}km 内的到站成本")
        else:
            # ── 单基地模式 ──
            base_names = ["赤城", "如东", "宁东", "沧州"]
            cols = st.columns(4)
            sel_base = "赤城"
            for i, (col, name) in enumerate(zip(cols, base_names)):
                with col:
                    cost = GUOHUA_BASES_COST.get(name, 15.2)
                    if st.button(f"🏭 {name}\n{cost}元/kg", key=f"base_{name}", use_container_width=True,
                                 type="primary" if i == 0 else "secondary"):
                        sel_base = name

            base_cost = GUOHUA_BASES_COST.get(sel_base, 15.2)
            blat, blon = BASE_COORDS.get(sel_base, (40.91, 115.83))

            matches = []
            for s in stations:
                lat, lon = s.get("lat"), s.get("lon")
                if not lat or not lon: continue
                dist = haversine_km(blat, blon, lat, lon)
                if dist > sel_radius: continue
                landed, trans_fee = compute_landed(base_cost, dist, sel_mode)
                retail = s.get("purchase_price_low") or s.get("retail_price")
                cluster = s.get("city_cluster", "")
                eff_retail = retail
                if show_subsidy and retail:
                    for ck, sv in CITY_SUBSIDIES.items():
                        if ck in cluster or cluster in ck:
                            eff_retail = retail - sv; break
                gap = (eff_retail - landed) if eff_retail and eff_retail > 0 else None
                matches.append({
                    "name": s.get("name", "")[:25], "cluster": cluster,
                    "city": s.get("province", ""),
                    "distance": round(dist, 1), "transport_fee": trans_fee,
                    "landed": landed, "retail": retail, "gap": gap,
                    "competitive": gap is not None and gap > 0,
                })
            matches.sort(key=lambda x: x["distance"])

            competitive = [m for m in matches if m.get("competitive")]
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("圈内站点", f"{len(matches)} 座")
            with c2: st.metric("成本优势站", f"{len(competitive)} 座",
                              delta=f"{len(competitive)/max(len(matches),1)*100:.0f}%")
            with c3: st.metric("平均到站成本", f"{np.mean([m['landed'] for m in matches]):.1f} 元/kg" if matches else "—")
            with c4: st.metric("平均价差", f"{np.mean([m['gap'] for m in competitive]):+.1f} 元/kg" if competitive else "—")

            # Scatter chart
            fig = go.Figure()
            colors = [GREEN if m["competitive"] else RED if m.get("gap") is not None else "#94a3b8" for m in matches]
            fig.add_trace(go.Scatter(
                x=[m["distance"] for m in matches], y=[m["landed"] for m in matches],
                mode="markers", marker=dict(size=9, color=colors, opacity=0.75, line=dict(width=1, color="white")),
                text=[f"<b>{m['name']}</b><br>距离:{m['distance']}km<br>到站:{m['landed']}元" for m in matches],
                hoverinfo="text",
            ))
            fig.add_hline(y=base_cost, line_dash="dash", line_color=BRAND,
                          annotation=dict(text=f"出厂{base_cost}元", font_size=10))
            fig.add_hline(y=30, line_dash="dot", line_color=RED,
                          annotation=dict(text="市场参考30元", font_size=10))
            fig.update_layout(title=f"{sel_base} · {sel_mode} · {sel_radius}km 成本竞争力", height=430,
                            xaxis_title="运输距离(km)", yaxis_title="到站成本(元/kg)",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            # Key insight
            if competitive:
                best = min(competitive, key=lambda m: m["landed"])
                st.info(f"💡 **关键洞察**：{sel_base}基地在{sel_radius}km内覆盖{len(matches)}站，其中{len(competitive)}站具有成本优势。最近优势站为「{best['name']}」，到站价{best['landed']}元/kg，较零售价低{best['gap']}元/kg。")

            # Data table + Excel export
            if matches:
                df = build_match_dataframe(matches[:15])
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Excel export
                df_full = build_match_dataframe(matches)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_full.to_excel(writer, sheet_name=f'{sel_base}_{sel_radius}km', index=False)
                st.download_button("📥 导出Excel", data=output.getvalue(),
                                  file_name=f"成本竞争力_{sel_base}_{sel_radius}km.xlsx",
                                  mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # ── Next action ──
            if competitive:
                top3 = competitive[:3]
                actions = "；".join([f"「{m['name']}」到站{m['landed']}元，低于零售{m['gap']}元" for m in top3])
                st.success(f"🎯 **推荐行动**：优先联系 {actions}。建议以到站成本+合理利润报价，突出绿色认证+碳码追溯差异化服务。")

    # ═══════════ TAB 2 ═══════════
    with tab2:
        st.subheader("运输方式比选")
        fig = go.Figure()
        dists = list(range(0, 501, 50))
        for mode_name, mode_info in TRANSPORT_MODES.items():
            costs = [d * mode_info["cost_per_100km"] / 100 for d in dists]
            dash = "solid" if "气态" in mode_name else "dot" if "液氢" in mode_name else "dash"
            fig.add_trace(go.Scatter(x=dists, y=costs, name=mode_name, mode="lines",
                                    line=dict(width=2.5, dash=dash)))
        fig.update_layout(title="运输成本随距离变化", height=360,
                         xaxis_title="运输距离(km)", yaxis_title="运输成本(元/kg)",
                         plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 **关键洞察**：200km以内长管拖车(30MPa)最具经济性；200-500km液氢优势明显；500km以上铁路液氨成本最低（仅0.03元/100km·kg折氢）。")

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
                with c4: st.metric("vs零售价", f"{sc['retail']} 元/kg", delta=f"{gap:+.1f} 元/kg")

        # Custom scenario
        st.markdown("---")
        st.subheader("自定义销售场景")
        cc1, cc2, cc3, cc4 = st.columns(4)
        with cc1:
            cust_base = st.selectbox("制氢基地", list(GUOHUA_BASES_COST.keys()), key="cust_base")
        with cc2:
            cust_dist = st.number_input("运输距离(km)", 0, 3000, 100, 10, key="cust_dist")
        with cc3:
            cust_mode = st.selectbox("运输方式", list(TRANSPORT_MODES.keys()), key="cust_mode")
        with cc4:
            cust_retail = st.number_input("目标零售价(元/kg)", 10, 80, 30, 1, key="cust_retail")

        cust_cost = GUOHUA_BASES_COST.get(cust_base, 15.2)
        cust_landed, cust_trans = compute_landed(cust_cost, cust_dist, cust_mode)
        cust_gap = cust_retail - cust_landed
        st.metric("到站成本", f"{cust_landed} 元/kg", delta=f"vs零售 {cust_gap:+.1f} 元/kg")
        if cust_gap > 0:
            st.success(f"✅ 有成本优势：每kg毛利 {cust_gap:.1f} 元")
        else:
            st.error(f"❌ 无成本优势：到站成本高于零售价 {abs(cust_gap):.1f} 元/kg")

    # ═══════════ TAB 3 ═══════════
    with tab3:
        st.subheader("国华基地 vs 市场零售价")
        pin_unlocked = st.session_state.get("show_exact_costs", False)

        fig = go.Figure()
        base_names_all = list(GUOHUA_BASES_COST.keys())
        if pin_unlocked:
            base_costs_all = [GUOHUA_BASES_COST[n] for n in base_names_all]
            fig.add_trace(go.Bar(name="出厂成本(精确)", x=base_names_all, y=base_costs_all,
                                marker_color=BRAND, text=[f"{c}元" for c in base_costs_all],
                                textposition="outside", textfont_size=10))
        else:
            base_costs_mid = [GUOHUA_BASES_COST.get(n, 15) for n in base_names_all]
            fig.add_trace(go.Bar(name="出厂成本(区间)", x=base_names_all, y=base_costs_mid,
                                marker_color=BRAND, text=["~15元" if n != "沧州" else "~10元" for n in base_names_all],
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
                      annotation=dict(text="市场参考30元/kg", font_size=9))
        fig.add_hline(y=25, line_dash="dot", line_color=GREEN, line_width=1,
                      annotation=dict(text="2030目标25元/kg", font_size=9))
        fig.update_layout(title="国华基地成本对标" + ("（精确值）" if pin_unlocked else "（锁定中）"),
                         height=400, yaxis_title="元/kg",
                         plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        st.info("💡 **关键洞察**：沧州副产氢出厂成本最低(9.6元/kg)，但产量有限(6500t/y)。绿氢基地(赤城/如东/宁东)成本一致(15.2元/kg)，200km到站约30元/kg，已接近市场均价，具备规模化竞争力。")

        st.markdown("### 城市群零售价与补贴")
        sub_tbl = [{"城市群": k, "补贴标准(元/kg)": v} for k, v in CITY_SUBSIDIES.items()]
        st.dataframe(pd.DataFrame(sub_tbl), use_container_width=True, hide_index=True)

        st.markdown("### 行业参考数据")
        ref_tbl = [{"指标": k, "数值": v["value"], "来源": v["source"]} for k, v in REFERENCE_DATA.items()]
        st.dataframe(pd.DataFrame(ref_tbl), use_container_width=True, hide_index=True,
                    column_config={"来源": st.column_config.TextColumn(width="large")})
        st.caption("💡 数据来源包括中国产业发展促进会氢能分会、全国碳市场、国家能源局、隆众资讯、ICE、IEA、model.xlsx等。标注时间为公开值。")
