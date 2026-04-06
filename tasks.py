"""
tasks.py — All debugging tasks for the BugHunterRL environment.

All tasks use the Regression Test Oracle format:
  each has failing_tests (must fix) and passing_tests (must not break).
Includes new Project-Based (Multi-File) debugging tasks.
"""
import random

# Base Tasks (Single File)
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
            "The bug is initializing product to 0 instead of 1."
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
            "Binary search index of target or -1. The bug is integer division — mid should use // not /."
        ),
        "test_hint": "Tested with: ([1,3,5,7,9], 5)→2, ([1,3,5], 6)→-1, ([], 1)→-1",
        "correct_line": 4,
        "correct_bug_type": "runtime",
        "failing_tests": [
            {"name": "test_found_middle", "code": "assert binary_search([1, 3, 5, 7, 9], 5) == 2, 'should find 5 at index 2'"},
        ],
        "passing_tests": [
            {"name": "test_not_found", "code": "assert binary_search([1, 3, 5], 6) == -1, 'should return -1'"},
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
            "Recursively flatten a deeply nested list. The bug is returning nested instead of result."
        ),
        "test_hint": "[1,[2,3]]→[1,2,3]",
        "correct_line": 8,
        "correct_bug_type": "logic",
        "failing_tests": [
            {"name": "test_nested", "code": "assert flatten_list([1, [2, 3]]) == [1, 2, 3]"},
        ],
        "passing_tests": [
            {"name": "test_empty", "code": "assert flatten_list([]) == []"},
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
            "Bug: mutable default argument items=[] causes instance state sharing."
        ),
        "test_hint": "s1=Stack(); s2=Stack(); s1.push(1); assert 1 not in s2.items",
        "correct_line": 2,
        "correct_bug_type": "logic",
        "failing_tests": [
            {"name": "test_isolation", "code": "s1 = Stack(); s2 = Stack(); s1.push(1); assert 1 not in s2.items"},
        ],
        "passing_tests": [
            {"name": "test_peek", "code": "s = Stack(); s.push(5); assert s.peek() == 5"},
        ],
    },

    # ── HARD 2 (SQL Injection) ──────────────────────────────────────────────────
    {
        "task_id": "hard_02",
        "difficulty": "hard",
        "code_snippet": '''import sqlite3
def get_user(db, name):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
    return cursor.fetchone()''',
        "task_description": (
            "Security vulnerability: SQL injection via f-string query. Use parameterized query."
        ),
        "test_hint": "no f' in SQL; use '?'",
        "correct_line": 5,
        "correct_bug_type": "security",
        "failing_tests": [
            {"name": "test_no_fstring", "code": "import inspect; src = inspect.getsource(get_user); assert \"f'\" not in src and 'f\"' not in src"},
        ],
        "passing_tests": [
            {"name": "test_parameterized", "code": "import inspect; src = inspect.getsource(get_user); assert '?' in src or '%s' in src"},
        ],
    },

    # ── STEP 3: NEW TASK CATEGORY — Project-Based (Multi-File) ─────────────────
    {
        "task_id": "multi_file_01",
        "difficulty": "hard",
        "code_snippet": '''# --- project_structure/auth.py ---
import hashlib
def hash_pswd(password):
    # SECURITY BUG: Using md5 is insecure for password hashing
    return hashlib.md5(password.encode()).hexdigest()

# --- project_structure/api.py ---
from auth import hash_pswd
def create_user(username, pswd):
    token = hash_pswd(pswd)
    return {"user": username, "token": token}''',
        "task_description": (
            "Multi-file Project Bug: The 'auth.py' module uses insecure hashlib.md5(). "
            "The agent must identify the insecure hash in auth.py and replace it with hashlib.sha256()."
        ),
        "test_hint": "Replace md5 with sha256 in the auth.py section of the snippet.",
        "correct_line": 5,
        "correct_bug_type": "security",
        "failing_tests": [
            {"name": "test_no_md5", "code": "assert 'md5' not in code_snippet, 'md5 matches insecure pattern'"},
        ],
        "passing_tests": [
            {"name": "test_uses_sha256", "code": "assert 'sha256' in code_snippet, 'must upgrade to sha256'"},
            {"name": "test_api_ref", "code": "assert 'from auth import hash_pswd' in code_snippet, 'do not break imports'"},
        ],
    }
]

# STEP 4: Dynamic Task Template Helper
def get_randomized_task():
    """Generates a randomized variation of a task to prevent agent memorization."""
    # Only randomize easy/medium tasks for now to ensure grader stability
    base_task = random.choice([t for t in TASKS if t["difficulty"] != "hard"])
    
    # Randomize variable names
    var_map = {
        "lst": random.choice(["items", "nums", "data", "collection"]),
        "result": random.choice(["out", "final", "acc", "output"]),
        "count": random.choice(["total", "val", "n_items", "acc"]),
    }
    
    task_copy = base_task.copy()
    code = task_copy["code_snippet"]
    for old, new in var_map.items():
        code = code.replace(old, new)
    
    task_copy["code_snippet"] = code
    task_copy["task_id"] = f"dynamic_{base_task['task_id']}_{random.randint(100,999)}"
    return task_copy
