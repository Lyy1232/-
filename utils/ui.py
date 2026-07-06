"""UI utilities: premium professional styling."""
import streamlit as st


def inject_global_css():
    st.markdown("""
    <style>
    /* ═══════════════════════════════════════════
       Premium Design System v2
       ═══════════════════════════════════════════ */

    :root {
      --navy-900: #060e1a;
      --navy-800: #0b1a2e;
      --navy-700: #0f2240;
      --brand: #0d9488;
      --brand-light: #14b8a6;
      --brand-50: #f0fdfa;
      --accent: #2563eb;
      --accent-50: #eff6ff;
      --warning: #f59e0b;
      --warning-50: #fffbeb;
      --danger: #ef4444;
      --danger-50: #fef2f2;
      --success: #10b981;
      --shadow-xs: 0 1px 2px rgba(0,0,0,0.03);
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.04), 0 2px 6px rgba(0,0,0,0.03);
      --shadow-md: 0 4px 14px rgba(0,0,0,0.05), 0 2px 6px rgba(0,0,0,0.03);
      --shadow-lg: 0 8px 28px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.03);
      --radius-sm: 6px;
      --radius: 10px;
      --radius-lg: 14px;
      --radius-xl: 18px;
      --spacing-xs: 6px;
      --spacing-sm: 12px;
      --spacing: 18px;
      --spacing-lg: 24px;
      --transition: 0.18s cubic-bezier(0.4,0,0.2,1);
    }
    /* ── Global ── */
    .stApp { background: #f8fafc; }
    .block-container { padding-top: 0.6rem; padding-bottom: 2.5rem; max-width: 1340px; }
    h1, h2, h3, h4, h5 { color: var(--navy-900); font-weight: 700; letter-spacing: -0.015em; }
    h1 { font-size: 1.45rem; line-height: 1.25; }
    h2 { font-size: 1.2rem; line-height: 1.3; }
    h3 { font-size: 1.05rem; line-height: 1.35; }
    p, li { color: #334155; font-size: 0.875rem; }
    a { color: var(--brand); text-decoration: none; transition: var(--transition); }
    a:hover { color: var(--brand-light); }
    hr { border-color: #e2e8f0; margin: 20px 0; }

    /* ── Top Ticker ── */
    .ticker-bar {
      background: linear-gradient(90deg, var(--navy-900) 0%, #0a1625 50%, var(--navy-800) 100%);
      margin: -0.6rem -2rem 0.6rem -2rem;
      padding: 8px 32px;
      display: flex;
      align-items: center;
      gap: 24px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .ticker-brand {
      font-weight: 800; font-size: 13px; color: #fff;
      white-space: nowrap; letter-spacing: -0.3px;
      padding-right: 20px; border-right: 1px solid rgba(255,255,255,0.1);
      display: flex; align-items: center; gap: 7px;
    }
    .ticker-brand .tb-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--brand-light); }
    .ticker-item {
      display: flex; align-items: baseline; gap: 8px;
      font-size: 11px; white-space: nowrap; color: rgba(255,255,255,0.55);
    }
    .ticker-item .ti-label { font-size: 9px; text-transform: uppercase; letter-spacing: 0.8px; color: rgba(255,255,255,0.3); }
    .ticker-item .ti-value { color: rgba(255,255,255,0.9); font-weight: 700; font-size: 12.5px; font-variant-numeric: tabular-nums; }
    .ticker-status { display: flex; align-items: center; gap: 7px; font-size: 10px; color: rgba(255,255,255,0.35); margin-left: auto; }
    .ticker-dot { width: 5px; height: 5px; border-radius: 50%; background: #10b981; box-shadow: 0 0 6px rgba(16,185,129,0.5); animation: ticker-pulse 2.5s infinite; }
    @keyframes ticker-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
      background: linear-gradient(180deg, var(--navy-900) 0%, var(--navy-800) 100%);
      border-right: none;
    }
    /* 隐藏 Streamlit 默认页面导航（与自定义中文导航重复） */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] { display: none !important; }
    section[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
    section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.06); }
    section[data-testid="stSidebar"] .stRadio > div {
      background: rgba(255,255,255,0.04); border-radius: var(--radius-sm); padding: 3px;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
      background: rgba(255,255,255,0.03) !important;
      border: 1px solid rgba(255,255,255,0.05) !important;
      color: rgba(255,255,255,0.7) !important;
      border-radius: var(--radius-sm) !important;
      font-weight: 500 !important; font-size: 12.5px !important;
      text-align: left !important; padding: 9px 12px !important;
      margin-bottom: 1px !important; transition: var(--transition) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
      background: rgba(255,255,255,0.08) !important;
      border-color: rgba(255,255,255,0.12) !important;
      color: #fff !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"] {
      background: var(--brand) !important;
      border-color: var(--brand) !important;
      color: #fff !important; font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
      background: var(--brand-light) !important;
    }

    /* ── Professional Metric Card ── */
    .metric-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: var(--radius-lg);
      padding: 20px 22px;
      box-shadow: var(--shadow-sm);
      transition: transform var(--transition), box-shadow var(--transition), border-color var(--transition);
      position: relative; overflow: hidden;
    }
    .metric-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg);
      border-color: #cbd5e1;
    }
    .metric-card .mc-accent-bar {
      position: absolute; top: 0; left: 0; right: 0; height: 3px;
      border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    }
    .metric-card .mc-icon { font-size: 20px; margin-bottom: 8px; opacity: 0.85; }
    .metric-card .mc-value {
      font-size: 27px; font-weight: 800; color: var(--navy-900);
      line-height: 1.15; font-variant-numeric: tabular-nums; letter-spacing: -0.8px;
    }
    .metric-card .mc-label {
      font-size: 10.5px; color: #64748b; margin-top: 4px;
      text-transform: uppercase; letter-spacing: 0.6px; font-weight: 600;
    }
    .metric-card .mc-sub { font-size: 10px; color: #94a3b8; margin-top: 5px; }
    .metric-card .mc-delta { font-size: 11px; font-weight: 600; margin-top: 6px; }
    .mc-delta.up { color: #059669; }
    .mc-delta.down { color: #dc2626; }

    /* ── Data Container Card ── */
    .data-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: var(--radius-lg);
      padding: 22px 24px;
      box-shadow: var(--shadow-xs);
      transition: var(--transition);
    }
    .data-card:hover { box-shadow: var(--shadow-sm); }
    .data-card .dc-header {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 16px; padding-bottom: 12px;
      border-bottom: 1px solid #f1f5f9;
    }
    .data-card .dc-title {
      font-size: 11px; font-weight: 700; color: #64748b;
      text-transform: uppercase; letter-spacing: 0.8px;
    }
    .data-card .dc-badge {
      font-size: 9px; padding: 3px 8px; border-radius: 100px;
      font-weight: 600; letter-spacing: 0.4px;
    }
    .dc-badge.live { background: #ecfdf5; color: #065f46; }
    .dc-badge.updated { background: var(--accent-50); color: #1e40af; }

    /* ── Info Card (left-border accent) ── */
    .info-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-left: 3px solid var(--brand);
      border-radius: 0 var(--radius) var(--radius) 0;
      padding: 15px 18px; margin-bottom: 8px;
      box-shadow: var(--shadow-xs);
      transition: transform var(--transition), box-shadow var(--transition);
    }
    .info-card:hover {
      transform: translateX(2px);
      box-shadow: var(--shadow-md);
    }
    .info-card.warning { border-left-color: var(--warning); }
    .info-card.danger { border-left-color: var(--danger); }
    .info-card .ic-title { font-size: 13px; font-weight: 700; color: var(--navy-900); margin-bottom: 5px; }
    .info-card .ic-row { display: flex; gap: 16px; font-size: 11px; color: #64748b; flex-wrap: wrap; }
    .info-card .ic-row b { color: #334155; font-weight: 600; }

    /* ── Buttons ── */
    div[data-testid="stButton"] > button {
      border-radius: var(--radius-sm) !important;
      font-weight: 600 !important; font-size: 12.5px !important;
      transition: var(--transition) !important;
      border: 1px solid #e2e8f0 !important;
      background: #ffffff !important;
      color: #334155 !important;
      padding: 7px 14px !important;
    }
    div[data-testid="stButton"] > button:hover {
      transform: translateY(-1px);
      box-shadow: var(--shadow-md);
      border-color: var(--brand-light) !important;
      color: var(--brand) !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
      background: var(--brand) !important;
      color: #fff !important; border-color: var(--brand) !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
      background: var(--brand-light) !important;
      box-shadow: 0 4px 16px rgba(8,155,140,0.2);
    }

    /* ── Data Editor ── */
    div[data-testid="stDataEditor"] {
      border: 1px solid #e2e8f0 !important;
      border-radius: var(--radius-lg) !important;
      overflow: hidden;
      box-shadow: var(--shadow-xs);
    }

    /* ── Dataframe / Table ── */
    [data-testid="stDataFrame"] {
      border: 1px solid #e2e8f0 !important;
      border-radius: var(--radius-lg) !important;
      overflow: hidden;
      box-shadow: var(--shadow-xs);
    }
    [data-testid="stDataFrame"] th {
      background: #f8fafc !important;
      color: #64748b !important;
      font-size: 10.5px !important; font-weight: 700 !important;
      text-transform: uppercase !important; letter-spacing: 0.6px !important;
      padding: 10px 14px !important;
      border-bottom: 2px solid #e2e8f0 !important;
    }
    [data-testid="stDataFrame"] td {
      padding: 10px 14px !important; font-size: 12.5px !important;
      border-bottom: 1px solid #f1f5f9 !important;
      color: #334155 !important;
    }
    [data-testid="stDataFrame"] tbody tr:hover td {
      background: var(--brand-50) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
      gap: 2px; background: transparent;
      border-bottom: 2px solid #e2e8f0; padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
      border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
      padding: 9px 18px !important; font-weight: 600 !important;
      font-size: 12.5px !important; color: #64748b !important;
      background: transparent !important; border: none !important;
      margin-bottom: -2px; transition: var(--transition) !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #334155 !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
      color: var(--brand) !important;
      border-bottom: 2px solid var(--brand) !important;
    }

    /* ── Expanders ── */
    details[data-testid="stExpander"] {
      border: 1px solid #e2e8f0 !important;
      border-radius: var(--radius-lg) !important;
      box-shadow: var(--shadow-xs); background: #ffffff;
      transition: box-shadow var(--transition);
    }
    details[data-testid="stExpander"]:hover { box-shadow: var(--shadow-sm); }

    /* ── Native Metric ── */
    [data-testid="stMetric"] {
      background: #ffffff; border: 1px solid #e2e8f0;
      border-radius: var(--radius-lg); padding: 16px 18px;
      box-shadow: var(--shadow-xs);
    }
    [data-testid="stMetric"] label {
      color: #64748b !important; font-size: 10.5px !important;
      font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.6px;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
      font-size: 22px !important; font-weight: 800 !important; color: var(--navy-900) !important;
    }

    /* ── Checkbox / Radio ── */
    .stCheckbox label, .stRadio label { color: #334155 !important; font-size: 13px !important; }

    /* ── Toast ── */
    [data-testid="stToast"] { border-radius: var(--radius) !important; font-weight: 500 !important; }

    /* ── Spinner ── */
    .stSpinner > div { border-top-color: var(--brand) !important; }

    /* ── Select box ── */
    .stSelectbox [data-baseweb="select"] > div {
      border-radius: var(--radius-sm) !important; border-color: #e2e8f0 !important;
    }

    /* ── Caption ── */
    .stCaption { color: #94a3b8 !important; font-size: 10.5px !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.18); }

    /* ── Section header ── */
    .section-kicker {
      font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
      text-transform: uppercase; color: var(--brand);
      margin-bottom: 4px;
    }

    /* ── Responsive ── */
    @media (max-width: 900px) {
      .ticker-bar { flex-wrap: wrap; gap: 10px; padding: 8px 16px; }
      .ticker-status { margin-left: 0; width: 100%; }
      .metric-card .mc-value { font-size: 22px; }
      .block-container { padding: 0.4rem; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_ticker(sites_count: int = 0, capacity: int = 0, stations_count: int = 0):
    st.markdown(f"""
    <div class="ticker-bar">
      <div class="ticker-brand">
        <span class="tb-dot"></span>陆上氢基能源销售平台
      </div>
      <div class="ticker-item">
        <span class="ti-label">制氢基地</span>
        <span class="ti-value">{sites_count}</span>
      </div>
      <div class="ticker-item">
        <span class="ti-label">总产能</span>
        <span class="ti-value">{capacity:,} t/y</span>
      </div>
      <div class="ticker-item">
        <span class="ti-label">加氢站覆盖</span>
        <span class="ti-value">{stations_count}</span>
      </div>
      <div class="ticker-item">
        <span class="ti-label">平台</span>
        <span class="ti-value" style="color:#10b981">LIVE</span>
      </div>
      <div class="ticker-status">
        <span class="ticker-dot"></span>
        Streamlit Cloud · v0.2.0
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_module_header(title: str, subtitle: str = "", badge: str = ""):
    badge_html = f'<span class="dc-badge live" style="margin-left:10px;font-size:10px;padding:3px 10px">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div style="padding:4px 0 18px">
      <div style="display:flex;align-items:center;margin-bottom:2px">
        <h1 style="font-size:1.35rem;margin:0;font-weight:800;letter-spacing:-0.3px">{title}</h1>
        {badge_html}
      </div>
      {f'<p style="color:#64748b;font-size:0.8rem;margin:2px 0 0">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)
