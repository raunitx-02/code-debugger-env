import sys
from server.environment import CodeDebuggerEnvironment
from models import CodeDebugAction

env = CodeDebuggerEnvironment()
from server.tasks import TASKS

out_of_bounds = []

for t in TASKS:
    task_id = t["task_id"]
    print(f"Testing {task_id}...")
    
    # Test 1: Empty Action
    env.reset(task_id=task_id)
    obs = env.step(CodeDebugAction(bug_line=1, bug_type="logic", fixed_code=""))
    if not (0 < obs.reward < 1.0):
        out_of_bounds.append((task_id, "empty", obs.reward))
        
    # Test 2: Random Action
    env.reset(task_id=task_id)
    obs = env.step(CodeDebugAction(bug_line=1, bug_type="logic", fixed_code="def x(): pass"))
    if not (0 < obs.reward < 1.0):
        out_of_bounds.append((task_id, "random", obs.reward))
        
    # Test 3: "Perfect" Action (roughly simulated by using passing_tests or expected behavior)
    # If it's a legacy task, it checks test_cases.
    env.reset(task_id=task_id)
    raw_snippet = t.get("code_snippet", "")
    
    # To really get perfect, we need the exact fix. Since we do not have it immediately, we can just check if any score from the grader fails. 
    # But wait, we can just call grade() directly with a perfect score spoof.

for err in out_of_bounds:
    print("FAILED:", err)
if not out_of_bounds:
    print("ALL TESTS RETURNED REWARDS STRICTLY BETWEEN 0 AND 1.")
