"""陆上氢销售分析平台 — 主入口"""
import streamlit as st
from utils.ui import inject_global_css
from utils.data_loader import load_sites, get_updated_time

st.set_page_config(page_title="陆上氢销售分析平台", page_icon="🌱", layout="wide")

inject_global_css()

# ── Session init ──
if "lang" not in st.session_state:
    st.session_state.lang = "zh"
if "page" not in st.session_state:
    st.session_state.page = "home"

lang = st.session_state.lang

# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div style="padding:4px 0 12px">
      <div style="font-weight:800;font-size:1.05rem;color:#0f172a;">🌱 陆上氢销售分析</div>
      <div style="font-size:0.7rem;color:#94a3b8;margin-top:1px">Onshore H₂ Sales Analytics</div>
    </div>
    """, unsafe_allow_html=True)

    # Language
    lang_label = st.radio("语言 / Language", ["中文", "English"], horizontal=True,
                          index=0 if lang == "zh" else 1, label_visibility="collapsed")
    st.session_state.lang = "zh" if lang_label == "中文" else "en"

    st.markdown("---")

    # Navigation with active state
    pages = [
        ("home", "🏠", "首页总览", "Home"),
        ("map", "🗺️", "基地地图", "Map"),
        ("stations", "⛽", "加氢站网络", "Stations"),
        ("data", "📊", "数据管理", "Data"),
    ]
    current_page = st.session_state.page

    for page_key, icon, zh_label, en_label in pages:
        label = f"{icon}  {zh_label}" if lang == "zh" else f"{icon}  {en_label}"
        btn_type = "primary" if current_page == page_key else "secondary"
        if st.button(label, key=f"nav_{page_key}", type=btn_type, width="stretch"):
            st.session_state.page = page_key
            st.rerun()

    st.markdown("---")

    # Phase progress
    st.caption("**开发阶段**")
    phases = [
        ("P1 搭框架", True),
        ("P2 供需端搭建", True),
        ("P3 成本计算+供需调控", False),
        ("P4 优化补充", False),
    ]
    for phase, done in phases:
        icon = "✅" if done else "⏳"
        color = "#10b981" if done else "#94a3b8"
        st.markdown(f'<span style="font-size:12px;color:{color}">{icon} {phase}</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Data status
    try:
        sites = load_sites()
        st.caption(f"🏭 {len(sites)} 个基地 · {sum(s.get('capacity', 0) for s in sites):,} t/y")
        ts = get_updated_time()
        if ts and ts != "无法读取" and ts != "未记录":
            st.caption(f"📅 更新: {ts[:10]}")
    except Exception:
        st.caption("数据加载中...")

    st.caption("v0.1.0 · P1")

# ── Page routing ──
if st.session_state.page == "map":
    from pages import production_map
    production_map.render()
elif st.session_state.page == "stations":
    from pages import station_network
    station_network.render()
elif st.session_state.page == "data":
    from pages import data_input
    data_input.render()
else:
    from pages import home
    home.render()
