"""首页总览 — v2.0 基础设施构想图 + 成本横栏 + 卡片式仪表盘"""
import io
import base64
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patheffects import withStroke
import numpy as np
from utils.data_loader import load_sites, load_stations, get_station_stats, get_cluster_stats, get_updated_time
from utils.ui import render_module_header
from config.constants import (
    ECONOMIC_RADIUS_KM, GUOHUA_BASES_COST, REFERENCE_DATA,
    TRANSPORT_MODES, INFRA_COSTS,
)

BRAND = "#0d9488"; BRAND_LT = "#14b8a6"; NAVY = "#060e1a"; WHITE60 = "#ffffff99"

# ═══════════════════════ Hero 图生成 ═══════════════════════
def _draw_infrastructure_hero() -> str:
    """用 matplotlib 绘制基础设施构想图，返回 base64 PNG data-uri。"""
    # 设置中文字体 (macOS STHeiti)
    import matplotlib.font_manager as fm
    for fname in ["/System/Library/Fonts/STHeiti Medium.ttc",
                  "/System/Library/Fonts/STHeiti Light.ttc"]:
        try:
            fp = fm.FontProperties(fname=fname)
            fm.fontManager.addfont(fname)
            plt.rcParams["font.family"] = fp.get_name()
            break
        except Exception:
            continue
    fig, ax = plt.subplots(figsize=(14, 4.8), facecolor=NAVY)
    ax.set_xlim(0, 14); ax.set_ylim(0, 5); ax.axis("off")

    # ── 背景光晕 ──
    for cx, cy, r in [(1.8, 2.5, 2.8), (5.5, 2.5, 2.5), (10.5, 2.5, 2.5)]:
        ax.imshow(np.linspace(0, 0.06, 256).reshape(1, -1),
                  extent=[cx - r, cx + r, cy - r * 0.55, cy + r * 0.55],
                  cmap="Greens", aspect="auto", alpha=0.25, zorder=0)

    # ── 1. 风电剪影 ──
    for bx, bh in [(1.0, 1.4), (1.6, 1.2), (2.2, 1.5)]:
        ax.plot([bx, bx], [0.8, 0.8 + bh], color=WHITE60, lw=2.5, zorder=2)
        ax.plot([bx - 0.25, bx, bx + 0.25],
                [0.8 + bh * 0.65, 0.8 + bh, 0.8 + bh * 0.65],
                color=WHITE60, lw=4, zorder=2, solid_joinstyle="round")
        for a in [0.35, 1.4, 2.45]:
            dx = np.cos(a) * 0.18; dy = np.sin(a) * 0.18
            ax.plot([bx, bx + dx], [0.8 + bh, 0.8 + bh + dy],
                    color=WHITE60, lw=1.8, alpha=0.5, zorder=2)

    # ── 2. 光伏阵列 ──
    for px in np.linspace(3.0, 4.2, 5):
        ax.add_patch(mpatches.Rectangle((px, 1.55), 0.15, 0.65, angle=15,
                                         color="#4da8da", alpha=0.5, zorder=2))
    ax.text(3.6, 2.45, "风电+光伏", color=WHITE60, fontsize=7, ha="center", fontweight="bold")

    # ── 3. 四大基地发光点 ──
    bases = [
        (3.1, 3.5, "赤城", "#00d4aa"), (3.8, 1.7, "沧州", "#f59e0b"),
        (5.1, 3.0, "宁东", "#4da8da"), (6.0, 1.3, "如东", "#00d4aa"),
    ]
    for bx, by, name, clr in bases:
        for r in [0.32, 0.18, 0.08]:
            ax.add_patch(plt.Circle((bx, by), r, color=clr,
                                     alpha=0.15 if r > 0.2 else (0.5 if r > 0.1 else 0.9), zorder=3))
        ax.text(bx, by - 0.38, name, color="#fff", fontsize=7.5, ha="center", fontweight="bold",
                path_effects=[withStroke(linewidth=1.5, foreground=NAVY)])

    # ── 4. 纯化/压缩/液化工厂 ──
    ax.add_patch(mpatches.FancyBboxPatch((6.4, 1.6), 1.2, 1.8, boxstyle="round,pad=0.15",
                                          facecolor="#0f2240", edgecolor=BRAND_LT, lw=1.2, zorder=2))
    ax.text(7.0, 3.65, "纯化·压缩·液化", color="#fff", fontsize=7.5, ha="center", fontweight="bold")
    for pipe_x in [6.5, 7.0, 7.5]:
        ax.plot([pipe_x, pipe_x], [3.2, 3.5], color=BRAND_LT, lw=1.5, zorder=2)

    # ── 5. 运输网络 ──
    routes = [
        (6.6, 3.4, 8.8, 3.4, "dashed", WHITE60, "长管拖车 20/30MPa → 150–200km"),
        (6.6, 2.5, 9.5, 2.5, "dotted", "#4da8da", "液氢槽车 → 500km"),
        (6.6, 1.7, 10.8, 1.7, "dashdot", BRAND_LT, "铁路液氨→裂解 → 2000km"),
    ]
    for x1, y1, x2, y2, ls, clr, label in routes:
        ax.plot([x1, x2], [y1, y2], linestyle=ls, color=clr, lw=1.8, alpha=0.7, zorder=2)
        ax.text(x2 + 0.15, y2, label, color=clr, fontsize=5.5, va="center", alpha=0.8)

    # ── 6. 加氢站 + 城市群 ──
    for rx, ry, rlab in [(9.2, 4.1, "京津冀"), (10.2, 3.2, "长三角"), (9.5, 2.0, "宁东·银川")]:
        ax.add_patch(plt.Circle((rx, ry), 0.2, color=BRAND, alpha=0.5, zorder=3))
        ax.text(rx, ry + 0.3, rlab, color="#fff", fontsize=6.5, ha="center", fontweight="bold")

    end_users = ["公交/重卡", "化工原料\n(煤化工替代)", "实验室/半导体\n(高纯氢)"]
    for i, eu in enumerate(end_users):
        ax.text(11.5, 4.1 - i * 0.7, eu, color=WHITE60, fontsize=6.5, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#0f2240", edgecolor=BRAND_LT, alpha=0.7))

    # ── 7. 200km 辐射圈示意 ──
    for r_ring, a in [(0.55, 0.18), (0.95, 0.10), (1.4, 0.05)]:
        ax.add_patch(plt.Circle((3.8, 3.2), r_ring, fill=False, edgecolor=BRAND_LT, lw=0.8, alpha=a, zorder=1))
    ax.annotate("200km 辐射圈", xy=(3.8 + 1.4, 3.2), xytext=(5.2, 4.55),
                fontsize=6, color=BRAND_LT, arrowprops=dict(arrowstyle="->", color=BRAND_LT, lw=0.7), alpha=0.5)

    ax.text(7, 4.82, "国华氢能 · 从生产到加注的全链条基础设施构想",
            color="#fff", fontsize=12, ha="center", fontweight="bold", alpha=0.9)
    ax.text(7, 4.52, "风电/光伏电场  →  制氢基地  →  纯化/压缩/液化  →  公路/铁路运输  →  加氢站  →  终端用户",
            color=WHITE60, fontsize=7, ha="center", alpha=0.6)

    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=160, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig); buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ═══════════════════════ 组件 ═══════════════════════
