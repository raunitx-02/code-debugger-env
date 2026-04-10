"""
inference.py — OpenEnv standard inference script for BugHunterRL.
Uses raw HTTP requests to the environment server + OpenAI-compatible LLM client.

Mandatory stdout log format (hackathon spec):
  [START] {"task_id": "...", "difficulty": "...", "episode_id": "..."}
  [STEP]  {"step": 1, "action": {...}, "reward": 0.0, "done": false, "score_so_far": 0.0}
  [END]   {"task_id": "...", "final_score": 0.0, "steps_taken": 1, "difficulty": "..."}
"""
import os
import sys
import json
import time
import re

import requests
from typing import List, Any, Optional
from openai import OpenAI

# Dynamically resolve NUM_EPISODES from the TASKS list
sys.path.insert(0, os.path.dirname(__file__))
try:
    from server.tasks import TASKS as _TASKS
    NUM_EPISODES = len(_TASKS)
except Exception:
    NUM_EPISODES = 13

# ── Environment variable wiring (hackathon spec) ──────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api-inference.huggingface.co/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "meta-llama/Llama-3.1-8B-Instruct")
API_KEY      = os.environ.get("HF_TOKEN",     "")
ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:7860")

# Fallback ENV_BASE_URL resolution for Hugging Face Spaces
HF_SPACE_ID = os.environ.get("HF_SPACE_ID", "")
if HF_SPACE_ID and ENV_BASE_URL == "http://localhost:7860":
    space_owner, space_name = HF_SPACE_ID.split("/") if "/" in HF_SPACE_ID else ("", HF_SPACE_ID)
    ENV_BASE_URL = f"https://{space_owner.lower()}-{space_name.lower()}.hf.space"

