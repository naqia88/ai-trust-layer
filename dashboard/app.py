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

# ── Custom CSS - Clean Minimalist Design ────────────────────────────────────

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
        background: #f0f4f8;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: none !important;
        box-shadow: 2px 0 20px rgba(0, 0, 0, 0.05);
        padding-top: 30px !important;
    }

    .sidebar-header {
        padding: 0 24px 24px 24px;
        border-bottom: 1px solid #eef2f6;
        margin-bottom: 24px;
    }
    .sidebar-header .logo {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .sidebar-header .logo-icon {
        font-size: 32px;
    }
    .sidebar-header .logo-text {
        font-size: 20px;
        font-weight: 800;
        color: #1a2332;
        letter-spacing: -0.5px;
    }
    .sidebar-header .logo-text span {
        color: #4f7cff;
    }
    .sidebar-header .subtitle {
        font-size: 12px;
        color: #8a9bb5;
        margin-top: 4px;
        padding-left: 44px;
    }

    .sidebar-user {
        padding: 16px 20px;
        background: #f8faff;
        border-radius: 12px;
        margin: 0 16px 20px 16px;
        display: flex;
        align-items: center;
        gap: 14px;
        border: 1px solid #eef2f6;
    }
    .sidebar-user .avatar {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: linear-gradient(135deg, #4f7cff, #6c5ce7);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        font-size: 16px;
        flex-shrink: 0;
    }
    .sidebar-user .user-info .name {
        font-size: 14px;
        font-weight: 600;
        color: #1a2332;
    }
    .sidebar-user .user-info .role {
        font-size: 12px;
        color: #8a9bb5;
    }

    .nav-section {
        padding: 0 16px;
    }
    .nav-section .nav-label {
        font-size: 11px;
        font-weight: 600;
        color: #8a9bb5;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding: 0 8px 8px 8px;
    }
    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        border-radius: 10px;
        color: #4a5a72;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.15s ease;
        cursor: pointer;
        margin: 2px 0;
        text-decoration: none;
    }
    .nav-item:hover {
        background: #f0f4ff;
        color: #1a2332;
    }
    .nav-item.active {
        background: #4f7cff;
        color: #ffffff;
        box-shadow: 0 4px 12px rgba(79, 124, 255, 0.25);
    }
    .nav-item .icon {
        font-size: 18px;
        width: 24px;
        text-align: center;
    }
    .nav-item .badge {
        margin-left: auto;
        background: #ff6b6b;
        color: #fff;
        font-size: 11px;
        padding: 1px 10px;
        border-radius: 20px;
        font-weight: 600;
    }

    .sidebar-footer {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 20px 24px;
        border-top: 1px solid #eef2f6;
        font-size: 12px;
        color: #8a9bb5;
        text-align: center;
    }

    /* Header */
    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0 24px 0;
        border-bottom: 1px solid #eef2f6;
        margin-bottom: 28px;
    }
    .page-header .header-left h1 {
        font-size: 26px;
        font-weight: 700;
        color: #1a2332;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .page-header .header-left .breadcrumb {
        font-size: 13px;
        color: #8a9bb5;
        margin-top: 4px;
    }
    .page-header .header-left .breadcrumb span {
        color: #4f7cff;
    }
    .page-header .header-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .header-right .status-badge {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: #e8f5e9;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        color: #2e7d32;
    }
    .header-right .status-badge .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #22c55e;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    /* Metric Cards */
    [data-testid="metric-container"] {
        background: #ffffff !important;
        border: 1px solid #eef2f6 !important;
        border-radius: 12px !important;
        padding: 18px 20px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    }
    [data-testid="metric-container"]:hover {
        border-color: #d0d9e6 !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06) !important;
        transform: translateY(-2px);
    }
    [data-testid="metric-container"] label {
        color: #8a9bb5 !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #1a2332 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #ffffff;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #eef2f6;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #4a5a72;
        font-weight: 500;
        font-size: 14px;
        padding: 8px 24px;
        transition: all 0.15s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #1a2332;
        background: #f0f4ff;
    }
    .stTabs [aria-selected="true"] {
        background: #4f7cff !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(79, 124, 255, 0.25);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: #ffffff !important;
        border: 1px solid #eef2f6 !important;
        border-radius: 10px !important;
        color: #1a2332 !important;
        font-weight: 500 !important;
        padding: 12px 16px !important;
        transition: all 0.15s;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    }
    .streamlit-expanderHeader:hover {
        border-color: #d0d9e6 !important;
        background: #fafcff !important;
    }
    .streamlit-expanderContent {
        background: #ffffff !important;
        border: 1px solid #eef2f6 !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 16px !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.15s !important;
        border: 1px solid #d0d9e6 !important;
        background: #ffffff !important;
        color: #1a2332 !important;
        padding: 8px 20px !important;
        height: auto !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
    }
    .stButton > button:hover {
        background: #f0f4ff !important;
        border-color: #4f7cff !important;
        color: #4f7cff !important;
        box-shadow: 0 2px 8px rgba(79, 124, 255, 0.1) !important;
        transform: translateY(-1px);
    }

    /* Form Inputs */
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background: #ffffff !important;
        border: 1px solid #d0d9e6 !important;
        border-radius: 8px !important;
        color: #1a2332 !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        transition: all 0.15s;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
        border-color: #4f7cff !important;
        box-shadow: 0 0 0 3px rgba(79, 124, 255, 0.08) !important;
    }
    .stSelectbox > div > div {
        background: #ffffff !important;
        border: 1px solid #d0d9e6 !important;
        border-radius: 8px !important;
        color: #1a2332 !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
    }
    .stSelectbox > div > div:hover {
        border-color: #4f7cff !important;
    }

    /* Dataframe */
    .stDataFrame {
        border: 1px solid #eef2f6;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }
    .stDataFrame thead tr th {
        background: #f8faff !important;
        color: #4a5a72 !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 16px !important;
        border-bottom: 1px solid #eef2f6 !important;
    }
    .stDataFrame tbody tr td {
        color: #1a2332 !important;
        padding: 10px 16px !important;
        border-bottom: 1px solid #f0f4f8 !important;
        font-size: 14px;
    }
    .stDataFrame tbody tr:hover td {
        background: #f8faff !important;
    }

    /* Alerts */
    .stAlert {
        border-radius: 10px !important;
        border: none !important;
        padding: 14px 18px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    }
    .stAlert.info {
        background: #eef4ff !important;
        border-left: 3px solid #4f7cff !important;
    }
    .stAlert.success {
        background: #e8f5e9 !important;
        border-left: 3px solid #22c55e !important;
    }
    .stAlert.warning {
        background: #fff8e1 !important;
        border-left: 3px solid #f59e0b !important;
    }
    .stAlert.error {
        background: #fce4ec !important;
        border-left: 3px solid #ef4444 !important;
    }

    /* Band Pills */
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
        border: 1px solid #eef2f6;
        background: #ffffff;
    }

    /* Score Bar */
    .score-bar-wrap {
        background: #f0f4f8;
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
        background: #eef2f6;
        margin: 24px 0;
    }

    @media (max-width: 768px) {
        .page-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
        }
        .page-header .header-left h1 {
            font-size: 22px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 6px 14px;
            font-size: 13px;
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
          <span style="color:#4a5a72;font-size:13px;font-weight:500;width:80px;flex-shrink:0;">{label}</span>
          <div class="score-bar-wrap" style="flex:1;">
            <div class="score-bar-fill" style="width:{score}%;background:{color};"></div>
          </div>
          <span style="color:#1a2332;font-size:14px;font-weight:600;width:32px;text-align:right;flex-shrink:0;">{score}</span>
        </div>
    """, unsafe_allow_html=True)


def show_decision_result(result):
    decision = result["decision"]
    color = DECISION_COLORS[decision]
    icon = DECISION_ICONS[decision]
    label = decision.replace("_", " ").title()

    st.markdown(f"""
        <div style="background:#ffffff;border:1px solid #eef2f6;
                    border-left:4px solid {color};border-radius:10px;padding:16px 20px;margin:12px 0;
                    box-shadow:0 1px 3px rgba(0,0,0,0.02);">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <span style="font-size:24px;">{icon}</span>
            <span style="color:{color};font-size:18px;font-weight:700;">{label}</span>
            <span style="color:#8a9bb5;font-size:14px;margin-left:auto;">
              Final score: <b style="color:#1a2332;font-size:16px;">{result['final_score']}</b>
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
                <span class="logo-icon">🛡️</span>
                <span class="logo-text">Trust<span>Layer</span></span>
            </div>
            <div class="subtitle">AI Action Governance</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="sidebar-user">
            <div class="avatar">JD</div>
            <div class="user-info">
                <div class="name">John Doe</div>
                <div class="role">Admin · johndoe@company.com</div>
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
        <div style="height:20px;"></div>
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
    st.markdown("### Filters")
    
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
    
    st.markdown("""
        <div class="sidebar-footer">
            Version 2.0 · © 2024 TrustLayer
        </div>
    """, unsafe_allow_html=True)

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
    <div class="page-header">
        <div class="header-left">
            <h1>Dashboard</h1>
            <div class="breadcrumb">Home / <span>Overview</span></div>
        </div>
        <div class="header-right">
            <div class="status-badge">
                <span class="dot"></span> System Online
            </div>
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
    st.metric("Approved", decision_counts["approved"])
with c5:
    st.metric("Warnings", decision_counts["approved_with_warning"])
with c6:
    st.metric("Escalated", decision_counts["escalated"])
with c7:
    st.metric("Blocked", decision_counts["blocked"])

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
            text=f"<b>{len(all_actions)}</b><br><span style='font-size:11px;color:#8a9bb5;'>actions</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=22, color="#1a2332", family="Inter"),
        )
        fig_donut.update_layout(
            title=dict(text="Decision Breakdown", font=dict(color="#1a2332", size=16, weight=600)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#4a5a72", family="Inter"),
            legend=dict(font=dict(color="#4a5a72"), bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=-0.12),
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
                font=dict(color="#4a5a72", family="Inter"),
                title=dict(font=dict(color="#1a2332", size=16, weight=600)),
                legend=dict(font=dict(color="#4a5a72"), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(gridcolor="#eef2f6", tickfont=dict(color="#4a5a72")),
                yaxis=dict(gridcolor="#eef2f6", tickfont=dict(color="#4a5a72"), range=[0, 100]),
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

        st.markdown(f"<p style='color:#8a9bb5;font-size:13px;margin-top:6px;'>"
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
                        f"<div style='margin-top:10px;padding:10px;background:#f8faff;"
                        f"border-radius:8px;border:1px solid #eef2f6;'>"
                        f"<span style='color:#4a5a72;font-size:13px;'>"
                        f"Resolved by <b style='color:#1a2332;'>{action['resolved_by']}</b> · "
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
          <p style="color:#22c55e;font-weight:600;font-size:18px;margin:8px 0;">All clear</p>
          <p style="color:#8a9bb5;font-size:14px;">No open escalations require attention.</p>
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
        for a in resolved[:5]:  # Show last 5 resolved
            color = "#22c55e" if a["resolution"] == "approved" else "#ef4444"
            st.markdown(
                f"<div style='padding:8px 14px;margin:4px 0;background:#ffffff;"
                f"border-radius:8px;border:1px solid #eef2f6;border-left:3px solid {color};'>"
                f"<span style='color:#1a2332;font-size:14px;'>"
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
