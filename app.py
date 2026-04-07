import uvicorn
from openenv_core.env_server import create_app, http_server
from models import CodeDebugAction, CodeDebugObservation
from environment import CodeDebuggerEnvironment
from grader import normalize_score
from typing import Any, Dict

# MONKEY-PATCH: Resolve openenv-core 0.1.1 serialization and health check priority.
# These ensure numeric rewards and the mandatory 'status: ok' payload.

# Force numeric reward in range 0.001 - 0.999 per validator rules
original_serialize = http_server.HTTPEnvServer._serialize_observation
def patched_serialize(self, observation: Any) -> Dict[str, Any]:
    res = original_serialize(self, observation)
    # FIX 4: Force reward to be strictly in (0, 1) — never 0.0 or 1.0
    raw_reward = res.get("reward")
    if raw_reward is None or float(raw_reward) <= 0.0:
        res["reward"] = 0.001
    elif float(raw_reward) >= 1.0:
        res["reward"] = 0.999
    else:
        res["reward"] = round(float(raw_reward), 4)

    # Force score_so_far to be strictly in (0, 1)
    raw_score = res.get("score_so_far")
    if raw_score is not None:
        if float(raw_score) <= 0.0:
            res["score_so_far"] = 0.001
        elif float(raw_score) >= 1.0:
            res["score_so_far"] = 0.999
        else:
            res["score_so_far"] = round(float(raw_score), 4)
            
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
    
    # STEP 17: Add metadata endpoint
    @app.get("/metadata")
    def metadata():
        return {
            "name": "code-debugger-env",
            "version": "1.0.0",
            "description": "BugHunterRL: RL environment for automated code debugging",
            "tasks": 12,
            "max_episode_steps": 5
        }

    # FIX 5: Add a /step and /reset response interceptor as FastAPI middleware
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    import json as _json

    class ClampRewardMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            if response.headers.get("content-type", "").startswith("application/json"):
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                try:
                    data = _json.loads(body)
                    # Clamp top-level reward and score_so_far
                    for key in ("reward", "score_so_far"):
                        if key in data:
                            v = float(data[key])
                            data[key] = max(0.001, min(0.999, v))
                    # Also clamp inside "observation" nested object
                    if "observation" in data and isinstance(data["observation"], dict):
                        for key in ("reward", "score_so_far"):
                            if key in data["observation"]:
                                v = float(data["observation"][key])
                                data["observation"][key] = max(0.001, min(0.999, v))
                    body = _json.dumps(data).encode()
                except Exception:
                    pass
                from starlette.responses import Response as StarResponse
                return StarResponse(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json"
                )
            return response

    app.add_middleware(ClampRewardMiddleware)

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
