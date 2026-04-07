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
> 13 real-world Python debugging tasks • Regression Test Oracle • Code Smell AST Penalty  
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
| **Multi-File Simulation** | Hard tasks simulate cross-module dependency bugs |
| **Dynamic Randomization** | 30% chance of randomized task variant to prevent memorization |

---

## 🏗️ Environment Specifications

| Feature | Specification |
|---|---|
| **API Type** | RESTful OpenAI-compatible (FastAPI) |
| **SDK** | openenv-core==0.2.1 |
| **Task Count** | 13 Graded Tasks |
| **Difficulty Tiers** | Easy (4), Medium (4), Hard (5) |
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
| `/health` | GET | Health check — returns {"status": "ok"} |
| `/metadata` | GET | Environment metadata |
| `/stats` | GET | Live runtime statistics |

---

## 🎮 Action Space

Agents submit a CodeDebugAction to /step:

| Field | Type | Description |
|---|---|---|
| `bug_line` | int | 1-indexed line number of the bug |
| `bug_type` | str | logic / runtime / security / mutable_state / syntax |
| `fixed_code` | str | Complete corrected Python snippet |
| `explanation` | str | Technical explanation of the fix |

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

## 🗂️ Task Catalog

### Easy (4 tasks)
| Task ID | Bug | Type |
|---|---|---|
| easy_01 | Off-by-one in list doubler | logic |
| easy_02 | IndexError in palindrome checker | runtime |
| easy_03 | Missing assignment (count+1 vs count+=1) | logic |
| easy_04 | Product initialized to 0 instead of 1 | logic |

### Medium (4 tasks)
| Task ID | Bug | Type |
|---|---|---|
| medium_01 | Infinite recursion (lst not sliced) | runtime |
| medium_02 | Float division in binary search | runtime |
| medium_03 | Wrong return variable | logic |
| medium_04 | Wrong return variable | logic |

### Hard (5 tasks)
| Task ID | Bug | Type |
|---|---|---|
| hard_01 | Mutable default argument | mutable_state |
| hard_02 | SQL Injection via f-string | security |
| hard_03 | Weak MD5 password hashing | security |
| hard_04 | OS command injection via shell=True | security |
| hard_05 | Cross-module typo superuser vs super_user | logic |

---

## 📈 Baseline Scores (Meta Llama 3.1 8B)

| Difficulty | Avg Score |
|---|---|
| Easy | 0.85 |
| Medium | 0.72 |
| Hard | 0.48 |
| **Overall** | **0.68** |

---

## 🚀 Quickstart

### Run Locally
```bash
git clone https://huggingface.co/spaces/raunit19/code-debugger-env
cd code-debugger-env
pip install -r requirements.txt
export PYTHONPATH=$PYTHONPATH:.
python server/app.py
```

### Verify
```bash
curl http://localhost:7860/health
# {"status": "ok"}
```

---

## 🤖 Reproduce Baseline Evaluation

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="your_token_here"
export ENV_BASE_URL="http://localhost:7860"
python inference.py
```
