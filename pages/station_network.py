"""氢基产品需求信息网络 — 数据源：国内氢需求企业数据库 Excel · 双向同步"""
import os, json
import streamlit as st
import folium
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import openpyxl
from folium import Popup, Tooltip, Circle
from folium.plugins import Fullscreen, MarkerCluster
from streamlit_folium import st_folium
from utils.data_loader import load_sites
from utils.ui import render_module_header
from config.constants import TECH_COLORS, TECH_ZH, ECONOMIC_RADIUS_KM

EXCEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "国内氢需求企业数据库.xlsx"))

# ── 原始列名（Excel header row 3），用于读取/写入 ──
RAW_COLS = [
    "序号","企业名称","所属集团","省份","城市","行业","子行业",
    "用氢场景","氢气形态需求","当前用氢量\n(吨H2/年)","绿氢替代潜力\n(吨H2/年)",
    "需求等级","需求确定性\n(1-5)","匹配集团基地","距最近基地\n预估距离(km)",
    "关键政策驱动","备注/关键项目","数据类型","需求坐标-经度","需求坐标-纬度",
    "坐标描述","需求点数量",
]
# 去\n 后的列名（DataFrame 内部使用）
CLEAN_COLS = [c.replace('\n','') if isinstance(c,str) else c for c in RAW_COLS]

# ── 显示列（含去\n版）→ 显示中文 ──
SHOW_COLS = ["序号","企业名称","所属集团","省份","城市","行业","子行业",
             "用氢场景","氢气形态需求","当前用氢量(吨H2/年)","绿氢替代潜力(吨H2/年)",
             "需求等级","需求确定性(1-5)","匹配集团基地","距最近基地预估距离(km)",
             "关键政策驱动","数据类型","需求坐标-经度","需求坐标-纬度","坐标描述","需求点数量"]

COL_LABELS = {
    "序号":"序号","企业名称":"企业名称","所属集团":"所属集团",
    "省份":"省份","城市":"城市","行业":"行业","子行业":"子行业",
    "用氢场景":"用氢场景","氢气形态需求":"氢气形态需求",
    "当前用氢量(吨H2/年)":"当前用氢量(t/y)","绿氢替代潜力(吨H2/年)":"绿氢替代潜力(t/y)",
    "需求等级":"需求等级","需求确定性(1-5)":"需求确定性",
    "匹配集团基地":"匹配集团基地","距最近基地预估距离(km)":"预估距离(km)",
    "关键政策驱动":"关键政策驱动","数据类型":"数据类型",
    "需求坐标-经度":"经度","需求坐标-纬度":"纬度",
    "坐标描述":"坐标描述","需求点数量":"需求点数量",
}

TYPE_COLORS = {"需求企业":"#2563eb","加氢站":"#10b981","政府/区域":"#f59e0b"}
TYPE_ICONS  = {"需求企业":"building","加氢站":"gas-pump","政府/区域":"flag"}
ICON_COLORS = {"需求企业":"blue","加氢站":"green","政府/区域":"orange"}


# ═══════════════════════ EXCEL 读写 ═══════════════════════
@st.cache_data(show_spinner=False, ttl=10)
def _read_excel_cached(_path: str) -> pd.DataFrame:
    """缓存读取，ttl=10s 保证 Excel 改动后快速同步。"""
    return _read_excel_raw()


def _read_excel_raw() -> pd.DataFrame:
    if not os.path.exists(EXCEL_PATH):
        return pd.DataFrame()
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active
    headers = [ws.cell(row=3, column=c).value for c in range(1, len(RAW_COLS)+1)]
    headers = [h.strip() if isinstance(h,str) else (h or f"c{i}") for i,h in enumerate(headers)]
    data = []
    for r in range(4, ws.max_row + 1):
        row = [ws.cell(row=r, column=c).value for c in range(1, len(headers)+1)]
        v0 = row[0]
        if v0 is None: continue
        if isinstance(v0, str) and (v0.strip().startswith("坐标") or v0.strip().startswith("排序")):
            continue
        data.append(row)
    wb.close()
    df = pd.DataFrame(data, columns=headers)
    # 统一列名为去\n版
    df.columns = [c.replace('\n','') if isinstance(c,str) else c for c in df.columns]
    # 数值转换
    num_cols = ["当前用氢量(吨H2/年)","绿氢替代潜力(吨H2/年)","需求坐标-经度","需求坐标-纬度","需求点数量"]
    for c in num_cols:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')
    return df


