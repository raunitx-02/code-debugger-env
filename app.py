"""
app.py — FastAPI server for Code Debugger OpenEnv Environment
Runs on port 7860 (required for Hugging Face Spaces).
"""
import uvicorn
import os
from openenv_core.env_server import create_app
from models import CodeDebugAction, CodeDebugObservation
from environment import CodeDebuggerEnvironment
from tasks import TASKS
from fastapi import Request, Response

# Instantiate the environment
env_instance = CodeDebuggerEnvironment()

# FIX 1: Use the built-in OpenEnv app creator (it handles /reset, /step, /state).
app = create_app(
    env_instance,
    CodeDebugAction,
    CodeDebugObservation,
    env_name="code-debugger-env",
)

# Populate app.state for any manual extensions
app.state.env = env_instance

@app.get("/health")
def health():
    """FIX 7: Health check returning simple status: ok."""
    return {"status": "ok"}

@app.get("/openenv.yaml")
def get_openenv_yaml():
    path = os.path.join(os.path.dirname(__file__), "openenv.yaml")
    if not os.path.exists(path):
        return {"error": "openenv.yaml not found at repo root"}
    with open(path, "r") as f:
        content = f.read()
    return Response(content=content, media_type="application/x-yaml")

@app.get("/info")
def get_info():
    return {
        "name": "code-debugger-env",
        "version": "1.0.0",
        "author": "raunit19",
        "description": "Professional Python debugging and security auditing environment with 12 tasks.",
    }

@app.get("/tasks")
def list_tasks():
    return [
        {"id": t["task_id"], "difficulty": t["difficulty"], "description": t["task_description"][:100]}
        for t in TASKS
    ]

@app.get("/metadata")
def get_metadata():
    return {
        "name": "code-debugger-env",
        "version": "1.0.0",
        "author": "raunit19",
        "description": "A real-world Python code debugging environment where AI agents identify and fix bugs across 12 tasks spanning runtime errors, logic bugs, and critical security vulnerabilities.",
        "tags": ["code-review", "debugging", "security", "python", "real-world", "openenv"],
        "action_space": {
            "type": "object",
            "fields": ["bug_line", "bug_type", "fixed_code", "explanation"]
        },
        "observation_space": {
            "type": "object",
            "fields": ["code_snippet", "task_description", "test_hint", "feedback", "attempt_number", "score_so_far", "done", "reward"]
        },
        "reward_range": [0.001, 0.999],
        "max_episode_steps": 3,
        "num_tasks": 12
    }

if __name__ == "__main__":
    # FIX 6: Explicit uvicorn startup on port 7860
    uvicorn.run(app, host="0.0.0.0", port=7860)
