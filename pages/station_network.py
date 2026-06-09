"""P2 核心：加氢站网络分析 — 200km覆盖 + 城市群分类 + 需求缺口"""
import streamlit as st
import folium
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from folium import Circle, Popup, Tooltip
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from utils.data_loader import load_sites, load_stations, get_station_stats, get_cluster_stats
from utils.geo_utils import haversine_km
from utils.ui import render_header
from config.constants import TECH_COLORS, TECH_ZH, ECONOMIC_RADIUS_KM

CLUSTER_COLORS = {
    "京津冀": "#00d4aa", "长三角": "#4da8da", "珠三角": "#f59e0b",
    "山东半岛": "#a78bfa", "成渝": "#ef4444", "中原城市群": "#fb923c",
}


def _station_popup(s: dict) -> str:
    is_gh = s.get("is_guohua", False)
    badge = '<span style="background:#dcfce7;color:#166534;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:700">国华供氢</span>' if is_gh else ""
    return f"""
    <div style="font-family:-apple-system,sans-serif;min-width:200px">
      <h4 style="margin:0 0 2px;font-size:14px">{s['name']} {badge}</h4>
      <p style="margin:2px 0;font-size:11px;color:#64748b">{s.get('owner','')} · {s.get('province','')} · {s.get('city_cluster','')}</p>
      <hr style="margin:6px 0;border-color:#e5e7eb">
      <table style="font-size:11px;width:100%;line-height:1.6">
        <tr><td style="color:#64748b">日加注能力</td><td><b>{s.get('daily_capacity_kg',0)} kg</b></td></tr>
        <tr><td style="color:#64748b">实际加注量</td><td><b>{s.get('actual_throughput_kg',0)} kg</b></td></tr>
        <tr><td style="color:#64748b">负荷率</td><td><b>{s.get('actual_throughput_kg',0)/max(s.get('daily_capacity_kg',1),1)*100:.0f}%</b></td></tr>
        <tr><td style="color:#64748b">购氢价格</td><td><b>¥{s.get('purchase_price_low',0)}–¥{s.get('purchase_price_high',0)}/kg</b></td></tr>
        <tr><td style="color:#64748b">氢源</td><td>{s.get('h2_source','—')}</td></tr>
        <tr><td style="color:#64748b">状态</td><td>{s.get('status','—')}</td></tr>
      </table>
    </div>"""


def _station_icon(station: dict) -> tuple[str, str]:
    if station.get("is_guohua"):
        return "green", "star"
    if station.get("status") == "在建":
        return "orange", "wrench"
    return "blue", "gas-pump"


