def strip_indentation(html_str: str) -> str:
    return "".join(line.strip() for line in html_str.split('\n'))

def demo_scenario_header_html() -> str:
    return strip_indentation("""
    <div style="background: #071426; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px;">
            <div style="display: flex; gap: 16px; align-items: center;">
                <div style="width: 50px; height: 50px; border-radius: 12px; background: linear-gradient(135deg, rgba(255,59,77,0.2), rgba(255,59,77,0.05)); border: 1px solid rgba(255,59,77,0.4); display: flex; justify-content: center; align-items: center; color: #ff3b4d;">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><circle cx="12" cy="11" r="3"></circle><line x1="12" y1="14" x2="12" y2="17"></line></svg>
                </div>
                <div>
                    <h2 style="margin: 0; font-size: 26px; color: #f1f5f9; font-weight: 800;">Demo Scenario: <span style="color: #60a5fa;">Progressive Internal Attack</span></h2>
                    <div style="color: #94a3b8; font-size: 14px; margin-top: 4px;">Simulate how an attacker moves inside the network and see how risk evolves over time.</div>
                </div>
            </div>
            <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid #334155; border-radius: 8px; padding: 8px 12px; display: flex; gap: 8px; align-items: center;">
                <div style="color: #60a5fa;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg></div>
                <div>
                    <div style="font-size: 12px; color: #f1f5f9; font-weight: 600;">Simulated Environment</div>
                    <div style="font-size: 10px; color: #94a3b8;">No live monitoring • For demo only</div>
                </div>
            </div>
        </div>

        <div style="display: flex; gap: 8px; align-items: center; overflow-x: auto; padding-bottom: 8px;">
            <!-- Step 1: Observe -->
            <div style="flex: 1; min-width: 140px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 8px; padding: 10px; position: relative; box-shadow: 0 0 15px rgba(16, 185, 129, 0.15);">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="color: #10b981; display: flex; align-items: center; justify-content: center;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></div>
                    <div>
                        <div style="font-size: 13px; font-weight: bold; color: #f1f5f9; line-height: 1.2;">Observe</div>
                        <div style="font-size: 10px; color: #10b981;">Normal behavior</div>
                    </div>
                </div>
            </div>
            <div style="color: #475569; font-size: 16px;">&rarr;</div>
            
            <!-- Step 2: Window -->
            <div style="flex: 1; min-width: 140px; background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 8px; padding: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="color: #3b82f6; display: flex; align-items: center; justify-content: center;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg></div>
                    <div>
                        <div style="font-size: 13px; font-weight: bold; color: #f1f5f9; line-height: 1.2;">Window</div>
                        <div style="font-size: 10px; color: #94a3b8;">Time-based analysis</div>
                    </div>
                </div>
            </div>
            <div style="color: #475569; font-size: 16px;">&rarr;</div>

            <!-- Step 3: Learn -->
            <div style="flex: 1; min-width: 140px; background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 8px; padding: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="color: #a855f7; display: flex; align-items: center; justify-content: center;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"></path></svg></div>
                    <div>
                        <div style="font-size: 13px; font-weight: bold; color: #f1f5f9; line-height: 1.2;">Learn</div>
                        <div style="font-size: 10px; color: #94a3b8;">Model learns patterns</div>
                    </div>
                </div>
            </div>
            <div style="color: #475569; font-size: 16px;">&rarr;</div>

            <!-- Step 4: Forecast -->
            <div style="flex: 1; min-width: 140px; background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 8px; padding: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="color: #eab308; display: flex; align-items: center; justify-content: center;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg></div>
                    <div>
                        <div style="font-size: 13px; font-weight: bold; color: #f1f5f9; line-height: 1.2;">Forecast</div>
                        <div style="font-size: 10px; color: #94a3b8;">Predict next risk</div>
                    </div>
                </div>
            </div>
            <div style="color: #475569; font-size: 16px;">&rarr;</div>

            <!-- Step 5: Explain -->
            <div style="flex: 1; min-width: 140px; background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 8px; padding: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="color: #ec4899; display: flex; align-items: center; justify-content: center;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg></div>
                    <div>
                        <div style="font-size: 13px; font-weight: bold; color: #f1f5f9; line-height: 1.2;">Explain</div>
                        <div style="font-size: 10px; color: #94a3b8;">Show key factors</div>
                    </div>
                </div>
            </div>
            <div style="color: #475569; font-size: 16px;">&rarr;</div>

            <!-- Step 6: Prioritize -->
            <div style="flex: 1; min-width: 140px; background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 8px; padding: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="color: #f43f5e; display: flex; align-items: center; justify-content: center;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg></div>
                    <div>
                        <div style="font-size: 13px; font-weight: bold; color: #f1f5f9; line-height: 1.2;">Prioritize</div>
                        <div style="font-size: 10px; color: #94a3b8;">Rank by severity</div>
                    </div>
                </div>
            </div>
            <div style="color: #475569; font-size: 16px;">&rarr;</div>

            <!-- Step 7: Review -->
            <div style="flex: 1; min-width: 140px; background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 8px; padding: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="color: #10b981; display: flex; align-items: center; justify-content: center;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg></div>
                    <div>
                        <div style="font-size: 13px; font-weight: bold; color: #f1f5f9; line-height: 1.2;">Review</div>
                        <div style="font-size: 10px; color: #94a3b8;">Final insights</div>
                    </div>
                </div>
            </div>
        </div>


    </div>
    """)

