"""
inference.py — Baseline inference script for Code Debugger OpenEnv environment.

Mandatory environment variables:
  API_BASE_URL  — LLM API endpoint
  MODEL_NAME    — Model identifier
  HF_TOKEN      — Hugging Face / API key

STDOUT FORMAT (mandatory):
  [START] task=<task_id> env=code-debugger model=<model>
  [STEP] step=<n> action=<bug_type>:line<bug_line> reward=<0.00> done=<true|false> error=<msg|null>
  [END] success=<true|false> steps=<n> rewards=<r1,r2,...>
"""
import os
import json
import time
import sys
import subprocess
import re
from typing import List, Optional

from openai import OpenAI
from openenv.core import GenericEnvClient

# ── Configuration ──────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "dummy")
MODEL_NAME   = os.getenv("MODEL_NAME") or "meta-llama/Llama-3.1-8B-Instruct"
ENV_BASE_URL = os.getenv("ENV_BASE_URL") or "http://localhost:7860"
BENCHMARK    = "code-debugger"
MAX_ATTEMPTS = 3
NUM_EPISODES = 9
SUCCESS_THRESHOLD = 0.5

SYSTEM_PROMPT = """You are an expert Python debugger and security researcher.

You will receive a Python code snippet containing exactly one bug.

Your task:
1. Find the exact line number of the bug (count ALL lines from 1, including blank lines)
2. Classify the bug type as EXACTLY one of: syntax | logic | runtime | security
3. Write the COMPLETE corrected function(s) — not just the fix, the entire code snippet

RESPOND WITH ONLY A VALID JSON OBJECT — no explanation text, no markdown, no code blocks:
{
  "bug_line": <integer>,
  "bug_type": "<syntax|logic|runtime|security>",
  "fixed_code": "<complete corrected Python code as a single string>",
  "explanation": "<one sentence describing what the bug was>"
}"""

# ── Mandatory log helpers ───────────────────────────────────────────

def log_start(task_id: str, model: str) -> None:
    print(f"[START] task={task_id} env={BENCHMARK} model={model}", flush=True)

def log_step(step: int, bug_type: str, bug_line: int, reward: float, done: bool, error: Optional[str]) -> None:
    action_str = f"{bug_type}:line{bug_line}"
    error_val  = error if error else "null"
    done_val   = str(done).lower()
    print(f"[STEP] step={step} action={action_str} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}", flush=True)


# ── Server + parsing helpers ────────────────────────────────────────

def start_local_server():
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(5)
    return proc

def parse_llm_action(response_text: str) -> dict:
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
    return {"bug_line": 1, "bug_type": "logic", "fixed_code": "", "explanation": "parse failed"}


# ── Episode runner ──────────────────────────────────────────────────

