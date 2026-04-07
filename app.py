import uvicorn
from openenv_core.env_server import create_app, http_server
from models import CodeDebugAction, CodeDebugObservation
from environment import CodeDebuggerEnvironment
from grader import normalize_score
from typing import Any, Dict
import json as _json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response as StarResponse

# ── Patch 1: Serializer — clamp reward/score_so_far to (0.001, 0.999) ──────
original_serialize = http_server.HTTPEnvServer._serialize_observation

def patched_serialize(self, observation: Any) -> Dict[str, Any]:
    res = original_serialize(self, observation)
    raw_reward = res.get("reward")
    if raw_reward is None or float(raw_reward) <= 0.0:
        res["reward"] = 0.001
    elif float(raw_reward) >= 1.0:
        res["reward"] = 0.999
    else:
        res["reward"] = round(float(raw_reward), 4)
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

# ── Patch 2: register_routes — add /health and /metadata ───────────────────
original_register = http_server.HTTPEnvServer.register_routes

def patched_register(self, app: Any) -> None:
    original_register(self, app)
    from fastapi.routing import APIRoute
    app.router.routes = [r for r in app.router.routes
                         if not (isinstance(r, APIRoute) and r.path == "/health")]
    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/metadata")
    def metadata():
        return {
            "name": "code-debugger-env",
            "version": "1.1.0",
            "description": "BugHunterRL: RL environment for automated code debugging",
            "tasks": 12,
            "max_episode_steps": 5,
        }

# ── APPLY PATCHES BEFORE create_app() ──────────────────────────────────────
http_server.HTTPEnvServer._serialize_observation = patched_serialize
http_server.HTTPEnvServer.register_routes = patched_register

# ── Create the app ──────────────────────────────────────────────────────────
env = CodeDebuggerEnvironment()
app = create_app(
    env,
    CodeDebugAction,
    CodeDebugObservation,
    env_name="code-debugger-env"
)

# ── Middleware: clamp reward/score_so_far in ALL JSON responses ─────────────
# Must be added AFTER create_app() returns the real app object
class ClampRewardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        ct = response.headers.get("content-type", "")
        if "application/json" in ct:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            try:
                data = _json.loads(body)
                for key in ("reward", "score_so_far"):
                    if key in data:
                        data[key] = max(0.001, min(0.999, float(data[key])))
                if "observation" in data and isinstance(data["observation"], dict):
                    for key in ("reward", "score_so_far"):
                        if key in data["observation"]:
                            data["observation"][key] = max(0.001, min(0.999, float(data["observation"][key])))
                body = _json.dumps(data).encode()
            except Exception:
                pass
            return StarResponse(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )
        return response

app.add_middleware(ClampRewardMiddleware)


def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
