"""首页总览 — 动态KPI + 平台信息"""
import streamlit as st
from utils.data_loader import load_sites, get_updated_time
from utils.ui import render_header
from config.constants import ECONOMIC_RADIUS_KM


def _kpi_card(icon: str, value: str, label: str, accent: str = "#0f766e"):
    return f"""
    <div class="metric-card" style="border-top:3px solid {accent}">
      <div style="font-size:26px;margin-bottom:4px">{icon}</div>
      <div class="val" style="color:{accent}">{value}</div>
      <div class="lbl">{label}</div>
    </div>"""


def render():
    lang = st.session_state.get("lang", "zh")
    render_header()

    sites = load_sites()
    total_capacity = sum(s.get("capacity", 0) for s in sites)
    avg_cost = sum(s.get("cost_avg", 0) for s in sites) / len(sites) if sites else 0
    avg_util = sum(s.get("utilization", 0) for s in sites) / len(sites) if sites else 0
    updated = get_updated_time()

    # ── KPI Row ──
    cols = st.columns(4)
    kpis = [
        ("🏭", str(len(sites)), "制氢基地" if lang == "zh" else "Production Bases", "#0f766e"),
        ("⚡", f"{total_capacity:,}", "总产能 (吨/年)" if lang == "zh" else "Total Capacity (t/y)", "#0284c7"),
        ("💰", f"¥{avg_cost:.1f}", "平均成本 (/kg)" if lang == "zh" else "Avg Cost (/kg)", "#d97706"),
        ("📈", f"{avg_util:.0f}%", "平均利用率" if lang == "zh" else "Avg Utilization", "#7c3aed"),
    ]
    for col, (icon, val, lbl, accent) in zip(cols, kpis):
        with col:
            st.markdown(_kpi_card(icon, val, lbl, accent), unsafe_allow_html=True)

    st.markdown("---")

    # ── Platform Info + Quick Nav ──
    c1, c2 = st.columns([0.55, 0.45])

    with c1:
        st.subheader("🌱 平台介绍")
        st.markdown(f"""
        本平台服务于**国家能源集团国内氢能销售业务**，以四大制氢基地（赤城·宁东·沧州·如东）为核心，
        绘制 **{ECONOMIC_RADIUS_KM}km 经济辐射圈**，整合供给端生产成本数据，
        为销售团队提供供需匹配和定价决策支持。

        **当前阶段**：P1 搭框架 ✅
        **下一步**：P2 供给端深化 + 需求端（加氢站数据）接入
        """)

        st.markdown("---")
        st.subheader("📋 平台功能模块")
        modules = [
            ("🗺️", "基地地图", "Folium 交互地图 · 四大基地标注 · 200km辐射圈 · 成本区间展示", "已完成"),
            ("📊", "数据管理", "Excel 批量导入 · 在线编辑 · 数据校验 · 版本记录", "已完成"),
            ("🔗", "供需匹配（P3）", "产地→需求区最优匹配 · 运输成本计算 · 到站价格推导", "待开发"),
            ("💲", "定价决策（P3）", "区域氢价对标 · 成本优势热力图 · 毛利测算", "待开发"),
            ("📈", "市场监测（P4）", "政策跟踪 · 竞品分析 · FCV销量趋势 · 周报自动生成", "待开发"),
        ]
        for icon, name, desc, status in modules:
            color = "#10b981" if status == "已完成" else "#94a3b8"
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:12px;padding:10px 0;
            border-bottom:1px solid rgba(15,23,42,0.04)">
              <span style="font-size:20px;flex-shrink:0;margin-top:2px">{icon}</span>
              <div style="flex:1">
                <div style="display:flex;align-items:center;gap:8px">
                  <strong>{name}</strong>
                  <span style="font-size:10px;padding:1px 6px;border-radius:10px;color:{color};background:{color}15">{status}</span>
                </div>
                <span style="color:#64748b;font-size:0.82rem">{desc}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

    with c2:
        st.subheader("🚀 快速入口")
        if st.button("🗺️ 基地地图 →", width="stretch", type="primary"):
            st.session_state.page = "map"
            st.rerun()
        if st.button("📊 数据管理 →", width="stretch"):
            st.session_state.page = "data"
            st.rerun()

        st.markdown("---")
        st.subheader("📌 基地概览")
        for site in sites:
            tech_color = {"风电+光伏电解": "#10b981", "风电电解": "#10b981",
                          "光伏电解": "#0284c7", "煤制氢+CCS": "#0284c7",
                          "工业副产氢": "#d97706"}.get(site.get("tech", ""), "#64748b")
            st.markdown(f"""
            <div style="padding:10px 14px;margin-bottom:8px;background:#fff;
            border:1px solid rgba(15,23,42,0.05);border-left:3px solid {tech_color};
            border-radius:6px">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <strong>{site['name']}</strong>
                <span style="font-size:11px;color:#64748b">{site.get('province', '')}</span>
              </div>
              <div style="font-size:12px;color:#475569;margin-top:4px">
                产能 {site.get('capacity', 0):,}t · ¥{site.get('cost_avg', 0)}/kg · {site.get('cert_status', '—')}
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.caption(f"📅 数据更新: {updated[:16] if updated else '—'}")

    st.markdown("---")
    st.caption("P1 · 搭框架阶段 · 基于 Streamlit + Folium + Pandas")
