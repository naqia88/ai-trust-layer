# Import FastAPI, request validation helpers, and the trust-layer services.
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from action_schema import create_action
from database.audit import get_actions, init_db, resolve_action
from trust.interceptor import intercept_action


# Create the local API application used by worker agents and the dashboard.
app = FastAPI(title="AI Trust Layer")


# Validate requests while preserving the required action details structure.
class ActionRequest(BaseModel):
    action_type: Literal["transfer_money", "send_email", "execute_code"]
    details: dict
    triggered_by: str = "Worker Agent"


# Validate the identity and decision supplied by a human reviewer.
class ResolutionRequest(BaseModel):
    resolved_by: str = Field(min_length=1)
    resolution: Literal["approved", "rejected"]


# Create the audit table when the API server starts.
@app.on_event("startup")
def initialize_database():
    init_db()


# Confirm that the local trust service is available.
@app.get("/health")
def get_health():
    return {"status": "ok"}


# Create and intercept an action before any external work can occur.
@app.post("/actions")
def submit_action(action_request: ActionRequest):
    action = create_action(
        action_type=action_request.action_type,
        details=action_request.details,
        triggered_by=action_request.triggered_by,
    )
    return intercept_action(action)


# Return the complete audit trail for the dashboard and reviewers.
@app.get("/actions")
def list_actions():
    return get_actions()


# Record the decision that resolved an escalated action.
@app.post("/actions/{action_id}/resolve")
def resolve_escalated_action(action_id: int, resolution_request: ResolutionRequest):
    resolve_action(
        action_id,
        resolution_request.resolved_by,
        resolution_request.resolution,
    )
    return {
        "action_id": action_id,
        "resolved_by": resolution_request.resolved_by,
        "resolution": resolution_request.resolution,
    }