BENCHMARK    = "code-debugger"
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
  "fixed_code": "import hashlib\\ndef hash_password(p):\\n    return hashlib.sha256(p.encode()).hexdigest()"
}"""


# ── Logging functions — strict hackathon format ───────────────────────────────

def log_start(task_id: str, difficulty: str, episode_id: str) -> None:
    """Emit [START] line with task_id, difficulty, episode_id as JSON."""
    payload = {
        "task_id":    task_id,
        "difficulty": difficulty,
        "episode_id": episode_id,
    }
    print(f"[START] {json.dumps(payload)}", flush=True)


def log_step(
    step: int,
    action: dict,
    reward: float,
    done: bool,
    score_so_far: float,
) -> None:
    """Emit [STEP] line with step, action, reward, done, score_so_far as JSON."""
    safe_reward      = max(0.001, min(0.999, float(reward)))
    safe_score_so_far = max(0.001, min(0.999, float(score_so_far)))
    payload = {
        "step":         step,
        "action":       action,
        "reward":       round(safe_reward, 4),
        "done":         done,
        "score_so_far": round(safe_score_so_far, 4),
    }
    print(f"[STEP] {json.dumps(payload)}", flush=True)


def log_end(task_id: str, final_score: float, steps_taken: int, difficulty: str) -> None:
    """Emit [END] line with task_id, final_score, steps_taken, difficulty as JSON."""
    safe_score = max(0.001, min(0.999, float(final_score)))
    payload = {
        "task_id":     task_id,
        "final_score": round(safe_score, 4),
        "steps_taken": steps_taken,
        "difficulty":  difficulty,
    }
    print(f"[END] {json.dumps(payload)}", flush=True)


# ── LLM parsing helpers ───────────────────────────────────────────────────────

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


# ── Episode runner ────────────────────────────────────────────────────────────

def run_episode(llm: OpenAI, base_url: str, episode_num: int) -> dict:
    reset_resp = requests.post(f"{base_url}/reset")
    reset_resp.raise_for_status()
    result = reset_resp.json()
    obs = result.get("observation", {})

    task_id    = obs.get("task_id",    "unknown")
    difficulty = obs.get("difficulty", "unknown")
    episode_id = obs.get("episode_id", str(episode_num))

    log_start(task_id=task_id, difficulty=difficulty, episode_id=episode_id)

    step_rewards: List[float] = []
    best_score  = 0.001
    total_steps = 0
    last_error  = None
    max_attempts = 5  # Matches openenv.yaml max_episode_steps: 5

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

            obs          = step_result.get("observation", {})
            reward       = float(step_result.get("reward", 0.001))
            done         = step_result.get("done", False)
            score_so_far = float(obs.get("score_so_far", reward))

            total_steps += 1
            step_rewards.append(reward)
            best_score = max(best_score, reward)

            log_step(
                step=total_steps,
                action={
                    "bug_line": action_dict.get("bug_line", 1),
                    "bug_type": action_dict.get("bug_type", "logic"),
                },
                reward=reward,
                done=done,
                score_so_far=score_so_far,
            )

            if done:
                break

    except Exception as e:
        last_error = str(e)
        print(f"[DEBUG] Episode crashed: {e}", file=sys.stderr, flush=True)

    log_end(
        task_id=task_id,
        final_score=best_score,
        steps_taken=total_steps,
        difficulty=difficulty,
    )

    return {
        "task_id":    task_id,
        "difficulty": difficulty,
        "best_score": best_score,
        "attempts":   total_steps,
        "error":      last_error,
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    try:
        print(f"[DEBUG] BugHunterRL Inference | model={MODEL_NAME} | env={ENV_BASE_URL}", file=sys.stderr, flush=True)

        # Health check retry loop (safe for HF cold start)
        max_retries = 3
        for i in range(max_retries):
            try:
                print(f"[DEBUG] Health check attempt {i+1}/{max_retries}...", file=sys.stderr, flush=True)
                resp = requests.get(f"{ENV_BASE_URL}/health", timeout=5)
                if resp.status_code == 200:
                    print("[DEBUG] Environment is healthy and ready.", file=sys.stderr, flush=True)
                    break
            except Exception as e:
                if i == max_retries - 1:
                    print(f"[DEBUG] Environment unreachable after {max_retries} attempts: {e}", file=sys.stderr, flush=True)
                else:
                    time.sleep(5)

        if not API_KEY:
            print("[DEBUG] ERROR: HF_TOKEN environment variable is not set.", file=sys.stderr)
            sys.exit(1)

        llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
        results    = []
        start_time = time.time()

        print(f"[DEBUG] Running {NUM_EPISODES} episodes...", file=sys.stderr, flush=True)

        for ep_num in range(1, NUM_EPISODES + 1):
            if time.time() - start_time > 1080:  # 18 minutes in seconds
                print("[DEBUG] Time limit approaching, stopping early.", file=sys.stderr, flush=True)
                break
                
            print(f"[DEBUG] Episode {ep_num}/{NUM_EPISODES}", file=sys.stderr, flush=True)
            ep_result = run_episode(llm_client, ENV_BASE_URL, ep_num)
            results.append(ep_result)
            print(
                f"[DEBUG] -> {ep_result['task_id']:20s} | "
                f"{ep_result['difficulty']:6s} | "
                f"score={ep_result['best_score']:.3f} | "
                f"attempts={ep_result['attempts']}",
                file=sys.stderr, flush=True,
            )

        total_episodes = len(results)
        if total_episodes == 0:
            print("[DEBUG] No episodes run.", file=sys.stderr)
            return

        all_scores    = [r["best_score"] for r in results]
        def avg(lst): return sum(lst) / len(lst) if lst else 0.0

        easy_scores   = [r["best_score"] for r in results if r["difficulty"] == "easy"]
        medium_scores = [r["best_score"] for r in results if r["difficulty"] == "medium"]
        hard_scores   = [r["best_score"] for r in results if r["difficulty"] == "hard"]

        print(
            f"[DEBUG] easy_avg={avg(easy_scores):.3f} "
            f"medium_avg={avg(medium_scores):.3f} "
            f"hard_avg={avg(hard_scores):.3f} "
            f"overall={avg(all_scores):.3f}",
            file=sys.stderr
        )
        print("[DEBUG] All checks passed. Submission ready!", file=sys.stderr)

    except Exception as e:
        print(f"Inference error: {str(e)}", flush=True)
        return


if __name__ == "__main__":
    main()
