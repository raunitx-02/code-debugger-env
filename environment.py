"""
environment.py — Code Debugger OpenEnv Environment
An AI agent receives Python code with a bug, identifies and fixes it.
Multi-turn: up to 3 attempts (5 for hard) with feedback.
"""
from openenv_core.env_server import Environment
from models import CodeDebugAction, CodeDebugObservation, CodeDebugState
from tasks import TASKS
from grader import grade
from typing import Optional
import random
import uuid

class CodeDebuggerEnvironment(Environment):
    """
    Code Debugger: agent identifies and fixes Python bugs.
    12 tasks across easy/medium/hard difficulty (4 per tier).
    Multi-turn: up to 3 attempts per episode with feedback.
    Hard tasks get 5 attempts. Execution-based grading via sandbox.
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

        # Support specific task_id selection (mandatory for agent strategy)
        target_id = kwargs.get("task_id")
        task = None
        if target_id:
            task = next((t for t in TASKS if t["task_id"] == target_id), None)
        
        if not task:
            task = random.choice(TASKS)

        ep_id = episode_id or str(uuid.uuid4())[:8]

        self._current_task = task
        self._state = CodeDebugState(
            episode_id=ep_id,
            step_count=0,
            task_id=task["task_id"],
            difficulty=task["difficulty"],
            max_attempts=5 if task.get("difficulty") == "hard" else 3,
            best_score=0.001,
        )

        # FIX 3 & 4: Ensure all fields are present and task_id is in metadata
        return CodeDebugObservation(
            code_snippet=task["code_snippet"],
            task_description=task["task_description"],
            test_hint=task["test_hint"],
            feedback="",
            attempt_number=1,
            score_so_far=0.001,
            difficulty=task["difficulty"],
            done=False,
            reward=0.0,
            metadata={
                "task_id": task["task_id"],  # Required for inference.py to load task context
            }
        )

    def step(
        self,
        action: CodeDebugAction,
        timeout_s: Optional[float] = None,
        **kwargs
    ) -> CodeDebugObservation:
        """Grade the agent's fix and return updated observation."""
        if self._state is None or self._current_task is None:
            self.reset()

        self._state.step_count += 1

        # Grade the submitted fix (grader now handles clamping)
        score, feedback, info = grade(
            fixed_code=action.fixed_code,
            task=self._current_task,
            bug_line=action.bug_line,
            bug_type=action.bug_type,
        )

        # Track best score
        if score > self._state.best_score:
            self._state.best_score = score

        # End episode
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
            difficulty=self._current_task["difficulty"],
            done=done,
            reward=score,
            metadata={
                "task_id": self._current_task["task_id"],
                "code_smells": info.get("code_smells", []),
                "tests_fixed": info.get("tests_fixed", []),
                "tests_broken": info.get("tests_broken", []),
                "regression_penalty": info.get("regression_penalty", False),
            },
        )

    @property
    def state(self) -> CodeDebugState:
        if self._state is None:
            return CodeDebugState()
        return self._state

    def close(self) -> None:
        self._current_task = None
        self._state = None
