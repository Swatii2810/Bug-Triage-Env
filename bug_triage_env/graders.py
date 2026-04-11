"""Deterministic graders for tasks 1, 2, and 3."""

from models import BugTriageAction, BugTriageReward

# Validator requires scores strictly between 0 and 1 (exclusive)
_SCORE_MIN = 0.001
_SCORE_MAX = 0.999

STEP_PENALTY_WEIGHT = 0.10


def _clamp(score: float) -> float:
    """Clamp score to strictly (0, 1) as required by the validator."""
    return round(max(_SCORE_MIN, min(_SCORE_MAX, score)), 4)


def _time_score(step_number: int, max_steps: int) -> float:
    """Full bonus if action taken on first step, zero on last step."""
    if max_steps <= 1:
        return STEP_PENALTY_WEIGHT
    ratio = (step_number - 1) / max(max_steps - 1, 1)
    return round(STEP_PENALTY_WEIGHT * (1 - ratio), 4)


def _repro_quality(repro_text: str, keywords: list) -> float:
    # Partial credit: score proportional to keyword coverage, max 0.18
    if not keywords:
        return 0.18
    text_lower = repro_text.lower()
    matched = sum(1 for kw in keywords if kw.lower() in text_lower)
    return round((matched / len(keywords)) * 0.18, 4)


def grade_task1(
    action: BugTriageAction,
    ground_truth: dict,
    step_number: int = 1,
    max_steps: int = 1,
) -> BugTriageReward:
    correct = action.issue_type == ground_truth["issue_type"]
    ts = _time_score(step_number, max_steps)
    # Task 1: type correct = 0.90, time bonus = 0.10
    type_s = 0.90 if correct else 0.0
    total = _clamp(type_s + ts)
    return BugTriageReward(
        total=total,
        type_score=type_s,
        severity_score=0.0,
        component_score=0.0,
        repro_score=0.0,
        duplicate_score=0.0,
        time_score=ts,
        breakdown={
            "issue_type": {"predicted": action.issue_type, "expected": ground_truth["issue_type"], "correct": correct},
            "time": {"step_number": step_number, "max_steps": max_steps, "score": ts},
        },
    )


def grade_task2(
    action: BugTriageAction,
    ground_truth: dict,
    step_number: int = 1,
    max_steps: int = 2,
) -> BugTriageReward:
    sev_correct  = action.severity  == ground_truth["severity"]
    comp_correct = action.component == ground_truth["component"]
    ts = _time_score(step_number, max_steps)
    # Task 2: severity=0.45, component=0.45, time=0.10
    sev_score  = 0.45 if sev_correct  else 0.0
    comp_score = 0.45 if comp_correct else 0.0
    total = _clamp(round(sev_score + comp_score + ts, 4))
    return BugTriageReward(
        total=total,
        type_score=0.0,
        severity_score=sev_score,
        component_score=comp_score,
        repro_score=0.0,
        duplicate_score=0.0,
        time_score=ts,
        breakdown={
            "severity":  {"predicted": action.severity,  "expected": ground_truth["severity"],  "correct": sev_correct},
            "component": {"predicted": action.component, "expected": ground_truth["component"], "correct": comp_correct},
            "time": {"step_number": step_number, "max_steps": max_steps, "score": ts},
        },
    )


def grade_task3(
    action: BugTriageAction,
    ground_truth: dict,
    step_number: int = 1,
    max_steps: int = 3,
) -> BugTriageReward:
    # Rebalanced: type=0.18, severity=0.22, component=0.18, repro=0.18, dup=0.14, time=0.10
    type_correct = action.issue_type == ground_truth["issue_type"]
    sev_correct  = action.severity   == ground_truth["severity"]
    comp_correct = action.component  == ground_truth["component"]

    type_score  = 0.18 if type_correct else 0.0
    sev_score   = 0.22 if sev_correct  else 0.0
    comp_score  = 0.18 if comp_correct else 0.0
    repro_score = _repro_quality(action.repro_steps, ground_truth.get("repro_steps_keywords", []))
    ts          = _time_score(step_number, max_steps)

    expected_dup   = ground_truth["is_duplicate"]
    predicted_dup  = action.is_duplicate
    dup_id_correct = action.duplicate_of.strip() == ground_truth.get("duplicate_of", "").strip()
    if expected_dup:
        dup_score = 0.14 if (predicted_dup and dup_id_correct) else 0.0
    else:
        dup_score = 0.14 if not predicted_dup else 0.0

    total = _clamp(round(type_score + sev_score + comp_score + repro_score + dup_score + ts, 4))

    return BugTriageReward(
        total=total,
        type_score=type_score,
        severity_score=sev_score,
        component_score=comp_score,
        repro_score=repro_score,
        duplicate_score=dup_score,
        time_score=ts,
        breakdown={
            "issue_type": {"predicted": action.issue_type, "expected": ground_truth["issue_type"], "correct": type_correct},
            "severity":   {"predicted": action.severity,   "expected": ground_truth["severity"],   "correct": sev_correct},
            "component":  {"predicted": action.component,  "expected": ground_truth["component"],  "correct": comp_correct},
            "repro_steps": {"score": repro_score, "keywords": ground_truth.get("repro_steps_keywords", [])},
            "duplicate": {
                "predicted_is_dup": predicted_dup, "expected_is_dup": expected_dup,
                "predicted_id": action.duplicate_of, "expected_id": ground_truth.get("duplicate_of", ""),
                "score": dup_score,
            },
            "time": {"step_number": step_number, "max_steps": max_steps, "score": ts},
        },
    )


def grade_action(
    action: BugTriageAction,
    ground_truth: dict,
    task_id: int,
    step_number: int = 1,
    max_steps: int = 1,
) -> BugTriageReward:
    if task_id == 1:
        return grade_task1(action, ground_truth, step_number, max_steps)
    elif task_id == 2:
        return grade_task2(action, ground_truth, step_number, max_steps)
    elif task_id == 3:
        return grade_task3(action, ground_truth, step_number, max_steps)
    raise ValueError(f"Unknown task_id: {task_id}")
