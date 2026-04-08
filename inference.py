"""
Baseline inference script for the Bug Triage Environment.

Log format:
  [START] {"task_id": 1, "episode": 0}
  [STEP]  {"step": 1, "action": {...}, "reward": 0.0, "done": false}
  [END]   {"task_id": 1, "total_reward": 0.85, "steps": 3}

Env vars: API_BASE_URL, MODEL_NAME, HF_TOKEN (used as api_key)
"""

import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "llama-3.1-8b-instant")
HF_TOKEN     = os.environ.get("HF_TOKEN",     "")
OPENAI_KEY   = os.environ.get("OPENAI_API_KEY", HF_TOKEN)

client = OpenAI(
    api_key=OPENAI_KEY,
    base_url=API_BASE_URL,
)

VALID_TYPES      = ["bug", "feature", "question"]
VALID_SEVERITIES = ["P1", "P2", "P3", "P4"]
VALID_COMPONENTS = ["frontend", "backend", "infra", "database", "mobile"]
VALID_TEAMS      = ["core", "platform", "devops", "mobile"]

SYSTEM_PROMPT = (
    "You are a software engineering manager. "
    "Analyze the issue and respond in JSON format only. "
    "No markdown, no explanation — raw JSON only."
)


def build_user_prompt(obs: dict) -> str:
    prompt = (
        f"Title: {obs['title']}\n"
        f"Description: {obs['description']}\n"
    )
    if obs.get("existing_issues"):
        prompt += "\nExisting issues (for duplicate detection):\n"
        for ex in obs["existing_issues"][:10]:
            prompt += f"  - {ex['issue_id']}: {ex['title']}\n"
    prompt += (
        '\nRespond with JSON:\n'
        '{\n'
        '  "issue_type": "bug" or "feature" or "question",\n'
        '  "severity": "P1" or "P2" or "P3" or "P4",\n'
        '  "component": "frontend" or "backend" or "infra" or "database" or "mobile",\n'
        '  "assigned_team": "core" or "platform" or "devops" or "mobile",\n'
        '  "repro_steps": "your reproduction steps here",\n'
        '  "is_duplicate": false,\n'
        '  "duplicate_of": ""\n'
        '}'
    )
    return prompt


def call_llm(obs: dict) -> dict:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": build_user_prompt(obs)},
        ],
        temperature=0.0,
    )
    raw = response.choices[0].message.content.strip()

    # strip markdown fences some models add despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        action = json.loads(raw)
    except json.JSONDecodeError:
        action = {}

    action.setdefault("issue_type",    "bug")
    action.setdefault("severity",      "P3")
    action.setdefault("component",     "backend")
    action.setdefault("assigned_team", "core")
    action.setdefault("repro_steps",   "")
    action.setdefault("is_duplicate",  False)
    action.setdefault("duplicate_of",  "")

    if action["issue_type"]    not in VALID_TYPES:      action["issue_type"]    = "bug"
    if action["severity"]      not in VALID_SEVERITIES: action["severity"]      = "P3"
    if action["component"]     not in VALID_COMPONENTS: action["component"]     = "backend"
    if action["assigned_team"] not in VALID_TEAMS:      action["assigned_team"] = "core"

    return action


TASK_MAX_STEPS = {1: 1, 2: 2, 3: 3}


def run_episode(task_id: int, episode: int) -> float:
    print(json.dumps({"tag": "[START]", "task_id": task_id, "episode": episode}))

    resp = requests.post(
        f"http://localhost:7860/reset", json={"task_id": task_id}
    )
    resp.raise_for_status()
    obs = resp.json()

    max_steps    = TASK_MAX_STEPS[task_id]
    total_reward = 0.0
    step_count   = 0

    for _ in range(max_steps):
        action = call_llm(obs)
        step_resp = requests.post(
            "http://localhost:7860/step", json={"action": action}
        )
        step_resp.raise_for_status()
        result = step_resp.json()

        reward     = result["reward"]
        done       = result["done"]
        obs        = result["observation"]
        step_count += 1
        total_reward += reward

        print(json.dumps({
            "tag":    "[STEP]",
            "step":   step_count,
            "action": action,
            "reward": reward,
            "done":   done,
        }))

        if done:
            break

    print(json.dumps({
        "tag":          "[END]",
        "task_id":      task_id,
        "total_reward": round(total_reward, 4),
        "steps":        step_count,
    }))

    return total_reward


def main():
    EPISODES_PER_TASK = 5
    summary = {}

    for task_id in [1, 2, 3]:
        rewards = []
        for ep in range(EPISODES_PER_TASK):
            r = run_episode(task_id, ep)
            rewards.append(r)
        avg = round(sum(rewards) / len(rewards), 4)
        summary[f"task_{task_id}"] = {"episodes": rewards, "avg_reward": avg}
        print(f"\n=== Task {task_id} avg reward: {avg} ===\n")

    print("\n=== Final Summary ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
