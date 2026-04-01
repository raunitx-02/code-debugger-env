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
  - security
  - python
license: mit
---

# Python Code Debugger — OpenEnv Environment

An OpenEnv environment where AI agents identify and fix bugs in Python code.
Covers runtime errors, logic bugs, and security vulnerabilities.
Uses execution-based grading — fixed code is run against real test cases in a sandboxed subprocess.

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

| Task ID | Difficulty | Description | Bug Type |
|---|---|---|---|
| easy_01 | Easy | Average calculator crashes on empty list | runtime |
| easy_02 | Easy | Palindrome checker off-by-one index error | runtime |
| easy_03 | Easy | Vowel counter never increments (count + 1) | logic |
| medium_01 | Medium | Binary search uses / instead of // for mid | logic |
| medium_02 | Medium | Flatten returns nested instead of result | logic |
| medium_03 | Medium | Product initialised to 0 instead of 1 | logic |
| hard_01 | Hard | SQL injection via f-string query | security |
| hard_02 | Hard | MD5 used for password hashing | security |
| hard_03 | Hard | eval() used on user input | security |

---

## Episode Structure

- Max 3 attempts per episode
- Grader feedback returned after each step so agent can improve
- Episode ends early if score >= 0.95
- Best score across all attempts is the final episode reward

---

## Baseline Scores

| Difficulty | Average Score |
|---|---|
| Easy | 0.50 |
| Medium | 0.00 |
| Hard | 0.00 |
| Overall | 0.22 |

*Scores from `Llama-3.1-8B-Instruct` via HF Inference API — easy tasks solved on first attempt, limited by free-tier API credits for remaining episodes.*

---

## Quick Start

```python
from openenv.core import GenericEnvClient

env = GenericEnvClient(base_url="http://localhost:7860").sync()

with env:
    result = env.reset()
    obs = result.observation
    print(obs["code_snippet"])

    action = {
        "bug_line": 5,
        "bug_type": "runtime",
        "fixed_code": "def calculate_average(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)",
        "explanation": "Added empty list guard before division"
    }
    result = env.step(action)
    print(f"Score: {result.reward}")
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
