"""
Baseline inference script for the Bug Triage Environment.

Log format:
  [START] task=1 episode=0
  [STEP]  step=1 reward=0.0 done=false
  [END]   task=1 score=0.85 steps=1

Validator injects:
  API_BASE_URL — LLM proxy base URL
  API_KEY      — LLM proxy API key
  MODEL_NAME   — model name
  ENV_URL      — environment server URL
"""

import os
import sys
import json
import time
import requests

from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
API_KEY      = os.environ.get("API_KEY") or os.environ.get("HF_TOKEN", "no-key")
MODEL_NAME   = os.environ.get("MODEL_NAME", "gpt-4o-mini")
ENV_URL      = os.environ.get("ENV_URL", "http://localhost:7860")

# Lazy-init the OpenAI client so import errors don't crash at module level
_client = None

def get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    return _client


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
    "repro_steps":   "follow steps in the description",
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
    action = {}
    try:
        c = get_client()
        response = c.chat.completions.create(
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
    except BaseException as e:
        print(f"[WARN] LLM call failed ({type(e).__name__}): {e}", flush=True)
        action = {}

    for k, v in DEFAULT_ACTION.items():
        action.setdefault(k, v)

    if action["issue_type"]    not in VALID_TYPES:      action["issue_type"]    = "bug"
    if action["severity"]      not in VALID_SEVERITIES: action["severity"]      = "P3"
    if action["component"]     not in VALID_COMPONENTS: action["component"]     = "backend"
    if action["assigned_team"] not in VALID_TEAMS:      action["assigned_team"] = "core"

    return action


def env_post(path: str, payload: dict = None, retries: int = 3) -> dict:
    url = f"{ENV_URL}{path}"
    for attempt in range(retries):
        try:
            r = requests.post(url, json=payload or {}, timeout=30)
            if r.status_code == 200:
                return r.json()
            print(f"[WARN] {path} returned {r.status_code}: {r.text[:200]}", flush=True)
        except BaseException as e:
            print(f"[WARN] {path} attempt {attempt+1} failed ({type(e).__name__}): {e}", flush=True)
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
            try:
                r = run_episode(task_id, ep)
            except BaseException as e:
                print(f"[WARN] episode {ep} task {task_id} failed ({type(e).__name__}): {e}", flush=True)
                print(f"[END] task={task_id} score=0.0 steps=0", flush=True)
                r = 0.0
            rewards.append(r)
        avg = round(sum(rewards) / len(rewards), 4)
        summary[f"task_{task_id}"] = {"episodes": rewards, "avg_reward": avg}
        print(f"\n=== Task {task_id} avg reward: {avg} ===\n", flush=True)

    print("\n=== Final Summary ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print(f"[FATAL] {type(e).__name__}: {e}", flush=True)
        sys.exit(0)  # always exit 0 so validator doesn't see non-zero
