"""P1 核心：生产基地地图 — Folium 交互地图 + 四基地标注 + 200km 辐射圈"""
import streamlit as st
import folium
from folium import Circle, Popup
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from utils.data_loader import load_sites
from utils.geo_utils import haversine_km
from utils.ui import render_header
from config.constants import TECH_COLORS, TECH_ZH, TILE_OPTIONS, DEFAULT_COLOR, ECONOMIC_RADIUS_KM


def _fmt_site_popup(site: dict, color: str) -> str:
    """Build HTML popup for a production site marker."""
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
    """Map tech route to Folium icon (color, icon_name)."""
    if "电解" in tech:
        return "darkgreen", "industry"
    if "CCS" in tech:
        return "blue", "industry"
    if "副产" in tech:
        return "orange", "industry"
    return "gray", "industry"


def build_map(sites: list[dict], show_radius: bool = True,
              selected_site: dict | None = None, tile_key: str = "高德地图（推荐）") -> folium.Map:
    """Build Folium map with site markers, 200km radius circles, and legend."""

    tile_cfg = TILE_OPTIONS.get(tile_key, TILE_OPTIONS["高德地图（推荐）"])

    # Build tile layer
    if "subdomains" in tile_cfg:
        tiles = tile_cfg["url"]
        attr = tile_cfg.get("attr", "")
    else:
        tiles = tile_cfg["url"]
        attr = tile_cfg.get("attr", tiles)

    center_lat = selected_site["lat"] if selected_site else 37.5
    center_lon = selected_site["lon"] if selected_site else 110.0
    zoom = 8 if selected_site else 5

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles=tiles,
        attr=attr,
        control_scale=True,
    )
    Fullscreen().add_to(m)

    for site in sites:
        lat, lon = site["lat"], site["lon"]
        tech = site["tech"]
        color = TECH_COLORS.get(tech, DEFAULT_COLOR)
        is_sel = selected_site and selected_site["name"] == site["name"]

        # 200km radius
        if show_radius:
            Circle(
                location=[lat, lon],
                radius=ECONOMIC_RADIUS_KM * 1000,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.07 if is_sel else 0.04,
                weight=2 if is_sel else 1,
                opacity=0.6 if is_sel else 0.25,
                dash_array=None if is_sel else "6 5",
                popup=folium.Popup(f"<b>{site['name']}</b> {ECONOMIC_RADIUS_KM}km 经济辐射圈", max_width=200),
            ).add_to(m)

        # Marker
        icon_color, icon_name = _get_folium_icon(tech)
        folium.Marker(
            location=[lat, lon],
            popup=Popup(_fmt_site_popup(site, color), max_width=300),
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa"),
        ).add_to(m)

        # Text label
        folium.map.Marker(
            location=[lat + 0.10, lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:11px;font-weight:700;color:#0f172a;background:rgba(255,255,255,0.88);padding:2px 7px;border-radius:3px;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,0.08);border-left:3px solid {color}">{site["name"]}<br><span style="font-size:8px;color:#64748b">{TECH_ZH.get(tech, tech)} · ¥{site["cost_avg"]}/kg</span></div>'
            ),
        ).add_to(m)

    # Legend
    legend_html = '<div style="position:fixed;bottom:22px;right:22px;z-index:9999;background:rgba(255,255,255,0.92);padding:10px 14px;border-radius:8px;font-size:11px;box-shadow:0 2px 12px rgba(0,0,0,0.08);line-height:1.8">'
    legend_html += '<b style="font-size:12px">图例</b><br>'
    for tech, color in TECH_COLORS.items():
        legend_html += f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{color};margin-right:4px"></span> {TECH_ZH.get(tech, tech)}<br>'
    legend_html += f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;border:1.5px solid #94a3b8;margin-right:4px"></span> {ECONOMIC_RADIUS_KM}km 辐射圈'
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def _build_site_card(site: dict) -> str:
    """Build HTML for a site info card."""
    tech = site["tech"]
    color = TECH_COLORS.get(tech, DEFAULT_COLOR)
    tech_zh = TECH_ZH.get(tech, tech)
    cert = site.get("cert_status", "—")
    util = site.get("utilization", "—")
    return f"""
    <div class="site-card" style="margin-bottom:10px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
        <span style="width:10px;height:10px;border-radius:50%;background:{color};display:inline-block;flex-shrink:0"></span>
        <strong style="color:#0f172a;font-size:15px">{site['name']}</strong>
        <span style="color:#64748b;font-size:11px">{site['province']}</span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;font-size:12px;color:#475569">
        <div>技术: <b>{tech_zh}</b></div>
        <div>产能: <b>{site['capacity']:,} t/y</b></div>
        <div>成本: <b style="color:{color}">¥{site['cost_avg']}/kg</b></div>
        <div>利用率: <b>{util}%</b></div>
        <div style="grid-column:1/-1">认证: {cert}</div>
      </div>
    </div>"""


