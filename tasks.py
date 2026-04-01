"""
tasks.py — All 9 debugging tasks for the Code Debugger environment.
3 easy (syntax/obvious bugs), 3 medium (subtle logic bugs), 3 hard (security vulnerabilities).
"""

TASKS = [

    # ─── EASY TASKS ────────────────────────────────────────────────────────────

    {
        "task_id": "easy_01",
        "difficulty": "easy",
        "code_snippet": '''def calculate_average(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total / len(numbers)

result = calculate_average([])
print(result)''',
        "task_description": "Calculate the average of a list of numbers. Must return 0 for an empty list instead of crashing.",
        "test_hint": "Tested with: empty list (expect 0), single element [5] (expect 5.0), normal list [1,2,3,4] (expect 2.5)",
        "correct_line": 5,
        "correct_bug_type": "runtime",
        "test_cases": [
            {"type": "exec", "setup": "", "call": "calculate_average([])", "expected": 0},
            {"type": "exec", "setup": "", "call": "calculate_average([5])", "expected": 5.0},
            {"type": "exec", "setup": "", "call": "calculate_average([1,2,3,4])", "expected": 2.5},
        ]
    },

    {
        "task_id": "easy_02",
        "difficulty": "easy",
        "code_snippet": '''def is_palindrome(s):
    s = s.lower()
    left = 0
    right = len(s)
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True''',
        "task_description": "Check if a string is a palindrome (case-insensitive). 'racecar' -> True, 'hello' -> False.",
        "test_hint": "Tested with: 'racecar' (True), 'hello' (False), 'Madam' (True), '' (True)",
        "correct_line": 4,
        "correct_bug_type": "runtime",
        "test_cases": [
            {"type": "exec", "setup": "", "call": "is_palindrome('racecar')", "expected": True},
            {"type": "exec", "setup": "", "call": "is_palindrome('hello')", "expected": False},
            {"type": "exec", "setup": "", "call": "is_palindrome('Madam')", "expected": True},
            {"type": "exec", "setup": "", "call": "is_palindrome('')", "expected": True},
        ]
    },

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
        "task_description": "Count the number of vowels in a string (case-insensitive).",
        "test_hint": "Tested with: 'hello' (2), 'AEIOU' (5), 'rhythm' (0), '' (0)",
        "correct_line": 6,
        "correct_bug_type": "logic",
        "test_cases": [
            {"type": "exec", "setup": "", "call": "count_vowels('hello')", "expected": 2},
            {"type": "exec", "setup": "", "call": "count_vowels('AEIOU')", "expected": 5},
            {"type": "exec", "setup": "", "call": "count_vowels('rhythm')", "expected": 0},
            {"type": "exec", "setup": "", "call": "count_vowels('')", "expected": 0},
        ]
    },

    # ─── MEDIUM TASKS ──────────────────────────────────────────────────────────

    {
        "task_id": "medium_01",
        "difficulty": "medium",
        "code_snippet": '''def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) / 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1''',
        "task_description": "Binary search: return the index of target in a sorted list, or -1 if not found.",
        "test_hint": "Tested with sorted list [1,3,5,7,9]: find 5 (index 2), find 1 (index 0), find 9 (index 4), find 4 (returns -1)",
        "correct_line": 4,
        "correct_bug_type": "logic",
        "test_cases": [
            {"type": "exec", "setup": "", "call": "binary_search([1,3,5,7,9], 5)", "expected": 2},
            {"type": "exec", "setup": "", "call": "binary_search([1,3,5,7,9], 1)", "expected": 0},
            {"type": "exec", "setup": "", "call": "binary_search([1,3,5,7,9], 9)", "expected": 4},
            {"type": "exec", "setup": "", "call": "binary_search([1,3,5,7,9], 4)", "expected": -1},
        ]
    },

    {
        "task_id": "medium_02",
        "difficulty": "medium",
        "code_snippet": '''def flatten_list(nested):
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return nested''',
        "task_description": "Recursively flatten a nested list of any depth into a single flat list.",
        "test_hint": "Tested with: [1,[2,3],[4,[5,6]]] -> [1,2,3,4,5,6], [] -> [], [1,2,3] -> [1,2,3]",
        "correct_line": 8,
        "correct_bug_type": "logic",
        "test_cases": [
            {"type": "exec", "setup": "", "call": "flatten_list([1, [2, 3], [4, [5, 6]]])", "expected": [1,2,3,4,5,6]},
            {"type": "exec", "setup": "", "call": "flatten_list([])", "expected": []},
            {"type": "exec", "setup": "", "call": "flatten_list([1, 2, 3])", "expected": [1,2,3]},
            {"type": "exec", "setup": "", "call": "flatten_list([[1, [2]], 3])", "expected": [1,2,3]},
        ]
    },

    {
        "task_id": "medium_03",
        "difficulty": "medium",
        "code_snippet": '''def compute_product(nums):
    total = 0
    for n in nums:
        total *= n
    return total

def compute_sum(nums):
    return sum(nums)

def compute_stats(nums):
    return {
        "sum": compute_sum(nums),
        "product": compute_product(nums),
        "average": compute_sum(nums) / len(nums) if nums else 0
    }''',
        "task_description": "compute_product should return the product of all numbers. compute_stats should return correct sum, product, and average.",
        "test_hint": "product([1,2,3,4,5]) should be 120 not 0. The bug is in the initialization of total in compute_product.",
        "correct_line": 2,
        "correct_bug_type": "logic",
        "test_cases": [
            {"type": "exec", "setup": "", "call": "compute_product([1,2,3,4,5])", "expected": 120},
            {"type": "exec", "setup": "", "call": "compute_product([2,3,4])", "expected": 24},
            {"type": "exec", "setup": "", "call": "compute_product([7])", "expected": 7},
            {"type": "exec", "setup": "", "call": "compute_stats([1,2,3])['product']", "expected": 6},
        ]
    },

    # ─── HARD TASKS (Security Vulnerabilities) ─────────────────────────────────

    {
        "task_id": "hard_01",
        "difficulty": "hard",
        "code_snippet": '''import sqlite3

def get_user_by_name(db_path, username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = \'{username}\'"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

# This function is called with raw user input:
# get_user_by_name("app.db", user_input_from_form)''',
        "task_description": "Fetch a user from SQLite by username. The current code is vulnerable to SQL injection — must be fixed using parameterized queries.",
        "test_hint": "Fixed code must use parameterized query with ? placeholder. Will test that injection string like '; DROP TABLE users; -- does not cause issues.",
        "correct_line": 6,
        "correct_bug_type": "security",
        "test_cases": [
            {"type": "pattern_absent", "pattern": 'f"', "description": "Must not use f-string for SQL query"},
            {"type": "pattern_absent", "pattern": "f'", "description": "Must not use f-string (single quote) for SQL query"},
            {"type": "pattern_absent", "pattern": "% username", "description": "Must not use % string formatting for SQL"},
            {"type": "pattern_present", "pattern": "?", "description": "Must use ? parameterized placeholder"},
            {"type": "pattern_present", "pattern": "cursor.execute", "description": "Must still use cursor.execute"},
        ]
    },

    {
        "task_id": "hard_02",
        "difficulty": "hard",
        "code_snippet": '''import hashlib

def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

def verify_password(plain_password: str, stored_hash: str) -> bool:
    return hash_password(plain_password) == stored_hash

def create_user_record(username: str, password: str) -> dict:
    return {
        "username": username,
        "password_hash": hash_password(password),
        "created_at": "2024-01-01"
    }''',
        "task_description": "Hash passwords for secure storage. MD5 is cryptographically broken for passwords and must be replaced with a secure algorithm.",
        "test_hint": "MD5 must not appear in fixed code. Must use hashlib.sha256 at minimum. The hash output for any password must be 64 hex characters (SHA-256) or longer.",
        "correct_line": 4,
        "correct_bug_type": "security",
        "test_cases": [
            {"type": "pattern_absent", "pattern": "md5", "description": "Must not use MD5"},
            {"type": "pattern_absent", "pattern": "MD5", "description": "Must not use MD5 (uppercase)"},
            {"type": "pattern_present", "pattern": "sha256", "description": "Must use SHA-256 or stronger"},
            {"type": "code_runs", "code": "import hashlib\nhash_fn = lambda p: hashlib.sha256(p.encode()).hexdigest()\nresult = hash_fn('testpass123')\nassert len(result) == 64, f'Expected 64 chars, got {len(result)}'", "description": "SHA-256 hash must be 64 hex chars"},
        ]
    },

    {
        "task_id": "hard_03",
        "difficulty": "hard",
        "code_snippet": '''def safe_calculate(user_formula: str) -> float:
    """
    Evaluate a user-provided math formula.
    Supports: integers, +, -, *, /, parentheses
    Example: safe_calculate("2 + 3 * (4 - 1)") == 11.0
    """
    allowed_chars = set("0123456789+-*/() .")
    for char in user_formula:
        if char not in allowed_chars:
            raise ValueError(f"Invalid character: {char}")
    return eval(user_formula)''',
        "task_description": "Safely evaluate math expressions from user input. The character whitelist is insufficient — eval() can still execute dangerous code via built-ins.",
        "test_hint": "eval() must be removed. Use ast.literal_eval or ast.parse with NodeVisitor. safe_calculate('2+3') must return 5, safe_calculate('2*3+4') must return 10.",
        "correct_line": 11,
        "correct_bug_type": "security",
        "test_cases": [
            {"type": "pattern_absent", "pattern": "eval(", "description": "Must not use eval()"},
            {"type": "pattern_present_any", "patterns": ["ast.parse", "ast.literal_eval", "ast.NodeVisitor", "operator."], "description": "Must use ast module or operator-based safe evaluation"},
            {"type": "code_runs", "code": "import ast\nimport operator\ndef safe_calc(expr):\n    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}\n    def eval_node(node):\n        if isinstance(node, ast.Constant): return node.value\n        if isinstance(node, ast.BinOp): return ops[type(node.op)](eval_node(node.left), eval_node(node.right))\n        raise ValueError('unsafe')\n    return eval_node(ast.parse(expr, mode='eval').body)\nassert safe_calc('2+3') == 5\nassert safe_calc('2*3+4') == 10", "description": "AST-based evaluator must work correctly"},
        ]
    },
]
