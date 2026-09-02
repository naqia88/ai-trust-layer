# Check an action for company-policy violations not covered by other checkers.
def check_policy(action):
    score = 0
    reasons = []
    flagged_fields = []
    details = action["details"]
    action_type = action["action_type"]

    # Block transfers when the recipient is missing, unverified, or a new account.
    if action_type == "transfer_money":
        recipient = str(details.get("recipient", "")).lower()
        description = str(details.get("description", "")).lower()
        recipient_context = f"{recipient} {description}"

        if not recipient or "unverified" in recipient_context or "new account" in recipient_context:
            score = 100
            reasons.append("Transfer recipient is unverified or a new account")
            flagged_fields.append("recipient")

    # Flag external email risks that require human approval under company policy.
    if action_type == "send_email":
        recipient = str(details.get("to", "")).lower()
        attachment_name = str(details.get("attachment_name", "")).lower()
        body = str(details.get("body", "")).lower()

        if not recipient or "unknown" in recipient:
            score = max(score, 80)
            reasons.append("Email to an unknown recipient requires human review")
            flagged_fields.append("to")

        if details.get("has_attachment") and "financial" in attachment_name:
            score = max(score, 70)
            reasons.append("Financial-record attachments require manager approval")
            flagged_fields.append("attachment_name")

        if "confidential" in attachment_name and "external" in body:
            score = max(score, 100)
            reasons.append("Confidential documents may not be shared externally")
            flagged_fields.append("attachment_name")

    # Require approval for production code and block destructive production changes.
    if action_type == "execute_code":
        code = str(details.get("code", "")).lower()
        environment = str(details.get("environment", "")).lower()
        is_production = "production" in environment or environment == "prod"
        changes_database = any(
            command in code
            for command in ("insert ", "update ", "delete from", "alter table", "drop table")
        )
        deletes_data = any(
            command in code for command in ("delete from", "drop table", "drop database", "rm -rf")
        )

        if is_production:
            score = max(score, 80)
            reasons.append("Production code execution requires senior engineer sign-off")
            flagged_fields.append("environment")

        if is_production and deletes_data:
            score = 100
            reasons.append("Production data deletion requires explicit human approval")
            flagged_fields.append("code")

        if changes_database:
            score = max(score, 70)
            reasons.append("Database modifications must be logged and reviewed")
            flagged_fields.append("code")

    # Keep every checker score within the required 0 to 100 range.
    return {
        "score": min(score, 100),
        "reasons": reasons,
        "flagged_fields": flagged_fields,
    }
