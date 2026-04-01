"""
grader.py — Execution-based grader for Code Debugger environment.
Runs fixed code in isolated subprocesses with 5-second timeout.
NEVER raises exceptions — always returns a (float, str) tuple.
"""
import subprocess
import sys
import textwrap
from typing import Tuple


def _run_code_safely(code: str, timeout: int = 5) -> Tuple[bool, str]:
    """Run Python code in a subprocess. Returns (success, output/error)."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()[-300:]
    except subprocess.TimeoutExpired:
        return False, "Timed out after 5 seconds"
    except Exception as e:
        return False, f"Execution error: {e}"


def grade(
    fixed_code: str,
    task: dict,
    bug_line: int,
    bug_type: str
) -> Tuple[float, str]:
    """
    Grade the agent's fix. Returns (score_0_to_1, feedback_string).
    Score breakdown:
      - Test cases pass: up to 0.75
      - Correct bug line (within ±2): +0.15 bonus
      - Correct bug type: +0.10 bonus
    Final score is clipped to [0.0, 1.0].
    """
    try:
        test_cases = task.get("test_cases", [])
        if not test_cases:
            return 0.0, "No test cases defined for this task."

        if not fixed_code or not fixed_code.strip():
            return 0.0, "No fixed code provided."

        passed = 0
        total = len(test_cases)
        feedback_lines = []

        for tc in test_cases:
            tc_type = tc.get("type", "exec")

            # ── Type: exec — run the fixed code and call a function ──
            if tc_type == "exec":
                call = tc.get("call", "")
                expected = tc.get("expected")
                test_script = textwrap.dedent(f"""
{fixed_code}

_result = {call}
_expected = {repr(expected)}
assert _result == _expected, f"Got {{_result!r}}, expected {{_expected!r}}"
""").strip()
                ok, msg = _run_code_safely(test_script)
                if ok:
                    passed += 1
                    feedback_lines.append(f"✓ {call} == {expected!r}")
                else:
                    short = msg.split('\n')[-1][:120] if msg else "Failed"
                    feedback_lines.append(f"✗ {call}: {short}")

            # ── Type: pattern_absent — string must NOT appear in fixed_code ──
            elif tc_type == "pattern_absent":
                pattern = tc.get("pattern", "")
                desc = tc.get("description", pattern)
                if pattern.lower() not in fixed_code.lower():
                    passed += 1
                    feedback_lines.append(f"✓ Security: {desc}")
                else:
                    feedback_lines.append(f"✗ Security: {desc} (found forbidden pattern '{pattern}')")

            # ── Type: pattern_present — string MUST appear in fixed_code ──
            elif tc_type == "pattern_present":
                pattern = tc.get("pattern", "")
                desc = tc.get("description", pattern)
                if pattern.lower() in fixed_code.lower():
                    passed += 1
                    feedback_lines.append(f"✓ Security: {desc}")
                else:
                    feedback_lines.append(f"✗ Security: {desc} (pattern '{pattern}' not found)")

            # ── Type: pattern_present_any — at least one pattern must appear ──
            elif tc_type == "pattern_present_any":
                patterns = tc.get("patterns", [])
                desc = tc.get("description", str(patterns))
                if any(p.lower() in fixed_code.lower() for p in patterns):
                    passed += 1
                    feedback_lines.append(f"✓ Security: {desc}")
                else:
                    feedback_lines.append(f"✗ Security: {desc} (none of {patterns} found)")

            # ── Type: code_runs — run standalone verification code ──
            elif tc_type == "code_runs":
                code_to_run = tc.get("code", "")
                desc = tc.get("description", "standalone check")
                ok, msg = _run_code_safely(code_to_run)
                if ok:
                    passed += 1
                    feedback_lines.append(f"✓ Verify: {desc}")
                else:
                    short = msg.split('\n')[-1][:120] if msg else "Failed"
                    feedback_lines.append(f"✗ Verify: {desc}: {short}")

        # Base score from test cases (max 0.75)
        base_score = (passed / total) * 0.75 if total > 0 else 0.0

        # Bonus: correct bug line (within ±2 lines)
        correct_line = task.get("correct_line", 0)
        line_bonus = 0.0
        if correct_line and abs(bug_line - correct_line) <= 2:
            line_bonus = 0.15
            feedback_lines.append(f"✓ Bug location bonus: line {bug_line} (correct is ~{correct_line})")
        else:
            feedback_lines.append(f"✗ Bug location: you said line {bug_line}, actual is line {correct_line}")

        # Bonus: correct bug type
        correct_type = task.get("correct_bug_type", "")
        type_bonus = 0.0
        if correct_type and bug_type.lower().strip() == correct_type.lower().strip():
            type_bonus = 0.10
            feedback_lines.append(f"✓ Bug type correct: {bug_type}")
        else:
            feedback_lines.append(f"✗ Bug type: you said '{bug_type}', actual is '{correct_type}'")

        final_score = min(1.0, base_score + line_bonus + type_bonus)

        summary = f"Score: {final_score:.2f} | Tests: {passed}/{total} passed"
        feedback = summary + "\n" + "\n".join(feedback_lines)

        return round(final_score, 4), feedback

    except Exception as e:
        # NEVER crash the server — always return a valid result
        return 0.0, f"Grader error (please try again): {e}"
