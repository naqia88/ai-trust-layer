import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.chdir(PROJECT_ROOT)

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from config import AUTO_APPROVE, AUTO_BLOCK, FLAG_FOR_REVIEW
from database.audit import get_actions, init_db, resolve_action
from trust.interceptor import intercept_action
from worker.agent import (
    create_execute_code_action,
    create_send_email_action,
    create_transfer_money_action,
)

# ── Constants ─────────────────────────────────────────────────────────────────

DECISIONS = ["approved", "approved_with_warning", "escalated", "blocked"]
ACTION_TYPES = ["transfer_money", "send_email", "execute_code"]

DECISION_COLORS = {
    "approved": "#22c55e",
    "approved_with_warning": "#f59e0b",
    "escalated": "#f97316",
    "blocked": "#ef4444",
}

DECISION_ICONS = {
    "approved": "✅",
    "approved_with_warning": "⚠️",
    "escalated": "🔺",
    "blocked": "🚫",
}

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Trust Layer",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded",
)

# ── Custom CSS - Figma Dashboard Style ──────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: #f5f7fb;
    }

    [data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #eef2f6 !important;
        padding-top: 20px !important;
        box-shadow: none !important;
    }

    .sidebar-header {
        padding: 0 20px 20px 20px;
        border-bottom: 1px solid #f0f2f5;
        margin-bottom: 16px;
    }
    .sidebar-header .logo {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .sidebar-header .logo-icon {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #7c3aed, #6d28d9);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        font-size: 16px;
    }
    .sidebar-header .logo-text {
        font-size: 18px;
        font-weight: 700;
        color: #111827;
    }
    .sidebar-header .logo-text span {
        color: #7c3aed;
    }

    .nav-section {
        padding: 0 12px;
    }
    .nav-section .nav-label {
        font-size: 11px;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding: 8px 12px 6px 12px;
    }
    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 9px 14px;
        border-radius: 10px;
        color: #6b7280;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.15s ease;
        cursor: pointer;
        margin: 1px 0;
    }
    .nav-item:hover {
        background: #f3f4f6;
        color: #111827;
    }
    .nav-item.active {
        background: #7c3aed;
        color: #ffffff;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
    }
    .nav-item .icon {
        font-size: 16px;
        width: 22px;
        text-align: center;
    }
    .nav-item .badge {
        margin-left: auto;
        background: #ef4444;
        color: #fff;
        font-size: 10px;
        padding: 1px 10px;
        border-radius: 20px;
        font-weight: 600;
    }

    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0 20px 0;
        border-bottom: 1px solid #f0f2f5;
        margin-bottom: 24px;
    }
    .main-header h1 {
        font-size: 24px;
        font-weight: 700;
        color: #111827;
        margin: 0;
        letter-spacing: -0.3px;
    }
    .main-header .header-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .main-header .status-badge {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        background: #ecfdf5;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        color: #10b981;
    }
    .main-header .status-badge .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
    .main-header .avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7c3aed, #6d28d9);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 14px;
    }

    [data-testid="metric-container"] {
        background: #ffffff !important;
        border: 1px solid #f0f2f5 !important;
        border-radius: 16px !important;
        padding: 20px 24px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="metric-container"]:hover {
        box-shadow: 0 8px 25px rgba(0,0,0,0.06) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="metric-container"] label {
        color: #9ca3af !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #111827 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #ffffff;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #f0f2f5;
        margin-bottom: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #6b7280;
        font-weight: 500;
        font-size: 14px;
        padding: 8px 20px;
        transition: all 0.15s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #111827;
        background: #f3f4f6;
    }
    .stTabs [aria-selected="true"] {
        background: #7c3aed !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(124, 58, 237, 0.25);
    }

    .streamlit-expanderHeader {
        background: #ffffff !important;
        border: 1px solid #f0f2f5 !important;
        border-radius: 12px !important;
        color: #111827 !important;
        font-weight: 500 !important;
        padding: 12px 16px !important;
        transition: all 0.15s;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }
    .streamlit-expanderHeader:hover {
        border-color: #d1d5db !important;
        background: #fafafa !important;
    }
    .streamlit-expanderContent {
        background: #ffffff !important;
        border: 1px solid #f0f2f5 !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 16px !important;
    }

    .stButton > button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.15s !important;
        border: 1px solid #e5e7eb !important;
        background: #ffffff !important;
        color: #111827 !important;
        padding: 8px 20px !important;
        height: auto !important;
    }
    .stButton > button:hover {
        background: #f3f4f6 !important;
        border-color: #d1d5db !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }

    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 10px !important;
        color: #111827 !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        transition: all 0.15s;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.08) !important;
    }
    .stSelectbox > div > div {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 10px !important;
        color: #111827 !important;
    }
    .stSelectbox > div > div:hover {
        border-color: #7c3aed !important;
    }

    .stDataFrame {
        border: 1px solid #f0f2f5;
        border-radius: 12px;
        overflow: hidden;
    }
    .stDataFrame thead tr th {
        background: #f9fafb !important;
        color: #6b7280 !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 16px !important;
        border-bottom: 1px solid #f0f2f5 !important;
    }
    .stDataFrame tbody tr td {
        color: #111827 !important;
        padding: 10px 16px !important;
        border-bottom: 1px solid #f9fafb !important;
        font-size: 14px;
    }
    .stDataFrame tbody tr:hover td {
        background: #fafbfc !important;
    }

    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        padding: 14px 18px !important;
    }
    .stAlert.info {
        background: #eef2ff !important;
        border-left: 3px solid #7c3aed !important;
    }
    .stAlert.success {
        background: #ecfdf5 !important;
        border-left: 3px solid #10b981 !important;
    }
    .stAlert.warning {
        background: #fffbeb !important;
        border-left: 3px solid #f59e0b !important;
    }
    .stAlert.error {
        background: #fef2f2 !important;
        border-left: 3px solid #ef4444 !important;
    }

    .band-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
        border: 1px solid #f0f2f5;
        background: #ffffff;
    }

    .score-bar-wrap {
        background: #f3f4f6;
        border-radius: 999px;
        height: 6px;
        width: 100%;
        overflow: hidden;
    }
    .score-bar-fill {
        height: 6px;
        border-radius: 999px;
        transition: width 0.6s ease;
    }

    .divider {
        border: none;
        height: 1px;
        background: #f0f2f5;
        margin: 24px 0;
    }

    @media (max-width: 768px) {
        .main-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
        }
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-size: 22px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def decode_json(value, default_value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default_value
    return value if value is not None else default_value


def load_actions():
    actions = []
    for action in get_actions():
        action["details"] = decode_json(action["details"], {})
        action["reasons"] = decode_json(action["reasons"], [])
        actions.append(action)
    return actions


def filter_actions(actions, decisions, action_types):
    return [
        a for a in actions
        if a["decision"] in decisions and a["action_type"] in action_types
    ]


def count_decisions(actions):
    counts = {d: 0 for d in DECISIONS}
    for a in actions:
        counts[a["decision"]] += 1
    return counts


def get_open_escalations(actions):
    return [a for a in actions if a["decision"] == "escalated" and not a["resolved_by"]]


def build_sample_action(sample_name):
    if sample_name == "Routine PKR transfer (approved)":
        return create_transfer_money_action(50000, "PKR", "Verified Vendor", "Monthly office supplies invoice")
    if sample_name == "Production cleanup command (warning)":
        return create_execute_code_action("DROP TABLE temporary_logs;", "production", "SQL")
    if sample_name == "High-risk transfer (escalated)":
        return create_transfer_money_action(250000, "PKR", "Unverified Vendor", "Please call 03001234567 before processing.")
    if sample_name == "Email containing a CNIC (escalated)":
        return create_send_email_action("unknown@partner.example", "Customer verification", "Customer CNIC: 35202-1234567-1", False, "")
    return create_transfer_money_action(250000, "USD", "Unverified Vendor", "Customer CNIC: 35202-1234567-1")


def score_color(score):
    if score <= AUTO_APPROVE:
        return DECISION_COLORS["approved"]
    elif score <= FLAG_FOR_REVIEW:
        return DECISION_COLORS["approved_with_warning"]
    elif score < AUTO_BLOCK:
        return DECISION_COLORS["escalated"]
    return DECISION_COLORS["blocked"]


def render_score_bar(score, label=""):
    color = score_color(score)
    st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin:4px 0;">
          <span style="color:#6b7280;font-size:13px;font-weight:500;width:80px;flex-shrink:0;">{label}</span>
          <div class="score-bar-wrap" style="flex:1;">
            <div class="score-bar-fill" style="width:{score}%;background:{color};"></div>
          </div>
          <span style="color:#111827;font-size:14px;font-weight:600;width:32px;text-align:right;flex-shrink:0;">{score}</span>
        </div>
    """, unsafe_allow_html=True)


def show_decision_result(result):
    decision = result["decision"]
    color = DECISION_COLORS[decision]
    icon = DECISION_ICONS[decision]
    label = decision.replace("_", " ").title()

    st.markdown(f"""
        <div style="background:#ffffff;border:1px solid #f0f2f5;
                    border-left:4px solid {color};border-radius:12px;padding:16px 20px;margin:12px 0;
                    box-shadow:0 1px 3px rgba(0,0,0,0.02);">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <span style="font-size:24px;">{icon}</span>
            <span style="color:{color};font-size:18px;font-weight:700;">{label}</span>
            <span style="color:#9ca3af;font-size:14px;margin-left:auto;">
              Final score: <b style="color:#111827;font-size:16px;">{result['final_score']}</b>
            </span>
          </div>
        </div>
    """, unsafe_allow_html=True)

    if result["reasons"]:
        st.markdown("<div style='margin-top:6px;'>", unsafe_allow_html=True)
        for reason in result["reasons"]:
            st.markdown(f"<span style='color:#f59e0b;font-size:14px;'>⚡ {reason}</span><br>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def submit_action(action):
    st.session_state["last_result"] = intercept_action(action)
    st.rerun()

# ── Init ──────────────────────────────────────────────────────────────────────

init_db()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
        <div class="sidebar-header">
            <div class="logo">
                <div class="logo-icon">🛡️</div>
                <div class="logo-text">Trust<span>Layer</span></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="nav-section">
            <div class="nav-label">Main</div>
            <div class="nav-item active">
                <span class="icon">📊</span> Dashboard
            </div>
            <div class="nav-item">
                <span class="icon">📋</span> Audit Log
            </div>
            <div class="nav-item">
                <span class="icon">🔺</span> Review Queue
                <span class="badge">12</span>
            </div>
            <div class="nav-item">
                <span class="icon">🧪</span> Test Action
            </div>
        </div>
        <div style="height:16px;"></div>
        <div class="nav-section">
            <div class="nav-label">Settings</div>
            <div class="nav-item">
                <span class="icon">⚙️</span> Preferences
            </div>
            <div class="nav-item">
                <span class="icon">👤</span> Profile
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🎛️ Filters")
    
    selected_decisions = st.multiselect(
        "Decision Status",
        DECISIONS,
        default=DECISIONS,
        format_func=lambda d: f"{DECISION_ICONS[d]}  {d.replace('_', ' ').title()}",
    )
    selected_action_types = st.multiselect(
        "Action Type",
        ACTION_TYPES,
        default=ACTION_TYPES,
        format_func=lambda t: t.replace("_", " ").title(),
    )
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# ── MAIN CONTENT ─────────────────────────────────────────────────────────────

all_actions = load_actions()
filtered_actions = filter_actions(all_actions, selected_decisions, selected_action_types)
decision_counts = count_decisions(all_actions)
open_escalations = get_open_escalations(all_actions)
average_score = (
    sum(a["final_score"] for a in all_actions) / len(all_actions) if all_actions else 0
)

# ── PAGE HEADER ─────────────────────────────────────────────────────────────

st.markdown("""
    <div class="main-header">
        <h1>AI Trust Layer</h1>
        <div class="header-right">
            <div class="status-badge">
                <span class="dot"></span> System Online
            </div>
            <div class="avatar">JD</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── DECISION BANDS ───────────────────────────────────────────────────────────

st.markdown(f"""
    <div style="margin-bottom:24px;display:flex;flex-wrap:wrap;gap:4px;">
        <span class="band-pill" style="border-color:#22c55e;color:#22c55e;">✅ 0–{AUTO_APPROVE} Approved</span>
        <span class="band-pill" style="border-color:#f59e0b;color:#f59e0b;">⚠️ {AUTO_APPROVE+1}–{FLAG_FOR_REVIEW} Warning</span>
        <span class="band-pill" style="border-color:#f97316;color:#f97316;">🔺 {FLAG_FOR_REVIEW+1}–{AUTO_BLOCK-1} Escalated</span>
        <span class="band-pill" style="border-color:#ef4444;color:#ef4444;">🚫 {AUTO_BLOCK}–100 Blocked</span>
    </div>
""", unsafe_allow_html=True)

# ── METRICS ROW ──────────────────────────────────────────────────────────────

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
with c1:
    st.metric("Total Actions", len(all_actions))
with c2:
    st.metric("Open Escalations", len(open_escalations))
with c3:
    st.metric("Avg Risk Score", f"{average_score:.1f}")
with c4:
    st.metric("✅ Approved", decision_counts["approved"])
with c5:
    st.metric("⚠️ Warnings", decision_counts["approved_with_warning"])
with c6:
    st.metric("🔺 Escalated", decision_counts["escalated"])
with c7:
    st.metric("🚫 Blocked", decision_counts["blocked"])

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── CHARTS ROW ────────────────────────────────────────────────────────────────

if all_actions:
    chart_col1, chart_col2 = st.columns([1, 2])

    with chart_col1:
        labels = [d.replace("_", " ").title() for d in DECISIONS]
        values = [decision_counts[d] for d in DECISIONS]
        colors = [DECISION_COLORS[d] for d in DECISIONS]

        fig_donut = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.65,
            marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
        ))
        fig_donut.add_annotation(
            text=f"<b>{len(all_actions)}</b><br><span style='font-size:11px;color:#9ca3af;'>actions</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=22, color="#111827", family="Inter"),
        )
        fig_donut.update_layout(
            title=dict(text="Decision Breakdown", font=dict(color="#111827", size=16, weight=600)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#6b7280", family="Inter"),
            legend=dict(font=dict(color="#6b7280"), bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=-0.12),
            margin=dict(t=40, b=30, l=10, r=10),
            height=300,
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with chart_col2:
        if filtered_actions:
            df = pd.DataFrame(filtered_actions)
            fig_bar = px.box(
                df,
                x="action_type",
                y="final_score",
                color="decision",
                color_discrete_map=DECISION_COLORS,
                labels={"action_type": "Action Type", "final_score": "Risk Score", "decision": "Decision"},
                title="Risk Score Distribution by Action Type",
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#6b7280", family="Inter"),
                title=dict(font=dict(color="#111827", size=16, weight=600)),
                legend=dict(font=dict(color="#6b7280"), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(gridcolor="#f0f2f5", tickfont=dict(color="#6b7280")),
                yaxis=dict(gridcolor="#f0f2f5", tickfont=dict(color="#6b7280"), range=[0, 100]),
                margin=dict(t=40, b=10, l=10, r=10),
                height=300,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────

audit_tab, review_tab, submit_tab = st.tabs([
    "📋 Audit Log",
    f"🔺 Review Queue  {'  🔴 ' + str(len(open_escalations)) if open_escalations else ''}",
    "🧪 Submit Test Action",
])

# ── Audit Log ─────────────────────────────────────────────────────────────────

with audit_tab:
    if not filtered_actions:
        st.info("No audit records match the current filters.")
    else:
        df = pd.DataFrame([
            {
                "ID": a["id"],
                "Timestamp": a["timestamp"],
                "Type": a["action_type"].replace("_", " ").title(),
                "Financial": a["financial_score"],
                "Privacy": a["privacy_score"],
                "Policy": a["policy_score"],
                "Final": a["final_score"],
                "Decision": DECISION_ICONS[a["decision"]] + " " + a["decision"].replace("_", " ").title(),
                "Resolution": a["resolution"] or "Open",
            }
            for a in filtered_actions
        ])

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Final": st.column_config.ProgressColumn(
                    "Final Score",
                    help="Final risk score (0–100)",
                    min_value=0,
                    max_value=100,
                    format="%d",
                ),
                "Financial": st.column_config.ProgressColumn(
                    "Financial",
                    min_value=0,
                    max_value=100,
                    format="%d",
                ),
                "Privacy": st.column_config.ProgressColumn(
                    "Privacy",
                    min_value=0,
                    max_value=100,
                    format="%d",
                ),
                "Policy": st.column_config.ProgressColumn(
                    "Policy",
                    min_value=0,
                    max_value=100,
                    format="%d",
                ),
            },
        )

        st.markdown(f"<p style='color:#9ca3af;font-size:13px;margin-top:6px;'>"
                    f"Showing {len(filtered_actions)} of {len(all_actions)} actions</p>",
                    unsafe_allow_html=True)

        st.markdown("### Action Details")
        for action in filtered_actions:
            dec = action["decision"]
            with st.expander(
                f"{DECISION_ICONS[dec]}  Action {action['id']}  ·  "
                f"{action['action_type'].replace('_', ' ').title()}  ·  "
                f"Score {action['final_score']}"
            ):
                left, right = st.columns([1, 1])
                with left:
                    st.markdown("**Score breakdown**")
                    render_score_bar(action["financial_score"], "Financial")
                    render_score_bar(action["privacy_score"], "Privacy")
                    render_score_bar(action["policy_score"], "Policy")
                    render_score_bar(action["final_score"], "Final")
                with right:
                    st.markdown("**Action details**")
                    st.json(action["details"])

                if action["reasons"]:
                    st.markdown("**Risk reasons**")
                    for r in action["reasons"]:
                        st.markdown(f"<span style='color:#f59e0b;font-size:14px;'>⚡ {r}</span>",
                                    unsafe_allow_html=True)

                if action["resolved_by"]:
                    st.markdown(
                        f"<div style='margin-top:10px;padding:10px;background:#f9fafb;"
                        f"border-radius:8px;border:1px solid #f0f2f5;'>"
                        f"<span style='color:#6b7280;font-size:13px;'>"
                        f"Resolved by <b style='color:#111827;'>{action['resolved_by']}</b> · "
                        f"{action['resolution']} · {action['resolution_time']}"
                        f"</span></div>",
                        unsafe_allow_html=True,
                    )

# ── Review Queue ──────────────────────────────────────────────────────────────

with review_tab:
    if "review_message" in st.session_state:
        st.success(st.session_state.pop("review_message"))

    if not open_escalations:
        st.markdown("""
        <div style="text-align:center;padding:48px 0;">
          <div style="font-size:48px;">✅</div>
          <p style="color:#10b981;font-weight:600;font-size:18px;margin:8px 0;">All clear</p>
          <p style="color:#9ca3af;font-size:14px;">No open escalations require attention.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color:#f97316;font-weight:600;font-size:16px;'>"
                    f"🔺 {len(open_escalations)} action(s) need your review</p>",
                    unsafe_allow_html=True)

        reviewer_name = st.text_input(
            "Your name",
            placeholder="Enter your name before approving or rejecting",
            help="Required for audit trail",
        )

        for action in open_escalations:
            with st.expander(
                f"🔺  Action {action['id']}  ·  "
                f"{action['action_type'].replace('_', ' ').title()}  ·  "
                f"Score {action['final_score']}"
            ):
                left, right = st.columns([1, 1])
                with left:
                    st.markdown("**Score breakdown**")
                    render_score_bar(action["financial_score"], "Financial")
                    render_score_bar(action["privacy_score"], "Privacy")
                    render_score_bar(action["policy_score"], "Policy")
                    render_score_bar(action["final_score"], "Final")
                with right:
                    st.markdown("**Action details**")
                    st.json(action["details"])

                if action["reasons"]:
                    st.markdown("**Risk reasons**")
                    for r in action["reasons"]:
                        st.markdown(f"<span style='color:#f59e0b;font-size:14px;'>⚡ {r}</span>",
                                    unsafe_allow_html=True)

                st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                approve_col, reject_col = st.columns(2)

                if approve_col.button(
                    "✅  Approve", key=f"approve_{action['id']}", use_container_width=True
                ):
                    if not reviewer_name.strip():
                        st.warning("Enter your name before resolving.")
                    else:
                        resolve_action(action["id"], reviewer_name.strip(), "approved")
                        st.session_state["review_message"] = (
                            f"Action {action['id']} approved by {reviewer_name.strip()}."
                        )
                        st.rerun()

                if reject_col.button(
                    "🚫  Reject", key=f"reject_{action['id']}", use_container_width=True
                ):
                    if not reviewer_name.strip():
                        st.warning("Enter your name before resolving.")
                    else:
                        resolve_action(action["id"], reviewer_name.strip(), "rejected")
                        st.session_state["review_message"] = (
                            f"Action {action['id']} rejected by {reviewer_name.strip()}."
                        )
                        st.rerun()

    resolved = [a for a in all_actions if a["resolved_by"]]
    if resolved:
        st.markdown("---")
        st.markdown("### Recently resolved")
        for a in resolved[:5]:
            color = "#22c55e" if a["resolution"] == "approved" else "#ef4444"
            st.markdown(
                f"<div style='padding:8px 14px;margin:4px 0;background:#ffffff;"
                f"border-radius:8px;border:1px solid #f0f2f5;border-left:3px solid {color};'>"
                f"<span style='color:#111827;font-size:14px;'>"
                f"Action {a['id']} — <b style='color:{color};'>{a['resolution']}</b>"
                f" by {a['resolved_by']} · {a['resolution_time']}"
                f"</span></div>",
                unsafe_allow_html=True,
            )

# ── Submit Test Action ────────────────────────────────────────────────────────

with submit_tab:
    if "last_result" in st.session_state:
        show_decision_result(st.session_state["last_result"])
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    submission_mode = st.radio(
        "Submission mode",
        ["Use a sample action", "Enter action details"],
        horizontal=True,
    )

    if submission_mode == "Use a sample action":
        with st.form("sample_action_form"):
            sample_name = st.selectbox(
                "Select a sample action",
                [
                    "Routine PKR transfer (approved)",
                    "Production cleanup command (warning)",
                    "High-risk transfer (escalated)",
                    "Email containing a CNIC (escalated)",
                    "International high-risk transfer (blocked)",
                ],
            )
            submitted = st.form_submit_button("🚀  Evaluate sample action", use_container_width=True)
        if submitted:
            submit_action(build_sample_action(sample_name))

    else:
        action_type = st.selectbox(
            "Action type",
            ACTION_TYPES,
            format_func=lambda t: t.replace("_", " ").title(),
        )

        if action_type == "transfer_money":
            with st.form("transfer_action_form"):
                col_a, col_b = st.columns(2)
                amount = col_a.number_input("Amount", min_value=0.0, step=1000.0)
                currency = col_b.text_input("Currency", value="PKR")
                recipient = st.text_input("Recipient")
                description = st.text_area("Description", height=100)
                submitted = st.form_submit_button("🚀  Evaluate transfer", use_container_width=True)
            if submitted:
                submit_action(create_transfer_money_action(amount, currency, recipient, description))

        elif action_type == "send_email":
            with st.form("email_action_form"):
                col_a, col_b = st.columns(2)
                recipient = col_a.text_input("Recipient email")
                subject = col_b.text_input("Subject")
                body = st.text_area("Email body", height=120)
                has_attachment = st.checkbox("Has attachment")
                attachment_name = st.text_input("Attachment name", disabled=not has_attachment)
                submitted = st.form_submit_button("🚀  Evaluate email", use_container_width=True)
            if submitted:
                submit_action(create_send_email_action(recipient, subject, body, has_attachment, attachment_name))

        else:
            with st.form("code_action_form"):
                code = st.text_area("Code", height=140)
                col_a, col_b = st.columns(2)
                environment = col_a.selectbox("Environment", ["development", "staging", "production"])
                language = col_b.text_input("Language", value="Python")
                submitted = st.form_submit_button("🚀  Evaluate code", use_container_width=True)
            if submitted:
                submit_action(create_execute_code_action(code, environment, language))
