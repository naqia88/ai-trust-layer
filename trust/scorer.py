# Import timestamps and the configured score thresholds and checker weights.
import datetime

from config import AUTO_APPROVE, AUTO_BLOCK, FLAG_FOR_REVIEW, WEIGHTS


# Calculate the weighted risk score for one supported action type.
def calculate_final_score(action_type, financial_score, privacy_score, policy_score):
    weights = WEIGHTS[action_type]
    weighted_score = (
        financial_score * weights["financial"]
        + privacy_score * weights["privacy"]
        + policy_score * weights["policy"]
    )
    return round(weighted_score)


# Translate a final risk score into the documented trust decision.
def get_decision(final_score):
    if final_score <= AUTO_APPROVE:
        return "approved"
    if final_score <= FLAG_FOR_REVIEW:
        return "approved_with_warning"
    if final_score < AUTO_BLOCK:
        return "escalated"
    return "blocked"


# Combine the three checker results into the audit-ready trust decision.
def score_action(action, financial_result, privacy_result, policy_result):
    financial_score = financial_result["score"]
    privacy_score = privacy_result["score"]
    policy_score = policy_result["score"]
    final_score = calculate_final_score(
        action["action_type"],
        financial_score,
        privacy_score,
        policy_score,
    )
    reasons = []

    # Prefix each reason so reviewers can identify the checker that found it.
    for checker_name, checker_result in (
        ("Financial", financial_result),
        ("Privacy", privacy_result),
        ("Policy", policy_result),
    ):
        for reason in checker_result["reasons"]:
            reasons.append(f"{checker_name}: {reason}")

    return {
        "action": action,
        "financial_score": financial_score,
        "privacy_score": privacy_score,
        "policy_score": policy_score,
        "final_score": final_score,
        "decision": get_decision(final_score),
        "reasons": reasons,
        "timestamp": datetime.datetime.now().isoformat(),
    }
