---
title: Python Code Debugger OpenEnv Environment
emoji: 🐛
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
tags:
  - openenv
  - code-review
  - debugging
version: "1.0.0"
author: "raunit19"
license: "mit"
---

# Python Code Debugger — OpenEnv Environment

Code review and security auditing cost the software industry billions annually.
This OpenEnv environment trains AI agents on real-world Python debugging — from
simple runtime errors to critical security vulnerabilities like SQL injection and
unsafe eval(). Unlike text-matching evaluators, every score is computed by
**executing the agent's fixed code** against real test cases in a sandboxed
subprocess — making rewards fully deterministic and impossible to game.

---

## Overview

Code review and debugging are among the most valuable real-world developer tasks. This environment trains and evaluates agents on a realistic debugging workflow:

1. Agent receives a Python code snippet with exactly one planted bug
2. Agent identifies bug location, classifies it, and submits a complete fix
3. Grader executes the fixed code against real test cases in a subprocess sandbox
4. Feedback is returned so the agent can retry (up to 3 attempts per episode)

Security vulnerability detection (SQL injection, weak hashing, unsafe eval) is in the hard tier — directly useful for training code-safety agents.

---

## Action Space

| Field | Type | Description |
|---|---|---|
| `bug_line` | int (>=1) | 1-indexed line number of the bug |
| `bug_type` | str | Exactly one of: syntax, logic, runtime, security |
| `fixed_code` | str | Complete corrected Python code (whole snippet) |
| `explanation` | str | One sentence about the bug (optional) |

---

## Observation Space

| Field | Type | Description |
|---|---|---|
| `code_snippet` | str | Python code with one bug |
| `task_description` | str | What the function should do correctly |
| `test_hint` | str | Description of grading test cases |
| `feedback` | str | Grader feedback from previous attempt |
| `attempt_number` | int | Current attempt (1-3) |
| `score_so_far` | float | Best score so far this episode |
| `done` | bool | True when episode ends |
| `reward` | float | Score for the most recent step |

---

## Reward Function

```
reward = min(1.0,
    (tests_passed / total_tests) * 0.75
  + 0.15  if abs(bug_line - correct_line) <= 2
  + 0.10  if bug_type == correct_bug_type
)
```

Partial credit is intentional — an agent that locates the bug correctly but fixes it imperfectly still gets a useful training signal.

---

## Tasks

| Task ID | Difficulty | Bug Type | Description |
|---|---|---|---|
| easy_01 | Easy | logic | Off-by-one error in list doubler |
| easy_02 | Easy | runtime | IndexError in palindrome checker |
| easy_03 | Easy | logic | Assignment error in vowel counter (count + 1 not stored) |
| easy_04 | Easy | logic | Product initialized to 0 instead of 1 in multiply_list |
| medium_01 | Medium | logic | Infinite recursion in recursive_sum |
| medium_02 | Medium | runtime | Integer division error in binary search |
| medium_03 | Medium | logic | Nested return instead of flat result in list flattener |
| medium_04 | Medium | logic | Returns `seen` instead of `duplicates` in find_duplicates |
| hard_01 | Hard | logic | Mutable default argument in class constructor |
| hard_02 | Hard | security | SQL injection via f-string — use parameterized queries |
| hard_03 | Hard | security | MD5 password hashing — replace with SHA-256 |
| hard_04 | Hard | security | OS command injection via shell=True subprocess |

---

## Episode Structure

- Max 3 attempts per episode
- Grader feedback returned after each step so agent can improve
- Episode ends early if score >= 0.95
- Best score across all attempts is the final episode reward

---

## Baseline Scores

| Difficulty | Avg Score | Notes |
|---|---|---|
| Easy | 1.00 | Solved reliably by feedback-driven loops |
| Medium | 1.00 | Complex logic bugs handled via test-case feedback |
| Hard | 0.70 | Security and isolation bugs challenge smaller models |
| Overall | 0.91 | Exceeds hackathon baseline requirements |

Baseline run with `meta-llama/Llama-3.1-8B-Instruct`. 
The environment provides clear signal for training stronger code-security agents.

---

## Quick Start

```python
from openenv_core.env_client import GenericEnvClient

env = GenericEnvClient(base_url="http://localhost:7860").sync()

with env:
    # Start a new episode
    result = env.reset()
    obs = result.observation
    print(obs["code_snippet"])      # buggy Python code
    print(obs["task_description"])  # what it should do
    print(obs["test_hint"])         # what tests will check

    # Submit your fix
    action = {
        "bug_line": 5,
        "bug_type": "runtime",
        "fixed_code": "def calculate_average(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)",
        "explanation": "Added empty list guard to prevent ZeroDivisionError"
    }
    result = env.step(action)
    print(f"Score: {result.reward}")       # 0.0 - 1.0
    print(f"Done: {result.done}")
    print(f"Feedback: {result.observation['feedback']}")
```

---

## Setup

```bash
pip install openenv-core fastapi uvicorn pydantic openai
python app.py

# Docker
docker build -t code-debugger-env .
docker run -p 7860:7860 code-debugger-env

# Validate
openenv validate .

# Run baseline inference
API_BASE_URL="https://router.huggingface.co/v1" \
HF_TOKEN="your_token" \
MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct" \
python inference.py
```

---

## Design Notes

Execution-based grading prevents agents from gaming the system with syntactically correct but logically broken fixes. Every score is fully reproducible — run the same fixed_code against the same test cases and you always get the same score.

## Limitations

- Single-function snippets only — does not cover multi-file bugs
- Security grading uses pattern matching plus code execution, not formal verification

## Why This Matters

Code review and security auditing are among the most expensive tasks in software engineering. Developers who miss SQL injection vulnerabilities, weak password hashing (MD5), unsafe eval(), or OS command injection expose organizations to breaches costing millions. This environment trains AI agents on the exact bug classes responsible for the majority of real-world CVEs — making it one of the most practically impactful RL training environments in the OpenEnv ecosystem.

## Architecture
┌─────────────────────────────────────────────────────────────┐
│ HuggingFace Space │
│ ┌──────────────┐ POST /reset ┌──────────────────────┐ │
│ │ inference │ ─────────────► │ CodeDebugger │ │
│ │ (LLM agent) │ │ Environment │ │
│ │ │ ◄───────────── │ (environment.py) │ │
│ │ │ observation │ │ │
│ │ │ POST /step │ ┌────────────────┐ │ │
│ │ │ ─────────────► │ │ grader.py │ │ │
│ │ │ ◄───────────── │ │ Regression │ │ │
│ │ │ reward+done │ │ Oracle + │ │ │
│ └──────────────┘ │ │ Code Smell │ │ │
│ │ │ Penalty │ │ │
│ │ └────────────────┘ │ │
│ └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

**Key Design Decisions:**
- **Execution-based grading** — fixed code is actually run against test cases, not pattern-matched
- **Regression Test Oracle** — both failing tests (must fix) and passing tests (must not break) are checked
- **Code Smell Penalty** — 40% score reduction for `eval()`, `exec()`, `shell=True`, hardcoded secrets
- **Multi-turn with feedback** — agent gets grader output after each step and can retry
- **Difficulty tiers** — Easy (logic/runtime bugs), Medium (algorithm bugs), Hard (security vulnerabilities)

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HF_TOKEN` | (required) | HuggingFace API token for LLM access |
| `API_BASE_URL` | `https://router.huggingface.co/v1` | OpenAI-compatible inference endpoint |
| `MODEL_NAME` | `meta-llama/Llama-3.1-8B-Instruct` | Model to use for inference |
| `ENV_BASE_URL` | `http://localhost:7860` | URL of the running environment server |
