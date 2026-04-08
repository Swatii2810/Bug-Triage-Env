from pydantic import BaseModel, Field
from typing import Optional


class BugTriageAction(BaseModel):
    issue_type: str     # "bug" | "feature" | "question"
    severity: str       # "P1" | "P2" | "P3" | "P4"
    component: str      # "frontend" | "backend" | "infra" | "database" | "mobile"
    assigned_team: str  # "core" | "platform" | "devops" | "mobile"
    repro_steps: str
    is_duplicate: bool
    duplicate_of: str   # issue ID or ""


class BugTriageObservation(BaseModel):
    issue_id: str
    title: str
    description: str
    reporter: str
    created_at: str
    existing_issues: list
    task_id: int
    step_number: int
    max_steps: int


class BugTriageReward(BaseModel):
    total: float
    type_score: float       # 0.0 or 0.20
    severity_score: float   # 0.0 or 0.25
    component_score: float  # 0.0 or 0.20
    repro_score: float      # 0.0–0.20 partial
    duplicate_score: float  # 0.0 or 0.15
    breakdown: dict


class ResetRequest(BaseModel):
    task_id: int = Field(default=1, ge=1, le=3)


class StepRequest(BaseModel):
    action: BugTriageAction


class StepResponse(BaseModel):
    observation: BugTriageObservation
    reward: float
    done: bool
    info: dict
