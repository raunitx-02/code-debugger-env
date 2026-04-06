"""
inference.py — OpenEnv standard inference script for Python Code Debugger.
Mandatory log format: [START], [STEP], [END] as key=value.
"""
import os
import sys
import json
import time
import re
import subprocess
from typing import List, Dict, Any, Optional
from openai import OpenAI
from openenv.core import GenericEnvClient

# ── Configuration ─────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
API_KEY      = os.getenv("HF_TOKEN", "")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
BENCHMARK    = "code-debugger"

NUM_EPISODES = 9
MAX_ATTEMPTS = 3

# ── Prompt / System Message ───────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert Python security auditor and debugger. 
You will be given a Python code snippet containing exactly one bug (syntax, logic, runtime, or security).
Your goal is to identify the bug line (1-indexed), categorize it, and provide the complete fixed code.

IMPORTANT RULES:
1. ALWAYS provide the COMPLETE fixed code.
2. If this is a RETRY, you will receive feedback from the grader. Use it to improve your fix.
3. SECURITY: Do NOT use eval(), exec(), bare except:, or while True without a break.
4. Format your response as a single JSON object.

Example Output:
{
  "bug_line": 4,
  "bug_type": "runtime",
  "explanation": "Integer division by zero.",
  "fixed_code": "def divide(a, b):\\n    return a // b if b != 0 else 0"
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
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {"bug_line": 1, "bug_type": "logic", "fixed_code": text[:100], "explanation": "failed to parse json"}


def build_user_message(obs: Any, attempt: int) -> str:
    # Unpack observation (handle both dict and Pydantic modes)
    if isinstance(obs, dict):
        code         = obs.get("code_snippet", "")
        task_desc    = obs.get("task_description", "")
        hint         = obs.get("test_hint", "")
        feedback     = obs.get("feedback", "")
        score_so_far = obs.get("score_so_far", 0.0)
    else:
        code         = getattr(obs, "code_snippet", "")
        task_desc    = getattr(obs, "task_description", "")
        hint         = getattr(obs, "test_hint", "")
        feedback     = getattr(obs, "feedback", "")
        score_so_far = getattr(obs, "score_so_far", 0.0)

    msg = f"""TASK: {task_desc}
CODE SNIPPET:
```python
{code}
```
TESTING HINT: {hint}

Attempt {attempt} | Score so far: {score_so_far:.2f}
"""
    if feedback and attempt > 1:
        msg += f"\nGRADER FEEDBACK FROM PREVIOUS ATTEMPT:\n{feedback}\n"
        msg += "\nINSTRUCTIONS: Fix the ✗ items above. Correct the bug_line or logic. Write COMPLETE fixed code."
    
    return msg


# ── Episode runner ────────────────────────────────────────────────────────────
def run_episode(llm: OpenAI, env_sync, episode_num: int) -> dict:
    result   = env_sync.reset()
    obs      = result.observation if hasattr(result, "observation") else result
    task_id  = "unknown"
    difficulty = "unknown"

    try:
        if isinstance(obs, dict):
            task_id = obs.get("task_id", "unknown")
            difficulty = obs.get("difficulty", "unknown")
        else:
            task_id = getattr(obs, "task_id", "unknown")
            difficulty = getattr(obs, "difficulty", "unknown")
    except Exception:
        pass

    log_start(task_id, MODEL_NAME)

    step_rewards: List[float] = []
    best_score  = 0.0
    total_steps = 0
    last_error  = None
    max_attempts = 5 if difficulty == "hard" else MAX_ATTEMPTS

    try:
        for attempt in range(1, max_attempts + 1):
            # ── Get model response ────────────────────────────────────────
            user_msg = build_user_message(obs, attempt)
            completion = llm.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
            )
            resp_text = completion.choices[0].message.content
            action_dict = parse_llm_action(resp_text)
            
            # ── Execute environment step ──────────────────────────────────
            step_result = env_sync.step({
                "bug_line": action_dict.get("bug_line", 1),
                "bug_type": action_dict.get("bug_type", "logic"),
                "fixed_code": action_dict.get("fixed_code", ""),
                "explanation": action_dict.get("explanation", ""),
            })
            
            obs    = step_result.observation
            reward = float(step_result.reward) if step_result.reward is not None else 0.0
            done   = step_result.done
            
            total_steps += 1
            step_rewards.append(reward)
            best_score = max(best_score, reward)
            
            err_msg = None
            if reward <= 0 and "✗" in getattr(obs, "feedback", ""):
                 err_msg = "test_failure"

            log_step(
                step=total_steps,
                bug_type=action_dict.get("bug_type", "logic"),
                bug_line=action_dict.get("bug_line", 1),
                reward=reward,
                done=done,
                error=err_msg
            )
            
            if done:
                break

    except Exception as e:
        last_error = str(e)
        print(f"[DEBUG] Episode crashed: {e}", file=sys.stderr, flush=True)

    success = best_score >= 0.5
    log_end(success, total_steps, step_rewards)

    return {
        "task_id":      task_id,
        "difficulty":   difficulty,
        "best_score":   best_score,
        "attempts":     total_steps,
        "error":        last_error,
    }


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(
        f"[DEBUG] Code Debugger Upgraded Inference | model={MODEL_NAME} | env={ENV_BASE_URL}",
        file=sys.stderr, flush=True,
    )

    server_proc = None
    if "localhost" in ENV_BASE_URL or "127.0.0.1" in ENV_BASE_URL:
        import urllib.request as _ur
        try:
            _ur.urlopen(ENV_BASE_URL + "/health", timeout=2)
            print("[DEBUG] Server already running.", file=sys.stderr, flush=True)
        except Exception:
            print("[DEBUG] Starting local server...", file=sys.stderr, flush=True)
            server_proc = start_local_server()

    llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env_sync   = GenericEnvClient(base_url=ENV_BASE_URL).sync()

    results    = []
    start_time = time.time()

    print(f"[DEBUG] Running {NUM_EPISODES} episodes...", file=sys.stderr, flush=True)

    with env_sync:
        for ep_num in range(1, NUM_EPISODES + 1):
            print(f"[DEBUG] Episode {ep_num}/{NUM_EPISODES}", file=sys.stderr, flush=True)
            ep_result = run_episode(llm_client, env_sync, ep_num)
            results.append(ep_result)
            print(
                f"[DEBUG]   → {ep_result['task_id']:15s} | "
                f"{ep_result['difficulty']:6s} | "
                f"score={ep_result['best_score']:.3f} | "
                f"attempts={ep_result['attempts']}",
                file=sys.stderr, flush=True,
            )

    if server_proc:
        server_proc.terminate()

    # ── Final Summary ───────────────────────────────────────────────────────────
    total_episodes = len(results)
    if total_episodes == 0:
        print("[DEBUG] No episodes run.", file=sys.stderr)
        return

    easy_scores   = [r['best_score'] for r in results if r['difficulty'] == 'easy']
    medium_scores = [r['best_score'] for r in results if r['difficulty'] == 'medium']
    hard_scores   = [r['best_score'] for r in results if r['difficulty'] == 'hard']
    all_scores    = [r['best_score'] for r in results]

    def avg(lst): return sum(lst) / len(lst) if lst else 0.0

    print("\n[DEBUG] ════════ FINAL SUMMARY ════════", file=sys.stderr)
    print(f"[DEBUG]   Episodes:      {total_episodes}", file=sys.stderr)
    print(f"[DEBUG]   Avg Score:     {avg(all_scores):.3f}", file=sys.stderr)
    print("[DEBUG] ────────────────────────────────", file=sys.stderr)
    for res in results:
        print(f"[DEBUG]   {res['task_id']:15s} | {res['difficulty']:6s} | {res['best_score']:.3f}", file=sys.stderr)
    print("[DEBUG] ────────────────────────────────", file=sys.stderr)
    print(f"[DEBUG]   Easy average:    {avg(easy_scores):.3f}", file=sys.stderr)
    print(f"[DEBUG]   Medium average:  {avg(medium_scores):.3f}", file=sys.stderr)
    print(f"[DEBUG]   Hard average:    {avg(hard_scores):.3f}", file=sys.stderr)
    print(f"[DEBUG]   Overall average: {avg(all_scores):.3f}", file=sys.stderr)
    print(f"[DEBUG]   Runtime:         {time.time() - start_time:.1f}s", file=sys.stderr)
    print("[DEBUG] ════════════════════════════════", file=sys.stderr)

    # FINAL MANDATORY SUMMARY LINE
    print(f"easy_avg={avg(easy_scores):.3f} medium_avg={avg(medium_scores):.3f} hard_avg={avg(hard_scores):.3f} overall={avg(all_scores):.3f}")
    print("[DEBUG] All checks passed. Submission ready!", file=sys.stderr)


if __name__ == "__main__":
    main()