def _write_excel(df: pd.DataFrame):
    """全量写回 Excel，保留标题/副标题/表头（row 1-3）。"""
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active
    # 清空旧数据 row 4+
    for r in range(4, ws.max_row + 1):
        for c in range(1, len(RAW_COLS) + 1):
            ws.cell(row=r, column=c).value = None
    # 写入新数据（用原始列名）
    for ri, (_, row) in enumerate(df.iterrows()):
        for ci, raw_col in enumerate(RAW_COLS):
            clean_col = raw_col.replace('\n','') if isinstance(raw_col,str) else raw_col
            val = row.get(clean_col)
            try:
                if pd.isna(val): val = None
            except (TypeError, ValueError): pass
            ws.cell(row=4 + ri, column=ci + 1).value = val
    wb.save(EXCEL_PATH); wb.close()
    _read_excel_cached.clear()  # 刷新缓存


# ═══════════════════════ 地图 ═══════════════════════
def _build_map_html(sites, demand_rows):
    """非缓存版地图构建，接收 demand_rows list of dict。"""
    m = folium.Map(location=[37.5, 113.0], zoom_start=5,
                   tiles="https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
                   attr="高德地图", control_scale=True)
    Fullscreen().add_to(m)

    # 基地 + 辐射圈
    for site in sites:
        color = TECH_COLORS.get(site.get("tech",""), "#64748b")
        Circle([site["lat"],site["lon"]], radius=ECONOMIC_RADIUS_KM*1000,
               color=color, fill=True, fill_color=color, fill_opacity=0.06, weight=1.5, opacity=0.35).add_to(m)
        folium.Marker([site["lat"],site["lon"]],
                      icon=folium.Icon(color="darkgreen", icon="industry", prefix="fa"),
                      popup=Popup(f"<b>{site['name']}</b><br>{TECH_ZH.get(site.get('tech',''),site.get('tech',''))}<br>¥{site.get('cost_avg','')}/kg", max_width=180)).add_to(m)
        folium.map.Marker([site["lat"]+0.04, site["lon"]],
                          icon=folium.DivIcon(html=f'<div style="font-size:9px;font-weight:700;color:#1e293b;background:rgba(255,255,255,0.9);padding:1px 4px;border-radius:2px">🏭 {site["name"]}</div>')).add_to(m)

    # 需求点 MarkerCluster（360点也流畅）
    cluster = MarkerCluster(name="需求点").add_to(m)
    for d in demand_rows:
        lat, lon = d.get("lat"), d.get("lon")
        if lat is None or lon is None: continue
        if not (-90<=lat<=90 and -180<=lon<=180): continue
        dt = d.get("type","需求企业")
        c = TYPE_COLORS.get(dt,"#94a3b8")
        popup = f"""<div style="font-family:-apple-system,sans-serif;min-width:200px">
          <h4 style="margin:0;font-size:12px">{d.get('name','')[:25]}</h4>
          <span style="background:{c}20;color:{c};padding:1px 6px;border-radius:3px;font-size:9px;font-weight:600">{dt}</span>
          <hr style="margin:4px 0"><table style="font-size:10px;line-height:1.5">
          <tr><td style="color:#64748b">省份</td><td><b>{d.get('prov','')} · {d.get('city','')}</b></td></tr>
          <tr><td style="color:#64748b">集团</td><td>{d.get('group','')}</td></tr>
          <tr><td style="color:#64748b">行业</td><td>{d.get('industry','')}</td></tr>
          <tr><td style="color:#64748b">用氢量</td><td><b>{d.get('demand','')} t/y</b></td></tr>
          <tr><td style="color:#64748b">需求等级</td><td>{d.get('grade','')}</td></tr>
          </table></div>"""
        folium.Marker([lat,lon],
                      icon=folium.Icon(color=ICON_COLORS.get(dt,"gray"), icon=TYPE_ICONS.get(dt,"info-sign"), prefix="fa"),
                      popup=Popup(popup, max_width=300),
                      tooltip=Tooltip(f"{dt} · {d.get('name','')[:20]}")).add_to(cluster)

    # Legend
    lr = "".join(f'<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{c}"></span></td><td style="font-size:10px;color:#334155">{t}</td></tr>' for t,c in TYPE_COLORS.items())
    m.get_root().html.add_child(folium.Element(f"""<div style="position:fixed;bottom:18px;right:18px;z-index:9999;background:rgba(255,255,255,0.95);padding:8px 13px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.08);line-height:1.6">
      <b style="font-size:11px;color:#1e293b">图例</b><table style="margin-top:3px">{lr}</table></div>"""))
    return m


