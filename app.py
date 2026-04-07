import uvicorn
from openenv_core.env_server import create_app
from models import CodeDebugAction, CodeDebugObservation
from environment import CodeDebuggerEnvironment
from typing import Any
import json as _json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response as StarResponse

# ── Create the environment instance ──────────────────────────────────────────
env = CodeDebuggerEnvironment()

# ── Create the FastAPI app ──────────────────────────────────────────────────
# Standard create_app already provides /health, /state, /metadata, /schema etc.
# /metadata is populated from openenv.yaml + environment metadata.
app = create_app(
    lambda: env,
    CodeDebugAction,
    CodeDebugObservation,
    env_name="code-debugger-env"
)

# ── Middleware: clamp reward/score_so_far in ALL JSON responses ─────────────
# This is a safe and robust way to ensure the (0.001, 0.999) range on the wire.
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
                # Clamp root-level reward fields
                for key in ("reward", "score_so_far"):
                    if key in data and data[key] is not None:
                        try:
                            data[key] = max(0.001, min(0.999, float(data[key])))
                        except (ValueError, TypeError):
                            pass
                # Clamp nested observation fields
                if "observation" in data and isinstance(data["observation"], dict):
                    for key in ("reward", "score_so_far"):
                        if key in data["observation"] and data["observation"][key] is not None:
                            try:
                                data["observation"][key] = max(0.001, min(0.999, float(data["observation"][key])))
                            except (ValueError, TypeError):
                                pass
                body = _json.dumps(data).encode()
            except Exception:
                pass
            
            # ── FIX: Correctly handle modified body headers ──────────────────
            headers = dict(response.headers)
            headers.pop("content-length", None)
            headers.pop("content-encoding", None)
            
            return StarResponse(
                content=body,
                status_code=response.status_code,
                headers=headers,
                media_type="application/json",
            )
        return response

app.add_middleware(ClampRewardMiddleware)

# ── Custom /metadata (optional enrichment) ──────────────────────────────────
@app.get("/metadata")
def metadata():
    return {
        "name": "code-debugger-env",
        "version": "1.1.0",
        "description": "BugHunterRL: RL environment for automated code debugging",
        "tasks": 12,
        "max_episode_steps": 5,
    }

def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
