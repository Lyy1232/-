"""陆上氢销售分析平台 — 主入口"""
import streamlit as st
import json
from pathlib import Path
from utils.ui import inject_global_css, render_header

PROJECT_ROOT = Path(__file__).resolve().parent

st.set_page_config(page_title="陆上氢销售分析平台", page_icon="🌱", layout="wide")

inject_global_css()

if "lang" not in st.session_state:
    st.session_state.lang = "zh"
if "page" not in st.session_state:
    st.session_state.page = "home"

lang = st.session_state.lang

# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 16px">
      <div style="font-weight:800;font-size:1rem;color:#0f172a;">🌱 陆上氢销售分析</div>
      <div style="font-size:0.72rem;color:#64748b;">Onshore H₂ Sales Analytics</div>
    </div>
    """, unsafe_allow_html=True)

    lang_label = st.radio("语言", ["中文", "English"], horizontal=True, index=0 if lang == "zh" else 1)
    st.session_state.lang = "zh" if lang_label == "中文" else "en"

    st.markdown("---")
    st.markdown("**📍 核心功能**")

    if st.button("🏠 首页总览", width="stretch"):
        st.session_state.page = "home"
        st.rerun()
    if st.button("🗺️ 基地地图", width="stretch"):
        st.session_state.page = "map"
        st.rerun()
    if st.button("📊 数据管理", width="stretch"):
        st.session_state.page = "data"
        st.rerun()

    st.markdown("---")
    st.caption("P1 · 搭框架阶段 · 2026.06")

# ── Page routing ──
if st.session_state.page == "map":
    from pages import production_map
    production_map.render()
elif st.session_state.page == "data":
    from pages import data_input
    data_input.render()
else:
    from pages import home
    home.render()
