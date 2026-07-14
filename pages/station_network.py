"""氢基产品需求信息网络 — 数据源：国内氢需求企业数据库 Excel · 双向同步"""
import os
import json
import streamlit as st
import folium
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import openpyxl
from folium import Popup, Tooltip, Circle
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from utils.data_loader import load_sites
from utils.geo_utils import haversine_km
from utils.ui import render_module_header
from config.constants import TECH_COLORS, TECH_ZH, ECONOMIC_RADIUS_KM, GUOHUA_BASES_COST, TRANSPORT_MODES

EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "国内氢需求企业数据库.xlsx")
EXCEL_PATH = os.path.abspath(EXCEL_PATH)

# ── 列名映射（Excel原始列 → 显示中文）──
COL_MAP = {
    "序号": "序号", "企业名称": "企业名称", "所属集团": "所属集团",
    "省份": "省份", "城市": "城市", "行业": "行业", "子行业": "子行业",
    "用氢场景": "用氢场景", "氢气形态需求": "氢气形态需求",
    "当前用氢量(吨H2/年)": "当前用氢量(t/y)", "绿氢替代潜力(吨H2/年)": "绿氢替代潜力(t/y)",
    "需求等级": "需求等级", "需求确定性(1-5)": "需求确定性",
    "匹配集团基地": "匹配集团基地", "距最近基地预估距离(km)": "预估距离(km)",
    "关键政策驱动": "关键政策驱动", "备注/关键项目": "备注",
    "数据类型": "数据类型", "需求坐标-经度": "经度", "需求坐标-纬度": "纬度",
    "坐标描述": "坐标描述", "需求点数量": "需求点数量",
}

TYPE_COLORS = {"需求企业": "#2563eb", "加氢站": "#10b981", "政府/区域": "#f59e0b"}
TYPE_ICONS = {"需求企业": "building", "加氢站": "gas-pump", "政府/区域": "flag"}


