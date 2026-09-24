"""NetForeSight — AI-Based Network Attack Forecasting (offline MVP).

Runs fully offline: ``streamlit run app.py``. All data, inference
(deterministic demo engine) and visualizations execute locally.
"""
from __future__ import annotations

import time
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

import importlib
from modules import ATTACK_STAGES, SEVERITY_COLORS
from modules import visualizations as V
from modules import demo_ui
importlib.reload(V)
importlib.reload(demo_ui)
from modules.data_loader import (
    DataLoadError, describe_dataset, load_demo_dataset, load_pcap,
    load_uploaded_csv,
)
from modules.explainability import (
    feature_contributions, narrative, shap_style_values,
)
from modules.feature_extractor import (
    extract_features, normalize_features, summarize_flows,
)
from modules.forecast_engine import (
    DEFAULT_THRESHOLD, PIPELINE_STAGES, SCENARIO_PHASES, DemoWorldModel,
    TorchLSTMWorldModel, build_world_model, scenario_phase,
)
from modules.windowing import (
    NetworkWindow, generate_windows, state_matrix, windows_to_dataframe,
)

st.set_page_config(page_title="NetForeSight — Network Attack Forecasting",
                   page_icon="🛡️", layout="wide")

# --------------------------------------------------------------------------- #
# Styling                                                                      #
# --------------------------------------------------------------------------- #

