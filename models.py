"""
models.py — Pydantic models for Code Debugger OpenEnv Environment
All three classes MUST inherit from the openenv_core base classes.
"""
from openenv_core.env_server.interfaces import Action, Observation, State
from pydantic import Field
from typing import Optional, List

class CodeDebugAction(Action):
    """
    Action submitted by the agent.
    Inherits 'metadata: Dict[str, Any]' from Action base.
    """
    bug_line: int = Field(..., ge=1, description="1-indexed line number of the bug")
    bug_type: str = Field(..., description="One of: syntax | logic | runtime | security")
    fixed_code: str = Field(..., description="Complete corrected Python code")
    explanation: str = Field(default="", description="Agent's explanation (optional)")

class CodeDebugObservation(Observation):
    """
    What the agent observes.
    Inherits from Observation base:
      - done: bool = False
      - reward: float | None = None
      - metadata: Dict[str, Any] = {}
    """
    task_id: str = Field(..., description="Unique ID of the current task")
    code_snippet: str = Field(..., description="Python code containing one bug")
    task_description: str = Field(..., description="What this function should do correctly")
    test_hint: str = Field(..., description="Description of test cases (not actual code)")
    feedback: str = Field(default="", description="Feedback from previous step")
    attempt_number: int = Field(default=1, description="Current attempt (1, 2, or 3)")
    score_so_far: float = Field(default=0.001, description="Best score so far in this episode")
    difficulty: str = Field(default="unknown", description="Difficulty tier of the task")

class CodeDebugState(State):
    """
    Internal environment state.
    Inherits from State base (extra='allow'):
      - episode_id: Optional[str] = None
      - step_count: int = 0
    """
    task_id: str = Field(default="")
    difficulty: str = Field(default="")
    max_attempts: int = Field(default=3)
    best_score: float = Field(default=0.001)
    current_task_index: int = Field(default=0)
