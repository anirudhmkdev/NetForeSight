"""Plotly chart builders and HTML card helpers (all local, offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from . import SEVERITY_COLORS

BG = "#070b16"
CARD = "#111a2e"
GRID = "rgba(148,163,184,0.15)"
TEXT = "#f1f5f9"
MUTED = "#94a3b8"
CYAN = "#22d3ee"
ORANGE = "#f59e0b"
RED = "#ff3b4d"

SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _base_layout(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": TEXT, "family": "Inter, Segoe UI, sans-serif"},
        margin={"l": 50, "r": 20, "t": 40, "b": 40},
        legend={"orientation": "h", "y": 1.08, "x": 0,
                "font": {"size": 11, "color": MUTED}},
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, tickfont={"color": MUTED})
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont={"color": MUTED})
    return fig


# --------------------------------------------------------------------------- #
# Forecast                                                                     #
# --------------------------------------------------------------------------- #

def risk_gauge(current_risk: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_risk,
        title={"text": "Current Risk", "font": {"color": TEXT, "size": 16}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": MUTED},
            "bar": {"color": RED if current_risk >= 70 else (ORANGE if current_risk >= 40 else CYAN)},
            "bgcolor": "rgba(255,255,255,0.05)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "rgba(34, 211, 238, 0.15)"},
                {"range": [40, 70], "color": "rgba(245, 158, 11, 0.15)"},
                {"range": [70, 100], "color": "rgba(255, 59, 77, 0.15)"}],
        }
    ))
    fig.update_layout(margin={"l": 20, "r": 20, "t": 40, "b": 20})
    return _base_layout(fig, height=280)


def risk_forecast_chart(forecast: dict) -> go.Figure:
    obs = forecast["observed_risk"]
    fut = forecast["forecast_risk"]
    thr = forecast["threshold"] * 100.0
    n_obs = len(obs)
    y_fut = [obs[-1]] + fut
    x_all = [f"T+{i}" for i in range(n_obs + len(y_fut) - 1)]
    x_obs = x_all[:n_obs]
    x_fut = x_all[n_obs - 1: n_obs - 1 + len(y_fut)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_obs, y=obs, mode="lines+markers",
                             name="Observed Risk", line={"color": CYAN, "width": 3},
                             marker={"size": 8, "color": CYAN},
                             hovertemplate="%{x}<br>Observed: %{y:.1f}%<extra></extra>"))
    band = 6.0
    fig.add_trace(go.Scatter(
        x=x_fut + x_fut[::-1],
        y=[v + band for v in y_fut] + [v - band for v in y_fut][::-1],
        fill="toself", fillcolor="rgba(251,146,60,0.15)",
        line={"width": 0}, showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x_fut, y=y_fut, mode="lines+markers",
                             name="Forecast Risk",
                             line={"color": ORANGE, "width": 3, "dash": "dash"},
                             marker={"size": 9, "color": ORANGE,
                                     "symbol": "diamond"},
                             hovertemplate="%{x}<br>Forecast: %{y:.1f}%<extra></extra>"))
    fig.add_hline(y=thr, line_dash="dot", line_color=RED, line_width=2,
                  annotation_text=f"Alert Threshold = {thr:.0f}%",
                  annotation_position="top right",
                  annotation_font_color=RED)
    now_x = x_obs[-1]
    fig.add_shape(type="line", x0=now_x, x1=now_x, xref="x",
                  y0=0, y1=1, yref="paper",
                  line={"dash": "dash", "color": MUTED, "width": 1})
    fig.add_annotation(x=now_x, y=97, xref="x", yref="y", text="NOW",
                       showarrow=False, font={"color": MUTED, "size": 10})
    if forecast.get("crosses_threshold") and forecast.get("crossing_index") is not None:
        cx = x_fut[1 + forecast["crossing_index"]] \
            if len(x_fut) > 1 + forecast["crossing_index"] else x_fut[-1]
        cy = fut[forecast["crossing_index"]]
        fig.add_trace(go.Scatter(x=[cx], y=[cy], mode="markers+text",
                                 name="Threshold crossing",
                                 marker={"size": 14, "color": RED,
                                         "symbol": "x"},
                                 text=["crossing"], textposition="top center",
                                 textfont={"color": RED, "size": 11},
                                 hovertemplate="Threshold crossed at %{x}: %{y:.1f}%<extra></extra>"))
    fig.update_yaxes(title="Risk (%)", range=[0, 100])
    fig.update_xaxes(title="Time window")
    fig.update_layout(title={"text": "Future Attack Risk Forecast", "x": 0,
                             "font": {"size": 16, "color": TEXT}})
    return _base_layout(fig, height=420)


def kstep_forecast_chart(future_stages: list[dict], current_risk: float, threshold: float = 70.0) -> go.Figure:
    x_obs = ["Now"]
    y_obs = [current_risk]
    
    x_fut = ["Now"] + [s["step"] for s in future_stages]
    y_fut = [current_risk] + [s["risk"] for s in future_stages]
    
    # Confidence band calculation (use confidence to derive uncertainty)
    # E.g. if confidence is 80%, uncertainty is +/- 10%
    y_upper = [current_risk] + [min(100, s["risk"] + (100 - s.get("confidence", 80)) / 2) for s in future_stages]
    y_lower = [current_risk] + [max(0, s["risk"] - (100 - s.get("confidence", 80)) / 2) for s in future_stages]

    fig = go.Figure()
    
    # Add confidence band
    fig.add_trace(go.Scatter(
        x=x_fut + x_fut[::-1],
        y=y_upper + y_lower[::-1],
        fill="toself", fillcolor="rgba(245,158,11,0.15)",
        line={"width": 0}, showlegend=False, hoverinfo="skip",
        name="Confidence Band"
    ))
    
    # Add Predicted Line
    fig.add_trace(go.Scatter(
        x=x_fut, y=y_fut, mode="lines+markers",
        name="Predicted Risk", line={"color": ORANGE, "width": 3, "dash": "dash"},
        marker={"size": 10, "color": ORANGE, "symbol": "diamond"},
        hovertemplate="Predicted (%{x}): %{y:.1f}%<extra></extra>"
    ))
    
    # Add Observed Point
    fig.add_trace(go.Scatter(
        x=x_obs, y=y_obs, mode="markers",
        name="Observed Risk", line={"color": CYAN},
        marker={"size": 12, "color": CYAN, "symbol": "circle"},
        hovertemplate="Observed (%{x}): %{y:.1f}%<extra></extra>"
    ))
    
    # Add Threshold
    fig.add_hline(y=threshold, line_dash="dot", line_color=RED, line_width=2,
                  annotation_text=f"Critical Threshold ({threshold:.0f}%)",
                  annotation_position="top left",
                  annotation_font_color=RED)

    fig.update_yaxes(title="Risk Score (%)", range=[0, 100])
    fig.update_xaxes(title="Forecast Step")
    fig.update_layout(title={"text": "K-Step Risk Trajectory", "x": 0, "font": {"size": 15, "color": TEXT}},
                      showlegend=True, legend={"orientation": "h", "y": -0.2, "x": 0})
    return _base_layout(fig, height=350)


def contribution_bar_chart(contributions: dict[str, float]) -> go.Figure:
    items = sorted(contributions.items(), key=lambda kv: kv[1])
    labels = [k for k, _ in items]
    values = [v for _, v in items]
    colors = ["#38bdf8", "#818cf8", "#22d3ee", "#34d399", "#a78bfa", "#fbbf24", "#fb923c", "#f87171"]
    bar_colors = colors[-len(labels):] if len(labels) <= len(colors) else (colors * 2)[-len(labels):]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker={"color": bar_colors},
        text=[f"{v:.0f}%" for v in values], textposition="outside",
        textfont={"color": TEXT},
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
    fig.update_xaxes(title="Contribution (%)", range=[0, max(values) * 1.35])
    fig.update_layout(title={"text": "Top Contributing Traffic Signals", "x": 0,
                             "font": {"size": 15, "color": TEXT}},
                      showlegend=False)
    return _base_layout(fig, height=360)


# --------------------------------------------------------------------------- #
# Analytics                                                                    #
# --------------------------------------------------------------------------- #

def risk_distribution_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty or "risk" not in df:
        return _base_layout(go.Figure(), height=260)
    
    counts = df["risk"].value_counts()
    labels = counts.index.tolist()
    values = counts.values.tolist()
    
    colors_map = {"LOW": "#22c55e", "MEDIUM": "#f59e0b", "HIGH": "#fb923c", "CRITICAL": "#ef4444"}
    marker_colors = [colors_map.get(l, MUTED) for l in labels]
    
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.6,
        marker={"colors": marker_colors},
        textinfo="label+percent", textfont={"color": TEXT},
        hovertemplate="%{label}: %{value:,} flows<extra></extra>"
    ))
    fig.update_layout(title={"text": "Risk Distribution", "x": 0.5, "font": {"size": 14, "color": TEXT}},
                      margin={"l": 10, "r": 10, "t": 30, "b": 10}, showlegend=False)
    return _base_layout(fig, height=260)

def protocol_distribution_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty or "protocol" not in df:
        return _base_layout(go.Figure(), height=260)
        
    counts = df["protocol"].value_counts()
    labels = counts.index.tolist()
    values = counts.values.tolist()
    
    fig = go.Figure(go.Bar(
        x=labels, y=values, marker={"color": CYAN},
        text=[f"{v:,}" for v in values], textposition="outside",
        textfont={"color": TEXT}, hovertemplate="%{x}: %{y:,} flows<extra></extra>"
    ))
    fig.update_layout(title={"text": "Protocol Distribution", "x": 0.5, "font": {"size": 14, "color": TEXT}},
                      margin={"l": 10, "r": 10, "t": 30, "b": 10}, showlegend=False)
    fig.update_yaxes(visible=False)
    return _base_layout(fig, height=260)

def activity_timeline_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty or "timestamp" not in df:
        return _base_layout(go.Figure(), height=260)
        
    df_sorted = df.sort_values("timestamp")
    # Bin into roughly 30 bins
    time_span = (df_sorted["timestamp"].max() - df_sorted["timestamp"].min()).total_seconds()
    freq = f"{max(1, int(time_span / 30))}s"
    
    timeline = df_sorted.set_index("timestamp").resample(freq).size().reset_index(name="count")
    
    fig = go.Figure(go.Scatter(
        x=timeline["timestamp"], y=timeline["count"],
        mode="lines", fill="tozeroy", line={"color": CYAN, "width": 2},
        fillcolor="rgba(34, 211, 238, 0.1)",
        hovertemplate="%{x|%H:%M:%S}: %{y} flows<extra></extra>"
    ))
    fig.update_layout(title={"text": "Traffic Activity Timeline", "x": 0.5, "font": {"size": 14, "color": TEXT}},
                      margin={"l": 10, "r": 10, "t": 30, "b": 10}, showlegend=False)
    fig.update_xaxes(title="")
    fig.update_yaxes(title="")
    return _base_layout(fig, height=260)


def stage_distribution_chart(flows: pd.DataFrame) -> go.Figure:
    from . import stage_for_risk
    stages = flows["risk_score"].apply(lambda s: stage_for_risk(s * 100))
    order = ["Reconnaissance", "Initial Access", "Lateral Movement",
             "Command & Control", "Exfiltration"]
    counts = stages.value_counts()
    vals = [int(counts.get(s, 0)) for s in order]
    fig = go.Figure(go.Bar(
        x=order, y=vals, marker={"color": ["#38bdf8", "#22d3ee", "#fb923c", "#f87171", "#a855f7"]},
        text=vals, textposition="outside", textfont={"color": TEXT},
        hovertemplate="%{x}: %{y} flows<extra></extra>"))
    fig.update_xaxes(tickangle=-18)
    fig.update_layout(title={"text": "Attack Stage Distribution", "x": 0,
                             "font": {"size": 14, "color": TEXT}},
                      showlegend=False)
    return _base_layout(fig, height=340)


def risk_histogram(flows: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Histogram(
        x=flows["risk_score"] * 100, nbinsx=30,
        marker={"color": CYAN, "line": {"color": BG, "width": 0.5}},
        hovertemplate="Risk %{x:.0f}%: %{y} flows<extra></extra>"))
    fig.update_xaxes(title="Flow risk score (%)")
    fig.update_yaxes(title="Flows")
    fig.update_layout(title={"text": "Risk Distribution", "x": 0,
                             "font": {"size": 14, "color": TEXT}},
                      showlegend=False)
    return _base_layout(fig, height=340)


def suspicious_timeseries(flows: pd.DataFrame) -> go.Figure:
    df = flows.copy()
    df["bucket"] = df["timestamp"].dt.floor("30s")
    total = df.groupby("bucket").size()
    susp = df[df["risk"].isin(["HIGH", "CRITICAL"])].groupby("bucket").size()
    idx = total.index
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=idx, y=total.values, mode="lines",
                             name="All flows", line={"color": CYAN, "width": 2},
                             hovertemplate="%{x|%H:%M:%S}<br>%{y} flows<extra></extra>"))
    fig.add_trace(go.Scatter(x=susp.index, y=susp.values, mode="lines+markers",
                             name="Suspicious", line={"color": RED, "width": 2},
                             marker={"size": 5},
                             hovertemplate="%{x|%H:%M:%S}<br>%{y} suspicious<extra></extra>"))
    fig.update_xaxes(title="Time")
    fig.update_yaxes(title="Flows / 30 s")
    fig.update_layout(title={"text": "Suspicious Traffic Over Time", "x": 0,
                             "font": {"size": 14, "color": TEXT}})
    return _base_layout(fig, height=340)


def protocol_donut(flows: pd.DataFrame) -> go.Figure:
    counts = flows["protocol"].value_counts()
    fig = go.Figure(go.Pie(
        labels=counts.index.tolist(), values=counts.values.tolist(), hole=0.55,
        marker={"colors": [CYAN, ORANGE, "#a855f7", "#22c55e", MUTED]},
        textinfo="label+percent", textfont={"color": TEXT},
        hovertemplate="%{label}: %{value} flows<extra></extra>"))
    fig.update_layout(title={"text": "Protocol Distribution", "x": 0,
                             "font": {"size": 14, "color": TEXT}},
                      showlegend=False)
    return _base_layout(fig, height=340)


def top_ports_chart(flows: pd.DataFrame, top_n: int = 8) -> go.Figure:
    counts = flows["dst_port"].value_counts().head(top_n).sort_values()
    fig = go.Figure(go.Bar(
        x=counts.values, y=[f"Port {p}" for p in counts.index], orientation="h",
        marker={"color": ORANGE},
        text=counts.values, textposition="outside", textfont={"color": TEXT},
        hovertemplate="%{y}: %{x} flows<extra></extra>"))
    fig.update_xaxes(title="Flows")
    fig.update_layout(title={"text": "Top Targeted Ports", "x": 0,
                             "font": {"size": 14, "color": TEXT}},
                      showlegend=False)
    return _base_layout(fig, height=340)


def flow_volume_chart(flows: pd.DataFrame) -> go.Figure:
    df = flows.copy()
    df["bucket"] = df["timestamp"].dt.floor("30s")
    vol = df.groupby("bucket").size()
    fig = go.Figure(go.Scatter(x=vol.index, y=vol.values, mode="lines",
                               fill="tozeroy", fillcolor="rgba(34,211,238,0.15)",
                               line={"color": CYAN, "width": 2},
                               hovertemplate="%{x|%H:%M:%S}<br>%{y} flows<extra></extra>"))
    fig.update_xaxes(title="Time")
    fig.update_yaxes(title="Flows / 30 s")
    fig.update_layout(title={"text": "Flow Volume", "x": 0,
                             "font": {"size": 14, "color": TEXT}},
                      showlegend=False)
    return _base_layout(fig, height=340)


def window_risk_chart(windows) -> go.Figure:
    labels = [f"W{w.id}" for w in windows]
    risks = [w.risk for w in windows]
    colors = [SEVERITY_COLORS[
        "CRITICAL" if r >= 80 else "HIGH" if r >= 60 else "MEDIUM" if r >= 35 else "LOW"]
        for r in risks]
    fig = go.Figure(go.Bar(x=labels, y=risks, marker={"color": colors},
                           text=[f"{r:.0f}%" for r in risks],
                           textposition="outside", textfont={"color": TEXT},
                           hovertemplate="%{x}: %{y:.1f}%<extra></extra>"))
    fig.update_yaxes(title="Window risk (%)", range=[0, 100])
    fig.update_layout(title={"text": "Risk by Network State Window", "x": 0,
                             "font": {"size": 14, "color": TEXT}},
                      showlegend=False)
    return _base_layout(fig, height=300)


# --------------------------------------------------------------------------- #
# Network graph                                                                #
# --------------------------------------------------------------------------- #

GRAPH_NODES = [
    {"ip": "203.0.113.7", "role": "External Client", "x": 0.0, "y": 2.0},
    {"ip": "10.0.1.1", "role": "Gateway", "x": 1.0, "y": 2.0},
    {"ip": "10.0.2.15", "role": "Compromised Host (suspect)", "x": 2.0, "y": 2.6},
    {"ip": "10.0.2.0/24", "role": "Workstations", "x": 2.0, "y": 1.4},
    {"ip": "10.0.4.21", "role": "Server A (targeted)", "x": 3.2, "y": 2.8},
    {"ip": "10.0.4.22", "role": "Server B (targeted)", "x": 3.2, "y": 2.0},
    {"ip": "10.0.4.27", "role": "Server C (targeted)", "x": 3.2, "y": 1.2},
]

GRAPH_EDGES = [
    ("203.0.113.7", "10.0.1.1", False),
    ("10.0.1.1", "10.0.2.15", False),
    ("10.0.1.1", "10.0.2.0/24", False),
    ("10.0.2.15", "10.0.4.21", True),
    ("10.0.2.15", "10.0.4.22", True),
    ("10.0.2.15", "10.0.4.27", True),
    ("10.0.2.0/24", "10.0.4.21", False),
    ("10.0.2.0/24", "10.0.4.22", False),
]


def network_graph_figure(selected_ip: str | None = None) -> go.Figure:
    pos = {n["ip"]: (n["x"], n["y"]) for n in GRAPH_NODES}
    fig = go.Figure()
    for a, b, susp in GRAPH_EDGES:
        x0, y0 = pos[a]
        x1, y1 = pos[b]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode="lines",
            line={"color": RED if susp else "rgba(148,163,184,0.5)",
                  "width": 3 if susp else 1.5,
                  "dash": "solid" if susp else "dot"},
            showlegend=False, hoverinfo="skip"))
    for n in GRAPH_NODES:
        susp = n["ip"] == "10.0.2.15" or "(targeted)" in n["role"]
        sel = n["ip"] == selected_ip
        fig.add_trace(go.Scatter(
            x=[n["x"]], y=[n["y"]], mode="markers+text",
            marker={"size": 30 if sel else 22,
                    "color": RED if n["ip"] == "10.0.2.15" else
                    (ORANGE if susp else CYAN),
                    "line": {"color": "#fff" if sel else BG, "width": 3 if sel else 2}},
            text=[n["role"]], textposition="bottom center",
            textfont={"color": TEXT, "size": 10},
            name=n["ip"],
            hovertemplate=f"{n['ip']}<br>{n['role']}<extra></extra>"))
    fig.update_xaxes(visible=False, range=[-0.4, 3.7])
    fig.update_yaxes(visible=False, range=[0.6, 3.3])
    fig.update_layout(title={"text": "Network Graph — suspicious paths highlighted",
                             "x": 0, "font": {"size": 14, "color": TEXT}},
                      showlegend=False)
    return _base_layout(fig, height=420)


# --------------------------------------------------------------------------- #
# HTML helpers                                                                 #
# --------------------------------------------------------------------------- #

def kpi_card(label: str, value: str, sub: str = "", accent: str = CYAN) -> str:
    return f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value" style="color:{accent}">{value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>"""

