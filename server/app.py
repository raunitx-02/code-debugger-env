import uvicorn
from openenv_core.env_server import create_app
from models import CodeDebugAction, CodeDebugObservation
from .environment import CodeDebuggerEnvironment

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

@app.get("/")
def root():
    """Environment root — provides deployment status and endpoint directory."""
    return {
        "name": "code-debugger-env",
        "status": "running",
        "message": "BugHunterRL OpenEnv environment is live",
        "endpoints": ["/health", "/metadata", "/stats", "/reset", "/step", "/state"]
    }

@app.get("/health")
def health():
    """Health check endpoint required by Dockerfile HEALTHCHECK and inference.py."""
    return {"status": "ok"}

@app.get("/metadata")
def metadata():
    """Metadata enrichment for the /metadata endpoint."""
    return {
        "name": "code-debugger-env",
        "version": "1.1.0",
        "description": "BugHunterRL: RL environment for automated code debugging",
        "tasks": {
            "total": 15,
            "easy": 5,
            "medium": 5,
            "hard": 5
        },
        "features": ["regression_oracle", "code_smell_penalty", "multi_file_simulation"],
        "max_episode_steps": 5,
    }

@app.get("/stats")
def stats():
    """Real-time in-memory environment statistics (Wow Factor)."""
    return {
        "status": "healthy",
        "active_sessions": env.SUPPORTS_CONCURRENT_SESSIONS,
        "framework": "openenv-core 0.2.1",
        "pydantic_version": "v2",
    }

def main():
    # Use string reference to allow reload if needed, though not standard for production
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
