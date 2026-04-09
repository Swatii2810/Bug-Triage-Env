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
import sys
import time
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# The validator injects API_BASE_URL pointing at the running env container
ENV_URL    = os.environ.get("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.environ.get("MODEL_NAME",   "llama-3.1-8b-instant")
HF_TOKEN   = os.environ.get("HF_TOKEN",     "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY") or HF_TOKEN
LLM_URL    = os.environ.get("LLM_BASE_URL",  "https://api.groq.com/openai/v1")

client = OpenAI(api_key=OPENAI_KEY, base_url=LLM_URL)

VALID_TYPES      = ["bug", "feature", "question"]
VALID_SEVERITIES = ["P1", "P2", "P3", "P4"]
VALID_COMPONENTS = ["frontend", "backend", "infra", "database", "mobile"]
VALID_TEAMS      = ["core", "platform", "devops", "mobile"]

SYSTEM_PROMPT = (
    "You are a software engineering manager. "
    "Analyze the issue and respond in JSON format only. "
    "No markdown, no explanation — raw JSON only."
)

DEFAULT_ACTION = {
    "issue_type":    "bug",
    "severity":      "P3",
    "component":     "backend",
    "assigned_team": "core",
    "repro_steps":   "reproduce by following the steps in the description",
    "is_duplicate":  False,
    "duplicate_of":  "",
}


def build_user_prompt(obs: dict) -> str:
    prompt = (
        f"Title: {obs.get('title', '')}\n"
        f"Description: {obs.get('description', '')}\n"
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
        '  "repro_steps": "steps to reproduce",\n'
        '  "is_duplicate": false,\n'
        '  "duplicate_of": ""\n'
        '}'
    )
    return prompt


def call_llm(obs: dict) -> dict:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(obs)},
            ],
            temperature=0.0,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        action = json.loads(raw)
    except Exception:
        action = {}

    for k, v in DEFAULT_ACTION.items():
        action.setdefault(k, v)

    if action["issue_type"]    not in VALID_TYPES:      action["issue_type"]    = "bug"
    if action["severity"]      not in VALID_SEVERITIES: action["severity"]      = "P3"
    if action["component"]     not in VALID_COMPONENTS: action["component"]     = "backend"
    if action["assigned_team"] not in VALID_TEAMS:      action["assigned_team"] = "core"

    return action


def env_post(path: str, payload: dict = None, retries: int = 3) -> dict:
    """POST to the env server with retries. Never raises — returns {} on failure."""
    url = f"{ENV_URL}{path}"
    for attempt in range(retries):
        try:
            r = requests.post(url, json=payload or {}, timeout=30)
            if r.status_code == 200:
                return r.json()
            print(f"[WARN] {path} returned {r.status_code}: {r.text[:200]}", flush=True)
        except Exception as e:
            print(f"[WARN] {path} attempt {attempt+1} failed: {e}", flush=True)
        time.sleep(1)
    return {}


TASK_MAX_STEPS = {1: 1, 2: 2, 3: 3}


def run_episode(task_id: int, episode: int) -> float:
    print(f"[START] task={task_id} episode={episode}", flush=True)

    obs = env_post("/reset", {"task_id": task_id})
    if not obs:
        print(f"[END] task={task_id} score=0.0 steps=0", flush=True)
        return 0.0

    max_steps    = TASK_MAX_STEPS[task_id]
    total_reward = 0.0
    step_count   = 0

    for _ in range(max_steps):
        action = call_llm(obs)
        result = env_post("/step", {"action": action})
        if not result:
            break

        reward     = result.get("reward", 0.0)
        done       = result.get("done", False)
        obs        = result.get("observation", obs)
        step_count += 1
        total_reward += reward

        print(f"[STEP] step={step_count} reward={reward} done={str(done).lower()}", flush=True)

        if done:
            break

    score = round(total_reward, 4)
    print(f"[END] task={task_id} score={score} steps={step_count}", flush=True)
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
        print(f"\n=== Task {task_id} avg reward: {avg} ===\n", flush=True)

    print("\n=== Final Summary ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
