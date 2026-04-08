"""FastAPI server — OpenEnv-compatible endpoints."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    BugTriageObservation,
    ResetRequest,
    StepRequest,
    StepResponse,
)
from environment import BugTriageEnvironment

app = FastAPI(
    title="Bug Triage Environment",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = BugTriageEnvironment()


@app.get("/")
def root():
    return {
        "name": "bug-triage-env",
        "version": "1.0.0",
        "tasks": [
            {"id": 1, "name": "Issue Classification",        "difficulty": "easy",   "max_steps": 1},
            {"id": 2, "name": "Severity & Component Routing","difficulty": "medium", "max_steps": 2},
            {"id": 3, "name": "Full Bug Triage",             "difficulty": "hard",   "max_steps": 3},
        ],
        "endpoints": ["/reset", "/step", "/state", "/health"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reset", response_model=BugTriageObservation)
def reset(request: ResetRequest):
    try:
        obs = env.reset(task_id=request.task_id)
        return obs
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResponse)
def step(request: StepRequest):
    try:
        obs, reward, done, info = env.step(request.action)
        return StepResponse(observation=obs, reward=reward, done=done, info=info)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state")
def state():
    return env.state()
