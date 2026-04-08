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

An OpenEnv-compatible environment for software bug triage. An AI agent receives
GitHub-style issue reports and must classify, prioritize, and resolve them.

## Project Structure

```
.
├── README.md
├── inference.py          ← baseline agent script
├── requirements.txt
├── Dockerfile
├── openenv.yaml
├── .gitignore
└── bug_triage_env/
    ├── server.py         ← FastAPI app (port 7860)
    ├── environment.py    ← BugTriageEnvironment
    ├── graders.py        ← deterministic graders
    ├── models.py         ← Pydantic v2 models
    └── data/
        └── issues.py     ← 30 realistic bug reports
```

## Tasks

| ID | Name | Difficulty | Max Steps | Max Reward |
|----|------|-----------|-----------|------------|
| 1 | Issue Classification | Easy | 1 | 1.00 |
| 2 | Severity & Component Routing | Medium | 2 | 1.00 |
| 3 | Full Bug Triage | Hard | 3 | 1.00 |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/reset` | Start new episode `{"task_id": 1}` |
| POST | `/step` | Submit action, get reward |
| GET | `/state` | Current environment state |
| GET | `/health` | Health check |

## Action Space

| Field | Type | Values |
|-------|------|--------|
| `issue_type` | string | `bug`, `feature`, `question` |
| `severity` | string | `P1`, `P2`, `P3`, `P4` |
| `component` | string | `frontend`, `backend`, `infra`, `database`, `mobile` |
| `assigned_team` | string | `core`, `platform`, `devops`, `mobile` |
| `repro_steps` | string | free text |
| `is_duplicate` | bool | `true`, `false` |
| `duplicate_of` | string | issue ID or `""` |

## Setup

```bash
pip install -r requirements.txt
cd bug_triage_env
uvicorn server:app --host 0.0.0.0 --port 7860
```

## Running Inference

```bash
export API_BASE_URL=http://localhost:7860
export LLM_BASE_URL=https://api.groq.com/openai/v1
export MODEL_NAME=llama-3.1-8b-instant
export HF_TOKEN=your_groq_key_here

python inference.py
```

## Baseline Scores

Measured over 5 episodes per task using `llama-3.1-8b-instant` via Groq API.

| Task | Difficulty | Random Baseline | LLM Baseline (llama-3.1-8b) |
|------|------------|-----------------|------------------------------|
| Issue Classification | Easy | 0.33 | 1.00 |
| Severity & Component | Medium | 0.10 | 0.45 |
| Full Triage | Hard | 0.05 | 0.56 |

## Docker

```bash
docker build -t bug-triage-env .
docker run -p 7860:7860 bug-triage-env
```
