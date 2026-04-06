"""
app.py — FastAPI server for Code Debugger OpenEnv Environment
Runs on port 7860 (required for Hugging Face Spaces).
"""
import uvicorn
from openenv.core import create_app
from models import CodeDebugAction, CodeDebugObservation
from environment import CodeDebuggerEnvironment
from tasks import TASKS
from fastapi import Request

# IMPORTANT: first argument is the Environment CLASS (a callable factory),
# NOT an instance. openenv calls CodeDebuggerEnvironment() internally.
app = create_app(
    CodeDebuggerEnvironment,
    CodeDebugAction,
    CodeDebugObservation,
    env_name="code-debugger-env",
)

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
