"""数据管理页 — Excel上传 + st.data_editor编辑 + 校验"""
import streamlit as st
import pandas as pd
from io import BytesIO
from utils.data_loader import load_sites, save_sites, validate_sites
from utils.ui import render_header
from config.constants import VALID_TECH_ROUTES


COLUMN_MAP = {
    "name": "基地名称",
    "province": "省份",
    "tech": "技术路线",
    "capacity": "产能(t/y)",
    "utilization": "利用率(%)",
    "cost_low": "最低成本(¥/kg)",
    "cost_avg": "平均成本(¥/kg)",
    "cost_high": "最高成本(¥/kg)",
    "cert_status": "认证状态",
    "start_date": "投产时间",
    "contact": "联系人",
    "lat": "纬度",
    "lon": "经度",
}


def validate_uploaded_df(df: pd.DataFrame) -> list[str]:
    """Quick validation for uploaded Excel. Returns error messages."""
    errors = []
    required = ["name", "province", "lat", "lon", "tech", "capacity", "cost_low", "cost_avg", "cost_high"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"缺少必需列：{missing}")
    return errors


def render():
    lang = st.session_state.get("lang", "zh")
    render_header()

    tab1, tab2 = st.tabs(["📋 数据总览与编辑", "📤 Excel 批量导入"])

    # ═══════ Tab 1: View & Edit ═══════
    with tab1:
        sites = load_sites()
        if not sites:
            st.warning("暂无基地数据。请切换到「Excel 批量导入」上传数据，或手动添加。")
            if st.button("➕ 添加示例基地"):
                default_sites = [{
                    "name": "新基地", "province": "", "lat": 39.9, "lon": 116.4,
                    "tech": "风电+光伏电解", "capacity": 10000, "utilization": 50,
                    "cost_low": 18.0, "cost_avg": 20.0, "cost_high": 22.0,
                    "cert_status": "", "start_date": "", "contact": "",
                }]
                ok, msg = save_sites(default_sites)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)
            return

        st.caption(f"共 **{len(sites)}** 个基地 · 双击单元格编辑 · 修改后点击底部保存")

        # Convert to DataFrame for st.data_editor
        df = pd.DataFrame(sites)

        # Reorder columns: important ones first
        display_cols = ["name", "province", "tech", "capacity", "utilization",
                        "cost_low", "cost_avg", "cost_high", "cert_status",
                        "start_date", "contact", "lat", "lon"]
        display_cols = [c for c in display_cols if c in df.columns]
        df_display = df[display_cols].copy()

        # Configure columns
        col_config = {}
        for col in display_cols:
            label = COLUMN_MAP.get(col, col)
            if col == "tech":
                col_config[col] = st.column_config.SelectboxColumn(
                    label, options=VALID_TECH_ROUTES, required=True,
                )
            elif col == "cert_status":
                col_config[col] = st.column_config.SelectboxColumn(
                    label, options=["", "已获ISCC EU", "已获国内绿氢认证", "ISCC认证中", "不适用（副产氢）", "未认证"],
                )
            elif col in ("capacity", "utilization"):
                col_config[col] = st.column_config.NumberColumn(label, min_value=0, format="%d")
            elif col in ("cost_low", "cost_avg", "cost_high"):
                col_config[col] = st.column_config.NumberColumn(label, min_value=0.0, format="%.1f")
            elif col in ("lat", "lon"):
                col_config[col] = st.column_config.NumberColumn(label, format="%.4f")
            else:
                col_config[col] = st.column_config.TextColumn(label)

        edited_df = st.data_editor(
            df_display,
            column_config=col_config,
            num_rows="dynamic",
            width="stretch",
            height=420,
            key="sites_editor",
        )

        # ── Action buttons ──
        bc1, bc2, bc3 = st.columns([1, 1, 2])
        with bc1:
            if st.button("💾 保存修改", type="primary", width="stretch"):
                # Convert back
                new_sites = edited_df.to_dict(orient="records")
                # Remove empty rows
                new_sites = [s for s in new_sites if s.get("name") and str(s["name"]).strip()]
                ok, msg = save_sites(new_sites)
                if ok:
                    st.toast(msg, icon="✅")
                    st.rerun()
                else:
                    st.error(msg)
        with bc2:
            if st.button("🔄 撤销修改", width="stretch"):
                st.rerun()
        with bc3:
            st.caption(f"最后更新: {sites[0].get('updated_at', '—')[:16] if sites and sites[0].get('updated_at') else '未保存过'}")

    # ═══════ Tab 2: Excel Upload ═══════
    with tab2:
        st.markdown("""
        **Excel 导入说明**：下载模板 → 填入基地数据 → 上传 → 自动覆盖当前数据。

        必须包含列：`name, province, lat, lon, tech, capacity, cost_low, cost_avg, cost_high`
        可选列：`utilization, cert_status, start_date, contact`
        """)

        # Download template
        template_data = {
            "name": ["示例基地"],
            "province": ["省份"],
            "lat": [39.9],
            "lon": [116.4],
            "tech": ["风电+光伏电解"],
            "capacity": [10000],
            "utilization": [50],
            "cost_low": [18.0],
            "cost_avg": [20.0],
            "cost_high": [22.0],
            "cert_status": ["ISCC认证中"],
            "start_date": ["2025-01"],
            "contact": [""],
        }
        template_df = pd.DataFrame(template_data)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="基地数据")
        st.download_button(
            "📥 下载 Excel 模板",
            data=buffer.getvalue(),
            file_name="陆上氢平台_基地数据模板.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        st.markdown("---")
        uploaded = st.file_uploader("上传填好的 Excel（将覆盖当前数据）", type=["xlsx", "xls"])
        if uploaded:
            try:
                df = pd.read_excel(uploaded, engine="openpyxl")
                errs = validate_uploaded_df(df)
                if errs:
                    st.error("\n".join(errs))
                else:
                    sites_new = df.to_dict(orient="records")
                    ok, msg = save_sites(sites_new)
                    if ok:
                        st.success(msg)
                        st.toast("数据已导入，请切换到「数据总览与编辑」查看", icon="✅")
                    else:
                        st.error(msg)
            except Exception as e:
                st.error(f"读取失败：{e}")
