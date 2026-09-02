# Import the three independent risk checkers and the score aggregator.
from trust.checkers.financial import check_financial
from trust.checkers.policy import check_policy
from trust.checkers.privacy import check_privacy
from trust.scorer import score_action


# Evaluate one pending action and return its complete trust decision.
def evaluate_action(action):
    financial_result = check_financial(action)
    privacy_result = check_privacy(action)
    policy_result = check_policy(action)

    return score_action(
        action,
        financial_result,
        privacy_result,
        policy_result,
    )
