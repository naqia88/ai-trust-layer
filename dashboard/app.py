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

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* ===== IMPORTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ===== RESET & BASE ===== */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: #080d1a;
    }

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0d1526;
    }
    ::-webkit-scrollbar-thumb {
        background: #1e3a6e;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #2e4a7a;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090f1f 0%, #0d1526 100%);
        border-right: 1px solid rgba(30, 45, 74, 0.6);
        padding-top: 20px;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #8aa9d9;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 700;
        padding: 0 0 8px 0;
        border-bottom: 1px solid rgba(30, 45, 74, 0.4);
    }

    /* Sidebar user profile card */
    .sidebar-profile {
        background: linear-gradient(135deg, #0d1a33 0%, #13203a 100%);
        border: 1px solid #1e2d4a;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 24px;
        text-align: center;
    }
    .sidebar-profile .avatar {
        width: 72px;
        height: 72px;
        border-radius: 50%;
        background: linear-gradient(135deg, #1e3a6e, #2e4a7a);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px;
        font-size: 28px;
        font-weight: 700;
        color: #e8f0fe;
        border: 2px solid #2e4a7a;
        box-shadow: 0 4px 20px rgba(30, 58, 110, 0.4);
    }
    .sidebar-profile .name {
        color: #e8f0fe;
        font-weight: 700;
        font-size: 1rem;
        margin: 0;
    }
    .sidebar-profile .email {
        color: #7a9cc4;
        font-size: 0.78rem;
        margin: 2px 0 0 0;
    }

    /* Sidebar nav items */
    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        border-radius: 10px;
        color: #7a9cc4;
        text-decoration: none;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        cursor: pointer;
        margin: 2px 0;
    }
    .nav-item:hover {
        background: rgba(30, 58, 110, 0.4);
        color: #e8f0fe;
    }
    .nav-item.active {
        background: linear-gradient(135deg, #1e3a6e, #1a3370);
        color: #e8f0fe;
        border: 1px solid #2e4a7a;
    }
    .nav-item .icon {
        font-size: 1.2rem;
        width: 24px;
        text-align: center;
    }
    .nav-item .badge {
        margin-left: auto;
        background: #ef4444;
        color: #fff;
        font-size: 0.7rem;
        padding: 1px 8px;
        border-radius: 20px;
        font-weight: 700;
    }

    /* ===== MAIN HEADER ===== */
    .main-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 0 24px 0;
        border-bottom: 1px solid rgba(30, 45, 74, 0.4);
        margin-bottom: 28px;
    }
    .main-header .brand {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .main-header .brand .logo {
        font-size: 2.4rem;
        line-height: 1;
    }
    .main-header .brand h1 {
        font-size: 1.5rem;
        font-weight: 800;
        color: #e8f0fe;
        margin: 0;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #e8f0fe 60%, #7a9cc4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .main-header .brand .subtitle {
        font-size: 0.78rem;
        color: #7a9cc4;
        font-weight: 400;
        -webkit-text-fill-color: #7a9cc4;
    }
    .main-header .header-actions {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .header-actions .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #22c55e;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
    .header-actions .status-text {
        color: #7a9cc4;
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* ===== STAT CARDS ===== */
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 14px;
        margin-bottom: 24px;
    }
    .stat-card {
        background: linear-gradient(145deg, #0d1a33, #111d38);
        border: 1px solid #1e2d4a;
        border-radius: 14px;
        padding: 16px 18px;
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #2e4a7a, transparent);
        opacity: 0;
        transition: opacity 0.3s;
    }
    .stat-card:hover {
        border-color: #2e4a7a;
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .stat-card:hover::before {
        opacity: 1;
    }
    .stat-card .stat-label {
        color: #7a9cc4;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }
    .stat-card .stat-value {
        color: #e8f0fe;
        font-size: 1.6rem;
        font-weight: 800;
        margin: 4px 0 2px;
        line-height: 1.2;
    }
    .stat-card .stat-change {
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 20px;
        display: inline-block;
    }
    .stat-card .stat-change.positive {
        color: #22c55e;
        background: rgba(34, 197, 94, 0.12);
    }
    .stat-card .stat-change.negative {
        color: #ef4444;
        background: rgba(239, 68, 68, 0.12);
    }
    .stat-card .stat-icon {
        position: absolute;
        right: 14px;
        top: 14px;
        font-size: 1.4rem;
        opacity: 0.3;
    }

    /* ===== METRIC CONTAINER OVERRIDE ===== */
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, #0d1a33, #111d38);
        border: 1px solid #1e2d4a;
        border-radius: 14px;
        padding: 16px 18px !important;
        transition: all 0.25s ease;
    }
    [data-testid="metric-container"]:hover {
        border-color: #2e4a7a;
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    [data-testid="metric-container"] label {
        color: #7a9cc4 !important;
        font-size: 0.68rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #e8f0fe !important;
        font-size: 1.6rem !important;
        font-weight: 800 !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricDelta"] {
        color: #7a9cc4 !important;
        font-size: 0.78rem !important;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: #0d1526;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #1e2d4a;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 9px;
        color: #7a9cc4;
        font-weight: 500;
        font-size: 0.85rem;
        padding: 8px 22px;
        transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #e8f0fe;
        background: rgba(30, 58, 110, 0.2);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1e3a6e, #1a3370) !important;
        color: #e8f0fe !important;
        box-shadow: 0 2px 12px rgba(30, 58, 110, 0.3);
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        background: linear-gradient(145deg, #0d1a33, #111d38) !important;
        border: 1px solid #1e2d4a !important;
        border-radius: 10px !important;
        color: #c8d8f0 !important;
        font-weight: 500 !important;
        padding: 12px 16px !important;
        transition: all 0.2s;
    }
    .streamlit-expanderHeader:hover {
        border-color: #2e4a7a !important;
    }
    .streamlit-expanderContent {
        background: #0a1528 !important;
        border: 1px solid #1e2d4a !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 16px !important;
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.25s !important;
        border: 1px solid #1e2d4a !important;
        background: linear-gradient(145deg, #112040, #0d1a33) !important;
        color: #c8d8f0 !important;
        padding: 8px 20px !important;
        height: auto !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1e3a6e, #1a3370) !important;
        border-color: #2e4a7a !important;
        color: #ffffff !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(30, 58, 110, 0.3);
    }
    .stButton > button:active {
        transform: translateY(0px);
    }
    .stButton > button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    /* ===== FORM INPUTS ===== */
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background: #0d1a33 !important;
        border: 1px solid #1e2d4a !important;
        border-radius: 10px !important;
        color: #e8f0fe !important;
        padding: 10px 14px !important;
        font-size: 0.9rem !important;
        transition: border-color 0.2s;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
        border-color: #2e4a7a !important;
        box-shadow: 0 0 0 3px rgba(30, 58, 110, 0.15);
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #4a6a8a !important;
    }
    .stSelectbox > div > div {
        background: #0d1a33 !important;
        border: 1px solid #1e2d4a !important;
        border-radius: 10px !important;
        color: #e8f0fe !important;
    }
    .stSelectbox > div > div:hover {
        border-color: #2e4a7a !important;
    }

    /* ===== DATAFRAME ===== */
    .stDataFrame {
        border: 1px solid #1e2d4a;
        border-radius: 12px;
        overflow: hidden;
    }
    .stDataFrame [data-testid="stDataFrame"] {
        background: #0a1528;
    }
    .stDataFrame thead tr th {
        background: #0d1a33 !important;
        color: #7a9cc4 !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 10px 12px !important;
        border-bottom: 1px solid #1e2d4a !important;
    }
    .stDataFrame tbody tr td {
        color: #c8d8f0 !important;
        padding: 8px 12px !important;
        border-bottom: 1px solid rgba(30, 45, 74, 0.3) !important;
    }
    .stDataFrame tbody tr:hover td {
        background: rgba(30, 58, 110, 0.15) !important;
    }

    /* ===== ALERTS ===== */
    .stAlert {
        border-radius: 10px !important;
        border: none !important;
        padding: 14px 18px !important;
    }
    .stAlert > div {
        color: #e8f0fe !important;
    }
    .stAlert.info {
        background: rgba(30, 58, 110, 0.25) !important;
        border-left: 3px solid #2e4a7a !important;
    }
    .stAlert.success {
        background: rgba(34, 197, 94, 0.12) !important;
        border-left: 3px solid #22c55e !important;
    }
    .stAlert.warning {
        background: rgba(245, 158, 11, 0.12) !important;
        border-left: 3px solid #f59e0b !important;
    }
    .stAlert.error {
        background: rgba(239, 68, 68, 0.12) !important;
        border-left: 3px solid #ef4444 !important;
    }

    /* ===== BAND PILLS ===== */
    .band-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid transparent;
        letter-spacing: 0.02em;
    }

    /* ===== RISK BADGE ===== */
    .risk-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }

    /* ===== SCORE BAR ===== */
    .score-bar-wrap {
        background: #0d1a33;
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

    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        .main-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
        }
        .stat-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        .stTabs [data-baseweb="tab"] {
            padding: 6px 14px;
            font-size: 0.78rem;
        }
        .stat-card .stat-value {
            font-size: 1.2rem;
        }
    }

    /* ===== SPECIAL ===== */
    .divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #1e2d4a, transparent);
        margin: 20px 0;
    }
    .section-title {
        color: #c8d8f0;
        font-size: 0.95rem;
        font-weight: 600;
        margin: 16px 0 12px 0;
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
          <span style="color:#7a9cc4;font-size:0.75rem;font-weight:500;width:72px;flex-shrink:0;">{label}</span>
          <div class="score-bar-wrap" style="flex:1;">
            <div class="score-bar-fill" style="width:{score}%;background:{color};"></div>
          </div>
          <span style="color:#e8f0fe;font-size:0.78rem;font-weight:700;width:28px;text-align:right;flex-shrink:0;">{score}</span>
        </div>
    """, unsafe_allow_html=True)


def show_decision_result(result):
    decision = result["decision"]
    color = DECISION_COLORS[decision]
    icon = DECISION_ICONS[decision]
    label = decision.replace("_", " ").title()

    st.markdown(f"""
        <div style="background:linear-gradient(145deg,#0d1a33,#111d38);border:1px solid {color}44;
                    border-left:4px solid {color};border-radius:12px;padding:16px 20px;margin:12px 0;">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <span style="font-size:1.6rem;">{icon}</span>
            <span style="color:{color};font-size:1.1rem;font-weight:700;">{label}</span>
            <span style="color:#7a9cc4;font-size:0.85rem;margin-left:auto;">
              Final score: <b style="color:#e8f0fe;font-size:1rem;">{result['final_score']}</b>
            </span>
          </div>
        </div>
    """, unsafe_allow_html=True)

    if result["reasons"]:
        st.markdown("<div style='margin-top:6px;'>", unsafe_allow_html=True)
        for reason in result["reasons"]:
            st.markdown(f"<span style='color:#f59e0b;font-size:0.85rem;'>⚡ {reason}</span><br>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def submit_action(action):
    st.session_state["last_result"] = intercept_action(action)
    st.rerun()

# ── Init ──────────────────────────────────────────────────────────────────────

init_db()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # Profile Card
    st.markdown("""
        <div class="sidebar-profile">
            <div class="avatar">👨‍💻</div>
            <p class="name">Admin User</p>
            <p class="email">admin@company.com</p>
        </div>
    """, unsafe_allow_html=True)

    # Navigation
    st.markdown("### Navigation")
    
    nav_items = [
        ("📊", "Dashboard", True),
        ("📋", "Audit Log", False),
        ("🔺", "Review Queue", False),
        ("🧪", "Test Action", False),
        ("⚙️", "Settings", False),
    ]
    
    for icon, label, active in nav_items:
        active_class = "active" if active else ""
        st.markdown(f"""
            <div class="nav-item {active_class}">
                <span class="icon">{icon}</span>
                {label}
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🎛️ Filters")
    
    selected_decisions = st.multiselect(
        "Decision status",
        DECISIONS,
        default=DECISIONS,
        format_func=lambda d: f"{DECISION_ICONS[d]}  {d.replace('_', ' ').title()}",
    )
    selected_action_types = st.multiselect(
        "Action type",
        ACTION_TYPES,
        default=ACTION_TYPES,
        format_func=lambda t: t.replace("_", " ").title(),
    )
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# ── MAIN HEADER ──────────────────────────────────────────────────────────────

st.markdown("""
    <div class="main-header">
        <div class="brand">
            <span class="logo">🛡️</span>
            <div>
                <h1>AI Trust Layer</h1>
                <span class="subtitle">Real-time governance for AI actions</span>
            </div>
        </div>
        <div class="header-actions">
            <span class="status-text">
                <span class="status-dot"></span> System Online
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── Decision Band Pills ──────────────────────────────────────────────────────

st.markdown(f"""
    <div style="margin-bottom:20px;display:flex;flex-wrap:wrap;gap:4px;">
        <span class="band-pill" style="background:#22c55e18;color:#22c55e;border-color:#22c55e33;">✅ 0–{AUTO_APPROVE} Approved</span>
        <span class="band-pill" style="background:#f59e0b18;color:#f59e0b;border-color:#f59e0b33;">⚠️ {AUTO_APPROVE+1}–{FLAG_FOR_REVIEW} Warning</span>
        <span class="band-pill" style="background:#f9731618;color:#f97316;border-color:#f9731633;">🔺 {FLAG_FOR_REVIEW+1}–{AUTO_BLOCK-1} Escalated</span>
        <span class="band-pill" style="background:#ef444418;color:#ef4444;border-color:#ef444433;">🚫 {AUTO_BLOCK}–100 Blocked</span>
    </div>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────

all_actions = load_actions()
filtered_actions = filter_actions(all_actions, selected_decisions, selected_action_types)
decision_counts = count_decisions(all_actions)
open_escalations = get_open_escalations(all_actions)
average_score = (
    sum(a["final_score"] for a in all_actions) / len(all_actions) if all_actions else 0
)

# ── Metrics Row ──────────────────────────────────────────────────────────────

st.markdown('<div class="stat-grid">', unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
with c1:
    st.metric("Total Actions", len(all_actions), delta=None)
with c2:
    st.metric("Open Escalations", len(open_escalations), 
              delta=f"+{len(open_escalations)}" if open_escalations else "0")
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

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Charts Row ────────────────────────────────────────────────────────────────

if all_actions:
    chart_col1, chart_col2 = st.columns([1, 2])

    with chart_col1:
        labels = [d.replace("_", " ").title() for d in DECISIONS]
        values = [decision_counts[d] for d in DECISIONS]
        colors = [DECISION_COLORS[d] for d in DECISIONS]

        fig_donut = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.68,
            marker=dict(colors=colors, line=dict(color="#080d1a", width=3)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
        ))
        fig_donut.add_annotation(
            text=f"<b>{len(all_actions)}</b><br><span style='font-size:9px;color:#7a9cc4;'>actions</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="#e8f0fe", family="Inter"),
        )
        fig_donut.update_layout(
            title=dict(text="Decision Breakdown", font=dict(color="#c8d8f0", size=14, weight=600)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#7a9cc4", family="Inter"),
            legend=dict(font=dict(color="#c8d8f0"), bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=-0.15),
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
                font=dict(color="#7a9cc4", family="Inter"),
                title=dict(font=dict(color="#c8d8f0", size=14, weight=600)),
                legend=dict(font=dict(color="#c8d8f0"), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(gridcolor="#1e2d4a", tickfont=dict(color="#c8d8f0")),
                yaxis=dict(gridcolor="#1e2d4a", tickfont=dict(color="#c8d8f0"), range=[0, 100]),
                margin=dict(t=40, b=10, l=10, r=10),
                height=300,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────

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