# ═══════════════════════ EXCEL 读写 ═══════════════════════
def _read_excel() -> pd.DataFrame:
    """从 Excel 读取需求数据（header在row 3即第4行，0-indexed row 2）。"""
    if not os.path.exists(EXCEL_PATH):
        return pd.DataFrame()
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active
    # 读表头（row 3, 1-indexed）
    headers = [ws.cell(row=3, column=c).value for c in range(1, ws.max_column + 1)]
    headers = [h.strip() if h else f"col_{c}" for c, h in enumerate(headers, 1)]
    data = []
    for r in range(4, ws.max_row + 1):
        row = [ws.cell(row=r, column=c).value for c in range(1, len(headers) + 1)]
        # 跳过空行和注释行
        if row[0] is None or (isinstance(row[0], str) and row[0].strip().startswith("坐标")):
            continue
        data.append(row)
    wb.close()
    df = pd.DataFrame(data, columns=headers)
    # 清理列名中的换行
    df.columns = [c.replace('\n', '') if isinstance(c, str) else c for c in df.columns]
    # 强制转换数值列（列名已去\n）
    for col in ["当前用氢量(吨H2/年)", "绿氢替代潜力(吨H2/年)", "需求坐标-经度", "需求坐标-纬度", "需求点数量"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def _write_excel(df: pd.DataFrame):
    """将 DataFrame 写回 Excel，保留标题行和表头行。"""
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active
    # 保留 row 1-3（标题行、副标题行、表头行）不动
    # 从 row 4 开始清空并重写
    for r in range(4, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            ws.cell(row=r, column=c).value = None
    # 写入数据
    for ri, (_, row) in enumerate(df.iterrows()):
        excel_row = 4 + ri
        for ci, col_name in enumerate(df.columns):
            val = row[col_name]
            # NaN → None
            try:
                if pd.isna(val):
                    val = None
            except (TypeError, ValueError):
                pass
            ws.cell(row=excel_row, column=ci + 1).value = val
    wb.save(EXCEL_PATH); wb.close()


# ═══════════════════════ 地图渲染 ═══════════════════════
@st.cache_resource(show_spinner=False)
def _cached_demand_map(_sites_json: str, _demand_json: str):
    sites = json.loads(_sites_json)
    demand = json.loads(_demand_json)
    return _build_demand_map(sites, demand)


def _build_demand_map(sites, demand):
    m = folium.Map(location=[37.5, 113.0], zoom_start=5,
                   tiles="https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
                   attr="高德地图", control_scale=True)
    Fullscreen().add_to(m)

    # 基地标注
    for site in sites:
        color = TECH_COLORS.get(site["tech"], "#64748b")
        Circle(location=[site["lat"], site["lon"]], radius=ECONOMIC_RADIUS_KM * 1000,
               color=color, fill=True, fill_color=color,
               fill_opacity=0.06, weight=1.5, opacity=0.35).add_to(m)
        folium.Marker(location=[site["lat"], site["lon"]],
                      icon=folium.Icon(color="darkgreen", icon="industry", prefix="fa"),
                      popup=Popup(f"<b>{site['name']}</b><br>{TECH_ZH.get(site['tech'], site['tech'])}<br>¥{site['cost_avg']}/kg", max_width=180)).add_to(m)
        folium.map.Marker(location=[site["lat"] + 0.04, site["lon"]],
                          icon=folium.DivIcon(html=f'<div style="font-size:9px;font-weight:700;color:#1e293b;background:rgba(255,255,255,0.9);padding:1px 4px;border-radius:2px">🏭 {site["name"]}</div>')).add_to(m)

    # 需求点标注
    for d in demand:
        lat = d.get("lat"); lon = d.get("lon")
        if lat is None or lon is None or (not (-90 <= lat <= 90)) or (not (-180 <= lon <= 180)):
            continue
        dtype = d.get("type", "需求企业")
        c = TYPE_COLORS.get(dtype, "#94a3b8")
        ico = TYPE_ICONS.get(dtype, "info-sign")
        name = d.get("name", "—")[:25]
        popup_html = f"""
        <div style="font-family:-apple-system,sans-serif;min-width:200px">
          <h4 style="margin:0;font-size:12px">{name}</h4>
          <span style="background:{c}20;color:{c};padding:1px 6px;border-radius:3px;font-size:9px;font-weight:600">{dtype}</span>
          <hr style="margin:4px 0;border-color:#e5e7eb">
          <table style="font-size:10px;width:100%;line-height:1.5">
            <tr><td style="color:#64748b">省份/城市</td><td><b>{d.get('prov','')} · {d.get('city','')}</b></td></tr>
            <tr><td style="color:#64748b">集团</td><td>{d.get('group','')}</td></tr>
            <tr><td style="color:#64748b">行业</td><td>{d.get('industry','')}</td></tr>
            <tr><td style="color:#64748b">用氢量</td><td><b>{d.get('demand','')} t/y</b></td></tr>
            <tr><td style="color:#64748b">需求等级</td><td>{d.get('grade','')}</td></tr>
          </table>
        </div>"""
        folium.Marker(location=[lat, lon],
                      icon=folium.Icon(color={"需求企业":"blue","加氢站":"green","政府/区域":"orange"}.get(dtype,"gray"),
                                       icon=ico, prefix="fa"),
                      popup=Popup(popup_html, max_width=300),
                      tooltip=Tooltip(f"{dtype} · {name}")).add_to(m)

    # Legend
    lr = "".join(f'<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{c}"></span></td><td style="font-size:10px;color:#334155">{t}</td></tr>' for t, c in TYPE_COLORS.items())
    legend_html = f"""<div style="position:fixed;bottom:18px;right:18px;z-index:9999;background:rgba(255,255,255,0.95);padding:8px 13px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.08);line-height:1.6">
      <b style="font-size:11px;color:#1e293b">图例</b><table style="margin-top:3px">{lr}
      <tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#64748b;opacity:0.3"></span></td><td style="font-size:10px;color:#334155">200km辐射圈</td></tr></table></div>"""
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


# ═══════════════════════ 主渲染 ═══════════════════════
def render():
    render_module_header("氢基产品需求信息网络", "国内氢需求企业数据库 · 双向同步Excel · 需求企业 + 加氢站 + 政府/区域", badge="LIVE")

    # ── 加载数据 ──
    df = _read_excel()
    if df.empty:
        st.error(f"⚠️ 未找到数据文件：{EXCEL_PATH}")
        return
    sites = load_sites()

    # ── 数据统计 ──
    total = len(df)
    type_counts = df["数据类型"].value_counts()
    ent_count = type_counts.get("需求企业", 0)
    sta_count = type_counts.get("加氢站", 0)
    gov_count = type_counts.get("政府/区域", 0)
    has_coords = df["需求坐标-经度"].notna() & df["需求坐标-纬度"].notna()
    coord_count = has_coords.sum()
    total_demand = df["当前用氢量(吨H2/年)"].sum() if "当前用氢量(吨H2/年)" in df.columns else 0

    # ── KPI 行 ──
    st.markdown('<p style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.8px;margin:0 0 8px;font-weight:600">数据总览</p>', unsafe_allow_html=True)
    kpi_cols = st.columns(5)
    kpis = [
        ("📋", str(total), "数据总量", f"需求企业 {ent_count} · 加氢站 {sta_count} · 政府 {gov_count}"),
        ("🏭", str(ent_count), "需求企业", "含化工/交通/电力/冶金等"),
        ("⛽", str(sta_count), "加氢站", "已建成+在建+规划"),
        ("🗺️", str(coord_count), "含GPS坐标", f"覆盖率 {coord_count/max(total,1)*100:.0f}%"),
        ("⚡", f"{total_demand:,.0f}", "当前用氢量 t/y", "仅需求企业口径"),
    ]
    for col, (icon, val, lbl, sub) in zip(kpi_cols, kpis):
        with col:
            st.markdown(f"""<div class="metric-card">
              <div class="mc-accent-bar" style="background:#2563eb"></div>
              <div class="mc-icon">{icon}</div>
              <div class="mc-value">{val}</div>
              <div class="mc-label">{lbl}</div>
              <div class="mc-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div style="margin:16px 0"></div>', unsafe_allow_html=True)

    # ── TAB 结构 ──
    tab1, tab2, tab3 = st.tabs(["📋 数据管理", "🗺️ 需求网络地图", "📊 统计分析"])

    # ═══════════════════════ TAB 1: 数据管理 ═══════════════════════
    with tab1:
        st.info('💡 **双向同步**：在此编辑数据后点击「保存到Excel」，数据将写入Excel文件；在Excel中直接修改后刷新页面即可同步到平台。')
        c1, c2, c3 = st.columns(3)
        with c1:
            type_filter = st.multiselect("数据类型筛选", ["需求企业", "加氢站", "政府/区域"],
                                         default=["需求企业", "加氢站", "政府/区域"], key="tf")
        with c2:
            prov_filter = st.multiselect("省份筛选",
                                         sorted(df["省份"].dropna().unique().tolist()) if "省份" in df.columns else [],
                                         default=[], key="pf")
        with c3:
            search = st.text_input("🔍 企业名称搜索", "", placeholder="输入关键词...")

        disp = df.copy()
        if type_filter:
            disp = disp[disp["数据类型"].isin(type_filter)]
        if prov_filter:
            disp = disp[disp["省份"].isin(prov_filter)]
        if search:
            disp = disp[disp["企业名称"].str.contains(search, na=False)]

        st.caption(f"显示 {len(disp)} / {total} 条 | 数据源：{os.path.basename(EXCEL_PATH)} | 双击单元格编辑 · 底部可添加/删除行")

        # ── 选取展示列 ──
        show_cols = ["序号", "企业名称", "所属集团", "省份", "城市", "行业", "子行业",
                     "用氢场景", "氢气形态需求", "当前用氢量(吨H2/年)", "绿氢替代潜力(吨H2/年)",
                     "需求等级", "需求确定性(1-5)", "匹配集团基地", "距最近基地预估距离(km)",
                     "关键政策驱动", "数据类型", "需求坐标-经度", "需求坐标-纬度", "坐标描述", "需求点数量"]
        show_cols = [c for c in show_cols if c in disp.columns]

        edited = st.data_editor(
            disp[show_cols].rename(columns={k: COL_MAP.get(k, k) for k in show_cols}),
            num_rows="dynamic", use_container_width=True, height=500, key="demand_editor",
            column_config={
                "序号": st.column_config.NumberColumn(width="small"),
                "当前用氢量(t/y)": st.column_config.NumberColumn(format="%.0f"),
                "绿氢替代潜力(t/y)": st.column_config.NumberColumn(format="%.0f"),
                "需求确定性": st.column_config.NumberColumn(min_value=1, max_value=5),
                "经度": st.column_config.NumberColumn(format="%.4f"),
                "纬度": st.column_config.NumberColumn(format="%.4f"),
                "需求点数量": st.column_config.NumberColumn(width="small"),
            })

        c1, c2, c3 = st.columns([1, 1, 3])
        with c1:
            if st.button("💾 保存到Excel", type="primary", use_container_width=True):
                # 反向映射回原始列名
                rev_map = {v: k for k, v in COL_MAP.items()}
                save_df = edited.rename(columns={c: rev_map.get(c, c) for c in edited.columns})
                # 合并回完整df
                if type_filter:
                    mask = df["数据类型"].isin(type_filter)
                    if prov_filter:
                        mask = mask & df["省份"].isin(prov_filter)
                    if search:
                        mask = mask & df["企业名称"].str.contains(search, na=False)
                    # 只更新被筛选的行的展示列
                    for col in save_df.columns:
                        if col in df.columns:
                            df.loc[mask, col] = save_df[col].values
                    _write_excel(df)
                else:
                    _write_excel(save_df)
                st.success(f"✅ 已保存到 {os.path.basename(EXCEL_PATH)}")
                st.rerun()
        with c2:
            if st.button("🔄 刷新数据", use_container_width=True):
                st.rerun()
        with c3:
            st.caption(f"📁 文件路径：`{EXCEL_PATH}`")

    # ═══════════════════════ TAB 2: 需求网络地图 ═══════════════════════
    with tab2:
        map_type = st.multiselect("地图显示类型", ["需求企业", "加氢站", "政府/区域"],
                                   default=["需求企业", "加氢站"], key="mt")
        demand_for_map = []
        for _, row in df.iterrows():
            lon = row.get("需求坐标-经度"); lat = row.get("需求坐标-纬度")
            try:
                lat = float(lat) if lat is not None and not (isinstance(lat, float) and pd.isna(lat)) else None
                lon = float(lon) if lon is not None and not (isinstance(lon, float) and pd.isna(lon)) else None
            except (ValueError, TypeError):
                lat = lon = None
            if lat is None or lon is None:
                continue
            dt = str(row.get("数据类型", ""))
            if dt not in map_type:
                continue
            demand_for_map.append({
                "name": str(row.get("企业名称", "")),
                "type": dt,
                "lat": lat, "lon": lon,
                "prov": str(row.get("省份", "")),
                "city": str(row.get("城市", "")),
                "group": str(row.get("所属集团", "")),
                "industry": str(row.get("行业", "")),
                "demand": str(row.get("当前用氢量(吨H2/年)", "")),
                "grade": str(row.get("需求等级", "")),
            })

        st.caption(f"地图显示 {len(demand_for_map)} 个需求点")
        if demand_for_map:
            m = _cached_demand_map(
                json.dumps(sites, ensure_ascii=False, sort_keys=True),
                json.dumps(demand_for_map, ensure_ascii=False, sort_keys=True),
            )
            st_folium(m, width="100%", height=580, returned_objects=[])
        else:
            st.warning("所选类型无有效坐标数据")

    # ═══════════════════════ TAB 3: 统计分析 ═══════════════════════
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("行业分布")
            if "行业" in df.columns:
                ind_counts = df["行业"].value_counts().head(10)
                fig = px.bar(x=ind_counts.index, y=ind_counts.values,
                             color=ind_counts.index, color_discrete_sequence=px.colors.qualitative.Pastel,
                             labels={"x": "行业", "y": "企业数"})
                fig.update_layout(height=320, showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  font_family="-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif",
                                  xaxis=dict(tickfont=dict(size=10, color="#64748b")),
                                  yaxis=dict(tickfont=dict(size=10, color="#64748b"), gridcolor="rgba(0,0,0,0.04)"))
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("需求等级分布")
            if "需求等级" in df.columns:
                grade_counts = df["需求等级"].value_counts().reindex(["A", "B", "C", "D"])
                colors = {"A": "#ef4444", "B": "#f59e0b", "C": "#2563eb", "D": "#94a3b8"}
                fig = px.bar(x=grade_counts.index, y=grade_counts.values,
                             color=grade_counts.index,
                             color_discrete_map=colors,
                             labels={"x": "需求等级", "y": "企业数"})
                fig.update_layout(height=320, showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  font_family="-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif",
                                  xaxis=dict(tickfont=dict(size=10, color="#64748b")),
                                  yaxis=dict(tickfont=dict(size=10, color="#64748b"), gridcolor="rgba(0,0,0,0.04)"))
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("省份分布")
        if "省份" in df.columns:
            prov_counts = df["省份"].value_counts().head(15)
            fig = px.bar(x=prov_counts.index, y=prov_counts.values,
                         color=prov_counts.index, color_discrete_sequence=px.colors.qualitative.Set3,
                         labels={"x": "省份", "y": "企业/站数"})
            fig.update_layout(height=350, showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              font_family="-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif",
                              xaxis=dict(tickfont=dict(size=10, color="#64748b")),
                              yaxis=dict(tickfont=dict(size=10, color="#64748b"), gridcolor="rgba(0,0,0,0.04)"))
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("数据类型分布")
        c1, c2 = st.columns(2)
        with c1:
            if "数据类型" in df.columns:
                fig = px.pie(names=type_counts.index, values=type_counts.values,
                             color=type_counts.index,
                             color_discrete_map=TYPE_COLORS,
                             hole=0.45, height=300)
                fig.update_traces(textinfo="label+value")
                fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  font_family="-apple-system, BlinkMacSystemFont, PingFang SC, sans-serif")
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("用氢量 Top 10 企业")
            if "当前用氢量(吨H2/年)" in df.columns:
                top10 = df.nlargest(10, "当前用氢量(吨H2/年)")[["企业名称", "当前用氢量(吨H2/年)", "省份"]]
                for _, r in top10.iterrows():
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f1f5f9">
                      <span style="font-size:12px;font-weight:600;color:#0f172a">{r['企业名称'][:18]}</span>
                      <span style="font-size:10px;color:#64748b">{r.get('省份','')} · {r['当前用氢量\n(吨H2/年)']:,.0f} t/y</span>
                    </div>""", unsafe_allow_html=True)

    st.caption("v0.4.1 · 需求信息网络 · Excel 双向同步 · openpyxl 读写")
