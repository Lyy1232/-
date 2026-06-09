"""数据管理页 — Excel上传 + 手动录入 + 参数配置"""
import streamlit as st
import pandas as pd
import json
from pathlib import Path
from utils.ui import render_header

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SITES_FILE = PROJECT_ROOT / "config" / "sites.json"


def load_sites():
    with open(SITES_FILE, "r") as f:
        return json.load(f)


def render():
    lang = st.session_state.get("lang", "zh")
    render_header()

    st.subheader("供给端数据管理")

    tab1, tab2, tab3 = st.tabs(["📋 基地数据总览", "📤 Excel 批量上传", "✏️ 手动编辑"])

    # ── Tab 1: Overview ──
    with tab1:
        sites = load_sites()
        df = pd.DataFrame(sites)
        df_display = df.rename(columns={
            "name": "基地名称", "province": "省份", "tech": "技术路线",
            "capacity": "产能(t/y)", "cost_low": "最低成本(¥/kg)",
            "cost_avg": "平均成本(¥/kg)", "cost_high": "最高成本(¥/kg)",
            "lat": "纬度", "lon": "经度"
        })
        st.dataframe(df_display, width="stretch", hide_index=True)
        st.caption(f"数据源：`config/sites.json` · 共 {len(sites)} 个基地")

    # ── Tab 2: Excel Upload ──
    with tab2:
        st.markdown("""
        **Excel 模板格式**：必须包含以下列：
        `name, province, lat, lon, tech, capacity, cost_low, cost_avg, cost_high`

        下载模板后填入数据，上传即可批量更新基地信息。
        """)

        # Generate template
        template_df = pd.DataFrame(columns=[
            "name", "province", "lat", "lon", "tech",
            "capacity", "cost_low", "cost_avg", "cost_high"
        ])
        template_row = {
            "name": "示例基地", "province": "省份", "lat": 39.9, "lon": 116.4,
            "tech": "风电电解", "capacity": 10000,
            "cost_low": 18.0, "cost_avg": 20.0, "cost_high": 22.0
        }
        template_df.loc[0] = template_row

        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="基地数据")
        st.download_button(
            "📥 下载 Excel 模板",
            data=buffer.getvalue(),
            file_name="基地数据模板.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        uploaded = st.file_uploader("上传填好的 Excel", type=["xlsx", "xls"])
        if uploaded:
            try:
                df = pd.read_excel(uploaded, engine="openpyxl")
                required = ["name", "province", "lat", "lon", "tech", "capacity", "cost_low", "cost_avg", "cost_high"]
                missing = [c for c in required if c not in df.columns]
                if missing:
                    st.error(f"缺少必需列：{missing}")
                else:
                    sites_new = df.to_dict(orient="records")
                    with open(SITES_FILE, "w") as f:
                        json.dump(sites_new, f, ensure_ascii=False, indent=2)
                    st.success(f"已更新 {len(sites_new)} 个基地数据。刷新地图页面查看。")
            except Exception as e:
                st.error(f"读取失败：{e}")

    # ── Tab 3: Manual Edit ──
    with tab3:
        sites = load_sites()
        for i, site in enumerate(sites):
            with st.expander(f"{site['name']} — {site['province']} · {site['tech']}", expanded=(i == 0)):
                c1, c2, c3 = st.columns(3)
                with c1:
                    site["name"] = st.text_input("名称", site["name"], key=f"name_{i}")
                    site["province"] = st.text_input("省份", site["province"], key=f"prov_{i}")
                    site["tech"] = st.text_input("技术路线", site["tech"], key=f"tech_{i}")
                with c2:
                    site["lat"] = st.number_input("纬度", value=site["lat"], format="%.4f", key=f"lat_{i}")
                    site["lon"] = st.number_input("经度", value=site["lon"], format="%.4f", key=f"lon_{i}")
                    site["capacity"] = st.number_input("产能(t/y)", value=int(site["capacity"]), key=f"cap_{i}")
                with c3:
                    site["cost_low"] = st.number_input("最低成本 ¥/kg", value=site["cost_low"], key=f"clo_{i}")
                    site["cost_avg"] = st.number_input("平均成本 ¥/kg", value=site["cost_avg"], key=f"cav_{i}")
                    site["cost_high"] = st.number_input("最高成本 ¥/kg", value=site["cost_high"], key=f"chi_{i}")

        if st.button("💾 保存修改", width="stretch"):
            with open(SITES_FILE, "w") as f:
                json.dump(sites, f, ensure_ascii=False, indent=2)
            st.success("已保存。")
            st.rerun()
