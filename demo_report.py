"""陆上氢销售分析平台 示范城市群深度分析 Demo · 交互式数据仪表盘"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from utils.ui import inject_global_css

st.set_page_config(page_title="陆上氢销售分析平台 · 示范城市群深度分析", page_icon="●", layout="wide")
inject_global_css()

# ── Load data ──
@st.cache_data
def load_demo_data():
    with open('data/demo_data.json', 'r') as f:
        return json.load(f)

data = load_demo_data()

# ═══════════════════════════════════════
# Color palette
# ═══════════════════════════════════════
NAVY = '#060e1a'
TEAL = '#089b8c'
TEAL_LIGHT = '#0ab8a5'
BLUE = '#1d4ed8'
AMBER = '#f59e0b'
RED = '#ef4444'
GREEN = '#10b981'
PURPLE = '#7c3aed'
SLATE_50 = '#f6f7f9'
CLUSTER_COLORS = {
    '京津冀': TEAL, '河北': AMBER, '郑州': BLUE,
    '上海': PURPLE, '广东': RED, '广东(广州)': RED,
    '广州': RED
}

# ═══════════════════════════════════════
# Ticker
# ═══════════════════════════════════════
y3y4 = data['y3y4']
total_y4_stations = sum(y3y4['y4_stations'])
total_y4_refuel = sum(y3y4['y4_refuel_tons'])
total_procurement = 10060  # from analysis

st.markdown(f"""
<div class="ticker-bar">
  <div class="ticker-brand">
    <span class="tb-dot"></span>陆上氢销售分析平台 · 示范城市群深度分析
  </div>
  <div class="ticker-item">
    <span class="ti-label">Y4加氢站</span>
    <span class="ti-value">{total_y4_stations}</span>
  </div>
  <div class="ticker-item">
    <span class="ti-label">Y4加注量</span>
    <span class="ti-value">{total_y4_refuel:,} 吨</span>
  </div>
  <div class="ticker-item">
    <span class="ti-label">制氢企业</span>
    <span class="ti-value">43</span>
  </div>
  <div class="ticker-item">
    <span class="ti-label">年采购量</span>
    <span class="ti-value">{total_procurement:,} 吨</span>
  </div>
  <div class="ticker-item">
    <span class="ti-label">可交易闲置产能</span>
    <span class="ti-value" style="color:#f59e0b">>1.5万 吨/年</span>
  </div>
  <div class="ticker-status">
    <span class="ticker-dot"></span>
    数据来源：示范城市群氢能供应明细表
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 18px">
      <div style="font-weight:800;font-size:1.1rem;color:#fff">● 陆上氢销售分析平台 Demo</div>
      <div style="font-size:0.68rem;color:rgba(255,255,255,0.45);margin-top:2px;letter-spacing:0.5px">示范城市群深度分析仪表盘</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:10px;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">导航</p>', unsafe_allow_html=True)

    page = st.radio(
        "页面",
        ["📊 总览仪表盘", "📈 年度对比", "🏭 制氢企业分析", "⛽ 加氢站余缺", "🗺️ 跨区域套利", "💡 核心洞察"],
        label_visibility="collapsed"
    )

    st.markdown('<div style="margin:12px 0;border-top:1px solid rgba(255,255,255,0.08)"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:10px;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">参数设定</p>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:rgba(255,255,255,0.5);line-height:1.6">气态运氢：10元/100km·kg<br>绿氢成本：35元/kg<br>液氢运输：1.5元/100km·kg</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin:12px 0;border-top:1px solid rgba(255,255,255,0.08)"></div>', unsafe_allow_html=True)
    st.caption("v0.1.0 · Demo")

# ═══════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════
def metric_card(label, value, delta=None, delta_up_good=True, icon=""):
    delta_html = ""
    if delta is not None:
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        delta_cls = "up" if (delta > 0) == delta_up_good else "down"
        delta_color = "#059669" if delta_cls == "up" else "#dc2626"
        delta_html = f'<div class="mc-delta {delta_cls}" style="color:{delta_color}">{delta_str}</div>'
    icon_html = f'<div class="mc-icon">{icon}</div>' if icon else ""
    st.markdown(f"""
    <div class="metric-card">
      <div class="mc-accent-bar" style="background:linear-gradient(90deg,{TEAL},#0ab8a5)"></div>
      {icon_html}
      <div class="mc-value">{value}</div>
      <div class="mc-label">{label}</div>
      {delta_html}
    </div>
    """, unsafe_allow_html=True)

