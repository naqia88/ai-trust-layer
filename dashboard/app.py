import json
import os
import sys

# Streamlit runs this script from dashboard/, so project imports need the root path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# The configured SQLite path is relative to the project root.
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


# Decode SQLite's JSON text fields before displaying them in the dashboard.
def decode_json(value, default_value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default_value
    return value if value is not None else default_value


# Load the audit records and make their stored details readable to reviewers.
def load_actions():
    actions = []
    for action in get_actions():
        action["details"] = decode_json(action["details"], {})
        action["reasons"] = decode_json(action["reasons"], [])
        actions.append(action)
    return actions


# Apply the dashboard filters without changing the audit records themselves.
def filter_actions(actions, decisions, action_types):
    return [
        action
        for action in actions
        if action["decision"] in decisions and action["action_type"] in action_types
    ]


# Count each decision type so the metrics use the same decision names as the scorer.
def count_decisions(actions):
    counts = {decision: 0 for decision in DECISIONS}
    for action in actions:
        counts[action["decision"]] += 1
    return counts


# Find escalated actions that a human reviewer has not resolved yet.
def get_open_escalations(actions):
    return [
        action
        for action in actions
        if action["decision"] == "escalated" and not action["resolved_by"]
    ]


# Build complete audit-safe actions through the existing worker helper functions.
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


# Show a decision with the status color that matches its risk level.
def show_decision_result(result):
    decision = result["decision"]
    message = (
        f"Trust decision: {decision.replace('_', ' ')} "
        f"(final score: {result['final_score']})"
    )

    if decision == "approved":
        st.success(message)
    elif decision in {"approved_with_warning", "escalated"}:
        st.warning(message)
    else:
        st.error(message)

    if result["reasons"]:
        st.write("Reasons:")
        for reason in result["reasons"]:
            st.write(f"- {reason}")


# Submit only through the interceptor so every decision is evaluated and logged.
def submit_action(action):
    st.session_state["last_result"] = intercept_action(action)
    st.rerun()


st.set_page_config(page_title="AI Trust Layer", layout="wide")
init_db()

st.title("AI Trust Layer Dashboard")
st.caption("Review trust decisions before actions are carried out.")
st.info(
    "Decision bands: "
    f"0-{AUTO_APPROVE} approved, "
    f"{AUTO_APPROVE + 1}-{FLAG_FOR_REVIEW} approved with warning, "
    f"{FLAG_FOR_REVIEW + 1}-{AUTO_BLOCK - 1} escalated, "
    f"{AUTO_BLOCK}-100 blocked."
)

with st.sidebar:
    st.header("Review controls")
    reviewer_name = st.text_input("Reviewer name")
    selected_decisions = st.multiselect(
        "Decision filter",
        DECISIONS,
        default=DECISIONS,
    )
    selected_action_types = st.multiselect(
        "Action type filter",
        ACTION_TYPES,
        default=ACTION_TYPES,
    )
    if st.button("Refresh data"):
        st.rerun()

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

metric_row_one = st.columns(3)
metric_row_one[0].metric("Total actions", len(all_actions))
metric_row_one[1].metric("Open escalations", len(open_escalations))
metric_row_one[2].metric("Average risk score", f"{average_score:.1f}")

metric_row_two = st.columns(4)
for column, decision in zip(metric_row_two, DECISIONS):
    column.metric(decision.replace("_", " ").title(), decision_counts[decision])

audit_tab, review_tab, submit_tab = st.tabs(
    ["Audit log", "Review queue", "Submit test action"]
)

with audit_tab:
    st.subheader("Audit log")
    if not filtered_actions:
        st.info("No audit records match the current filters.")
    else:
        table_rows = []
        for action in filtered_actions:
            table_rows.append(
                {
                    "ID": action["id"],
                    "Timestamp": action["timestamp"],
                    "Action type": action["action_type"],
                    "Financial": action["financial_score"],
                    "Privacy": action["privacy_score"],
                    "Policy": action["policy_score"],
                    "Final": action["final_score"],
                    "Decision": action["decision"],
                    "Resolution": action["resolution"] or "Open",
                }
            )
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        for action in filtered_actions:
            with st.expander(
                f"Action {action['id']}: {action['action_type']} "
                f"({action['decision'].replace('_', ' ')})"
            ):
                st.write("Details")
                st.json(action["details"])
                st.write("Reasons")
                if action["reasons"]:
                    for reason in action["reasons"]:
                        st.write(f"- {reason}")
                else:
                    st.write("No risk reasons were recorded.")
                if action["resolved_by"]:
                    st.write(f"Resolved by: {action['resolved_by']}")
                    st.write(f"Resolution: {action['resolution']}")
                    st.write(f"Resolution time: {action['resolution_time']}")

with review_tab:
    st.subheader("Escalations needing review")
    if "review_message" in st.session_state:
        st.success(st.session_state.pop("review_message"))

    if not open_escalations:
        st.info("There are no open escalations.")
    else:
        for action in open_escalations:
            with st.expander(
                f"Action {action['id']}: {action['action_type']} "
                f"(score: {action['final_score']})"
            ):
                st.json(action["details"])
                for reason in action["reasons"]:
                    st.write(f"- {reason}")

                approve_column, reject_column = st.columns(2)
                if approve_column.button("Approve", key=f"approve_{action['id']}"):
                    if not reviewer_name.strip():
                        st.warning("Enter a reviewer name before resolving an escalation.")
                    else:
                        resolve_action(action["id"], reviewer_name.strip(), "approved")
                        st.session_state["review_message"] = (
                            f"Action {action['id']} was approved by {reviewer_name.strip()}."
                        )
                        st.rerun()
                if reject_column.button("Reject", key=f"reject_{action['id']}"):
                    if not reviewer_name.strip():
                        st.warning("Enter a reviewer name before resolving an escalation.")
                    else:
                        resolve_action(action["id"], reviewer_name.strip(), "rejected")
                        st.session_state["review_message"] = (
                            f"Action {action['id']} was rejected by {reviewer_name.strip()}."
                        )
                        st.rerun()

    resolved_actions = [action for action in all_actions if action["resolved_by"]]
    if resolved_actions:
        st.subheader("Recently resolved")
        for action in resolved_actions:
            st.write(
                f"Action {action['id']} was {action['resolution']} by "
                f"{action['resolved_by']} at {action['resolution_time']}."
            )

with submit_tab:
    st.subheader("Submit a test action")
    if "last_result" in st.session_state:
        show_decision_result(st.session_state["last_result"])

    submission_mode = st.radio(
        "Submission mode",
        ["Use a sample action", "Enter action details"],
        horizontal=True,
    )

    if submission_mode == "Use a sample action":
        with st.form("sample_action_form"):
            sample_name = st.selectbox(
                "Sample action",
                [
                    "Routine PKR transfer (approved)",
                    "Production cleanup command (warning)",
                    "High-risk transfer (escalated)",
                    "Email containing a CNIC (escalated)",
                    "International high-risk transfer (blocked)",
                ],
            )
            sample_submitted = st.form_submit_button("Evaluate sample action")

        if sample_submitted:
            submit_action(build_sample_action(sample_name))
    else:
        action_type = st.selectbox("Action type", ACTION_TYPES)

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
