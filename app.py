import uvicorn
from openenv_core.env_server import create_app, http_server
from models import CodeDebugAction, CodeDebugObservation
from environment import CodeDebuggerEnvironment
from typing import Any, Dict

# MONKEY-PATCH: Resolve openenv-core 0.1.1 serialization and health check priority.
# These ensure numeric rewards and the mandatory 'status: ok' payload in Python 3.10+.

# Force numeric reward even if asdict() extraction misses it.
original_serialize = http_server.HTTPEnvServer._serialize_observation
def patched_serialize(self, observation: Any) -> Dict[str, Any]:
    res = original_serialize(self, observation)
    if res.get("reward") is None: res["reward"] = 0.0
    if res.get("done") is None: res["done"] = False
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

if __name__ == "__main__":
    # Standard startup on port 7860
    uvicorn.run("app:app", host="0.0.0.0", port=7860)
