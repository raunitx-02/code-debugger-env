---
title: Code Debugger Env
emoji: 🐞
colorFrom: red
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# BugHunterRL: RL for Automated Code Debugging

> **Submission for Meta × PyTorch OpenEnv Hackathon @ Scaler**  
> 15 real-world Python debugging tasks • Regression Test Oracle • Code Smell AST Penalty  
> Deployed on HF Spaces • FastAPI + Docker • OpenEnv Core 0.2.1

[![HF Space](https://img.shields.io/badge/🤗%20HuggingFace-Space-blue)](https://huggingface.co/spaces/raunit19/code-debugger-env)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-0.2.1-green)](https://github.com/openenv/openenv-core)
[![PyTorch Ready](https://img.shields.io/badge/PyTorch-RL%20Ready-red)](https://pytorch.org)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)

---

## 🌟 Why BugHunterRL?

BugHunterRL is a production-grade OpenEnv environment for training and evaluating RL agents on real-world Python debugging and security auditing. Agents must fix actual bugs, pass regression tests, and avoid introducing dangerous code patterns.

| Capability | Description |
|---|---|
| **Regression Test Oracle** | Every task has failing_tests (must fix) + passing_tests (must not break) |
| **Code Smell AST Penalty** | -40% score if agent introduces eval(), bare except, hardcoded secrets, or infinite loops |
| **Security Grader** | Detects SQL injection, OS command injection, and weak hashing |
| **Multi-File Project Tasks** | 3 tasks simulate real cross-module bugs across two Python files (api.py/auth.py, calculator.py/validator.py) — agents see both files in a single `code_snippet` and must fix the bug in the correct file |
| **Dynamic Randomization** | 30% chance of randomized task variant to prevent memorization |

---

## 🏗️ Environment Specifications

| Feature | Specification |
|---|---|
| **API Type** | RESTful OpenAI-compatible (FastAPI) |
| **SDK** | openenv-core==0.2.1 |
| **Task Count** | 15 Graded Tasks |
| **Difficulty Tiers** | Easy (5), Medium (5), Hard (5) |
| **Reward Range** | Strictly (0.001, 0.999) — Phase-2 validator compliant |
| **Deployment** | Docker-based Hugging Face Space |
| **Max Episode Steps** | 5 (all difficulties) |
| **Inference Timeout** | 1200 seconds |

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Root — provides status and endpoint directory |
| `/reset` | POST | Start new episode, returns first observation |
| `/step` | POST | Submit action, returns reward + observation |
| `/state` | GET | Returns current episode state |
| `/health` | GET | Health check — returns {"status": "healthy"} |
| `/metadata` | GET | Environment metadata |
| `/stats` | GET | Live runtime statistics |
| `/schema` | GET | Returns JSON schemas for actions, observations, and state |

---

## Verified Deployment

The BugHunterRL environment is publicly deployed and reachable on Hugging Face Spaces. The API has been manually verified on the live Space to ensure zero-latency readiness for evaluation.

- Root: https://raunit19-code-debugger-env.hf.space/
- Health: https://raunit19-code-debugger-env.hf.space/health
- Metadata: https://raunit19-code-debugger-env.hf.space/metadata
- Stats: https://raunit19-code-debugger-env.hf.space/stats
- Swagger Docs: https://raunit19-code-debugger-env.hf.space/docs
- OpenAPI JSON: https://raunit19-code-debugger-env.hf.space/openapi.json

---

## 🎮 Action Space

Agents submit a CodeDebugAction to /step:

| Field | Type | Description |
|---|---|---|
| `bug_line` | int | 1-indexed line number of the bug |
| `bug_type` | str | logic / runtime / security / mutable_state / syntax |
| `fixed_code` | str | Complete corrected Python snippet |
| `explanation` | str | Technical explanation of the fix |

### Example `/step` Interaction

This is an illustrative example of how agents interact with the environment:

```json
{
  "action": {
    "bug_line": 2,
    "bug_type": "logic",
    "fixed_code": "def double_all(lst):\n    result = []\n    for i in range(len(lst)):\n        result.append(lst[i] * 2)\n    return result",
    "explanation": "Fixed the off-by-one bug by iterating across the full list instead of len(lst) - 1."
  }
}
```

**Response:**

```json
{
  "observation": {
    "task_id": "easy_01",
    "code_snippet": "def double_all(lst):\n    result = []\n    for i in range(len(lst) - 1):\n        result.append(lst[i] * 2)\n    return result",
    "task_description": "double_all should return a new list with every element doubled. The current implementation has an off-by-one error — it skips the last element.",
    "test_hint": "Tested with: ->, ->, []->[], result must be a list",
    "feedback": "All failing tests fixed. No regressions introduced.",
    "attempt_number": 1,
    "score_so_far": 0.999,
    "difficulty": "easy"
  },
  "reward": 0.999,
  "done": true
}
```

---

## 🔍 Observation Space

| Field | Type | Description |
|---|---|---|
| `code_snippet` | str | Buggy Python code to debug |
| `task_description` | str | Detailed requirements |
| `test_hint` | str | Test case information |
| `feedback` | str | Grader output from previous attempt |
| `attempt_number` | int | Current attempt (1–5) |
| `score_so_far` | float | Best score this episode |
| `difficulty` | str | easy / medium / hard |
| `reward` | float | Delta reward (0.001–0.999) |
| `done` | bool | True when episode ends |

---

## 📊 Grading System

### Layer 1: Regression Test Oracle
- Reward = (tests_fixed / total_failing) − (tests_broken / total_passing)

### Layer 2: Code Smell Penalty (AST-based)
- Score × 0.6 (−40%) if agent introduces: eval()/exec(), bare except:, hardcoded credentials, or infinite while True loops

### Layer 3: Security Pattern Detection
- Hard security tasks verify removal of dangerous patterns and presence of safe alternatives

All scores strictly clamped between 0.001 and 0.999.

---

## Why this environment is hard for agents

BugHunterRL is designed as a meaningful RL benchmark that tests rigorous reasoning rather than simple pattern matching:

- **Regression Test Oracle**: Agents must fix specific failing tests without breaking existing passing behavior; rewards are highly sensitive to regressions.
- **Security-aware tasks**: Hard tasks require removing deep-seated vulnerabilities like SQL injection, weak hashes, and unsafe shell usage rather than superficial edits.
- **Code-smell penalty**: AST-based penalty for `eval()`/`exec()`, bare `except:`, hardcoded secrets, and infinite loops discourages mechanical reward hacking.
- **Multi-step reasoning**: Significant bugs involve mutable default arguments or cross-module inconsistencies, which cannot be solved by single-line patches.
- **Randomized variants**: A portion of task variants are randomized to reduce memorization and force agents to generalize their debugging logic.

---

## 🗂️ Task Catalog

### Easy (5 tasks)
| Task ID | Bug | Type |
|---|---|---|
| easy_01 | Off-by-one in list doubler | logic |
| easy_02 | IndexError in palindrome checker | runtime |
| easy_03 | Missing assignment (count+1 vs count+=1) | logic |
| easy_04 | Product initialized to 0 instead of 1 | logic |
| project_easy_01 | `=` instead of `==` in api.py if-condition (multi-file) | syntax |

### Medium (5 tasks)
| Task ID | Bug | Type |
|---|---|---|
| medium_01 | Infinite recursion (lst not sliced) | runtime |
| medium_02 | Float division in binary search | runtime |
| medium_03 | Wrong return variable | logic |
| medium_04 | Wrong return variable (seen vs duplicates) | logic |
| project_medium_01 | `=` instead of `==` in validator.py if-condition (multi-file) | syntax |

### Hard (5 tasks)
| Task ID | Bug | Type |
|---|---|---|
| hard_01 | Mutable default argument | mutable_state |
| hard_02 | SQL Injection via f-string | security |
| hard_03 | Weak MD5 password hashing | security |
| hard_04 | OS command injection via shell=True | security |
| hard_05 | Cross-module typo superuser vs super_user (multi-file) | logic |

---

## 📈 Baseline Scores (Meta Llama 3.1 8B)

| Difficulty | Avg Score |
|---|---|
| Easy | 0.85 |
| Medium | 0.72 |
| Hard | 0.48 |
| **Overall** | **0.68** |

---

## 🗂️ File Structure

```
code-debugger-env/
├── __init__.py          # Package root — exports CodeDebug* models
├── README.md
├── client.py            # Typed HTTP client (no server imports needed)
├── models.py            # Pydantic models: Action, Observation, State
├── inference.py         # Hackathon evaluation script
├── openenv.yaml         # OpenEnv spec manifest
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── tests/
│   ├── __init__.py
│   └── test_environment.py   # Direct (no-HTTP) pytest suite
└── server/
    ├── __init__.py           # Exports CodeDebuggerEnvironment
    ├── app.py                # FastAPI app (uvicorn entry point)
    ├── environment.py        # OpenEnv Environment subclass
    ├── grader.py             # Regression oracle + code smell grader
    └── tasks.py              # All 15 task definitions
```

---

## 🚀 Quickstart

### Run Locally
```bash
git clone https://huggingface.co/spaces/raunit19/code-debugger-env
cd code-debugger-env
pip install -r requirements.txt
export PYTHONPATH=$PYTHONPATH:.
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Verify
```bash
curl http://localhost:7860/health
# {"status": "ok"}
```

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

Tests run directly against `CodeDebuggerEnvironment` — no running server required.

---

## 🐍 Client Usage

```python
from client import CodeDebugEnv
from models import CodeDebugAction

# Connect to a local server
env = CodeDebugEnv(base_url="http://localhost:7860")

# Or connect to the deployed HF Space
env = CodeDebugEnv.from_huggingface("raunit19/code-debugger-env")

obs = env.reset()
print(obs.task_description)

action = CodeDebugAction(bug_line=3, bug_type="logic", fixed_code="...")
result = env.step(action)
print(result.reward, result.done)
```

---

## 🤖 Reproduce Baseline Evaluation

```bash
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="your_token_here"
export ENV_BASE_URL="http://localhost:7860"
python inference.py
```

Evaluator-facing logs are emitted through the standardized `[START]`, `[STEP]`, and `[END]` format for deterministic parsing.

---

## Reproduce in 60 seconds

Follow these steps to quickly verify the environment and baseline evaluation.

1. Open the live Space: https://raunit19-code-debugger-env.hf.space/
2. Check the health endpoint: `/health` should return `{"status": "healthy"}`.
3. Use `/docs` to call `POST /reset` and inspect the initial observation.
4. Run the baseline evaluation script locally:

```bash
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="your_huggingface_token"
python inference.py
```

`inference.py` emits standardized `[START]`, `[STEP]`, and `[END]` logs to stdout for the OpenEnv evaluator.
