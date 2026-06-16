"""生产基地地图 — Folium + Plotly · Platts风格"""
import streamlit as st
import folium
import plotly.graph_objects as go
import pandas as pd
from folium import Circle, Popup, Tooltip
from folium.plugins import Fullscreen, MeasureControl
from streamlit_folium import st_folium
from utils.data_loader import load_sites, load_competitors
from utils.geo_utils import haversine_km
from utils.ui import render_module_header
from config.constants import TECH_COLORS, TECH_ZH, TILE_OPTIONS, DEFAULT_COLOR, ECONOMIC_RADIUS_KM

COMPETITOR_STATUS_COLORS = {"已投产": "#ef4444", "在建": "#d97706", "规划": "#94a3b8"}


def _fmt_site_popup(site: dict, color: str) -> str:
    tech_zh = TECH_ZH.get(site["tech"], site["tech"])
    cert = site.get("cert_status", "—")
    util = site.get("utilization", "—")
    return f"""
    <div style="font-family:-apple-system,sans-serif;min-width:210px">
      <h4 style="margin:0 0 2px;color:{color};font-size:14px">{site['name']} · {site['province']}</h4>
      <p style="margin:2px 0;font-size:10px;color:#64748b">{tech_zh}</p>
      <hr style="margin:6px 0;border-color:#e5e7eb">
      <table style="font-size:10px;width:100%;line-height:1.6">
        <tr><td style="color:#64748b">产能</td><td><b>{site['capacity']:,} t/y</b></td></tr>
        <tr><td style="color:#64748b">利用率</td><td><b>{util}%</b></td></tr>
        <tr><td style="color:#64748b">成本</td><td style="color:{color}"><b>¥{site['cost_low']}–¥{site['cost_high']}/kg</b></td></tr>
        <tr><td style="color:#64748b">认证</td><td>{cert}</td></tr>
      </table>
    </div>"""


import json

@st.cache_resource(show_spinner=False)
def _cached_build_map(sites_json: str, show_radius: bool, selected_name: str,
                      tile_key: str, show_competitors: bool, competitors_json: str):
    """Cached Folium map builder — only rebuilds when params change."""
    sites = json.loads(sites_json)
    competitors = json.loads(competitors_json) if competitors_json else []
    selected_site = next((s for s in sites if s["name"] == selected_name), None) if selected_name else None
    return _build_map_impl(sites, show_radius, selected_site, tile_key, show_competitors, competitors)


