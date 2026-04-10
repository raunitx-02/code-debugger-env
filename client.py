"""
client.py — Typed HTTP client for the BugHunterRL OpenEnv environment.

Usage:
    from client import CodeDebugEnv, CodeDebugAction

    env = CodeDebugEnv()                          # local server
    env = CodeDebugEnv.from_huggingface("raunit19/code-debugger-env")

    obs = env.reset(seed=42)
    obs = env.step(CodeDebugAction(
        bug_line=4,
        bug_type="logic",
        fixed_code="def foo(): return 1",
        explanation="Fixed the off-by-one error",
    ))
    state = env.state()
    env.close()
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from models import CodeDebugAction, CodeDebugObservation, CodeDebugState


class CodeDebugEnv:
    """
    Synchronous HTTP client for the BugHunterRL OpenEnv environment.

    Communicates with a running ``server/app.py`` instance via the standard
    OpenEnv REST API (POST /reset, POST /step, GET /state).
    """

    def __init__(self, base_url: str = "http://localhost:7860") -> None:
        """
        Initialise the client.

        Args:
            base_url: Root URL of the running environment server.
                      Defaults to ``http://localhost:7860``.
        """
        self.base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------ #
    # Internal helpers                                                      #
    # ------------------------------------------------------------------ #

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a POST request and return the parsed JSON body.

        Raises:
            RuntimeError: If the server returns a non-200 status code.
        """
        url = f"{self.base_url}{path}"
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code != 200:
            raise RuntimeError(
                f"POST {url} returned {response.status_code}: {response.text}"
            )
        return response.json()

    def _get(self, path: str) -> Dict[str, Any]:
        """Send a GET request and return the parsed JSON body.

        Raises:
            RuntimeError: If the server returns a non-200 status code.
        """
        url = f"{self.base_url}{path}"
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            raise RuntimeError(
                f"GET {url} returned {response.status_code}: {response.text}"
            )
        return response.json()

    # ------------------------------------------------------------------ #
    # Public API                                                            #
    # ------------------------------------------------------------------ #

    def reset(
        self,
        seed: Optional[int] = None,
        task_id: Optional[str] = None,
    ) -> CodeDebugObservation:
        """Start a new episode and return the initial observation.

        Args:
            seed:    Optional random seed for reproducibility.
            task_id: Optional specific task ID to load; if omitted the
                     server selects one at random.

        Returns:
            A :class:`CodeDebugObservation` representing the initial state.
        """
        payload: Dict[str, Any] = {}
        if seed is not None:
            payload["seed"] = seed
        if task_id is not None:
            payload["task_id"] = task_id

        data = self._post("/reset", payload)
        obs_data = data.get("observation", data)
        return CodeDebugObservation(
            **{k: v for k, v in obs_data.items() if k in CodeDebugObservation.model_fields}
        )

    def step(self, action: CodeDebugAction) -> CodeDebugObservation:
        """Submit an agent action and return the resulting observation.

        Args:
            action: A :class:`CodeDebugAction` containing the agent's fix,
                    the predicted bug line, and bug type.

        Returns:
            A :class:`CodeDebugObservation` with the graded score and
            feedback for this step.
        """
        payload = {"action": action.model_dump()}
        data = self._post("/step", payload)
        obs_data = data.get("observation", data)
        return CodeDebugObservation(
            **{k: v for k, v in obs_data.items() if k in CodeDebugObservation.model_fields}
        )

    def state(self) -> CodeDebugState:
        """Retrieve the current internal state of the environment.

        Returns:
            A :class:`CodeDebugState` reflecting the active episode's
            metadata (episode ID, step count, best score, etc.).
        """
        data = self._get("/state")
        return CodeDebugState(
            **{k: v for k, v in data.items() if k in CodeDebugState.model_fields}
        )

    def close(self) -> None:
        """Close the client session.

        This is a no-op for the HTTP client but is provided for API
        symmetry with async or stateful client variants.
        """

    # ------------------------------------------------------------------ #
    # Constructors                                                          #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_huggingface(cls, repo_id: str) -> "CodeDebugEnv":
        """Construct a client pointed at a Hugging Face Space deployment.

        Args:
            repo_id: The HF Space repo ID in ``owner/space-name`` format,
                     e.g. ``"raunit19/code-debugger-env"``.

        Returns:
            A :class:`CodeDebugEnv` instance configured for that Space.

        Example::

            env = CodeDebugEnv.from_huggingface("raunit19/code-debugger-env")
        """
        url = f"https://huggingface.co/spaces/{repo_id}"
        return cls(base_url=url)
