import uvicorn
from openenv_core.env_server import create_app
from models import CodeDebugAction, CodeDebugObservation
from environment import CodeDebuggerEnvironment

# Initialize the environment instance
env = CodeDebuggerEnvironment()

# Create the standard FastAPI app
# Pydantic handles validation, schema generation, and range compliance automatically.
app = create_app(
    lambda: env,
    CodeDebugAction,
    CodeDebugObservation,
    env_name="code-debugger-env"
)

@app.get("/metadata")
def metadata():
    """Metadata enrichment for the /metadata endpoint."""
    return {
        "name": "code-debugger-env",
        "version": "1.1.0",
        "description": "BugHunterRL: RL environment for automated code debugging",
        "tasks": 12,
        "max_episode_steps": 5,
    }

def main():
    # Use string reference to allow reload if needed, though not standard for production
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
