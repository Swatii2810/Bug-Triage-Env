---
title: Bug Triage Env
emoji: 🐛
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
tags:
- openenv
- bug-triage
- reinforcement-learning
---

# Bug Triage Environment

An OpenEnv-compatible environment for software bug triage. An AI agent receives GitHub-style issue reports and must classify, prioritize, and resolve them.

## Motivation

Bug triage is a high-value, repetitive engineering task. This repo provides a deterministic benchmark with partial reward signals for training and evaluating triage agents.

---

## Action Space

| Field | Type | Valid Values | Description |
|---|---|---|---|
| `issue_type` | string | `bug`, `feature`, `question` | Classification of the issue |
| `severity` | string | `P1`, `P2`, `P3`, `P4` | Priority level (P1=critical, P4=low) |
| `component` | string | `frontend`, `backend`, `infra`, `database`, `mobile` | Affected system component |
| `assigned_team` | string | `core`, `platform`, `devops`, `mobile` | Team responsible for resolution |
| `repro_steps` | string | Free text | Steps to reproduce the issue |
| `is_duplicate` | boolean | `true`, `false` | Whether this is a duplicate issue |
| `duplicate_of` | string | Issue ID or `""` | ID of the original issue if duplicate |

## Observation Space

| Field | Type | Description |
|---|---|---|
| `issue_id` | string | Unique issue identifier (e.g. `ISSUE-001`) |
| `title` | string | Short issue title |
| `description` | string | Full issue description |
| `reporter` | string | Username of the reporter |
| `created_at` | string | ISO 8601 timestamp |
| `existing_issues` | list | Prior issues for duplicate detection (Task 3 only) |
| `task_id` | int | Current task (1, 2, or 3) |
| `step_number` | int | Current step within the episode |
| `max_steps` | int | Maximum steps allowed for this task |

---

## Tasks

### Task 1 — Issue Classification (easy)
- Classify `issue_type` as `bug`, `feature`, or `question`.
- Reward: `1.0` correct, `0.0` wrong.
- Max steps: 1

### Task 2 — Severity & Component Routing (medium)
- Assign correct `severity` (P1–P4) and `component`.
- Reward: `+0.50` severity, `+0.50` component.
- Max steps: 2

### Task 3 — Full Bug Triage (hard)
- Full triage including duplicate detection against prior issues.
- Reward breakdown:

| Criterion | Max Score |
|---|---|
| `issue_type` correct | +0.20 |
| `severity` correct | +0.25 |
| `component` correct | +0.20 |
| `repro_steps` quality (keyword rubric) | +0.20 |
| Duplicate detection correct | +0.15 |
| **Total** | **1.00** |

- Max steps: 3

---

## Setup

### Local

```bash
cd bug_triage_env
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 7860
```

### Docker

```bash
cd bug_triage_env
docker build -t bug-triage-env .
docker run -p 7860:7860 bug-triage-env
```

### Hugging Face Spaces

Push the `bug_triage_env/` directory as a Docker Space. Port `7860` is pre-configured.

---

## Running Inference

From the project root:

```bash
export API_BASE_URL=http://localhost:7860
export MODEL_NAME=gpt-4o-mini
export OPENAI_API_KEY=sk-...

python inference.py
```

---

## Example Usage

```python
import requests

BASE = "http://localhost:7860"

# Start Task 1
obs = requests.post(f"{BASE}/reset", json={"task_id": 1}).json()
print(obs["title"])

# Submit an action
action = {
    "issue_type":    "bug",
    "severity":      "P1",
    "component":     "backend",
    "assigned_team": "core",
    "repro_steps":   "1. Open app 2. Click login 3. Observe crash",
    "is_duplicate":  False,
    "duplicate_of":  ""
}
result = requests.post(f"{BASE}/step", json={"action": action}).json()
print(result["reward"])   # 1.0 if issue_type was correct
print(result["done"])
```

---

## Baseline Scores

Tested with `gpt-4o-mini` at `temperature=0`, seed=0 (static dataset):

| Task | Difficulty | Avg reward | Notes |
|---|---|---|---|
| 1 — Type classification | Easy | ~0.90 | Simple binary; high ceiling |
| 2 — Severity + component | Medium | ~0.60 | P1/P2 confusion is common |
| 3 — Full triage + adversarial | Hard | ~0.42 | Misleading titles, PII-as-cosmetic, subtle duplicate defeat naive agents |

Time bonus (up to 0.10) is included in all scores. Adversarial cases in Task 3: T3-002 (feature title → bug), T3-003 (cosmetic title → P1 PII leak), T3-007 (subtle duplicate of T3-005).

---

## Dataset

30 realistic GitHub-style issues in `data/issues.py`:
- 10 bugs (P1 crashes, P2 data issues, P3 UI bugs)
- 10 feature requests
- 10 questions / support requests
- 5 duplicates of earlier issues
