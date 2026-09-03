import html
import json
import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.chdir(PROJECT_ROOT)

import streamlit as st

from config import AUTO_APPROVE, AUTO_BLOCK, FLAG_FOR_REVIEW
from database.audit import get_actions, init_db, resolve_action
from trust.interceptor import intercept_action
from worker.agent import (
    create_execute_code_action,
    create_send_email_action,
    create_transfer_money_action,
)


DECISIONS = ["approved", "approved_with_warning", "escalated", "blocked"]
ACTION_TYPES = ["transfer_money", "send_email", "execute_code"]
NAV_ITEMS = ["Overview", "Review Queue", "Audit History", "Test Action"]
DECISION_META = {
    "approved": {
        "label": "Approved",
        "risk": "Low risk",
        "tone": "approved",
        "color": "#10b981",
    },
    "approved_with_warning": {
        "label": "Approved with warning",
        "risk": "Moderate risk",
        "tone": "warning",
        "color": "#f59e0b",
    },
    "escalated": {
        "label": "Escalated",
        "risk": "High risk",
        "tone": "escalated",
        "color": "#ef4444",
    },
    "blocked": {
        "label": "Blocked",
        "risk": "Critical risk",
        "tone": "blocked",
        "color": "#9a3412",
    },
}
ACTION_LABELS = {
    "transfer_money": "Money transfer",
    "send_email": "Email review",
    "execute_code": "Code execution",
}
SAMPLE_ACTIONS = [
    "Routine PKR transfer (approved)",
    "Production cleanup command (warning)",
    "High-risk transfer (escalated)",
    "Email containing a CNIC (escalated)",
    "International high-risk transfer (blocked)",
]


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
        action
        for action in actions
        if action["decision"] in decisions and action["action_type"] in action_types
    ]


def count_decisions(actions):
    counts = {decision: 0 for decision in DECISIONS}
    for action in actions:
        counts[action["decision"]] += 1
    return counts


def get_open_escalations(actions):
    return [
        action
        for action in actions
        if action["decision"] == "escalated" and not action["resolved_by"]
    ]


def build_sample_action(sample_name):
    if sample_name == "Routine PKR transfer (approved)":
        return create_transfer_money_action(
            50000,
            "PKR",
            "Verified Vendor",
            "Monthly office supplies invoice",
        )
    if sample_name == "Production cleanup command (warning)":
        return create_execute_code_action(
            "DROP TABLE temporary_logs;",
            "production",
            "SQL",
        )
    if sample_name == "High-risk transfer (escalated)":
        return create_transfer_money_action(
            250000,
            "PKR",
            "Unverified Vendor",
            "Please call 03001234567 before processing.",
        )
    if sample_name == "Email containing a CNIC (escalated)":
        return create_send_email_action(
            "unknown@partner.example",
            "Customer verification",
            "Customer CNIC: 35202-1234567-1",
            False,
            "",
        )
    return create_transfer_money_action(
        250000,
        "USD",
        "Unverified Vendor",
        "Customer CNIC: 35202-1234567-1",
    )


def decision_meta(decision):
    return DECISION_META.get(
        decision,
        {
            "label": decision.replace("_", " ").title(),
            "risk": "Unknown",
            "tone": "warning",
            "color": "#f59e0b",
        },
    )


def readable_action_type(action_type):
    return ACTION_LABELS.get(action_type, action_type.replace("_", " ").title())


def format_amount(amount):
    try:
        return f"{float(amount):,.0f}"
    except (TypeError, ValueError):
        return str(amount or "0")


def action_title(action):
    details = action["details"]
    if action["action_type"] == "transfer_money":
        return f"{details.get('currency', 'PKR')} {format_amount(details.get('amount'))} transfer"
    if action["action_type"] == "send_email":
        return details.get("subject") or "Email review"
    return f"{details.get('language', 'Code')} code execution"


def action_summary(action):
    details = action["details"]
    if action["action_type"] == "transfer_money":
        recipient = details.get("recipient") or "No recipient provided"
        description = details.get("description") or "No description provided"
        return f"To {recipient} · {description}"
    if action["action_type"] == "send_email":
        recipient = details.get("to") or "No recipient provided"
        return f"To {recipient}"
    environment = details.get("environment") or "No environment provided"
    return f"Running in {environment}"


