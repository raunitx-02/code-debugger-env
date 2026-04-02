"""
inference.py — Baseline inference script for Code Debugger OpenEnv environment.

Mandatory environment variables:
  API_BASE_URL  — LLM API endpoint
  MODEL_NAME    — Model identifier
  HF_TOKEN      — Hugging Face / API key

Uses OpenAI Client for all LLM calls.
Runtime must be under 20 minutes.
Runs on machine with vcpu=2, memory=8gb.

Structured log format (required by hackathon evaluator):
  [START] {"episode": N, "task_id": "...", "difficulty": "..."}
  [STEP]  {"episode": N, "step": M, "action": {...}, "reward": F, "done": B}
  [END]   {"episode": N, "task_id": "...", "difficulty": "...", "best_score": F, "total_attempts": N}
  [SUMMARY] {"total_episodes": N, "overall_avg": F, ...}
"""
import os
import json
import time
import sys
import subprocess
import re

from openai import OpenAI
from openenv.core import GenericEnvClient

# ── Configuration ─────────────────────────────────────────────────
# Provider priority:
#   1. GROQ (free) : set GROQ_API_KEY  → uses api.groq.com
#   2. Custom      : set API_BASE_URL + API_KEY
#   3. HF Router   : set HF_TOKEN      → uses router.huggingface.co
GROQ_KEY     = os.getenv("GROQ_API_KEY", "")
HF_TOKEN     = os.getenv("HF_TOKEN", "")

if GROQ_KEY:
    API_BASE_URL = os.getenv("API_BASE_URL") or "https://api.groq.com/openai/v1"
    API_KEY      = GROQ_KEY
    MODEL_NAME   = os.getenv("MODEL_NAME") or "llama-3.1-8b-instant"
elif os.getenv("API_BASE_URL"):
    API_BASE_URL = os.getenv("API_BASE_URL")
    API_KEY      = os.getenv("API_KEY") or HF_TOKEN or "dummy"
    MODEL_NAME   = os.getenv("MODEL_NAME") or "meta-llama/Llama-3.1-8B-Instruct"
else:
    API_BASE_URL = "https://router.huggingface.co/v1"
    API_KEY      = HF_TOKEN or "dummy"
    MODEL_NAME   = os.getenv("MODEL_NAME") or "meta-llama/Llama-3.1-8B-Instruct"

ENV_BASE_URL = os.getenv("ENV_BASE_URL") or "http://localhost:7860"
MAX_ATTEMPTS = 3
NUM_EPISODES = 9

SYSTEM_PROMPT = """You are an expert Python debugger and security researcher.

You will receive a Python code snippet containing exactly one bug.

Your task:
1. Find the exact line number of the bug (count ALL lines from 1, including blank lines and comments)
2. Classify the bug type as EXACTLY one of: syntax | logic | runtime | security
3. Write the COMPLETE corrected function(s) — not just the fix, the entire code snippet

RESPOND WITH ONLY A VALID JSON OBJECT — no explanation text, no markdown, no code blocks:
{
  "bug_line": <integer>,
  "bug_type": "<syntax|logic|runtime|security>",
  "fixed_code": "<complete corrected Python code as a single string>",
  "explanation": "<one sentence describing what the bug was>"
}"""


