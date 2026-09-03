import html
import json
import os
import sys

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
DECISION_META = {
    "approved": {"label": "Approved", "risk": "Low risk", "tone": "approved"},
    "approved_with_warning": {
        "label": "Approved with warning",
        "risk": "Moderate risk",
        "tone": "warning",
    },
    "escalated": {"label": "Escalated", "risk": "High risk", "tone": "escalated"},
    "blocked": {"label": "Blocked", "risk": "Critical risk", "tone": "blocked"},
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
        {"label": decision.replace("_", " ").title(), "risk": "Unknown", "tone": "warning"},
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
                background: #f6f8fc;
                color: #172033;
            }
            .dashboard-header {
                background: linear-gradient(125deg, #102a43, #1d4ed8);
                border-radius: 20px;
                color: #ffffff;
                display: flex;
                justify-content: space-between;
                gap: 24px;
                margin: 0 0 24px;
                padding: 28px 30px;
            }
            .dashboard-header h1 {
                color: #ffffff;
                font-size: 2rem;
                margin: 4px 0 8px;
            }
            .dashboard-header p {
                color: #dbeafe;
                margin: 0;
            }
            .eyebrow {
                color: #bfdbfe;
                font-size: 0.73rem;
                font-weight: 700;
                letter-spacing: 0.12em;
            }
            .header-rule {
                align-self: center;
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: 12px;
                color: #eff6ff;
                font-size: 0.8rem;
                line-height: 1.5;
                max-width: 330px;
                padding: 12px 14px;
            }
            .metric-card {
                background: #ffffff;
                border: 1px solid #dfe6f2;
                border-radius: 16px;
                box-shadow: 0 5px 14px rgba(15, 23, 42, 0.04);
                min-height: 130px;
                padding: 18px;
            }
            .metric-card.approved { border-top: 4px solid #059669; }
            .metric-card.warning { border-top: 4px solid #d97706; }
            .metric-card.escalated { border-top: 4px solid #dc2626; }
            .metric-card.blocked { border-top: 4px solid #7f1d1d; }
            .metric-card.neutral { border-top: 4px solid #2563eb; }
            .metric-label {
                color: #667085;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.05em;
                margin: 0;
                text-transform: uppercase;
            }
            .metric-value {
                color: #172033;
                font-size: 2rem;
                font-weight: 750;
                line-height: 1.25;
                margin: 9px 0 5px;
            }
            .metric-detail {
                color: #667085;
                font-size: 0.85rem;
                margin: 0;
            }
            .decision-badge {
                border-radius: 999px;
                display: inline-block;
                font-size: 0.76rem;
                font-weight: 750;
                padding: 6px 10px;
                text-align: center;
            }
            .decision-badge.approved { background: #d1fae5; color: #065f46; }
            .decision-badge.warning { background: #fef3c7; color: #92400e; }
            .decision-badge.escalated { background: #fee2e2; color: #b42318; }
            .decision-badge.blocked { background: #f3e8ff; color: #6b21a8; }
            .action-stripe {
                border-radius: 10px 10px 0 0;
                height: 5px;
                margin-bottom: -5px;
                position: relative;
                z-index: 1;
            }
            .action-stripe.approved { background: #059669; }
            .action-stripe.warning { background: #d97706; }
            .action-stripe.escalated { background: #dc2626; }
            .action-stripe.blocked { background: #7f1d1d; }
            .reason-heading {
                color: #475467;
                font-size: 0.8rem;
                font-weight: 700;
                margin: 14px 0 7px;
                text-transform: uppercase;
            }
            .reason-chip {
                background: #eef2f7;
                border-radius: 999px;
                color: #344054;
                display: inline-block;
                font-size: 0.8rem;
                margin: 0 5px 6px 0;
                padding: 5px 9px;
            }
            .empty-state {
                background: #ffffff;
                border: 1px dashed #cbd5e1;
                border-radius: 16px;
                color: #475467;
                padding: 28px;
                text-align: center;
            }
            [data-testid="stSidebar"] {
                background: #ffffff;
                border-right: 1px solid #e4e7ec;
            }
            [data-testid="stTabs"] button {
                font-weight: 650;
            }
            [data-testid="stVerticalBlockBorderWrapper"] {
                border-radius: 14px;
            }
            @media (max-width: 800px) {
                .dashboard-header { display: block; padding: 22px; }
                .header-rule { margin-top: 18px; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    st.markdown(
        f"""
        <div class="dashboard-header">
            <div>
                <div class="eyebrow">RISK OPERATIONS</div>
                <h1>AI Trust Layer</h1>
                <p>Review decisions before actions are carried out.</p>
            </div>
            <div class="header-rule">
                <strong>Decision bands</strong><br>
                0–{AUTO_APPROVE} approved · {AUTO_APPROVE + 1}–{FLAG_FOR_REVIEW} warning<br>
                {FLAG_FOR_REVIEW + 1}–{AUTO_BLOCK - 1} escalated · {AUTO_BLOCK}–100 blocked
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label, value, detail, tone="neutral"):
    st.markdown(
        f"""
        <div class="metric-card {tone}">
            <p class="metric-label">{html.escape(str(label))}</p>
            <p class="metric-value">{html.escape(str(value))}</p>
            <p class="metric-detail">{html.escape(str(detail))}</p>
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


st.set_page_config(page_title="AI Trust Layer", layout="wide")
init_db()
render_styles()
render_header()

with st.sidebar:
    st.markdown("## Review filters")
    st.caption("Control which actions appear in audit history and the command center.")
    selected_decisions = st.multiselect(
        "Decision status",
        DECISIONS,
        default=DECISIONS,
        format_func=lambda decision: decision_meta(decision)["label"],
    )
    selected_action_types = st.multiselect(
        "Action type",
        ACTION_TYPES,
        default=ACTION_TYPES,
        format_func=readable_action_type,
    )
    st.divider()
    if st.button("Refresh data", use_container_width=True):
        st.rerun()
    st.caption("Every action is evaluated and written to the SQLite audit trail.")

all_actions = load_actions()
filtered_actions = filter_actions(
    all_actions,
    selected_decisions,
    selected_action_types,
)
decision_counts = count_decisions(all_actions)
open_escalations = get_open_escalations(all_actions)
average_score = (
    sum(action["final_score"] for action in all_actions) / len(all_actions)
    if all_actions
    else 0
)

metric_columns = st.columns(4)
with metric_columns[0]:
    render_metric_card("Total actions", len(all_actions), "All recorded trust decisions")
with metric_columns[1]:
    render_metric_card(
        "Needs review",
        len(open_escalations),
        "Open escalations awaiting a human",
        "escalated",
    )
with metric_columns[2]:
    render_metric_card(
        "Blocked actions",
        decision_counts["blocked"],
        "Actions stopped automatically",
        "blocked",
    )
with metric_columns[3]:
    render_metric_card(
        "Average risk",
        f"{average_score:.1f}",
        "Average final trust score",
        "warning" if average_score > AUTO_APPROVE else "approved",
    )

overview_tab, review_tab, audit_tab, submit_tab = st.tabs(
    ["Overview", "Review queue", "Audit history", "Test an action"]
)

with overview_tab:
    st.subheader("Risk overview")
    overview_left, overview_right = st.columns([2, 1])
    with overview_left:
        st.write(
            "Monitor the latest trust decisions and open high-risk actions from one place."
        )
    with overview_right:
        if open_escalations:
            st.warning(f"{len(open_escalations)} action(s) require human review.")
        else:
            st.success("No actions currently require human review.")

    st.markdown("### Latest actions")
    if not filtered_actions:
        st.markdown(
            '<div class="empty-state">No audit records match the current filters.</div>',
            unsafe_allow_html=True,
        )
    else:
        for index in range(0, min(len(filtered_actions), 6), 2):
            action_columns = st.columns(2)
            for column, action in zip(action_columns, filtered_actions[index : index + 2]):
                with column:
                    render_action_card(action)

with review_tab:
    st.subheader("Review queue")
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

    resolved_actions = [action for action in all_actions if action["resolved_by"]]
    if resolved_actions:
        st.markdown("### Recently resolved")
        for action in resolved_actions[:3]:
            render_action_card(action)

with audit_tab:
    st.subheader("Audit history")
    st.caption(
        f"Showing {len(filtered_actions)} of {len(all_actions)} recorded actions using the current filters."
    )
    if not filtered_actions:
        st.markdown(
            '<div class="empty-state">No audit records match the current filters.</div>',
            unsafe_allow_html=True,
        )
    else:
        table_rows = []
        for action in filtered_actions:
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
        st.markdown("### Action details")
        for action in filtered_actions:
            render_action_card(action)

with submit_tab:
    st.subheader("Test an action")
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
