"""
models.py — Data structures for Code Debugger OpenEnv Environment
Uses standard @dataclass(kw_only=True) for full compatibility with openenv_core 0.1.1 in Python 3.10+.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from openenv_core.env_server.interfaces import Action, Observation, State

@dataclass(kw_only=True)
class CodeDebugAction(Action):
    """
    Action submitted by the agent.
    Inherits 'metadata: Dict[str, Any]' from Action base.
    """
    bug_line: int
    bug_type: str
    fixed_code: str
    explanation: str = ""

@dataclass(kw_only=True)
class CodeDebugObservation(Observation):
    """
    What the agent observes.
    Inherits from Observation base (done, reward, metadata).
    Must be a dataclass for openenv_core serializer (asdict) to work correctly.
    """
    task_id: str
    code_snippet: str
    task_description: str
    test_hint: str
    feedback: str = ""
    attempt_number: int = 1
    score_so_far: float = 0.001
    difficulty: str = "unknown"
    
    # We must explicitly re-define these fields to ensure asdict() recognizes them in 3.11.
    done: bool = False
    reward: Optional[float] = 0.001
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(kw_only=True)
class CodeDebugState(State):
    """
    Internal environment state.
    Inherits from State base (episode_id, step_count).
    """
    task_id: str = ""
    difficulty: str = ""
    max_attempts: int = 3
    best_score: float = 0.001
    current_task_index: int = 0