def kpi_row_traffic(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return ""
    
    total = f"{len(df):,}"
    suspicious = f"{len(df[df['risk'].isin(['HIGH', 'CRITICAL'])]) if 'risk' in df else 'N/A':,}"
    critical = f"{len(df[df['risk'] == 'CRITICAL']) if 'risk' in df else 'N/A':,}"
    src_ips = f"{df['src_ip'].nunique():,}"
    dst_ips = f"{df['dst_ip'].nunique():,}"
    packets = f"{df['packets'].sum():,}"
    
    html = f"""
    <div style="display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 140px; background: #111A2E; border: 1px solid #26364F; border-radius: 8px; padding: 16px; display: flex; flex-direction: column;">
            <div style="font-size: 12px; color: #94A3B8; font-weight: 600; text-transform: uppercase;">Total Flows</div>
            <div style="font-size: 24px; color: {CYAN}; font-weight: 700; margin-top: 8px;">{total}</div>
        </div>
        <div style="flex: 1; min-width: 140px; background: #111A2E; border: 1px solid #26364F; border-radius: 8px; padding: 16px; display: flex; flex-direction: column;">
            <div style="font-size: 12px; color: #94A3B8; font-weight: 600; text-transform: uppercase;">Suspicious Flows</div>
            <div style="font-size: 24px; color: {ORANGE}; font-weight: 700; margin-top: 8px;">{suspicious}</div>
        </div>
        <div style="flex: 1; min-width: 140px; background: #111A2E; border: 1px solid #26364F; border-radius: 8px; padding: 16px; display: flex; flex-direction: column;">
            <div style="font-size: 12px; color: #94A3B8; font-weight: 600; text-transform: uppercase;">Critical Risk</div>
            <div style="font-size: 24px; color: {RED}; font-weight: 700; margin-top: 8px;">{critical}</div>
        </div>
        <div style="flex: 1; min-width: 140px; background: #111A2E; border: 1px solid #26364F; border-radius: 8px; padding: 16px; display: flex; flex-direction: column;">
            <div style="font-size: 12px; color: #94A3B8; font-weight: 600; text-transform: uppercase;">Unique Sources</div>
            <div style="font-size: 24px; color: {CYAN}; font-weight: 700; margin-top: 8px;">{src_ips}</div>
        </div>
        <div style="flex: 1; min-width: 140px; background: #111A2E; border: 1px solid #26364F; border-radius: 8px; padding: 16px; display: flex; flex-direction: column;">
            <div style="font-size: 12px; color: #94A3B8; font-weight: 600; text-transform: uppercase;">Unique Dests</div>
            <div style="font-size: 24px; color: {CYAN}; font-weight: 700; margin-top: 8px;">{dst_ips}</div>
        </div>
        <div style="flex: 1; min-width: 140px; background: #111A2E; border: 1px solid #26364F; border-radius: 8px; padding: 16px; display: flex; flex-direction: column;">
            <div style="font-size: 12px; color: #94A3B8; font-weight: 600; text-transform: uppercase;">Total Packets</div>
            <div style="font-size: 24px; color: {CYAN}; font-weight: 700; margin-top: 8px;">{packets}</div>
        </div>
    </div>
    """
    return html


def severity_badge(sev: str) -> str:
    color = SEVERITY_COLORS.get(sev, MUTED)
    return (f'<span class="badge" style="border-color:{color};color:{color}">'
            f'{sev}</span>')


def timeline_html(timeline: list[dict], predicted_stage: str,
                  confidence: float) -> str:
    style = {"Observed": ("✓", "#22C55E", "solid"),
             "Suspected": ("◐", "#F59E0B", "solid"),
             "Predicted": ("⚠", "#FF3B4D", "dashed"),
             "Future": ("○", "#94A3B8", "dotted")}
    cards = []
    for i, item in enumerate(timeline):
        mark, color, border = style[item["state"]]
        tag = (f'<span class="badge" style="border-color:{color};color:{color}">'
               f'{item["state"].upper()}</span>')
        arrow = '<div class="tl-arrow">↓</div>' if i < len(timeline) - 1 else ""
        cards.append(f"""
        <div class="tl-card" style="border:1px {border} {color}55">
          <div style="font-size:20px;color:{color}">{mark}</div>
          <div class="tl-stage">{item["stage"]}</div>
          <div style="margin-top:6px">{tag}</div>
        </div>{arrow}""")
    return f"""
    <div class="tl-wrap">{''.join(cards)}</div>
    <div style="display:flex;gap:12px;margin-top:14px;flex-wrap:wrap">
      <div class="info-chip">Predicted Next Stage: <b style="color:{ORANGE}">
        {predicted_stage.upper()}</b></div>
      <div class="info-chip">Confidence: <b style="color:{CYAN}">
        {confidence:.0f}%</b></div>
    </div>"""

# --------------------------------------------------------------------------- #
# Premium Cyberpunk Flowchart                                                  #
# --------------------------------------------------------------------------- #

NEON_STAGES = [
    {"id": "01", "title": "File Loaded", "desc": "Load CSV/PCAP data<br>into system", "color": "#0ea5e9", 
     "icon": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><polyline points="9 15 12 12 15 15"></polyline></svg>'},
    {"id": "02", "title": "Feature Extraction", "desc": "Extract relevant<br>network features", "color": "#14b8a6",
     "icon": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>'},
    {"id": "03", "title": "Normalization", "desc": "Normalize and<br>scale features", "color": "#06b6d4",
     "icon": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'},
    {"id": "04", "title": "Time Window", "desc": "Create sequential<br>time windows", "color": "#a855f7",
     "icon": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'},
    {"id": "05", "title": "State Rep.", "desc": "Convert to model<br>input format", "color": "#f59e0b",
     "icon": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>'},
    {"id": "06", "title": "Forecasting", "desc": "Predict future<br>network states", "color": "#ef4444",
     "icon": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"></path><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"></path></svg>'},
    {"id": "07", "title": "Explainability", "desc": "Generate feature<br>importance", "color": "#ec4899",
     "icon": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>'},
    {"id": "08", "title": "Analysis Complete", "desc": "Results ready<br>for visualization", "color": "#10b981",
     "icon": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><polyline points="9 12 11 14 15 10"></polyline></svg>'}
]

def neon_workflow_html(current_step: int, failed: bool = False, stats: dict = None, logs: list = None, ds_info: dict = None, disabled: bool = False, is_demo: bool = False) -> str:
    if stats is None: stats = {}
    if logs is None: logs = []
    
    total = len(NEON_STAGES)
    completed_count = current_step if not failed else current_step
    if current_step >= total:
        completed_count = total
        
    cards = []
    for i, stg in enumerate(NEON_STAGES):
        is_completed = i < current_step and not disabled
        is_active = i == current_step and not disabled
        
        if disabled:
            border_color = "#1E293B"
            box_shadow = "none"
            icon_color = "#475569"
            status_html = f'<div style="color: #475569; font-size: 10px; font-weight: 600; text-align: center; padding: 2px 6px; margin-top: 6px;">Waiting</div>'
        elif is_completed:
            border_color = stg["color"]
            box_shadow = f"drop-shadow(0 0 6px {stg['color']}88)"
            icon_color = stg["color"]
            status_html = f'<div style="color: #00E6A0; font-size: 10px; font-weight: 600; display:flex; align-items:center; gap:4px; justify-content:center; background: rgba(0,230,160,0.1); padding: 2px 6px; border-radius: 4px; margin-top: 6px;"><span>✓</span> Done</div>'
        elif is_active:
            border_color = "#FF3B4D" if failed else stg["color"]
            box_shadow = f"drop-shadow(0 0 10px {border_color})"
            icon_color = border_color
            status_text = "Failed" if failed else "Processing"
            status_color = "#FF3B4D" if failed else "#F1F5F9"
            bg = "rgba(255,59,77,0.1)" if failed else f"rgba({int(border_color[1:3],16)},{int(border_color[3:5],16)},{int(border_color[5:7],16)},0.2)"
            status_html = f'<div style="color: {status_color}; font-size: 10px; font-weight: 600; text-align: center; background: {bg}; padding: 2px 6px; border-radius: 4px; margin-top: 6px;">{status_text}</div>'
        else:
            border_color = "#1E293B"
            box_shadow = "none"
            icon_color = "#475569"
            status_html = f'<div style="color: #475569; font-size: 10px; font-weight: 600; text-align: center; padding: 2px 6px; margin-top: 6px;">Waiting</div>'
            
        step_stats = stats.get(i, {})
        dur = step_stats.get("duration", "—") if not disabled else "—"
        
        arrow_html = f'<div style="position: absolute; right: -18px; top: 40%; transform: translateY(-50%); color: #16D9F5; font-size: 18px; font-weight: bold; z-index: 5;">→</div>' if i < total - 1 else ''
        
        card = f"""
<div class="wf-card-wrapper" style="flex: 0 0 145px; display: flex; flex-direction: column; align-items: center; position: relative;">
<div style="width: 100%; position: relative; background: #0D1B31; border: 1px solid {border_color}; border-radius: 8px; filter: {box_shadow}; display: flex; flex-direction: column; align-items: center; text-align: center; flex: 1; padding: 12px 8px;">
<div style="position: absolute; top: -10px; left: -6px; background: #071426; width: 22px; height: 22px; border-radius: 50%; border: 1px solid {border_color}; display: flex; align-items: center; justify-content: center; color: #F1F5F9; font-size: 10px; font-weight: bold; z-index: 10; box-shadow: 0 0 6px {border_color};">
{stg["id"]}
</div>
<div style="color: {icon_color}; margin-bottom: 8px; display: flex; justify-content: center;">{stg['icon']}</div>
<div style="font-size: 12px; font-weight: 700; color: #F1F5F9; line-height: 1.2; margin-bottom: 4px;">{stg['title']}</div>
<div style="font-size: 10px; color: #94A3B8; line-height: 1.2; flex: 1;">{stg['desc']}</div>
<div style="width: 100%;">{status_html}</div>
<div style="font-size: 10px; color: #cbd5e1; margin-top: 6px; display: flex; align-items: center; justify-content: center; gap: 4px;"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg> {dur}</div>
</div>
<!-- Stem and Dot for Bottom Connector -->
<div style="width: 2px; height: 12px; background: #16D9F5; box-shadow: 0 0 4px #16D9F5; z-index: 2;"></div>
<div style="width: 8px; height: 8px; border-radius: 50%; background: #071426; border: 2px solid #16D9F5; box-shadow: 0 0 8px #16D9F5; z-index: 3;"></div>
<!-- Connecting Arrow -->
{arrow_html}
</div>
"""
        cards.append(card.strip())
        
    pct = int((completed_count / total) * 100) if current_step > 0 and not disabled else 0
    if current_step >= total and not disabled: pct = 100
    if disabled: pct = 0
    
    log_rows = "<br>".join(logs)
    
    success_html = ""
    if disabled:
        success_html = f"""
<div class="wf-summary-panel" style="flex: 4.2; min-width: 280px; background: #0D1B31; border: 1px solid #1E293B; border-radius: 8px; padding: 16px; display: flex; align-items: center; justify-content: center;">
<div style="color: #475569; font-size: 13px;">Analysis Not Started</div>
</div>
"""
    elif current_step >= total and not failed:
        recs = ds_info.get("records", 0) if ds_info else 0
        feats = stats.get(1, {}).get("output", "42 features").split(" ")[0]
        tot_time = round(sum([float(stats[k].get("duration", "0s").replace("s","")) for k in stats if k != total]), 1)
        
        demo_badge = f'<div style="font-size: 10px; font-weight: bold; color: #F59E0B; background: rgba(245,158,11,0.15); padding: 2px 6px; border-radius: 4px; display: inline-block; margin-top: 4px;">SIMULATED RESULTS</div>' if is_demo else ""
        
        success_html = f"""
<div class="wf-summary-panel" style="flex: 4.2; min-width: 280px; background: #0D1B31; border: 1px solid #00E6A0; border-radius: 8px; padding: 16px; box-shadow: inset 0 0 15px rgba(0, 230, 160, 0.05), 0 0 10px rgba(0, 230, 160, 0.1);">
<div style="display: flex; gap: 12px; align-items: center; margin-bottom: 12px;">
<div style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid #00E6A0; display: flex; align-items: center; justify-content: center; color: #00E6A0; box-shadow: 0 0 12px rgba(0,230,160,0.3);">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
</div>
<div>
<div style="font-size: 15px; font-weight: bold; color: #F1F5F9;">Processing Completed Successfully!</div>
<div style="font-size: 11px; color: #94A3B8; margin-top: 2px;">Analysis is ready for visualization.</div>
{demo_badge}
</div>
</div>
<div style="display: flex; gap: 8px;">
<div style="flex: 1; background: #071426; border-radius: 6px; padding: 8px; display: flex; align-items: center; gap: 8px;">
<div style="color: #16D9F5;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg></div>
<div><div style="font-size: 9px; color: #94A3B8;">Records Processed</div><div style="font-size: 13px; font-weight: bold; color: #F1F5F9;">{recs:,}</div></div>
</div>
<div style="flex: 1; background: #071426; border-radius: 6px; padding: 8px; display: flex; align-items: center; gap: 8px;">
<div style="color: #16D9F5;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 16 14"></polyline></svg></div>
<div><div style="font-size: 9px; color: #94A3B8;">Total Time</div><div style="font-size: 13px; font-weight: bold; color: #F1F5F9;">{tot_time}s</div></div>
</div>
<div style="flex: 1; background: #071426; border-radius: 6px; padding: 8px; display: flex; align-items: center; gap: 8px;">
<div style="color: #16D9F5;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg></div>
<div><div style="font-size: 9px; color: #94A3B8;">Features</div><div style="font-size: 13px; font-weight: bold; color: #F1F5F9;">{feats}</div></div>
</div>
</div>
</div>
"""
    else:
        success_html = f"""
<div class="wf-summary-panel" style="flex: 4.2; min-width: 280px; background: #0D1B31; border: 1px solid #1E293B; border-radius: 8px; padding: 16px; display: flex; align-items: center; justify-content: center;">
<div style="color: #475569; font-size: 13px;">Processing in Progress...</div>
</div>
"""
        
    if disabled:
        status_color = "#475569"
        status_text = "No file uploaded"
        status_sub = "Waiting for data"
        status_icon = '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path>'
        header_title = "Upload a CSV or PCAP file to start network traffic analysis."
        header_sub = "Processing Workflow"
    elif failed:
        status_color = "#FF3B4D"
        status_text = "Processing Failed"
        status_sub = "An error occurred"
        status_icon = '<line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>'
        header_title = "Processing Workflow"
        header_sub = "From raw network data to AI-powered threat forecast"
    elif current_step >= total:
        status_color = "#00E6A0"
        status_text = "Processing Complete"
        status_sub = "All steps finished"
        status_icon = '<polyline points="20 6 9 17 4 12"></polyline>'
        header_title = "Processing Workflow"
        header_sub = "From raw network data to AI-powered threat forecast"
    else:
        status_color = "#16D9F5"
        status_text = "Processing..."
        status_sub = f"Stage {current_step+1}/{total}"
        status_icon = '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>'
        header_title = "Processing Workflow"
        header_sub = "From raw network data to AI-powered threat forecast"

    header_html = f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
<div style="display: flex; gap: 12px; align-items: center;">
<div style="position: relative; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; color: #16D9F5;">
<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 6px #16D9F5);"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path><circle cx="12" cy="12" r="2" fill="#16D9F5"></circle><circle cx="12" cy="17" r="2" fill="#16D9F5"></circle><line x1="12" y1="12" x2="12" y2="7"></line><line x1="12" y1="17" x2="12" y2="12"></line></svg>
</div>
<div>
<h2 style="margin: 0; font-size: 22px; font-weight: 800; color: #F1F5F9; letter-spacing: -0.5px;">{header_title}</h2>
<div style="font-size: 13px; color: #94A3B8; margin-top: 2px;">{header_sub}</div>
</div>
</div>
<div style="display: flex; align-items: center; gap: 8px; background: rgba(13, 27, 49, 0.6); border: 1px solid #1E293B; border-radius: 6px; padding: 6px 12px;">
<div style="width: 8px; height: 8px; border-radius: 50%; background: {status_color}; box-shadow: 0 0 8px {status_color};"></div>
<div>
<div style="font-size: 12px; font-weight: bold; color: #F1F5F9; line-height: 1.1;">{status_text}</div>
<div style="font-size: 10px; color: #94A3B8; line-height: 1.1;">{status_sub}</div>
</div>
<div style="margin-left: 8px; width: 26px; height: 26px; border-radius: 4px; border: 1px solid {status_color}; display: flex; align-items: center; justify-content: center; color: {status_color}; box-shadow: inset 0 0 6px rgba({int(status_color[1:3],16)}, {int(status_color[3:5],16)}, {int(status_color[5:7],16)}, 0.2);">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">{status_icon}</svg>
</div>
</div>
</div>
"""

    cards_str = '\n'.join(cards)
    
    html = f"""
<div style="margin-bottom: 20px; padding: 20px; background: #071426; border-radius: 12px; border: 1px solid #1e293b; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
{header_html}
<div style="width: 100%; overflow-x: auto; padding-bottom: 15px; margin-bottom: 15px;">
<div style="display: flex; gap: 24px; min-width: max-content; padding: 12px 10px 4px 10px; position: relative;">
{cards_str}
<!-- Glowing cyan connector line underneath all cards -->
<div style="position: absolute; bottom: 8px; left: 75px; right: 75px; height: 2px; background: #16D9F5; box-shadow: 0 0 8px #16D9F5; z-index: 1;"></div>
</div>
</div>
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
<div style="flex: 1; height: 8px; background: #0D1B31; border-radius: 4px; overflow: hidden; border: 1px solid #1E293B;">
<div style="width: {pct}%; height: 100%; background: #00E6A0; box-shadow: 0 0 10px #00E6A0; transition: width 0.5s ease;"></div>
</div>
<div style="font-size: 13px; font-weight: bold; color: #F1F5F9; min-width: 35px; text-align: right;">{pct}%</div>
</div>
<div style="display: flex; gap: 16px; flex-wrap: wrap; align-items: stretch;">
<div class="wf-log-panel" style="flex: 5.8; min-width: 320px; background: #0D1B31; border: 1px solid #2196F3; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column;">
<div style="padding: 10px 14px; background: #071426; border-bottom: 1px solid #2196F3; display: flex; align-items: center; gap: 8px;">
<div style="color: #2196F3; display: flex; align-items: center; justify-content: center;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg></div>
<div style="font-size: 13px; font-weight: bold; color: #F1F5F9;">Processing Log</div>
</div>
<div style="padding: 14px; font-family: monospace; font-size: 12px; color: #cbd5e1; line-height: 1.5; flex: 1; max-height: 150px; overflow-y: auto;">
{log_rows if (log_rows and not disabled) else '<span style="color:#475569;">No processing activity yet. Upload a file to begin.</span>'}
</div>
</div>
{success_html}
</div>
</div>
"""
    return html

# --------------------------------------------------------------------------- #
# Workflow Flowchart                                                           #
# --------------------------------------------------------------------------- #

WORKFLOW_STAGES = [
    ("File Loaded", "📂", "Raw traffic ingested"),
    ("Feature Extraction", "⚙", "Flow signatures built"),
    ("Normalization", "⚖", "Scaled traffic properties"),
    ("Time Window Generation", "⏱", "Temporal sequences"),
    ("State Representation", "▦", "World model inputs"),
    ("Forecasting", "🔮", "AI trajectory inference"),
    ("Explainability", "🔍", "SHAP attribution"),
    ("Analysis Complete", "✅", "Results ready")
]

def workflow_html(current_step: int, failed: bool = False, stats: dict = None) -> str:
    if stats is None:
        stats = {}
        
    cards = []
    total = len(WORKFLOW_STAGES)
    completed_count = current_step if not failed else current_step
    if current_step >= total:
        completed_count = total
    
    for i, (title, icon, desc) in enumerate(WORKFLOW_STAGES):
        # Determine status
        if i < current_step:
            status = "Completed"
            color = "#22C55E" # Green
            border = f"1px solid {color}"
            shadow = f"0 0 10px rgba(34, 197, 94, 0.2)"
            icon_color = color
        elif i == current_step:
            if failed:
                status = "Failed"
                color = "#FF3B4D" # Red
                border = f"1px solid {color}"
                shadow = f"0 0 15px rgba(255, 59, 77, 0.5)"
                icon_color = color
            else:
                status = "Processing"
                color = "#22D3EE" # Cyan
                border = f"1px solid {color}"
                shadow = f"0 0 15px rgba(34, 211, 238, 0.4)"
                icon_color = color
        else:
            status = "Waiting"
            color = "#94A3B8" # Muted
            border = "1px solid #26364F"
            shadow = "none"
            icon_color = "#475569"
            
        # Get details from stats
        step_stats = stats.get(i, {})
        dur = step_stats.get("duration", "N/A")
        out_info = step_stats.get("output", "N/A")
        err_msg = step_stats.get("error", "")
        
        err_html = f'<div style="color:#FF3B4D; margin-top:4px;">{err_msg}</div>' if err_msg else ""
        
        card = f"""
        <div style="background: #111A2E; border: {border}; border-radius: 10px; padding: 12px; min-width: 160px; max-width: 200px; flex: 1; box-shadow: {shadow}; transition: all 0.3s ease;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="font-size: 20px; color: {icon_color};">{icon}</div>
                <div style="font-size: 13px; font-weight: 700; color: #F1F5F9; line-height: 1.1;">{i+1}. {title}</div>
            </div>
            <div style="font-size: 11px; color: #94A3B8; margin-top: 6px;">{desc}</div>
            <div style="font-size: 11px; color: {color}; font-weight: 600; margin-top: 4px; text-transform: uppercase;">{status}</div>
            <details style="margin-top: 8px; font-size: 11px;">
               <summary style="cursor: pointer; color: #22D3EE; font-size: 11px; font-weight: 600; outline: none;">View Details</summary>
               <div style="margin-top: 4px; padding: 6px; background: rgba(0,0,0,0.2); border-radius: 4px; color: #cbd5e1; word-wrap: break-word;">
                 Duration: {dur}<br>
                 Output: {out_info}
                 {err_html}
               </div>
            </details>
        </div>
        """
        cards.append(card)
        if i < total - 1:
            cards.append(f'<div style="color: #475569; font-size: 20px;">→</div>')
            
    pct = int((completed_count / (total - 1)) * 100) if current_step > 0 else 0
    if current_step >= total: pct = 100
    
    bar_color = "#FF3B4D" if failed else "#22D3EE"
    if current_step >= total and not failed: bar_color = "#22C55E"
    
    html = f"""
    <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: center; margin-bottom: 24px;">
        {''.join(cards)}
    </div>
    <div style="width: 100%; height: 6px; background: #111A2E; border-radius: 3px; overflow: hidden; margin-bottom: 8px; border: 1px solid #26364F;">
       <div style="width: {pct}%; height: 100%; background: {bar_color}; transition: width 0.5s ease;"></div>
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 13px; color: #94A3B8; margin-bottom: 16px;">
      <span>Overall Progress: {pct}%</span>
      <span>{completed_count} / {total} Stages</span>
    </div>
    """
    return html

def model_status_card(model_name: str, is_demo: bool) -> str:
    status_text = "Forecast Engine Ready" if not is_demo else "Forecast Engine Ready (Demo)"
    mode_text = "Simulated Inference" if is_demo else "Live Inference"
    return f"""
<div style="background: #111A2E; border: 1px solid #26364F; border-radius: 8px; padding: 16px; height: 100%; display: flex; flex-direction: column; justify-content: center;">
    <div style="color: #94a3b8; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 8px;">Model Status</div>
    <div style="color: #22d3ee; font-size: 18px; font-weight: bold; margin-bottom: 4px;">{status_text}</div>
    <div style="color: #cbd5e1; font-size: 14px; margin-bottom: 12px;">{model_name}</div>
    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <span style="background: #0f172a; border: 1px solid #334155; padding: 2px 8px; border-radius: 4px; font-size: 11px; color: #94a3b8;">{mode_text}</span>
        <span style="background: #0f172a; border: 1px solid #334155; padding: 2px 8px; border-radius: 4px; font-size: 11px; color: #94a3b8;">ATT&CK Mapping Active</span>
    </div>
</div>
"""

def forecast_warning_block_v2(crosses_threshold: bool, threshold: float, crossing_stage: str, crossing_risk: float, step: str) -> str:
    if not crosses_threshold:
        return ""
    
    # Critical if risk > 90, High if > threshold
    sev_color = "#ef4444" if crossing_risk > 90 else "#f59e0b"
    sev_text = "CRITICAL RISK" if crossing_risk > 90 else "HIGH RISK"
    
    return f"""
<div style="background: rgba(255, 59, 77, 0.05); border-left: 4px solid {sev_color}; border-radius: 0 8px 8px 0; padding: 16px; margin: 20px 0;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
        <div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="background: {sev_color}22; color: {sev_color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{sev_text}</span>
                <span style="color: #f1f5f9; font-size: 16px; font-weight: bold;">Forecast Threshold Exceeded</span>
            </div>
            <div style="color: #cbd5e1; font-size: 14px;">The predicted network trajectory crosses the {threshold:.0f}% configured risk threshold at <b>{step}</b>.</div>
        </div>
        <div style="text-align: right;">
            <div style="color: #94a3b8; font-size: 12px; margin-bottom: 2px;">Predicted Stage</div>
            <div style="color: #f1f5f9; font-size: 15px; font-weight: bold;">{crossing_stage}</div>
            <div style="color: {sev_color}; font-size: 14px; font-weight: bold; margin-top: 2px;">{crossing_risk:.1f}% Risk</div>
        </div>
    </div>
</div>
"""

def timeline_html_v2(timeline_events: list, predicted_stage: str, confidence: float) -> str:
    stages = ["Reconnaissance", "Initial Access", "Lateral Movement", "Command & Control", "Exfiltration"]
    
    # Map events to stages
    observed_stages = {e["stage"]: e for e in timeline_events if e["state"] == "Observed"}
    suspected_stages = {e["stage"]: e for e in timeline_events if e["state"] == "Suspected"}
    
    cards = []
    found_predicted = False
    
    for i, stage in enumerate(stages):
        if stage in observed_stages:
            state = "OBSERVED"
            color = "#22c55e" # Green
            border = f"1px solid {color}"
            bg = f"rgba(34, 197, 94, 0.1)"
            risk_val = observed_stages[stage].get("risk", 100)
            risk_text = f"Risk: {risk_val:.0f}%"
        elif stage == predicted_stage and not found_predicted:
            state = "PREDICTED"
            color = "#f59e0b" # Orange
            border = f"1px dashed {color}"
            bg = f"rgba(245, 158, 11, 0.1)"
            risk_text = f"Confidence: {confidence:.0f}%"
            found_predicted = True
        elif stage in suspected_stages:
            state = "SUSPECTED"
            color = "#f59e0b" # Orange
            border = f"1px solid {color}55"
            bg = "transparent"
            risk_val = suspected_stages[stage].get("risk", 0)
            risk_text = f"Risk: {risk_val:.0f}%"
        else:
            state = "FUTURE"
            color = "#475569" # Slate
            border = "1px solid #1e293b"
            bg = "transparent"
            risk_text = "Not observed"
            
        arrow = ""
        if i < len(stages) - 1:
            arrow_color = "#22c55e" if state == "OBSERVED" and stages[i+1] in observed_stages else "#334155"
            arrow = f'<div style="color: {arrow_color}; font-size: 18px; margin: 0 8px; flex-shrink: 0;">→</div>'
            
        cards.append(f"""
<div style="flex: 1; min-width: 140px; background: {bg}; border: {border}; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; justify-content: space-between;">
    <div>
        <div style="color: {color}; font-size: 10px; font-weight: bold; letter-spacing: 1px; margin-bottom: 6px;">{state}</div>
        <div style="color: #f1f5f9; font-size: 13px; font-weight: bold; line-height: 1.3; margin-bottom: 8px;">{stage}</div>
    </div>
    <div style="color: #94a3b8; font-size: 11px;">{risk_text}</div>
</div>
""")
        if arrow:
            cards.append(arrow)
            
    return f"""
<div style="display: flex; align-items: center; justify-content: space-between; overflow-x: auto; padding: 10px 0; gap: 4px;">
    {''.join(cards)}
</div>
"""
