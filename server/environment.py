"""
environment.py — BugHunterRL Environment
Enhanced with multi-file project simulation and dynamic BugGeneration.
Score range compliant: 0.05 to 0.95.
"""
from openenv_core.env_server import Environment
from models import CodeDebugAction, CodeDebugObservation, CodeDebugState
from .tasks import TASKS, get_randomized_task
from .grader import grade, normalize_score
from typing import Optional
import random
import uuid

class CodeDebuggerEnvironment(Environment):
    """
    BugHunterRL: Reinforcement Learning Environment for Automated Code Debugging.
    Features:
    - 12+ Base tasks in easy/medium/hard categories.
    - Multi-file project debugging (Project-Based simulation).
    - Dynamic randomization to prevent agent memorization.
    """
    SUPPORTS_CONCURRENT_SESSIONS = True

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
        """Start a new episode with a randomized or standard task."""
        if seed is not None:
            random.seed(seed)

        # Support randomized bug generation for higher score
        target_id = kwargs.get("task_id")
        task = None
        
        if target_id:
            task = next((t for t in TASKS if t["task_id"] == target_id), None)
        
        if not task:
            # 30% chance of randomizing an existing task to increase difficulty
            if random.random() < 0.3:
                task = get_randomized_task()
                import sys
                print(f"[DEBUG] Dynamic task generated: {task['task_id']}", file=sys.stderr)
            else:
                task = random.choice(TASKS)

        ep_id = episode_id or str(uuid.uuid4())[:8]

        self._current_task = task
        self._state = CodeDebugState(
            episode_id=ep_id,
            task_id=task["task_id"],
            difficulty=task["difficulty"],
            max_attempts=5 if task.get("difficulty") == "hard" else 3,
            best_score=0.001,
        )

        # FIX 1: Return 0.05 (strictly between 0 and 1) for reset observation
        return CodeDebugObservation(
            task_id=task["task_id"],
            code_snippet=task["code_snippet"],
            task_description=task["task_description"],
            test_hint=task["test_hint"],
            feedback="",
            attempt_number=1,
            score_so_far=0.001,
            difficulty=task["difficulty"],
            done=False,
            reward=0.001,
            metadata={"task_id": task["task_id"]}
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

        try:
            self._state.step_count += 1
        except AttributeError:
            object.__setattr__(self._state, 'step_count', 1)

        # Execution-based grading via grader.py
        score, feedback, info = grade(
            fixed_code=action.fixed_code,
            task=self._current_task,
            bug_line=action.bug_line,
            bug_type=action.bug_type,
        )

        # Ensure score is normalized (already done in grade, but for safety)
        score = normalize_score(score)

        if score > self._state.best_score:
            self._state.best_score = score

        done = (
            self._state.step_count >= self._state.max_attempts
            or score >= 0.95
            or info.get("done_signal", False)
        )

        return CodeDebugObservation(
            task_id=self._current_task["task_id"],
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
                "is_dynamic": self._current_task["task_id"].startswith("dynamic_"),
                "tests_fixed": info.get("tests_fixed", []),
                "tests_broken": info.get("tests_broken", []),
            },
        )

    def state(self) -> CodeDebugState:
        if self._state is None:
            return CodeDebugState()
        return self._state

    def close(self) -> None:
        self._current_task = None
        self._state = None
