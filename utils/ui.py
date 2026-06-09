"""UI utilities: CSS injection, hero rendering, common components."""
import streamlit as st


def inject_global_css():
    st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1260px; }
    section[data-testid="stSidebar"] { background: #f7faf8; border-right: 1px solid rgba(15,23,42,0.08); }
    .stApp { background: #f8fafb; }
    h1, h2, h3 { color: #0f172a; }
    .metric-card {
        background: #fff; border: 1px solid rgba(15,23,42,0.06);
        border-radius: 12px; padding: 22px 20px; text-align: center;
        box-shadow: 0 2px 12px rgba(15,23,42,0.04);
    }
    .metric-card .val { font-size: 30px; font-weight: 800; color: #0f172a; }
    .metric-card .lbl { font-size: 12px; color: #64748b; margin-top: 4px; }
    .site-card {
        background: #fff; border: 1px solid rgba(15,23,42,0.06);
        border-radius: 12px; padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(15,23,42,0.04);
    }
    .site-card h4 { color: #0f172a; margin: 0 0 6px; font-size: 16px; }
    .site-card p { color: #475569; font-size: 13px; margin: 2px 0; }
    .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
    .tag-green { background: #dcfce7; color: #166534; }
    .tag-blue { background: #dbeafe; color: #1e40af; }
    .tag-amber { background: #fef3c7; color: #92400e; }
    div[data-testid="stButton"] > button {
        border-radius: 8px; font-weight: 600;
        transition: transform 0.15s, box-shadow 0.15s;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(15,23,42,0.1);
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    lang = st.session_state.get("lang", "zh")
    title = "陆上氢销售分析平台" if lang == "zh" else "Onshore H₂ Sales Analytics"
    subtitle = "国内氢能供需匹配与定价决策工具 · 四大基地 → 200km经济辐射圈" if lang == "zh" else "Domestic H₂ supply-demand matching & pricing · 4 Bases → 200km Radius"
    st.markdown(f"""
    <div style="padding:20px 0 10px;border-bottom:1px solid rgba(15,23,42,0.06);margin-bottom:14px">
      <h1 style="font-size:1.6rem;font-weight:800;margin:0;color:#0f172a;">🌱 {title}</h1>
      <p style="color:#64748b;font-size:0.85rem;margin:4px 0 0;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)
