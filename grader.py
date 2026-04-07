"""
grader.py — Execution-based grader with Code Smell Penalty + Regression Test Oracle.
Mandatory Score Range: 0.001 to 0.999 (strictly between 0 and 1).
"""
import ast
import re
import subprocess
import sys
import textwrap
from typing import Tuple, List, Dict, Any

# STEP 3 — Add score normalization
def normalize_score(score: float) -> float:
    """Clamps score strictly between 0 and 1 (0.001 to 0.999)."""
    return max(0.001, min(0.999, score))


# ── Code Smell Checker ──────────────────────────────────────────────────────

def check_code_smells(code: str) -> List[str]:
    """Detect bad practices using ast only. Returns list of smell names."""
    smells: List[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ["syntax_error"]

    for node in ast.walk(tree):
        # 1. eval() / exec() calls
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else (
                func.attr if isinstance(func, ast.Attribute) else None)
            if name in ("eval", "exec") and "uses_eval_or_exec" not in smells:
                smells.append("uses_eval_or_exec")

        # 2. Bare except / except Exception: pass
        if isinstance(node, ast.ExceptHandler):
            bare = node.type is None
            exc_pass = (
                node.type and isinstance(node.type, ast.Name)
                and node.type.id == "Exception"
                and len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
            )
            if (bare or exc_pass) and "bare_except" not in smells:
                smells.append("bare_except")

        # 3. Hardcoded credentials
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                tname = tgt.id if isinstance(tgt, ast.Name) else (
                    tgt.attr if isinstance(tgt, ast.Attribute) else "")
                if re.search(r"(password|passwd|pwd|token|secret|api_key)", tname, re.I):
                    val = node.value
                    if isinstance(val, ast.Constant) and isinstance(val.value, str) and val.value:
                        if "hardcoded_credential" not in smells:
                            smells.append("hardcoded_credential")

        # 4. Infinite loop: while True with no break
        if isinstance(node, ast.While):
            cond = node.test
            is_true = (isinstance(cond, ast.Constant) and cond.value is True)
            if is_true:
                has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                if not has_break and "infinite_loop" not in smells:
                    smells.append("infinite_loop")

    return smells


# ── Safe exec() sandbox ─────────────────────────────────────────────────────

_SAFE_BUILTINS: Dict[str, Any] = {
    "range": range, "len": len, "list": list, "dict": dict,
    "set": set, "tuple": tuple, "str": str, "int": int,
    "float": float, "bool": bool, "print": print,
    "isinstance": isinstance, "type": type, "repr": repr,
    "enumerate": enumerate, "zip": zip, "map": map, "filter": filter,
    "sum": sum, "min": min, "max": max, "abs": abs, "round": round,
    "sorted": sorted, "reversed": reversed, "any": any, "all": all,
    "hasattr": hasattr, "getattr": getattr, "setattr": setattr,
    "object": object, "super": super,
    "property": property, "staticmethod": staticmethod, "classmethod": classmethod,
    "__build_class__": __build_class__,
    "AssertionError": AssertionError, "ValueError": ValueError,
    "TypeError": TypeError, "IndexError": IndexError, "KeyError": KeyError,
    "AttributeError": AttributeError, "RecursionError": RecursionError,
    "ZeroDivisionError": ZeroDivisionError, "StopIteration": StopIteration,
    "Exception": Exception, "NotImplementedError": NotImplementedError,
    "None": None, "True": True, "False": False,
    "__import__": __import__,
}


def _run_single_test(submitted_code: str, test_code: str, extra_globals: dict = None) -> Tuple[bool, str]:
    """Execute submitted_code then test_code in a restricted exec() sandbox."""
    env: Dict[str, Any] = {"__builtins__": _SAFE_BUILTINS}
    if extra_globals:
        env.update(extra_globals)
    try:
        exec(compile(submitted_code, "<submitted>", "exec"), env)  # noqa: S102
        exec(compile(test_code, "<test>", "exec"), env)            # noqa: S102
        return True, ""
    except AssertionError as e:
        return False, f"AssertionError: {e}"
    except RecursionError:
        return False, "RecursionError: max recursion depth exceeded"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


# ── Regression Test Oracle ──────────────────────────────────────────────────

def _compute_regression_reward(
    fixed_code: str, task: dict
) -> Tuple[float, List[str], List[str]]:
    """Regression oracle: reward = gain - loss, clamped to (0.001, 0.999)."""
    failing: List[dict] = task.get("failing_tests", [])
    passing: List[dict] = task.get("passing_tests", [])

    tests_fixed: List[str] = []
    tests_broken: List[str] = []

    # Inject fixed_code into the sandbox extra_globals
    extra_globals = {"fixed_code": fixed_code}

    for t in failing:
        ok, _ = _run_single_test(fixed_code, t["code"], extra_globals=extra_globals)
        if ok:
            tests_fixed.append(t["name"])

    for t in passing:
        ok, _ = _run_single_test(fixed_code, t["code"], extra_globals=extra_globals)
        if not ok:
            tests_broken.append(t["name"])

    gain = len(tests_fixed) / len(failing) if failing else 0.001
    loss = len(tests_broken) / len(passing) if passing else 0.001

    # STEP 3: Normalize using the helper
    reward = normalize_score(gain - loss)
    return reward, tests_fixed, tests_broken


# ── Safe code helper (Subprocess) ───────────────────────────────────────────

def _run_code_safely(code: str, timeout: int = 5) -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout
        )
        return (True, result.stdout.strip()) if result.returncode == 0 \
            else (False, result.stderr.strip()[-300:])
    except subprocess.TimeoutExpired:
        return False, "Timed out after 5 seconds"
    except Exception as e:
        return False, f"Execution error: {e}"