def demo_metric_html(label: str, value: str, icon_svg: str = "") -> str:
    return strip_indentation(f"""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 8px; padding: 12px 16px; height: 60px; display: flex; align-items: center; gap: 12px;">
        <div style="color: #60a5fa; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;">{icon_svg}</div>
        <div>
            <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">{label}</div>
            <div style="font-size: 14px; font-weight: bold; color: #f1f5f9; margin-top: 2px;">{value}</div>
        </div>
    </div>
    """)

def demo_scenario_type_html() -> str:
    return strip_indentation("""
    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 8px; padding: 12px 16px; height: 60px; display: flex; align-items: center; gap: 12px;">
        <div style="color: #ef4444; width: 28px; height: 28px; border-radius: 50%; background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); display: flex; align-items: center; justify-content: center;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>
        </div>
        <div>
            <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">Scenario Type</div>
            <div style="font-size: 14px; font-weight: bold; color: #ef4444; margin-top: 2px;">Progressive Internal Attack</div>
            <div style="font-size: 9px; color: #64748b; margin-top: 1px;">From normal activity &rarr; lateral movement &rarr; high risk</div>
        </div>
    </div>
    """)

def demo_run_log_html(current_phase: int) -> str:
    # Phase configs based on SCENARIO_PHASES in forecast_engine.py
    phases = [
        {"desc": "Normal network behavior", "r_start": 18, "r_end": 28, "level": "Low", "color": "#10b981"},
        {"desc": "Reconnaissance activity increases", "r_start": 36, "r_end": 44, "level": "Medium", "color": "#eab308"},
        {"desc": "SYN activity increases", "r_start": 54, "r_end": 58, "level": "Medium", "color": "#f97316"},
        {"desc": "Multiple internal ports are probed", "r_start": 68, "r_end": 66, "level": "High", "color": "#f97316"},
        {"desc": "Connections to multiple internal systems increase", "r_start": 68, "r_end": 69, "level": "High", "color": "#ef4444"},
        {"desc": "Model forecasts lateral movement", "r_start": 68, "r_end": 79, "level": "High", "color": "#ef4444"},
        {"desc": "Future risk crosses the alert threshold", "r_start": 68, "r_end": 84, "level": "Critical", "color": "#e11d48"},
    ]
    
    rows = []
    for i, p in enumerate(phases):
        is_active = (i + 1) == current_phase
        is_done = (i + 1) < current_phase
        
        if is_done or (current_phase == 7 and i == 6):
            icon = f'<div style="width:24px;height:24px;border-radius:50%;background:#10b981;color:white;display:flex;align-items:center;justify-content:center;font-size:14px;box-shadow:0 0 10px rgba(16,185,129,0.5);z-index:2;position:relative;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></div>'
            bg_color = "transparent"
            text_color = "#f1f5f9"
            border = "border-bottom: 1px solid #1e293b;"
            row_glow = ""
        elif is_active:
            icon = f'<div style="width:24px;height:24px;border-radius:50%;border:2px solid {p["color"]};background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;box-shadow:0 0 15px {p["color"]}, inset 0 0 5px {p["color"]};z-index:2;position:relative;"><div style="width:8px;height:8px;border-radius:50%;background:{p["color"]};"></div></div>'
            bg_color = f"rgba(168, 85, 247, 0.05)"
            text_color = p["color"]
            border = f"border: 1px solid rgba(168, 85, 247, 0.4); border-radius: 8px;"
            row_glow = "box-shadow: 0 0 20px rgba(168, 85, 247, 0.1);"
        else:
            icon = f'<div style="width:24px;height:24px;border-radius:50%;border:2px solid #334155;background:#0f172a;z-index:2;position:relative;"></div>'
            bg_color = "transparent"
            text_color = "#64748b"
            border = "border-bottom: 1px solid #1e293b;"
            row_glow = ""
            
        progress_width = f"{p['r_end']}%"
        
        badge_style = f"border: 1px solid {p['color']}; color: {p['color']}; padding: 2px 12px; border-radius: 12px; font-size: 11px; font-weight: bold; width: 80px; white-space: nowrap; text-align: center; box-shadow: inset 0 0 5px {p['color']}20;"
        if p['level'] == "Critical":
            badge_style = f"background: rgba(225,29,72,0.1); border: 1px solid {p['color']}; color: {p['color']}; padding: 2px 12px; border-radius: 12px; font-size: 11px; font-weight: bold; width: 80px; white-space: nowrap; text-align: center; box-shadow: 0 0 10px rgba(225,29,72,0.3), inset 0 0 10px rgba(225,29,72,0.2);"

        # Add connecting vertical line behind icons (except last row)
        line_html = ""
        if i < len(phases) - 1:
            line_color = "#10b981" if is_done else "#334155"
            line_html = f'<div style="position:absolute; width:2px; height:100%; background:{line_color}; left:11px; top:24px; z-index:1; opacity:0.5;"></div>'

        row_html = f"""
        <div style="display: flex; align-items: center; padding: 12px 16px; margin: 2px 0; {border} background: {bg_color}; {row_glow} position: relative;">
            <div style="width: 40px; position: relative;">
                {icon}
                {line_html}
            </div>
            <div style="width: 100px; font-size: 13px; font-weight: bold; color: {p['color'] if is_active else text_color};">Phase {i+1}/7</div>
            <div style="flex: 1; font-size: 13px; color: {'#94a3b8' if not is_done and not is_active else '#cbd5e1'};">{p['desc']}</div>
            <div style="width: 120px; font-size: 12px; color: {p['color'] if (is_done or is_active) else '#475569'};"><span style="color:#64748b">Risk:</span> {p['r_start']}% &rarr; {p['r_end']}%</div>
            <div style="width: 120px; display: flex; align-items: center; gap: 8px;">
                <div style="flex: 1; height: 6px; background: #1e293b; border-radius: 3px; overflow: hidden;">
                    <div style="width: {progress_width}; height: 100%; background: {p['color'] if (is_done or is_active) else '#334155'}; border-radius: 3px; box-shadow: 0 0 8px {p['color'] if (is_done or is_active) else 'transparent'};"></div>
                </div>
            </div>
            <div style="width: 40px; font-size: 12px; font-weight: bold; color: #f1f5f9; text-align: right; margin-right: 16px;">{p['r_end']}%</div>
            <div><div style="{badge_style}">{p['level']}</div></div>
        </div>
        """
        rows.append(row_html)
        
    return strip_indentation(f"""
    <style>
    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
    <div style="background: #0B1224; border: 1px solid #1e293b; border-radius: 12px; overflow: hidden; height: 100%;">
        <div style="padding: 16px 20px; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="color: #22d3ee;"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg></div>
                <div>
                    <h3 style="margin: 0; font-size: 16px; color: #f1f5f9;">Scenario Run Log</h3>
                    <div style="font-size: 12px; color: #94a3b8;">Step-by-step progression of the simulated attack</div>
                </div>
            </div>
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #10b981; font-size: 11px; padding: 4px 10px; border-radius: 12px; display: flex; align-items: center; gap: 6px;">
                <div style="width: 6px; height: 6px; border-radius: 50%; background: #10b981; box-shadow: 0 0 6px #10b981;"></div>
                Simulation Running...
            </div>
        </div>
        <div>
            {''.join(rows)}
        </div>
    </div>
    """)

