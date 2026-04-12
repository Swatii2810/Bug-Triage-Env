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

# Bug Triage Environment — OpenEnv

> **A reinforcement learning environment for training AI agents on real-world
> software bug triage** — the daily engineering workflow of classifying,
> prioritising, routing, and deduplicating incoming issue reports.

[![HF Space](https://img.shields.io/badge/🤗%20Space-swasss0%2Fbug--triage--env-blue)](https://huggingface.co/spaces/swasss0/bug-triage-env)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-compatible-green)](https://github.com/meta-pytorch/OpenEnv)

---

## Why This Environment

Every software team with a public issue tracker faces the same problem: a continuous stream of incoming reports that must be read, understood, classified, and routed before any engineer can act on them. This task requires real language understanding — titles can be misleading, severity cues are buried in descriptions, and duplicate reports are paraphrased rather than copied.

This environment is designed so that **naive agents fail in interesting ways**:
- An agent that reads only the title will misclassify adversarial issues
- An agent that ignores severity language will route P1 incidents as P3
- An agent without memory of prior issues will miss paraphrased duplicates

These are the same failure modes seen in real triage tooling. Fixing them requires genuine language understanding, not pattern matching.

---

## Environment Design

### What makes this trainable (not just evaluable)

- **Feedback observations**: After each wrong triage decision, the next
  observation includes a `feedback` field describing exactly what was
  incorrect. An RL agent can use this signal to adjust within an episode.
- **Dynamic generation**: `seed` parameter on `/reset` produces different
  issue sets every episode. Agents cannot memorise the dataset.
- **SLA time bonus**: Acting on the first available step earns up to 0.10
  extra reward, modelling real-world SLA pressure.
- **Episode history carry-over**: The agent's own prior triage decisions
  appear in subsequent observations, enabling duplicate detection across
  issues within one episode.

### Action Space

```json
{
  "issue_type":    "bug | feature | question",
  "severity":      "P1 | P2 | P3 | P4",
  "component":     "frontend | backend | infra | database | mobile",
  "assigned_team": "core | platform | devops | mobile",
  "repro_steps":   "",
  "is_duplicate":  false,
  "duplicate_of":  ""
}
```

### Observation Space

```json
{
  "issue_id":        "T3-003",
  "title":           "Profile page UI tweak needed",
  "description":     "...",
  "reporter":        "mia@corp.io",
  "created_at":      "2024-03-13T20:15:00Z",
  "existing_issues": [...],
  "episode_history": [...],
  "feedback":        "Corrections: Severity was 'P3' but should be 'P1'",
  "task_id":         3,
  "step_number":     1,
  "max_steps":       3
}
```

---

## Tasks

### Task 1 — Issue type classification *(Easy)*
Classify each issue as `bug`, `feature`, or `question`. Reward: 1.0 if correct, 0.0 otherwise (+ time bonus up to 0.10). Expected baseline (gpt-4o-mini): **~0.90**

### Task 2 — Severity and component routing *(Medium)*
Predict the correct severity (P1–P4) and owning component. Reward: 0.50 per correct field (+ time bonus). Expected baseline (gpt-4o-mini): **~0.60**

### Task 3 — Full triage with adversarial cases *(Hard)*

| Component | Weight | Graded by |
|---|---|---|
| `issue_type` | 0.18 | Exact match |
| `severity` | 0.22 | Exact match |
| `component` | 0.18 | Exact match |
| `repro_steps` | 0–0.18 | Keyword coverage |
| `duplicate` | 0.14 | Flag + correct parent ID |
| `time bonus` | 0.10 | Step taken on step 1 |

**Adversarial cases (intentional — designed to defeat naive agents):**
- **T3-002**: Title says "Enhancement" but description is a P1 regression bug (data loss)
- **T3-003**: Opens with "UI tweak" language but conceals a PII data leak (true severity: P1, component: backend)
- **T3-007**: Paraphrased duplicate of T3-005 — same bug described with completely different vocabulary

Expected baseline (gpt-4o-mini): **~0.42** A score above 0.65 on Task 3 indicates strong language understanding.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/reset` | POST | Start new episode. Body: `{"task_id": 1\|2\|3, "seed": int\|null}` |
| `/step` | POST | Submit triage action. Body: `{"action": {...}}` |
| `/state` | GET | Current environment state |
| `/health` | GET | Liveness probe |
| `/metrics` | GET | Aggregate performance statistics |
| `/leaderboard` | GET | Ranked difficulty analysis across all episodes |

---

## Setup

```bash
# Local development
pip install -r requirements.txt
uvicorn bug_triage_env.server:app --host 0.0.0.0 --port 7860

# Docker
docker build -t bug-triage-env .
docker run -p 7860:7860 bug-triage-env

# Run baseline
ENV_URL=http://localhost:7860 \
API_KEY=your-key \
MODEL_NAME=gpt-4o-mini \
python inference.py
```

---

## Reward Function Design

The reward function is designed to provide **dense signal** throughout an episode, not just at the end:

1. **Partial credit** (Tasks 2 & 3): Getting severity right but component
   wrong still earns 0.22–0.50, so the agent has signal to improve each field
   independently.
2. **Keyword coverage** (repro_steps): Score proportional to how many of 5
   expected keywords appear in the agent's reproduction steps. Encourages
   descriptive, structured output.
3. **SLA time bonus**: Rewards decisiveness. An agent that acts immediately
   scores up to 0.10 higher than one that deliberates until the last step.
4. **Feedback loop**: Wrong decisions generate a `feedback` string in the
   next observation, enabling within-episode correction.

All rewards clamped to (0.001, 0.999) per OpenEnv validator requirements.

---

## Project Structure

```
├── inference.py          # Baseline script (OpenAI client, structured logs)
├── openenv.yaml          # OpenEnv spec metadata
├── Dockerfile
├── requirements.txt
└── bug_triage_env/
    ├── server.py         # FastAPI endpoints
    ├── environment.py    # Core reset/step/state logic
    ├── graders.py        # Deterministic per-task reward graders
    ├── models.py         # Pydantic typed schemas
    └── data/
        ├── issues.py     # 18 labelled issues (5 + 5 + 8 adversarial)
        └── generator.py  # Procedural issue generation (seed-based)
```
