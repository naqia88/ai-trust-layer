
import os
import secrets
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from action_schema import create_action
from database.audit import get_actions, init_db, resolve_action
from trust.interceptor import intercept_action


app = FastAPI(title="AI Trust Layer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://naqia88.github.io",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


# Credentials will be configured in Render, not in frontend code.
# If they are unset, local development continues to work without login.
API_USERNAME = os.getenv("API_USERNAME")
API_PASSWORD = os.getenv("API_PASSWORD")

security = HTTPBasic(auto_error=False)


def require_api_auth(
    credentials: HTTPBasicCredentials | None = Depends(security),
):
    if not API_USERNAME or not API_PASSWORD:
        return

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    username_ok = secrets.compare_digest(
        credentials.username, API_USERNAME
    )
    password_ok = secrets.compare_digest(
        credentials.password, API_PASSWORD
    )

    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


class ActionRequest(BaseModel):
    action_type: Literal[
        "transfer_money", "send_email", "execute_code"
    ]
    details: dict
    triggered_by: str = "Worker Agent"


class ResolutionRequest(BaseModel):
    resolved_by: str = Field(min_length=1)
    resolution: Literal["approved", "rejected"]


@app.on_event("startup")
def initialize_database():
    init_db()


@app.get("/health")
def get_health():
    return {"status": "ok"}


@app.post("/actions", dependencies=[Depends(require_api_auth)])
def submit_action(action_request: ActionRequest):
    action = create_action(
        action_type=action_request.action_type,
        details=action_request.details,
        triggered_by=action_request.triggered_by,
    )
    return intercept_action(action)


@app.get("/actions", dependencies=[Depends(require_api_auth)])
def list_actions():
    return get_actions()


@app.post(
    "/actions/{action_id}/resolve",
    dependencies=[Depends(require_api_auth)],
)
def resolve_escalated_action(
    action_id: int,
    resolution_request: ResolutionRequest,
):
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
