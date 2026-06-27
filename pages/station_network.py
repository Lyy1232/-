"""加氢站网络分析 — Platts风格 · 数据源：SQLite/示范城市群真实运营数据"""
import json
import streamlit as st
import folium
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from folium import Circle, Popup, Tooltip
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from utils.data_loader import load_sites, load_stations, load_stations_from_db, get_station_stats, get_cluster_stats
from utils.geo_utils import haversine_km
from utils.ui import render_module_header
from config.constants import TECH_COLORS, TECH_ZH, ECONOMIC_RADIUS_KM

CLUSTER_COLORS = {
    "京津冀": "#00a99d", "河北": "#f59e0b", "郑州": "#2563eb",
    "广东": "#d97706", "上海": "#7c3aed",
}


@st.cache_resource(show_spinner=False)
def _cached_station_map(sites_json: str, stations_json: str, selected_name: str):
    """Cached station map — only rebuilds when params change."""
    sites = json.loads(sites_json)
    stations = json.loads(stations_json)
    selected_site = next((s for s in sites if s["name"] == selected_name), None) if selected_name else None
    return _build_coverage_map_impl(sites, stations, selected_site)


def _build_coverage_map_impl(sites, stations, selected_site=None):
    clat = selected_site["lat"] if selected_site else 39.0
    clon = selected_site["lon"] if selected_site else 116.0
    m = folium.Map(location=[clat, clon], zoom_start=8 if selected_site else 6,
                   tiles="https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
                   attr="高德地图", control_scale=True)
    Fullscreen().add_to(m)

    for site in sites:
        color = TECH_COLORS.get(site["tech"], "#64748b")
        is_sel = selected_site and selected_site["name"] == site["name"]
        # Concentric rings: 50/100/150/200km
        rings = [
            (50,  0.14, 1.2, 0.65),
            (100, 0.08, 0.9, 0.40),
            (150, 0.05, 0.6, 0.22),
            (200, 0.02, 0.4, 0.10),
        ]
        if is_sel:
            rings = [(r, fo + 0.06, w + 0.6, op + 0.2) for r, fo, w, op in rings]
        for radius_km, fill_op, weight, opacity in rings:
            Circle(location=[site["lat"], site["lon"]], radius=radius_km * 1000,
                   color=color, fill=True, fill_color=color,
                   fill_opacity=fill_op, weight=weight, opacity=opacity).add_to(m)
        folium.Marker(location=[site["lat"], site["lon"]],
                      icon=folium.Icon(color="darkgreen", icon="industry", prefix="fa"),
                      popup=folium.Popup(f"<b>{site['name']}</b><br>{TECH_ZH.get(site['tech'], site['tech'])}<br>¥{site['cost_avg']}/kg", max_width=180)).add_to(m)
        folium.map.Marker(location=[site["lat"] + 0.05, site["lon"]],
                          icon=folium.DivIcon(html=f'<div style="font-size:9px;font-weight:700;color:#1e293b;background:rgba(255,255,255,0.88);padding:1px 4px;border-radius:2px">🏭 {site["name"]}</div>')).add_to(m)

    for s in stations:
        lat, lon = s["lat"], s["lon"]
        covered_by = [site["name"] for site in sites if haversine_km(lat, lon, site["lat"], site["lon"]) <= ECONOMIC_RADIUS_KM]
        cov_label = f"覆盖: {', '.join(covered_by)}" if covered_by else "⚠️ 无覆盖"
        ico_c, ico_n = ("green", "star") if s.get("is_guohua") else ("orange", "wrench") if s.get("status") == "在建" else ("blue", "gas-pump")
        popup_html = f"""
        <div style="font-family:-apple-system,sans-serif;min-width:190px">
          <h4 style="margin:0;font-size:13px">{s['name']} {'<span style="background:#dcfce7;color:#166534;padding:1px 5px;border-radius:3px;font-size:9px">国华</span>' if s.get('is_guohua') else ''}</h4>
          <p style="font-size:10px;color:#64748b;margin:2px 0">{s.get('owner','')} · {s.get('province','')}</p>
          <hr style="margin:4px 0;border-color:#e5e7eb">
          <table style="font-size:10px;width:100%;line-height:1.5">
            <tr><td style="color:#64748b">日能力</td><td><b>{s.get('daily_capacity_kg',0)} kg</b></td></tr>
            <tr><td style="color:#64748b">实际</td><td><b>{s.get('actual_throughput_kg',0)} kg</b></td></tr>
            <tr><td style="color:#64748b">购氢价</td><td><b>¥{s.get('purchase_price_low',0)}–¥{s.get('purchase_price_high',0)}</b></td></tr>
            <tr><td style="color:#64748b">氢源</td><td>{s.get('h2_source','—')}</td></tr>
          </table>
        </div>"""
        folium.Marker(location=[lat, lon],
                      icon=folium.Icon(color=ico_c, icon=ico_n, prefix="fa"),
                      popup=Popup(popup_html, max_width=280),
                      tooltip=Tooltip(f"{s['name']} · {cov_label}")).add_to(m)

    # Legend
    clusters_in = list(dict.fromkeys(s.get("city_cluster", "") for s in stations))
    lr = "".join(f'<tr><td><span style="display:inline-block;width:9px;height:9px;border-radius:2px;background:{CLUSTER_COLORS.get(c,"#94a3b8")}"></span></td><td style="font-size:10px;color:#334155">{c}</td></tr>' for c in clusters_in)
    legend_html = f"""<div style="position:fixed;bottom:18px;right:18px;z-index:9999;background:rgba(255,255,255,0.95);padding:8px 12px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.08);line-height:1.6">
      <b style="font-size:11px;color:#1e293b">图例</b><table style="margin-top:3px">{lr}
      <tr><td><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#10b981"></span></td><td style="font-size:10px;color:#334155">⭐ 国华供氢</td></tr>
      <tr><td><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#2563eb"></span></td><td style="font-size:10px;color:#334155">社会站</td></tr></table></div>"""
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


