"""陆上氢销售分析平台 — 主入口 · Platts/Argus 风格"""
import streamlit as st
from utils.ui import inject_global_css, render_ticker
from utils.data_loader import load_sites, load_stations

st.set_page_config(page_title="H₂Trace · 陆上氢销售分析", page_icon="●", layout="wide")

inject_global_css()

# ── Session ──
if "lang" not in st.session_state:
    st.session_state.lang = "zh"
if "page" not in st.session_state:
    st.session_state.page = "home"

lang = st.session_state.lang

# ── Load data for ticker ──
try:
    sites = load_sites()
    stations = load_stations()
except Exception:
    sites, stations = [], []

# ── Top Ticker ──
render_ticker(
    sites_count=len(sites),
    capacity=sum(s.get("capacity", 0) for s in sites),
    stations_count=len(stations),
)

# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 18px">
      <div style="font-weight:800;font-size:1.1rem;color:#fff">● H₂Trace</div>
      <div style="font-size:0.68rem;color:rgba(255,255,255,0.45);margin-top:2px;letter-spacing:0.5px">陆上氢销售分析平台</div>
    </div>
    """, unsafe_allow_html=True)

    lang_label = st.radio("语言", ["中文", "English"], horizontal=True,
                          index=0 if lang == "zh" else 1, label_visibility="collapsed")
    st.session_state.lang = "zh" if lang_label == "中文" else "en"

    st.markdown('<div style="margin:8px 0;border-top:1px solid rgba(255,255,255,0.08)"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:10px;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">导航</p>', unsafe_allow_html=True)

    pages = [
        ("home", "🏠", "首页总览"),
        ("map", "🗺️", "基地地图"),
        ("stations", "⛽", "加氢站网络"),
        ("trading", "💹", "交易撮合"),
        ("data", "⚙️", "数据管理"),
    ]
    current_page = st.session_state.page
    for page_key, icon, label in pages:
        btn_type = "primary" if current_page == page_key else "secondary"
        if st.button(f"{icon}  {label}", key=f"nav_{page_key}", type=btn_type, width="stretch"):
            st.session_state.page = page_key
            st.rerun()

    st.markdown('<div style="margin:12px 0;border-top:1px solid rgba(255,255,255,0.08)"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:10px;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">开发进度</p>', unsafe_allow_html=True)

    phases = [("P1 搭框架", True), ("P2 供需端搭建", True),
              ("P3 成本计算", False), ("P4 优化补充", False)]
    for phase, done in phases:
        icon = "✓" if done else "○"
        color = "rgba(16,185,129,0.9)" if done else "rgba(255,255,255,0.25)"
        st.markdown(f'<div style="font-size:11px;color:{color};padding:2px 0">{icon}  {phase}</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin:12px 0;border-top:1px solid rgba(255,255,255,0.08)"></div>', unsafe_allow_html=True)
    try:
        st.caption(f"🏭 {len(sites)} 基地 · {sum(s.get('capacity',0) for s in sites):,} t/y")
        st.caption(f"⛽ {len(stations)} 加氢站")
    except Exception:
        pass
    st.caption("v0.2.0 · Streamlit Cloud")

# ── Page router ──
if st.session_state.page == "map":
    from pages import production_map
    production_map.render()
elif st.session_state.page == "stations":
    from pages import station_network
    station_network.render()
elif st.session_state.page == "trading":
    from pages import trading_dashboard
    trading_dashboard.render()
elif st.session_state.page == "data":
    from pages import data_input
    data_input.render()
else:
    from pages import home
    home.render()
