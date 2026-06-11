"""数据管理 — Platts风格 data workspace"""
import streamlit as st
import pandas as pd
from io import BytesIO
from utils.data_loader import load_sites, save_sites, validate_sites
from utils.ui import render_module_header
from config.constants import VALID_TECH_ROUTES

COL_MAP = {"name":"基地名称","province":"省份","tech":"技术路线","capacity":"产能(t/y)","utilization":"利用率(%)",
           "cost_low":"最低成本(¥/kg)","cost_avg":"平均成本(¥/kg)","cost_high":"最高成本(¥/kg)",
           "cert_status":"认证状态","start_date":"投产时间","contact":"联系人","lat":"纬度","lon":"经度"}
DISPLAY_COLS = ["name","province","tech","capacity","utilization","cost_low","cost_avg","cost_high",
                "cert_status","start_date","contact","lat","lon"]
CERT_OPTIONS = ["","已获ISCC EU","已获国内绿氢认证","ISCC认证中","不适用（副产氢）","未认证"]


def _column_config():
    cfg = {}
    for col in DISPLAY_COLS:
        label = COL_MAP.get(col, col)
        if col == "tech": cfg[col] = st.column_config.SelectboxColumn(label, options=VALID_TECH_ROUTES, required=True)
        elif col == "cert_status": cfg[col] = st.column_config.SelectboxColumn(label, options=CERT_OPTIONS)
        elif col in ("capacity",): cfg[col] = st.column_config.NumberColumn(label, min_value=0, format="%d")
        elif col == "utilization": cfg[col] = st.column_config.NumberColumn(label, min_value=0, max_value=100, format="%d")
        elif col in ("cost_low","cost_avg","cost_high"): cfg[col] = st.column_config.NumberColumn(label, min_value=0.0, format="%.1f")
        elif col in ("lat","lon"): cfg[col] = st.column_config.NumberColumn(label, format="%.4f")
        elif col == "start_date": cfg[col] = st.column_config.TextColumn(label, help="YYYY-MM")
        else: cfg[col] = st.column_config.TextColumn(label)
    return cfg


def _export_excel(sites):
    df = pd.DataFrame(sites)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df[[c for c in DISPLAY_COLS if c in df.columns]].to_excel(w, index=False, sheet_name="基地数据")
    buf.seek(0)
    return buf


def render():
    render_module_header("数据管理", "基地数据编辑 · Excel 导入导出 · 数据校验", badge="DATA")
    sites = load_sites()

    if not sites:
        st.warning("暂无基地数据。")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("➕ 创建示例基地", type="primary"):
                ok, msg = save_sites([{"name":"新基地","province":"","lat":39.9,"lon":116.4,"tech":"风电+光伏电解",
                                        "capacity":10000,"utilization":50,"cost_low":18.0,"cost_avg":20.0,"cost_high":22.0,
                                        "cert_status":"","start_date":"","contact":""}])
                if ok: st.rerun()
                else: st.error(msg)
        with c2:
            upl = st.file_uploader("上传 Excel", type=["xlsx","xls"], key="empty_up")
            if upl:
                try:
                    df = pd.read_excel(upl, engine="openpyxl")
                    ok, msg = save_sites(df.to_dict(orient="records"))
                    if ok: st.toast(msg, icon="✅"); st.rerun()
                    else: st.error(msg)
                except Exception as e: st.error(f"读取失败: {e}")
        return

    tab1, tab2 = st.tabs(["📋 数据编辑", "📤 导入 / 导出"])

    with tab1:
        st.caption(f"共 **{len(sites)}** 个基地 · 双击编辑 · 底部可添加行 · 修改后保存")
        df = pd.DataFrame(sites)
        display = df[[c for c in DISPLAY_COLS if c in df.columns]].copy()
        edited = st.data_editor(display, column_config=_column_config(),
                                num_rows="dynamic", width="stretch", height=420, key="editor")

        bc1, bc2, bc3, bc4 = st.columns([1, 1, 1, 1.5])
        with bc1:
            if st.button("💾 保存修改", type="primary", width="stretch"):
                new_sites = edited.to_dict(orient="records")
                new_sites = [s for s in new_sites if s.get("name") and str(s["name"]).strip()]
                ok, msg = save_sites(new_sites)
                if ok: st.toast(msg, icon="✅"); st.rerun()
                else: st.error(msg)
        with bc2:
            if st.button("🔄 撤销", width="stretch"): st.rerun()
        with bc3:
            st.download_button("📥 导出 Excel", data=_export_excel(sites),
                               file_name="陆上氢平台_基地数据.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
        with bc4:
            ts = sites[0].get("updated_at","—")[:16] if sites else "—"
            st.caption(f"📅 更新: {ts}")

    with tab2:
        st.subheader("📤 Excel 批量导入")
        st.markdown("下载模板 → 填入数据 → 上传 → 预览 → 确认覆盖。必需列: `name, province, lat, lon, tech, capacity, cost_low, cost_avg, cost_high`")
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            pd.DataFrame({"name":["示例"],"province":[""],"lat":[39.9],"lon":[116.4],"tech":["风电+光伏电解"],
                          "capacity":[10000],"utilization":[50],"cost_low":[18.0],"cost_avg":[20.0],"cost_high":[22.0],
                          "cert_status":[""],"start_date":[""],"contact":[""]}).to_excel(w, index=False, sheet_name="基地数据")
        st.download_button("📥 下载模板", data=buf.getvalue(), file_name="基地数据模板.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.markdown("---")
        upl = st.file_uploader("上传填好的 Excel（覆盖当前数据）", type=["xlsx","xls"], key="main_up")
        if upl:
            try:
                df = pd.read_excel(upl, engine="openpyxl")
                req = ["name","province","lat","lon","tech","capacity","cost_low","cost_avg","cost_high"]
                miss = [c for c in req if c not in df.columns]
                if miss: st.error(f"缺少列: {miss}")
                else:
                    st.success(f"格式正确，共 **{len(df)}** 条。确认后覆盖当前数据。")
                    st.dataframe(df, width="stretch", hide_index=True)
                    if st.button("⚠️ 确认导入（覆盖）", type="primary"):
                        ok, msg = save_sites(df.to_dict(orient="records"))
                        if ok: st.toast(msg, icon="✅"); st.rerun()
                        else: st.error(msg)
            except Exception as e: st.error(f"读取失败: {e}")

        st.markdown("---")
        st.subheader("📥 数据导出")
        st.caption("下载当前全部基地数据为 Excel。")
        st.download_button("📥 下载当前数据", data=_export_excel(sites),
                           file_name=f"陆上氢平台_基地数据_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
