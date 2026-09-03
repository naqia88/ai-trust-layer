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
  /* Import font */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  /* Main background */
  .stApp {
    background-color: #0a0f1e;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background-color: #0d1526;
    border-right: 1px solid #1e2d4a;
  }

  /* Metric cards */
  [data-testid="metric-container"] {
    background: linear-gradient(135deg, #0d1a33 0%, #111d38 100%);
    border: 1px solid #1e2d4a;
    border-radius: 12px;
    padding: 20px !important;
    transition: border-color 0.2s;
  }
  [data-testid="metric-container"]:hover {
    border-color: #2e4a7a;
  }
  [data-testid="metric-container"] label {
    color: #7a9cc4 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e8f0fe !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    background-color: #0d1526;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #1e2d4a;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #7a9cc4;
    font-weight: 500;
    font-size: 0.875rem;
    padding: 8px 20px;
  }
  .stTabs [aria-selected="true"] {
    background-color: #1e3a6e !important;
    color: #e8f0fe !important;
  }

  /* Expander */
  .streamlit-expanderHeader {
    background-color: #0d1a33 !important;
    border: 1px solid #1e2d4a !important;
    border-radius: 8px !important;
    color: #c8d8f0 !important;
    font-weight: 500 !important;
  }
  .streamlit-expanderContent {
    background-color: #0a1528 !important;
    border: 1px solid #1e2d4a !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
  }

  /* Buttons */
  .stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    transition: all 0.2s !important;
    border: 1px solid #1e2d4a !important;
    background-color: #112040 !important;
    color: #c8d8f0 !important;
  }
  .stButton > button:hover {
    background-color: #1e3a6e !important;
    border-color: #2e4a7a !important;
    color: #ffffff !important;
  }

  /* Form inputs */
  .stTextInput input, .stTextArea textarea, .stNumberInput input {
    background-color: #0d1a33 !important;
    border: 1px solid #1e2d4a !important;
    border-radius: 8px !important;
    color: #c8d8f0 !important;
  }
  .stSelectbox > div > div {
    background-color: #0d1a33 !important;
    border: 1px solid #1e2d4a !important;
    border-radius: 8px !important;
    color: #c8d8f0 !important;
  }

  /* Dataframe */
  .stDataFrame {
    border: 1px solid #1e2d4a;
    border-radius: 10px;
    overflow: hidden;
  }

  /* Info / warning / success / error alerts */
  .stAlert {
    border-radius: 8px !important;
    border: none !important;
  }

  /* Title */
  h1 { color: #e8f0fe !important; font-weight: 700 !important; }
  h2, h3 { color: #c8d8f0 !important; font-weight: 600 !important; }

  /* Risk badge */
  .risk-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.03em;
  }

  /* Score bar */
  .score-bar-wrap {
    background: #0d1a33;
    border-radius: 999px;
    height: 6px;
    width: 100%;
  }
  .score-bar-fill {
    height: 6px;
    border-radius: 999px;
  }

  /* Band info pill */
  .band-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 500;
    margin-right: 6px;
    margin-bottom: 4px;
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
          <span style="color:#7a9cc4;font-size:0.78rem;width:60px;">{label}</span>
          <div class="score-bar-wrap" style="flex:1;">
            <div class="score-bar-fill" style="width:{score}%;background:{color};"></div>
          </div>
          <span style="color:#e8f0fe;font-size:0.8rem;font-weight:600;width:28px;text-align:right;">{score}</span>
        </div>
    """, unsafe_allow_html=True)


def show_decision_result(result):
    decision = result["decision"]
    color = DECISION_COLORS[decision]
    icon = DECISION_ICONS[decision]
    label = decision.replace("_", " ").title()

    st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0d1a33,#111d38);border:1px solid {color}44;
                    border-left:4px solid {color};border-radius:10px;padding:16px 20px;margin:12px 0;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span style="font-size:1.4rem;">{icon}</span>
            <span style="color:{color};font-size:1.1rem;font-weight:700;">{label}</span>
            <span style="color:#7a9cc4;font-size:0.875rem;margin-left:auto;">
              Final score: <b style="color:#e8f0fe;">{result['final_score']}</b>
            </span>
          </div>
        </div>
    """, unsafe_allow_html=True)

    if result["reasons"]:
        st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
        for reason in result["reasons"]:
            st.markdown(f"<span style='color:#f59e0b;font-size:0.85rem;'>⚡ {reason}</span><br>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def submit_action(action):
    st.session_state["last_result"] = intercept_action(action)
    st.rerun()

# ── Init ──────────────────────────────────────────────────────────────────────

init_db()

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div style="display:flex;align-items:center;gap:14px;padding:8px 0 20px;">
  <span style="font-size:2.2rem;">🛡️</span>
  <div>
    <h1 style="margin:0;font-size:1.8rem;">AI Trust Layer</h1>
    <p style="margin:0;color:#7a9cc4;font-size:0.9rem;">Review and govern AI-initiated actions in real time</p>
  </div>
</div>
""", unsafe_allow_html=True)

# Decision band pills
st.markdown(f"""
<div style="margin-bottom:24px;">
  <span class="band-pill" style="background:#22c55e18;color:#22c55e;">✅ 0–{AUTO_APPROVE} Approved</span>
  <span class="band-pill" style="background:#f59e0b18;color:#f59e0b;">⚠️ {AUTO_APPROVE+1}–{FLAG_FOR_REVIEW} Warning</span>
  <span class="band-pill" style="background:#f9731618;color:#f97316;">🔺 {FLAG_FOR_REVIEW+1}–{AUTO_BLOCK-1} Escalated</span>
  <span class="band-pill" style="background:#ef444418;color:#ef4444;">🚫 {AUTO_BLOCK}–100 Blocked</span>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
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
    st.markdown("---")
    if st.button("🔄 Refresh data", use_container_width=True):
        st.rerun()

# ── Data ──────────────────────────────────────────────────────────────────────

all_actions = load_actions()
filtered_actions = filter_actions(all_actions, selected_decisions, selected_action_types)
decision_counts = count_decisions(all_actions)
open_escalations = get_open_escalations(all_actions)
average_score = (
    sum(a["final_score"] for a in all_actions) / len(all_actions) if all_actions else 0
)

# ── Metrics row ───────────────────────────────────────────────────────────────

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
c1.metric("Total Actions", len(all_actions))
c2.metric("Open Escalations", len(open_escalations))
c3.metric("Avg Risk Score", f"{average_score:.1f}")
c4.metric("✅ Approved", decision_counts["approved"])
c5.metric("⚠️ Warnings", decision_counts["approved_with_warning"])
c6.metric("🔺 Escalated", decision_counts["escalated"])
c7.metric("🚫 Blocked", decision_counts["blocked"])

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

# ── Charts row ────────────────────────────────────────────────────────────────

if all_actions:
    chart_col1, chart_col2 = st.columns([1, 2])

    with chart_col1:
        # Donut chart — decision breakdown
        labels = [d.replace("_", " ").title() for d in DECISIONS]
        values = [decision_counts[d] for d in DECISIONS]
        colors = [DECISION_COLORS[d] for d in DECISIONS]

        fig_donut = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.65,
            marker=dict(colors=colors, line=dict(color="#0a0f1e", width=2)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
        ))
        fig_donut.add_annotation(
            text=f"<b>{len(all_actions)}</b><br><span style='font-size:10px'>actions</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, color="#e8f0fe"),
        )
        fig_donut.update_layout(
            title=dict(text="Decision Breakdown", font=dict(color="#c8d8f0", size=14)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#7a9cc4"),
            legend=dict(font=dict(color="#c8d8f0"), bgcolor="rgba(0,0,0,0)"),
            margin=dict(t=40, b=10, l=10, r=10),
            height=280,
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with chart_col2:
        # Bar chart — score distribution by action type
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
                font=dict(color="#7a9cc4"),
                title=dict(font=dict(color="#c8d8f0", size=14)),
                legend=dict(font=dict(color="#c8d8f0"), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(gridcolor="#1e2d4a", tickfont=dict(color="#c8d8f0")),
                yaxis=dict(gridcolor="#1e2d4a", tickfont=dict(color="#c8d8f0"), range=[0, 100]),
                margin=dict(t=40, b=10, l=10, r=10),
                height=280,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────

audit_tab, review_tab, submit_tab = st.tabs([
    "📋  Audit Log",
    f"🔺  Review Queue  {'  🔴 ' + str(len(open_escalations)) if open_escalations else ''}",
    "🧪  Submit Test Action",
])

# ── Audit log ─────────────────────────────────────────────────────────────────

with audit_tab:
    if not filtered_actions:
        st.info("No audit records match the current filters.")
    else:
        # Coloured table
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
                "Financial": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
                "Privacy": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
                "Policy": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
            },
        )

        st.markdown(f"<p style='color:#7a9cc4;font-size:0.82rem;margin-top:6px;'>"
                    f"Showing {len(filtered_actions)} of {len(all_actions)} actions</p>",
                    unsafe_allow_html=True)

        st.markdown("### Action details")
        for action in filtered_actions:
            dec = action["decision"]
            color = DECISION_COLORS[dec]
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
                        st.markdown(f"<span style='color:#f59e0b;font-size:0.85rem;'>⚡ {r}</span>",
                                    unsafe_allow_html=True)

                if action["resolved_by"]:
                    st.markdown(
                        f"<div style='margin-top:10px;padding:10px;background:#0d1a33;"
                        f"border-radius:8px;border:1px solid #1e2d4a;'>"
                        f"<span style='color:#7a9cc4;font-size:0.82rem;'>"
                        f"Resolved by <b style='color:#c8d8f0;'>{action['resolved_by']}</b> · "
                        f"{action['resolution']} · {action['resolution_time']}"
                        f"</span></div>",
                        unsafe_allow_html=True,
                    )

# ── Review queue ──────────────────────────────────────────────────────────────

with review_tab:
    if "review_message" in st.session_state:
        st.success(st.session_state.pop("review_message"))

    if not open_escalations:
        st.markdown("""
        <div style="text-align:center;padding:48px 0;">
          <div style="font-size:3rem;">✅</div>
          <p style="color:#22c55e;font-weight:600;font-size:1.1rem;margin:8px 0;">All clear</p>
          <p style="color:#7a9cc4;font-size:0.9rem;">No open escalations require attention.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color:#f97316;font-weight:600;'>"
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
                        st.markdown(f"<span style='color:#f59e0b;font-size:0.85rem;'>⚡ {r}</span>",
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
        for a in resolved:
            color = "#22c55e" if a["resolution"] == "approved" else "#ef4444"
            st.markdown(
                f"<div style='padding:8px 14px;margin:4px 0;background:#0d1a33;"
                f"border-radius:8px;border-left:3px solid {color};'>"
                f"<span style='color:#c8d8f0;font-size:0.85rem;'>"
                f"Action {a['id']} — <b style='color:{color};'>{a['resolution']}</b>"
                f" by {a['resolved_by']} · {a['resolution_time']}"
                f"</span></div>",
                unsafe_allow_html=True,
            )

# ── Submit test action ────────────────────────────────────────────────────────

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
