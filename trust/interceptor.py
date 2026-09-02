# Import the audit helpers and the trust-agent evaluator.
from database.audit import init_db, log_action
from trust.trust_agent import evaluate_action


# Intercept an action before execution, evaluate it, and persist the decision.
def intercept_action(action):
    result = evaluate_action(action)
    action["status"] = result["decision"]

    # Ensure the audit table exists before recording this trust decision.
    init_db()
    result["action_id"] = log_action(result)

    return result