def render():
    lang = st.session_state.get("lang", "zh")
    render_header()

    sites = load_sites()
    if not sites:
        st.warning("未加载到基地数据，请先在数据管理中录入。")
        return

    # ── Session state init ──
    if "map_selected_idx" not in st.session_state:
        st.session_state.map_selected_idx = 0
    if "map_show_radius" not in st.session_state:
        st.session_state.map_show_radius = True
    if "map_tile_key" not in st.session_state:
        st.session_state.map_tile_key = "高德地图（推荐）"

    # ── Top control bar ──
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        st.session_state.map_show_radius = st.checkbox(
            f"显示 {ECONOMIC_RADIUS_KM}km 辐射圈",
            value=st.session_state.map_show_radius,
        )
    with c2:
        tile_keys = list(TILE_OPTIONS.keys())
        current_tile_idx = tile_keys.index(st.session_state.map_tile_key) if st.session_state.map_tile_key in tile_keys else 0
        st.session_state.map_tile_key = st.selectbox(
            "地图底图", tile_keys, index=current_tile_idx,
        )
    with c3:
        site_names = ["全部基地"] + [s["name"] for s in sites]
        new_idx = st.selectbox(
            "聚焦基地", range(len(site_names)),
            index=st.session_state.map_selected_idx,
            format_func=lambda i: site_names[i],
        )
        st.session_state.map_selected_idx = new_idx
    with c4:
        st.caption("💡 点击标记查看详情")
        st.caption(f"📅 数据更新: {sites[0].get('updated_at', '—')[:16] if sites else '—'}")

    selected_site = sites[st.session_state.map_selected_idx - 1] if st.session_state.map_selected_idx > 0 else None

    # ── Main layout: map (65%) | side cards (35%) ──
    map_col, info_col = st.columns([0.65, 0.35])

    with map_col:
        with st.spinner("加载地图..."):
            m = build_map(
                sites,
                show_radius=st.session_state.map_show_radius,
                selected_site=selected_site,
                tile_key=st.session_state.map_tile_key,
            )
        st_folium(m, width="100%", height=580, returned_objects=[])

    with info_col:
        st.markdown("**📋 基地详情**")
        if selected_site:
            st.info(f"📍 当前聚焦: **{selected_site['name']}**")
        for site in sites:
            st.markdown(_build_site_card(site), unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**📏 覆盖统计**")
        for site in sites:
            lat, lon = site["lat"], site["lon"]
            nearby = [s for s in sites if s["name"] != site["name"]
                      and haversine_km(lat, lon, s["lat"], s["lon"]) <= ECONOMIC_RADIUS_KM]
            if nearby:
                st.caption(f"🔗 {site['name']} ↔ {', '.join(s['name'] for s in nearby)} ({ECONOMIC_RADIUS_KM}km内)")
            else:
                st.caption(f"📍 {site['name']}: 独立覆盖区")