def demo_network_progression_html(current_phase: int) -> str:
    nodes = [
        {"label": "Normal Network", "icon": '<circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>'},
        {"label": "Recon Activity", "icon": '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>'},
        {"label": "SYN Increase", "icon": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>'},
        {"label": "Port Scanning", "icon": '<rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line>'},
        {"label": "Internal Connections", "icon": '<rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line>'},
        {"label": "Lateral Movement", "icon": '<circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>'},
        {"label": "High Risk (Alert)", "icon": '<circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle>'}
    ]
    
    html = strip_indentation("""
    <div style="background: #0B1224; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; height: 100%;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 24px;">
            <div style="color: #60a5fa;"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg></div>
            <div>
                <h3 style="margin: 0; font-size: 15px; color: #f1f5f9;">Network Attack Progression</h3>
                <div style="font-size: 12px; color: #94a3b8;">Visual representation of attacker movement</div>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; padding: 10px 0;">
    """)
    
    for i, node in enumerate(nodes):
        phase = i + 1
        
        # Determine styling based on phase
        if phase <= current_phase:
            if phase == 7:
                color = "#ef4444" # Critical (Red)
                shadow = "0 0 15px rgba(239, 68, 68, 0.4), inset 0 0 10px rgba(239, 68, 68, 0.4)"
            elif phase >= 4:
                color = "#eab308" if phase == 4 else "#ec4899" if phase == 5 else "#f43f5e"
                shadow = f"0 0 15px {color}60, inset 0 0 10px {color}60"
            elif phase >= 2:
                color = "#3b82f6" if phase == 2 else "#a855f7"
                shadow = f"0 0 15px {color}60, inset 0 0 10px {color}60"
            else:
                color = "#10b981" # Low (Green)
                shadow = "0 0 15px rgba(16, 185, 129, 0.4), inset 0 0 10px rgba(16, 185, 129, 0.4)"
            border_width = "2px"
            bg = "#0f172a"
        else:
            color = "#475569"
            shadow = "none"
            border_width = "1px"
            bg = "transparent"
            
        arrow = f'<div style="color: {color}; margin-top: 20px; font-size: 18px;">&rarr;</div>' if i < len(nodes) - 1 else ""
        
        html += strip_indentation(f"""
            <div style="display: flex; flex-direction: column; align-items: center; width: 60px;">
                <div style="width: 44px; height: 44px; border-radius: 50%; border: {border_width} solid {color}; background: {bg}; display: flex; align-items: center; justify-content: center; color: {color}; box-shadow: {shadow}; margin-bottom: 12px; transition: all 0.3s ease;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">{node['icon']}</svg>
                </div>
                <div style="font-size: 11px; color: {'#f1f5f9' if phase <= current_phase else '#64748b'}; text-align: center; line-height: 1.3;">{node['label']}</div>
            </div>
            {arrow}
        """)
        
    html += strip_indentation("""
        </div>
    </div>
    """)
    return html

def risk_trend_demo_html(current_phase: int) -> str:
    phases = [1, 2, 3, 4, 5, 6, 7]
    obs_risk = [18, 36, 54, 68, 68, 68, 68]
    for_risk = [28, 44, 58, 66, 69, 79, 84]
    
    def get_x_pct(phase_idx):
        return (phase_idx / 6) * 100
        
    def get_y_pct(risk):
        return 100 - risk

    grid_html = ""
    for val in [0, 25, 50, 75, 100]:
        y = get_y_pct(val)
        grid_html += f'<div style="position: absolute; left: 0; right: 0; top: {y}%; border-top: 1px dashed rgba(148,163,184,0.15);"></div>'
        grid_html += f'<div style="position: absolute; left: -36px; top: calc({y}% - 6px); font-size: 11px; color: #94a3b8; text-align: right; width: 28px;">{val}%</div>'

    for i, p in enumerate(phases):
        x = get_x_pct(i)
        grid_html += f'<div style="position: absolute; left: {x}%; top: 0; bottom: 0; border-left: 1px dashed rgba(148,163,184,0.08);"></div>'
        grid_html += f'<div style="position: absolute; left: calc({x}% - 24px); bottom: -24px; width: 48px; text-align: center; font-size: 11px; color: #94a3b8;">Phase {p}</div>'

    obs_points = " ".join([f"{get_x_pct(i)},{get_y_pct(obs_risk[i])}" for i in range(current_phase)])
    for_points = " ".join([f"{get_x_pct(i)},{get_y_pct(for_risk[i])}" for i in range(current_phase)])
    
    svg_lines = f"""
    <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none" style="position: absolute; left: 0; top: 0; overflow: visible;">
        <polyline points="{obs_points}" fill="none" stroke="#3b82f6" stroke-width="2" vector-effect="non-scaling-stroke" />
        <polyline points="{for_points}" fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="4,4" vector-effect="non-scaling-stroke" />
    </svg>
    """
    
    points_html = ""
    for i in range(current_phase):
        points_html += f'<div style="position: absolute; left: {get_x_pct(i)}%; top: {get_y_pct(obs_risk[i])}%; width: 10px; height: 10px; border-radius: 50%; background: #3b82f6; transform: translate(-50%, -50%); box-shadow: 0 0 10px #3b82f6; z-index: 2;"></div>'
        points_html += f'<div style="position: absolute; left: {get_x_pct(i)}%; top: {get_y_pct(for_risk[i])}%; width: 8px; height: 8px; border-radius: 50%; background: #ef4444; transform: translate(-50%, -50%); box-shadow: 0 0 10px #ef4444; z-index: 2;"></div>'

    html = f"""
    <div style="background: #0B1224; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; display: flex; flex-direction: column;">
        <div style="display: flex; flex-direction: column; gap: 4px;">
            <div style="font-size: 19px; color: #f1f5f9; font-weight: 700;">Risk Trend (Observed vs Forecast)</div>
            <div style="font-size: 13.5px; color: #94a3b8;">Risk level progression across phases</div>
        </div>
        
        <div style="height: 12px;"></div>
        
        <div style="display: flex; gap: 16px; align-items: center; justify-content: flex-end; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 12px; height: 12px; border-radius: 50%; background: #3b82f6; box-shadow: 0 0 8px rgba(59,130,246,0.6);"></div>
                <span style="font-size: 13px; color: #cbd5e1; font-weight: 500;">Observed Risk</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="display: flex; align-items: center; width: 18px; justify-content: space-between;">
                    <div style="width: 6px; height: 2px; background: #ef4444;"></div>
                    <div style="width: 6px; height: 2px; background: #ef4444;"></div>
                </div>
                <span style="font-size: 13px; color: #cbd5e1; font-weight: 500;">Forecasted Risk</span>
            </div>
        </div>
        
        <div style="margin-top: 24px; margin-left: 40px; margin-right: 20px; margin-bottom: 24px; height: 180px; position: relative;">
            {grid_html}
            {svg_lines}
            {points_html}
        </div>
    </div>
    """
    return strip_indentation(html)