def run_episode(llm: OpenAI, env_sync, episode_num: int) -> dict:
    result = env_sync.reset()
    obs = result.observation if hasattr(result, 'observation') else result

    task_id    = "unknown"
    difficulty = "unknown"
    try:
        state      = env_sync.state()
        state_dict = state if isinstance(state, dict) else (state.dict() if hasattr(state, 'dict') else {})
        task_id    = state_dict.get("task_id", "unknown")
        difficulty = state_dict.get("difficulty", "unknown")
    except Exception as e:
        print(f"[DEBUG] state() error: {e}", file=sys.stderr, flush=True)

    log_start(task_id=task_id, model=MODEL_NAME)

    step_rewards: List[float] = []
    best_score  = 0.0
    total_steps = 0
    last_error  = None

    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            if isinstance(obs, dict):
                done        = obs.get("done", False)
                code        = obs.get("code_snippet", "")
                task_desc   = obs.get("task_description", "")
                hint        = obs.get("test_hint", "")
                feedback    = obs.get("feedback", "")
                score_so_far = obs.get("score_so_far", 0.0)
            else:
                done        = getattr(obs, "done", False)
                code        = getattr(obs, "code_snippet", "")
                task_desc   = getattr(obs, "task_description", "")
                hint        = getattr(obs, "test_hint", "")
                feedback    = getattr(obs, "feedback", "")
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

            last_error  = None
            step_error  = None

            try:
                completion = llm.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": user_msg},
                    ],
                    temperature=0.1,
                    max_tokens=800,
                    stream=False,
                )
                response_text = completion.choices[0].message.content or ""
            except Exception as e:
                print(f"[DEBUG] LLM error: {e}", file=sys.stderr, flush=True)
                response_text = ""
                last_error    = str(e)[:80]

            action   = parse_llm_action(response_text)
            bug_line = action.get("bug_line", 1)
            bug_type = action.get("bug_type", "logic")

            try:
                step_result = env_sync.step(action)
                obs         = step_result.observation if hasattr(step_result, 'observation') else step_result
                reward      = (
                    step_result.reward if hasattr(step_result, 'reward') and step_result.reward is not None
                    else (obs.get("reward") if isinstance(obs, dict) else getattr(obs, "reward", 0.0)) or 0.0
                )
                done_after  = (
                    step_result.done if hasattr(step_result, 'done')
                    else (obs.get("done", False) if isinstance(obs, dict) else getattr(obs, "done", False))
                )
            except Exception as e:
                print(f"[DEBUG] step() error: {e}", file=sys.stderr, flush=True)
                reward     = 0.0
                done_after = True
                step_error = str(e)[:80]
                last_error = step_error

            step_rewards.append(float(reward))
            total_steps = attempt

            if reward > best_score:
                best_score = reward

            log_step(
                step=attempt,
                bug_type=bug_type,
                bug_line=bug_line,
                reward=float(reward),
                done=bool(done_after),
                error=step_error or last_error,
            )

            if done_after or best_score >= 0.95:
                break

    finally:
        success = best_score >= SUCCESS_THRESHOLD
        log_end(success=success, steps=total_steps, rewards=step_rewards)

    return {
        "task_id":    task_id,
        "difficulty": difficulty,
        "best_score": best_score,
        "attempts":   total_steps,
    }


# ── Main ────────────────────────────────────────────────────────────

def main():
    print(f"[DEBUG] Starting Code Debugger inference | model={MODEL_NAME} | env={ENV_BASE_URL}", file=sys.stderr, flush=True)

    server_proc = None
    if "localhost" in ENV_BASE_URL or "127.0.0.1" in ENV_BASE_URL:
        import urllib.request as _ur
        try:
            _ur.urlopen(ENV_BASE_URL + "/health", timeout=2)
            print("[DEBUG] Server already running — skipping start.", file=sys.stderr, flush=True)
        except Exception:
            print("[DEBUG] Starting local server...", file=sys.stderr, flush=True)
            server_proc = start_local_server()

    llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env_sync   = GenericEnvClient(base_url=ENV_BASE_URL).sync()

    results    = []
    start_time = time.time()

    with env_sync:
        for ep_num in range(1, NUM_EPISODES + 1):
            print(f"[DEBUG] Episode {ep_num}/{NUM_EPISODES}", file=sys.stderr, flush=True)
            ep_result = run_episode(llm_client, env_sync, ep_num)
            results.append(ep_result)

    elapsed = time.time() - start_time

    by_diff = {"easy": [], "medium": [], "hard": []}
    for r in results:
        d = r.get("difficulty", "easy")
        if d in by_diff:
            by_diff[d].append(r["best_score"])

    overall_avg = sum(r["best_score"] for r in results) / len(results) if results else 0.0
    easy_avg    = sum(by_diff["easy"])   / len(by_diff["easy"])   if by_diff["easy"]   else 0.0
    medium_avg  = sum(by_diff["medium"]) / len(by_diff["medium"]) if by_diff["medium"] else 0.0
    hard_avg    = sum(by_diff["hard"])   / len(by_diff["hard"])   if by_diff["hard"]   else 0.0

    print(
        f"easy_avg={easy_avg:.3f} medium_avg={medium_avg:.3f} "
        f"hard_avg={hard_avg:.3f} overall={overall_avg:.3f}",
        file=sys.stderr,
        flush=True,
    )

    assert elapsed < 1200, f"FAIL: runtime {elapsed:.0f}s exceeds 20-minute limit"
    print("[DEBUG] All checks passed. Submission ready!", file=sys.stderr, flush=True)

    if server_proc:
        server_proc.terminate()


if __name__ == "__main__":
    main()
