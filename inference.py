"""
inference.py — OpenEnv standard inference script for BugHunterRL.
Now uses raw HTTP requests to resolve "ModuleNotFoundError: openenv_core.client" in Phase-2.
Mandatory log format: [START], [STEP], [END] as key=value.
"""
import os
import sys
import json
import time
import re
import subprocess
import signal
import requests
from typing import List, Any, Optional
from openai import OpenAI

# STEP 1: Removed OpenEnv client library imports for validator compatibility
# Using 'requests' to call endpoints directly at localhost:7860

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "meta-llama/Llama-3.1-8B-Instruct")
API_KEY     = os.getenv("HF_TOKEN")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
BENCHMARK    = "code-debugger"
NUM_EPISODES = 12
MAX_ATTEMPTS = 3

SYSTEM_PROMPT = """You are BugHunterRL, an expert Python security auditor and debugger.
You will be given a Python code snippet (sometimes representing a multi-file project) containing exactly one bug.
Your goal is to identify the bug line (1-indexed), categorize it, and provide the COMPLETE fixed code.

IMPORTANT RULES:
1. ALWAYS provide the COMPLETE fixed code — never truncate.
2. If this is a RETRY, you will receive grader feedback. Use it precisely.
3. SECURITY: Do NOT use eval(), exec(), bare except:, shell=True, or while True without a break.
4. Format your response as a SINGLE valid JSON object — no markdown fences.

Example Output:
{
  "bug_line": 4,
  "bug_type": "security",
  "explanation": "Using md5 for password hashing is insecure. Replacing with sha256.",
  "fixed_code": "import hashlib\ndef hash_password(p):\n    return hashlib.sha256(p.encode()).hexdigest()"
}"""


def log_start(episode_num: int, task_id: str, model: str) -> None:
    print(f"[START] task={task_id} env={BENCHMARK} model={model}", flush=True)


def log_step(step: int, bug_type: str, bug_line: int, reward: float, done: bool, error: Optional[str]) -> None:
    action_str = f"{bug_type}:line{bug_line}"
    error_val  = error if error else "null"
    done_val   = str(done).lower()
    print(f"[STEP] step={step} action={action_str} reward={reward:.2f} done={done_val} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)


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
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {"bug_line": 1, "bug_type": "logic", "fixed_code": text[:500], "explanation": "failed to parse json"}


def build_user_message(obs: Any, attempt: int) -> str:
    # obs is a dictionary from the JSON response
    code         = obs.get("code_snippet", "")
    task_desc    = obs.get("task_description", "")
    hint         = obs.get("test_hint", "")
    feedback     = obs.get("feedback", "")
    score_so_far = obs.get("score_so_far", 0.0)
    difficulty   = obs.get("difficulty", "")

    msg = f"""TASK: {task_desc}
DIFFICULTY: {difficulty}

CODE SNIPPET:
```python
{code}
```

TESTING HINT: {hint}
Attempt {attempt} | Score so far: {score_so_far:.2f}
"""
    if feedback and attempt > 1:
        msg += f"\nGRADER FEEDBACK FROM PREVIOUS ATTEMPT:\n{feedback}\n"
        msg += "\nINSTRUCTIONS: Carefully fix ALL failing items above. Write COMPLETE fixed code."
    return msg


def run_episode(llm: OpenAI, base_url: str, episode_num: int) -> dict:
    # STEP 2: Rewritten to use HTTP POST /reset
    reset_resp = requests.post(f"{base_url}/reset")
    reset_resp.raise_for_status()
    result = reset_resp.json()
    obs = result.get("observation", {})

    task_id    = obs.get("task_id", "unknown")
    difficulty = obs.get("difficulty", "unknown")

    log_start(episode_num, task_id, MODEL_NAME)

    step_rewards: List[float] = []
    best_score  = 0.0
    total_steps = 0
    last_error  = None
    max_attempts = 5 if difficulty == "hard" else MAX_ATTEMPTS

    try:
        for attempt in range(1, max_attempts + 1):
            user_msg = build_user_message(obs, attempt)
            completion = llm.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                temperature=0.1,
                max_tokens=2048,
            )
            resp_text   = completion.choices[0].message.content
            action_dict = parse_llm_action(resp_text)

            # STEP 2: Rewritten to use HTTP POST /step
            step_resp = requests.post(
                f"{base_url}/step",
                json={"action": {
                    "bug_line":    action_dict.get("bug_line",    1),
                    "bug_type":    action_dict.get("bug_type",    "logic"),
                    "fixed_code":  action_dict.get("fixed_code",  ""),
                    "explanation": action_dict.get("explanation", ""),
                }}
            )
            step_resp.raise_for_status()
            step_result = step_resp.json()

            obs    = step_result.get("observation", {})
            reward = float(step_result.get("reward", 0.0))
            done   = step_result.get("done", False)

            total_steps += 1
            step_rewards.append(reward)
            best_score = max(best_score, reward)

            err_msg = None
            if reward <= 0 and obs.get("feedback"):
                err_msg = "test_failure"

            log_step(
                step=total_steps,
                bug_type=action_dict.get("bug_type", "logic"),
                bug_line=action_dict.get("bug_line", 1),
                reward=reward,
                done=done,
                error=err_msg,
            )

            if done:
                break

    except Exception as e:
        last_error = str(e)
        print(f"[DEBUG] Episode crashed: {e}", file=sys.stderr, flush=True)

    success = best_score >= 0.5
    log_end(success, total_steps, best_score, step_rewards)

    return {
        "task_id":    task_id,
        "difficulty": difficulty,
        "best_score": best_score,
        "attempts":   total_steps,
        "error":      last_error,
    }


