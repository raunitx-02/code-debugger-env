"""
tests/test_environment.py — Direct (no HTTP) pytest tests for BugHunterRL.

Instantiates CodeDebuggerEnvironment directly so no running server is needed.
"""
import os
import sys

# Make the repo root importable regardless of where pytest is invoked from.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from server.environment import CodeDebuggerEnvironment
from server.tasks import TASKS
from models import CodeDebugAction

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_DUMMY_ACTION = CodeDebugAction(
    bug_line=1,
    bug_type="logic",
    fixed_code="def test(): pass",
    explanation="test",
)


def _make_env() -> CodeDebuggerEnvironment:
    """Return a fresh environment instance."""
    return CodeDebuggerEnvironment()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_reset_returns_observation():
    """reset() must return a valid CodeDebugObservation with correct field values."""
    env = _make_env()
    obs = env.reset()

    # All expected fields must be present
    for field in (
        "task_id",
        "code_snippet",
        "task_description",
        "feedback",
        "attempt_number",
        "score_so_far",
        "done",
        "reward",
    ):
        assert hasattr(obs, field), f"Observation missing field: {field}"

    # Episode starts incomplete
    assert obs.done is False, "done must be False immediately after reset()"

    # Score range compliance: strictly between 0 and 1
    assert obs.reward >= 0.05, f"reward too low: {obs.reward}"
    assert obs.reward <= 0.95, f"reward too high: {obs.reward}"


def test_step_returns_observation():
    """step() must return a scored observation with attempt_number incremented to 2."""
    env = _make_env()
    env.reset()

    obs = env.step(_DUMMY_ACTION)

    assert obs.reward >= 0.05, f"reward below floor: {obs.reward}"
    assert obs.reward <= 0.95, f"reward above ceiling: {obs.reward}"
    assert obs.attempt_number == 2, (
        f"Expected attempt_number == 2 after one step, got {obs.attempt_number}"
    )


def test_state_after_reset():
    """state() after reset() must reflect a freshly initialised episode."""
    env = _make_env()
    env.reset()

    state = env.state()

    # task_id must be populated
    assert state.task_id != "", "state.task_id must be set after reset()"
    # best_score starts at the floor value
    assert state.best_score == 0.05, (
        f"Expected best_score == 0.05 after reset, got {state.best_score}"
    )


def test_all_tasks_have_graders():
    """Every task dict must contain the required keys for the regression oracle."""
    required_keys = {
        "task_id",
        "difficulty",
        "code_snippet",
        "task_description",
        "failing_tests",
        "passing_tests",
    }

    assert len(TASKS) >= 3, f"Expected at least 3 tasks, found {len(TASKS)}"

    for task in TASKS:
        missing = required_keys - task.keys()
        assert not missing, (
            f"Task '{task.get('task_id', '?')}' is missing keys: {missing}"
        )


def test_difficulty_levels_present():
    """TASKS must include at least one task for each difficulty tier."""
    difficulties = {t["difficulty"] for t in TASKS}

    assert "easy" in difficulties, "No 'easy' task found in TASKS"
    assert "medium" in difficulties, "No 'medium' task found in TASKS"
    assert "hard" in difficulties, "No 'hard' task found in TASKS"


def test_score_range_compliance():
    """score_so_far from reset() must be within (0.05, 0.95) across multiple seeds."""
    env = _make_env()

    for seed in (0, 42, 99):
        obs = env.reset(seed=seed)
        assert obs.score_so_far >= 0.05, (
            f"seed={seed}: score_so_far below floor: {obs.score_so_far}"
        )
        assert obs.score_so_far <= 0.95, (
            f"seed={seed}: score_so_far above ceiling: {obs.score_so_far}"
        )


def test_done_after_max_attempts():
    """The environment must signal done=True once max_attempts steps have been taken."""
    env = _make_env()
    env.reset()

    last_obs = None
    for _ in range(5):
        last_obs = env.step(_DUMMY_ACTION)

    assert last_obs is not None
    assert last_obs.done is True, (
        f"Expected done==True after 5 steps, got done={last_obs.done}"
    )