# ═══════════════════════ RENDER ═══════════════════════
def render():
    render_module_header("氢基产品需求信息网络", "国内氢需求企业数据库 · 双向同步Excel · 需求企业+加氢站+政府/区域", badge="LIVE")

    df = _read_excel_cached(EXCEL_PATH)
    if df.empty:
        st.error(f"⚠️ 未找到数据文件：{EXCEL_PATH}")
        return
    sites = load_sites()
    total = len(df)

    # ── 基本统计 ──
    tc = df["数据类型"].value_counts()
    ent_c, sta_c, gov_c = tc.get("需求企业",0), tc.get("加氢站",0), tc.get("政府/区域",0)
    coord_ok = (df["需求坐标-经度"].notna() & df["需求坐标-纬度"].notna()).sum()
    total_h2 = df["当前用氢量(吨H2/年)"].sum() if "当前用氢量(吨H2/年)" in df.columns else 0

    st.markdown('<p style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.8px;margin:0 0 8px;font-weight:600">数据总览</p>', unsafe_allow_html=True)
    for col,(ico,val,lab,sub) in zip(st.columns(5),[
        ("📋",str(total),"数据总量",f"需求企业 {ent_c} · 加氢站 {sta_c} · 政府 {gov_c}"),
        ("🏭",str(ent_c),"需求企业","化工/交通/电力/冶金等"),
        ("⛽",str(sta_c),"加氢站","已建成+在建+规划"),
        ("🗺️",str(coord_ok),"含GPS坐标",f"覆盖率 {coord_ok/max(total,1)*100:.0f}%"),
        ("⚡",f"{total_h2:,.0f}","当前用氢量 t/y","需求企业口径"),
    ]):
        with col:
            st.markdown(f"""<div class="metric-card"><div class="mc-accent-bar" style="background:#2563eb"></div><div class="mc-icon">{ico}</div><div class="mc-value">{val}</div><div class="mc-label">{lab}</div><div class="mc-sub">{sub}</div></div>""", unsafe_allow_html=True)

    st.markdown('<div style="margin:16px 0"></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 数据管理","🗺️ 需求网络地图","📊 统计分析"])

    # ═══════════════════ TAB 1: 数据管理 ═══════════════════
    with tab1:
        st.info('💡 **双向同步**：修改后点击「保存到Excel」写入文件；在 Excel 中直接编辑后刷新页面即同步。')
        c1,c2,c3 = st.columns(3)
        with c1:
            tf = st.multiselect("数据类型筛选",["需求企业","加氢站","政府/区域"],
                                default=["需求企业","加氢站","政府/区域"], key="dem_tf")
        with c2:
            provs = sorted(df["省份"].dropna().unique().tolist()) if "省份" in df.columns else []
            pf = st.multiselect("省份筛选", provs, default=[], key="dem_pf")
        with c3:
            kw = st.text_input("🔍 企业名称搜索","",placeholder="输入关键词...", key="dem_kw")

        disp = df.copy()
        if tf: disp = disp[disp["数据类型"].isin(tf)]
        if pf: disp = disp[disp["省份"].isin(pf)]
        if kw: disp = disp[disp["企业名称"].str.contains(kw, na=False)]

        st.caption(f"显示 {len(disp)} / {total} 条 | 双击编辑 · 底部可增删行")

        avail = [c for c in SHOW_COLS if c in disp.columns]
        edited = st.data_editor(
            disp[avail].rename(columns=COL_LABELS),
            num_rows="dynamic", use_container_width=True, height=500, key="dem_editor",
            column_config={
                "序号": st.column_config.NumberColumn(width="small"),
                "当前用氢量(t/y)": st.column_config.NumberColumn(format="%.0f"),
                "绿氢替代潜力(t/y)": st.column_config.NumberColumn(format="%.0f"),
                "需求确定性": st.column_config.NumberColumn(min_value=1,max_value=5),
                "经度": st.column_config.NumberColumn(format="%.4f"),
                "纬度": st.column_config.NumberColumn(format="%.4f"),
                "需求点数量": st.column_config.NumberColumn(width="small"),
            })

        c1,c2,c3 = st.columns([1,1,3])
        with c1:
            if st.button("💾 保存到Excel", type="primary", use_container_width=True, key="dem_save"):
                # 反向映射显示名→原始列名
                rev = {v:k for k,v in COL_LABELS.items()}
                saved = edited.rename(columns={c: rev.get(c,c) for c in edited.columns})
                # 简化：全量写回（取展示列与完整df对齐）
                # 先合并回完整df（仅更新展示列）
                for cc in saved.columns:
                    if cc in df.columns:
                        # 对齐行：saved行数==disp行数
                        if len(saved) == len(disp):
                            df.loc[disp.index, cc] = saved[cc].values
                _write_excel(df)
                st.success(f"✅ 已保存到 Excel · {len(saved)} 行")
                st.rerun()
        with c2:
            if st.button("🔄 刷新", use_container_width=True, key="dem_refresh"):
                _read_excel_cached.clear()
                st.rerun()
        with c3:
            st.caption(f"📁 `{os.path.basename(EXCEL_PATH)}`")

    # ═══════════════════ TAB 2: 地图 ═══════════════════
    with tab2:
        mt = st.multiselect("地图显示类型",["需求企业","加氢站","政府/区域"],
                            default=["需求企业","加氢站"], key="dem_mt")
        rows = []
        for _, r in df.iterrows():
            lon_val = r.get("需求坐标-经度"); lat_val = r.get("需求坐标-纬度")
            try:
                lon_val = float(lon_val) if lon_val is not None and not (isinstance(lon_val,float) and pd.isna(lon_val)) else None
                lat_val = float(lat_val) if lat_val is not None and not (isinstance(lat_val,float) and pd.isna(lat_val)) else None
            except: lon_val = lat_val = None
            if lat_val is None or lon_val is None: continue
            dt = str(r.get("数据类型",""))
            if dt not in mt: continue
            rows.append(dict(name=str(r.get("企业名称","")),type=dt,lat=lat_val,lon=lon_val,
                             prov=str(r.get("省份","")),city=str(r.get("城市","")),
                             group=str(r.get("所属集团","")),industry=str(r.get("行业","")),
                             demand=str(r.get("当前用氢量(吨H2/年)","")),grade=str(r.get("需求等级",""))))
        st.caption(f"地图显示 {len(rows)} 个需求点（MarkerCluster 聚合）")
        if rows:
            m = _build_map_html(sites, rows)
            st_folium(m, width="100%", height=580, returned_objects=[])
        else:
            st.warning("所选类型无有效坐标")

    # ═══════════════════ TAB 3: 统计 ═══════════════════
    with tab3:
        c1,c2 = st.columns(2)
        with c1:
            st.subheader("行业分布")
            if "行业" in df.columns:
                ic = df["行业"].value_counts().head(10)
                fig = px.bar(x=ic.index,y=ic.values,color=ic.index,
                             color_discrete_sequence=px.colors.qualitative.Pastel,
                             labels={"x":"行业","y":"企业数"})
                fig.update_layout(height=320,showlegend=False,plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig,use_container_width=True)
        with c2:
            st.subheader("需求等级分布")
            if "需求等级" in df.columns:
                gc = df["需求等级"].value_counts().reindex(["A","B","C","D"])
                fig = px.bar(x=gc.index,y=gc.values,color=gc.index,
                             color_discrete_map={"A":"#ef4444","B":"#f59e0b","C":"#2563eb","D":"#94a3b8"},
                             labels={"x":"需求等级","y":"企业数"})
                fig.update_layout(height=320,showlegend=False,plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig,use_container_width=True)

        st.subheader("省份分布")
        if "省份" in df.columns:
            pc = df["省份"].value_counts().head(15)
            fig = px.bar(x=pc.index,y=pc.values,color=pc.index,
                         color_discrete_sequence=px.colors.qualitative.Set3,
                         labels={"x":"省份","y":"企业/站数"})
            fig.update_layout(height=350,showlegend=False,plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,use_container_width=True)

        c1,c2 = st.columns(2)
        with c1:
            st.subheader("数据类型分布")
            fig = px.pie(names=tc.index,values=tc.values,color=tc.index,
                         color_discrete_map=TYPE_COLORS,hole=0.45,height=300)
            fig.update_traces(textinfo="label+value")
            fig.update_layout(showlegend=False,plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,use_container_width=True)
        with c2:
            st.subheader("用氢量 Top 10")
            if "当前用氢量(吨H2/年)" in df.columns:
                t10 = df.nlargest(10, "当前用氢量(吨H2/年)")
                for _, r in t10.iterrows():
                    h2val = r.get("当前用氢量(吨H2/年)",0)
                    st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f1f5f9">
                      <span style="font-size:12px;font-weight:600;color:#0f172a">{str(r.get('企业名称',''))[:18]}</span>
                      <span style="font-size:10px;color:#64748b">{r.get('省份','')} · {h2val:,.0f} t/y</span>
                    </div>""", unsafe_allow_html=True)

    st.caption("v0.4.2 · 需求信息网络 · 全量重写修复 · MarkerCluster")
