# Import Python's built-in datetime module for action timestamps.
import datetime


# Create a pending action record in the system's required schema format.
def create_action(action_type, details, triggered_by="Worker Agent"):
    return {
        "action_type": action_type,
        "details": details,
        "triggered_by": triggered_by,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "pending",
    }