def format_timestamp(timestamp):
    return timestamp.replace("T", " ", 1) if timestamp else "Unknown time"


def render_styles():
    st.markdown(
        """
        <style>
            .stApp {
                background: #fff7ed;
                color: #1c1917;
            }
            .eyebrow {
                color: #f97316;
                font-size: 0.7rem;
                font-weight: 700;
                letter-spacing: 0.14em;
                text-transform: uppercase;
            }
            .topbar-title h1 {
                color: #c2410c;
                font-size: 1.6rem;
                font-weight: 700;
                margin: 4px 0 0;
            }
            .avatar {
                align-items: center;
                background: #ffedd5;
                border: 2px solid #fed7aa;
                border-radius: 999px;
                color: #c2410c;
                display: flex;
                font-size: 1.2rem;
                font-weight: 700;
                height: 44px;
                justify-content: center;
                margin-left: auto;
                width: 44px;
            }
            .metric-tile {
                align-items: center;
                background: #ffffff;
                border: 1px solid #fed7aa;
                border-radius: 16px;
                box-shadow: 0 1px 3px rgba(249, 115, 22, 0.06);
                display: flex;
                gap: 16px;
                min-height: 110px;
                padding: 18px;
            }
            .icon-box {
                align-items: center;
                background: #ffedd5;
                border-radius: 12px;
                color: #c2410c;
                display: flex;
                flex-shrink: 0;
                font-size: 1.6rem;
                height: 56px;
                justify-content: center;
                width: 56px;
            }
            .icon-box.approved { background: #d1fae5; color: #065f46; }
            .icon-box.warning { background: #fef3c7; color: #92400e; }
            .icon-box.escalated { background: #fee2e2; color: #b42318; }
            .icon-box.blocked { background: #ffedd5; color: #9a3412; }
            .metric-content { flex: 1; }
            .metric-label {
                color: #9a3412;
                font-size: 0.75rem;
                font-weight: 600;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }
            .metric-value {
                color: #7c2d12;
                font-size: 1.8rem;
                font-weight: 700;
                line-height: 1.2;
                margin: 4px 0 2px;
            }
            .metric-delta {
                color: #ea580c;
                font-size: 0.8rem;
                font-weight: 500;
            }
            .section-title {
                color: #7c2d12;
                font-size: 1.15rem;
                font-weight: 700;
                margin: 22px 0 14px;
            }
            .chart-card-title {
                color: #7c2d12;
                font-size: 1rem;
                font-weight: 700;
                margin-bottom: 4px;
            }
            .chart-card-subtitle {
                color: #9a3412;
                font-size: 0.8rem;
                margin-bottom: 14px;
            }
            .decision-badge {
                border-radius: 999px;
                display: inline-block;
                font-size: 0.74rem;
                font-weight: 600;
                padding: 5px 11px;
                text-align: center;
            }
            .decision-badge.approved { background: #d1fae5; color: #065f46; }
            .decision-badge.warning { background: #fef3c7; color: #92400e; }
            .decision-badge.escalated { background: #fee2e2; color: #b42318; }
            .decision-badge.blocked { background: #ffedd5; color: #9a3412; }
            .action-stripe {
                background: #fdba74;
                border-radius: 10px 10px 0 0;
                height: 3px;
                margin-bottom: -3px;
                position: relative;
                z-index: 1;
            }
            .action-stripe.approved { background: #10b981; }
            .action-stripe.warning { background: #f59e0b; }
            .action-stripe.escalated { background: #ef4444; }
            .action-stripe.blocked { background: #9a3412; }
            .reason-heading {
                color: #9a3412;
                font-size: 0.72rem;
                font-weight: 600;
                letter-spacing: 0.04em;
                margin: 14px 0 8px;
                text-transform: uppercase;
            }
            .reason-chip {
                background: #ffedd5;
                border-radius: 999px;
                color: #9a3412;
                display: inline-block;
                font-size: 0.78rem;
                margin: 0 6px 6px 0;
                padding: 5px 10px;
            }
            .empty-state {
                background: #ffffff;
                border: 1px dashed #fdba74;
                border-radius: 12px;
                color: #9a3412;
                padding: 32px;
                text-align: center;
            }
            [data-testid="stVerticalBlockBorderWrapper"] {
                background: #ffffff !important;
                border: 1px solid #fed7aa !important;
                border-radius: 12px !important;
            }
            [data-testid="stSidebar"] {
                background: #ffffff;
                border-right: 1px solid #fed7aa;
            }
            .nav-brand {
                align-items: center;
                display: flex;
                gap: 12px;
                margin: 18px 4px 22px;
            }
            .nav-logo {
                align-items: center;
                background: #fff7ed;
                border: 1px solid #fed7aa;
                border-radius: 10px;
                color: #f97316;
                display: flex;
                font-size: 1.4rem;
                height: 42px;
                justify-content: center;
                width: 42px;
            }
            .nav-title {
                color: #7c2d12;
                font-size: 1.05rem;
                font-weight: 700;
                line-height: 1.2;
            }
            .nav-subtitle {
                color: #9a3412;
                font-size: 0.75rem;
            }
            .filter-heading {
                color: #7c2d12;
                font-size: 0.8rem;
                font-weight: 600;
                margin-bottom: 10px;
            }
            [data-testid="stSidebar"] [role="radiogroup"] label {
                align-items: center;
                border: 1px solid transparent;
                border-radius: 10px;
                color: #57534e;
                cursor: pointer;
                display: flex;
                font-weight: 500;
                gap: 10px;
                margin: 4px 0;
                padding: 10px 12px;
            }
            [data-testid="stSidebar"] [role="radiogroup"] label:hover {
                background: #fff7ed;
            }
            [data-testid="stSidebar"] [role="radiogroup"] label[aria-checked="true"] {
                background: #fff7ed;
                border-color: #fed7aa;
                color: #c2410c;
                font-weight: 700;
            }
            [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
                display: none !important;
            }
            .nav-footer {
                background: #fff7ed;
                border: 1px solid #fed7aa;
                border-radius: 12px;
                color: #9a3412;
                font-size: 0.78rem;
                line-height: 1.5;
                margin-top: 18px;
                padding: 14px;
            }
            @media (max-width: 800px) {
                .metric-tile { min-height: auto; padding: 14px; }
                .avatar { margin: 12px 0 0; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar():
    left, center, right = st.columns([4, 3, 1])
    with left:
        st.markdown(
            '<div class="topbar-title"><div class="eyebrow">Risk Operations</div><h1>AI Trust Layer</h1></div>',
            unsafe_allow_html=True,
        )
    with center:
        st.text_input(
            "Search actions",
            placeholder="Search actions...",
            label_visibility="collapsed",
            key="search_query",
        )
    with right:
        st.markdown('<div class="avatar">R</div>', unsafe_allow_html=True)
    return st.session_state.get("search_query", "")


def render_sidebar():
    st.markdown(
        """
        <div class="nav-brand">
            <div class="nav-logo">🔒</div>
            <div>
                <div class="nav-title">AI Trust Layer</div>
                <div class="nav-subtitle">Risk Operations</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.radio(
        "Navigation",
        NAV_ITEMS,
        label_visibility="collapsed",
        key="nav",
    )
    st.divider()
    st.markdown('<div class="filter-heading">Review filters</div>', unsafe_allow_html=True)
    st.multiselect(
        "Decision status",
        DECISIONS,
        default=DECISIONS,
        format_func=lambda decision: decision_meta(decision)["label"],
        key="selected_decisions",
    )
    st.multiselect(
        "Action type",
        ACTION_TYPES,
        default=ACTION_TYPES,
        format_func=readable_action_type,
        key="selected_action_types",
    )
    st.divider()
    if st.button("Refresh data", use_container_width=True):
        st.rerun()
    st.markdown(
        f"""
        <div class="nav-footer">
            <strong>Decision bands</strong><br>
            0–{AUTO_APPROVE} approved · {AUTO_APPROVE + 1}–{FLAG_FOR_REVIEW} warning<br>
            {FLAG_FOR_REVIEW + 1}–{AUTO_BLOCK - 1} escalated · {AUTO_BLOCK}–100 blocked
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Every action is evaluated and written to the SQLite audit trail.")


def render_metric_tile(icon, label, value, delta, tone="neutral"):
    st.markdown(
        f"""
        <div class="metric-tile">
            <div class="icon-box {tone}">{icon}</div>
            <div class="metric-content">
                <div class="metric-label">{html.escape(str(label))}</div>
                <div class="metric-value">{html.escape(str(value))}</div>
                <div class="metric-delta">{html.escape(str(delta))}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_badge(decision):
    meta = decision_meta(decision)
    st.markdown(
        f'<span class="decision-badge {meta["tone"]}">{html.escape(meta["label"])}</span>',
        unsafe_allow_html=True,
    )


def render_reason_chips(reasons):
    st.markdown('<div class="reason-heading">Risk signals</div>', unsafe_allow_html=True)
    if not reasons:
        st.markdown(
            '<span class="reason-chip">No risk indicators recorded</span>',
            unsafe_allow_html=True,
        )
        return
    chips = "".join(
        f'<span class="reason-chip">{html.escape(str(reason))}</span>'
        for reason in reasons
    )
    st.markdown(chips, unsafe_allow_html=True)


def resolve_review_action(action_id, reviewer_name, resolution):
    reviewer_name = reviewer_name.strip()
    if not reviewer_name:
        st.warning("Enter a reviewer name before resolving an escalation.")
        return
    resolve_action(action_id, reviewer_name, resolution)
    st.session_state["review_message"] = (
        f"Action {action_id} was {resolution} by {reviewer_name}."
    )
    st.rerun()


def render_action_card(action, reviewer_name="", allow_resolution=False):
    meta = decision_meta(action["decision"])
    score = max(0, min(100, int(action["final_score"])))
    st.markdown(
        f'<div class="action-stripe {meta["tone"]}"></div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        title_column, badge_column = st.columns([4, 1])
        with title_column:
            st.subheader(action_title(action))
            st.caption(
                f"Action #{action['id']} · {readable_action_type(action['action_type'])} "
                f"· {format_timestamp(action['timestamp'])}"
            )
        with badge_column:
            render_decision_badge(action["decision"])
            st.caption(f"Score {score}/100")

        st.write(action_summary(action))
        st.caption(f"{meta['risk']} · final trust score")
        st.progress(score / 100)

        financial_column, privacy_column, policy_column = st.columns(3)
        financial_column.metric("Financial", action["financial_score"])
        privacy_column.metric("Privacy", action["privacy_score"])
        policy_column.metric("Policy", action["policy_score"])

        render_reason_chips(action["reasons"])

        with st.expander("View complete action details"):
            st.json(action["details"])
            if action["resolved_by"]:
                st.success(
                    f"Resolved as {action['resolution']} by {action['resolved_by']} "
                    f"at {format_timestamp(action['resolution_time'])}."
                )

        if allow_resolution:
            st.divider()
            st.caption("Human decision required")
            approve_column, reject_column, spacer_column = st.columns([1, 1, 3])
            if approve_column.button("Approve", key=f"approve_{action['id']}"):
                resolve_review_action(action["id"], reviewer_name, "approved")
            if reject_column.button("Reject", key=f"reject_{action['id']}"):
                resolve_review_action(action["id"], reviewer_name, "rejected")
            spacer_column.empty()


def show_decision_result(result):
    decision = result["decision"]
    meta = decision_meta(decision)
    with st.container(border=True):
        title_column, score_column = st.columns([4, 1])
        with title_column:
            st.subheader("Latest trust decision")
            render_decision_badge(decision)
        with score_column:
            st.metric("Final score", result["final_score"])

        message = f"{meta['label']} · {meta['risk']}"
        if decision == "approved":
            st.success(message)
        elif decision in {"approved_with_warning", "escalated"}:
            st.warning(message)
        else:
            st.error(message)

        if result.get("action_id"):
            st.caption(f"Audit action #{result['action_id']} was recorded.")
        render_reason_chips(result["reasons"])


def submit_action(action):
    st.session_state["last_result"] = intercept_action(action)
    st.rerun()


def actions_dataframe(actions):
    if not actions:
        return pd.DataFrame()
    df = pd.DataFrame(actions)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["decision_label"] = df["decision"].apply(lambda d: decision_meta(d)["label"])
    df["action_label"] = df["action_type"].apply(readable_action_type)
    return df


def search_actions(actions, query):
    query = query.lower().strip()
    if not query:
        return actions
    filtered = []
    for action in actions:
        if query in str(action["id"]).lower():
            filtered.append(action)
            continue
        if query in readable_action_type(action["action_type"]).lower():
            filtered.append(action)
            continue
        if query in action_title(action).lower():
            filtered.append(action)
            continue
        if query in action_summary(action).lower():
            filtered.append(action)
            continue
        if any(query in str(reason).lower() for reason in action.get("reasons", [])):
            filtered.append(action)
    return filtered


def _compute_delta(actions, value_fn):
    now = datetime.now()
    current_window = [
        action
        for action in actions
        if action.get("timestamp")
        and datetime.fromisoformat(action["timestamp"]) >= now - timedelta(days=7)
    ]
    previous_window = [
        action
        for action in actions
        if action.get("timestamp")
        and now - timedelta(days=14)
        <= datetime.fromisoformat(action["timestamp"])
        < now - timedelta(days=7)
    ]
    current = value_fn(current_window)
    previous = value_fn(previous_window)
    diff = current - previous
    return current, previous, diff


def _format_delta(diff, previous, is_score=False):
    if previous == 0 and diff == 0:
        return "No change vs last 7 days"
    sign = "+" if diff >= 0 else ""
    unit = " pts" if is_score else ""
    return f"{sign}{diff:.1f}{unit} vs last 7 days"


def _avg_score(actions):
    return sum(action["final_score"] for action in actions) / len(actions) if actions else 0


def style_figure(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font_color="#7c2d12",
        margin=dict(l=10, r=10, t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#ffedd5", gridwidth=1)
    return fig


def build_trend_chart(df):
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data", showarrow=False)
        return style_figure(fig)
    df = df.sort_values("timestamp")
    fig = px.line(
        df,
        x="timestamp",
        y="final_score",
        markers=True,
        color_discrete_sequence=["#f97316"],
    )
    fig.add_hline(
        y=AUTO_APPROVE,
        line_dash="dot",
        line_color="#10b981",
        annotation_text="Approve",
        annotation_position="bottom right",
    )
    fig.add_hline(
        y=FLAG_FOR_REVIEW,
        line_dash="dot",
        line_color="#f59e0b",
        annotation_text="Warning",
        annotation_position="bottom right",
    )
    fig.add_hline(
        y=AUTO_BLOCK,
        line_dash="dot",
        line_color="#ef4444",
        annotation_text="Block",
        annotation_position="bottom right",
    )
    fig.update_yaxes(range=[0, 100])
    fig.update_xaxes(title_text=None)
    fig.update_yaxes(title_text="Trust score")
    return style_figure(fig)


def build_donut_chart(df):
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data", showarrow=False)
        return style_figure(fig)
    counts = df["decision_label"].value_counts().reset_index()
    counts.columns = ["Decision", "Count"]
    color_map = {
        meta["label"]: meta["color"] for meta in DECISION_META.values()
    }
    fig = px.pie(
        counts,
        values="Count",
        names="Decision",
        hole=0.55,
        color="Decision",
        color_discrete_map=color_map,
    )
    fig.update_traces(textinfo="percent+label", pull=None)
    return style_figure(fig)


def build_breakdown_chart(df):
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data", showarrow=False)
        return style_figure(fig)
    grouped = (
        df.groupby(["action_label", "decision_label"])
        .size()
        .reset_index(name="Count")
    )
    color_map = {
        meta["label"]: meta["color"] for meta in DECISION_META.values()
    }
    fig = px.bar(
        grouped,
        x="action_label",
        y="Count",
        color="decision_label",
        barmode="stack",
        color_discrete_map=color_map,
    )
    fig.update_xaxes(title_text=None)
    fig.update_yaxes(title_text=None)
    return style_figure(fig)


def page_overview(actions, open_escalations, decision_counts, average_score):
    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)

    _, total_prev, total_diff = _compute_delta(actions, lambda arr: len(arr))
    _, review_prev, review_diff = _compute_delta(
        open_escalations, lambda arr: len(arr)
    )
    blocked_actions = [
        action for action in actions if action["decision"] == "blocked"
    ]
    _, blocked_prev, blocked_diff = _compute_delta(
        blocked_actions, lambda arr: len(arr)
    )
    _, avg_prev, avg_diff = _compute_delta(actions, _avg_score)

    metric_columns = st.columns(4)
    with metric_columns[0]:
        render_metric_tile(
            "📝",
            "Total actions",
            len(actions),
            _format_delta(total_diff, total_prev),
            "neutral",
        )
    with metric_columns[1]:
        render_metric_tile(
            "🚨",
            "Needs review",
            len(open_escalations),
            _format_delta(review_diff, review_prev),
            "escalated",
        )
    with metric_columns[2]:
        render_metric_tile(
            "🚫",
            "Blocked actions",
            decision_counts["blocked"],
            _format_delta(blocked_diff, blocked_prev),
            "blocked",
        )
    with metric_columns[3]:
        render_metric_tile(
            "⚠️",
            "Average risk",
            f"{average_score:.1f}",
            _format_delta(avg_diff, avg_prev, is_score=True),
            "warning",
        )

    df = actions_dataframe(actions)
    chart_columns = st.columns([2, 1])
    with chart_columns[0]:
        with st.container(border=True):
            st.markdown(
                '<div class="chart-card-title">Risk score trend</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="chart-card-subtitle">Final trust score over time</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                build_trend_chart(df),
                use_container_width=True,
                config={"displayModeBar": False},
                key="trend_chart",
            )
    with chart_columns[1]:
        with st.container(border=True):
            st.markdown(
                '<div class="chart-card-title">Decision distribution</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="chart-card-subtitle">Share of each decision</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                build_donut_chart(df),
                use_container_width=True,
                config={"displayModeBar": False},
                key="donut_chart",
            )

    with st.container(border=True):
        st.markdown(
            '<div class="chart-card-title">Decisions by action type</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="chart-card-subtitle">Stacked breakdown across action types</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            build_breakdown_chart(df),
            use_container_width=True,
            config={"displayModeBar": False},
            key="breakdown_chart",
        )

    st.markdown('<div class="section-title">Latest actions</div>', unsafe_allow_html=True)
    if not actions:
        st.markdown(
            '<div class="empty-state">No audit records match the current filters.</div>',
            unsafe_allow_html=True,
        )
        return
    for index in range(0, min(len(actions), 6), 2):
        action_columns = st.columns(2)
        for column, action in zip(action_columns, actions[index : index + 2]):
            with column:
                render_action_card(action)


def page_review_queue(actions, open_escalations):
    st.markdown('<div class="section-title">Review queue</div>', unsafe_allow_html=True)
    st.caption("Resolve escalated actions after reviewing their checker scores and risk signals.")
    if "review_message" in st.session_state:
        st.success(st.session_state.pop("review_message"))

    if not open_escalations:
        st.markdown(
            '<div class="empty-state">There are no open escalations. New high-risk actions will appear here.</div>',
            unsafe_allow_html=True,
        )
    else:
        reviewer_name = st.text_input(
            "Reviewer name",
            placeholder="Enter your name before resolving an escalation",
        )
        for action in open_escalations:
            render_action_card(action, reviewer_name, allow_resolution=True)

    resolved_actions = [action for action in actions if action["resolved_by"]]
    if resolved_actions:
        st.markdown('<div class="section-title">Recently resolved</div>', unsafe_allow_html=True)
        for action in resolved_actions[:3]:
            render_action_card(action)


def page_audit_history(actions, all_actions_count):
    st.markdown('<div class="section-title">Audit history</div>', unsafe_allow_html=True)
    st.caption(
        f"Showing {len(actions)} of {all_actions_count} recorded actions using the current filters."
    )
    if not actions:
        st.markdown(
            '<div class="empty-state">No audit records match the current filters.</div>',
            unsafe_allow_html=True,
        )
        return

    table_rows = []
    for action in actions:
        table_rows.append(
            {
                "ID": action["id"],
                "Timestamp": format_timestamp(action["timestamp"]),
                "Action type": readable_action_type(action["action_type"]),
                "Financial": action["financial_score"],
                "Privacy": action["privacy_score"],
                "Policy": action["policy_score"],
                "Final score": action["final_score"],
                "Decision": decision_meta(action["decision"])["label"],
                "Resolution": action["resolution"] or "Open",
            }
        )
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Action details</div>', unsafe_allow_html=True)
    for action in actions:
        render_action_card(action)


def page_test_action():
    st.markdown('<div class="section-title">Test an action</div>', unsafe_allow_html=True)
    st.caption("Submit a sample or custom action through the same trust and audit pipeline.")
    if "last_result" in st.session_state:
        show_decision_result(st.session_state["last_result"])

    submission_mode = st.radio(
        "Submission mode",
        ["Use a sample action", "Enter action details"],
        horizontal=True,
    )

    if submission_mode == "Use a sample action":
        with st.form("sample_action_form"):
            sample_name = st.selectbox("Sample action", SAMPLE_ACTIONS)
            sample_submitted = st.form_submit_button("Evaluate sample action")

        if sample_submitted:
            submit_action(build_sample_action(sample_name))
    else:
        action_type = st.selectbox(
            "Action type",
            ACTION_TYPES,
            format_func=readable_action_type,
        )

        if action_type == "transfer_money":
            with st.form("transfer_action_form"):
                amount = st.number_input("Amount", min_value=0.0, step=1000.0)
                currency = st.text_input("Currency", value="PKR")
                recipient = st.text_input("Recipient")
                description = st.text_area("Description")
                transfer_submitted = st.form_submit_button("Evaluate transfer")

            if transfer_submitted:
                submit_action(
                    create_transfer_money_action(
                        amount,
                        currency,
                        recipient,
                        description,
                    )
                )
        elif action_type == "send_email":
            with st.form("email_action_form"):
                recipient = st.text_input("Recipient email")
                subject = st.text_input("Subject")
                body = st.text_area("Email body")
                has_attachment = st.checkbox("Has attachment")
                attachment_name = st.text_input("Attachment name")
                email_submitted = st.form_submit_button("Evaluate email")

            if email_submitted:
                submit_action(
                    create_send_email_action(
                        recipient,
                        subject,
                        body,
                        has_attachment,
                        attachment_name,
                    )
                )
        else:
            with st.form("code_action_form"):
                code = st.text_area("Code")
                environment = st.selectbox(
                    "Environment",
                    ["development", "staging", "production"],
                )
                language = st.text_input("Language", value="Python")
                code_submitted = st.form_submit_button("Evaluate code")

            if code_submitted:
                submit_action(
                    create_execute_code_action(
                        code,
                        environment,
                        language,
                    )
                )


def main():
    st.set_page_config(
        page_title="AI Trust Layer",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_db()
    render_styles()

    all_actions = load_actions()
    query = render_topbar()

    with st.sidebar:
        render_sidebar()

    selected_decisions = st.session_state.get("selected_decisions", DECISIONS)
    selected_action_types = st.session_state.get("selected_action_types", ACTION_TYPES)

    filtered_actions = filter_actions(all_actions, selected_decisions, selected_action_types)
    if query:
        filtered_actions = search_actions(filtered_actions, query)

    open_escalations = get_open_escalations(filtered_actions)
    decision_counts = count_decisions(filtered_actions)
    average_score = (
        sum(action["final_score"] for action in filtered_actions) / len(filtered_actions)
        if filtered_actions
        else 0
    )

    nav = st.session_state.get("nav", "Overview")
    if nav == "Overview":
        page_overview(filtered_actions, open_escalations, decision_counts, average_score)
    elif nav == "Review Queue":
        page_review_queue(filtered_actions, open_escalations)
    elif nav == "Audit History":
        page_audit_history(filtered_actions, len(all_actions))
    else:
        page_test_action()


if __name__ == "__main__":
    main()
