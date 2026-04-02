"""
tasks.py — All debugging tasks for the Code Debugger environment.

Tasks 1-3 (easy/medium/hard) use the Regression Test Oracle reward:
  each has failing_tests (must fix) and passing_tests (must not break).

Tasks 4-9 use the legacy execution-based grader.
"""

TASKS = [

    # ── EASY (Regression Oracle) ────────────────────────────────────────────
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
        "test_hint": (
            "Tested with: [1,2,3]→[2,4,6], [5]→[10], []→[], result must be a list"
        ),
        "correct_line": 3,
        "correct_bug_type": "logic",
        "failing_tests": [
            {
                "name": "test_full_list",
                "code": "assert double_all([1, 2, 3]) == [2, 4, 6], 'all elements must be doubled'",
            },
            {
                "name": "test_single_element",
                "code": "assert double_all([5]) == [10], 'single element must be doubled'",
            },
        ],
        "passing_tests": [
            {
                "name": "test_empty_list",
                "code": "assert double_all([]) == [], 'empty list must return empty'",
            },
            {
                "name": "test_returns_list",
                "code": "assert isinstance(double_all([1, 2]), list), 'must return a list'",
            },
        ],
    },

    # ── MEDIUM (Regression Oracle) ───────────────────────────────────────────
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
        "test_hint": (
            "Tested with: []→0, [5]→5, [1,2]→3, [1,2,3,4,5]→15"
        ),
        "correct_line": 4,
        "correct_bug_type": "runtime",
        "failing_tests": [
            {
                "name": "test_single_item",
                "code": "assert recursive_sum([5]) == 5, 'single item sum'",
            },
            {
                "name": "test_two_items",
                "code": "assert recursive_sum([1, 2]) == 3, 'two items sum'",
            },
            {
                "name": "test_large_input",
                "code": "assert recursive_sum([1, 2, 3, 4, 5]) == 15, 'large input sum'",
            },
        ],
        "passing_tests": [
            {
                "name": "test_empty_input",
                "code": "assert recursive_sum([]) == 0, 'empty list returns 0'",
            },
            {
                "name": "test_returns_integer",
                "code": "assert isinstance(recursive_sum([]), int), 'must return int'",
            },
        ],
    },

    # ── HARD (Regression Oracle) ─────────────────────────────────────────────
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
            "Stack is a simple stack class. The bug is a mutable default argument: "
            "items=[] in __init__ causes ALL Stack instances to share the same list. "
            "Fix: use None as default and assign self.items = items if items is not None else []."
        ),
        "test_hint": (
            "Tests isolation between instances: s1=Stack(); s2=Stack(); s1.push(1) must not appear in s2"
        ),
        "correct_line": 2,
        "correct_bug_type": "logic",
        "failing_tests": [
            {
                "name": "test_instance_isolation",
                "code": (
                    "s1 = Stack(); s2 = Stack(); s1.push(1); "
                    "assert 1 not in s2.items, 'instances must not share state'"
                ),
            },
            {
                "name": "test_append_doesnt_affect_other",
                "code": (
                    "s1 = Stack(); s2 = Stack(); s1.push('x'); "
                    "assert s2.items == [], 's2 must remain empty'"
                ),
            },
            {
                "name": "test_multiple_instances",
                "code": (
                    "s1 = Stack(); s2 = Stack(); s3 = Stack(); "
                    "s1.push(99); assert s2.items is not s1.items, 'items must be separate lists'"
                ),
            },
        ],
        "passing_tests": [
            {
                "name": "test_init_creates_instance",
                "code": "s = Stack(); assert isinstance(s, Stack), 'must create Stack instance'",
            },
            {
                "name": "test_push_works",
                "code": "s = Stack(); s.push(42); assert 42 in s.items, 'push must add item'",
            },
        ],
    },

    # ── EASY 2 (legacy grader) ───────────────────────────────────────────────
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
            "Case-insensitive. Must return True for palindromes, False otherwise."
        ),
        "test_hint": "Tested with: 'racecar'→True, 'hello'→False, 'A'→True, ''→True",
        "correct_line": 4,
        "correct_bug_type": "runtime",
        "test_cases": [
            {"type": "exec", "call": "is_palindrome('racecar')", "expected": True},
            {"type": "exec", "call": "is_palindrome('hello')",   "expected": False},
            {"type": "exec", "call": "is_palindrome('A')",        "expected": True},
            {"type": "exec", "call": "is_palindrome('')",         "expected": True},
        ],
    },

    # ── EASY 3 (legacy grader) ───────────────────────────────────────────────
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
            "Count the number of vowels in a string (case-insensitive)."
        ),
        "test_hint": "Tested with: 'hello'→2, 'AEIOU'→5, 'rhythm'→0, ''→0",
        "correct_line": 6,
        "correct_bug_type": "logic",
        "test_cases": [
            {"type": "exec", "call": "count_vowels('hello')",   "expected": 2},
            {"type": "exec", "call": "count_vowels('AEIOU')",   "expected": 5},
            {"type": "exec", "call": "count_vowels('rhythm')",  "expected": 0},
            {"type": "exec", "call": "count_vowels('')",        "expected": 0},
        ],
    },

    # ── MEDIUM 2 (legacy grader) ─────────────────────────────────────────────
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
            "The bug is integer division — mid should use // not / (causes TypeError in Python 3)."
        ),
        "test_hint": "Tested with: ([1,3,5,7,9], 5)→2, ([1,3,5], 6)→-1, ([], 1)→-1",
        "correct_line": 4,
        "correct_bug_type": "runtime",
        "test_cases": [
            {"type": "exec", "call": "binary_search([1, 3, 5, 7, 9], 5)", "expected": 2},
            {"type": "exec", "call": "binary_search([1, 3, 5, 7, 9], 1)", "expected": 0},
            {"type": "exec", "call": "binary_search([1, 3, 5],       6)", "expected": -1},
            {"type": "exec", "call": "binary_search([],             1)", "expected": -1},
        ],
    },

    # ── MEDIUM 3 (legacy grader) ─────────────────────────────────────────────
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
            "The bug is in the return statement — it returns nested instead of result."
        ),
        "test_hint": "Tested with: [1,[2,3],[4,[5,6]]]→[1,2,3,4,5,6], []→[], [1,2,3]→[1,2,3]",
        "correct_line": 8,
        "correct_bug_type": "logic",
        "test_cases": [
            {"type": "exec", "call": "flatten_list([1, [2, 3], [4, [5, 6]]])", "expected": [1, 2, 3, 4, 5, 6]},
            {"type": "exec", "call": "flatten_list([])",                        "expected": []},
            {"type": "exec", "call": "flatten_list([1, 2, 3])",                 "expected": [1, 2, 3]},
            {"type": "exec", "call": "flatten_list([[1, [2]], 3])",             "expected": [1, 2, 3]},
        ],
    },

    # ── HARD 2 (legacy grader) ───────────────────────────────────────────────
    {
        "task_id": "hard_02",
        "difficulty": "hard",
        "code_snippet": '''import sqlite3

def get_user_by_name(db_path, username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE username = \'{username}\'")
    result = cursor.fetchone()
    conn.close()
    return result''',
        "task_description": (
            "Retrieve a user record from a SQLite database by username. "
            "The bug is an SQL injection vulnerability — the f-string query allows "
            "attackers to inject arbitrary SQL. Use parameterized queries instead."
        ),
        "test_hint": "Must use parameterized query (?), not f-string interpolation",
        "correct_line": 6,
        "correct_bug_type": "security",
        "test_cases": [
            {"type": "pattern_absent",      "pattern": "f\"",   "description": "No f-string in SQL query"},
            {"type": "pattern_absent",      "pattern": "f'",    "description": "No f-string interpolation"},
            {"type": "pattern_present_any", "patterns": ["?", "%s", ":username"],
             "description": "Uses parameterized query placeholder"},
        ],
    },

    # ── HARD 3 (legacy grader) ───────────────────────────────────────────────
    {
        "task_id": "hard_03",
        "difficulty": "hard",
        "code_snippet": '''import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed''',
        "task_description": (
            "Hash a password for secure storage. "
            "The bug is using MD5 which is cryptographically broken for passwords. "
            "Use hashlib.sha256 with a salt, or ideally bcrypt/argon2. "
            "At minimum replace md5 with sha256."
        ),
        "test_hint": "Must not use md5. Should use sha256 or stronger.",
        "correct_line": 4,
        "correct_bug_type": "security",
        "test_cases": [
            {"type": "pattern_absent",      "pattern": "md5",    "description": "MD5 not used"},
            {"type": "pattern_present_any", "patterns": ["sha256", "sha512", "bcrypt", "argon2", "pbkdf2"],
             "description": "Uses strong hashing algorithm"},
        ],
    },
]