def _render_hero(transport_mode="长管拖车20MPa"):
    """渲染 Hero 区段：基础设施构想图 + 成本横栏叠加。"""
    img_b64 = _draw_infrastructure_hero()
    mode_info = TRANSPORT_MODES.get(transport_mode, TRANSPORT_MODES["长管拖车20MPa"])
    transport_cost = mode_info["cost_per_100km"]
    transport_label = mode_info["note"]
    storage_cost = INFRA_COSTS["储存（高压气态）"]["value"]
    refuel_cost = INFRA_COSTS["加注（加氢站运营）"]["value"]
    load_cost = INFRA_COSTS["装卸（槽车装卸）"]["value"]

    st.markdown(f"""
    <div class="hero-container">
      <img class="hero-img" src="data:image/png;base64,{img_b64}" alt="氢能基础设施构想">
      <div class="hero-costbar">
        <div class="hero-cost-item">
          <div class="hci-icon">🚛</div>
          <div class="hci-value">{transport_cost:.1f} <span style="font-size:11px;font-weight:400">元/100km·kg</span></div>
          <div class="hci-label">运输成本</div>
          <div class="hci-sub">({transport_mode} · {transport_label[:20]})</div>
        </div>
        <div class="hero-cost-item">
          <div class="hci-icon">🏭</div>
          <div class="hci-value">{storage_cost:.1f} <span style="font-size:11px;font-weight:400">元/kg</span></div>
          <div class="hci-label">储存成本</div>
          <div class="hci-sub">(高压气态储氢·估算值)</div>
        </div>
        <div class="hero-cost-item">
          <div class="hci-icon">⛽</div>
          <div class="hci-value">{refuel_cost:.1f} <span style="font-size:11px;font-weight:400">元/kg</span></div>
          <div class="hci-label">加注成本</div>
          <div class="hci-sub">(加氢站运营摊销·估算值)</div>
        </div>
        <div class="hero-cost-item">
          <div class="hci-icon">📦</div>
          <div class="hci-value">{load_cost:.1f} <span style="font-size:11px;font-weight:400">元/kg</span></div>
          <div class="hci-label">装卸成本</div>
          <div class="hci-sub">(槽车装卸·估算值)</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════ 主渲染 ═══════════════════════
def render():
    sites = load_sites()
    stations = load_stations()
    stats = get_station_stats(stations)
    clusters = get_cluster_stats(stations)
    updated = get_updated_time()
    total_cap = sum(s.get("capacity", 0) for s in sites)

    st.caption(f"📅 数据更新于 {updated[:10] if updated else '—'} | 数据来源：示范城市群氢能供应明细表 | PIN 2026 解锁精确成本")

    # ═══════════════════ ① HERO ═══════════════════
    _render_hero("长管拖车20MPa")

    # ═══════════════════ ② KPI 精简行 ═══════════════════
    st.markdown('<p style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.8px;margin:0 0 8px;font-weight:600">核心指标</p>', unsafe_allow_html=True)
    avg_cost = sum(s.get("cost_avg", 0) for s in sites) / max(len(sites), 1)
    cost_lo = min(s.get("cost_low", 99) for s in sites) if sites else 0
    cost_hi = max(s.get("cost_high", 0) for s in sites) if sites else 0
    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-badge">
        <div class="kb-value">🏭 {len(sites)}</div>
        <div class="kb-label">制氢基地</div>
        <div class="kb-sub">总产能 {total_cap:,} t/y</div>
      </div>
      <div class="kpi-badge">
        <div class="kb-value">💰 ¥{avg_cost:.1f}</div>
        <div class="kb-label">平均成本 /kg</div>
        <div class="kb-sub">区间 ¥{cost_lo:.0f}–¥{cost_hi:.0f}</div>
      </div>
      <div class="kpi-badge">
        <div class="kb-value">⛽ {stats['count']}</div>
        <div class="kb-label">覆盖加氢站</div>
        <div class="kb-sub">日需求 {stats['total_throughput']:,} kg</div>
      </div>
      <div class="kpi-badge">
        <div class="kb-value">⭐ {stats['guohua_count']}/{stats['count']}</div>
        <div class="kb-label">国华供氢站</div>
        <div class="kb-sub">占比 {stats['guohua_count'] / max(stats['count'], 1) * 100:.0f}% · {updated[:10] if updated else '—'}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════ ③ 三卡片行 ═══════════════════
    st.markdown('<div class="triple-row">', unsafe_allow_html=True)

    # 左：基地成本对比
    st.markdown('<div class="triple-card"><div class="tc-title">基地成本对比 · ¥/kg</div>', unsafe_allow_html=True)
    for site in sites:
        color = {"风电+光伏电解": "#00a99d", "风电电解": "#00a99d", "光伏电解": "#2563eb",
                 "煤制氢+CCS": "#2563eb", "工业副产氢": "#d97706"}.get(site.get("tech", ""), "#64748b")
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid #f1f5f9">
          <span style="font-weight:700;font-size:12px;width:42px;color:#0f172a">{site['name']}</span>
          <div style="flex:1;height:5px;background:#f1f5f9;border-radius:3px;position:relative">
            <div style="position:absolute;left:{max(0, (site['cost_low'] - 8) / 22 * 100)}%;width:{min(100, (site['cost_high'] - site['cost_low']) / 22 * 100)}%;height:100%;background:{color};border-radius:3px;opacity:0.6"></div>
          </div>
          <span style="font-size:10.5px;color:#64748b;width:80px;text-align:right">¥{site['cost_low']}–¥{site['cost_high']}</span>
        </div>""", unsafe_allow_html=True)
    st.markdown('<div style="display:flex;justify-content:space-between;font-size:8px;color:#94a3b8;margin-top:3px;padding:0 42px"><span>¥8</span><span>¥15</span><span>¥22</span><span>¥30</span></div></div>', unsafe_allow_html=True)

    # 中：辐射圈覆盖概览
    st.markdown('<div class="triple-card"><div class="tc-title">200km 辐射圈覆盖概览</div>', unsafe_allow_html=True)
    from utils.geo_utils import haversine_km
    rows_html = ""
    for site in sites:
        cov_count = sum(1 for s in stations if haversine_km(s["lat"], s["lon"], site["lat"], site["lon"]) <= ECONOMIC_RADIUS_KM)
        cov_demand = sum(s.get("actual_throughput_kg", 0) for s in stations
                       if haversine_km(s["lat"], s["lon"], site["lat"], site["lon"]) <= ECONOMIC_RADIUS_KM)
        supply_daily = round(site["capacity"] / 365, 1)
        sufficiency = "充足" if supply_daily * 1000 > cov_demand else "不足"
        s_color = "#10b981" if sufficiency == "充足" else "#ef4444"
        rows_html += f"""
        <tr>
          <td style="font-weight:600;color:#0f172a">{site['name']}</td>
          <td>{cov_count} 站</td>
          <td>{cov_demand:,} kg</td>
          <td>{supply_daily} t/天</td>
          <td><span style="color:{s_color};font-weight:600;font-size:10.5px">{sufficiency}</span></td>
        </tr>"""
    st.markdown(f"""
    <table style="width:100%;font-size:11px;border-collapse:collapse">
      <thead><tr style="color:#64748b;font-size:9.5px;text-transform:uppercase;letter-spacing:0.4px">
        <th style="text-align:left;padding:6px 4px;border-bottom:2px solid #e2e8f0">基地</th>
        <th style="text-align:left;padding:6px 4px;border-bottom:2px solid #e2e8f0">覆盖</th>
        <th style="text-align:left;padding:6px 4px;border-bottom:2px solid #e2e8f0">日需求</th>
        <th style="text-align:left;padding:6px 4px;border-bottom:2px solid #e2e8f0">供给</th>
        <th style="text-align:left;padding:6px 4px;border-bottom:2px solid #e2e8f0">状态</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table></div>""", unsafe_allow_html=True)

    # 右：成本优势速览（新增）
    competitive_count = 0; total_cov = 0; gaps = []
    for site in sites:
        base_cost = GUOHUA_BASES_COST.get(site["name"], 15.2)
        for s in stations:
            d = haversine_km(s["lat"], s["lon"], site["lat"], site["lon"])
            if d <= ECONOMIC_RADIUS_KM:
                total_cov += 1
                landed = base_cost + d * TRANSPORT_MODES["长管拖车20MPa"]["cost_per_100km"] / 100
                retail = s.get("retail_price_kg") or s.get("real_price_kg") or 0
                if retail and landed < retail:
                    competitive_count += 1; gaps.append(retail - landed)
    avg_gap = np.mean(gaps) if gaps else 0
    pct = competitive_count / max(total_cov, 1) * 100
    st.markdown(f"""
    <div class="triple-card"><div class="tc-title">成本优势速览</div>
      <div class="advantage-card">
        <div class="av-big">{competitive_count}<span style="font-size:16px;color:#64748b"> / {total_cov}</span></div>
        <div class="av-pct">{pct:.0f}%</div>
        <div class="av-label">竞争优势站占比 · 辐射圈内</div>
        <div style="margin-top:14px;font-size:13px;color:#334155;font-weight:600">
          平均价差 <span style="color:{BRAND};font-size:22px">+{avg_gap:.1f}</span> 元/kg
        </div>
        <div style="font-size:10px;color:#94a3b8;margin-top:4px">国华到站价 vs 零售价（{TRANSPORT_MODES['长管拖车20MPa']['cost_per_100km']:.0f}元/100km·kg）</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════ ④ 快速入口 ═══════════════════
    st.markdown('<p style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.8px;margin:0 0 8px;font-weight:600">快速入口</p>', unsafe_allow_html=True)
    st.markdown('<div class="qnav-row">', unsafe_allow_html=True)
    navs = [
        ("🗺️", "基地地图", "查看四大基地位置 · 200km 辐射圈 · 竞品对标", "map"),
        ("⛽", "加氢站网络", "覆盖范围分析 · 市场机会发现 · 站级信息", "stations"),
        ("📊", "成本竞争力", "运输比选 · 销售场景 · 对标分析 · 导出", "cost"),
    ]
    qcols = st.columns(3)
    for col, (icon, title, desc, target) in zip(qcols, navs):
        with col:
            st.markdown(f"""
            <div class="qnav-card" style="margin-bottom:6px">
              <div class="qnav-icon">{icon}</div>
              <div class="qnav-title">{title}</div>
              <div class="qnav-desc">{desc}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"进入 {title} →", key=f"qnav_{target}", use_container_width=True):
                st.session_state.page = target
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════ ⑤ 底部 ═══════════════════
    r5l, r5r = st.columns([0.62, 0.38])
    with r5l:
        st.markdown('<p style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.8px;margin:0 0 8px;font-weight:600">基地状态</p>', unsafe_allow_html=True)
        scols = st.columns(len(sites))
        for col, site in zip(scols, sites):
            tech_color = {"风电+光伏电解": "#00a99d", "风电电解": "#00a99d", "光伏电解": "#2563eb",
                          "煤制氢+CCS": "#2563eb", "工业副产氢": "#d97706"}.get(site.get("tech", ""), "#64748b")
            util_color = "#10b981" if site.get("utilization", 0) >= 70 else "#d97706" if site.get("utilization", 0) >= 50 else "#ef4444"
            with col:
                st.markdown(f"""
                <div class="info-card" style="border-left-color:{tech_color}">
                  <div class="ic-title">{site['name']} <span style="font-size:9px;color:#94a3b8;font-weight:400">{site['province']}</span></div>
                  <div class="ic-row">
                    <span>产能 <b>{site['capacity']:,}t</b></span>
                    <span>成本 <b>¥{site['cost_avg']}</b></span>
                  </div>
                  <div class="ic-row" style="margin-top:2px">
                    <span>利用率 <b style="color:{util_color}">{site.get('utilization','—')}%</b></span>
                    <span>{site.get('cert_status','—')}</span>
                  </div>
                </div>""", unsafe_allow_html=True)

    with r5r:
        st.markdown('<p style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.8px;margin:0 0 8px;font-weight:600">数据状态</p>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="data-card">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
            <span style="width:8px;height:8px;border-radius:50%;background:#10b981"></span>
            <span style="font-weight:600;font-size:13px;color:#0f172a">平台运行中</span>
          </div>
          <div style="font-size:12px;color:#334155;line-height:1.8">
            <div>🏭 基地数据: <b>{len(sites)} 个</b></div>
            <div>⛽ 加氢站: <b>{stats['count']} 座</b></div>
            <div>⚠️ 竞品项目: <b>7 个</b></div>
            <div>📅 最后更新: <b>{updated[:10] if updated else '—'}</b></div>
            <div>🔗 部署: <b>Streamlit Cloud</b></div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.caption("v0.4.0 · 首页 v2.0 重构 · Hero 图 + 成本横栏 · P1–P4 ✅")

    with st.expander("📚 行业参考数据（Argus/BNEF/公开报告）", expanded=False):
        ref_tbl = [{"指标": k, "数值": v["value"], "来源": v["source"]} for k, v in REFERENCE_DATA.items()]
        st.dataframe(pd.DataFrame(ref_tbl), use_container_width=True, hide_index=True,
                    column_config={"来源": st.column_config.TextColumn(width="large")})
        st.caption("💡 数据来源：中国产业发展促进会氢能分会、全国碳市场、国家能源局、隆众资讯、ICE、IEA等。标注时间为公开值，实际以最新行情为准。")