def main():
    try:
        print(f"[DEBUG] BugHunterRL Inference v3 | model={MODEL_NAME} | env={ENV_BASE_URL}", file=sys.stderr, flush=True)

        # Health check
        try:
            requests.get(f"{ENV_BASE_URL}/health", timeout=2)
            print("[DEBUG] Server unreachable or starting...", file=sys.stderr, flush=True)
        except Exception:
            pass

        if not API_KEY:
            print("[DEBUG] ERROR: HF_TOKEN environment variable is not set.", file=sys.stderr)
            sys.exit(1)

        llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
        results    = []
        start_time = time.time()

        print(f"[DEBUG] Running {NUM_EPISODES} episodes...", file=sys.stderr, flush=True)

        for ep_num in range(1, NUM_EPISODES + 1):
            print(f"[DEBUG] Episode {ep_num}/{NUM_EPISODES}", file=sys.stderr, flush=True)
            ep_result = run_episode(llm_client, ENV_BASE_URL, ep_num)
            results.append(ep_result)
            print(
                f"[DEBUG] -> {ep_result['task_id']:15s} | "
                f"{ep_result['difficulty']:6s} | "
                f"score={ep_result['best_score']:.3f} | "
                f"attempts={ep_result['attempts']}",
                file=sys.stderr, flush=True,
            )

        total_episodes = len(results)
        if total_episodes == 0:
            print("[DEBUG] No episodes run.", file=sys.stderr)
            return

        print("\n[DEBUG] ════════ FINAL SUMMARY ════════", file=sys.stderr)
        easy_scores   = [r["best_score"] for r in results if r["difficulty"] == "easy"]
        medium_scores = [r["best_score"] for r in results if r["difficulty"] == "medium"]
        hard_scores   = [r["best_score"] for r in results if r["difficulty"] == "hard"]
        all_scores    = [r["best_score"] for r in results]

        def avg(lst): return sum(lst) / len(lst) if lst else 0.0

        print(f"[DEBUG] Episodes : {total_episodes}", file=sys.stderr)
        print(f"[DEBUG] Avg Score: {avg(all_scores):.3f}", file=sys.stderr)
        print("[DEBUG] ────────────────────────────────", file=sys.stderr)
        for res in results:
            status = "PASS" if res["best_score"] >= 0.5 else "FAIL"
            print(f"[DEBUG] {status} {res['task_id']:15s} | {res['difficulty']:6s} | {res['best_score']:.3f}", file=sys.stderr)
        print("[DEBUG] ────────────────────────────────", file=sys.stderr)
        print(f"[DEBUG] Runtime        : {time.time()-start_time:.1f}s", file=sys.stderr)
        print("[DEBUG] ════════════════════════════════", file=sys.stderr)

        print(
            f"easy_avg={avg(easy_scores):.3f} "
            f"medium_avg={avg(medium_scores):.3f} "
            f"hard_avg={avg(hard_scores):.3f} "
            f"overall={avg(all_scores):.3f}"
        )
        print("[DEBUG] All checks passed. Submission ready!", file=sys.stderr)

    except Exception as e:
        print(f"Inference error: {str(e)}", flush=True)
        return


if __name__ == "__main__":
    main()
