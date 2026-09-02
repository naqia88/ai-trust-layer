# Import regular expressions to detect sensitive data in action details.
import re


# Check an action for privacy risks defined by the company policy.
def check_privacy(action):
    score = 0
    reasons = []
    flagged_fields = []
    details = action["details"]
    content = " ".join(str(value) for value in details.values())

    # Detect Pakistan CNIC values, which are highly sensitive data.
    if re.search(r"\b\d{5}-\d{7}-\d\b", content):
        score = 100
        reasons.append("Customer CNIC number detected")
        flagged_fields.append("details")

    # Detect common phone-number formats before data is shared externally.
    if re.search(r"\b(?:\+92|0092|0)?3\d{2}[-\s]?\d{7}\b", content):
        score = max(score, 90)
        reasons.append("Customer phone number detected")
        flagged_fields.append("details")

    # Detect explicit personal-address fields or address labels in content.
    if "address" in details or "address:" in content.lower():
        score = max(score, 90)
        reasons.append("Personal address detected")
        flagged_fields.append("address")

    # Emails containing customer data require legal review before sending.
    is_customer_data = "customer data" in content.lower() or "customer" in str(
        details.get("attachment_name", "")
    ).lower()
    if action["action_type"] == "send_email" and (score > 0 or is_customer_data):
        score = max(score, 80)
        reasons.append("Email containing customer data requires legal review")
        flagged_fields.append("body")

    # Keep every checker score within the required 0 to 100 range.
    return {
        "score": score,
        "reasons": reasons,
        "flagged_fields": flagged_fields,
    }
