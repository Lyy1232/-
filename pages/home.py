"""首页总览 — Platts/Argus 风格 Widget 仪表盘"""
import streamlit as st
import pandas as pd
from utils.data_loader import load_sites, load_stations, get_station_stats, get_cluster_stats, get_updated_time
from utils.ui import render_module_header
from config.constants import ECONOMIC_RADIUS_KM, GUOHUA_BASES_COST, REFERENCE_DATA


def _metric_card(icon: str, value: str, label: str, sub: str = "", delta: str = "", delta_up: bool = True,
                 accent: str = "#00a99d"):
    delta_html = ""
    if delta:
        cls = "up" if delta_up else "down"
        arrow = "↑" if delta_up else "↓"
        delta_html = f'<div class="mc-delta {cls}">{arrow} {delta}</div>'
    return f"""
    <div class="metric-card">
      <div class="mc-accent-bar" style="background:{accent}"></div>
      <div class="mc-icon">{icon}</div>
      <div class="mc-value" style="margin-top:4px">{value}</div>
      <div class="mc-label">{label}</div>
      {delta_html}
      {f'<div class="mc-sub">{sub}</div>' if sub else ''}
    </div>"""


def render():
    lang = st.session_state.get("lang", "zh")
    render_module_header("业务总览", "四大基地 · 200km辐射圈 · 行业参考数据", badge="LIVE")

    sites = load_sites()
    stations = load_stations()
    stats = get_station_stats(stations)
    clusters = get_cluster_stats(stations)
    updated = get_updated_time()
    total_cap = sum(s.get("capacity", 0) for s in sites)
    avg_cost = sum(s.get("cost_avg", 0) for s in sites) / max(len(sites), 1)
    avg_util = sum(s.get("utilization", 0) for s in sites) / max(len(sites), 1)

    # ═══════ ROW 1: Top-line KPIs ═══════
    st.markdown('<p style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;font-weight:600">核心指标</p>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(_metric_card("🏭", str(len(sites)), "制氢基地",
                                 f"总产能 {total_cap:,} t/y", accent="#00a99d"), unsafe_allow_html=True)
    with c2:
        st.markdown(_metric_card("💰", f"¥{avg_cost:.1f}", "平均成本 /kg",
                                 f"区间 ¥{min(s['cost_low'] for s in sites) if sites else 0}–¥{max(s['cost_high'] for s in sites) if sites else 0}",
                                 accent="#d97706"), unsafe_allow_html=True)
    with c3:
        st.markdown(_metric_card("⛽", str(stats["count"]), "覆盖加氢站",
                                 f"日需求 {stats['total_throughput']:,} kg", accent="#2563eb"), unsafe_allow_html=True)
    with c4:
        st.markdown(_metric_card("📈", f"{avg_util:.0f}%", "平均利用率",
                                 f"产能 {total_cap:,} t/y", delta="目标 85%" if avg_util < 85 else "",
                                 delta_up=avg_util >= 85, accent="#7c3aed"), unsafe_allow_html=True)
    with c5:
        gh_pct = stats["guohua_count"] / max(stats["count"], 1) * 100
        st.markdown(_metric_card("⭐", f"{stats['guohua_count']}/{stats['count']}", "国华供氢站",
                                 f"占比 {gh_pct:.0f}%", accent="#10b981"), unsafe_allow_html=True)

    st.markdown('<div style="margin:20px 0"></div>', unsafe_allow_html=True)

    # ═══════ ROW 2: Cost comparison + Station coverage ═══════
    r2l, r2r = st.columns([0.5, 0.5])

    with r2l:
        st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">基地成本对比</span><span class="dc-badge updated">¥/kg</span></div>', unsafe_allow_html=True)
        for site in sites:
            color = {"风电+光伏电解": "#00a99d", "风电电解": "#00a99d",
                     "光伏电解": "#2563eb", "煤制氢+CCS": "#2563eb",
                     "工业副产氢": "#d97706"}.get(site.get("tech", ""), "#64748b")
            cost_range_pct = (site["cost_high"] - site["cost_low"]) / max(site["cost_avg"], 0.1) * 100
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #f1f5f9">
              <span style="font-weight:700;font-size:13px;width:48px;color:#0f172a">{site['name']}</span>
              <div style="flex:1;height:6px;background:#f1f5f9;border-radius:3px;position:relative">
                <div style="position:absolute;left:{ (site['cost_low']-10)/20*100 }%;width:{ (site['cost_high']-site['cost_low'])/20*100 }%;height:100%;background:{color};border-radius:3px;opacity:0.7"></div>
                <div style="position:absolute;left:{ (site['cost_avg']-10)/20*100 }%;top:-3px;width:12px;height:12px;border-radius:50%;background:#fff;border:2px solid {color}"></div>
              </div>
              <span style="font-size:11px;color:#64748b;width:100px;text-align:right">¥{site['cost_low']}–¥{site['cost_high']}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown('<div style="display:flex;justify-content:space-between;font-size:9px;color:#94a3b8;margin-top:4px;padding:0 48px"><span>¥10</span><span>¥15</span><span>¥20</span><span>¥25</span><span>¥30</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r2r:
        st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">城市群需求分布</span><span class="dc-badge live">⛽</span></div>', unsafe_allow_html=True)
        for c in clusters[:6]:
            pct = c["throughput"] / max(stats["total_throughput"], 1) * 100
            st.markdown(f"""
            <div style="padding:6px 0;border-bottom:1px solid #f1f5f9">
              <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                <span style="font-size:12px;font-weight:600;color:#0f172a">{c['name']}</span>
                <span style="font-size:11px;color:#64748b">{c['count']}站 · {c['throughput']:,} kg/天</span>
              </div>
              <div style="height:5px;background:#f1f5f9;border-radius:3px">
                <div style="width:{pct}%;height:100%;background:#2563eb;border-radius:3px;opacity:0.7"></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin:20px 0"></div>', unsafe_allow_html=True)

    # ═══════ ROW 3: Coverage + Quick nav ═══════
    r3l, r3r = st.columns([0.55, 0.45])

    with r3l:
        st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">200km 辐射圈覆盖概览</span><span class="dc-badge updated">覆盖分析</span></div>', unsafe_allow_html=True)
        from utils.geo_utils import haversine_km
        cov_data = []
        for site in sites:
            cov_count = sum(1 for s in stations if haversine_km(s["lat"], s["lon"], site["lat"], site["lon"]) <= ECONOMIC_RADIUS_KM)
            cov_demand = sum(s.get("actual_throughput_kg", 0) for s in stations
                           if haversine_km(s["lat"], s["lon"], site["lat"], site["lon"]) <= ECONOMIC_RADIUS_KM)
            cov_data.append({"基地": site["name"], "覆盖站数": cov_count, "日需求(kg)": cov_demand,
                             "供给能力(t/天)": round(site["capacity"] / 365, 1)})
        df_cov = pd.DataFrame(cov_data)
        # Display as styled HTML
        rows_html = ""
        for _, r in df_cov.iterrows():
            sufficiency = "充足" if r["供给能力(t/天)"] * 1000 > r["日需求(kg)"] else "不足"
            s_color = "#10b981" if sufficiency == "充足" else "#ef4444"
            rows_html += f"""
            <tr>
              <td style="font-weight:600;color:#0f172a">{r['基地']}</td>
              <td>{r['覆盖站数']} 站</td>
              <td>{r['日需求(kg)']:,} kg</td>
              <td>{r['供给能力(t/天)']} t/天</td>
              <td><span style="color:{s_color};font-weight:600">{sufficiency}</span></td>
            </tr>"""
        st.markdown(f"""
        <table style="width:100%;font-size:12px;border-collapse:collapse">
          <thead><tr style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:0.5px">
            <th style="text-align:left;padding:8px;border-bottom:2px solid #e2e8f0">基地</th>
            <th style="text-align:left;padding:8px;border-bottom:2px solid #e2e8f0">覆盖</th>
            <th style="text-align:left;padding:8px;border-bottom:2px solid #e2e8f0">日需求</th>
            <th style="text-align:left;padding:8px;border-bottom:2px solid #e2e8f0">供给能力</th>
            <th style="text-align:left;padding:8px;border-bottom:2px solid #e2e8f0">状态</th>
          </tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r3r:
        st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">快速入口</span></div>', unsafe_allow_html=True)
        nav_items = [
            ("🗺️", "基地地图", "查看四大基地位置与竞品对标", "map"),
            ("⛽", "加氢站网络", "分析覆盖范围与市场机会", "stations"),
            ("⚙️", "数据管理", "更新基地与加氢站数据", "data"),
        ]
        for icon, title, desc, target in nav_items:
            st.markdown(f"""
            <div style="padding:10px 0;border-bottom:1px solid #f1f5f9;
            display:flex;align-items:center;gap:12px;cursor:pointer"
            onclick="document.getElementById('dummy').click()">
              <span style="font-size:22px">{icon}</span>
              <div style="flex:1"><div style="font-weight:600;font-size:13px;color:#0f172a">{title}</div>
              <div style="font-size:11px;color:#64748b">{desc}</div></div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"进入 {title} →", key=f"qnav_{target}", width="stretch"):
                st.session_state.page = target
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin:20px 0"></div>', unsafe_allow_html=True)

    # ═══════ ROW 4: Site cards + Status ═══════
    r4l, r4r = st.columns([0.6, 0.4])
    with r4l:
        st.markdown('<p style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;font-weight:600">基地状态</p>', unsafe_allow_html=True)
        site_cols = st.columns(len(sites))
        for col, site in zip(site_cols, sites):
            tech_color = {"风电+光伏电解": "#00a99d", "风电电解": "#00a99d",
                          "光伏电解": "#2563eb", "煤制氢+CCS": "#2563eb",
                          "工业副产氢": "#d97706"}.get(site.get("tech", ""), "#64748b")
            util_color = "#10b981" if site.get("utilization", 0) >= 70 else "#d97706" if site.get("utilization", 0) >= 50 else "#ef4444"
            with col:
                st.markdown(f"""
                <div class="info-card" style="border-left-color:{tech_color}">
                  <div class="ic-title">{site['name']} <span style="font-size:10px;color:#94a3b8;font-weight:400">{site['province']}</span></div>
                  <div class="ic-row">
                    <span>产能 <b>{site['capacity']:,}t</b></span>
                    <span>成本 <b>¥{site['cost_avg']}</b></span>
                  </div>
                  <div class="ic-row" style="margin-top:2px">
                    <span>利用率 <b style="color:{util_color}">{site.get('utilization','—')}%</b></span>
                    <span>{site.get('cert_status','—')}</span>
                  </div>
                </div>""", unsafe_allow_html=True)

    with r4r:
        st.markdown('<p style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;font-weight:600">数据状态</p>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="data-card">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
            <span style="width:8px;height:8px;border-radius:50%;background:#10b981"></span>
            <span style="font-weight:600;font-size:13px">平台运行中</span>
          </div>
          <div style="font-size:12px;color:#334155;line-height:1.8">
            <div>🏭 基地数据: <b>{len(sites)} 个</b></div>
            <div>⛽ 加氢站: <b>{stats['count']} 座</b></div>
            <div>⚠️ 竞品项目: <b>7 个</b></div>
            <div>📅 最后更新: <b>{updated[:10] if updated else '—'}</b></div>
            <div>🔗 部署: <b>Streamlit Cloud</b></div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.caption("P1 ✅ · P2 ✅ · P3 ✅ · P4 成本竞争力+聚焦 ✅")

    # ── 行业参考数据 ──
    with st.expander("📚 行业参考数据（Argus/BNEF/公开报告）", expanded=False):
        ref_tbl = [{"指标": k, "数值": v["value"], "来源": v["source"]} for k, v in REFERENCE_DATA.items()]
        st.dataframe(pd.DataFrame(ref_tbl), use_container_width=True, hide_index=True,
                    column_config={"来源": st.column_config.TextColumn(width="large")})
        st.caption("💡 数据来源：中国产业发展促进会氢能分会、全国碳市场、国家能源局、隆众资讯、ICE、IEA等。标注时间为公开值，实际以最新行情为准。")
