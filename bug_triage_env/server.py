"""FastAPI server — OpenEnv-compatible endpoints."""

import sys
import os
import threading
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from models import BugTriageObservation, StepRequest, StepResponse
from environment import BugTriageEnvironment

app = FastAPI(title="Bug Triage Environment", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = BugTriageEnvironment()

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
        "endpoints": ["/reset", "/step", "/state", "/health", "/metrics", "/leaderboard"],
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
        return {
            "total_resets": _metrics["total_resets"],
            "total_steps":  _metrics["total_steps"],
            "avg_reward_by_task": {
                t: round(sum(r) / len(r), 4) if r else 0.0
                for t, r in _metrics["rewards_by_task"].items()
            },
            "component_accuracy": {
                comp: {
                    "correct": _metrics["component_correct"][comp],
                    "total":   _metrics["component_total"][comp],
                    "rate": round(
                        _metrics["component_correct"][comp] /
                        _metrics["component_total"][comp], 4
                    ) if _metrics["component_total"][comp] else 0.0,
                }
                for comp in _metrics["component_total"]
            },
            "severity_accuracy": {
                sev: {
                    "correct": _metrics["severity_correct"][sev],
                    "total":   _metrics["severity_total"][sev],
                    "rate": round(
                        _metrics["severity_correct"][sev] /
                        _metrics["severity_total"][sev], 4
                    ) if _metrics["severity_total"][sev] else 0.0,
                }
                for sev in _metrics["severity_total"]
            },
            "duplicate_detection_rate": round(
                _metrics["duplicate_correct"] / _metrics["duplicate_total"], 4
            ) if _metrics["duplicate_total"] else 0.0,
        }


@app.get("/leaderboard")
def get_leaderboard() -> dict:
    """Ranked summary of agent performance. Shows hardest components and severities."""
    with _metrics_lock:
        total_steps = _metrics["total_steps"]
        if total_steps == 0:
            return {
                "message": "No episodes completed yet. Run inference.py to populate.",
                "leaderboard": [],
                "hardest_components": [],
                "hardest_severities": [],
            }

        component_difficulty = []
        for comp, total in _metrics["component_total"].items():
            if total > 0:
                correct = _metrics["component_correct"].get(comp, 0)
                rate = round(correct / total, 4)
                component_difficulty.append({
                    "component": comp, "accuracy": rate,
                    "correct": correct, "total": total,
                    "difficulty": "hard" if rate < 0.5 else "medium" if rate < 0.8 else "easy",
                })
        component_difficulty.sort(key=lambda x: x["accuracy"])

        severity_difficulty = []
        for sev, total in _metrics["severity_total"].items():
            if total > 0:
                correct = _metrics["severity_correct"].get(sev, 0)
                rate = round(correct / total, 4)
                severity_difficulty.append({
                    "severity": sev, "accuracy": rate,
                    "correct": correct, "total": total,
                    "difficulty": "hard" if rate < 0.5 else "medium" if rate < 0.8 else "easy",
                })
        severity_difficulty.sort(key=lambda x: x["accuracy"])

        task_summary = []
        for task_id in ["1", "2", "3"]:
            rewards = _metrics["rewards_by_task"].get(task_id, [])
            if rewards:
                task_summary.append({
                    "task_id": int(task_id),
                    "episodes_run": len(rewards),
                    "avg_reward": round(sum(rewards) / len(rewards), 4),
                    "best_reward": round(max(rewards), 4),
                    "worst_reward": round(min(rewards), 4),
                })

        dup_total = _metrics["duplicate_total"]
        return {
            "total_steps": total_steps,
            "total_resets": _metrics["total_resets"],
            "task_performance": task_summary,
            "hardest_components": component_difficulty[:3],
            "hardest_severities": severity_difficulty[:3],
            "duplicate_detection_rate": round(
                _metrics["duplicate_correct"] / dup_total, 4
            ) if dup_total else 0.0,
            "note": "Accuracy below 0.5 indicates a genuinely hard sub-task for the agent.",
        }
