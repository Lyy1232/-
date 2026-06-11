"""UI utilities: Platts/Argus-inspired professional styling."""
import streamlit as st


def inject_global_css():
    st.markdown("""
    <style>
    /* ═══════════════════════════════════════════
       Design System — Platts/Argus Inspired
       ═══════════════════════════════════════════ */

    :root {
      --navy: #0a1628;
      --navy-light: #132038;
      --navy-card: #162a45;
      --teal: #00a99d;
      --teal-light: #e0f7f5;
      --blue: #2563eb;
      --blue-light: #eff6ff;
      --amber: #d97706;
      --amber-light: #fffbeb;
      --red: #dc2626;
      --red-light: #fef2f2;
      --text: #1e293b;
      --text-2: #475569;
      --text-3: #64748b;
      --text-4: #94a3b8;
      --border: #e2e8f0;
      --border-light: #f1f5f9;
      --bg: #f4f6f9;
      --bg-white: #ffffff;
      --shadow-xs: 0 1px 2px rgba(10,22,40,0.04);
      --shadow-sm: 0 1px 3px rgba(10,22,40,0.06), 0 1px 2px rgba(10,22,40,0.04);
      --shadow-md: 0 4px 12px rgba(10,22,40,0.06), 0 2px 4px rgba(10,22,40,0.04);
      --shadow-lg: 0 12px 32px rgba(10,22,40,0.08), 0 4px 8px rgba(10,22,40,0.04);
      --radius-xs: 4px;
      --radius-sm: 8px;
      --radius: 10px;
      --radius-lg: 14px;
      --transition: 0.2s cubic-bezier(0.4,0,0.2,1);
    }

    /* ── Global ── */
    .stApp {
      background: var(--bg);
    }
    .block-container {
      padding-top: 0.8rem;
      padding-bottom: 2rem;
      max-width: 1320px;
    }
    h1, h2, h3, h4, h5 { color: var(--text); font-weight: 700; letter-spacing: -0.01em; }
    h1 { font-size: 1.5rem; }
    h2 { font-size: 1.25rem; }
    h3 { font-size: 1.1rem; }
    p, li { color: var(--text-2); }
    a { color: var(--teal); text-decoration: none; }
    a:hover { text-decoration: underline; }
    hr { border-color: var(--border); margin: 16px 0; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
      background: linear-gradient(180deg, var(--navy) 0%, var(--navy-light) 100%);
      border-right: none;
    }
    section[data-testid="stSidebar"] * {
      color: rgba(255,255,255,0.9) !important;
    }
    section[data-testid="stSidebar"] .stRadio > div {
      background: rgba(255,255,255,0.06);
      border-radius: var(--radius-sm);
      padding: 4px;
    }
    section[data-testid="stSidebar"] hr {
      border-color: rgba(255,255,255,0.08);
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
      background: rgba(255,255,255,0.05) !important;
      border: 1px solid rgba(255,255,255,0.08) !important;
      color: rgba(255,255,255,0.85) !important;
      border-radius: var(--radius-sm) !important;
      font-weight: 500 !important;
      text-align: left !important;
      padding: 10px 14px !important;
      margin-bottom: 2px !important;
      transition: var(--transition) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
      background: rgba(255,255,255,0.1) !important;
      border-color: rgba(255,255,255,0.15) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button:has(kbd) {
      background: var(--teal) !important;
      border-color: var(--teal) !important;
      color: #fff !important;
      font-weight: 600 !important;
    }
    /* Active page = primary type button */
    section[data-testid="stSidebar"] button[kind="primary"] {
      background: var(--teal) !important;
      border-color: var(--teal) !important;
      color: #fff !important;
      font-weight: 600 !important;
    }

    /* ── Top Ticker Bar ── */
    .ticker-bar {
      background: linear-gradient(90deg, var(--navy) 0%, #0d1f3c 100%);
      margin: -0.8rem -2rem 0.8rem -2rem;
      padding: 10px 28px;
      display: flex;
      align-items: center;
      gap: 28px;
      overflow: hidden;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .ticker-brand {
      font-weight: 800;
      font-size: 14px;
      color: #fff;
      white-space: nowrap;
      letter-spacing: -0.3px;
      padding-right: 20px;
      border-right: 1px solid rgba(255,255,255,0.12);
    }
    .ticker-brand span { color: var(--teal); }
    .ticker-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      white-space: nowrap;
      color: rgba(255,255,255,0.7);
    }
    .ticker-item .ticker-label { color: rgba(255,255,255,0.45); font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
    .ticker-item .ticker-value { color: #fff; font-weight: 700; font-size: 13px; font-variant-numeric: tabular-nums; }
    .ticker-item .ticker-change { font-size: 10px; font-weight: 600; padding: 1px 5px; border-radius: 3px; }
    .ticker-change.up { color: #10b981; background: rgba(16,185,129,0.12); }
    .ticker-change.down { color: #ef4444; background: rgba(239,68,68,0.12); }
    .ticker-status { display: flex; align-items: center; gap: 6px; font-size: 10px; color: rgba(255,255,255,0.5); margin-left: auto; }
    .ticker-dot { width: 6px; height: 6px; border-radius: 50%; background: #10b981; animation: pulse-dot 2s infinite; }
    @keyframes pulse-dot { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

    /* ── Metric Cards (Platts-style) ── */
    .metric-card {
      background: var(--bg-white);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px 22px;
      box-shadow: var(--shadow-sm);
      transition: transform var(--transition), box-shadow var(--transition);
      position: relative;
      overflow: hidden;
    }
    .metric-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-md);
    }
    .metric-card .mc-icon { font-size: 22px; margin-bottom: 8px; }
    .metric-card .mc-value {
      font-size: 28px;
      font-weight: 800;
      color: var(--text);
      line-height: 1.1;
      font-variant-numeric: tabular-nums;
      letter-spacing: -0.5px;
    }
    .metric-card .mc-label { font-size: 11px; color: var(--text-3); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
    .metric-card .mc-sub { font-size: 10px; color: var(--text-4); margin-top: 4px; }
    .metric-card .mc-accent-bar { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
    .metric-card .mc-delta { font-size: 11px; font-weight: 600; margin-top: 4px; }
    .metric-card .mc-delta.up { color: #10b981; }
    .metric-card .mc-delta.down { color: #ef4444; }

    /* ── Data Cards ── */
    .data-card {
      background: var(--bg-white);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      box-shadow: var(--shadow-sm);
      transition: var(--transition);
    }
    .data-card:hover { box-shadow: var(--shadow-md); }
    .data-card .dc-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-light);
    }
    .data-card .dc-title { font-size: 13px; font-weight: 700; color: var(--text); text-transform: uppercase; letter-spacing: 0.5px; }
    .data-card .dc-badge { font-size: 10px; padding: 3px 8px; border-radius: 100px; font-weight: 600; letter-spacing: 0.3px; }
    .dc-badge.live { background: #dcfce7; color: #166534; }
    .dc-badge.updated { background: var(--blue-light); color: #1e40af; }
    .dc-badge.pending { background: var(--amber-light); color: #92400e; }

    /* ── Site/Station Cards ── */
    .info-card {
      background: var(--bg-white);
      border: 1px solid var(--border);
      border-left: 3px solid var(--teal);
      border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
      padding: 14px 16px;
      margin-bottom: 8px;
      box-shadow: var(--shadow-xs);
      transition: var(--transition);
    }
    .info-card:hover {
      box-shadow: var(--shadow-sm);
      border-left-color: var(--blue);
    }
    .info-card.warning { border-left-color: var(--amber); }
    .info-card.danger { border-left-color: var(--red); }
    .info-card .ic-title { font-size: 13px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
    .info-card .ic-row { display: flex; gap: 14px; font-size: 11px; color: var(--text-3); flex-wrap: wrap; }
    .info-card .ic-row span { white-space: nowrap; }
    .info-card .ic-row b { color: var(--text-2); }

    /* ── Buttons ── */
    div[data-testid="stButton"] > button {
      border-radius: var(--radius-sm) !important;
      font-weight: 600 !important;
      font-size: 13px !important;
      transition: var(--transition) !important;
      border: 1px solid var(--border) !important;
      background: var(--bg-white) !important;
      color: var(--text) !important;
      padding: 8px 16px !important;
    }
    div[data-testid="stButton"] > button:hover {
      transform: translateY(-1px);
      box-shadow: var(--shadow-sm);
      border-color: var(--teal) !important;
      color: var(--teal) !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
      background: var(--teal) !important;
      color: #fff !important;
      border-color: var(--teal) !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
      background: #008f85 !important;
      color: #fff !important;
    }

    /* ── Data Editor ── */
    div[data-testid="stDataEditor"] {
      border: 1px solid var(--border) !important;
      border-radius: var(--radius) !important;
      overflow: hidden;
    }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] {
      border: 1px solid var(--border) !important;
      border-radius: var(--radius) !important;
      overflow: hidden;
    }
    [data-testid="stDataFrame"] th {
      background: #f8fafc !important;
      color: var(--text-3) !important;
      font-size: 11px !important;
      font-weight: 600 !important;
      text-transform: uppercase !important;
      letter-spacing: 0.5px !important;
      padding: 10px 14px !important;
      border-bottom: 2px solid var(--border) !important;
    }
    [data-testid="stDataFrame"] td {
      padding: 10px 14px !important;
      font-size: 13px !important;
      border-bottom: 1px solid var(--border-light) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
      gap: 2px;
      background: transparent;
      border-bottom: 2px solid var(--border);
      padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
      border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
      padding: 10px 20px !important;
      font-weight: 600 !important;
      font-size: 13px !important;
      color: var(--text-3) !important;
      background: transparent !important;
      border: none !important;
      margin-bottom: -2px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
      color: var(--teal) !important;
      border-bottom: 2px solid var(--teal) !important;
    }

    /* ── Expanders ── */
    details[data-testid="stExpander"] {
      border: 1px solid var(--border) !important;
      border-radius: var(--radius) !important;
      box-shadow: var(--shadow-xs);
      background: var(--bg-white);
    }

    /* ── Metric (Streamlit native) ── */
    [data-testid="stMetric"] {
      background: var(--bg-white);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 16px 18px;
      box-shadow: var(--shadow-xs);
    }
    [data-testid="stMetric"] label { color: var(--text-3) !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.5px; }

    /* ── Checkbox / Radio / Select ── */
    .stCheckbox label, .stRadio label { color: var(--text-2) !important; font-size: 13px !important; }

    /* ── Toast / Alert ── */
    [data-testid="stToast"] {
      border-radius: var(--radius-sm) !important;
      font-weight: 500 !important;
    }

    /* ── Spinner ── */
    .stSpinner > div { border-top-color: var(--teal) !important; }

    /* ── Caption ── */
    .stCaption { color: var(--text-4) !important; font-size: 11px !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(10,22,40,0.12); border-radius: 3px; }

    /* ── Selection boxes ── */
    .stSelectbox [data-baseweb="select"] > div {
      border-radius: var(--radius-sm) !important;
      border-color: var(--border) !important;
    }

    /* ── Responsive ── */
    @media (max-width: 900px) {
      .ticker-bar { flex-wrap: wrap; gap: 12px; padding: 8px 16px; }
      .ticker-status { margin-left: 0; width: 100%; }
      .metric-card .mc-value { font-size: 22px; }
      .block-container { padding: 0.4rem; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_ticker(sites_count: int = 0, capacity: int = 0, stations_count: int = 0):
    """Render a Platts-style top ticker bar with key metrics."""
    avg_cost = 23.5
    st.markdown(f"""
    <div class="ticker-bar">
      <div class="ticker-brand">H₂<span>Trace</span> 氢溯科技</div>
      <div class="ticker-item">
        <span class="ticker-label">制氢基地</span>
        <span class="ticker-value">{sites_count}</span>
      </div>
      <div class="ticker-item">
        <span class="ticker-label">总产能</span>
        <span class="ticker-value">{capacity:,} t/y</span>
      </div>
      <div class="ticker-item">
        <span class="ticker-label">加氢站覆盖</span>
        <span class="ticker-value">{stations_count}</span>
        <span class="ticker-change up">P2</span>
      </div>
      <div class="ticker-item">
        <span class="ticker-label">平台状态</span>
        <span class="ticker-value" style="color:#10b981">● LIVE</span>
      </div>
      <div class="ticker-status">
        <span class="ticker-dot"></span>
        <span>数据更新 · Streamlit Cloud · v0.2.0</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_header():
    """Minimal header — main branding is now in the ticker bar."""
    pass


def render_module_header(title: str, subtitle: str = "", badge: str = ""):
    """Professional module header with optional status badge."""
    badge_html = f'<span class="dc-badge live" style="margin-left:10px">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div style="padding:8px 0 16px;margin-bottom:8px">
      <div style="display:flex;align-items:center">
        <h1 style="font-size:1.4rem;margin:0;color:var(--text)">{title}</h1>
        {badge_html}
      </div>
      {f'<p style="color:var(--text-3);font-size:0.8rem;margin:4px 0 0">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)
