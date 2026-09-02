# Check the financial risk of an action against the company transfer policy.
def check_financial(action):
    score = 0
    reasons = []
    flagged_fields = []

    # Only money transfers require a financial-risk assessment.
    if action["action_type"] != "transfer_money":
        return {
            "score": score,
            "reasons": reasons,
            "flagged_fields": flagged_fields,
        }

    details = action["details"]
    amount = details.get("amount", 0)
    currency = details.get("currency", "PKR")
    recipient = details.get("recipient")

    # Transfers above PKR 100,000 require CFO approval.
    if amount > 100000:
        score += 70
        reasons.append("Amount exceeds the PKR 100,000 CFO approval limit")
        flagged_fields.append("amount")

    # A non-PKR transfer is treated as an international transfer.
    if currency != "PKR":
        score += 30
        reasons.append("International transfers require board approval")
        flagged_fields.append("currency")

    # A transfer cannot be evaluated without a recipient.
    if not recipient:
        score = 100
        reasons.append("Recipient is missing and cannot be verified")
        flagged_fields.append("recipient")

    # Keep every checker score within the required 0 to 100 range.
    return {
        "score": min(score, 100),
        "reasons": reasons,
        "flagged_fields": flagged_fields,
    }