# ── Structured log helpers ─────────────────────────────────────────
def log(tag: str, payload: dict):
    """Emit a structured log line: [TAG] {json}"""
    # Ensure all floats are rounded to 4 decimal places
    def round_floats(obj):
        if isinstance(obj, float):
            return round(obj, 4)
        if isinstance(obj, dict):
            return {k: round_floats(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [round_floats(v) for v in obj]
        return obj

    print(f"[{tag}] {json.dumps(round_floats(payload), separators=(',', ':'))}", flush=True)


def log_start(episode: int, task_id: str, difficulty: str):
    log("START", {"episode": episode, "task_id": task_id, "difficulty": difficulty})


def log_step(episode: int, step: int, action: dict, reward: float, done: bool):
    log("STEP", {
        "episode": episode,
        "step": step,
        "action": {
            "bug_line": action.get("bug_line", 1),
            "bug_type": action.get("bug_type", "logic"),
        },
        "reward": reward,
        "done": done,
    })


def log_end(episode: int, task_id: str, difficulty: str, best_score: float, total_attempts: int):
    log("END", {
        "episode": episode,
        "task_id": task_id,
        "difficulty": difficulty,
        "best_score": best_score,
        "total_attempts": total_attempts,
    })


def log_summary(total_episodes: int, overall_avg: float, easy_avg: float,
                medium_avg: float, hard_avg: float, runtime_seconds: float):
    log("SUMMARY", {
        "total_episodes": total_episodes,
        "overall_avg": overall_avg,
        "easy_avg": easy_avg,
        "medium_avg": medium_avg,
        "hard_avg": hard_avg,
        "runtime_seconds": runtime_seconds,
    })


# ── Server helper ──────────────────────────────────────────────────
def start_local_server():
    """Start the FastAPI environment server as a background process."""
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(5)
    return proc


# ── LLM helpers ───────────────────────────────────────────────────
def parse_llm_action(response_text: str) -> dict:
    """Parse LLM JSON response. Handles malformed responses gracefully."""
    if not response_text:
        return {"bug_line": 1, "bug_type": "logic", "fixed_code": "", "explanation": "empty response"}

    text = response_text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {
        "bug_line": 1,
        "bug_type": "logic",
        "fixed_code": "",
        "explanation": "JSON parse failed — fallback action",
    }


# ── Episode runner ─────────────────────────────────────────────────
def run_episode(llm: OpenAI, env_sync, episode_num: int) -> dict:
    """Run one complete episode: reset → up to 3 step() calls → return result."""
    result = env_sync.reset()
    obs = result.observation if hasattr(result, 'observation') else result

    task_id = "unknown"
    difficulty = "unknown"
    try:
        state = env_sync.state()
        state_dict = state if isinstance(state, dict) else (state.dict() if hasattr(state, 'dict') else {})
        task_id = state_dict.get("task_id", "unknown")
        difficulty = state_dict.get("difficulty", "unknown")
    except Exception:
        pass

    # Try to get task_id/difficulty from observation metadata if not in state
    if task_id == "unknown":
        try:
            meta = obs.get("metadata", {}) if isinstance(obs, dict) else getattr(obs, "metadata", {})
            task_id = meta.get("task_id", "unknown")
            difficulty = meta.get("difficulty", "unknown")
        except Exception:
            pass

    best_score = 0.0
    total_attempts = 0

    # ── [START] ────────────────────────────────────────────────────
    log_start(episode_num, task_id, difficulty)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if isinstance(obs, dict):
            done = obs.get("done", False)
            code = obs.get("code_snippet", "")
            task_desc = obs.get("task_description", "")
            hint = obs.get("test_hint", "")
            feedback = obs.get("feedback", "")
            score_so_far = obs.get("score_so_far", 0.0)
        else:
            done = getattr(obs, "done", False)
            code = getattr(obs, "code_snippet", "")
            task_desc = getattr(obs, "task_description", "")
            hint = getattr(obs, "test_hint", "")
            feedback = getattr(obs, "feedback", "")
            score_so_far = getattr(obs, "score_so_far", 0.0)

        if done:
            break

        user_msg = f"""Task description: {task_desc}

Test requirements: {hint}

Attempt {attempt}/{MAX_ATTEMPTS} | Score so far: {score_so_far:.2f}

Code to debug (line numbers start at 1):
```python
{code}
```"""

        if feedback:
            user_msg += f"\n\nFeedback from previous attempt:\n{feedback}"

        try:
            completion = llm.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
                max_tokens=800,
                stream=False,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as e:
            sys.stderr.write(f"[LLM_ERROR] episode={episode_num} step={attempt} error={e}\n")
            sys.stderr.flush()
            response_text = ""

        action = parse_llm_action(response_text)

        try:
            step_result = env_sync.step(action)
            obs = step_result.observation if hasattr(step_result, 'observation') else step_result
            reward = (
                step_result.reward if hasattr(step_result, 'reward') and step_result.reward is not None
                else (obs.get("reward") if isinstance(obs, dict) else getattr(obs, "reward", 0.0)) or 0.0
            )
            done_after = (
                step_result.done if hasattr(step_result, 'done')
                else (obs.get("done", False) if isinstance(obs, dict) else getattr(obs, "done", False))
            )
        except Exception as e:
            sys.stderr.write(f"[STEP_ERROR] episode={episode_num} step={attempt} error={e}\n")
            sys.stderr.flush()
            reward = 0.0
            done_after = True

        if reward > best_score:
            best_score = reward

        total_attempts = attempt

        # ── [STEP] ────────────────────────────────────────────────
        log_step(episode_num, attempt, action, float(reward), bool(done_after))

        if done_after or best_score >= 0.95:
            break

    # ── [END] ─────────────────────────────────────────────────────
    log_end(episode_num, task_id, difficulty, best_score, total_attempts)

    return {
        "task_id": task_id,
        "difficulty": difficulty,
        "best_score": best_score,
        "attempts": total_attempts,
    }


# ── Main ───────────────────────────────────────────────────────────
def main():
    sys.stderr.write(f"Code Debugger — Baseline Inference\n")
    sys.stderr.write(f"LLM: {API_BASE_URL} / {MODEL_NAME}\n")
    sys.stderr.write(f"ENV: {ENV_BASE_URL}\n")
    sys.stderr.flush()

    server_proc = None
    if "localhost" in ENV_BASE_URL or "127.0.0.1" in ENV_BASE_URL:
        import urllib.request as _ur
        try:
            _ur.urlopen(ENV_BASE_URL + "/health", timeout=2)
            sys.stderr.write("Environment server already running — skipping start.\n")
            sys.stderr.flush()
        except Exception:
            sys.stderr.write("Starting local environment server (port 7860)...\n")
            sys.stderr.flush()
            server_proc = start_local_server()
            sys.stderr.write("Server started.\n")
            sys.stderr.flush()

    llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env_sync = GenericEnvClient(base_url=ENV_BASE_URL).sync()

    results = []
    start_time = time.time()

    with env_sync:
        for ep_num in range(1, NUM_EPISODES + 1):
            ep_result = run_episode(llm_client, env_sync, ep_num)
            results.append(ep_result)

    elapsed = time.time() - start_time

    # ── Compute averages ───────────────────────────────────────────
    by_diff = {"easy": [], "medium": [], "hard": []}
    for r in results:
        d = r.get("difficulty", "easy")
        if d in by_diff:
            by_diff[d].append(r["best_score"])

    def avg(lst):
        return sum(lst) / len(lst) if lst else 0.0

    overall_avg = avg([r["best_score"] for r in results])
    easy_avg    = avg(by_diff["easy"])
    medium_avg  = avg(by_diff["medium"])
    hard_avg    = avg(by_diff["hard"])

    # ── [SUMMARY] ─────────────────────────────────────────────────
    log_summary(
        total_episodes=len(results),
        overall_avg=overall_avg,
        easy_avg=easy_avg,
        medium_avg=medium_avg,
        hard_avg=hard_avg,
        runtime_seconds=elapsed,
    )

    assert elapsed < 1200, f"FAIL: runtime {elapsed:.0f}s exceeds 20-minute limit"

    if server_proc:
        server_proc.terminate()


if __name__ == "__main__":
    main()