def plotly_theme(fig):
    fig.update_layout(
        font_family="Inter, system-ui, sans-serif",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#334155',
        title_font_size=14, title_font_color='#0f172a',
        margin=dict(l=10, r=10, t=40, b=10),
        hoverlabel=dict(bgcolor='white', font_size=12, font_color='#0f172a'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    )
    fig.update_xaxes(gridcolor='#e2e8f0', linecolor='#cbd5e1', tickfont_size=11)
    fig.update_yaxes(gridcolor='#e2e8f0', linecolor='#cbd5e1', tickfont_size=11)
    return fig

# ═══════════════════════════════════════
# PAGE 1: Executive Dashboard
# ═══════════════════════════════════════
if page == "📊 总览仪表盘":
    st.markdown('<h1>📊 示范城市群总览仪表盘</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:0.85rem;margin-top:-8px">基于第三/第四年度氢能供应明细数据 · 运输成本10元/100km·kg · 绿氢成本35元/kg</p>', unsafe_allow_html=True)

    # KPI Row 1
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Y4加氢站总数", f"{total_y4_stations} 座", delta=10, delta_up_good=True, icon="⛽")
    with c2:
        metric_card("Y4累计加注量", f"{total_y4_refuel:,} 吨", delta=round(total_y4_refuel - sum(y3y4['y3_refuel_tons']), -2), delta_up_good=True, icon="📦")
    with c3:
        metric_card("制氢企业数", "43 家", icon="🏭")
    with c4:
        metric_card("可交易闲置产能", ">1.5万 吨/年", icon="💎")
    with c5:
        avg_price_y4 = np.mean(y3y4['y4_avg_price'])
        avg_price_y3 = np.mean(y3y4['y3_avg_price'])
        metric_card("Y4平均零售价", f"{avg_price_y4:.1f} 元/kg", delta=round(avg_price_y4 - avg_price_y3, 1), delta_up_good=False, icon="💰")

    st.markdown("<br>", unsafe_allow_html=True)

    # KPI Row 2 - Y3 vs Y4 comparison
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("京津冀加注量增长", "+103%", delta=None, icon="🚀")
    with c2:
        metric_card("郑州加注量增长", "+271%", delta=None, icon="🚀")
    with c3:
        metric_card("上海加注量增长", "+233%", delta=None, icon="🚀")
    with c4:
        metric_card("广东氢价降幅", "-39.2%", delta=None, icon="📉")

    st.markdown("<br>", unsafe_allow_html=True)

    # Main charts row
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">Y3 vs Y4 各城市群加注量对比</span><span class="dc-badge live">LIVE</span></div>', unsafe_allow_html=True)

        fig = go.Figure()
        clusters = y3y4['clusters']
        fig.add_trace(go.Bar(name='第三年度', x=clusters, y=y3y4['y3_refuel_tons'],
                            marker_color=SLATE_50.replace('#', ''),
                            marker_line_color='#cbd5e1', marker_line_width=1,
                            text=[f'{v:,}t' for v in y3y4['y3_refuel_tons']],
                            textposition='outside', textfont_size=10, textfont_color='#94a3b8'))
        fig.add_trace(go.Bar(name='第四年度', x=clusters, y=y3y4['y4_refuel_tons'],
                            marker_color=TEAL.replace('#', ''),
                            text=[f'{v:,}t' for v in y3y4['y4_refuel_tons']],
                            textposition='outside', textfont_size=10, textfont_color=TEAL))
        fig.update_layout(barmode='group', height=420, yaxis_title='加注量（吨）')
        plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">Y3 vs Y4 各城市群零售均价对比</span><span class="dc-badge updated">价格</span></div>', unsafe_allow_html=True)

        price_data = data['prices']
        fig = go.Figure()
        clusters_p = price_data['clusters']
        fig.add_trace(go.Scatter(name='Y3均价', x=clusters_p, y=price_data['y3_price'],
                                mode='markers+lines', marker=dict(size=14, color='#94a3b8', symbol='circle-open'),
                                line=dict(color='#94a3b8', dash='dash', width=2)))
        fig.add_trace(go.Scatter(name='Y4均价', x=clusters_p, y=price_data['y4_price'],
                                mode='markers+lines', marker=dict(size=14, color=TEAL),
                                line=dict(color=TEAL, width=2.5)))
        # Add Y4 range as error bars
        fig.add_trace(go.Scatter(name='Y4价格区间', x=clusters_p + clusters_p[::-1],
                                y=price_data['y4_max'] + price_data['y4_min'][::-1],
                                fill='toself', fillcolor=f'rgba(8,155,140,0.1)',
                                line=dict(color='rgba(8,155,140,0)'), hoverinfo='skip',
                                showlegend=True))
        fig.update_layout(height=420, yaxis_title='零售均价（元/kg）')
        plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Transport cost impact
    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">运输成本对终端氢价的影响（高压气态：10元/100km·kg）</span></div>', unsafe_allow_html=True)

    transport = data['transport']
    fig = go.Figure()
    for t in transport:
        fig.add_trace(go.Bar(
            name=t['cluster'],
            x=[t['cluster']],
            y=[t['transport_cost_per_kg']],
            marker_color=CLUSTER_COLORS.get(t['cluster'], TEAL),
            text=f"{t['transport_cost_per_kg']}元/kg ({t['transport_pct']}%)",
            textposition='auto', textfont_size=11, textfont_color='white',
            hovertemplate=f"<b>{t['cluster']}</b><br>运输成本: {t['transport_cost_per_kg']}元/kg<br>占零售价: {t['transport_pct']}%<br>平均运距: {t['avg_km']}km<extra></extra>"
        ))
    fig.update_layout(height=360, showlegend=False, yaxis_title='运输成本（元/kg）')
    plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════
# PAGE 2: Y3 vs Y4 Comparison
# ═══════════════════════════════════════
elif page == "📈 年度对比":
    st.markdown('<h1>📈 第三年度 vs 第四年度 深度对比</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:0.85rem;margin-top:-8px">从规模扩张到效率提升的关键转折期</p>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["加注量与站数", "氢价与效率", "运营效率", "增长动力分解"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            clusters = y3y4['clusters']
            fig.add_trace(go.Bar(name='Y3站数', x=clusters, y=y3y4['y3_stations'],
                                marker_color='#94a3b8', offsetgroup=0), secondary_y=False)
            fig.add_trace(go.Bar(name='Y4站数', x=clusters, y=y3y4['y4_stations'],
                                marker_color=TEAL, offsetgroup=1), secondary_y=False)
            fig.update_layout(barmode='group', height=420, title='加氢站数量变化')
            plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Y3加注量', x=clusters, y=y3y4['y3_refuel_tons'],
                                marker_color='#94a3b8', text=[f'{v:,}t' for v in y3y4['y3_refuel_tons']], textposition='outside'))
            fig.add_trace(go.Bar(name='Y4加注量', x=clusters, y=y3y4['y4_refuel_tons'],
                                marker_color=TEAL, text=[f'{v:,}t' for v in y3y4['y4_refuel_tons']], textposition='outside'))
            fig.update_layout(height=420, title='累计加注量变化（吨）')
            plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

        # Growth rates
        growth_rates = []
        for i, c in enumerate(clusters):
            if y3y4['y3_refuel_tons'][i] > 500:
                growth_rates.append({
                    '城市群': c,
                    '站数增长': f"{'+' if y3y4['y4_stations'][i] >= y3y4['y3_stations'][i] else ''}{(y3y4['y4_stations'][i]-y3y4['y3_stations'][i])/y3y4['y3_stations'][i]*100:.0f}%",
                    '加注量增长': f"{'+' if y3y4['y4_refuel_tons'][i] >= y3y4['y3_refuel_tons'][i] else ''}{(y3y4['y4_refuel_tons'][i]-y3y4['y3_refuel_tons'][i])/y3y4['y3_refuel_tons'][i]*100:.0f}%",
                    '氢价变化': f"{(y3y4['y4_avg_price'][i]-y3y4['y3_avg_price'][i]):+.1f}元/kg",
                })
        st.dataframe(pd.DataFrame(growth_rates), use_container_width=True, hide_index=True)

    with tab2:
        price_data = data['prices']
        fig = go.Figure()
        for i, c in enumerate(price_data['clusters']):
            fig.add_trace(go.Scatter(
                x=[f'{c} Y3', f'{c} Y4'],
                y=[price_data['y3_price'][i], price_data['y4_price'][i]],
                mode='lines+markers',
                name=c,
                marker=dict(size=12),
                line=dict(width=3),
            ))
        # Add target line
        fig.add_hline(y=25, line_dash='dash', line_color=RED, annotation_text='2030目标: 25元/kg', annotation_position='top left')
        fig.update_layout(height=450, yaxis_title='零售均价（元/kg）', title='氢价走势：Y3→Y4全面下行')
        plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        # Price range comparison
        fig2 = go.Figure()
        for i, c in enumerate(price_data['clusters'][:4]):
            fig2.add_trace(go.Box(
                y=[price_data['y4_min'][i], price_data['y4_max'][i], price_data['y4_price'][i]],
                x=[c]*3, name=c, marker_color=CLUSTER_COLORS.get(c, TEAL),
                boxpoints=False
            ))
        fig2.update_layout(height=380, title='Y4各城市群价格区间（最低-均价-最高）', showlegend=False, yaxis_title='元/kg')
        plotly_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        # Single station efficiency
        fig = go.Figure()
        single_station = [
            (y3y4['y3_refuel_tons'][0]/y3y4['y3_stations'][0], y3y4['y4_refuel_tons'][0]/y3y4['y4_stations'][0]),
            (y3y4['y3_refuel_tons'][1]/y3y4['y3_stations'][1], y3y4['y4_refuel_tons'][1]/y3y4['y4_stations'][1]),
            (y3y4['y3_refuel_tons'][2]/y3y4['y3_stations'][2], y3y4['y4_refuel_tons'][2]/y3y4['y4_stations'][2]),
            (y3y4['y3_refuel_tons'][3]/y3y4['y3_stations'][3], y3y4['y4_refuel_tons'][3]/y3y4['y4_stations'][3]),
        ]
        for i, c in enumerate(clusters):
            fig.add_trace(go.Bar(name=c, x=['Y3', 'Y4'], y=[single_station[i][0], single_station[i][1]],
                                marker_color=CLUSTER_COLORS.get(c, TEAL),
                                text=[f'{single_station[i][0]:.0f}t', f'{single_station[i][1]:.0f}t'],
                                textposition='outside', textfont_size=10))
        fig.update_layout(height=420, title='单站加注量变化（吨/站）', yaxis_title='吨/站')
        plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        # Capacity utilization
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=clusters, y=y3y4['y4_capacity_util'],
                             marker_color=[CLUSTER_COLORS.get(c, TEAL) for c in clusters],
                             text=[f'{v}%' for v in y3y4['y4_capacity_util']],
                             textposition='outside'))
        fig2.update_layout(height=360, title='Y4产能利用率（%）', yaxis_title='%', showlegend=False)
        plotly_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    with tab4:
        st.markdown("### 增长动力分解（Y3→Y4）")

        # Decomposition waterfall
        fig = go.Figure(go.Waterfall(
            name="京津冀", orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=["Y3加注量", "站数增长贡献", "单站效率提升", "Y4加注量"],
            y=[3972, 3972*0.4, 3972*0.6, 8062],
            text=["3,972吨", "+1,589吨", "+2,384吨", "8,062吨"],
            connector={"mode": "spanning", "line": {"width": 1, "color": "rgb(203,213,225)"}},
            decreasing={"marker": {"color": TEAL}},
            increasing={"marker": {"color": BLUE}},
            totals={"marker": {"color": NAVY.replace('#', '')}}
        ))
        fig.update_layout(height=420, title='京津冀增长动力分解')
        plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        <div class="info-card">
          <div class="ic-title">📐 增长动力解读</div>
          <div class="ic-row">
            <b>外延式增长（站数增加）</b>贡献约40%的增量，主要体现在京津冀和郑州<br>
            <b>内涵式增长（单站效率提升）</b>贡献约60%的增量，上海单站效率+328%最为突出<br>
            <b>氢价弹性</b>：各群氢价平均下降约15%，测算氢价每降10%→加注量增20-30%
          </div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════
