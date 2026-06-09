"""UI utilities: enhanced CSS, header rendering, common components."""
import streamlit as st


def inject_global_css():
    st.markdown("""
    <style>
    /* ── Design Tokens ── */
    :root {
      --c-primary: #0f766e;
      --c-bg: #f8fafb;
      --c-card: #ffffff;
      --c-border: rgba(15,23,42,0.06);
      --c-text: #0f172a;
      --c-text-2: #475569;
      --c-text-3: #64748b;
      --shadow-sm: 0 1px 3px rgba(15,23,42,0.06);
      --shadow-md: 0 4px 16px rgba(15,23,42,0.08);
      --radius: 12px;
      --transition: 0.2s ease;
    }

    /* ── Global ── */
    .block-container {
      padding-top: 1rem;
      padding-bottom: 2rem;
      max-width: 1280px;
    }
    section[data-testid="stSidebar"] {
      background: var(--c-bg);
      border-right: 1px solid var(--c-border);
    }
    .stApp {
      background: var(--c-bg);
    }
    h1, h2, h3 {
      color: var(--c-text);
    }

    /* ── Metric Card ── */
    .metric-card {
      background: var(--c-card);
      border: 1px solid var(--c-border);
      border-radius: var(--radius);
      padding: 22px 20px;
      text-align: center;
      box-shadow: var(--shadow-sm);
      transition: transform var(--transition), box-shadow var(--transition);
    }
    .metric-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-md);
    }
    .metric-card .val {
      font-size: 28px;
      font-weight: 800;
      color: var(--c-text);
      line-height: 1.2;
    }
    .metric-card .lbl {
      font-size: 12px;
      color: var(--c-text-3);
      margin-top: 4px;
    }

    /* ── Site Card ── */
    .site-card {
      background: var(--c-card);
      border: 1px solid var(--c-border);
      border-radius: 10px;
      padding: 16px 18px;
      box-shadow: var(--shadow-sm);
      transition: transform var(--transition), box-shadow var(--transition);
    }
    .site-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-md);
    }

    /* ── Buttons ── */
    div[data-testid="stButton"] > button {
      border-radius: 8px;
      font-weight: 600;
      transition: transform 0.15s, box-shadow 0.15s;
    }
    div[data-testid="stButton"] > button:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 16px rgba(15,23,42,0.1);
    }

    /* ── Data Editor ── */
    div[data-testid="stDataEditor"] {
      border: 1px solid var(--c-border);
      border-radius: var(--radius);
      overflow: hidden;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
      gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
      border-radius: 8px 8px 0 0;
      padding: 8px 18px;
    }

    /* ── Expanders ── */
    details[data-testid="stExpander"] {
      border: 1px solid var(--c-border) !important;
      border-radius: var(--radius) !important;
      box-shadow: var(--shadow-sm);
    }

    /* ── Sidebar nav buttons ── */
    [data-testid="stSidebar"] div[data-testid="stButton"] > button {
      text-align: left;
      padding: 10px 14px;
      margin-bottom: 2px;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(15,23,42,0.12); border-radius: 3px; }

    /* ── Responsive ── */
    @media (max-width: 900px) {
      .metric-card .val { font-size: 22px; }
      .block-container { padding: 0.5rem; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    lang = st.session_state.get("lang", "zh")
    title = "陆上氢销售分析平台" if lang == "zh" else "Onshore H₂ Sales Platform"
    subtitle = (
        "国内氢能供需匹配与定价决策工具 · 四大基地 → 200km经济辐射圈"
        if lang == "zh"
        else "Domestic H₂ supply-demand matching & pricing · 4 Bases → 200km Radius"
    )
    st.markdown(f"""
    <div style="padding:16px 0 8px;border-bottom:1px solid rgba(15,23,42,0.05);margin-bottom:12px">
      <h1 style="font-size:1.5rem;font-weight:800;margin:0;color:#0f172a;">🌱 {title}</h1>
      <p style="color:#64748b;font-size:0.8rem;margin:4px 0 0;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)