def _build_map_impl(sites, show_radius=True, selected_site=None, tile_key="高德地图（推荐）",
                    show_competitors=False, competitors=None):
    tile_cfg = TILE_OPTIONS.get(tile_key, TILE_OPTIONS["高德地图（推荐）"])
    tiles, attr = tile_cfg["url"], tile_cfg.get("attr", "")
    clat = selected_site["lat"] if selected_site else 37.5
    clon = selected_site["lon"] if selected_site else 110.0

    m = folium.Map(location=[clat, clon], zoom_start=9 if selected_site else 5,
                   tiles=tiles, attr=attr, control_scale=True)
    Fullscreen().add_to(m)
    MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(m)

    for site in sites:
        lat, lon, tech = site["lat"], site["lon"], site["tech"]
        color = TECH_COLORS.get(tech, DEFAULT_COLOR)
        is_sel = selected_site and selected_site["name"] == site["name"]

        if show_radius:
            # Concentric rings at 50/100/150/200km — shows transport cost gradient
            # Transport cost: ¥10 per 100km
            rings = [
                (50,  0.16, 1.2, 0.70, "¥5/kg"),
                (100, 0.10, 1.0, 0.45, "¥10/kg"),
                (150, 0.06, 0.7, 0.28, "¥15/kg"),
                (200, 0.03, 0.5, 0.14, "¥20/kg"),
            ]
            if is_sel:
                rings = [(r, fo + 0.06, w + 0.6, op + 0.2, lbl) for r, fo, w, op, lbl in rings]

            for radius_km, fill_op, weight, opacity, label in rings:
                Circle(
                    location=[lat, lon],
                    radius=radius_km * 1000,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=fill_op,
                    weight=weight,
                    opacity=opacity,
                    dash_array=None,
                    popup=folium.Popup(
                        f"<b>{site['name']}</b><br>{radius_km}km 半径<br>运输成本 {label}",
                        max_width=180,
                    ),
                ).add_to(m)

        ico = "darkgreen" if "电解" in tech else "blue" if "CCS" in tech else "orange"
        folium.Marker(
            location=[lat, lon],
            popup=Popup(_fmt_site_popup(site, color), max_width=280),
            tooltip=Tooltip(f"{site['name']} · ¥{site['cost_avg']}/kg"),
            icon=folium.Icon(color=ico, icon="industry", prefix="fa"),
        ).add_to(m)
        folium.map.Marker(
            location=[lat + 0.10, lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:{"12px" if is_sel else "10px"};font-weight:{"700" if is_sel else "600"};color:#1e293b;background:rgba(255,255,255,0.9);padding:2px 6px;border-radius:3px;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,0.08);border-left:3px solid {color}">{site["name"]}<br><span style="font-size:7px;color:#64748b">¥{site["cost_avg"]}</span></div>'),
        ).add_to(m)

    if show_competitors and competitors:
        for comp in competitors:
            c_lat, c_lon = comp["lat"], comp["lon"]
            c_color = COMPETITOR_STATUS_COLORS.get(comp.get("status", ""), "#94a3b8")
            ico_c = "red" if comp.get("status") == "已投产" else "orange" if comp.get("status") == "在建" else "gray"
            ico_n = "exclamation-triangle" if comp.get("status") == "已投产" else "clock-o" if comp.get("status") == "在建" else "question"
            comp_popup = f"""
            <div style="font-family:-apple-system,sans-serif;min-width:180px">
              <h4 style="margin:0;color:{c_color};font-size:13px">⚠️ {comp['name']}</h4>
              <p style="font-size:10px;color:#64748b;margin:2px 0">{comp.get('province','')} · {comp.get('tech','')}</p>
              <hr style="margin:4px 0;border-color:#e5e7eb">
              <table style="font-size:10px;width:100%;line-height:1.5">
                <tr><td style="color:#64748b">产能</td><td><b>{comp.get('capacity',0):,} t/y</b></td></tr>
                <tr><td style="color:#64748b">估成本</td><td><b>¥{comp.get('cost_est',0)}/kg</b></td></tr>
                <tr><td style="color:#64748b">状态</td><td style="color:{c_color}"><b>{comp.get('status','')}</b></td></tr>
              </table>
            </div>"""
            folium.Marker(location=[c_lat, c_lon],
                          icon=folium.Icon(color=ico_c, icon=ico_n, prefix="fa"),
                          popup=folium.Popup(comp_popup, max_width=260),
                          tooltip=folium.Tooltip(f"⚠️ {comp['name']} · {comp.get('status','')}")).add_to(m)

    # Legend
    legend_rows = "".join(f'<tr><td><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:{c}"></span></td><td style="font-size:10px;color:#334155">{TECH_ZH.get(t,t)}</td></tr>' for t, c in TECH_COLORS.items())
    legend_html = f"""<div style="position:fixed;bottom:18px;right:18px;z-index:9999;background:rgba(255,255,255,0.95);padding:8px 12px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.08);line-height:1.6">
      <b style="font-size:11px;color:#1e293b">图例</b><table style="margin-top:3px">{legend_rows}
      <tr><td colspan="2" style="font-size:9px;color:#94a3b8;padding-top:3px">运输成本梯度</td></tr>
      <tr><td><span style="display:inline-block;width:14px;height:14px;border-radius:50%;background:rgba(100,100,100,0.3)"></span></td><td style="font-size:10px;color:#334155">50km ¥5</td></tr>
      <tr><td><span style="display:inline-block;width:18px;height:18px;border-radius:50%;background:rgba(100,100,100,0.15)"></span></td><td style="font-size:10px;color:#334155">100km ¥10</td></tr>
      <tr><td><span style="display:inline-block;width:22px;height:22px;border-radius:50%;background:rgba(100,100,100,0.08)"></span></td><td style="font-size:10px;color:#334155">150km ¥15</td></tr>
      <tr><td><span style="display:inline-block;width:26px;height:26px;border-radius:50%;border:1px solid #94a3b8"></span></td><td style="font-size:10px;color:#334155">200km ¥20</td></tr></table></div>"""
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


@st.cache_data(show_spinner=False, ttl=300)
def _cost_comparison_chart(sites_json: str):
    sites = json.loads(sites_json)
    df = pd.DataFrame(sites)
    df["tech_zh"] = df["tech"].map(TECH_ZH)
    df = df.sort_values("cost_avg")
    fig = go.Figure()
    for _, row in df.iterrows():
        color = TECH_COLORS.get(row["tech"], DEFAULT_COLOR)
        fig.add_trace(go.Bar(name=row["name"], x=[row["name"]], y=[row["cost_high"] - row["cost_low"]],
                             base=[row["cost_low"]], marker_color=color, marker_opacity=0.3, width=0.45,
                             text=f"¥{row['cost_low']}–¥{row['cost_high']}", textposition="outside",
                             textfont=dict(size=10, color="#64748b"),
                             hovertemplate=f"<b>{row['name']}</b><br>¥{row['cost_low']}–¥{row['cost_high']}/kg<extra></extra>", showlegend=False))
    fig.add_trace(go.Scatter(x=df["name"], y=df["cost_avg"], mode="markers+text",
                             marker=dict(symbol="diamond", size=12, color="#fff", line=dict(color="#1e293b", width=2)),
                             text=[f"¥{v}" for v in df["cost_avg"]], textposition="middle left",
                             textfont=dict(size=11, color="#1e293b"), name="平均", hovertemplate="%{text}/kg<extra></extra>"))
    fig.update_layout(
        height=280, margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_family="-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif",
        legend=dict(orientation="h", y=1.1, font=dict(size=11, color="#64748b")),
        xaxis=dict(tickfont=dict(size=11, color="#64748b"), gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(title="¥/kg", titlefont=dict(size=10, color="#94a3b8"), tickfont=dict(size=10, color="#64748b"), gridcolor="rgba(0,0,0,0.04)"),
    )
    return fig


def render():
    render_module_header("基地地图", "四大制氢基地 · 200km 经济辐射圈 · 竞品对标 · 成本分析", badge="MAP")

    sites = load_sites()
    competitors = load_competitors()
    if not sites:
        st.warning("⚠️ 未加载到基地数据，请先在「数据管理」中录入。")
        if st.button("前往数据管理 →", type="primary"):
            st.session_state.page = "data"; st.rerun()
        return

    for k in ["map_selected_idx", "map_show_radius", "map_tile_key"]:
        if k not in st.session_state: st.session_state[k] = 0 if k == "map_selected_idx" else True if k == "map_show_radius" else "高德地图（推荐）"

    c1, c2, c3, c4, c5 = st.columns([1.4, 0.9, 1, 0.8, 1.2])
    with c1:
        st.session_state.map_show_radius = st.checkbox(f"显示 50/100/150/200km 运输成本圈", value=st.session_state.map_show_radius)
    with c2:
        show_comp = st.checkbox("显示竞品", value=st.session_state.get("map_show_competitors", False))
        st.session_state.map_show_competitors = show_comp
    with c3:
        tile_keys = list(TILE_OPTIONS.keys())
        cur_t = tile_keys.index(st.session_state.map_tile_key) if st.session_state.map_tile_key in tile_keys else 0
        st.session_state.map_tile_key = st.selectbox("底图", tile_keys, index=cur_t)
    with c4:
        names = ["全部"] + [s["name"] for s in sites]
        st.session_state.map_selected_idx = st.selectbox("聚焦", range(len(names)), index=st.session_state.map_selected_idx, format_func=lambda i: names[i])
    with c5:
        ts = sites[0].get("updated_at", "—")[:10] if sites else "—"
        st.caption(f"💡 点击标记查看详情")
        st.caption(f"📅 更新: {ts}")

    sel = sites[st.session_state.map_selected_idx - 1] if st.session_state.map_selected_idx > 0 else None

    map_col, info_col = st.columns([0.64, 0.36])
    with map_col:
        with st.spinner("加载地图..."):
            m = _cached_build_map(
                json.dumps(sites, ensure_ascii=False, sort_keys=True),
                st.session_state.map_show_radius,
                sel["name"] if sel else "",
                st.session_state.map_tile_key,
                show_comp,
                json.dumps(competitors, ensure_ascii=False, sort_keys=True) if competitors else "",
            )
        st_folium(m, width="100%", height=560, returned_objects=[])

    with info_col:
        st.markdown('<p style="font-size:10px;color:var(--slate-400);text-transform:uppercase;letter-spacing:0.5px;font-weight:600;margin-bottom:4px">基地详情</p>', unsafe_allow_html=True)
        if sel:
            st.info(f"📍 聚焦: **{sel['name']}** · {TECH_ZH.get(sel['tech'], sel['tech'])}")
        for site in sites:
            tech = site["tech"]
            color = TECH_COLORS.get(tech, DEFAULT_COLOR)
            util = site.get("utilization", "—")
            st.markdown(f"""
            <div class="info-card" style="border-left-color:{color}">
              <div class="ic-title">{site['name']} <span style="font-size:10px;color:var(--slate-400);font-weight:400">{site['province']}</span></div>
              <div class="ic-row"><span>产能 <b>{site['capacity']:,}t</b></span><span>成本 <b style="color:{color}">¥{site['cost_avg']}</b></span><span>利用率 <b>{util}%</b></span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<p style="font-size:10px;color:var(--slate-400);text-transform:uppercase;letter-spacing:0.5px;font-weight:600;margin:12px 0 4px">距离测量</p>', unsafe_allow_html=True)
        sn = [s["name"] for s in sites]
        da = st.selectbox("起点", range(len(sites)), format_func=lambda i: sn[i], key="da")
        db = st.selectbox("终点", range(len(sites)), format_func=lambda i: sn[i], index=min(1, len(sites)-1), key="db")
        if da != db:
            d = haversine_km(sites[da]["lat"], sites[da]["lon"], sites[db]["lat"], sites[db]["lon"])
            st.info(f"{'✅' if d <= ECONOMIC_RADIUS_KM else '⚠️'} **{d:.0f} km** {'— 辐射半径内' if d <= ECONOMIC_RADIUS_KM else '— 超出辐射半径'}")

    st.markdown("---")
    st.subheader("📊 成本对比分析")
    st.plotly_chart(_cost_comparison_chart(json.dumps(sites, ensure_ascii=False, sort_keys=True)), width="stretch")

    if competitors:
        st.markdown("---")
        st.subheader("⚔️ 成本对标：国华 vs 竞品")
        comp_rows = []
        for s in sites:
            comp_rows.append({"类型": "🏭 国华", "名称": s["name"], "省份": s["province"],
                               "技术": TECH_ZH.get(s["tech"], s["tech"]), "产能(t/y)": s["capacity"],
                               "成本(¥/kg)": s["cost_avg"], "状态": "运营中"})
        for c in competitors:
            comp_rows.append({"类型": "⚠️ 竞品", "名称": c["name"], "省份": c.get("province", ""),
                               "技术": c.get("tech", ""), "产能(t/y)": c.get("capacity", 0),
                               "成本(¥/kg)": c.get("cost_est", 0), "状态": c.get("status", "")})
        dfc = pd.DataFrame(comp_rows).sort_values("成本(¥/kg)")
        st.dataframe(dfc, width="stretch", hide_index=True,
                     column_config={"成本(¥/kg)": st.column_config.NumberColumn(format="¥%.1f")})

        # Scatter
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=[s["cost_avg"] for s in sites], y=[s["capacity"] for s in sites],
                                   mode="markers+text", text=[s["name"] for s in sites], textposition="top center",
                                   marker=dict(size=16, color="#00a99d", symbol="diamond", line=dict(color="#1e293b", width=1)),
                                   name="国华"))
        fig2.add_trace(go.Scatter(x=[c["cost_est"] for c in competitors], y=[c.get("capacity",0) for c in competitors],
                                   mode="markers+text", text=[c["name"] for c in competitors], textposition="top center",
                                   marker=dict(size=12, color="#ef4444", symbol="x-thin", line=dict(color="#ef4444", width=1.5)),
                                   name="竞品"))
        fig2.update_layout(
        title=dict(text="成本 vs 产能 竞争格局", font=dict(size=15, color="#0f172a")),
        height=340, xaxis=dict(title="成本 (¥/kg)", gridcolor="rgba(0,0,0,0.04)", titlefont=dict(size=10, color="#94a3b8")),
        yaxis=dict(title="产能 (t/y)", gridcolor="rgba(0,0,0,0.04)", titlefont=dict(size=10, color="#94a3b8")),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_family="-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif",
        legend=dict(orientation="h", y=1.1, font=dict(size=11, color="#64748b")),
    )
        st.plotly_chart(fig2, width="stretch")
