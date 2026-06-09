"""P1 核心：生产基地地图 — Folium 交互地图 + 四基地标注 + 200km 辐射圈 + 成本对比"""
import streamlit as st
import folium
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from folium import Circle, Popup, Tooltip
from folium.plugins import Fullscreen, MeasureControl
from streamlit_folium import st_folium
from utils.data_loader import load_sites, load_competitors
from utils.geo_utils import haversine_km
from utils.ui import render_header
from config.constants import TECH_COLORS, TECH_ZH, TILE_OPTIONS, DEFAULT_COLOR, ECONOMIC_RADIUS_KM

COMPETITOR_STATUS_COLORS = {"已投产": "#ef4444", "在建": "#f59e0b", "规划": "#94a3b8"}


def _fmt_site_popup(site: dict, color: str) -> str:
    tech_zh = TECH_ZH.get(site["tech"], site["tech"])
    cert = site.get("cert_status", "—")
    util = site.get("utilization", "—")
    start = site.get("start_date", "—")
    return f"""
    <div style="font-family:-apple-system,sans-serif;min-width:220px">
      <h4 style="margin:0 0 2px;color:{color};font-size:15px">{site['name']} · {site['province']}</h4>
      <p style="margin:2px 0;font-size:11px;color:#64748b">{tech_zh}</p>
      <hr style="margin:6px 0;border-color:#e5e7eb">
      <table style="font-size:11px;width:100%;line-height:1.6">
        <tr><td style="color:#64748b">产能</td><td><b>{site['capacity']:,} 吨/年</b></td></tr>
        <tr><td style="color:#64748b">利用率</td><td><b>{util}%</b></td></tr>
        <tr><td style="color:#64748b">成本区间</td><td style="color:{color}"><b>¥{site['cost_low']}–¥{site['cost_high']}/kg</b></td></tr>
        <tr><td style="color:#64748b">平均成本</td><td style="color:{color};font-size:13px"><b>¥{site['cost_avg']}/kg</b></td></tr>
        <tr><td style="color:#64748b">认证</td><td>{cert}</td></tr>
        <tr><td style="color:#64748b">投产</td><td>{start}</td></tr>
      </table>
    </div>"""


def _get_folium_icon(tech: str) -> tuple[str, str]:
    if "电解" in tech:
        return "darkgreen", "industry"
    if "CCS" in tech:
        return "blue", "industry"
    if "副产" in tech:
        return "orange", "industry"
    return "gray", "industry"


