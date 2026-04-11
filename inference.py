"""
Baseline inference script — Bug Triage OpenEnv.

Log format (validator-required, do not change):
  [START] task=<int> episode=<int>
  [STEP]  step=<int> reward=<float> done=<true|false>
  [END]   task=<int> score=<float> steps=<int>
"""

import os
import sys
import json
import time
import signal
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
API_KEY      = os.environ.get("API_KEY") or os.environ.get("HF_TOKEN", "no-key")
MODEL_NAME   = os.environ.get("MODEL_NAME", "gpt-4o-mini")
ENV_URL      = os.environ.get("ENV_URL", "http://localhost:7860")

# Reduced to keep total LLM calls at 20: 5*1 + 3*2 + 3*3 = 20
EPISODES_PER_TASK = {1: 5, 2: 3, 3: 3}
TASK_MAX_STEPS    = {1: 1, 2: 2, 3: 3}
SUCCESS_THRESHOLD = 0.7

VALID_TYPES      = {"bug", "feature", "question"}
VALID_SEVERITIES = {"P1", "P2", "P3", "P4"}
VALID_COMPONENTS = {"frontend", "backend", "infra", "database", "mobile"}
VALID_TEAMS      = {"core", "platform", "devops", "mobile"}

DEFAULT_ACTION = {
    "issue_type": "bug", "severity": "P3", "component": "backend",
    "assigned_team": "core",
    "repro_steps": "reproduce as described in the issue",
    "is_duplicate": False, "duplicate_of": "",
}

_client = None


def get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    return _client


SYSTEM_PROMPT = (
    "You are a senior engineering manager performing bug triage. "
    "Read the FULL description carefully — the title may be misleading. "
    "If existing_issues or episode_history are provided, check for duplicates. "
    "Respond with raw JSON only, no markdown."
)


def build_prompt(obs: dict) -> str:
    lines = [
        f"Issue ID: {obs.get('issue_id', '')}",
        f"Title: {obs.get('title', '')}",
        f"Description:\n{obs.get('description', '')}",
    ]
    history = obs.get("episode_history", [])
    if history:
        lines.append("\nYour triage history this episode:")
        for h in history:
            lines.append(
                f"  [{h['issue_id']}] {h['title']} → "
                f"{h.get('agent_type','?')}/{h.get('agent_severity','?')}/{h.get('agent_component','?')}"
            )
    existing = obs.get("existing_issues", [])
    if existing:
        lines.append("\nExisting issues (check for duplicates):")
        for ex in existing[:15]:
            lines.append(f"  [{ex['issue_id']}] {ex['title']}: {ex.get('description','')[:120]}")
    lines.append(
        '\nRespond with exactly:\n'
        '{"issue_type":"bug|feature|question","severity":"P1|P2|P3|P4",'
        '"component":"frontend|backend|infra|database|mobile",'
        '"assigned_team":"core|platform|devops|mobile",'
        '"repro_steps":"<numbered steps>","is_duplicate":false,"duplicate_of":""}'
    )
    return "\n".join(lines)


def call_llm(obs: dict) -> dict:
    action = {}
    try:
        r = get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_prompt(obs)},
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
        print(f"[WARN] LLM error: {e}", flush=True)

    for k, v in DEFAULT_ACTION.items():
        action.setdefault(k, v)
    if action.get("issue_type")    not in VALID_TYPES:      action["issue_type"]    = "bug"
    if action.get("severity")      not in VALID_SEVERITIES: action["severity"]      = "P3"
    if action.get("component")     not in VALID_COMPONENTS: action["component"]     = "backend"
    if action.get("assigned_team") not in VALID_TEAMS:      action["assigned_team"] = "core"
    if not isinstance(action.get("is_duplicate"), bool):    action["is_duplicate"]  = False
    if not isinstance(action.get("duplicate_of"),  str):    action["duplicate_of"]  = ""
    return action


def env_post(path, payload=None, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(f"{ENV_URL}{path}", json=payload or {}, timeout=30)
            if r.status_code == 200:
                return r.json()
            print(f"[WARN] {path} → {r.status_code}", flush=True)
        except Exception as e:
            print(f"[WARN] {path} attempt {attempt+1}: {e}", flush=True)
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


def run_episode(task_id: int, episode: int) -> float:
    print(f"[START] task={task_id} episode={episode}", flush=True)
    obs = env_post("/reset", {"task_id": task_id, "seed": episode})
    if not obs:
        print(f"[END]   task={task_id} score=0.001 steps=0", flush=True)
        return 0.001

    total_reward, step_count = 0.0, 0
    for _ in range(TASK_MAX_STEPS[task_id]):
        action = call_llm(obs)
        result = env_post("/step", {"action": action})
        if not result:
            break
        reward     = float(result.get("reward", 0.0))
        done       = bool(result.get("done", False))
        obs        = result.get("observation", obs)
        step_count += 1
        total_reward += reward
        print(f"[STEP]  step={step_count} reward={round(reward,4)} done={'true' if done else 'false'}", flush=True)
        if done:
            break

    score = round(max(0.001, min(0.999, total_reward)), 4)
    print(f"[END]   task={task_id} score={score} steps={step_count}", flush=True)
    return score


def main():
    print("[INFO] Waiting for environment server...", flush=True)
    if not wait_for_server(60):
        print("[FATAL] Server not ready.", flush=True)
        sys.exit(0)

    summary = {}
    for task_id in [1, 2, 3]:
        rewards = []
        for ep in range(EPISODES_PER_TASK[task_id]):
            try:
                r = run_episode(task_id, ep)
            except Exception as e:
                print(f"[WARN] ep={ep} task={task_id}: {e}", flush=True)
                print(f"[END]   task={task_id} score=0.001 steps=0", flush=True)
                r = 0.001
            rewards.append(r)
        avg          = round(sum(rewards) / len(rewards), 4)
        success_rate = round(sum(1 for r in rewards if r >= SUCCESS_THRESHOLD) / len(rewards), 4)
        summary[f"task_{task_id}"] = {
            "episodes": rewards, "avg_reward": avg, "success_rate": success_rate,
        }
        print(f"\n=== Task {task_id} | avg={avg} | success_rate={success_rate} ===\n", flush=True)

    try:
        metrics = requests.get(f"{ENV_URL}/metrics", timeout=10).json()
        summary["live_metrics"] = metrics
    except Exception:
        pass

    print("\n=== Final Summary ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)


def _timeout_handler(signum, frame):
    print("[WARN] Global 18-minute timeout reached — printing partial summary.", flush=True)
    raise SystemExit(0)


if __name__ == "__main__":
    # SIGALRM only available on Unix — guard for Windows
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(18 * 60)
    try:
        main()
    except SystemExit:
        pass
    except Exception as e:
        print(f"[FATAL] {type(e).__name__}: {e}", flush=True)
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
