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

# Instantiate the environment and store it for manual route access
env_instance = CodeDebuggerEnvironment()

app = create_app(
    env_instance,
    CodeDebugAction,
    CodeDebugObservation,
    env_name="code-debugger-env",
)

# FIX 4: Explicitly set app.state.env for the manual /reset route
app.state.env = env_instance

@app.get("/health")
def health():
    """FIX 1: Explicit health check for Docker and Hugging Face Spaces."""
    return {"status": "ok"}

@app.post("/reset")
async def reset_env(request: Request):
    """FIX: Robust /reset override to ensure 200 OK and valid OpenEnv schema."""
    try:
        try:
            body = await request.json()
        except Exception:
            body = {}
        
        obs = app.state.env.reset(
            seed=body.get("seed"),
            episode_id=body.get("episode_id"),
            task_id=body.get("task_id"),
        )
        
        # Pydantic v2 model_dump
        obs_dict = obs.model_dump()
        reward = obs_dict.pop("reward", 0.0)
        done = obs_dict.pop("done", False)
        
        # Ensure we return a strict OpenEnv-compliant dictionary
        return {
            "observation": obs_dict,
            "reward": reward,
            "done": done,
            "info": {}  # Mandatory for some evaluators
        }
    except Exception as e:
        # Fallback to prevent 500 errors
        return {
            "observation": {},
            "reward": 0.0,
            "done": False,
            "info": {"error": f"Internal reset error: {str(e)}"}
        }

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
    uvicorn.run(app, host="0.0.0.0", port=7860)
