"""
app.py — FastAPI server for Code Debugger OpenEnv Environment
Runs on port 7860 (required for Hugging Face Spaces).
"""
import uvicorn
from openenv.core import create_app
from models import CodeDebugAction, CodeDebugObservation
from environment import CodeDebuggerEnvironment

# IMPORTANT: first argument is the Environment CLASS (a callable factory),
# NOT an instance. openenv calls CodeDebuggerEnvironment() internally.
app = create_app(
    CodeDebuggerEnvironment,
    CodeDebugAction,
    CodeDebugObservation,
    env_name="code-debugger-env",
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
