"""首页总览"""
import streamlit as st
from utils.ui import render_header


def render():
    lang = st.session_state.get("lang", "zh")
    render_header()

    # KPI Row
    cols = st.columns(4)
    metrics = [
        ("🏭", "4", "制氢基地" if lang == "zh" else "Production Bases"),
        ("⚡", "55,000", "总产能 (吨/年)" if lang == "zh" else "Capacity (t/y)"),
        ("🗺️", "200km", "经济辐射半径" if lang == "zh" else "Economic Radius"),
        ("📊", "P1", "当前阶段" if lang == "zh" else "Current Phase"),
    ]
    for col, (icon, val, lbl) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div style="font-size:24px;margin-bottom:4px">{icon}</div>
              <div class="val">{val}</div>
              <div class="lbl">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Phase status
    st.subheader("📋 P1 开发进度 — 搭框架")

    tasks = [
        ("✅", "技术栈确认", "Streamlit + Folium + Plotly，项目骨架已建立"),
        ("✅", "地图底座搭建", "中国地图底图，支持标注、缩放、点击交互"),
        ("✅", "四大基地标注", "赤城·宁东·沧州·如东 精确标注，点击查看详情"),
        ("✅", "200km 辐射圈", "基于经纬度计算的四基地经济辐射圈可视化"),
        ("✅", "数据录入后台", "Excel 上传 + 手动录入，基地产能/成本/电价参数"),
        ("✅", "页面框架导航", "侧边栏导航，三大模块：首页/地图/数据管理"),
    ]

    for status, task, desc in tasks:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:8px 0;
        border-bottom:1px solid rgba(15,23,42,0.04)">
          <span style="font-size:18px">{status}</span>
          <div>
            <strong>{task}</strong>
            <span style="color:#64748b;font-size:0.85rem;margin-left:8px">{desc}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Quick nav
    st.subheader("🚀 快速入口")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗺️ 打开基地地图 →", width="stretch"):
            st.session_state.page = "map"
            st.rerun()
    with c2:
        if st.button("📊 打开数据管理 →", width="stretch"):
            st.session_state.page = "data"
            st.rerun()

    st.caption("P1 阶段完成。下一步 P2：供给端深化 + 需求端（加氢站数据）接入。")
