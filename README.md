---
title: Code Debugger Env
emoji: 🐞
colorFrom: red
colorTo: indigo
sdk: docker
pinned: false
---

# BugHunterRL: Reinforcement Learning for Automated Code Debugging

**BugHunterRL (code-debugger-env)** is a production-grade OpenEnv environment designed for training and evaluating RL agents on real-world Python debugging and security auditing tasks. It provides a high-fidelity playground for agents to identify logic flaws, resolve runtime errors, and mitigate critical security vulnerabilities.

---

## 🌟 Why This Matters for Meta × PyTorch

BugHunterRL is built for the next generation of **Automated Software Engineering (ASE)** and **AI-Assisted Programming** research.

*   **PyTorch Integration**: Highly optimized for high-throughput RL training loops using PyTorch-based frameworks like `torchrl` or `StableBaselines3`.
*   **Llama-Family Benchmarking**: Specifically designed to evaluate the reasoning capabilities of **Meta Llama 3.1** models in identifying subtle security "sinks" (SQLi, Command Injection) and complex logic bugs.
*   **Real-World Logic Simulation**: Our "Hard" tasks simulate project-level dependencies and "Code Smells," rewarding agents that produce clean, production-safe code.

---

## 🏗️ Environment Specifications

| Feature | Specification |
| :--- | :--- |
| **API Type** | RESTful OpenAI-compatible (FastAPI) |
| **SDK Compatibility** | `openenv-core>=0.2.1` |
| **Task Count** | 13 Graded Tasks |
| **Difficulty Tiers** | Easy, Medium, Hard |
| **Grading Logic** | Deterministic Regression Oracle + Security Pattern Detection |
| **Reward Range** | Strictly (0.001, 0.999) |
| **Deployment** | Docker-based Hugging Face Space |

---

## 🎮 Action Space

Agents interact with the environment by submitting a `CodeDebugAction` (Pydantic Model) to the `/step` endpoint.

| Field | Type | Description |
| :--- | :--- | :--- |
| `bug_line` | `int` | The 1-indexed line number where the bug resides. |
| `bug_type` | `str` | Category (`logic`, `runtime`, `security`). |
| `fixed_code` | `str` | THE COMPLETE corrected Python snippet. |
| `explanation` | `str` | A concise technical explanation of the fix. |

---

## 🔍 Observation Space

The environment returns a `CodeDebugObservation` after every `reset()` or `step()`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `code_snippet` | `str` | The buggy Python code to be audited. |
| `task_description`| `str` | Detailed requirements and expected behavior. |
| `test_hint` | `str` | Information about the test cases used for grading. |
| `feedback` | `str` | Grader output from the previous attempt (on `step()`). |
| `score_so_far` | `float` | Best score achieved in the current episode. |
| `difficulty` | `str` | Task complexity (`easy`, `medium`, `hard`). |
| `reward` | `float` | Delta reward for the latest action. |
| `done` | `bool` | True when the episode has ended. |

---

## 📊 Evaluation & Reward Logic

BugHunterRL uses a multi-layered grading system to ensure agent reliability:

1.  **Regression Oracle**: Rewards agents for fixing `failing_tests` while subtractively penalizing them for breaking `passing_tests`.
2.  **Security Grader**: Hard security tasks use regex-based pattern detection to verify the removal of dangerous sinks (e.g., `shell=True`) and the use of parameterized queries.
3.  **Code Smell Penalty**: AST-based layer subtracts 40% of the score if the agent introduces dangerous patterns like `eval()`, `exec()`, or bare `except: pass`.
4.  **Range Compliance**: All scores are strictly clamped between **0.001 and 0.999** for Phase-2 validator compliance.

---

## 🛠️ Task Design

The environment features 13 tasks across three difficulty levels:
*   **Easy**: Logic bugs such as off-by-one errors and indexing flaws.
*   **Medium**: Algorithmic challenges including infinite recursion and list flattening.
*   **Hard**: Critical security vulnerabilities (SQL Injection, Weak Hashing) and **Multi-File Logic Simulations** involving cross-module dependency bugs.

---

## 🚀 Quickstart

### 1. Installation
```bash
git clone https://huggingface.co/spaces/raunit19/code-debugger-env
cd code-debugger-env
pip install -r requirements.txt
```

### 2. Run Local Server
```bash
export PYTHONPATH=$PYTHONPATH:.
python server/app.py
```

---

## 🤖 Reproduce Baseline

Our baseline uses the required OpenAI-compatible client to evaluate **Meta Llama 3.1 8B**.

### 1. Environment Variables
```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="your_huggingface_token"
export ENV_BASE_URL="http://localhost:7860" # Local or Space URL
```

### 2. Execute Inference
The `inference.py` script produces structured logs to `stdout` for the Phase-2 evaluator.
```bash
python inference.py
```
**Logging Compliance:** The script outputs structured sequences of `[START]`, `[STEP]`, and `[END]` with 4-decimal precision for deterministic validator parsing.

---

## 📂 Repository Layout

*   `server/app.py`: FastAPI entry point with enriched `/metadata` and `/stats`.
*   `environment.py`: Core OpenEnv logic with session management.
*   `models.py`: Hardened Pydantic v2 data models.
*   `grader.py`: Multi-layer regression oracle and security grader.
*   `tasks.py`: Catalog of 13 debugging challenges.
*   `inference.py`: Standardized agent evaluation script.
*   `openenv.yaml`: OpenEnv manifest with observation and task schemas.

---

Generated for the **Meta × PyTorch OpenEnv Hackathon @ Scaler**.
Developer: [raunit19](https://huggingface.co/raunit19)