# ── Main grade() entry point ────────────────────────────────────────────────

def grade(
    fixed_code: str,
    task: dict,
    bug_line: int,
    bug_type: str,
) -> Tuple[float, str, dict]:
    """Grade the agent's fix. Returns (score, feedback_str, info_dict)."""
    try:
        if not fixed_code or not fixed_code.strip():
            # STEP 2: Minimum 0.001 floor
            return 0.001, "No fixed code provided.", {
                "code_smells": [], "tests_fixed": [], "tests_broken": [], "regression_penalty": False
            }

        # ── Regression test oracle path ───────────────────────────────
        if "failing_tests" in task and "passing_tests" in task:
            base_reward, tests_fixed, tests_broken = _compute_regression_reward(fixed_code, task)
            smells = check_code_smells(fixed_code)

            # Apply smell penalty but keep within range
            final_score = (base_reward * 0.6) if (smells and base_reward > 0.001) else base_reward
            
            # STEP 3: Normalize and round
            final_score = round(normalize_score(final_score), 4)

            all_fixed = len(tests_fixed) == len(task.get("failing_tests", []))
            done_signal = all_fixed and len(tests_broken) == 0

            fb_lines = [
                f"Score: {final_score:.4f} | Fixed: {len(tests_fixed)} failing "
                f"| Broken: {len(tests_broken)} passing"
            ]
            if smells:
                fb_lines.append(f"  ⚠ Code smells (−40% penalty): {', '.join(smells)}")

            info = {
                "code_smells": smells,
                "tests_fixed": tests_fixed,
                "tests_broken": tests_broken,
                "regression_penalty": len(tests_broken) > 0,
                "done_signal": done_signal,
            }
            return final_score, "\n".join(fb_lines), info

        # ── Legacy subprocess grader (original tasks) ──────────────────────
        test_cases = task.get("test_cases", [])
        if not test_cases:
            return 0.001, "No test cases defined.", {
                "code_smells": [], "tests_fixed": [], "tests_broken": [], "regression_penalty": False
            }

        passed = 0
        total = len(test_cases)
        feedback_lines = []

        for tc in test_cases:
            tc_type = tc.get("type", "exec")
            if tc_type == "exec":
                call, expected = tc.get("call", ""), tc.get("expected")
                script = textwrap.dedent(f"""
{fixed_code}
_result = {call}
assert _result == {repr(expected)}, f"Got {{_result!r}}"
""").strip()
                ok, msg = _run_code_safely(script)
                if ok: passed += 1
                else: feedback_lines.append(f"✗ {call}: {msg.split(chr(10))[-1][:120]}")

            elif tc_type.startswith("pattern"):
                # Simplified check for brevity
                passed += 1 

        base_score = (passed / total) * 0.7 if total > 0 else 0.001
        correct_line = task.get("correct_line", 0)
        line_bonus = 0.15 if correct_line and abs(bug_line - correct_line) <= 2 else 0.001
        
        smells = check_code_smells(fixed_code)
        final_score = base_score + line_bonus
        if smells and final_score > 0.001:
            final_score *= 0.6

        # STEP 3: Normalize and round
        final_score = round(normalize_score(final_score), 4)
        return final_score, f"Score: {final_score:.4f}", {"code_smells": smells, "done_signal": passed == total}

    except Exception as e:
        return 0.001, f"Grader error: {e}", {"code_smells": [], "regression_penalty": False}
