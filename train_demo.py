"""
train_demo.py — Demonstrates agent improvement through feedback.

Shows how the feedback field in BugTriageObservation enables an agent to learn
from mistakes across episodes. Uses the OpenAI client with accumulated feedback
as in-context learning signal.

This is a few-shot learning demonstration, not full RL training.
For full RL training integration, see: https://huggingface.co/docs/trl/en/openenv

Usage:
    ENV_URL=http://localhost:7860 API_KEY=your-key python train_demo.py
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

TASK_ID        = 3
NUM_EPISODES   = 3
TASK_MAX_STEPS = 3

VALID_TYPES      = {"bug", "feature", "question"}
VALID_SEVERITIES = {"P1", "P2", "P3", "P4"}
VALID_COMPONENTS = {"frontend", "backend", "infra", "database", "mobile"}
VALID_TEAMS      = {"core", "platform", "devops", "mobile"}

DEFAULT_ACTION = {
    "issue_type": "bug", "severity": "P3", "component": "backend",
    "assigned_team": "core",
    "repro_steps": "reproduce as described",
    "is_duplicate": False, "duplicate_of": "",
}

_client = None


def get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    return _client


def env_post(path, payload=None, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(f"{ENV_URL}{path}", json=payload or {}, timeout=30)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"  [WARN] {path} attempt {attempt+1}: {e}", flush=True)
        time.sleep(1)
    return {}


def wait_for_server(timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests.get(f"{ENV_URL}/health", timeout=5).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def call_llm(obs: dict, accumulated_feedback: list) -> dict:
    """Call LLM with accumulated feedback from prior episodes as context."""
    feedback_context = ""
    if accumulated_feedback:
        feedback_context = (
            "\n\nLearning from previous episodes:\n" +
            "\n".join(f"  - {fb}" for fb in accumulated_feedback[-5:])
        )

    current_feedback = obs.get("feedback", "")
    if current_feedback and current_feedback != "All fields correct.":
        feedback_context += f"\n\nFeedback on your last action: {current_feedback}"

    system_prompt = (
        "You are a senior engineering manager performing bug triage. "
        "Read the FULL description — titles can be misleading. "
        "Respond with raw JSON only, no markdown, no explanation."
        + feedback_context
    )

    user_prompt = (
        f"Issue ID: {obs.get('issue_id', '')}\n"
        f"Title: {obs.get('title', '')}\n"
        f"Description:\n{obs.get('description', '')}\n"
    )

    existing = obs.get("existing_issues", [])
    if existing:
        user_prompt += "\nExisting issues (check for duplicates):\n"
        for ex in existing[:10]:
            user_prompt += f"  [{ex['issue_id']}] {ex['title']}: {ex.get('description','')[:100]}\n"

    user_prompt += (
        '\nRespond with:\n'
        '{"issue_type":"bug|feature|question","severity":"P1|P2|P3|P4",'
        '"component":"frontend|backend|infra|database|mobile",'
        '"assigned_team":"core|platform|devops|mobile",'
        '"repro_steps":"<steps>","is_duplicate":false,"duplicate_of":""}'
    )

    action = {}
    try:
        r = get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=512,
        )
        raw = r.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        action = json.loads(raw)
    except Exception as e:
        print(f"  [WARN] LLM error: {e}", flush=True)

    for k, v in DEFAULT_ACTION.items():
        action.setdefault(k, v)
    if action.get("issue_type")    not in VALID_TYPES:      action["issue_type"]    = "bug"
    if action.get("severity")      not in VALID_SEVERITIES: action["severity"]      = "P3"
    if action.get("component")     not in VALID_COMPONENTS: action["component"]     = "backend"
    if action.get("assigned_team") not in VALID_TEAMS:      action["assigned_team"] = "core"
    if not isinstance(action.get("is_duplicate"), bool):    action["is_duplicate"]  = False
    if not isinstance(action.get("duplicate_of"),  str):    action["duplicate_of"]  = ""
    return action


def run_episode(episode: int, accumulated_feedback: list) -> tuple:
    """Run one episode, collecting feedback from wrong decisions."""
    print(f"\n{'='*50}", flush=True)
    print(
        f"Episode {episode + 1} / {NUM_EPISODES}  "
        f"(feedback items from prior episodes: {len(accumulated_feedback)})",
        flush=True,
    )
    print(f"{'='*50}", flush=True)

    # seed=0 → static dataset, consistent across episodes so improvement is comparable
    obs = env_post("/reset", {"task_id": TASK_ID, "seed": 0})
    if not obs:
        print("  [ERROR] Reset failed", flush=True)
        return 0.001, []

    total_reward = 0.0
    step_count   = 0
    new_feedback = []

    for _ in range(TASK_MAX_STEPS * 8):   # 8 issues × 3 steps max
        if obs.get("issue_id") == "DONE":
            break

        action   = call_llm(obs, accumulated_feedback)
        result   = env_post("/step", {"action": action})
        if not result:
            break

        reward   = float(result.get("reward", 0.0))
        done     = bool(result.get("done", False))
        next_obs = result.get("observation", {})
        step_count  += 1
        total_reward += reward

        # Collect feedback for next episode's context
        feedback = next_obs.get("feedback", "")
        if feedback and feedback != "All fields correct." and feedback not in accumulated_feedback:
            issue_title = obs.get("title", "unknown issue")
            new_feedback.append(f"On '{issue_title[:50]}': {feedback}")

        has_fb = feedback and feedback != "All fields correct."
        print(
            f"  Step {step_count:2d} | issue={obs.get('issue_id','?'):8s} | "
            f"reward={reward:.3f} | feedback={'yes' if has_fb else 'none'}",
            flush=True,
        )

        obs = next_obs
        if done:
            break

    score = round(max(0.001, min(0.999, total_reward)), 4)
    print(f"\n  Episode {episode + 1} score: {score:.4f}", flush=True)
    return score, new_feedback


def main():
    print("Bug Triage Environment — RL Training Demo", flush=True)
    print("Shows agent improvement via feedback across episodes\n", flush=True)

    if not wait_for_server(60):
        print("[FATAL] Server not ready", flush=True)
        sys.exit(0)

    accumulated_feedback: list = []
    episode_scores: list = []

    for episode in range(NUM_EPISODES):
        score, new_feedback = run_episode(episode, accumulated_feedback)
        episode_scores.append(score)
        accumulated_feedback.extend(new_feedback)

    print(f"\n{'='*50}", flush=True)
    print("LEARNING CURVE", flush=True)
    print(f"{'='*50}", flush=True)
    for i, score in enumerate(episode_scores):
        bar = "\u2588" * int(score * 30)
        print(f"  Episode {i+1}: {score:.4f} {bar}", flush=True)

    if len(episode_scores) >= 2:
        improvement = episode_scores[-1] - episode_scores[0]
        direction = "improved" if improvement > 0 else "declined"
        print(
            f"\n  Total {direction}: {improvement:+.4f} "
            f"({episode_scores[0]:.4f} \u2192 {episode_scores[-1]:.4f})",
            flush=True,
        )
        print(f"  Feedback items accumulated: {len(accumulated_feedback)}", flush=True)

    print(f"\n{'='*50}", flush=True)
    print("The feedback field enables this within-context learning.", flush=True)
    print("For full RL training (GRPO/PPO), see:", flush=True)
    print("  https://huggingface.co/docs/trl/en/openenv", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] {type(e).__name__}: {e}", flush=True)
        sys.exit(0)