@st.cache_data(show_spinner=False, ttl=300)
def _coverage_table(sites_json: str, stations_json: str):
    sites = json.loads(sites_json)
    stations = json.loads(stations_json)
    rows = []
    for site in sites:
        covered = [(s, haversine_km(s["lat"], s["lon"], site["lat"], site["lon"]))
                   for s in stations if haversine_km(s["lat"], s["lon"], site["lat"], site["lon"]) <= ECONOMIC_RADIUS_KM]
        covered.sort(key=lambda x: x[1])
        rows.append({"基地": site["name"], "覆盖站数": len(covered),
                     "国华自有": sum(1 for s, _ in covered if s.get("is_guohua")),
                     "日需求(kg)": sum(s.get("actual_throughput_kg", 0) for s, _ in covered),
                     "最近站": covered[0][0]["name"] if covered else "—",
                     "最近距离": f"{covered[0][1]:.0f}km" if covered else "—",
                     "城市群": ", ".join(dict.fromkeys(s.get("city_cluster","") for s, _ in covered))})
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False, ttl=300)
def _demand_gap(sites_json: str, stations_json: str):
    sites = json.loads(sites_json)
    stations = json.loads(stations_json)
    opps = []
    for s in stations:
        if s.get("is_guohua") or s.get("status") != "运营中": continue
        for site in sites:
            d = haversine_km(s["lat"], s["lon"], site["lat"], site["lon"])
            if d <= ECONOMIC_RADIUS_KM:
                opps.append({"站名": s["name"], "城市群": s.get("city_cluster",""), "省份": s.get("province",""),
                              "当前氢源": s.get("h2_source",""), "日加注(kg)": s.get("actual_throughput_kg",0),
                              "购氢价": f"¥{s.get('purchase_price_low',0)}–¥{s.get('purchase_price_high',0)}",
                              "可供应基地": site["name"], "距离": f"{d:.0f}km", "基地成本": f"¥{site['cost_avg']}"})
                break
    return pd.DataFrame(opps) if opps else pd.DataFrame()