CSS = """
<style>
.stApp { background: #070B16; }
section[data-testid="stSidebar"] { background: #0B1224;
  border-right: 1px solid rgba(148,163,184,0.15); }
.brand { font-size: 22px; font-weight: 800; letter-spacing: 2px; color: #f1f5f9; }
.brand span { color: #22d3ee; }
.tagline { color: #94a3b8; font-size: 13px; margin: 2px 0 12px; }
.kpi-card { background: #111A2E; border: 1px solid
  rgba(148,163,184,0.18); border-radius: 12px; padding: 14px 16px;
  backdrop-filter: blur(6px); transition: all 0.3s ease; }
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(255, 59, 77, 0.1); border-color: rgba(255, 59, 77, 0.3); }
.kpi-label { color: #94a3b8; font-size: 13px; letter-spacing: 1px;
  text-transform: uppercase; }
.kpi-value { font-size: 30px; font-weight: 800; margin: 2px 0; color: #f1f5f9; }
.kpi-sub { color: #94a3b8; font-size: 13px; }
.panel { background: #111A2E; border: 1px solid
  rgba(148,163,184,0.18); border-radius: 12px; padding: 16px 18px;
  margin-bottom: 14px; transition: all 0.3s ease; }
.panel:hover { border-color: rgba(255, 59, 77, 0.3); }
.panel h4 { margin-top: 0; color: #f1f5f9; }
.badge { display: inline-block; border: 1px solid #22d3ee; color: #22d3ee;
  border-radius: 999px; padding: 2px 10px; font-size: 12px; font-weight: 700;
  letter-spacing: 1px; margin-right: 6px; }
.badge-dim { border-color: #475569; color: #94a3b8; }
.alert-card { background: linear-gradient(135deg, rgba(255,59,77,0.15),
  #111A2E); border: 1px solid rgba(255,59,77,0.55);
  border-radius: 12px; padding: 18px 20px; margin: 6px 0 16px; }
.warn-card { background: linear-gradient(135deg, rgba(245,158,11,0.15),
  #111A2E); border: 1px solid rgba(245,158,11,0.5);
  border-radius: 12px; padding: 14px 18px; margin: 6px 0 16px; }
.tl-wrap { display: flex; align-items: stretch; flex-wrap: wrap; }
.tl-card { background: #111A2E; border-radius: 10px;
  padding: 12px 16px; min-width: 150px; flex: 1; text-align: center; }
.tl-stage { font-weight: 700; color: #f1f5f9; margin-top: 4px; }
.tl-arrow { color: #475569; font-size: 18px; text-align: center;
  padding: 2px 6px; align-self: center; }
.info-chip { background: #111A2E; border: 1px solid
  rgba(148,163,184,0.25); border-radius: 8px; padding: 8px 14px;
  color: #cbd5e1; font-size: 14px; }
.win-card { background: #111A2E; border: 1px solid
  rgba(148,163,184,0.18); border-radius: 12px; padding: 14px 16px;
  height: 100%; transition: all 0.3s ease; }
.win-card:hover { transform: translateY(-2px); border-color: rgba(34, 211, 238, 0.4); }
.win-card h5 { margin: 0 0 2px; color: #f1f5f9; }
.step-card { background: #111A2E; border: 1px solid
  rgba(34,211,238,0.35); border-radius: 10px; padding: 12px 14px;
  text-align: center; }
.check-line { color: #22c55e; font-family: monospace; font-size: 14px;
  margin: 1px 0; }
.status-dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%;
  background: #22c55e; margin-right: 6px; box-shadow: 0 0 8px #22c55e; }
.status-dot.amber { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }
.report-box { background: #0B1224; border: 1px solid rgba(148,163,184,0.25);
  border-radius: 10px; padding: 18px 22px; font-family: monospace;
  font-size: 14px; color: #f1f5f9; white-space: pre-wrap; }
div[data-testid="stMetric"] { background: #111A2E;
  border: 1px solid rgba(148,163,184,0.18); border-radius: 12px; padding: 10px; }
div[data-testid="stMetric"] label { font-size: 0.8rem !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] > div { font-size: 1.2rem !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Session state                                                                #
# --------------------------------------------------------------------------- #

def initialize_session_state():
    defaults = {
        "uploaded_file": None,
        "file_name": None,
        "file_type": None,
        "file_size": None,
        "analysis_ready": False,
        "analysis_running": False,
        "analysis_completed": False,
        "network_stats": {},
        "forecast_results": {},
        "risk_timeline": [],
        "attack_progression": [],
        "mitre_results": {},
        "explainability_results": {},
        "alerts": [],
        "analysis_results": {},
        "selected_time_window": None,
        "current_page": "Dashboard",
        "page": "Dashboard",
        "flows": None,
        "windows": [],
        "visible_ids": [],
        "forecast": None,
        "contributions": {},
        "summary": {},
        "dataset_info": {},
        "is_demo": False,
        "horizon": 5,
        "threshold": DEFAULT_THRESHOLD,
        "n_windows": 5,
        "demo_phase": 7,
        "analysis_steps": [],
        "alert_dismissed": False,
        "show_investigation": False,
        "analyst_notes": "",
        "investigations": [],
        "inv_counter": 1,
        "selected_flow": None,
        "node_selected": "10.0.2.15",
        "revealed": 0,
        "scenario_log": [],
        "explain_step": "T+2",
        "backend": "demo",
        "workflow_active": False,
        "active_upload_source": None,
        "pipeline_stats": {},
        "pipeline_logs": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

def reset_application():
    keys_to_reset = [
        "uploaded_file", "file_name", "file_type", "file_size",
        "analysis_ready", "analysis_running", "analysis_completed",
        "network_stats", "forecast_results", "risk_timeline",
        "attack_progression", "mitre_results", "explainability_results",
        "alerts", "analysis_results", "selected_time_window",
        "flows", "windows", "visible_ids", "forecast", "contributions",
        "summary", "dataset_info", "is_demo", "demo_phase", "analysis_steps",
        "alert_dismissed", "show_investigation", "analyst_notes",
        "investigations", "inv_counter", "selected_flow", "node_selected",
        "revealed", "scenario_log", "explain_step", "workflow_active",
        "active_upload_source", "pipeline_stats", "pipeline_logs"
    ]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]
    initialize_session_state()


# --------------------------------------------------------------------------- #
# Analysis pipeline                                                            #
# --------------------------------------------------------------------------- #

PIPELINE_LABELS = ["File Loaded", "Feature Extraction", "Normalization",
                   "Time Window Generation", "State Representation",
                   "Forecasting", "Explainability", "Analysis Complete"]


def run_analysis(df: pd.DataFrame, name: str, ftype: str, size: str,
                 scenario_final: float | None = None,
                 show_progress: bool = True,
                 notes: list[str] | None = None,
                 ui_placeholder=None,
                 activate_workflow: bool = True) -> None:
    """Execute the offline pipeline and store every artifact in session."""
    if activate_workflow:
        st.session_state.workflow_active = True
        
    steps: list[str] = []
    logs: list[str] = []
    stats = {}

    def _mark(step_idx: int, output_info: str, err: str = ""):
        nonlocal t_start
        dur = time.time() - t_start
        label = PIPELINE_LABELS[step_idx]
        steps.append(label)
        
        # Colorize log text based on success/fail
        if err:
            logs.append(f'<span style="color:#ef4444;">[{datetime.now().strftime("%H:%M:%S")}] ✗ {label} failed: {err}</span>')
        else:
            logs.append(f'<span style="color:#10b981;">[{datetime.now().strftime("%H:%M:%S")}] ✓ {label}</span> <span style="color:#64748b;">({output_info})</span>')
            
        stats[step_idx] = {
            "duration": f"{dur:.2f}s",
            "output": output_info,
            "error": err
        }
        
        if ui_placeholder is not None and show_progress:
            # We pass the full ds_info during the pipeline so the success box can render if it completes
            ds_info = {"records": len(df), "file_name": name, "file_size": size}
            html = V.neon_workflow_html(step_idx + 1, failed=bool(err), stats=stats, logs=logs, ds_info=ds_info)
            ui_placeholder.markdown(html, unsafe_allow_html=True)
            time.sleep(0.2)
            
        t_start = time.time()

    if ui_placeholder is not None and show_progress:
        ui_placeholder.markdown(V.neon_workflow_html(0, stats=stats, logs=logs), unsafe_allow_html=True)

    t_start = time.time()
    try:
        stats[0] = {"duration": "0.0s", "output": f"{len(df)} records"}
        _mark(0, f"Loaded {name}")
        
        feats = extract_features(df)
        _mark(1, f"Extracted {len(feats.columns)} features")
        
        feats, _ = normalize_features(feats)
        _mark(2, "Normalization complete")
        
        windows = generate_windows(feats, st.session_state.n_windows)
        _mark(3, f"Generated {len(windows)} time windows")
        
        _ = state_matrix(windows)
        _mark(4, f"State matrix shape: ({len(windows)}, {len(feats.columns)})")
        
        model = build_world_model(st.session_state.backend)
        forecast = model.predict(windows, horizon=st.session_state.horizon,
                                 threshold=st.session_state.threshold,
                                 scenario_final=scenario_final)
        _mark(5, f"Forecast complete (horizon: {st.session_state.horizon})")
        
        contribs = feature_contributions(forecast.get("signals"))
        _mark(6, "Explainability analysis completed")
        
        _mark(7, "Pipeline finished successfully")
    except Exception as e:
        stats[len(steps)] = {"duration": "0.0s", "output": "Failed", "error": str(e)}
        if ui_placeholder is not None and show_progress:
            ds_info = {"records": len(df), "file_name": name, "file_size": size}
            html = V.neon_workflow_html(len(steps), failed=True, stats=stats, logs=logs, ds_info=ds_info)
            ui_placeholder.markdown(html, unsafe_allow_html=True)
        raise e

    st.session_state.pipeline_stats = stats
    st.session_state.pipeline_logs = logs

    st.session_state.flows = feats
    st.session_state.windows = windows
    st.session_state.forecast = forecast
    st.session_state.contributions = contribs
    st.session_state.summary = summarize_flows(feats)
    st.session_state.dataset_info = describe_dataset(
        feats, name, ftype, size, notes)
    st.session_state.analysis_steps = steps
    st.session_state.alert_dismissed = False
    st.session_state.show_investigation = False
    st.session_state.revealed = 0
    # Reset per-dataset UI selections.
    crit = feats[feats["risk"].isin(["HIGH", "CRITICAL"])]
    st.session_state.selected_flow = (int(crit.index[0])
                                      if len(crit) else int(feats.index[0]))


def apply_demo_phase(phase: int) -> None:
    """Recompute the visible demo view for a scenario phase."""
    st.session_state.demo_phase = int(phase)
    st.session_state.is_demo = True
    phase_spec = scenario_phase(phase)
    windows: list[NetworkWindow] = st.session_state.windows
    if not windows:  # fresh session: load demo first
        demo_df, _ = load_demo_dataset()
        run_analysis(demo_df, "demo_network.csv", "CSV",
                     "—", show_progress=False, activate_workflow=False)
        windows = st.session_state.windows
    k = min(int(phase), 4, len(windows))
    visible = windows[:k]
    st.session_state.visible_ids = [w.id for w in visible]
    model = build_world_model(st.session_state.backend)
    forecast = model.predict(visible, horizon=st.session_state.horizon,
                             threshold=st.session_state.threshold,
                             scenario_final=phase_spec.final_risk)
    st.session_state.forecast = forecast
    st.session_state.contributions = feature_contributions(
        forecast.get("signals"))
    feats: pd.DataFrame = st.session_state.flows
    # Flow KPIs always cover the full observed session; the scenario phase
    # only moves the "current time" (visible windows) and the forecast.
    st.session_state.summary = summarize_flows(feats)
    st.session_state.alert_dismissed = False
    st.session_state.revealed = 0



# --------------------------------------------------------------------------- #
# Sidebar                                                                      #
# --------------------------------------------------------------------------- #

st.sidebar.markdown('<div class="brand">NET<span>FORESIGHT</span></div>',
                    unsafe_allow_html=True)
st.sidebar.markdown('<div class="tagline">Network Attack Forecasting · '
                    'Offline MVP</div>', unsafe_allow_html=True)

NAV = ["🏠 Dashboard", "📡 Traffic Monitor", "🔮 Attack Forecast",
       "🧠 Explainability", "🌐 Network Graph", "📊 Analytics",
       "📄 Reports", "⚙ Settings"]
choice = st.sidebar.radio("Navigate", NAV,
                          index=[n.split(" ", 1)[1] for n in NAV].index(
                              st.session_state.page)
                          if st.session_state.page in
                          [n.split(" ", 1)[1] for n in NAV] else 0,
                          label_visibility="collapsed")
st.session_state.page = choice.split(" ", 1)[1]

st.sidebar.markdown("---")
st.sidebar.markdown("**SYSTEM STATUS**")
mode_text = "DEMO MODE" if st.session_state.is_demo else "REAL DATA MODE"
dot_class = "status-dot amber" if st.session_state.is_demo else "status-dot"
st.sidebar.markdown(f'<span class="{dot_class}"></span>{mode_text} (OFFLINE)',
                    unsafe_allow_html=True)
fc = st.session_state.forecast or {}
st.sidebar.markdown(f"Model: `{(fc.get('model', '—')).split(' (')[0]}`")
st.sidebar.markdown(f"Dataset: `{st.session_state.dataset_info.get('file_name', '—')}`")
st.sidebar.markdown("---")
caption_text = "SIMULATED DATA — demo inference only." if st.session_state.is_demo else "REAL OFFLINE DATA — analyzing observed traffic."
st.sidebar.caption(caption_text)

page = st.session_state.page

# --------------------------------------------------------------------------- #
# Shared render helpers                                                        #
# --------------------------------------------------------------------------- #

def header_block() -> None:
    st.markdown("# NETFORESIGHT")
    st.markdown("### Network Attack Forecasting")
    st.markdown("**“Predict the next stage. Investigate before compromise.”**")
    st.markdown(
        '<span class="badge">● DEMO MODE</span>'
        '<span class="badge">SIMULATED / OFFLINE DATA</span>'
        '<span class="badge badge-dim">OFFLINE MVP</span>'
        '<span class="badge badge-dim">PROTOTYPE WORLD MODEL</span>',
        unsafe_allow_html=True)
    st.markdown("")


def status_strip() -> None:
    info = st.session_state.dataset_info
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-label">Data Source</div>'
                f'<div style="font-weight:700">'
                f'{"Demo Network Traffic" if st.session_state.is_demo else info.get("file_name", "—")}'
                f'</div></div>', unsafe_allow_html=True)
    c2.markdown('<div class="kpi-card"><div class="kpi-label">Analysis Status</div>'
                '<div style="font-weight:700;color:#22c55e">● Complete</div></div>',
                unsafe_allow_html=True)
    c3.markdown('<div class="kpi-card"><div class="kpi-label">Model Status</div>'
                '<div style="font-weight:700;color:#22d3ee">Forecast Engine Ready</div></div>',
                unsafe_allow_html=True)
    c4.markdown('<div class="kpi-card"><div class="kpi-label">Environment</div>'
                '<div style="font-weight:700">Offline MVP</div></div>',
                unsafe_allow_html=True)


def kpi_row() -> None:
    f = st.session_state.forecast
    s = st.session_state.summary
    r1c1, r1c2, r1c3 = st.columns(3)
    r1c1.plotly_chart(V.risk_gauge(f['current_risk']), use_container_width=True)
    r1c2.markdown(V.kpi_card("Forecast Risk", f"{f['risk']:.0f}%",
                             "Demo Forecast · primary horizon", "#f59e0b"),
                  unsafe_allow_html=True)
    r1c3.markdown(V.kpi_card("Predicted Stage", f["predicted_stage"],
                             "MITRE ATT&CK mapping", "#f59e0b"),
                  unsafe_allow_html=True)
    r2c1, r2c2, r2c3 = st.columns(3)
    r2c1.markdown(V.kpi_card("Forecast Confidence", f"{f['confidence']:.0f}%",
                             "Demo Forecast", "#22d3ee"),
                  unsafe_allow_html=True)
    r2c2.markdown(V.kpi_card("Active Flows", f"{s['active_flows']:,}",
                             "Observed in scope", "#94a3b8"),
                  unsafe_allow_html=True)
    r2c3.markdown(V.kpi_card("Suspicious Flows", f"{s['suspicious_flows']:,}",
                             f"{s['suspicious_pct']:.2f}% of scope", "#ff3b4d"),
                  unsafe_allow_html=True)


def forecast_warning_block() -> None:
    f = st.session_state.forecast
    if f.get("crosses_threshold"):
        st.markdown(
            '<div class="warn-card"><h4 style="margin:0 0 4px">⚠ Forecast Warning</h4>'
            '“The predicted network trajectory crosses the configured risk '
            'threshold within the next few time windows.”</div>',
            unsafe_allow_html=True)


def alert_card() -> None:
    f = st.session_state.forecast
    if not f.get("crosses_threshold") or st.session_state.alert_dismissed:
        return
    st.markdown(
        f"""<div class="alert-card"><h3 style="margin:0 0 6px">
        ⚠ NETWORK ATTACK FORECAST</h3>
        <div style="color:#cbd5e1">Increasing attacker progression probability
        detected.</div>
        <div style="display:flex;gap:26px;margin-top:10px;flex-wrap:wrap">
        <div>Predicted Stage:<br><b style="color:#f59e0b;font-size:18px">
        {f['predicted_stage']}</b></div>
        <div>Forecast Risk:<br><b style="color:#ff3b4d;font-size:18px">
        {f['risk']:.0f}%</b></div>
        <div>Confidence:<br><b style="color:#22d3ee;font-size:18px">
        {f['confidence']:.0f}%</b></div>
        <div>Estimated Warning Lead:<br><b>Before predicted stage transition</b></div>
        </div></div>""", unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    if b1.button("🔍 Investigate", width="stretch"):
        st.session_state.show_investigation = True
    if b2.button("🧠 View Explanation", width="stretch"):
        st.session_state.page = "Explainability"
        st.rerun()
    if b3.button("📝 Add Analyst Note", width="stretch"):
        st.session_state.show_investigation = True
    if b4.button("Dismiss", width="stretch"):
        st.session_state.alert_dismissed = True
        st.rerun()


def investigation_panel() -> None:
    if not st.session_state.show_investigation:
        return
    f = st.session_state.forecast
    feats: pd.DataFrame = st.session_state.flows
    flagged = feats[feats["risk"].isin(["HIGH", "CRITICAL"])].sort_values(
        "risk_score", ascending=False).head(5)
    top_src = (flagged["src_ip"].value_counts().index[0]
               if len(flagged) else "—")
    top_dst = flagged["dst_ip"].unique().tolist()[:4]
    top_signals = sorted(st.session_state.contributions.items(),
                         key=lambda kv: kv[1], reverse=True)[:3]
    inv_id = f"INV-20260923-{st.session_state.inv_counter:03d}"
    st.markdown(f"""<div class="panel"><h4>🔍 Analyst Investigation — {inv_id}</h4>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 22px;
    color:#cbd5e1;font-size:14px">
    <div>Forecast Time: <b>{datetime.now().strftime('%H:%M:%S')}</b></div>
    <div>Affected Source: <b style="color:#ff3b4d">{top_src}</b></div>
    <div>Affected Destinations: <b>{', '.join(top_dst)}</b></div>
    <div>Predicted Stage: <b style="color:#f59e0b">{f['predicted_stage']}</b></div>
    <div>Risk: <b>{f['risk']:.0f}%</b> · Confidence: <b>{f['confidence']:.0f}%</b></div>
    <div>Top Signals: <b>{', '.join(s for s, _ in top_signals)}</b></div>
    <div>Flagged Flows: <b>{len(flagged)} shown / """
                f"""{st.session_state.summary['suspicious_flows']:,} total</b></div>
    <div>Related Windows: <b>{', '.join(f'W{i}' for i in st.session_state.visible_ids[-2:])}</b></div>
    </div></div>""", unsafe_allow_html=True)
    st.dataframe(flagged[["timestamp", "src_ip", "dst_ip", "dst_port",
                           "protocol", "tcp_flags", "risk"]],
                 width="stretch", hide_index=True)
    st.session_state.analyst_notes = st.text_area(
        "Analyst Notes", value=st.session_state.analyst_notes, height=110,
        placeholder="Record hypothesis, next steps, escalation decision …")
    c1, c2 = st.columns([1, 4])
    if c1.button("💾 Save Investigation", type="primary"):
        st.session_state.investigations.append({
            "id": inv_id, "time": datetime.now().strftime("%H:%M:%S"),
            "stage": f["predicted_stage"], "risk": f["risk"],
            "notes": st.session_state.analyst_notes})
        st.session_state.inv_counter += 1
        st.success(f"Investigation {inv_id} saved to this session.")
    if st.session_state.investigations:
        with st.expander(f"Saved investigations "
                         f"({len(st.session_state.investigations)})"):
            for inv in st.session_state.investigations:
                st.markdown(f"**{inv['id']}** · {inv['time']} · "
                            f"{inv['stage']} · {inv['risk']:.0f}% — "
                            f"{inv['notes'] or '_no notes_'}")

# --------------------------------------------------------------------------- #
# Pages                                                                        #
# --------------------------------------------------------------------------- #

def locked_card(title: str, subtitle: str, height: int = 300) -> str:
    return f"""
    <div style="background: #0B1224; border: 1px dashed rgba(148,163,184,0.2); border-radius: 12px; height: {height}px; display: flex; flex-direction: column; align-items: center; justify-content: center; opacity: 0.5; cursor: not-allowed; margin-bottom: 20px;">
        <div style="color: #475569; margin-bottom: 12px;"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></div>
        <div style="color: #94a3b8; font-size: 16px; font-weight: 600;">{title} Locked</div>
        <div style="color: #64748b; font-size: 13px; margin-top: 4px;">{subtitle}</div>
    </div>
    """

def file_upload_section():
    st.markdown("### NETWORK TRAFFIC INPUT")
    
    up = st.file_uploader("Upload PCAP / PCAPNG / CSV", type=["pcap", "pcapng", "csv"], key="netforesight_network_file")
    
    if up is not None:
        if "file_name" not in st.session_state or st.session_state.file_name != up.name:
            st.session_state.uploaded_file = up
            st.session_state.file_name = up.name
            st.session_state.file_type = up.type
            st.session_state.file_size = up.size
            st.session_state.analysis_ready = True
            
            # Clear previous results
            st.session_state.forecast = None
            st.session_state.flows = None
            st.session_state.windows = []
            st.session_state.dataset_info = {}
            st.session_state.pipeline_stats = {}
            st.session_state.pipeline_logs = []
            st.session_state.summary = {}
            st.session_state.analysis_steps = []
            st.session_state.is_demo = False
            
    if not st.session_state.get("analysis_ready", False):
        st.markdown("""
        <div style="background: #111A2E; border: 1px solid rgba(148,163,184,0.18); border-radius: 12px; padding: 16px; margin-bottom: 20px;">
            <div style="color: #94a3b8; font-size: 13px; margin-bottom: 8px;">Status when empty:</div>
            <div style="display: flex; align-items: center; gap: 8px; color: #475569; font-weight: 600;">
                <div style="width: 8px; height: 8px; border-radius: 50%; background: #475569;"></div>
                Waiting for network traffic file
            </div>
            <div style="color: #64748b; font-size: 13px; margin-top: 4px;">Analysis locked — upload a file to continue</div>
        </div>
        """, unsafe_allow_html=True)
        return False, None
    else:
        # File is present
        ext = st.session_state.file_name.split('.')[-1].lower()
        if ext not in ["pcap", "pcapng", "csv"]:
            st.error("Unsupported file type. Please upload a .pcap, .pcapng, or .csv network traffic file.")
            st.session_state.analysis_ready = False
            return False, None
            
        size_mb = st.session_state.file_size / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{st.session_state.file_size / 1024:.1f} KB"
        records_str = f" • {len(st.session_state.flows):,} packets" if st.session_state.flows is not None else ""
        
        st.markdown(f"""
        <div style="background: #111A2E; border: 1px solid rgba(16,185,129,0.3); border-radius: 12px; padding: 16px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: #10b981; font-weight: 600; display: flex; align-items: center; gap: 8px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        {st.session_state.file_name}
                    </div>
                    <div style="color: #94a3b8; font-size: 13px; margin-top: 4px;">{ext.upper()} • {size_str}{records_str}</div>
                </div>
                <div style="background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); color: #10b981; font-size: 11px; padding: 4px 10px; border-radius: 12px; font-weight: bold;">
                    READY
                </div>
            </div>
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(148,163,184,0.1); display: flex; align-items: center; gap: 8px; color: #10b981; font-weight: 600;">
                <div style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981;"></div>
                Traffic loaded — Analysis Ready
            </div>
        </div>
        """, unsafe_allow_html=True)
        return True, st.session_state.uploaded_file


def page_dashboard() -> None:
    header_block()
    
    # NEW FILE GATING LOGIC
    is_ready, up_file = file_upload_section()
    
    if not is_ready:
        st.markdown('<div class="run-btn-col" style="opacity:0.5;">', unsafe_allow_html=True)
        st.button("🔒 Start Network Analysis", disabled=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(locked_card("Analysis", "Upload PCAP/CSV to enable analysis", 150), unsafe_allow_html=True)
        st.markdown(locked_card("Attack Progression Timeline", "Upload PCAP/CSV to enable analysis", 150), unsafe_allow_html=True)
        st.markdown(locked_card("Demo Scenario", "Upload PCAP/CSV to enable demo mode", 150), unsafe_allow_html=True)
        return
        
    # Process file button
    st.markdown('<div class="run-btn-col">', unsafe_allow_html=True)
    if st.button("▶ Start Network Analysis", type="primary", use_container_width=True):
        ext = up_file.name.split('.')[-1].lower()
        ph = st.empty()
        try:
            if ext in ["pcap", "pcapng"]:
                df, notes = load_pcap(up_file)
                typ = "PCAP"
            else:
                df, notes = load_uploaded_csv(up_file)
                typ = "CSV"
            size_mb = len(up_file.getvalue()) / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{len(up_file.getvalue()) / 1024:.1f} KB"
            run_analysis(df, up_file.name, typ, size_str, notes=notes, ui_placeholder=ph)
            st.session_state.is_demo = False
            st.session_state.visible_ids = [w.id for w in st.session_state.windows]
            st.success(f"Processed {len(df):,} records.")
            st.rerun()
        except DataLoadError as exc:
            st.warning(f"⚠ Unable to process file. {exc}")
    st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.forecast:
        st.markdown(locked_card("Analysis Pending", "Click Start Network Analysis to process traffic", 200), unsafe_allow_html=True)
        return

    status_strip()
    st.markdown("")
    kpi_row()
    st.markdown("")

    f = st.session_state.forecast
    if f.get("error"):
        st.error(f"⚠ {f['error']}")
    else:
        st.plotly_chart(V.risk_forecast_chart(f), width="stretch")
        st.caption("Forecast trajectory. Observed (solid) vs forecast (dashed) with ±6% confidence band.")
        forecast_warning_block()
        alert_card()
        investigation_panel()

        st.markdown("### Attack Progression Timeline")
        st.markdown(V.timeline_html(f["timeline"], f["predicted_stage"],
                                    f["confidence"]), unsafe_allow_html=True)
        st.caption("Observed = confirmed from current data · Suspected = possible "
                   "stage · Predicted = world-model forecast · Future = not observed.")
    st.markdown("")

    if "pipeline_stats" in st.session_state and st.session_state.analysis_steps:
        st.markdown(V.neon_workflow_html(
            len(st.session_state.analysis_steps), 
            stats=st.session_state.pipeline_stats, 
            logs=st.session_state.pipeline_logs,
            ds_info=st.session_state.dataset_info,
            disabled=not st.session_state.workflow_active,
            is_demo=st.session_state.is_demo
        ), unsafe_allow_html=True)

    st.markdown("")

    st.markdown("## Network State Windows")
    wins = [w for w in st.session_state.windows if w.id in st.session_state.visible_ids]
    if st.session_state.is_demo:
        wins = [w for w in wins if w.id <= 4]
    cols = st.columns(5 if len(wins) >= 4 else max(len(wins), 1))
    for col, w in zip(cols, wins):
        col.markdown(
            f"""<div class="win-card"><h5>Window {w.id:02d}</h5>
            <div style="color:#22d3ee;font-size:13px;margin-bottom:8px">{w.label}</div>
            <div style="font-size:13px;color:#cbd5e1">
            Flows: <b>{w.flows:,}</b><br>Unique Sources: <b>{w.unique_src}</b>
            <br>Unique Destinations: <b>{w.unique_dst}</b><br>
            SYN Count: <b>{w.syn_count:,}</b><br>Average IAT: <b>{w.avg_iat}s</b>
            <br>Risk: <b>{w.risk:.0f}%</b></div></div>""",
            unsafe_allow_html=True)

    chart_wins = [w for w in st.session_state.windows if w.id in st.session_state.visible_ids]
    if st.session_state.is_demo:
        chart_wins = [w for w in chart_wins if w.id <= 4]
    if chart_wins:
        last = chart_wins[-1]
        chart_wins = chart_wins + [NetworkWindow(
            id=last.id + 1, label="Predicted High-Risk State",
            start=last.end, end=last.end, flows=0, unique_src=0,
            unique_dst=0, syn_count=0, avg_iat=0.0, retrans=0,
            risk=float(f["forecast_risk"][0]), predicted=True)]
        st.plotly_chart(V.window_risk_chart(chart_wins), width="stretch")
    st.markdown("")

    # ---- Demo scenario ---- #
    st.markdown(demo_ui.demo_scenario_header_html(), unsafe_allow_html=True)

    st.markdown("""<style>
    .run-btn-col button {
        width: 100%;
        height: 60px;
        font-size: 20px !important;
        background: linear-gradient(90deg, #0ea5e9, #8b5cf6) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }
    .run-btn-col button:disabled {
        background: #1e293b !important;
        color: #475569 !important;
    }
    .run-btn-col button:hover:not(:disabled) {
        opacity: 0.9;
        transform: translateY(-1px);
    }
    </style>""", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("▶ Run Demo Scenario", use_container_width=True, disabled=not st.session_state.analysis_ready):
            st.session_state.demo_phase = 1
            st.rerun()

    with c2:
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.markdown(demo_ui.demo_metric_html("Estimated Time", "~ 30 seconds", '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'), unsafe_allow_html=True)
        mc2.markdown(demo_ui.demo_metric_html("Phases", "7 steps", '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>'), unsafe_allow_html=True)
        mc3.markdown(demo_ui.demo_metric_html("Forecast Horizon", "Next 3 windows", '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>'), unsafe_allow_html=True)
        mc4.markdown(demo_ui.demo_scenario_type_html(), unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.get("demo_phase", 7) < 7:
        placeholder = st.empty()
        for phase in range(1, 8):
            apply_demo_phase(phase)
            with placeholder.container():
                pc1, pc2 = st.columns([1.2, 1])
                with pc1:
                    st.markdown(demo_ui.demo_run_log_html(phase), unsafe_allow_html=True)
                with pc2:
                    st.markdown(demo_ui.risk_trend_demo_html(phase), unsafe_allow_html=True)
                    st.markdown(demo_ui.demo_network_progression_html(phase), unsafe_allow_html=True)
            import time
            time.sleep(1)
        st.session_state.demo_phase_complete = True
        st.session_state.scenario_log = ["Complete"]
    else:
        phase = st.session_state.demo_phase if hasattr(st.session_state, 'demo_phase') else 7
        pc1, pc2 = st.columns([1.2, 1])
        with pc1:
            st.markdown(demo_ui.demo_run_log_html(phase), unsafe_allow_html=True)
        with pc2:
            st.markdown(demo_ui.risk_trend_demo_html(phase), unsafe_allow_html=True)
            st.markdown(demo_ui.demo_network_progression_html(phase), unsafe_allow_html=True)
        
    st.markdown('<div style="margin-top:20px; font-size: 12px; color: #64748b; display: flex; align-items: center; justify-content: space-between;"><div><span style="color: #eab308; font-weight: bold;">💡 Prototype limits:</span> Simulated inference, no live monitoring, forecasts are not validated detections.</div><div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); color: #c4b5fd; padding: 2px 10px; border-radius: 12px; font-weight: bold;">DEMO MODE</div></div>', unsafe_allow_html=True)



def _filtered_flows() -> pd.DataFrame:
    df: pd.DataFrame = st.session_state.flows
    with st.expander("Advanced Traffic Filters", expanded=True):
        f1, f2, f3, f4 = st.columns(4)
        risks = f1.multiselect("Risk", ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                               default=["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        protos = f2.multiselect("Protocol", sorted(df["protocol"].unique()),
                                default=sorted(df["protocol"].unique()))
        
        # Determine valid ports for default list, convert to strings
        all_ports = sorted(df["dst_port"].unique())
        
        dst_p = f3.text_input("Destination Port", "")
        
        sort_col = f4.selectbox("Sort by",
                                ["timestamp", "risk_score", "bytes", "packets",
                                 "duration", "dst_port"])
        f5, f6, f7 = st.columns([1.5, 1.5, 1])
        src_q = f5.text_input("Source IP contains", "")
        dst_q = f6.text_input("Destination IP contains", "")
        asc = f7.checkbox("Ascending order", value=False)
        span_min = int((df["timestamp"].max() - df["timestamp"].min()).total_seconds() // 60)
        t0, t1 = st.slider("Time range (minutes from start)", 0, max(span_min, 1),
                           (0, max(span_min, 1)))
                           
    base = df["timestamp"].min()
    out = df[df["risk"].isin(risks) & df["protocol"].isin(protos)]
    if src_q:
        out = out[out["src_ip"].str.contains(src_q)]
    if dst_q:
        out = out[out["dst_ip"].str.contains(dst_q)]
    if dst_p:
        try:
            port_val = int(dst_p)
            out = out[out["dst_port"] == port_val]
        except ValueError:
            pass # ignore invalid port inputs
            
    out = out[(out["timestamp"] >= base + pd.Timedelta(minutes=t0)) &
              (out["timestamp"] <= base + pd.Timedelta(minutes=t1))]
    out = out.sort_values(sort_col, ascending=asc)
    return out


def page_traffic() -> None:
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <div>
            <h1 style="margin:0; padding:0; font-size: 32px;">Traffic Monitor</h1>
            <p style="margin:0; color:#94a3b8; font-size: 16px;">Monitor, filter, and investigate network traffic.</p>
        </div>
        <div style="display:flex; gap:8px;">
            <span class="badge" style="background:#f59e0b22; color:#f59e0b; border:1px solid #f59e0b55;">{}</span>
            <span class="badge badge-dim" style="border:1px solid #94a3b855;">{}</span>
            <span class="badge" style="background:#22c55e22; color:#22c55e; border:1px solid #22c55e55;">Analysis Complete</span>
        </div>
    </div>
    <hr style="margin-top:5px; margin-bottom:20px; border-color:#26364F;">
    """.format("DEMO MODE" if st.session_state.is_demo else "REAL DATA MODE", "SIMULATED / OFFLINE DATA" if st.session_state.is_demo else "OBSERVED / OFFLINE DATA"), unsafe_allow_html=True)

    if st.session_state.flows is None or st.session_state.flows.empty:
        st.info("Upload a CSV or supported PCAP file to view network traffic.")
        return

    out = _filtered_flows()
    st.markdown(V.kpi_row_traffic(out), unsafe_allow_html=True)

    # Convert risk to emojis for the dataframe
    if "risk" in out.columns:
        emojis = {"LOW": "🟢 LOW", "MEDIUM": "🟡 MEDIUM", "HIGH": "🟠 HIGH", "CRITICAL": "🔴 CRITICAL"}
        display_out = out.copy()
        display_out["Risk Badge"] = display_out["risk"].map(lambda x: emojis.get(x, x))
    else:
        display_out = out.copy()
        display_out["Risk Badge"] = "Not available"

    st.markdown(f"### Flow Records <span style='font-size:14px; color:#94a3b8; font-weight:normal;'>({len(out):,} flows match current filters)</span>", unsafe_allow_html=True)
    
    table = pd.DataFrame({
        "Timestamp": display_out["timestamp"].dt.strftime("%H:%M:%S"),
        "Source IP": display_out["src_ip"], "Destination IP": display_out["dst_ip"],
        "Source Port": display_out["src_port"], "Destination Port": display_out["dst_port"],
        "Protocol": display_out["protocol"], "TCP Flags": display_out["tcp_flags"],
        "Packets": display_out["packets"], "Bytes": display_out["bytes_str"],
        "Flow Duration": display_out["duration_str"], "Risk Level": display_out["Risk Badge"],
        "_OriginalIndex": display_out.index # Store original index to link selections back
    })

    # Use Streamlit interactive dataframe
    event = st.dataframe(
        table.drop(columns=["_OriginalIndex"]), 
        width=None, 
        use_container_width=True, 
        hide_index=True, 
        height=300,
        selection_mode="single-row",
        on_select="rerun"
    )

    selected_rows = event.selection.rows if hasattr(event, "selection") else []
    
    st.markdown("### Suspicious Flow Investigation")
    if selected_rows:
        sel_idx = selected_rows[0]
        actual_index = table.iloc[sel_idx]["_OriginalIndex"]
        r = st.session_state.flows.loc[actual_index]
        st.session_state.selected_flow = actual_index
        risk_val = r.get("risk", "N/A")
        
        st.markdown(f"""
<div class="panel" style="border: 1px solid #22d3ee55; box-shadow: 0 4px 20px rgba(34, 211, 238, 0.05);">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #26364F; padding-bottom:12px; margin-bottom:16px;">
        <h4 style="margin:0;">Flow Details</h4>
        {V.severity_badge(risk_val)}
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px 22px;color:#cbd5e1;font-size:14px;">
        <div><span style="color:#94a3b8;">Source:</span> <b>{r.get('src_ip', '—')}:{r.get('src_port', '—')}</b></div>
        <div><span style="color:#94a3b8;">Destination:</span> <b>{r.get('dst_ip', '—')}:{r.get('dst_port', '—')}</b></div>
        <div><span style="color:#94a3b8;">Protocol / Flags:</span> <b>{r.get('protocol', '—')} / {r.get('tcp_flags', '—')}</b></div>
        <div><span style="color:#94a3b8;">Packets:</span> <b>{r.get('packets', 0):,}</b></div>
        <div><span style="color:#94a3b8;">Bytes:</span> <b>{r.get('bytes', 0):,} ({r.get('bytes_str', '—')})</b></div>
        <div><span style="color:#94a3b8;">Flow Duration:</span> <b>{r.get('duration_str', '—')}</b></div>
        <div><span style="color:#94a3b8;">Mean IAT:</span> <b>{r.get('iat_mean', '—')}s</b></div>
        <div><span style="color:#94a3b8;">TTL:</span> <b>{r.get('ttl', '—')}</b></div>
        <div><span style="color:#94a3b8;">Retransmissions:</span> <b>{r.get('retransmissions', '—')}</b></div>
    </div>
""" + (f"""<div style="margin-top:20px; padding-top:16px; border-top: 1px dashed #26364F;">
<div style="color:#cbd5e1;font-size:14px; margin-bottom:8px;">
Risk contribution: <b style="color:#fb923c">{r.get('risk_contrib', 0):.1f}/100</b></div>
<div style="background:#0d1528;border-radius:6px;height:10px;">
<div style="width:{r.get('risk_contrib', 0):.0f}%;height:10px;border-radius:6px; background:linear-gradient(90deg,#22d3ee,#fb923c,#ef4444)"></div>
</div>
</div>""" if "risk_contrib" in r else "") + """
</div>
""", unsafe_allow_html=True)
    else:
        st.info("Select a flow from the table above to view investigation details.")

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(V.risk_distribution_chart(out), use_container_width=True, key="risk_dist_chart")
    with c2:
        st.plotly_chart(V.protocol_distribution_chart(out), use_container_width=True, key="proto_dist_chart")
    with c3:
        st.plotly_chart(V.activity_timeline_chart(out), use_container_width=True, key="activity_chart")

def page_forecast() -> None:
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <div>
            <h1 style="margin:0; padding:0; font-size: 32px;">Attack Forecast</h1>
            <p style="margin:0; color:#94a3b8; font-size: 16px;">Forecast potential network attack progression and investigate emerging risks.</p>
        </div>
        <div style="display:flex; gap:8px;">
            <span class="badge" style="background:#f59e0b22; color:#f59e0b; border:1px solid #f59e0b55;">{}</span>
            <span class="badge badge-dim" style="border:1px solid #94a3b855;">{}</span>
            <span class="badge" style="background:#22c55e22; color:#22c55e; border:1px solid #22c55e55;">Model Ready</span>
        </div>
    </div>
    <hr style="margin-top:5px; margin-bottom:20px; border-color:#26364F;">
    """.format("DEMO FORECAST" if st.session_state.is_demo else "REAL MODEL", "OFFLINE MODE"), unsafe_allow_html=True)

    if st.session_state.flows is None or st.session_state.flows.empty:
        st.info("Upload a CSV or supported PCAP file to generate attack forecasts.")
        return

    f = st.session_state.forecast
    if not f or f.get("error"):
        st.error(f"⚠ {f.get('error', 'Forecast model unavailable.')}")
        return

    st.markdown("### Current Network State")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.plotly_chart(V.risk_gauge(f['current_risk']), use_container_width=True)
    with c2:
        model_name = f.get("model", "Unknown Model").split(" (")[0]
        st.markdown(V.model_status_card(model_name, st.session_state.is_demo), unsafe_allow_html=True)

    st.markdown("### Forecast Horizon")
    # Instead of segmented_control updating immediately, we use columns
    col_hz, col_btn = st.columns([3, 1])
    with col_hz:
        horizon = st.segmented_control("Steps", [1, 2, 3, 4, 5], default=st.session_state.horizon, key="horizon_ctrl")
    with col_btn:
        st.write("") # spacer
        st.write("") # spacer
        if st.button("Generate Forecast", type="primary", use_container_width=True):
            if horizon != st.session_state.horizon:
                st.session_state.horizon = horizon
                phase_final = (scenario_phase(st.session_state.demo_phase).final_risk if st.session_state.is_demo else None)
                vis = [w for w in st.session_state.windows if w.id in st.session_state.visible_ids] or st.session_state.windows
                model = build_world_model(st.session_state.backend)
                with st.spinner("Generating forecast..."):
                    st.session_state.forecast = model.predict(vis, horizon=horizon, threshold=st.session_state.threshold, scenario_final=phase_final)
                st.session_state.selected_forecast_step = "T+1"
                st.rerun()

    f = st.session_state.forecast
    steps = f.get("future_stages", [])
    if not steps:
        return
        
    st.markdown("### Forecast Results")
    cols = st.columns(len(steps))
    
    if "selected_forecast_step" not in st.session_state:
        st.session_state.selected_forecast_step = "T+1"

    for col, s in zip(cols, steps):
        step_id = s['step']
        is_selected = (st.session_state.selected_forecast_step == step_id)
        border_color = "#22d3ee" if is_selected else "#26364F"
        bg_color = "rgba(34, 211, 238, 0.05)" if is_selected else "#111A2E"
        
        with col:
            st.markdown(f"""
<div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 8px; padding: 12px; text-align: center; margin-bottom: 8px; transition: all 0.2s;">
    <div style="color:#94a3b8; font-size:12px; font-weight:bold;">{step_id}</div>
    <div style="font-size:24px; font-weight:800; color:#f59e0b; margin: 4px 0;">{s.get('risk', 0):.0f}%</div>
    <div style="font-weight:700; font-size:13px; color:#f1f5f9;">{s.get('stage', 'Unknown')}</div>
    <div style="color:#94a3b8; font-size:11px; margin-top: 4px;">Conf: {s.get('confidence', 0):.0f}%</div>
</div>
""", unsafe_allow_html=True)
            if st.button(f"Inspect {step_id}", key=f"btn_{step_id}", use_container_width=True):
                st.session_state.selected_forecast_step = step_id
                st.rerun()

    st.markdown("---")
    
    st.plotly_chart(V.kstep_forecast_chart(steps, f["current_risk"], f.get("threshold", 0.7)*100), use_container_width=True)
    
    crossing_stage = f.get("predicted_stage", "Unknown")
    crossing_risk = f.get("risk", 0)
    crossing_step = next((s["step"] for s in steps if s["risk"] > f.get("threshold", 0.7)*100), "Unknown")
    st.markdown(V.forecast_warning_block_v2(
        f.get("crosses_threshold", False), 
        f.get("threshold", 0.7)*100, 
        crossing_stage, 
        crossing_risk, 
        crossing_step
    ), unsafe_allow_html=True)

    sel_s = next((s for s in steps if s["step"] == st.session_state.selected_forecast_step), steps[0])
    st.markdown("### Network Attack Forecast Summary")
    
    s_col1, s_col2 = st.columns([2, 1])
    with s_col1:
        st.markdown(f"""
<div style="background: #111A2E; border: 1px solid #26364F; border-radius: 8px; padding: 20px;">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <div>
            <div style="color: #94a3b8; font-size: 12px; margin-bottom: 4px;">Predicted Attack Stage ({sel_s['step']})</div>
            <div style="color: #f59e0b; font-size: 18px; font-weight: bold;">{sel_s['stage']}</div>
        </div>
        <div>
            <div style="color: #94a3b8; font-size: 12px; margin-bottom: 4px;">Forecast Risk</div>
            <div style="color: #ff3b4d; font-size: 18px; font-weight: bold;">{sel_s['risk']:.1f}%</div>
        </div>
        <div>
            <div style="color: #94a3b8; font-size: 12px; margin-bottom: 4px;">Model Confidence</div>
            <div style="color: #22d3ee; font-size: 18px; font-weight: bold;">{sel_s['confidence']:.1f}%</div>
        </div>
        <div>
            <div style="color: #94a3b8; font-size: 12px; margin-bottom: 4px;">Warning Lead Time</div>
            <div style="color: #f1f5f9; font-size: 18px; font-weight: bold;">{"< 1 Window" if sel_s['step']=="T+1" else "Multiple Windows"}</div>
        </div>
    </div>
    <div style="margin-top: 16px; padding-top: 16px; border-top: 1px dashed #26364F; color: #cbd5e1; font-size: 14px;">
        Based on the current observed traffic, the model predicts the attack will progress to <b>{sel_s['stage']}</b> in the <b>{sel_s['step']}</b> horizon.
    </div>
</div>
""", unsafe_allow_html=True)
        
    with s_col2:
        st.markdown("**Interactive Actions**")
        if st.button("🔍 Investigate Flows", use_container_width=True):
            st.session_state.page = "Traffic Monitor"
            st.rerun()
        if st.button("🧠 View Explanation", use_container_width=True):
            st.session_state.page = "Explainability"
            st.rerun()
        if st.button("📝 Add Analyst Note", use_container_width=True):
            st.session_state.show_investigation = True
            st.session_state.page = "Traffic Monitor"
            st.rerun()
        if st.button("Dismiss Warning", use_container_width=True):
            st.session_state.alert_dismissed = True
            st.rerun()
            
    st.markdown("### Attack Progression Timeline")
    st.markdown(V.timeline_html_v2(f.get("timeline", []), sel_s["stage"], sel_s["confidence"]), unsafe_allow_html=True)
    
    with st.expander("Forecast Details (Raw Data)"):
        st.json(f)


def page_explain() -> None:
    st.markdown("# Why is NetForeSight Forecasting an Attack?")
    st.markdown('<span class="badge">DEMO EXPLANATION</span> '
                '<span class="badge badge-dim">SIMULATED ATTRIBUTION</span>',
                unsafe_allow_html=True)
    f = st.session_state.forecast
    if f.get("error"):
        st.error(f"⚠ {f['error']}")
        return
    step = st.selectbox("Forecast window",
                        ["T+1", "T+2", "T+3", "T+4", "T+5"][:f["horizon"]],
                        index=min(1, f["horizon"] - 1))
    st.session_state.explain_step = step
    s = next(x for x in f["future_stages"] if x["step"] == step)
    base_signals = dict(f.get("signals") or {})
    scale = 0.85 + 0.15 * (s["risk"] / max(f["current_risk"], 1))
    adj = {k: (v * scale if k in ("syn_rate", "dst_spread", "retrans") else v)
           for k, v in base_signals.items()}
    contribs = feature_contributions(adj if base_signals else None)
    st.plotly_chart(V.contribution_bar_chart(contribs),
                    width="stretch")
    st.markdown(f"> {narrative(contribs, 'current window', s['stage'])}")
    st.markdown("### SHAP-style feature contributions "
                f"({step} → {s['stage']})")
    rows = shap_style_values(contribs)
    html = ['<div class="panel">'
            '<div style="display:grid;grid-template-columns:1fr 120px 1fr;'
            'gap:4px 12px;font-size:14px">'
            '<div style="color:#94a3b8"><b>Feature</b></div>'
            '<div style="color:#94a3b8"><b>Contribution</b></div>'
            '<div style="color:#94a3b8"><b>Effect</b></div>']
    for row in rows:
        color = "#f87171" if row["value"] >= 0 else "#22c55e"
        bar = "█" * max(int(abs(row["value"]) * 30), 1)
        html.append(
            f"<div>{row['feature']}</div>"
            f"<div style='color:{color};font-family:monospace'>"
            f"{row['value']:+.2f}</div>"
            f"<div style='color:{color};font-family:monospace'>{bar}</div>")
    html.append("</div><div style='margin-top:8px'>"
                '<span class="badge">DEMO EXPLANATION</span></div></div>')
    st.markdown("".join(html), unsafe_allow_html=True)
    st.caption("Positive values push the forecast toward attack progression; "
               "negative values would push toward benign. Values are "
               "simulated attention-style attribution, not fitted SHAP values.")


def _node_stats(ip: str) -> dict:
    df: pd.DataFrame = st.session_state.flows
    if "/" in ip:  # aggregate node
        prefix = ip.split("/")[0].rsplit(".", 1)[0] + "."
        sub = df[df["src_ip"].str.startswith(prefix) |
                 df["dst_ip"].str.startswith(prefix)]
    else:
        sub = df[(df["src_ip"] == ip) | (df["dst_ip"] == ip)]
    susp = sub[sub["risk"].isin(["HIGH", "CRITICAL"])]
    return {
        "connections": len(sub),
        "suspicious": len(susp),
        "ports": sub["dst_port"].value_counts().head(4).index.tolist(),
        "risk": round(float(sub["risk_score"].max() * 100), 1) if len(sub) else 0.0,
    }


def page_graph() -> None:
    st.markdown("# Network Graph")
    st.markdown('<span class="badge">● DEMO MODE</span> '
                '<span class="badge badge-dim">SIMULATED TOPOLOGY</span>',
                unsafe_allow_html=True)
    f = st.session_state.forecast
    st.plotly_chart(V.network_graph_figure(st.session_state.node_selected),
                    width="stretch")
    st.caption("Suspicious communication paths are highlighted in red.")
    node = st.selectbox("Select a node to inspect",
                        [n["ip"] for n in V.GRAPH_NODES],
                        index=[n["ip"] for n in V.GRAPH_NODES].index(
                            st.session_state.node_selected),
                        format_func=lambda ip: next(
                            f"{n['ip']} — {n['role']}" for n in V.GRAPH_NODES
                            if n["ip"] == ip))
    st.session_state.node_selected = node
    meta = next(n for n in V.GRAPH_NODES if n["ip"] == node)
    stats = _node_stats(node)
    behav = ("Expected to participate in forecasted "
             f"{f['predicted_stage'].lower()}" if node in
             ("10.0.2.15", "10.0.4.21", "10.0.4.22", "10.0.4.27")
             else "No malicious behaviour forecast")
    st.markdown(f"""<div class="panel"><h4>Node — {node}</h4>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 22px;
    color:#cbd5e1;font-size:14px">
    <div>IP: <b>{node}</b></div><div>Role: <b>{meta['role']}</b></div>
    <div>Connections: <b>{stats['connections']:,}</b></div>
    <div>Suspicious Connections: <b style="color:#ef4444">
    {stats['suspicious']:,}</b></div>
    <div>Targeted Ports: <b>{', '.join(map(str, stats['ports'])) or '—'}</b></div>
    <div>Current Risk: <b>{stats['risk']:.0f}%</b></div>
    </div><div style="margin-top:8px;color:#cbd5e1;font-size:14px">
    Predicted Behavior: <b style="color:#fb923c">{behav}</b></div></div>""",
                unsafe_allow_html=True)


def page_analytics() -> None:
    st.markdown("# Analytics")
    st.markdown('<span class="badge">● DEMO MODE</span> '
                '<span class="badge badge-dim">SIMULATED / OFFLINE DATA</span>',
                unsafe_allow_html=True)
    df: pd.DataFrame = st.session_state.flows
    r1c1, r1c2 = st.columns(2)
    r1c1.plotly_chart(V.stage_distribution_chart(df), width="stretch")
    r1c2.plotly_chart(V.risk_histogram(df), width="stretch")
    r2c1, r2c2 = st.columns(2)
    r2c1.plotly_chart(V.suspicious_timeseries(df), width="stretch")
    r2c2.plotly_chart(V.protocol_donut(df), width="stretch")
    r3c1, r3c2 = st.columns(2)
    r3c1.plotly_chart(V.top_ports_chart(df), width="stretch")
    r3c2.plotly_chart(V.flow_volume_chart(df), width="stretch")


def _report_text() -> str:
    f = st.session_state.forecast
    if f.get("error"):
        return f"NETFORESIGHT\nError: {f['error']}"
    info = st.session_state.dataset_info
    contribs = st.session_state.contributions
    feats: pd.DataFrame = st.session_state.flows
    flagged = feats[feats["risk"].isin(["HIGH", "CRITICAL"])].sort_values(
        "risk_score", ascending=False).head(10)
    lines = [
        "NETFORESIGHT", "Network Attack Forecast Report",
        "─" * 40, "",
        f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Dataset: {info.get('file_name', '—')}",
        "Environment: Offline MVP (Demo Forecast)",
        f"Model Status: {f.get('model', '—')}", "",
        f"Current Risk: {f['current_risk']:.0f}%",
        f"Forecast Risk: {f['risk']:.0f}%",
        f"Predicted Stage: {f['predicted_stage']}",
        f"Confidence: {f['confidence']:.0f}%", "",
        "Top Contributing Signals:"]
    for i, (k, v) in enumerate(sorted(contribs.items(),
                                      key=lambda kv: kv[1], reverse=True), 1):
        lines.append(f"{i}. {k} — {v:.1f}%")
    lines += ["", "Flagged Flows (top 10):"]
    for _, r in flagged.iterrows():
        lines.append(f"- {r['timestamp']} {r['src_ip']} → {r['dst_ip']}:"
                     f"{r['dst_port']} {r['protocol']}/{r['tcp_flags']} "
                     f"[{r['risk']}]")
    lines += ["", "Attack Progression:"]
    for t in f["timeline"]:
        mark = {"Observed": "✓", "Suspected": "◐",
                "Predicted": "⚠", "Future": "○"}[t["state"]]
        lines.append(f"{mark} {t['stage']} — {t['state']}")
    lines += ["", f"Analyst Notes: {st.session_state.analyst_notes or '—'}",
              "", "Note: simulated demo inference — not a validated detection."]
    return "\n".join(lines)


def page_reports() -> None:
    st.markdown("# Security Forecast Report")
    st.markdown('<span class="badge">DEMO FORECAST</span> '
                '<span class="badge badge-dim">OFFLINE MVP</span>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="report-box">{_report_text()}</div>',
                unsafe_allow_html=True)
    st.markdown("")
    c1, c2 = st.columns(2)
    c1.download_button("📄 Export Report", _report_text(),
                       file_name="netforesight_report.txt", mime="text/plain",
                       width="stretch")
    csv = st.session_state.flows[[
        "timestamp", "src_ip", "dst_ip", "src_port", "dst_port", "protocol",
        "tcp_flags", "packets", "bytes", "duration", "iat_mean", "ttl",
        "retransmissions", "risk_score", "risk"]].to_csv(index=False)
    c2.download_button("⬇ Download CSV", csv,
                       file_name="netforesight_flows.csv", mime="text/csv",
                       width="stretch")


def page_settings() -> None:
    st.markdown("# Settings")
    st.markdown("### Forecast configuration")
    thr = st.slider("Alert Threshold (%)", 50, 90,
                    int(st.session_state.threshold * 100))
    if thr != int(st.session_state.threshold * 100):
        st.session_state.threshold = thr / 100.0
        vis = [w for w in st.session_state.windows
               if w.id in st.session_state.visible_ids] or st.session_state.windows
        phase_final = (scenario_phase(st.session_state.demo_phase).final_risk
                       if st.session_state.is_demo else None)
        model = build_world_model(st.session_state.backend)
        st.session_state.forecast = model.predict(
            vis, horizon=st.session_state.horizon,
            threshold=st.session_state.threshold, scenario_final=phase_final)
        st.rerun()
    n_win = st.selectbox("Time windows", [3, 4, 5, 6],
                         index=[3, 4, 5, 6].index(st.session_state.n_windows))
    if n_win != st.session_state.n_windows:
        st.session_state.n_windows = n_win
        info = st.session_state.dataset_info
        run_analysis(st.session_state.flows, info.get("file_name", "data"),
                     info.get("file_type", "CSV"), info.get("file_size", "—"),
                     scenario_final=(scenario_phase(
                         st.session_state.demo_phase).final_risk
                         if st.session_state.is_demo else None),
                     show_progress=False)
        if st.session_state.is_demo:
            apply_demo_phase(st.session_state.demo_phase)
        else:
            st.session_state.visible_ids = [w.id for w in
                                            st.session_state.windows]
        st.rerun()
    backend = st.radio("Forecast backend", ["demo", "torch"],
                       index=["demo", "torch"].index(st.session_state.backend),
                       format_func=lambda b: "DemoWorldModel (Prototype)"
                       if b == "demo" else
                       "TorchLSTMWorldModel (Untrained Placeholder)")
    if backend != st.session_state.backend:
        st.session_state.backend = backend
        st.rerun()
    tw = TorchLSTMWorldModel()
    st.info(f"**DemoWorldModel** — deterministic demo inference (active "
            f"backend: `{st.session_state.backend}`).\n\n"
            f"**TorchLSTMWorldModel** — reference LSTM→K-states→stage-logits "
            f"architecture; weights: `untrained-placeholder`; "
            f"torch installed: `{tw.torch_available}`. Swap the trained "
            f"module in later without UI changes.")
    st.markdown("### Session")
    st.write(f"Saved investigations: {len(st.session_state.investigations)}")
    st.markdown("────────────────────────────────────")
    st.markdown("### ⚠️ Danger Zone")
    st.markdown("**Reset NetForeSight Application**")
    st.markdown("""
This will remove:
• Uploaded traffic file
• Analysis results
• Forecasts
• Risk history
• Attack progression
• MITRE analysis
• Explainability results
    """)
    if "confirm_reset" not in st.session_state:
        st.session_state.confirm_reset = False

    if not st.session_state.confirm_reset:
        if st.button("🔄 RESET APPLICATION"):
            st.session_state.confirm_reset = True
            st.rerun()
    else:
        st.warning("Are you sure you want to reset NetForeSight?")
        c1, c2 = st.columns(2)
        if c1.button("Cancel"):
            st.session_state.confirm_reset = False
            st.rerun()
        if c2.button("Reset Application", type="primary"):
            st.session_state.confirm_reset = False
            reset_application()
            st.session_state.page = "Dashboard"
            st.rerun()
    st.markdown("────────────────────────────────────")
    st.markdown("### Environment")
    st.code("Data Source: local files only\nInference: local (no cloud APIs)\n"
            "Connectivity required: none at runtime", language="text")


PAGES = {"Dashboard": page_dashboard, "Traffic Monitor": page_traffic,
         "Attack Forecast": page_forecast, "Explainability": page_explain,
         "Network Graph": page_graph, "Analytics": page_analytics,
         "Reports": page_reports, "Settings": page_settings}

if not st.session_state.analysis_ready and page != "Dashboard":
    header_block()
    st.markdown(locked_card(page, "Upload a valid PCAP/CSV on the Dashboard to enable this feature.", 300), unsafe_allow_html=True)
else:
    PAGES[page]()

st.markdown("---")
st.caption("NetForeSight · Offline MVP · Simulated demo inference — "
           "forecasts are illustrative, not validated detections. "
           "The analyst remains in control: no automated blocking.")
