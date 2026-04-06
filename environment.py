"""
environment.py — Code Debugger OpenEnv Environment
An AI agent receives Python code with a bug, identifies and fixes it.
Supports up to 3 attempts per episode with feedback between attempts.
"""
from openenv.core import Environment
from models import CodeDebugAction, CodeDebugObservation, CodeDebugState
from tasks import TASKS
from grader import grade
from typing import Optional
import random
import uuid


class CodeDebuggerEnvironment(Environment[CodeDebugAction, CodeDebugObservation, CodeDebugState]):
    """
    Code Debugger: agent identifies and fixes Python bugs.
    12 tasks across easy/medium/hard difficulty (4 per tier).
    Multi-turn: up to 3 attempts per episode with feedback.
    Hard tasks get 5 attempts. Execution-based grading via subprocess sandbox.
    Regression Test Oracle with failing+passing tests for all 12 tasks.
    Code Smell Penalty (-40%) for eval(), exec(), shell=True, hardcoded secrets.
    """

    SUPPORTS_CONCURRENT_SESSIONS = False

    def __init__(self):
        super().__init__()
        self._current_task = None
        self._state: Optional[CodeDebugState] = None

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs
    ) -> CodeDebugObservation:
        """Start a new episode with a randomly selected task."""
        if seed is not None:
            random.seed(seed)

        task = random.choice(TASKS)
        ep_id = episode_id or str(uuid.uuid4())[:8]

        self._current_task = task
        self._state = CodeDebugState(
            episode_id=ep_id,
            step_count=0,
            task_id=task["task_id"],
            difficulty=task["difficulty"],
            max_attempts=3,
            best_score=0.0,
        )

        return CodeDebugObservation(
            code_snippet=task["code_snippet"],
            task_description=task["task_description"],
            test_hint=task["test_hint"],
            feedback="",
            attempt_number=1,
            score_so_far=0.0,
            done=False,
            reward=None,
        )

    def step(
        self,
        action: CodeDebugAction,
        timeout_s: Optional[float] = None,
        **kwargs
    ) -> CodeDebugObservation:
        """
        Grade the agent's fix and return updated observation.
        reward and done are set directly on the returned Observation object.
        """
        if self._state is None or self._current_task is None:
            # Auto-reset: HTTP server may call step() on a fresh env instance
            self.reset()

        self._state.step_count += 1

        # Grade the submitted fix
        score, feedback, info = grade(
            fixed_code=action.fixed_code,
            task=self._current_task,
            bug_line=action.bug_line,
            bug_type=action.bug_type,
        )

        # Track best score across all attempts this episode
        if score > self._state.best_score:
            self._state.best_score = score

        # End episode if max attempts reached, near-perfect score, or all regression tests fixed
        done = (
            self._state.step_count >= self._state.max_attempts
            or score >= 0.95
            or info.get("done_signal", False)
        )

        return CodeDebugObservation(
            code_snippet=self._current_task["code_snippet"],
            task_description=self._current_task["task_description"],
            test_hint=self._current_task["test_hint"],
            feedback=feedback,
            attempt_number=self._state.step_count + 1,
            score_so_far=self._state.best_score,
            done=done,
            reward=score,
            code_smells=info.get("code_smells", []),
            tests_fixed=info.get("tests_fixed", []),
            tests_broken=info.get("tests_broken", []),
            regression_penalty=info.get("regression_penalty", False),
        )

    @property
    def state(self) -> CodeDebugState:
        """Return current episode state."""
        if self._state is None:
            return CodeDebugState()
        return self._state

    def close(self) -> None:
        """Clean up resources."""
        self._current_task = None
        self._state = None