def build_map(sites: list[dict], show_radius: bool = True,
              selected_site: dict | None = None,
              tile_key: str = "高德地图（推荐）",
              show_competitors: bool = False, competitors: list[dict] | None = None) -> folium.Map:
    """Build Folium map with site markers, radius circles, competitor markers, legend, and measurement tool."""

    tile_cfg = TILE_OPTIONS.get(tile_key, TILE_OPTIONS["高德地图（推荐）"])
    tiles = tile_cfg["url"]
    attr = tile_cfg.get("attr", "")
    center_lat = selected_site["lat"] if selected_site else 37.5
    center_lon = selected_site["lon"] if selected_site else 110.0
    zoom = 9 if selected_site else 5

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles=tiles,
        attr=attr,
        control_scale=True,
    )
    Fullscreen().add_to(m)
    MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(m)

    for site in sites:
        lat, lon = site["lat"], site["lon"]
        tech = site["tech"]
        color = TECH_COLORS.get(tech, DEFAULT_COLOR)
        is_sel = selected_site and selected_site["name"] == site["name"]

        if show_radius:
            Circle(
                location=[lat, lon],
                radius=ECONOMIC_RADIUS_KM * 1000,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.08 if is_sel else 0.04,
                weight=2.5 if is_sel else 1,
                opacity=0.6 if is_sel else 0.2,
                dash_array=None if is_sel else "8 6",
            ).add_to(m)

        icon_color, icon_name = _get_folium_icon(tech)
        folium.Marker(
            location=[lat, lon],
            popup=Popup(_fmt_site_popup(site, color), max_width=300),
            tooltip=Tooltip(f"{site['name']} · {TECH_ZH.get(tech, tech)} · ¥{site['cost_avg']}/kg"),
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa"),
        ).add_to(m)

        # Label
        label_color = color if is_sel else "#475569"
        label_weight = "700" if is_sel else "600"
        folium.map.Marker(
            location=[lat + 0.12, lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:{"12px" if is_sel else "11px"};font-weight:{label_weight};color:#0f172a;background:rgba(255,255,255,0.9);padding:2px 7px;border-radius:3px;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,0.1);border-left:3px solid {label_color}">{site["name"]}<br><span style="font-size:8px;color:#64748b">{TECH_ZH.get(tech, tech)} · ¥{site["cost_avg"]}</span></div>'
            ),
        ).add_to(m)

    # Competitor markers
    if show_competitors and competitors:
        for comp in competitors:
            c_lat, c_lon = comp["lat"], comp["lon"]
            comp_color = COMPETITOR_STATUS_COLORS.get(comp.get("status", ""), "#94a3b8")
            comp_popup = f"""
            <div style="font-family:-apple-system,sans-serif;min-width:180px">
              <h4 style="margin:0 0 2px;color:{comp_color};font-size:14px">⚠️ {comp['name']}</h4>
              <p style="margin:2px 0;font-size:11px;color:#64748b">{comp.get('province','')} · {comp.get('tech','')}</p>
              <hr style="margin:6px 0;border-color:#e5e7eb">
              <table style="font-size:11px;width:100%;line-height:1.6">
                <tr><td style="color:#64748b">产能</td><td><b>{comp.get('capacity',0):,} t/y</b></td></tr>
                <tr><td style="color:#64748b">估成本</td><td><b>¥{comp.get('cost_est',0)}/kg</b></td></tr>
                <tr><td style="color:#64748b">状态</td><td style="color:{comp_color}"><b>{comp.get('status','')}</b></td></tr>
              </table>
              <p style="font-size:10px;color:#94a3b8;margin-top:4px">{comp.get('notes','')}</p>
            </div>"""
            folium.Marker(
                location=[c_lat, c_lon],
                icon=folium.Icon(color="red" if comp.get("status") == "已投产" else "orange" if comp.get("status") == "在建" else "gray",
                                 icon="exclamation-triangle" if comp.get("status") == "已投产" else "clock-o" if comp.get("status") == "在建" else "question", prefix="fa"),
                popup=folium.Popup(comp_popup, max_width=280),
                tooltip=folium.Tooltip(f"⚠️ {comp['name']} · {comp.get('status','')} · ¥{comp.get('cost_est',0)}/kg"),
            ).add_to(m)

    # Legend overlay
    legend_rows = ""
    for tech, color in TECH_COLORS.items():
        legend_rows += f'<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{color}"></span></td><td style="font-size:11px;color:#334155">{TECH_ZH.get(tech, tech)}</td></tr>'
    legend_html = f"""
    <div style="position:fixed;bottom:20px;right:20px;z-index:9999;background:rgba(255,255,255,0.94);padding:10px 14px;border-radius:8px;box-shadow:0 2px 14px rgba(0,0,0,0.08);line-height:1.7">
      <b style="font-size:12px;color:#0f172a">图例</b>
      <table style="margin-top:4px">{legend_rows}
        <tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;border:2px solid #94a3b8"></span></td><td style="font-size:11px;color:#334155">{ECONOMIC_RADIUS_KM}km 辐射圈</td></tr>
      </table>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def _build_site_card(site: dict) -> str:
    tech = site["tech"]
    color = TECH_COLORS.get(tech, DEFAULT_COLOR)
    tech_zh = TECH_ZH.get(tech, tech)
    cert = site.get("cert_status", "—")
    util = site.get("utilization", "—")
    return f"""
    <div class="site-card" style="margin-bottom:10px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
        <span style="width:10px;height:10px;border-radius:50%;background:{color};display:inline-block;flex-shrink:0"></span>
        <strong style="color:#0f172a;font-size:14px">{site['name']}</strong>
        <span style="color:#64748b;font-size:10px">{site['province']}</span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 14px;font-size:11px;color:#475569">
        <div>技术: <b>{tech_zh}</b></div>
        <div>产能: <b>{site['capacity']:,} t/y</b></div>
        <div>成本: <b style="color:{color}">¥{site['cost_avg']}/kg</b></div>
        <div>利用率: <b>{util}%</b></div>
        <div style="grid-column:1/-1">认证: {cert}</div>
      </div>
    </div>"""


def _cost_comparison_chart(sites: list[dict]):
    """Build a Plotly grouped bar chart comparing costs across sites."""
    df = pd.DataFrame(sites)
    df["tech_zh"] = df["tech"].map(TECH_ZH)
    df["color"] = df["tech"].map(TECH_COLORS).fillna(DEFAULT_COLOR)
    df = df.sort_values("cost_avg")

    fig = go.Figure()
    # Cost range bar
    for _, row in df.iterrows():
        fig.add_trace(go.Bar(
            name=row["name"],
            x=[row["name"]],
            y=[row["cost_high"] - row["cost_low"]],
            base=[row["cost_low"]],
            marker_color=row["color"],
            marker_opacity=0.35,
            width=0.5,
            text=f"¥{row['cost_low']}–¥{row['cost_high']}",
            textposition="outside",
            textfont=dict(size=10, color="#64748b"),
            hovertemplate=f"<b>{row['name']}</b><br>成本区间: ¥{row['cost_low']}–¥{row['cost_high']}/kg<br>平均: ¥{row['cost_avg']}/kg<extra></extra>",
            showlegend=False,
        ))

    # Avg cost marker
    fig.add_trace(go.Scatter(
        x=df["name"],
        y=df["cost_avg"],
        mode="markers+text",
        marker=dict(symbol="diamond", size=14, color="white", line=dict(color="#0f172a", width=2)),
        text=[f"¥{v}" for v in df["cost_avg"]],
        textposition="middle left",
        textfont=dict(size=11, color="#0f172a", family="sans-serif"),
        name="平均成本",
        hovertemplate="%{text}/kg<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="基地生产成本对比", font=dict(size=16, color="#0f172a")),
        xaxis=dict(title=None, tickfont=dict(size=12)),
        yaxis=dict(title="¥/kg", tickfont=dict(size=11), gridcolor="rgba(0,0,0,0.06)"),
        height=320,
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def _distance_calculator(sites: list[dict]):
    """Interactive distance calculator between two sites."""
    st.markdown("**📏 距离测量**")
    c1, c2, c3 = st.columns([1, 1, 2])
    site_names = [s["name"] for s in sites]
    with c1:
        a_idx = st.selectbox("起点", range(len(sites)), format_func=lambda i: site_names[i], key="dist_a")
    with c2:
        b_idx = st.selectbox("终点", range(len(sites)), format_func=lambda i: site_names[i],
                             index=min(1, len(sites)-1), key="dist_b")
    with c3:
        if a_idx != b_idx:
            d = haversine_km(sites[a_idx]["lat"], sites[a_idx]["lon"],
                             sites[b_idx]["lat"], sites[b_idx]["lon"])
            in_range = d <= ECONOMIC_RADIUS_KM
            emoji = "✅" if in_range else "⚠️"
            msg = f"{emoji} **{d:.0f} km** — {'在' if in_range else '超出'}经济辐射半径 ({ECONOMIC_RADIUS_KM}km)"
            st.info(msg)
        else:
            st.caption("请选择不同基地")


def render():
    lang = st.session_state.get("lang", "zh")
    render_header()

    sites = load_sites()
    competitors = load_competitors()
    if not sites:
        st.warning("⚠️ 未加载到基地数据，请先在「数据管理」中录入基地信息。")
        if st.button("📊 前往数据管理", type="primary"):
            st.session_state.page = "data"
            st.rerun()
        return

    # Session state
    if "map_selected_idx" not in st.session_state:
        st.session_state.map_selected_idx = 0
    if "map_show_radius" not in st.session_state:
        st.session_state.map_show_radius = True
    if "map_tile_key" not in st.session_state:
        st.session_state.map_tile_key = "高德地图（推荐）"

    # ── Control bar ──
    c1, c2, c3, c4, c5 = st.columns([1.5, 1, 1, 0.8, 1.2])
    with c1:
        st.session_state.map_show_radius = st.checkbox(
            f"显示 {ECONOMIC_RADIUS_KM}km 辐射圈", value=st.session_state.map_show_radius
        )
    with c2:
        show_comp = st.checkbox("显示竞品", value=st.session_state.get("map_show_competitors", False))
        st.session_state.map_show_competitors = show_comp
    with c3:
        tile_keys = list(TILE_OPTIONS.keys())
        cur_tile = tile_keys.index(st.session_state.map_tile_key) if st.session_state.map_tile_key in tile_keys else 0
        st.session_state.map_tile_key = st.selectbox("地图底图", tile_keys, index=cur_tile)
    with c4:
        site_names = ["全部基地"] + [s["name"] for s in sites]
        st.session_state.map_selected_idx = st.selectbox(
            "聚焦基地", range(len(site_names)),
            index=st.session_state.map_selected_idx,
            format_func=lambda i: site_names[i],
        )
    with c5:
        ts = sites[0].get("updated_at", "")[:10] if sites and sites[0].get("updated_at") else "—"
        st.caption(f"💡 点击标记查看详情 | 📅 更新: {ts}")

    selected_site = sites[st.session_state.map_selected_idx - 1] if st.session_state.map_selected_idx > 0 else None

    # ── Map + Sidebar ──
    map_col, info_col = st.columns([0.65, 0.35])

    with map_col:
        with st.spinner("加载地图..."):
            m = build_map(
                sites, show_radius=st.session_state.map_show_radius,
                selected_site=selected_site, tile_key=st.session_state.map_tile_key,
                show_competitors=show_comp, competitors=competitors,
            )
        st_folium(m, width="100%", height=580, returned_objects=[])

    with info_col:
        st.markdown("**📋 基地详情**")
        if selected_site:
            st.info(f"📍 聚焦: **{selected_site['name']}** · {TECH_ZH.get(selected_site['tech'], selected_site['tech'])}")
        for site in sites:
            st.markdown(_build_site_card(site), unsafe_allow_html=True)

        st.markdown("---")
        _distance_calculator(sites)

    # ── Cost comparison chart ──
    st.markdown("---")
    st.subheader("📊 成本对比分析")
    st.plotly_chart(_cost_comparison_chart(sites), width="stretch")

    # Cost comparison: Guohua vs Competitors
    if competitors:
        st.markdown("---")
        st.subheader("⚔️ 成本对标：国华 vs 竞品")
        comp_rows = []
        for site in sites:
            comp_rows.append({
                "类型": "🏭 国华基地", "名称": site["name"], "省份": site["province"],
                "技术路线": TECH_ZH.get(site["tech"], site["tech"]),
                "产能(t/y)": site["capacity"], "成本(¥/kg)": site["cost_avg"], "状态": "运营中",
            })
        for comp in competitors:
            comp_rows.append({
                "类型": "⚠️ 竞品", "名称": comp["name"], "省份": comp.get("province", ""),
                "技术路线": comp.get("tech", ""),
                "产能(t/y)": comp.get("capacity", 0), "成本(¥/kg)": comp.get("cost_est", 0),
                "状态": comp.get("status", ""),
            })
        df_comp = pd.DataFrame(comp_rows).sort_values("成本(¥/kg)")
        st.dataframe(df_comp, width="stretch", hide_index=True,
                     column_config={"成本(¥/kg)": st.column_config.NumberColumn(format="¥%.1f")})

        # Comparison scatter
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=[s["cost_avg"] for s in sites],
            y=[s["capacity"] for s in sites],
            mode="markers+text",
            text=[s["name"] for s in sites],
            textposition="top center",
            marker=dict(size=18, color="#00d4aa", symbol="diamond", line=dict(color="#0f172a", width=1)),
            name="国华基地",
        ))
        fig2.add_trace(go.Scatter(
            x=[c["cost_est"] for c in competitors],
            y=[c.get("capacity", 0) for c in competitors],
            mode="markers+text",
            text=[c["name"] for c in competitors],
            textposition="top center",
            marker=dict(size=14, color="#ef4444", symbol="x-thin", line=dict(color="#ef4444", width=1.5)),
            name="竞品",
        ))
        fig2.update_layout(
            title="成本 vs 产能 竞争格局", height=380,
            xaxis_title="成本 (¥/kg)", yaxis_title="产能 (t/y)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.12),
        )
        st.plotly_chart(fig2, width="stretch")

    # ── Coverage summary ──
    st.markdown("---")
    st.subheader("📏 覆盖分析")
    cov_cols = st.columns(len(sites))
    for col, site in zip(cov_cols, sites):
        lat, lon = site["lat"], site["lon"]
        nearby = [s for s in sites if s["name"] != site["name"]
                  and haversine_km(lat, lon, s["lat"], s["lon"]) <= ECONOMIC_RADIUS_KM]
        with col:
            st.metric(site["name"], f"{len(nearby)} 相邻基地", delta="独立覆盖" if not nearby else None)
            if nearby:
                for ns in nearby:
                    d = haversine_km(lat, lon, ns["lat"], ns["lon"])
                    st.caption(f"↔ {ns['name']} ({d:.0f}km)")
