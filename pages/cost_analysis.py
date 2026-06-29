"""成本竞争力分析 — 运输成本计算器 · 到站成本对比 · 情景模拟"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from utils.data_loader import load_sites, load_stations_from_db, load_trading_snapshots
from utils.geo_utils import haversine_km
from utils.ui import render_module_header
from config.constants import TECH_COLORS, TECH_ZH, ECONOMIC_RADIUS_KM

TEAL = "#0d9488"
RED = "#ef4444"
GREEN = "#10b981"
BLUE = "#2563eb"
AMBER = "#f59e0b"

# ── 国华基地基准成本（来源：绿氨竞争力模型 model.xlsx + 项目参数）──
GUOHUA_BASES = {
    "赤城风电制氢": {"lat": 40.90, "lon": 115.83, "cost": 15.2, "tech": "风电电解",
        "capacity": 1428, "elec_price": 0.20, "note": "风电直供电解水 · 电价28$/MWh · 电解效率45kWh/kg"},
    "宁东光伏制氢": {"lat": 38.15, "lon": 106.60, "cost": 15.2, "tech": "光伏电解",
        "capacity": 3080, "elec_price": 0.20, "note": "光伏+电解水 · 清水营一期3080t/y · CCER路径可选"},
    "沧州副产氢": {"lat": 38.30, "lon": 116.84, "cost": 9.6, "tech": "工业副产氢",
        "capacity": 6500, "elec_price": None, "note": "化工副产提纯 · 蓝氨路径折氢9.6元/kg"},
    "蒙西风电制氢(规划)": {"lat": 40.20, "lon": 107.00, "cost": 11.2, "tech": "风电电解",
        "capacity": 10000, "elec_price": 0.14, "note": "蒙西低电价基地 · 电价20$/MWh · 甘其毛都-黄骅港铁路"},
}


def compute_landed_cost(base_cost: float, distance_km: float, transport_rate: float = 10.0) -> float:
    """计算到站成本 = 出厂成本 + 运输成本"""
    return base_cost + distance_km * transport_rate / 100


def find_best_guohua_match(station_lat: float, station_lon: float, transport_rate: float = 10.0) -> dict | None:
    """找到距离最近的国华基地并计算到站成本"""
    best = None
    best_dist = float("inf")
    for name, info in GUOHUA_BASES.items():
        dist = haversine_km(station_lat, station_lon, info["lat"], info["lon"])
        if dist < best_dist:
            best_dist = dist
            best = {
                "base_name": name,
                "distance_km": round(dist, 1),
                "base_cost": info["cost"],
                "landed_cost": round(compute_landed_cost(info["cost"], dist, transport_rate), 1),
                "tech": info["tech"],
                "in_radius": dist <= ECONOMIC_RADIUS_KM,
            }
    return best


def render():
    render_module_header("成本竞争力分析", "运输成本计算 · 到站价格对比 · 情景模拟", badge="COST")

    sites = load_sites()
    stations = load_stations_from_db(year=4)
    if not stations:
        st.warning("请先运行 python utils/build_sqlite.py 构建数据库")
        return

    # ═══════════ 页级参数配置 ═══════════
    with st.expander("⚙️ 参数配置", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            transport_rate = st.slider("气态运氢成本 (元/100km·kg)", 5, 20, 10, 1)
        with c2:
            carbon_price = st.slider("碳价 (元/tCO₂)", 50, 200, 90, 10)
        with c3:
            green_premium = st.slider("绿氢溢价 (元/kg)", 0, 10, 3, 1)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🚛 运输成本计算器", "📊 到站成本竞争力", "🔄 情景模拟", "🏭 基地成本对标"
    ])

    # ═══════════ TAB 1: 运输成本计算器 ═══════════
    with tab1:
        st.subheader("陆路运输成本计算器")
        st.caption(f"基于高压气态运氢 {transport_rate}元/100km·kg")

        col1, col2 = st.columns([1, 1])
        with col1:
            base_name = st.selectbox("选择国华基地", list(GUOHUA_BASES.keys()))
            base = GUOHUA_BASES[base_name]
            st.metric("出厂成本", f"{base['cost']} 元/kg", delta=f"技术: {TECH_ZH.get(base['tech'], base['tech'])}")
            st.caption(f"📝 {base['note']}")

            manual_dist = st.number_input("输入运输距离 (km)", 0, 500, 100, 10)
            landed = compute_landed_cost(base["cost"], manual_dist, transport_rate)
            transport_fee = manual_dist * transport_rate / 100

        with col2:
            st.markdown(f"""
            <div class="data-card" style="text-align:center;padding:30px">
              <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">到站成本估算</div>
              <div style="font-size:3rem;font-weight:900;color:{TEAL};line-height:1">{landed:.1f}</div>
              <div style="font-size:14px;color:#64748b;margin-top:4px">元/kg</div>
              <hr style="margin:16px 0;border-color:#e5e7eb">
              <table style="width:100%;font-size:12px;text-align:left">
                <tr><td style="color:#64748b">出厂成本</td><td style="font-weight:700">{base['cost']} 元/kg</td></tr>
                <tr><td style="color:#64748b">运输距离</td><td style="font-weight:700">{manual_dist} km</td></tr>
                <tr><td style="color:#64748b">运输费用</td><td style="font-weight:700">{transport_fee:.1f} 元/kg</td></tr>
                <tr><td style="color:#64748b">运输占比</td><td style="font-weight:700">{transport_fee/landed*100:.0f}%</td></tr>
              </table>
            </div>
            """, unsafe_allow_html=True)

        # 距离-成本曲线
        fig = go.Figure()
        dists = list(range(0, 501, 10))
        fig.add_trace(go.Scatter(
            x=dists, y=[compute_landed_cost(base["cost"], d, transport_rate) for d in dists],
            mode="lines", fill="tozeroy", fillcolor=f"rgba(13,148,136,0.08)",
            line=dict(color=TEAL, width=3),
            name="到站成本曲线",
        ))
        fig.add_hline(y=base["cost"], line_dash="dash", line_color="#94a3b8",
                      annotation=dict(text=f"出厂成本 {base['cost']}元/kg", font_size=10))
        fig.add_vline(x=200, line_dash="dot", line_color=AMBER,
                      annotation=dict(text="经济半径 200km", font_size=10))
        fig.update_layout(
            title=f"{base_name} → 到站成本随距离变化", height=380,
            xaxis_title="运输距离 (km)", yaxis_title="到站成本 (元/kg)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ═══════════ TAB 2: 到站成本竞争力 ═══════════
    with tab2:
        st.subheader("国华基地 vs 当前市场 · 到站成本竞争力")
        st.caption("对每个加氢站计算最近国华基地的到站成本，与当前零售价对比")

        # 为每个站点计算最佳国华匹配
        rows = []
        for s in stations:
            lat, lon = s.get("lat"), s.get("lon")
            if not lat or not lon:
                continue
            match = find_best_guohua_match(lat, lon, transport_rate)
            if not match:
                continue
            current_price = s.get("purchase_price_low") or s.get("retail_price")
            cost_advantage = (current_price - match["landed_cost"]) if current_price else None
            rows.append({
                "station": s.get("name", "")[:25],
                "cluster": s.get("city_cluster", ""),
                "city": s.get("province", ""),
                "base": match["base_name"],
                "distance_km": match["distance_km"],
                "in_radius": match["in_radius"],
                "guohua_landed": match["landed_cost"],
                "current_price": current_price,
                "advantage": cost_advantage,
            })

        df = pd.DataFrame(rows)
        if df.empty:
            st.info("暂无数据")
            return

        # 统计
        in_radius = df[df["in_radius"]]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("辐射圈内站点", f"{len(in_radius)} 座", delta=f"/ {len(df)} 总站")
        with col2:
            has_price = df[df["current_price"].notna() & (df["current_price"] > 0)]
            adv_count = len(has_price[has_price["advantage"] > 0])
            st.metric("成本优势站", f"{adv_count} 座", delta=f"{adv_count/max(len(has_price),1)*100:.0f}%")
        with col3:
            avg_adv = has_price["advantage"].mean() if len(has_price) > 0 else 0
            st.metric("平均成本优势", f"{avg_adv:+.1f} 元/kg")

        # 散点图：到站成本 vs 当前价格
        fig = go.Figure()
        valid = df[df["current_price"].notna() & (df["current_price"] > 0)].copy()
        valid["color"] = valid["advantage"].apply(lambda x: GREEN if x > 0 else RED)
        fig.add_trace(go.Scatter(
            x=valid["current_price"], y=valid["guohua_landed"],
            mode="markers", marker=dict(size=8, color=valid["color"], opacity=0.7),
            text=[f"<b>{r['station']}</b><br>{r['cluster']}<br>当前价:{r['current_price']}→国华到站:{r['guohua_landed']}<br>优势:{r['advantage']:+.1f}元/kg" for _, r in valid.iterrows()],
            hoverinfo="text",
        ))
        # 对角线：y=x
        mx = max(valid["current_price"].max(), valid["guohua_landed"].max()) + 5
        fig.add_trace(go.Scatter(x=[0, mx], y=[0, mx], mode="lines",
                                line=dict(color="#cbd5e1", dash="dash", width=1),
                                name="价格相等线"))
        fig.update_layout(
            title="到站成本 vs 当前零售价 · 绿=国华有优势 · 红=无优势", height=450,
            xaxis_title="当前零售价 (元/kg)", yaxis_title="国华到站成本 (元/kg)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        # 辐射圈内详细表
        st.markdown("### 辐射圈内站点详情")
        st.dataframe(
            in_radius.rename(columns={
                "station": "站名", "cluster": "城市群", "city": "城市",
                "base": "最近基地", "distance_km": "距离(km)",
                "guohua_landed": "国华到站价", "current_price": "当前零售价",
                "advantage": "成本优势",
            }),
            use_container_width=True, hide_index=True,
            column_config={"成本优势": st.column_config.NumberColumn(format="+.1f 元/kg")}
        )

    # ═══════════ TAB 3: 情景模拟 ═══════════
    with tab3:
        st.subheader("情景模拟 · 参数对到站成本的影响")
        st.caption("调整电价、碳价、运输成本，观察各项指标变化")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            elec_price = st.slider("电价 (元/kWh)", 0.15, 0.50, 0.30, 0.01,
                                   help="风电/光伏度电成本")
        with c2:
            sim_carbon = st.slider("碳价 (元/tCO₂)", 0, 300, carbon_price, 10)
        with c3:
            sim_transport = st.slider("运输成本 (元/100km·kg)", 5, 20, transport_rate, 1)
        with c4:
            sim_target = st.slider("目标售价 (元/kg)", 20, 50, 30, 1,
                                   help="加氢站可接受的购氢价格")

        # 重新计算四大基地到站成本
        st.markdown("#### 四大基地到站成本模拟")
        sim_rows = []
        for name, info in GUOHUA_BASES.items():
            # 电价敏感型：电解水制氢（45度/kg，来源：绿氨模型 model.xlsx）
            if "电解" in info.get("tech", ""):
                sim_cost = info["cost"] + (elec_price - (info.get("elec_price") or 0.20)) * 45
            else:
                sim_cost = info["cost"]  # 副产氢对电价不敏感

            # 碳价影响：绿氢有碳信用收益（每kgH2替代煤制氢减排19kg CO₂）
            if "风电" in info.get("tech", "") or "光伏" in info.get("tech", ""):
                carbon_credit = sim_carbon * 0.019 / 1000
            else:
                carbon_credit = 0

            effective_cost = sim_cost - carbon_credit
            landed_200 = compute_landed_cost(effective_cost, 200, sim_transport)

            sim_rows.append({
                "基地": name,
                "技术路线": TECH_ZH.get(info["tech"], info["tech"]),
                "模拟出厂成本": round(sim_cost, 1),
                "碳信用收益": round(carbon_credit, 1),
                "有效成本": round(effective_cost, 1),
                "200km到站价": round(landed_200, 1),
                "利润率": f"{(sim_target - landed_200) / sim_target * 100:+.1f}%",
            })

        df_sim = pd.DataFrame(sim_rows)
        st.dataframe(df_sim, use_container_width=True, hide_index=True)

        # 关键指标
        best = min(sim_rows, key=lambda x: x["200km到站价"])
        st.markdown(f"""
        <div class="info-card" style="border-left-color:{TEAL}">
          <div class="ic-title">📊 模拟结论</div>
          <div class="ic-row">
            最具竞争力基地：<b>{best['基地']}</b> — 200km 到站价 <b>{best['200km到站价']} 元/kg</b><br>
            目标售价 {sim_target} 元/kg 下，{sum(1 for r in sim_rows if r['200km到站价'] < sim_target)}/4 个基地可实现盈利
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ═══════════ TAB 4: 基地成本对标 ═══════════
    with tab4:
        st.subheader("国华基地 vs 市场竞品 · 成本对标")
        st.caption("基于各基地出厂成本与运输成本，对标市场零售价区间")

        # 构建竞品数据（从stations数据提取）
        cluster_prices = {}
        for s in stations:
            c = s.get("city_cluster", "其他")
            p = s.get("purchase_price_low") or s.get("retail_price")
            if p and p > 0:
                if c not in cluster_prices:
                    cluster_prices[c] = []
                cluster_prices[c].append(p)

        fig = go.Figure()
        # 国华基地
        base_names = list(GUOHUA_BASES.keys())
        base_costs = [GUOHUA_BASES[n]["cost"] for n in base_names]
        fig.add_trace(go.Bar(
            name="国华出厂成本", x=base_names, y=base_costs,
            marker_color=TEAL, text=[f"{c}元" for c in base_costs], textposition="outside",
        ))

        # 加上200km运输成本
        base_landed_200 = [compute_landed_cost(GUOHUA_BASES[n]["cost"], 200, transport_rate) for n in base_names]
        fig.add_trace(go.Bar(
            name="国华200km到站价", x=base_names, y=base_landed_200,
            marker_color=GREEN, marker_opacity=0.6,
            text=[f"{c}元" for c in base_landed_200], textposition="outside",
        ))

        # 各城市群零售均价
        for i, (cluster, prices) in enumerate(cluster_prices.items()):
            avg_p = sum(prices) / len(prices)
            fig.add_hline(y=avg_p, line_dash="dot", line_color=["#3b82f6", "#f59e0b", "#7c3aed", "#ef4444", "#10b981"][i % 5],
                         annotation=dict(text=f"{cluster}均价{avg_p:.0f}元", font_size=9))

        fig.update_layout(
            title="国华基地成本 vs 市场零售价", height=450,
            yaxis_title="元/kg", barmode="group",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # 自己基地详情
        st.markdown("### 四大基地参数")
        for name, info in GUOHUA_BASES.items():
            with st.expander(f"🏭 {name} — {TECH_ZH.get(info['tech'], info['tech'])}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("出厂成本", f"{info['cost']} 元/kg")
                with c2:
                    st.metric("年产能", f"{info['capacity']:,} 吨")
                with c3:
                    landed_200 = compute_landed_cost(info["cost"], 200, transport_rate)
                    st.metric("200km到站价", f"{landed_200:.1f} 元/kg")
                st.caption(f"📝 {info['note']}")
