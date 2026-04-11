"""FastAPI server — OpenEnv-compatible endpoints."""

import sys
import os
import threading
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from models import (
    BugTriageObservation,
    StepRequest,
    StepResponse,
)
from environment import BugTriageEnvironment

app = FastAPI(title="Bug Triage Environment", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = BugTriageEnvironment()

# ── Metrics ───────────────────────────────────────────────────────────────────
_metrics_lock = threading.Lock()
_metrics: dict = {
    "total_resets":      0,
    "total_steps":       0,
    "rewards_by_task":   defaultdict(list),
    "component_correct": defaultdict(int),
    "component_total":   defaultdict(int),
    "severity_correct":  defaultdict(int),
    "severity_total":    defaultdict(int),
    "duplicate_correct": 0,
    "duplicate_total":   0,
}


@app.get("/")
def root():
    return {
        "name": "bug-triage-env",
        "version": "1.0.0",
        "tasks": [
            {"id": 1, "name": "Issue Classification",         "difficulty": "easy",   "max_steps": 1},
            {"id": 2, "name": "Severity & Component Routing", "difficulty": "medium", "max_steps": 2},
            {"id": 3, "name": "Full Bug Triage",              "difficulty": "hard",   "max_steps": 3},
        ],
        "endpoints": ["/reset", "/step", "/state", "/health", "/metrics"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/reset")
def reset_get():
    return {"status": "ok", "hint": "Use POST /reset with {task_id: 1|2|3, seed: int|null}"}


@app.post("/reset", response_model=BugTriageObservation)
async def reset(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        task_id = int(body.get("task_id", 1)) if isinstance(body, dict) else 1
        seed    = body.get("seed", None)       if isinstance(body, dict) else None
        obs = env.reset(task_id=task_id, seed=seed)
        with _metrics_lock:
            _metrics["total_resets"] += 1
        return obs
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResponse)
def step(request: StepRequest):
    try:
        obs, reward, done, info = env.step(request.action)

        with _metrics_lock:
            _metrics["total_steps"] += 1
            task = info.get("task_id", 1)
            _metrics["rewards_by_task"][str(task)].append(reward)
            bd = info.get("reward_breakdown", {})
            if "component" in bd:
                comp = bd["component"].get("expected", "")
                _metrics["component_total"][comp] += 1
                if bd["component"].get("correct"):
                    _metrics["component_correct"][comp] += 1
            if "severity" in bd:
                sev = bd["severity"].get("expected", "")
                _metrics["severity_total"][sev] += 1
                if bd["severity"].get("correct"):
                    _metrics["severity_correct"][sev] += 1
            if "duplicate" in bd:
                _metrics["duplicate_total"] += 1
                if bd["duplicate"].get("score", 0) > 0:
                    _metrics["duplicate_correct"] += 1

        return StepResponse(observation=obs, reward=reward, done=done, info=info)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state")
def state():
    return env.state()


@app.get("/metrics")
def get_metrics() -> dict:
    with _metrics_lock:
        avg_by_task = {}
        for t, rewards in _metrics["rewards_by_task"].items():
            avg_by_task[t] = round(sum(rewards) / len(rewards), 4) if rewards else 0.0

        comp_acc = {}
        for comp in set(_metrics["component_total"].keys()):
            total   = _metrics["component_total"][comp]
            correct = _metrics["component_correct"][comp]
            comp_acc[comp] = {"correct": correct, "total": total,
                               "rate": round(correct / total, 4) if total else 0.0}

        sev_acc = {}
        for sev in set(_metrics["severity_total"].keys()):
            total   = _metrics["severity_total"][sev]
            correct = _metrics["severity_correct"][sev]
            sev_acc[sev] = {"correct": correct, "total": total,
                             "rate": round(correct / total, 4) if total else 0.0}

        dup_total = _metrics["duplicate_total"]
        return {
            "total_resets":            _metrics["total_resets"],
            "total_steps":             _metrics["total_steps"],
            "avg_reward_by_task":      avg_by_task,
            "component_accuracy":      comp_acc,
            "severity_accuracy":       sev_acc,
            "duplicate_detection_rate": (
                round(_metrics["duplicate_correct"] / dup_total, 4) if dup_total else 0.0
            ),
        }
