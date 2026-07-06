"""陆上氢销售分析平台 — 主入口 · Platts/Argus 风格"""
import streamlit as st
from utils.ui import inject_global_css, render_ticker
from utils.data_loader import load_sites, load_stations

st.set_page_config(page_title="陆上氢基能源销售平台", page_icon="●", layout="wide")

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
      <div style="font-weight:800;font-size:1.1rem;color:#fff">● 陆上氢基能源销售平台</div>
      <div style="font-size:0.68rem;color:rgba(255,255,255,0.45);margin-top:2px;letter-spacing:0.5px">氢链 · 前端营销工具</div>
    </div>
    """, unsafe_allow_html=True)

    lang_label = st.radio("语言", ["中文", "English"], horizontal=True,
                          index=0 if lang == "zh" else 1, label_visibility="collapsed")
    st.session_state.lang = "zh" if lang_label == "中文" else "en"

    st.markdown('<div style="margin:8px 0;border-top:1px solid rgba(255,255,255,0.08)"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:10px;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">导航</p>', unsafe_allow_html=True)

    pages = [
        ("home", "🏠", "业务总览"),
        ("map", "🗺️", "基地与覆盖"),
        ("stations", "⛽", "加氢站网络"),
        ("cost", "📊", "成本竞争力"),
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
              ("P3 交易撮合+数据管道", True), ("P4 成本竞争力+聚焦", True)]
    for phase, done in phases:
        icon = "✓" if done else "○"
        color = "rgba(16,185,129,0.9)" if done else "rgba(255,255,255,0.25)"
        st.markdown(f'<div style="font-size:11px;color:{color};padding:2px 0">{icon}  {phase}</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin:12px 0;border-top:1px solid rgba(255,255,255,0.08)"></div>', unsafe_allow_html=True)

    # ── PIN 锁定 ──
    if "pin_verified" not in st.session_state:
        st.session_state.pin_verified = False
    if "show_exact_costs" not in st.session_state:
        st.session_state.show_exact_costs = False

    pin_input = st.text_input("🔒 解锁精确成本", type="password", placeholder="输入PIN查看精确成本",
                              key="pin_field", label_visibility="collapsed")
    if pin_input == "2026" and not st.session_state.pin_verified:
        st.session_state.pin_verified = True
        st.session_state.show_exact_costs = True
        st.rerun()
    elif pin_input and pin_input != "2026":
        st.caption("PIN错误")

    if st.session_state.pin_verified:
        st.caption("🔓 精确成本已解锁")
        if st.button("🔒 锁定", key="lock_btn", use_container_width=True):
            st.session_state.pin_verified = False
            st.session_state.show_exact_costs = False
            st.rerun()

    st.markdown('<div style="margin:8px 0;border-top:1px solid rgba(255,255,255,0.08)"></div>', unsafe_allow_html=True)

    # ── 重置模块 ──
    if st.button("🔄 重置默认参数", key="reset_btn", use_container_width=True):
        import json
        defaults = [
            {"name": "赤城", "province": "河北", "lat": 40.91, "lon": 115.83, "tech": "风电电解",
             "capacity": 20000, "cost_low": 13, "cost_avg": 15.2, "cost_high": 18, "utilization": 42, "cert_status": "可再生氢预评价"},
            {"name": "宁东", "province": "宁夏", "lat": 38.15, "lon": 106.57, "tech": "光伏电解",
             "capacity": 12000, "cost_low": 13, "cost_avg": 15.2, "cost_high": 18, "utilization": 50, "cert_status": "ISCC EU 认证中"},
            {"name": "沧州", "province": "河北", "lat": 38.30, "lon": 116.84, "tech": "工业副产氢",
             "capacity": 8000, "cost_low": 8, "cost_avg": 9.6, "cost_high": 12, "utilization": 60, "cert_status": "清洁氢认证"},
            {"name": "如东", "province": "江苏", "lat": 32.33, "lon": 121.18, "tech": "风电电解",
             "capacity": 15000, "cost_low": 13, "cost_avg": 15.2, "cost_high": 18, "utilization": 30, "cert_status": "规划中"},
        ]
        with open("config/sites.json", "w", encoding="utf-8") as f:
            json.dump(defaults, f, ensure_ascii=False, indent=2)
        load_sites.clear()
        st.success("参数已重置为默认值")
        st.rerun()

    st.markdown('<div style="margin:8px 0;border-top:1px solid rgba(255,255,255,0.08)"></div>', unsafe_allow_html=True)
    try:
        sites_count = len(sites)
        total_cap = sum(s.get('capacity', 0) for s in sites)
        st.caption(f"🏭 {sites_count} 基地 · {total_cap:,} t/y")
        st.caption(f"⛽ {len(stations)} 加氢站")
    except Exception:
        pass
    st.caption("v0.3.0 · Streamlit Cloud")

# ── Page router ──
if st.session_state.page == "map":
    from pages import production_map
    production_map.render()
elif st.session_state.page == "stations":
    from pages import station_network
    station_network.render()
elif st.session_state.page == "cost":
    from pages import cost_analysis
    cost_analysis.render()
elif st.session_state.page == "data":
    from pages import data_input
    data_input.render()
else:
    from pages import home
    home.render()
