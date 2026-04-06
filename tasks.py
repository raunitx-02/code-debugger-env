"""
tasks.py — All debugging tasks for the Code Debugger environment.

All 12 tasks now use the Regression Test Oracle format:
  each has failing_tests (must fix) and passing_tests (must not break).
Legacy formatting (test_cases) is kept for backward compatibility.
"""

TASKS = [

    # ── EASY 1 (Regression Oracle) ────────────────────────────────────────────
    {
        "task_id": "easy_01",
        "difficulty": "easy",
        "code_snippet": '''def double_all(lst):
    result = []
    for i in range(len(lst) - 1):
        result.append(lst[i] * 2)
    return result''',
        "task_description": (
            "double_all should return a new list with every element doubled. "
            "The current implementation has an off-by-one error — it skips the last element."
        ),
        "test_hint": "Tested with: [1,2,3]→[2,4,6], [5]→[10], []→[], result must be a list",
        "correct_line": 3,
        "correct_bug_type": "logic",
        "failing_tests": [
            {"name": "test_full_list", "code": "assert double_all([1, 2, 3]) == [2, 4, 6], 'all elements must be doubled'"},
            {"name": "test_single_element", "code": "assert double_all([5]) == [10], 'single element must be doubled'"},
        ],
        "passing_tests": [
            {"name": "test_empty_list", "code": "assert double_all([]) == [], 'empty list must return empty'"},
            {"name": "test_returns_list", "code": "assert isinstance(double_all([1, 2]), list), 'must return a list'"},
        ],
        "test_cases": [
            {"type": "exec", "call": "double_all([1, 2, 3])", "expected": [2, 4, 6]},
            {"type": "exec", "call": "double_all([])",        "expected": []},
        ],
    },

    # ── EASY 2 (Regression Oracle) ────────────────────────────────────────────
    {
        "task_id": "easy_02",
        "difficulty": "easy",
        "code_snippet": '''def is_palindrome(s):
    s = s.lower()
    for i in range(len(s) // 2):
        if s[i] != s[len(s) - i]:
            return False
    return True''',
        "task_description": (
            "Check whether a string is a palindrome (reads the same forwards and backwards). "
            "Case-insensitive. The bug is an off-by-one error in indexing (s[len(s)-i] hits index error or wrong char)."
        ),
        "test_hint": "Tested with: 'racecar'→True, 'hello'→False, 'A'→True, ''→True",
        "correct_line": 4,
        "correct_bug_type": "runtime",
        "failing_tests": [
            {"name": "test_racecar", "code": "assert is_palindrome('racecar') == True, 'racecar is palindrome'"},
            {"name": "test_hello", "code": "assert is_palindrome('hello') == False, 'hello is not palindrome'"},
            {"name": "test_single_char", "code": "assert is_palindrome('A') == True, 'single char is palindrome'"},
        ],
        "passing_tests": [
            {"name": "test_empty_string", "code": "assert is_palindrome('') == True, 'empty string is palindrome'"},
            {"name": "test_returns_bool", "code": "assert isinstance(is_palindrome('a'), bool), 'must return bool'"},
        ],
        "test_cases": [
            {"type": "exec", "call": "is_palindrome('racecar')", "expected": True},
            {"type": "exec", "call": "is_palindrome('hello')",   "expected": False},
        ],
    },

    # ── EASY 3 (Regression Oracle) ────────────────────────────────────────────
    {
        "task_id": "easy_03",
        "difficulty": "easy",
        "code_snippet": '''def count_vowels(text):
    vowels = "aeiou"
    count = 0
    for char in text.lower():
        if char in vowels:
            count + 1
    return count''',
        "task_description": (
            "Count the number of vowels in a string (case-insensitive). "
            "The bug is missing assignment: count + 1 should be count += 1."
        ),
        "test_hint": "Tested with: 'hello'→2, 'AEIOU'→5, 'rhythm'→0, ''→0",
        "correct_line": 6,
        "correct_bug_type": "logic",
        "failing_tests": [
            {"name": "test_hello", "code": "assert count_vowels('hello') == 2, 'hello has 2 vowels'"},
            {"name": "test_all_vowels", "code": "assert count_vowels('AEIOU') == 5, 'AEIOU has 5 vowels'"},
        ],
        "passing_tests": [
            {"name": "test_no_vowels", "code": "assert count_vowels('rhythm') == 0, 'rhythm has 0 vowels'"},
            {"name": "test_empty", "code": "assert count_vowels('') == 0, 'empty string has 0 vowels'"},
        ],
        "test_cases": [
            {"type": "exec", "call": "count_vowels('hello')", "expected": 2},
        ],
    },

    # ── EASY 4 (Regression Oracle) ────────────────────────────────────────────
    {
        "task_id": "easy_04",
        "difficulty": "easy",
        "code_snippet": '''def multiply_list(numbers):
    product = 0
    for n in numbers:
        product *= n
    return product''',
        "task_description": (
            "multiply_list should return the product of all numbers in a list. "
            "The bug is initializing product to 0 instead of 1 — multiplying by 0 always returns 0."
        ),
        "test_hint": "Tested with: [1,2,3,4]→24, [5,5]→25, [1]→1, [-1,-1]→1",
        "correct_line": 2,
        "correct_bug_type": "logic",
        "failing_tests": [
            {"name": "test_four_elements", "code": "assert multiply_list([1, 2, 3, 4]) == 24, 'product of [1,2,3,4] must be 24'"},
            {"name": "test_two_elements", "code": "assert multiply_list([5, 5]) == 25, 'product of [5,5] must be 25'"},
        ],
        "passing_tests": [
            {"name": "test_single", "code": "assert multiply_list([1]) == 1, 'single element product'"},
            {"name": "test_negatives", "code": "assert multiply_list([-1, -1]) == 1, 'two negatives give positive'"},
        ],
        "test_cases": [
            {"type": "exec", "call": "multiply_list([1, 2, 3, 4])", "expected": 24},
            {"type": "exec", "call": "multiply_list([5, 5])",      "expected": 25},
            {"type": "exec", "call": "multiply_list([1])",         "expected": 1},
        ],
    },

    # ── MEDIUM 1 (Regression Oracle) ───────────────────────────────────────────
    {
        "task_id": "medium_01",
        "difficulty": "medium",
        "code_snippet": '''def recursive_sum(lst):
    if not lst:
        return 0
    return lst[0] + recursive_sum(lst)''',
        "task_description": (
            "recursive_sum should return the sum of all numbers in a list using recursion. "
            "The bug causes infinite recursion — lst should be sliced to lst[1:] in the recursive call."
        ),
        "test_hint": "Tested with: []→0, [5]→5, [1,2]→3, [1,2,3,4,5]→15",
        "correct_line": 4,
        "correct_bug_type": "runtime",
        "failing_tests": [
            {"name": "test_single_item", "code": "assert recursive_sum([5]) == 5, 'single item sum'"},
            {"name": "test_two_items", "code": "assert recursive_sum([1, 2]) == 3, 'two items sum'"},
        ],
        "passing_tests": [
            {"name": "test_empty_input", "code": "assert recursive_sum([]) == 0, 'empty list returns 0'"},
        ],
        "test_cases": [
            {"type": "exec", "call": "recursive_sum([1, 2, 3])", "expected": 6},
        ],
    },

    # ── MEDIUM 2 (Regression Oracle) ───────────────────────────────────────────
    {
        "task_id": "medium_02",
        "difficulty": "medium",
        "code_snippet": '''def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) / 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1''',
        "task_description": (
            "Binary search: return the index of target in a sorted list, or -1 if not found. "
            "The bug is integer division — mid should use // not /."
        ),
        "test_hint": "Tested with: ([1,3,5,7,9], 5)→2, ([1,3,5], 6)→-1, ([], 1)→-1",
        "correct_line": 4,
        "correct_bug_type": "runtime",
        "failing_tests": [
            {"name": "test_found_middle", "code": "assert binary_search([1, 3, 5, 7, 9], 5) == 2, 'should find 5 at index 2'"},
            {"name": "test_found_first", "code": "assert binary_search([1, 3, 5, 7, 9], 1) == 0, 'should find 1 at index 0'"},
        ],
        "passing_tests": [
            {"name": "test_not_found", "code": "assert binary_search([1, 3, 5], 6) == -1, 'should return -1 when not found'"},
            {"name": "test_empty_array", "code": "assert binary_search([], 1) == -1, 'empty array returns -1'"},
        ],
        "test_cases": [
            {"type": "exec", "call": "binary_search([1, 3, 5, 7, 9], 5)", "expected": 2},
        ],
    },

    # ── MEDIUM 3 (Regression Oracle) ───────────────────────────────────────────
    {
        "task_id": "medium_03",
        "difficulty": "medium",
        "code_snippet": '''def flatten_list(nested):
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return nested''',
        "task_description": (
            "Recursively flatten a nested list of any depth into a single flat list. "
            "The bug is returning nested instead of result."
        ),
        "test_hint": "Tested with: [1,[2,3],[4,[5,6]]]→[1,2,3,4,5,6], []→[], [1,2,3]→[1,2,3]",
        "correct_line": 8,
        "correct_bug_type": "logic",
        "failing_tests": [
            {"name": "test_nested_list", "code": "assert flatten_list([1, [2, 3], [4, [5, 6]]]) == [1, 2, 3, 4, 5, 6], 'must flatten deeply'"},
            {"name": "test_deeply_nested", "code": "assert flatten_list([[1, [2]], 3]) == [1, 2, 3], 'deep nest must flatten'"},
        ],
        "passing_tests": [
            {"name": "test_empty", "code": "assert flatten_list([]) == [], 'empty list stays empty'"},
            {"name": "test_flat_list", "code": "assert flatten_list([1, 2, 3]) == [1, 2, 3], 'flat list unchanged'"},
        ],
        "test_cases": [
            {"type": "exec", "call": "flatten_list([1, [2, 3]])", "expected": [1, 2, 3]},
        ],
    },

    # ── MEDIUM 4 (Regression Oracle) ─────────────────────────────────────────────
    {
        "task_id": "medium_04",
        "difficulty": "medium",
        "code_snippet": '''def find_duplicates(lst):
    seen = set()
    duplicates = set()
    for item in lst:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return seen''',
        "task_description": (
            "find_duplicates should return a set of all items that appear more than once. "
            "The bug is returning 'seen' instead of 'duplicates'."
        ),
        "test_hint": "Tested with: [1,2,2,3,3,3]→{2,3}, [1,2,3]→set(), [1,1]→{1}",
        "correct_line": 8,
        "correct_bug_type": "logic",
        "failing_tests": [
            {"name": "test_multiple_dups", "code": "assert find_duplicates([1, 2, 2, 3, 3, 3]) == {2, 3}, 'must return only duplicates'"},
            {"name": "test_single_dup", "code": "assert find_duplicates([1, 1]) == {1}, 'single duplicate'"},
        ],
        "passing_tests": [
            {"name": "test_no_dups", "code": "assert find_duplicates([1, 2, 3]) == set(), 'no duplicates returns empty set'"},
            {"name": "test_returns_set", "code": "assert isinstance(find_duplicates([1]), set), 'must return a set'"},
        ],
        "test_cases": [
            {"type": "exec", "call": "find_duplicates([1, 2, 2, 3, 3, 3])", "expected": {2, 3}},
            {"type": "exec", "call": "find_duplicates([1, 2, 3])",          "expected": set()},
        ],
    },

    # ── HARD 1 (Regression Oracle) ─────────────────────────────────────────────
    {
        "task_id": "hard_01",
        "difficulty": "hard",
        "code_snippet": '''class Stack:
    def __init__(self, items=[]):
        self.items = items

    def push(self, item):
        self.items.append(item)

    def peek(self):
        return self.items[-1] if self.items else None''',
        "task_description": (
            "The bug is a mutable default argument: items=[] in __init__ causes all instances to share the same list."
        ),
        "test_hint": "Tests isolation between instances: s1=Stack(); s2=Stack(); s1.push(1) must not appear in s2",
        "correct_line": 2,
        "correct_bug_type": "logic",
        "failing_tests": [
            {"name": "test_instance_isolation", "code": "s1 = Stack(); s2 = Stack(); s1.push(1); assert 1 not in s2.items, 'instances must be separate'"},
        ],
        "passing_tests": [
            {"name": "test_init", "code": "s = Stack(); assert isinstance(s, Stack), 'must create instance'"},
        ],
        "test_cases": [
            {"type": "exec", "call": "s=Stack(); s.push(1); s.peek()", "expected": 1},
        ],
    },

    # ── HARD 2 (Regression Oracle) ─────────────────────────────────────────────
    {
        "task_id": "hard_02",
        "difficulty": "hard",
        "code_snippet": '''import sqlite3
def get_user_by_name(db_path, username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
    result = cursor.fetchone()
    conn.close()
    return result''',
        "task_description": (
            "The bug is SQL injection via f-string. Use parameterized queries instead."
        ),
        "test_hint": "no f-string allowed in SQL. Must use parameterized query.",
        "correct_line": 6,
        "correct_bug_type": "security",
        "failing_tests": [
            {"name": "test_no_fstring_sql", "code": "import inspect; src = inspect.getsource(get_user_by_name); assert \"f'\" not in src and 'f\"' not in src, 'no f-string in SQL'"},
        ],
        "passing_tests": [
            {"name": "test_uses_parameterized", "code": "import inspect; src = inspect.getsource(get_user_by_name); assert '?' in src or '%s' in src or ':username' in src, 'must use parameterized query'"},
        ],
        "test_cases": [
            {"type": "pattern_absent", "pattern": "f\"", "description": "No f-string"},
        ],
    },

    # ── HARD 3 (Regression Oracle) ─────────────────────────────────────────────
    {
        "task_id": "hard_03",
        "difficulty": "hard",
        "code_snippet": '''import hashlib
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()''',
        "task_description": (
            "The bug is using insecure MD5 for password hashing. Replace with SHA-256 or stronger."
        ),
        "test_hint": "md5 must not be used. Should use sha256 or stronger.",
        "correct_line": 3,
        "correct_bug_type": "security",
        "failing_tests": [
            {"name": "test_no_md5", "code": "import inspect; src = inspect.getsource(hash_password); assert 'md5' not in src, 'md5 must not be used'"},
        ],
        "passing_tests": [
            {"name": "test_uses_strong_hash", "code": "import inspect; src = inspect.getsource(hash_password); assert any(h in src for h in ['sha256', 'sha512', 'bcrypt', 'argon2', 'pbkdf2']), 'must use strong hash'"},
        ],
        "test_cases": [
            {"type": "pattern_absent", "pattern": "md5", "description": "MD5 not used"},
        ],
    },

    # ── HARD 4 (Regression Oracle) ───────────────────────────────────────────────
    {
        "task_id": "hard_04",
        "difficulty": "hard",
        "code_snippet": '''import subprocess
def run_command(user_input):
    result = subprocess.run(
        f"echo {user_input}",
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()''',
        "task_description": (
            "The bug is OS command injection via shell=True. Fix: pass command as a list with shell=False."
        ),
        "test_hint": "Must use shell=False and pass command as list, not f-string",
        "correct_line": 3,
        "correct_bug_type": "security",
        "failing_tests": [
            {"name": "test_no_shell_true", "code": "import inspect; src = inspect.getsource(run_command); assert 'shell=True' not in src, 'shell=True is dangerous'"},
            {"name": "test_no_fstring_cmd", "code": "import inspect; src = inspect.getsource(run_command); assert 'f\"echo' not in src and \"f'echo\" not in src, 'no f-string in command'"},
        ],
        "passing_tests": [
            {"name": "test_uses_list_or_shell_false", "code": "import inspect; src = inspect.getsource(run_command); assert 'shell=False' in src or '[' in src, 'must use list form or shell=False'"},
        ],
        "test_cases": [
            {"type": "pattern_absent", "pattern": "shell=True", "description": "No shell=True"},
        ],
    },
]
