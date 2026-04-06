import uvicorn
from openenv_core.env_server import create_app, http_server
from models import CodeDebugAction, CodeDebugObservation
from environment import CodeDebuggerEnvironment
from typing import Any, Dict

# MONKEY-PATCH: Resolve openenv-core 0.1.1 serialization and health check priority.
# These ensure numeric rewards and the mandatory 'status: ok' payload.

# STEP 3: Force numeric reward in range 0.001 - 0.999 per validator rules
original_serialize = http_server.HTTPEnvServer._serialize_observation
def patched_serialize(self, observation: Any) -> Dict[str, Any]:
    res = original_serialize(self, observation)
    # Ensure reward is strictly between 0 and 1
    if res.get("reward") is None or res.get("reward") <= 0.0:
        res["reward"] = 0.001
    elif res.get("reward") >= 1.0:
        res["reward"] = 0.999
    
    if res.get("done") is None: 
        res["done"] = False
    return res

# Override health priority by patching register_routes directly.
original_register = http_server.HTTPEnvServer.register_routes
def patched_register(self, app: Any) -> None:
    original_register(self, app)
    from fastapi.routing import APIRoute
    # Manually filter existing /health route so our new one takes precedence.
    app.router.routes = [r for r in app.router.routes if not (isinstance(r, APIRoute) and r.path == "/health")]
    @app.get("/health")
    def health(): return {"status": "ok"}

# Apply the patches to the framework classes before instantiation.
http_server.HTTPEnvServer._serialize_observation = patched_serialize
http_server.HTTPEnvServer.register_routes = patched_register

# Instantiate the environment
env = CodeDebuggerEnvironment()

# Step 1 Minimal Server (now fully compliant via runtime patching)
app = create_app(
    env,
    CodeDebugAction,
    CodeDebugObservation,
    env_name="code-debugger-env"
)

def main():
    """Server entrypoint for multi-mode deployment as required by openenv validate."""
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