def render():
    render_module_header("加氢站网络", "示范城市群真实运营数据 · SQLite 驱动 · 303座加氢站", badge="LIVE")

    sites = load_sites()
    # 优先使用 SQLite 真实数据，fallback 到 mock 数据
    stations = load_stations_from_db(year=4)
    if not stations:
        stations = load_stations()
    if not stations:
        st.warning("⚠️ 未加载加氢站数据。请先运行 python utils/build_sqlite.py")
        return

    stats = get_station_stats(stations)

    # KPI row
    kpi_cols = st.columns(5)
    kpis = [
        ("⛽", str(stats["count"]), "Y4 加氢站", "示范城市群统计"),
        ("⚡", f"{stats['total_capacity']:,}", "日供氢能力 kg", ""),
        ("📈", f"{stats['avg_load']}%", "平均负荷率", f"年加注 {stats['total_throughput']:,.0f} kg"),
        ("🏙️", str(len(get_cluster_stats(stations))), "城市群", "京津冀·河北·郑州·广东·上海"),
        ("🛢️", "91", "制氢企业", "去重后"),
    ]
    for col, (icon, val, lbl, sub) in zip(kpi_cols, kpis):
        with col:
            st.markdown(f"""<div class="metric-card">
              <div class="mc-accent-bar" style="background:#00a99d"></div>
              <div class="mc-icon">{icon}</div>
              <div class="mc-value">{val}</div>
              <div class="mc-label">{lbl}</div>
              {f'<div class="mc-sub">{sub}</div>' if sub else ''}
            </div>""", unsafe_allow_html=True)

    st.markdown('<div style="margin:16px 0"></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ 网络地图", "📊 覆盖分析", "🏙️ 城市群", "📋 数据明细"])

    with tab1:
        c1, c2 = st.columns([2, 1])
        with c1:
            focus = st.selectbox("聚焦基地", ["全部"] + [s["name"] for s in sites], key="sf")
        with c2:
            cl_sel = st.multiselect("城市群", list(dict.fromkeys(s.get("city_cluster","") for s in stations)), key="cf")
        sel = next((s for s in sites if s["name"] == focus), None) if focus != "全部" else None
        filtered = [s for s in stations if not cl_sel or s.get("city_cluster","") in cl_sel]
        with st.spinner("加载地图..."):
            m = _cached_station_map(
                json.dumps(sites, ensure_ascii=False, sort_keys=True),
                json.dumps(filtered, ensure_ascii=False, sort_keys=True),
                sel["name"] if sel else "",
            )
        st_folium(m, width="100%", height=540, returned_objects=[])

    with tab1:
        st.subheader(f"各基地 {ECONOMIC_RADIUS_KM}km 覆盖分析")
        df_cov = _coverage_table(json.dumps(sites, ensure_ascii=False, sort_keys=True), json.dumps(stations, ensure_ascii=False, sort_keys=True))
        st.dataframe(df_cov, width="stretch", hide_index=True)
        fig = px.bar(df_cov, x="基地", y="覆盖站数", color="基地",
                     color_discrete_sequence=["#00a99d", "#2563eb", "#d97706", "#7c3aed"],
                     text="覆盖站数", title=f"各基地辐射圈内加氢站数量")
        fig.update_traces(textposition="outside", textfont=dict(size=13, color="#1e293b"))
        fig.update_layout(
        height=280, showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_family="-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif",
        xaxis=dict(tickfont=dict(size=11, color="#64748b")), yaxis=dict(tickfont=dict(size=10, color="#64748b"), gridcolor="rgba(0,0,0,0.04)"),
    )
        st.plotly_chart(fig, width="stretch")

    with tab2:
        clusters = get_cluster_stats(stations)
        st.subheader("城市群统计")
        cc = st.columns(len(clusters))
        for col, c in zip(cc, clusters):
            with col:
                color = CLUSTER_COLORS.get(c["name"], "#94a3b8")
                st.markdown(f"""<div class="metric-card"><div class="mc-accent-bar" style="background:{color}"></div>
                  <div style="font-weight:800;font-size:14px;color:#1e293b;margin-bottom:4px">{c['name']}</div>
                  <div class="mc-value">{c['count']}<span style="font-size:11px;color:#64748b"> 站</span></div>
                  <div class="mc-label">能力 {c['capacity']:,}kg · 实加 {c['throughput']:,}kg</div></div>""", unsafe_allow_html=True)

        df_cl = pd.DataFrame(clusters)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="日能力(kg)", x=df_cl["name"], y=df_cl["capacity"], marker_color="#00a99d", marker_opacity=0.5))
        fig.add_trace(go.Bar(name="年加注(kg)", x=df_cl["name"], y=df_cl["throughput"], marker_color="#1e293b"))
        fig.update_layout(
        barmode="group", height=300,
        title=dict(text="各城市群日加氢能力 vs 年加注量", font=dict(size=15, color="#0f172a")),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_family="-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif",
        xaxis=dict(tickfont=dict(size=11, color="#64748b")), yaxis=dict(tickfont=dict(size=10, color="#64748b"), gridcolor="rgba(0,0,0,0.04)"),
        legend=dict(orientation="h", y=1.12, font=dict(size=11, color="#64748b")),
    )
        st.plotly_chart(fig, width="stretch")

    with tab3:
        st.subheader("加氢站明细（Y4 · 示范城市群真实数据）")
        st.caption(f"共 {len(stations)} 座 · 数据来源：国家燃料电池汽车示范城市群氢能供应明细表")
        df_st = pd.DataFrame(stations)
        disp = ["name", "city_cluster", "province", "owner", "daily_capacity_kg",
                "actual_throughput_kg", "purchase_price_low", "is_highway", "status"]
        df_st["负荷率%"] = (df_st["actual_throughput_kg"] / df_st["daily_capacity_kg"] * 100).round(1)
        st.dataframe(df_st[disp].rename(columns={
            "name": "站名", "city_cluster": "城市群", "province": "城市", "owner": "运营企业",
            "daily_capacity_kg": "日能力(kg)", "actual_throughput_kg": "日均加注(kg)",
            "purchase_price_low": "零售价", "is_highway": "高速示范", "status": "状态"
        }), width="stretch", hide_index=True,
            column_config={
                "高速示范": st.column_config.CheckboxColumn(),
            })
