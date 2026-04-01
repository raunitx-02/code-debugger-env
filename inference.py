"""
inference.py — Baseline inference script for Code Debugger OpenEnv environment.

Mandatory environment variables:
  API_BASE_URL  — LLM API endpoint
  MODEL_NAME    — Model identifier
  HF_TOKEN      — Hugging Face / API key

Uses OpenAI Client for all LLM calls.
Runtime must be under 20 minutes.
Runs on machine with vcpu=2, memory=8gb.
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
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "dummy")
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


def start_local_server():
    """Start the FastAPI environment server as a background process."""
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(5)
    return proc


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


def run_episode(llm: OpenAI, env_sync) -> dict:
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

    best_score = 0.0
    total_attempts = 0

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
            print(f"    [LLM ERROR] {e}")
            response_text = ""

        action = parse_llm_action(response_text)
        print(f"    Attempt {attempt}: bug_line={action.get('bug_line')}, bug_type={action.get('bug_type')}")

        try:
            result = env_sync.step(action)
            obs = result.observation if hasattr(result, 'observation') else result
            reward = (
                result.reward if hasattr(result, 'reward') and result.reward is not None
                else (obs.get("reward") if isinstance(obs, dict) else getattr(obs, "reward", 0.0)) or 0.0
            )
            done_after = (
                result.done if hasattr(result, 'done')
                else (obs.get("done", False) if isinstance(obs, dict) else getattr(obs, "done", False))
            )
        except Exception as e:
            print(f"    [STEP ERROR] {e}")
            break

        if reward > best_score:
            best_score = reward

        total_attempts = attempt
        print(f"    Score: {reward:.3f} (best: {best_score:.3f}) | done: {done_after}")

        if done_after or best_score >= 0.95:
            break

    return {
        "task_id": task_id,
        "difficulty": difficulty,
        "best_score": best_score,
        "attempts": total_attempts,
    }


def main():
    print("=" * 65)
    print("  Code Debugger Environment — Baseline Inference Script")
    print("=" * 65)
    print(f"  LLM endpoint : {API_BASE_URL}")
    print(f"  Model        : {MODEL_NAME}")
    print(f"  Environment  : {ENV_BASE_URL}")
    print("=" * 65)

    server_proc = None
    if "localhost" in ENV_BASE_URL or "127.0.0.1" in ENV_BASE_URL:
        # Only start if not already running
        import urllib.request as _ur
        try:
            _ur.urlopen(ENV_BASE_URL + "/health", timeout=2)
            print("Environment server already running — skipping start.\n")
        except Exception:
            print("\nStarting local environment server (port 7860)...")
            server_proc = start_local_server()
            print("Server started.\n")

    llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env_sync = GenericEnvClient(base_url=ENV_BASE_URL).sync()

    results = []
    start_time = time.time()

    print(f"Running {NUM_EPISODES} episodes...\n")

    with env_sync:
        for ep_num in range(1, NUM_EPISODES + 1):
            print(f"[Episode {ep_num}/{NUM_EPISODES}]")
            ep_result = run_episode(llm_client, env_sync)
            results.append(ep_result)
            print(f"  → {ep_result['task_id']:15s} | {ep_result['difficulty']:6s} | score: {ep_result['best_score']:.3f} | attempts: {ep_result['attempts']}\n")

    elapsed = time.time() - start_time

    by_diff = {"easy": [], "medium": [], "hard": []}
    for r in results:
        d = r.get("difficulty", "easy")
        if d in by_diff:
            by_diff[d].append(r["best_score"])

    overall_avg = sum(r["best_score"] for r in results) / len(results) if results else 0

    print("=" * 65)
    print("  BASELINE RESULTS")
    print("=" * 65)
    for r in results:
        print(f"  {r['task_id']:15s} | {r['difficulty']:6s} | {r['best_score']:.3f}")
    print("-" * 65)
    for diff in ["easy", "medium", "hard"]:
        scores = by_diff[diff]
        if scores:
            print(f"  {diff.capitalize()} average:    {sum(scores)/len(scores):.3f}")
    print(f"  Overall average:  {overall_avg:.3f}")
    print(f"  Total runtime:    {elapsed:.1f}s")
    print("=" * 65)

    assert elapsed < 1200, f"FAIL: runtime {elapsed:.0f}s exceeds 20-minute limit"
    print("\nAll checks passed. Submission ready!")

    if server_proc:
        server_proc.terminate()


if __name__ == "__main__":
    main()
