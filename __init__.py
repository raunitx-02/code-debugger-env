"""
code_debugger_env — BugHunterRL OpenEnv Client
pip install git+https://huggingface.co/spaces/raunit19/code-debugger-env
"""
from __future__ import annotations
import asyncio
import json
import httpx
from typing import Any, Dict, Optional
from .models import CodeDebugAction, CodeDebugObservation, CodeDebugState

__all__ = ["CodeDebuggerEnv", "CodeDebugAction", "CodeDebugObservation", "CodeDebugState"]


class _SyncProxy:
    """Synchronous wrapper around CodeDebuggerEnv for use without async."""
    def __init__(self, env: "CodeDebuggerEnv"):
        self._env = env
        self._loop = asyncio.new_event_loop()

    def __enter__(self):
        self._loop.run_until_complete(self._env.__aenter__())
        return self

    def __exit__(self, *args):
        self._loop.run_until_complete(self._env.__aexit__(*args))
        self._loop.close()

    def reset(self, **kwargs) -> CodeDebugObservation:
        return self._loop.run_until_complete(self._env.reset(**kwargs))

    def step(self, action: CodeDebugAction) -> CodeDebugObservation:
        return self._loop.run_until_complete(self._env.step(action))

    def state(self) -> Dict[str, Any]:
        return self._loop.run_until_complete(self._env.state())


class CodeDebuggerEnv:
    """
    Async client for the BugHunterRL OpenEnv environment.

    Usage (async):
        async with CodeDebuggerEnv(base_url="https://raunit19-code-debugger-env.hf.space") as env:
            obs = await env.reset()
            obs = await env.step(CodeDebugAction(bug_line=4, bug_type="logic", fixed_code="..."))

    Usage (sync):
        with CodeDebuggerEnv(base_url="...").sync() as env:
            obs = env.reset()
    """

    def __init__(self, base_url: str = "https://raunit19-code-debugger-env.hf.space", timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "CodeDebuggerEnv":
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
            self._client = None

    def sync(self) -> _SyncProxy:
        return _SyncProxy(self)

    async def reset(self, seed: Optional[int] = None, task_id: Optional[str] = None) -> CodeDebugObservation:
        payload: Dict[str, Any] = {}
        if seed is not None:
            payload["seed"] = seed
        if task_id is not None:
            payload["task_id"] = task_id
        resp = await self._client.post("/reset", json=payload)
        resp.raise_for_status()
        data = resp.json()
        obs_data = data.get("observation", data)
        # Use Pydantic v2 model_fields for filtering
        return CodeDebugObservation(**{k: v for k, v in obs_data.items() if k in CodeDebugObservation.model_fields})

    async def step(self, action: CodeDebugAction) -> CodeDebugObservation:
        # Use Pydantic v2 model_dump for serialization
        action_dict = action.model_dump(exclude={"metadata"})
        resp = await self._client.post("/step", json={"action": action_dict})
        resp.raise_for_status()
        data = resp.json()
        obs_data = data.get("observation", data)
        return CodeDebugObservation(**{k: v for k, v in obs_data.items() if k in CodeDebugObservation.model_fields})

    async def state(self) -> Dict[str, Any]:
        resp = await self._client.get("/state")
        resp.raise_for_status()
        return resp.json()
