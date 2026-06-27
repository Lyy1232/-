"""交易撮合看板 — 供需余缺分析 · 现货撮合 · 制氢企业闲置产能"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.trading_analysis import (
    get_dashboard_overview, get_supply_list, get_demand_list,
    get_idle_capacity, get_matching_suggestions,
)

TEAL = "#0d9488"
RED = "#ef4444"
GREEN = "#10b981"
AMBER = "#f59e0b"
BLUE = "#2563eb"


def render():
    st.markdown("""
    <div style="padding:4px 0 18px">
      <h1 style="font-size:1.35rem;margin:0;font-weight:800;letter-spacing:-0.3px;color:#0f172a">⛽ 交易撮合看板</h1>
      <p style="color:#64748b;font-size:0.8rem;margin:2px 0 0">基于第四年度示范城市群运营数据 · 供需余缺分析 · 现货撮合匹配</p>
    </div>
    """, unsafe_allow_html=True)

    overview = get_dashboard_overview()
    gs = overview["global_summary"]

    # ── KPI Row ──
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("统计加氢站", f"{gs['total_stations']} 座")
    with c2:
        st.metric("累计加注量", f"{gs['total_refuel_tons']:,.0f} 吨")
    with c3:
        st.metric("可售余量合计", f"{gs['total_surplus_tons']:,.0f} 吨")
    with c4:
        st.metric("采购缺口合计", f"{gs['total_shortage_tons']:,.0f} 吨")
    with c5:
        net = gs["total_surplus_tons"] - gs["total_shortage_tons"]
        st.metric("净余量", f"{net:+,.0f} 吨")

    # ── Tabs ──
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 城市群总览", "📤 供给端（余量站点）", "📥 需求端（缺口站点）", "🏭 制氢企业闲置产能"
    ])

    # ── Tab 1: Overview ──
    with tab1:
        df_clusters = pd.DataFrame(overview["clusters"])

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_clusters["cluster"], y=df_clusters["total_refuel_tons"],
                marker_color=[TEAL, BLUE, GREEN, AMBER, RED][:len(df_clusters)],
                text=[f"{v:,.0f}t" for v in df_clusters["total_refuel_tons"]],
                textposition="outside", textfont_size=11,
            ))
            fig.update_layout(
                title="各城市群累计加注量（吨）", height=380,
                yaxis_title="吨", showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="可售余量", x=df_clusters["cluster"], y=df_clusters["total_surplus_tons"],
                marker_color=GREEN, text=[f"{v:,.0f}t" for v in df_clusters["total_surplus_tons"]],
                textposition="outside",
            ))
            fig.add_trace(go.Bar(
                name="采购缺口", x=df_clusters["cluster"], y=df_clusters["total_shortage_tons"],
                marker_color=RED, text=[f"{v:,.0f}t" for v in df_clusters["total_shortage_tons"]],
                textposition="outside",
            ))
            fig.update_layout(
                title="各城市群余量/缺口（吨）", height=380, barmode="group",
                yaxis_title="吨", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=1.15),
            )
            st.plotly_chart(fig, use_container_width=True)

        # Detail table
        st.dataframe(
            df_clusters.rename(columns={
                "cluster": "城市群", "station_count": "站数",
                "total_refuel_tons": "加注量(吨)", "total_surplus_tons": "余量(吨)",
                "total_shortage_tons": "缺口(吨)", "avg_retail_price": "均价(元/kg)",
                "avg_utilization_pct": "利用率(%)", "abnormal_count": "异常站数",
            }),
            use_container_width=True, hide_index=True,
            column_config={
                "均价(元/kg)": st.column_config.NumberColumn(format="%.1f"),
                "利用率(%)": st.column_config.NumberColumn(format="%.1f"),
            }
        )

    # ── Tab 2: Supply List ──
    with tab2:
        supply = get_supply_list()
        if supply:
            df_supply = pd.DataFrame(supply)
            st.markdown(f"### 📤 可售余量站点（{len(df_supply)} 座）")
            st.caption("已排除异常数据站点（余量占比>90%）")

            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.bar(
                    df_supply.head(10), x="station_name", y="surplus_kg",
                    color="cluster", title="TOP10 余量站点",
                    labels={"surplus_kg": "可售余量(kg)", "station_name": ""},
                    color_discrete_sequence=[TEAL, BLUE, GREEN, AMBER, RED],
                )
                fig.update_layout(height=380, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.dataframe(
                    df_supply.rename(columns={
                        "station_name": "加氢站", "cluster": "城市群", "surplus_kg": "余量(kg)",
                        "retail_price": "零售价", "utilization_rate": "利用率(%)",
                    }),
                    use_container_width=True, hide_index=True,
                    column_order=["加氢站", "城市群", "余量(kg)", "零售价", "利用率(%)"],
                )
        else:
            st.info("暂无可售余量站点数据")

    # ── Tab 3: Demand List ──
    with tab3:
        demand = get_demand_list()
        if demand:
            df_demand = pd.DataFrame(demand)
            st.markdown(f"### 📥 缺口站点（{len(df_demand)} 座）")
            st.caption("已排除异常数据站点")

            fig = px.bar(
                df_demand.head(10), x="station_name", y="shortage_kg",
                color="cluster", title="TOP10 缺口站点",
                labels={"shortage_kg": "缺口量(kg)", "station_name": ""},
                color_discrete_sequence=[TEAL, BLUE, GREEN, AMBER, RED],
            )
            fig.update_layout(height=380, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                df_demand.rename(columns={
                    "station_name": "加氢站", "cluster": "城市群", "shortage_kg": "缺口(kg)",
                    "retail_price": "零售价", "utilization_rate": "利用率(%)",
                }),
                use_container_width=True, hide_index=True,
                column_order=["加氢站", "城市群", "缺口(kg)", "零售价", "利用率(%)"],
            )

            # Matching suggestions
            st.markdown("---")
            st.markdown("### 🔗 撮合匹配建议")
            matching = get_matching_suggestions()
            if matching:
                df_match = pd.DataFrame(matching)
                st.dataframe(
                    df_match.rename(columns={
                        "supply_station": "供给站", "supply_cluster": "供给群",
                        "supply_surplus_kg": "可售(kg)", "demand_station": "需求站",
                        "demand_cluster": "需求群", "demand_shortage_kg": "缺口(kg)",
                        "matchable_kg": "可撮合(kg)", "priority": "优先级", "match_logic": "逻辑",
                    }),
                    use_container_width=True, hide_index=True,
                )
        else:
            st.info("暂无缺口站点数据")

    # ── Tab 4: Idle Capacity ──
    with tab4:
        idle = get_idle_capacity()
        if idle:
            df_idle = pd.DataFrame(idle)
            st.markdown(f"### 🏭 头部制氢企业闲置产能（6家）")

            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name="年产能", y=df_idle["enterprise_name"],
                    x=df_idle["annual_capacity_tons"], orientation="h",
                    marker_color="#e2e8f0", marker_line_color="#cbd5e1", marker_line_width=0.5,
                    text=[f"{v:,}t" for v in df_idle["annual_capacity_tons"]],
                    textposition="outside", textfont_size=10, textfont_color="#94a3b8",
                ))
                fig.add_trace(go.Bar(
                    name="示范采购量", y=df_idle["enterprise_name"],
                    x=df_idle["demonstration_procurement_tons"], orientation="h",
                    marker_color=TEAL,
                    text=[f"{v:,}t" for v in df_idle["demonstration_procurement_tons"]],
                    textposition="inside", textfont_size=10, textfont_color="white",
                ))
                fig.update_layout(
                    title="年产能 vs 示范采购量", height=380, barmode="overlay",
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", y=1.1),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = go.Figure()
                colors = [
                    TEAL if u < 30 else (AMBER if u < 60 else RED)
                    for u in df_idle["utilization_pct"]
                ]
                fig.add_trace(go.Bar(
                    y=df_idle["enterprise_name"], x=df_idle["utilization_pct"],
                    orientation="h", marker_color=colors,
                    text=[f"{v:.1f}%" for v in df_idle["utilization_pct"]],
                    textposition="outside", textfont_size=10,
                ))
                fig.update_layout(
                    title="产能利用率（%）", height=380, showlegend=False,
                    xaxis=dict(range=[0, 100]),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                df_idle.rename(columns={
                    "enterprise_name": "企业", "annual_capacity_tons": "年产能(吨)",
                    "demonstration_procurement_tons": "示范采购(吨)",
                    "utilization_pct": "利用率(%)", "idle_capacity_tons": "闲置产能(吨)",
                    "hydrogen_type": "氢源类型", "region": "区域",
                }),
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("暂无制氢企业产能数据")