# PAGE 3: Producer Analysis
# ═══════════════════════════════════════
elif page == "🏭 制氢企业分析":
    st.markdown('<h1>🏭 制氢企业产能与闲置分析</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:0.85rem;margin-top:-8px">6家头部企业综合利用率仅18% · 可交易闲置产能超1.5万吨/年</p>', unsafe_allow_html=True)

    producers = data['producers_capacity']
    df_prod = pd.DataFrame(producers)
    df_prod['企业'] = df_prod['name']
    df_prod['年产能(吨)'] = df_prod['capacity_tons']
    df_prod['示范采购(吨)'] = df_prod['procurement_tons']
    df_prod['利用率'] = df_prod['utilization']
    df_prod['闲置产能(吨)'] = df_prod['idle_tons']

    col1, col2 = st.columns([1.2, 1])
    with col1:
        # Capacity vs Procurement
        fig = go.Figure()
        fig.add_trace(go.Bar(name='年产能', y=[p['name'] for p in producers], x=[p['capacity_tons'] for p in producers],
                            orientation='h', marker_color='#cbd5e1', text=[f'{p["capacity_tons"]:,}t' for p in producers],
                            textposition='outside', textfont_size=9.5))
        fig.add_trace(go.Bar(name='示范采购', y=[p['name'] for p in producers], x=[p['procurement_tons'] for p in producers],
                            orientation='h', marker_color=TEAL, text=[f'{p["procurement_tons"]:,}t' for p in producers],
                            textposition='inside', textfont_size=9.5, textfont_color='white'))
        fig.update_layout(height=420, barmode='overlay', title='年产能 vs 示范采购量',
                         xaxis_title='吨/年', legend=dict(x=0.7, y=1.05))
        plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Utilization gauge
        fig = go.Figure()
        for i, p in enumerate(producers):
            fig.add_trace(go.Bar(
                y=[p['name']], x=[p['utilization']],
                orientation='h', name=p['name'],
                marker_color=[TEAL if p['utilization'] < 30 else AMBER if p['utilization'] < 60 else RED][0],
                text=[f'{p["utilization"]:.1f}%'], textposition='outside', textfont_size=10,
                hovertemplate=f"<b>{p['name']}</b><br>利用率: {p['utilization']:.1f}%<br>闲置: {p['idle_tons']:,}吨/年<extra></extra>"
            ))
        fig.update_layout(height=420, title='产能利用率（%）', showlegend=False, xaxis_title='%',
                         xaxis=dict(range=[0, 110]))
        plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    # Idle capacity summary
    total_idle = sum(p['idle_tons'] for p in producers)
    st.markdown(f"""
    <div class="info-card" style="border-left-color:{TEAL};background:linear-gradient(135deg,#f0fdfa 0%,#fff 100%)">
      <div class="ic-title">💎 6家头部企业合计闲置产能：{total_idle:,.0f} 吨/年</div>
      <div class="ic-row">
        最大闲置：<b>燕山石化 6,893吨/年</b>（但燕山石化有大量非示范供应）<br>
        纯示范闲置最大：<b>唐山中溶科技 6,770吨/年</b>（利用率仅6%）<br>
        最适上线标的：<b>天津新源氢能 5,253吨/年</b>（清洁氢认证+到站成本25.9元/kg）
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Supply chain top 20
    st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">制氢企业供应量排名 TOP20</span></div>', unsafe_allow_html=True)
    top20 = data['producers_top20']
    df_top20 = pd.DataFrame([{
        '排名': i+1, '企业': p['name'][:25],
        '供应量(吨)': f"{p['total_kg']/1000:,.0f}",
        '供应站数': p['stations'],
        '平均运距(km)': f"{p['avg_radius']:.0f}",
    } for i, p in enumerate(top20)])
    st.dataframe(df_top20, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Transport cost competitiveness
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">运输成本视角下的到站竞争力评估（气态10元/100km·kg）</span></div>', unsafe_allow_html=True)

    comp_data = [
        {'企业': '唐山中溶→天津', '出厂成本': 18, '运距km': 80, '运输成本': 8, '到站成本': 26, '对标价': 30, '价差': 4},
        {'企业': '天津新源→京津冀', '出厂成本': 20, '运距km': 59, '运输成本': 5.9, '到站成本': 25.9, '对标价': 30.2, '价差': 4.3},
        {'企业': '燕山石化→京津冀', '出厂成本': 22, '运距km': 68, '运输成本': 6.8, '到站成本': 28.8, '对标价': 30.2, '价差': 1.4},
        {'企业': '唐山中溶→北京', '出厂成本': 18, '运距km': 150, '运输成本': 15, '到站成本': 33, '对标价': 30.2, '价差': -2.8},
        {'企业': '定州旭阳→北京', '出厂成本': 18, '运距km': 175, '运输成本': 17.5, '到站成本': 35.5, '对标价': 30.2, '价差': -5.3},
        {'企业': '国华赤城绿氢→北京', '出厂成本': 35, '运距km': 112, '运输成本': 11.2, '到站成本': 46.2, '对标价': 30.2, '价差': -16},
    ]
    df_comp = pd.DataFrame(comp_data)

    fig = go.Figure()
    colors_comp = [GREEN if d['价差'] > 0 else RED for d in comp_data]
    fig.add_trace(go.Bar(
        y=[d['企业'] for d in comp_data], x=[d['到站成本'] for d in comp_data],
        orientation='h', marker_color=colors_comp,
        text=[f"到站{d['到站成本']}元/kg (价差{d['价差']:+.0f})" for d in comp_data],
        textposition='outside', textfont_size=9.5
    ))
    fig.add_vline(x=30.2, line_dash='dash', line_color=RED, annotation_text='京津冀均价30.2', annotation_position='top')
    fig.update_layout(height=400, title='到站成本 vs 京津冀均价', xaxis_title='元/kg')
    plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════
# PAGE 4: Station Surplus/Deficit
# ═══════════════════════════════════════
elif page == "⛽ 加氢站余缺":
    st.markdown('<h1>⛽ 加氢站供需余缺分析</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:0.85rem;margin-top:-8px">12站余量653吨可售 · 21站缺口750吨需购 · 现货撮合匹配方案</p>', unsafe_allow_html=True)

    sd = data['stations_sd']
    surplus_s = sorted([s for s in sd if s['surplus'] > 100], key=lambda x: x['surplus'], reverse=True)
    deficit_s = sorted([s for s in sd if s['surplus'] < -100], key=lambda x: x['surplus'])

    # Summary
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("余量站点", f"{len(surplus_s)} 座", delta=None, icon="📤")
    with c2:
        metric_card("缺口站点", f"{len(deficit_s)} 座", delta=None, icon="📥")
    with c3:
        total_surplus = sum(s['surplus'] for s in surplus_s)
        total_deficit = sum(abs(s['surplus']) for s in deficit_s)
        metric_card("净缺口", f"{total_deficit-total_surplus:,.0f} kg", delta=None, icon="⚖️")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">余量站点（可出售氢气）</span></div>', unsafe_allow_html=True)
        surplus_display = [
            {'站名': s['name'][:28], '城市群': s['cluster'], '采购量(kg)': f"{s['procurement']:,.0f}",
             '加注量(kg)': f"{s['refuel']:,.0f}", '余量(kg)': f"{s['surplus']:,.0f}", '余量占比': f"{s['surplus_pct']:.1f}%"}
            for s in surplus_s[:8]
        ]
        st.dataframe(pd.DataFrame(surplus_display), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">缺口站点（需采购氢气）</span></div>', unsafe_allow_html=True)
        deficit_display = [
            {'站名': s['name'][:28], '城市群': s['cluster'], '采购量(kg)': f"{s['procurement']:,.0f}",
             '加注量(kg)': f"{s['refuel']:,.0f}", '缺口(kg)': f"{abs(s['surplus']):,.0f}", '缺口占比': f"{abs(s['surplus_pct']):.1f}%"}
            for s in deficit_s[:8]
        ]
        st.dataframe(pd.DataFrame(deficit_display), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Surplus/Deficit scatter
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">加氢站供需分布图</span></div>', unsafe_allow_html=True)

    fig = go.Figure()
    valid_sd = [s for s in sd if abs(s['surplus_pct']) < 500]  # Filter outliers
    fig.add_trace(go.Scatter(
        x=[s['procurement'] for s in valid_sd],
        y=[s['refuel'] for s in valid_sd],
        mode='markers',
        marker=dict(
            size=10,
            color=[GREEN if s['surplus'] > 0 else RED if s['surplus'] < 0 else '#94a3b8' for s in valid_sd],
            opacity=0.7,
        ),
        text=[f"<b>{s['name'][:20]}</b><br>{s['cluster']}<br>采购:{s['procurement']:,.0f}kg<br>加注:{s['refuel']:,.0f}kg<br>{'余量' if s['surplus']>0 else '缺口'}:{abs(s['surplus']):,.0f}kg" for s in valid_sd],
        hoverinfo='text',
    ))
    # Add x=y line
    max_val = max(max(s['procurement'] for s in valid_sd), max(s['refuel'] for s in valid_sd))
    fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode='lines',
                            line=dict(color='#cbd5e1', dash='dash', width=1),
                            name='采购=加注（平衡线）'))
    fig.update_layout(height=480, xaxis_title='采购量(kg)', yaxis_title='加注量(kg)',
                     title='上方=余量可售 · 下方=缺口需购')
    plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Matching plan
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">现货撮合匹配方案</span></div>', unsafe_allow_html=True)
    match_data = pd.DataFrame([
        {'优先级': 'P0', '供给方': '郑州：金马氢能化工路站', '余量(吨)': 120, '需求方': '郑州群内部', '缺口(吨)': '-', '匹配逻辑': '同城群内调拨，运距<100km'},
        {'优先级': 'P0', '供给方': '郑州：航空港区吴村站', '余量(吨)': 163, '需求方': '郑州：安阳洹科站等', '缺口(吨)': '18+', '匹配逻辑': '河南省内短距调拨'},
        {'优先级': 'P1', '供给方': '上海：安亭加氢站', '余量(吨)': 42, '需求方': '上海：嘉善站前路站', '缺口(吨)': 87, '匹配逻辑': '需多条余量汇合'},
        {'优先级': 'P1', '供给方': '广州：石湖加氢站', '余量(吨)': 12, '需求方': '广州：良田站/永丰站', '缺口(吨)': '218+132', '匹配逻辑': '广东省内物流通道'},
        {'优先级': 'P2', '供给方': '京津冀：迁安陆驰', '余量(吨)': '核实中', '需求方': '京津冀缺口站点', '缺口(吨)': '-', '匹配逻辑': '唐山→北京/天津约150-200km'},
    ])
    st.dataframe(match_data, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════
# PAGE 5: Cross-regional Arbitrage
# ═══════════════════════════════════════
elif page == "🗺️ 跨区域套利":
    st.markdown('<h1>🗺️ 跨区域套利空间分析</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:0.85rem;margin-top:-8px">气态10元/100km·kg · 液氢1.5元/100km·kg · 有效套利半径约100km（气态）</p>', unsafe_allow_html=True)

    arb = data['arbitrage']

    # Arbitrage waterfall chart
    st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">跨区域套利路线经济性测算</span></div>', unsafe_allow_html=True)

    fig = go.Figure()
    for i, route in enumerate(arb):
        color = GREEN if route['feasible'] else RED
        symbol = '✅' if route['feasible'] else '❌'
        fig.add_trace(go.Bar(
            name=f"{symbol} {route['from']}→{route['to']}（{route['transport_mode']}）",
            x=[f"{route['from']}→{route['to']}"],
            y=[route['spread']],
            marker_color=color,
            text=[f"套利{route['spread']:+.0f}元/kg<br>{route['transport_mode']} {route['distance_km']}km<br>到站{route['landed_cost']}元/kg"],
            textposition='outside', textfont_size=9,
            hovertemplate=f"<b>{route['from']}→{route['to']}</b><br>"
                          f"运输方式: {route['transport_mode']}<br>"
                          f"距离: {route['distance_km']}km<br>"
                          f"氢源成本: {route['source_cost']}元/kg<br>"
                          f"运输成本: {route['transport_cost']}元/kg<br>"
                          f"到站成本: {route['landed_cost']}元/kg<br>"
                          f"目标零售价: {route['target_price']}元/kg<br>"
                          f"套利空间: {route['spread']:+.0f}元/kg<br>"
                          f"可行性: {'可行' if route['feasible'] else '不可行'}<extra></extra>"
        ))
    fig.add_hline(y=0, line_color='#334155', line_width=1.5)
    fig.update_layout(height=500, showlegend=False, yaxis_title='套利空间（元/kg）')
    plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Key insights
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="data-card">
          <div class="dc-header"><span class="dc-title">✅ 可行路线</span></div>
          <div style="padding:4px 0">
            <div class="info-card">
              <div class="ic-title">唐山→天津（气态 80km）</div>
              <div class="ic-row">到站26元/kg vs 零售30元/kg → <b style="color:#059669">+4元/kg</b></div>
            </div>
            <div class="info-card">
              <div class="ic-title">天津新源→京津冀平均（气态 59km）</div>
              <div class="ic-row">到站25.9元/kg vs 零售30.2元/kg → <b style="color:#059669">+4.3元/kg</b></div>
            </div>
            <div class="info-card">
              <div class="ic-title">定州旭阳→北京（管道规划 164km）</div>
              <div class="ic-row">到站21元/kg vs 零售30.2元/kg → <b style="color:#059669">+9.2元/kg</b></div>
            </div>
            <div class="info-card">
              <div class="ic-title">山西吕梁→上海（液氢 1200km 氢源15元/kg）</div>
              <div class="ic-row">到站33元/kg vs 零售36元/kg → <b style="color:#059669">+3元/kg</b></div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="data-card">
          <div class="dc-header"><span class="dc-title">❌ 不可行路线</span></div>
          <div style="padding:4px 0">
            <div class="info-card danger">
              <div class="ic-title">唐山→北京东部（气态 150km）</div>
              <div class="ic-row">到站33元/kg vs 零售30.2元/kg → <b style="color:#dc2626">-2.8元/kg</b></div>
            </div>
            <div class="info-card danger">
              <div class="ic-title">国华赤城绿氢→北京（气态 112km）</div>
              <div class="ic-row">到站46.2元/kg vs 零售30.2元/kg → <b style="color:#dc2626">-16元/kg</b>（需碳信用+ESG）</div>
            </div>
            <div class="info-card danger">
              <div class="ic-title">山西吕梁→上海（液氢 氢源18元/kg）</div>
              <div class="ic-row">到站36元/kg vs 零售36元/kg → <b style="color:#dc2626">打平，无套利</b></div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Transport mode comparison
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">运输方式成本对比</span></div>', unsafe_allow_html=True)

    distances = list(range(0, 501, 50))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=distances, y=[d*10/100 for d in distances], name='高压气态（20MPa）',
                            mode='lines', line=dict(color=RED, width=2.5),
                            fill='tozeroy', fillcolor='rgba(239,68,68,0.05)'))
    fig.add_trace(go.Scatter(x=distances, y=[d*1.5/100 for d in distances], name='液氢',
                            mode='lines', line=dict(color=BLUE, width=2.5)))
    fig.add_trace(go.Scatter(x=distances, y=[d*0.3/100+1 for d in distances], name='管道输氢',
                            mode='lines', line=dict(color=GREEN, width=2.5)))
    fig.update_layout(height=380, xaxis_title='运输距离（km）', yaxis_title='运输成本（元/kg）',
                     title='运输成本随距离变化曲线')
    plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "💡 核心洞察":
    st.markdown('<h1>💡 核心洞察与交易机会总结</h1>', unsafe_allow_html=True)

    insights = data['insights']

    # Insight cards in 2-column grid
    for i in range(0, len(insights), 2):
        c1, c2 = st.columns(2)
        for j, col in enumerate([c1, c2]):
            idx = i + j
            if idx >= len(insights): break
            ins = insights[idx]
            cat_color = {
                '趋势': BLUE, '机会': GREEN, '风险': RED
            }.get(ins['category'], TEAL)
            with col:
                st.markdown(f"""
                <div class="data-card" style="border-top:3px solid {cat_color}">
                  <div style="font-size:1.8rem;margin-bottom:6px">{ins['icon']}</div>
                  <div style="font-size:9px;color:{cat_color};text-transform:uppercase;font-weight:700;letter-spacing:1px;margin-bottom:6px">{ins['category']}</div>
                  <div style="font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:8px">{ins['title']}</div>
                  <div style="font-size:0.8rem;color:#475569;line-height:1.5">{ins['body']}</div>
                </div>
                <br>
                """, unsafe_allow_html=True)

    # Trading product summary
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">四种交易产品设计</span></div>', unsafe_allow_html=True)

    products = pd.DataFrame([
        {'产品': '现货撮合交易', '目标客户': '缺口站点', '交易标的': '≥500kg/批次', '预计市场': '2,000-3,000吨/年', '优先级': 'P0'},
        {'产品': '季度/年度长约', '目标客户': '闲置制氢企业+稳定需求站', '交易标的': '月供≥5吨', '预计市场': '5,000-8,000吨/年', '优先级': 'P0'},
        {'产品': '跨区域调拨交易', '目标客户': '贸易商/大型运营商', '交易标的': '液氢≥3吨/车次', '预计市场': '待液氢规模化', '优先级': 'P1'},
        {'产品': '绿氢溢价交易专区', '目标客户': 'ESG/碳关税需求方', '交易标的': '碳认证绿氢', '预计市场': '800吨/年（现有）', '优先级': 'P1'},
    ])
    st.dataframe(products, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Roadmap
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="data-card"><div class="dc-header"><span class="dc-title">平台市场拓展路线图</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div style="background:#eff6ff;border-radius:10px;padding:16px;height:100%">
          <div style="font-weight:800;font-size:1rem;color:#1d4ed8;margin-bottom:8px">🚀 近期 Q3-Q4 2026</div>
          <div style="font-size:0.78rem;color:#334155;line-height:1.6">
          ✓ 上线现货撮合功能<br>
          ✓ 10+10站点入驻<br>
          ✓ 突破天津新源氢能<br>
          ✓ 建立分区域价格指数
          </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="background:#fffbeb;border-radius:10px;padding:16px;height:100%">
          <div style="font-weight:800;font-size:1rem;color:#b45309;margin-bottom:8px">📈 中期 2027</div>
          <div style="font-size:0.78rem;color:#334155;line-height:1.6">
          ✓ 标准长约合约+履约担保<br>
          ✓ 山西→长三角液氢专线<br>
          ✓ 绿氢交易专区运营<br>
          ✓ 接入碳交易所
          </div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div style="background:#f0fdfa;border-radius:10px;padding:16px;height:100%">
          <div style="font-weight:800;font-size:1rem;color:#089b8c;margin-bottom:8px">🎯 远期 2028-2030</div>
          <div style="font-size:0.78rem;color:#334155;line-height:1.6">
          ✓ 国家级氢能交易基础设施<br>
          ✓ 氢能期货/远期合约<br>
          ✓ 中日韩国际氢贸易通道<br>
          ✓ 年交易量突破5万吨
          </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align:center;padding:30px 0 10px;border-top:1px solid #e2e8f0;margin-top:30px">
  <div style="font-size:10px;color:#94a3b8">陆上氢销售分析平台 氢溯科技 · 国家能源集团 · Demo v0.1.0</div>
  <div style="font-size:9px;color:#cbd5e1;margin-top:4px">数据来源：国家燃料电池汽车示范应用城市群氢能供应明细表 · 参数：气态运氢10元/100km·kg · 绿氢35元/kg</div>
</div>
""", unsafe_allow_html=True)
