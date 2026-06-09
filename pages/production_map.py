"""P1 核心：生产基地地图 — Folium 交互地图 + 四基地标注 + 200km 辐射圈"""
import streamlit as st
import json
from pathlib import Path
import folium
from folium import Circle, Marker, Popup
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from utils.geo_utils import haversine_km
from utils.ui import render_header

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SITES_FILE = PROJECT_ROOT / "config" / "sites.json"

COLORS = {
    "风电+光伏电解": "#00d4aa",
    "风电电解": "#00d4aa",
    "光伏电解": "#4da8da",
    "煤制氢+CCS": "#4da8da",
    "工业副产氢": "#f59e0b",
}

TECH_ZH = {
    "风电+光伏电解": "风光制氢",
    "风电电解": "风电制氢",
    "光伏电解": "光伏制氢",
    "煤制氢+CCS": "煤制氢+CCS",
    "工业副产氢": "副产氢",
}


def load_sites():
    with open(SITES_FILE, "r") as f:
        return json.load(f)


def build_map(sites, show_radius=True, selected_site=None):
    """Build a Folium map centered on China with site markers and 200km radius circles."""
    m = folium.Map(
        location=[37.5, 110.0],
        zoom_start=5,
        tiles="CartoDB positron",
        control_scale=True,
    )
    Fullscreen().add_to(m)

    for site in sites:
        lat, lon = site["lat"], site["lon"]
        tech = site["tech"]
        color = COLORS.get(tech, "#64748b")
        tech_zh = TECH_ZH.get(tech, tech)
        is_selected = selected_site and selected_site["name"] == site["name"]

        # 200km radius circle
        if show_radius:
            Circle(
                location=[lat, lon],
                radius=200_000,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.06,
                weight=1.5 if is_selected else 1,
                opacity=0.5 if is_selected else 0.25,
                dash_array="6 4" if not is_selected else None,
                popup=f"{site['name']} 200km 经济辐射圈",
            ).add_to(m)

        # Site marker
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:200px">
          <h4 style="margin:0 0 4px;color:{color}">{site['name']} · {site['province']}</h4>
          <p style="margin:2px 0;font-size:12px;color:#64748b">{tech_zh}</p>
          <hr style="margin:6px 0">
          <table style="font-size:11px;width:100%">
            <tr><td>产能</td><td><b>{site['capacity']:,} 吨/年</b></td></tr>
            <tr><td>成本区间</td><td style="color:{color}"><b>¥{site['cost_low']} - ¥{site['cost_high']}/kg</b></td></tr>
            <tr><td>平均成本</td><td style="color:{color}"><b>¥{site['cost_avg']}/kg</b></td></tr>
          </table>
        </div>
        """

        Marker(
            location=[lat, lon],
            popup=Popup(popup_html, max_width=280),
            icon=folium.Icon(color="darkgreen" if "电解" in tech else "blue" if "CCS" in tech else "orange", icon="industry", prefix="fa"),
        ).add_to(m)

        # Label
        folium.map.Marker(
            location=[lat + 0.12, lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:12px;font-weight:700;color:#0f172a;background:rgba(255,255,255,0.85);padding:2px 8px;border-radius:4px;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,0.1)">{site["name"]}<br><span style="font-size:9px;color:{color}">{tech_zh}</span></div>'
            ),
        ).add_to(m)

    return m


def render():
    lang = st.session_state.get("lang", "zh")
    render_header()

    sites = load_sites()

    # ── Controls ──
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        show_radius = st.checkbox("显示 200km 辐射圈", value=True)
    with c2:
        site_names = ["全部基地"] + [s["name"] for s in sites]
        selected_name = st.selectbox("聚焦基地", site_names, index=0)
    with c3:
        st.caption("点击地图标记查看详情")

    selected_site = next((s for s in sites if s["name"] == selected_name), None)

    # ── Map ──
    m = build_map(sites, show_radius=show_radius, selected_site=selected_site)
    if selected_site:
        m.location = [selected_site["lat"], selected_site["lon"]]
        m.zoom_start = 8

    st_folium(m, width="100%", height=550, returned_objects=[])

    # ── Site Cards ──
    st.markdown("---")
    st.subheader("基地详情")

    cols = st.columns(len(sites))
    for col, site in zip(cols, sites):
        tech = site["tech"]
        color = COLORS.get(tech, "#64748b")
        tech_zh = TECH_ZH.get(tech, tech)
        with col:
            st.markdown(f"""
            <div class="site-card">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                <span style="width:10px;height:10px;border-radius:50%;background:{color};display:inline-block"></span>
                <h4 style="margin:0">{site["name"]}</h4>
              </div>
              <p>{site['province']} · {tech_zh}</p>
              <p>产能 <b>{site['capacity']:,} t/y</b></p>
              <p>成本 <b style="color:{color}">¥{site['cost_low']}-¥{site['cost_high']}/kg</b></p>
              <p>平均 <b style="color:{color}">¥{site['cost_avg']}/kg</b></p>
            </div>
            """, unsafe_allow_html=True)

    # ── Coverage Stats ──
    st.markdown("---")
    st.subheader("200km 覆盖统计")

    stats_cols = st.columns(len(sites))
    for col, site in zip(stats_cols, sites):
        lat, lon = site["lat"], site["lon"]
        # Count other sites within 200km
        nearby = [s for s in sites if s["name"] != site["name"] and haversine_km(lat, lon, s["lat"], s["lon"]) <= 200]
        with col:
            st.metric(
                f"{site['name']}",
                f"{len(nearby)} 个基地",
                delta="相邻基地" if nearby else "独立覆盖",
            )
            if nearby:
                st.caption("覆盖相邻: " + ", ".join(s["name"] for s in nearby))
