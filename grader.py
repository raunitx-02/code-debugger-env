"""
grader.py — Execution-based grader with Code Smell Penalty + Regression Test Oracle.
NEVER raises exceptions — always returns (float, str, dict).
"""
import ast
import re
import subprocess
import sys
import textwrap
from typing import Tuple, List, Dict, Any

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

# BUG 7 FIX: Include __import__ so test code can use imports (needed for hard tasks)
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
    "__import__": __import__,  # Allow imports in test code
}


def _run_single_test(submitted_code: str, test_code: str) -> Tuple[bool, str]:
    """Execute submitted_code then test_code in a restricted exec() sandbox."""
    env: Dict[str, Any] = {"__builtins__": _SAFE_BUILTINS}
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

    for t in failing:
        ok, _ = _run_single_test(fixed_code, t["code"])
        if ok:
            tests_fixed.append(t["name"])

    for t in passing:
        ok, _ = _run_single_test(fixed_code, t["code"])
        if not ok:
            tests_broken.append(t["name"])

    gain = len(tests_fixed) / len(failing) if failing else 0.0
    loss = len(tests_broken) / len(passing) if passing else 0.0
    
    # BUG 2 FIX: Strict clamping (0.001, 0.999)
    reward = max(0.001, min(0.999, gain - loss))
    return reward, tests_fixed, tests_broken


# ── Legacy subprocess grader (kept for existing tasks) ──────────────────────

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
    """
    Grade the agent's fix.
    Returns (score, feedback_str, info_dict).
    """
    try:
        if not fixed_code or not fixed_code.strip():
            # BUG 2 FIX: 0.001 floor
            return 0.001, "No fixed code provided.", {
                "code_smells": [], "tests_fixed": [], "tests_broken": [], "regression_penalty": False
            }

        # ── NEW: Regression test oracle path ───────────────────────────────
        if "failing_tests" in task and "passing_tests" in task:
            base_reward, tests_fixed, tests_broken = _compute_regression_reward(fixed_code, task)
            smells = check_code_smells(fixed_code)

            final_score = (base_reward * 0.6) if (smells and base_reward > 0.001) else base_reward
            # BUG 2 FIX: Strict clamping
            final_score = round(max(0.001, min(0.999, final_score)), 4)

            failing = task.get("failing_tests", [])
            passing = task.get("passing_tests", [])
            all_fixed = len(tests_fixed) == len(failing)
            done_signal = all_fixed and len(tests_broken) == 0

            fb_lines = [
                f"Score: {final_score:.2f} | Fixed: {len(tests_fixed)}/{len(failing)} failing "
                f"| Broken: {len(tests_broken)}/{len(passing)} passing"
            ]
            for t in failing:
                symbol = "✓" if t["name"] in tests_fixed else "✗"
                fb_lines.append(f"  {symbol} [fix] {t['name']}")
            for t in passing:
                symbol = "✗ BROKEN" if t["name"] in tests_broken else "✓"
                fb_lines.append(f"  {symbol} [keep] {t['name']}")
            if smells:
                fb_lines.append(f"  ⚠ Code smells detected (−40% penalty): {', '.join(smells)}")

            info = {
                "code_smells": smells,
                "tests_fixed": tests_fixed,
                "tests_broken": tests_broken,
                "regression_penalty": len(tests_broken) > 0,
                "done_signal": done_signal,
            }
            return final_score, "\n".join(fb_lines), info

        # ── LEGACY: subprocess grader (original tasks) ──────────────────────
        test_cases = task.get("test_cases", [])
        if not test_cases:
            # BUG 2 FIX: 0.001 floor
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
_expected = {repr(expected)}
assert _result == _expected, f"Got {{_result!r}}, expected {{_expected!r}}"
""").strip()
                ok, msg = _run_code_safely(script)
                if ok:
                    passed += 1
                    feedback_lines.append(f"✓ {call} == {expected!r}")
                else:
                    feedback_lines.append(f"✗ {call}: {msg.split(chr(10))[-1][:120]}")

            elif tc_type == "pattern_absent":
                pattern, desc = tc.get("pattern", ""), tc.get("description", "")
                if pattern.lower() not in fixed_code.lower():
                    passed += 1; feedback_lines.append(f"✓ Security: {desc}")
                else:
                    feedback_lines.append(f"✗ Security: {desc} (found '{pattern}')")

            elif tc_type == "pattern_present":
                pattern, desc = tc.get("pattern", ""), tc.get("description", "")
                if pattern.lower() in fixed_code.lower():
                    passed += 1; feedback_lines.append(f"✓ Security: {desc}")
                else:
                    feedback_lines.append(f"✗ Security: {desc} ('{pattern}' not found)")

            elif tc_type == "pattern_present_any":
                patterns, desc = tc.get("patterns", []), tc.get("description", "")
                if any(p.lower() in fixed_code.lower() for p in patterns):
                    passed += 1; feedback_lines.append(f"✓ Security: {desc}")
                else:
                    feedback_lines.append(f"✗ Security: {desc} (none of {patterns} found)")

            elif tc_type == "code_runs":
                ok, msg = _run_code_safely(tc.get("code", ""))
                desc = tc.get("description", "check")
                if ok:
                    passed += 1; feedback_lines.append(f"✓ Verify: {desc}")
                else:
                    feedback_lines.append(f"✗ Verify: {desc}: {msg.split(chr(10))[-1][:120]}")

        base_score = (passed / total) * 0.75 if total > 0 else 0.0
        correct_line = task.get("correct_line", 0)
        line_bonus = 0.15 if correct_line and abs(bug_line - correct_line) <= 2 else 0.0
        correct_type = task.get("correct_bug_type", "")
        type_bonus = 0.10 if correct_type and bug_type.lower() == correct_type.lower() else 0.0

        if line_bonus:
            feedback_lines.append(f"✓ Bug location bonus: line {bug_line}")
        else:
            feedback_lines.append(f"✗ Bug location: you said line {bug_line}, actual is line {correct_line}")
        if type_bonus:
            feedback_lines.append(f"✓ Bug type correct: {bug_type}")
        else:
            feedback_lines.append(f"✗ Bug type: you said '{bug_type}', actual is '{correct_type}'")

        # Apply smell penalty to legacy tasks too
        smells = check_code_smells(fixed_code)
        # BUG 2 FIX: Cap at 0.999
        final_score = min(0.999, base_score + line_bonus + type_bonus)
        if smells and final_score > 0.001:
            final_score *= 0.6

        # BUG 2 FIX: Floor/Cap + Round
        final_score = round(max(0.001, min(0.999, final_score)), 4)
        feedback = f"Score: {final_score:.2f} | Tests: {passed}/{total} passed\n" + "\n".join(feedback_lines)
        if smells:
            feedback += f"\n⚠ Code smells (−40% penalty): {', '.join(smells)}"

        # BUG 6 FIX: done_signal for legacy
        info = {
            "code_smells": smells,
            "tests_fixed": [],
            "tests_broken": [],
            "regression_penalty": False,
            "done_signal": (passed == total and total > 0),
        }
        return final_score, feedback, info

    except Exception as e:
        # BUG 2 FIX: 0.001 floor
        return 0.001, f"Grader error: {e}", {
            "code_smells": [], "tests_fixed": [], "tests_broken": [], "regression_penalty": False
        }
