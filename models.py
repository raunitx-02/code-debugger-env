"""
models.py — Data structures for Code Debugger OpenEnv Environment (Pydantic Edition)
Hardened for openenv_core 0.2.1+ using Pydantic BaseModel.
"""
from typing import Optional, Dict, Any
from pydantic import Field, field_validator
from openenv_core.env_server.interfaces import Action, Observation, State

class CodeDebugAction(Action):
    """
    Action submitted by the AI agent.
    Inherits from pydantic.BaseModel (Action).
    """
    bug_line: int
    bug_type: str
    fixed_code: str
    explanation: str = ""

class CodeDebugObservation(Observation):
    """
    What the agent sees from the environment.
    Native range clamping via Pydantic validators.
    """
    task_id: str
    code_snippet: str
    task_description: str
    test_hint: str
    feedback: str = ""
    attempt_number: int = 1
    score_so_far: float = Field(default=0.001)
    difficulty: str = "unknown"
    
    # Override/Refine Observation fields
    done: bool = False
    reward: float = Field(default=0.001)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("reward", "score_so_far", mode="before")
    @classmethod
    def clamp_range(cls, v: Any) -> float:
        """Enforce 0 < score < 1 (strictly between 0 and 1)."""
        try:
            val = float(v)
            return max(0.001, min(0.999, val))
        except (ValueError, TypeError):
            return 0.001

class CodeDebugState(State):
    """
    Internal persistent state for concurrent sessions.
    Inherits from pydantic.BaseModel (State).
    """
    task_id: str = ""
    difficulty: str = ""
    max_attempts: int = 3
    best_score: float = 0.001
    current_task_index: int = 0