def _build_coverage_map(sites: list[dict], stations: list[dict], selected_site: dict | None = None):
    """Build Folium map with stations, base radius, and coverage analysis."""
    center_lat = selected_site["lat"] if selected_site else 39.0
    center_lon = selected_site["lon"] if selected_site else 116.0
    zoom = 8 if selected_site else 6

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
        attr="高德地图",
    )
    Fullscreen().add_to(m)

    # Base radius circles
    for site in sites:
        color = TECH_COLORS.get(site["tech"], "#64748b")
        is_sel = selected_site and selected_site["name"] == site["name"]
        Circle(
            location=[site["lat"], site["lon"]], radius=ECONOMIC_RADIUS_KM * 1000,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.06 if is_sel else 0.02,
            weight=2 if is_sel else 0.8,
            opacity=0.5 if is_sel else 0.15,
            dash_array=None if is_sel else "8 6",
            popup=folium.Popup(f"<b>{site['name']}</b> {ECONOMIC_RADIUS_KM}km 辐射圈", max_width=200),
        ).add_to(m)
        # Base marker
        folium.Marker(
            location=[site["lat"], site["lon"]],
            icon=folium.Icon(color="darkgreen", icon="industry", prefix="fa"),
            popup=folium.Popup(f"<b>{site['name']}</b><br>{TECH_ZH.get(site['tech'], site['tech'])}<br>¥{site['cost_avg']}/kg", max_width=180),
        ).add_to(m)
        folium.map.Marker(
            location=[site["lat"] + 0.06, site["lon"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:700;color:#0f172a;background:rgba(255,255,255,0.88);padding:1px 5px;border-radius:2px;white-space:nowrap">🏭 {site["name"]}</div>'
            ),
        ).add_to(m)

    # Station markers with coverage check
    for s in stations:
        lat, lon = s["lat"], s["lon"]
        icon_color, icon_name = _station_icon(s)

        # Check if within any base's radius
        covered_by = []
        for site in sites:
            if haversine_km(lat, lon, site["lat"], site["lon"]) <= ECONOMIC_RADIUS_KM:
                covered_by.append(site["name"])

        coverage_label = f"覆盖: {', '.join(covered_by)}" if covered_by else "⚠️ 无覆盖"
        tooltip_text = f"{s['name']} · {s.get('city_cluster','')} · {coverage_label}"

        folium.Marker(
            location=[lat, lon],
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa"),
            popup=Popup(_station_popup(s), max_width=300),
            tooltip=Tooltip(tooltip_text),
        ).add_to(m)

    # Legend
    clusters_in_data = list(dict.fromkeys(s.get("city_cluster", "") for s in stations))
    legend_rows = ""
    for c in clusters_in_data:
        color = CLUSTER_COLORS.get(c, "#94a3b8")
        legend_rows += f'<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:{color}"></span></td><td style="font-size:11px;color:#334155">{c}</td></tr>'
    legend_html = f"""
    <div style="position:fixed;bottom:20px;right:20px;z-index:9999;background:rgba(255,255,255,0.94);padding:10px 14px;border-radius:8px;box-shadow:0 2px 14px rgba(0,0,0,0.08);line-height:1.7">
      <b style="font-size:12px;color:#0f172a">图例</b>
      <table style="margin-top:4px">{legend_rows}
        <tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:green"></span></td><td style="font-size:11px;color:#334155">⭐ 国华供氢站</td></tr>
        <tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:blue"></span></td><td style="font-size:11px;color:#334155">社会加氢站</td></tr>
      </table>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


def _coverage_table(sites: list[dict], stations: list[dict]):
    """Build coverage analysis table: each base × stations within 200km."""
    rows = []
    for site in sites:
        covered = []
        for s in stations:
            lat, lon = s["lat"], s["lon"]
            d = haversine_km(lat, lon, site["lat"], site["lon"])
            if d <= ECONOMIC_RADIUS_KM:
                covered.append({"name": s["name"], "distance": d, "throughput": s.get("actual_throughput_kg", 0),
                                "is_guohua": s.get("is_guohua", False), "cluster": s.get("city_cluster", "")})
        covered.sort(key=lambda x: x["distance"])
        rows.append({
            "基地": site["name"],
            "覆盖站数": len(covered),
            "国华自有站": sum(1 for c in covered if c["is_guohua"]),
            "总需求(kg/天)": sum(c["throughput"] for c in covered),
            "最近站": covered[0]["name"] if covered else "—",
            "最近距离": f"{covered[0]['distance']:.0f}km" if covered else "—",
            "覆盖城市群": ", ".join(dict.fromkeys(c["cluster"] for c in covered)),
        })
    return pd.DataFrame(rows)


def _demand_gap_analysis(sites: list[dict], stations: list[dict]):
    """Identify stations NOT covered by any Guohua base."""
    uncovered = []
    for s in stations:
        if s.get("is_guohua"):
            continue  # Already Guohua-supplied
        lat, lon = s["lat"], s["lon"]
        covered = any(
            haversine_km(lat, lon, site["lat"], site["lon"]) <= ECONOMIC_RADIUS_KM
            for site in sites
        )
        if not covered:
            uncovered.append(s)
        else:
            # Check if covered by competitor (Guohua in range but not supplying)
            pass

    # Stations that ARE within Guohua range but NOT currently supplied by Guohua
    opportunities = []
    for s in stations:
        if s.get("is_guohua") or s.get("status") != "运营中":
            continue
        lat, lon = s["lat"], s["lon"]
        for site in sites:
            d = haversine_km(lat, lon, site["lat"], site["lon"])
            if d <= ECONOMIC_RADIUS_KM:
                opportunities.append({
                    "站名": s["name"],
                    "城市群": s.get("city_cluster", ""),
                    "省份": s.get("province", ""),
                    "当前氢源": s.get("h2_source", ""),
                    "日加注量(kg)": s.get("actual_throughput_kg", 0),
                    "购氢价(¥/kg)": f"{s.get('purchase_price_low',0)}–{s.get('purchase_price_high',0)}",
                    "可供应基地": site["name"],
                    "距离(km)": f"{d:.0f}",
                    "基地成本(¥/kg)": site["cost_avg"],
                })
                break
    return pd.DataFrame(opportunities) if opportunities else pd.DataFrame()


def render():
    lang = st.session_state.get("lang", "zh")
    render_header()

    sites = load_sites()
    stations = load_stations()

    if not stations:
        st.warning("⚠️ 未加载加氢站数据。")
        return

    stats = get_station_stats(stations)

    # ── KPI Row ──
    kpi_cols = st.columns(5)
    kpis = [
        ("⛽", str(stats["count"]), "加氢站总数"),
        ("⚡", f"{stats['total_capacity']:,}", "总加注能力(kg/天)"),
        ("📈", f"{stats['avg_load']}%", "平均负荷率"),
        ("⭐", str(stats["guohua_count"]), "国华供氢站"),
        ("🏙️", f"{len(get_cluster_stats(stations))}", "城市群"),
    ]
    for col, (icon, val, lbl) in zip(kpi_cols, kpis):
        with col:
            st.markdown(f"""<div class="metric-card">
              <div style="font-size:22px;margin-bottom:2px">{icon}</div>
              <div class="val">{val}</div><div class="lbl">{lbl}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Tabs ──
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ 网络地图", "📊 覆盖分析", "🎯 市场机会", "🏙️ 城市群统计"])

    # ═══════ Tab 1: Network Map ═══════
    with tab1:
        c1, c2 = st.columns([2, 1])
        with c1:
            focus_sel = st.selectbox("聚焦基地", ["全部基地"] + [s["name"] for s in sites], key="station_focus")
        with c2:
            cluster_sel = st.multiselect("城市群筛选", list(dict.fromkeys(s.get("city_cluster", "") for s in stations)), key="cluster_filter")

        selected = next((s for s in sites if s["name"] == focus_sel), None) if focus_sel != "全部基地" else None
        filtered = [s for s in stations if not cluster_sel or s.get("city_cluster", "") in cluster_sel]

        with st.spinner("加载地图..."):
            m = _build_coverage_map(sites, filtered, selected)
        st_folium(m, width="100%", height=560, returned_objects=[])

    # ═══════ Tab 2: Coverage Analysis ═══════
    with tab2:
        st.subheader(f"各基地 {ECONOMIC_RADIUS_KM}km 覆盖分析")
        df_cov = _coverage_table(sites, stations)
        st.dataframe(df_cov, width="stretch", hide_index=True)

        # Bar chart: stations covered per base
        fig = px.bar(
            df_cov, x="基地", y="覆盖站数", color="基地",
            color_discrete_sequence=["#00d4aa", "#4da8da", "#f59e0b", "#a78bfa"],
            text="覆盖站数", title=f"各基地 {ECONOMIC_RADIUS_KM}km 内加氢站数量",
        )
        fig.update_traces(textposition="outside", textfont=dict(size=14, color="#0f172a"))
        fig.update_layout(height=300, showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch")

    # ═══════ Tab 3: Market Opportunities ═══════
    with tab3:
        st.subheader("🎯 潜在市场机会")
        st.caption(f"辐射圈内 · 运营中 · 非国华供氢 · 可替代的加氢站")

        df_opp = _demand_gap_analysis(sites, stations)
        if df_opp.empty:
            st.info("当前所有辐射圈内运营站已由国华供氢，或无可替代机会。")
        else:
            st.dataframe(df_opp, width="stretch", hide_index=True)
            total_opp_kg = sum(
                s.get("actual_throughput_kg", 0) for s in stations
                if s.get("status") == "运营中" and not s.get("is_guohua")
                and any(haversine_km(s["lat"], s["lon"], site["lat"], site["lon"]) <= ECONOMIC_RADIUS_KM for site in sites)
            )
            st.metric("可争取日需求量", f"{total_opp_kg:,} kg/天", delta="潜在增量")
            st.caption("💡 这些站点在辐射圈内，但氢源来自竞品。是销售团队优先攻坚的目标。")

    # ═══════ Tab 4: City Cluster Stats ═══════
    with tab4:
        clusters = get_cluster_stats(stations)
        st.subheader("城市群统计")

        cluster_cols = st.columns(len(clusters))
        for col, c in zip(cluster_cols, clusters):
            with col:
                color = CLUSTER_COLORS.get(c["name"], "#94a3b8")
                st.markdown(f"""<div class="metric-card" style="border-top:3px solid {color}">
                  <div style="font-weight:800;font-size:16px;color:#0f172a;margin-bottom:4px">{c['name']}</div>
                  <div class="val" style="font-size:24px">{c['count']}<span style="font-size:12px;color:#64748b"> 站</span></div>
                  <div class="lbl">运营中 {c['operational']} · 国华 {c['guohua']}</div>
                  <div class="lbl">日能力 {c['capacity']:,}kg · 实际 {c['throughput']:,}kg</div>
                </div>""", unsafe_allow_html=True)

        # Cluster comparison chart
        df_cl = pd.DataFrame(clusters)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="日加注能力(kg)", x=df_cl["name"], y=df_cl["capacity"],
                             marker_color="#00d4aa", marker_opacity=0.6))
        fig.add_trace(go.Bar(name="实际加注量(kg)", x=df_cl["name"], y=df_cl["throughput"],
                             marker_color="#0f766e"))
        fig.update_layout(
            barmode="group", height=320,
            title="各城市群加氢能力 vs 实际加注量",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.12),
        )
        st.plotly_chart(fig, width="stretch")

        st.markdown("---")
        st.subheader("加氢站明细")
        df_st = pd.DataFrame(stations)
        display_cols = ["name", "city_cluster", "province", "owner", "daily_capacity_kg",
                        "actual_throughput_kg", "purchase_price_low", "h2_source", "is_guohua", "status"]
        df_st["负荷率"] = (df_st["actual_throughput_kg"] / df_st["daily_capacity_kg"] * 100).round(1)
        st.dataframe(
            df_st[display_cols].rename(columns={
                "name": "站名", "city_cluster": "城市群", "province": "省份", "owner": "业主",
                "daily_capacity_kg": "日能力(kg)", "actual_throughput_kg": "实际加注(kg)",
                "purchase_price_low": "购氢低价", "h2_source": "氢源", "is_guohua": "国华供", "status": "状态",
            }),
            width="stretch", hide_index=True,
        )
