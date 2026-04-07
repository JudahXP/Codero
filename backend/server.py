from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# ============== MODELS ==============

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    xp: int = 0
    level: int = 1
    streak: int = 0
    hearts: int = 5
    max_hearts: int = 5
    gems: int = 0
    last_activity: Optional[str] = None
    badges: List[str] = []
    friends: List[str] = []
    daily_goal: int = 50
    daily_xp: int = 0
    combo_multiplier: float = 1.0
    total_lessons_completed: int = 0
    settings: Dict[str, Any] = {}
    created_at: str

class UserProgress(BaseModel):
    user_id: str
    language: str
    lesson_id: str
    completed: bool = False
    score: int = 0
    completed_at: Optional[str] = None

class LessonAnswer(BaseModel):
    lesson_id: str
    language: str
    answers: List[dict]
    time_taken: Optional[int] = None  # seconds

class FriendRequest(BaseModel):
    friend_username: str

class SettingsUpdate(BaseModel):
    settings: Dict[str, Any]

class DailyChallengeAnswer(BaseModel):
    challenge_id: str
    answers: List[dict]

# ============== HELPER FUNCTIONS ==============

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    session = await db.sessions.find_one({"token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.users.find_one({"id": session["user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ============== CODE VALIDATION ==============

def validate_code(user_code: str, solution: str, language: str, exercise_type: str = "code") -> tuple:
    """Enhanced code validation with multiple checks"""
    user_code = user_code.strip()
    solution = solution.strip()
    
    if not user_code:
        return False, "No code provided"
    
    # Normalize whitespace
    user_normalized = re.sub(r'\s+', ' ', user_code.lower())
    solution_normalized = re.sub(r'\s+', ' ', solution.lower())
    
    # Extract key patterns based on language
    patterns_to_check = []
    
    if language == "python":
        # Check for key Python constructs
        if "print" in solution.lower():
            patterns_to_check.append(r'print\s*\(')
        if "def " in solution.lower():
            patterns_to_check.append(r'def\s+\w+\s*\(')
        if "class " in solution.lower():
            patterns_to_check.append(r'class\s+\w+')
        if "for " in solution.lower():
            patterns_to_check.append(r'for\s+\w+\s+in\s+')
        if "while " in solution.lower():
            patterns_to_check.append(r'while\s+')
        if "if " in solution.lower():
            patterns_to_check.append(r'if\s+')
        if "return " in solution.lower():
            patterns_to_check.append(r'return\s+')
        if "import " in solution.lower():
            patterns_to_check.append(r'import\s+')
        if "lambda" in solution.lower():
            patterns_to_check.append(r'lambda\s+')
            
    elif language in ["javascript", "typescript"]:
        if "console.log" in solution.lower():
            patterns_to_check.append(r'console\.log\s*\(')
        if "function" in solution.lower():
            patterns_to_check.append(r'function\s+\w*\s*\(')
        if "const " in solution.lower() or "let " in solution.lower():
            patterns_to_check.append(r'(const|let|var)\s+\w+')
        if "=>" in solution:
            patterns_to_check.append(r'=>')
        if "async" in solution.lower():
            patterns_to_check.append(r'async\s+')
        if "await" in solution.lower():
            patterns_to_check.append(r'await\s+')
            
    elif language in ["java", "kotlin", "csharp"]:
        if "System.out" in solution:
            patterns_to_check.append(r'System\.out\.print')
        if "public " in solution.lower():
            patterns_to_check.append(r'public\s+')
        if "class " in solution.lower():
            patterns_to_check.append(r'class\s+\w+')
        if "void " in solution.lower():
            patterns_to_check.append(r'void\s+\w+')
            
    elif language in ["cpp", "c"]:
        if "cout" in solution.lower():
            patterns_to_check.append(r'cout\s*<<')
        if "printf" in solution.lower():
            patterns_to_check.append(r'printf\s*\(')
        if "#include" in solution.lower():
            patterns_to_check.append(r'#include\s*[<"]')
            
    elif language == "shell":
        if "echo" in solution.lower():
            patterns_to_check.append(r'echo\s+')
        if "if " in solution.lower():
            patterns_to_check.append(r'if\s+\[')
        if "for " in solution.lower():
            patterns_to_check.append(r'for\s+\w+\s+in')
            
    elif language == "rust":
        if "println!" in solution:
            patterns_to_check.append(r'println!\s*\(')
        if "fn " in solution.lower():
            patterns_to_check.append(r'fn\s+\w+')
        if "let " in solution.lower():
            patterns_to_check.append(r'let\s+(mut\s+)?\w+')
            
    elif language == "go":
        if "fmt.Print" in solution:
            patterns_to_check.append(r'fmt\.Print')
        if "func " in solution.lower():
            patterns_to_check.append(r'func\s+\w*')
            
    elif language == "elixir":
        if "IO.puts" in solution:
            patterns_to_check.append(r'IO\.puts')
        if "def " in solution.lower():
            patterns_to_check.append(r'def\s+\w+')
        if "defmodule" in solution.lower():
            patterns_to_check.append(r'defmodule\s+\w+')
            
    elif language == "zig":
        if "std.debug.print" in solution:
            patterns_to_check.append(r'std\.debug\.print')
        if "fn " in solution.lower():
            patterns_to_check.append(r'fn\s+\w+')
    
    # Check patterns
    patterns_matched = 0
    for pattern in patterns_to_check:
        if re.search(pattern, user_code, re.IGNORECASE):
            patterns_matched += 1
    
    # Calculate score
    if not patterns_to_check:
        # Fallback: simple similarity check
        if user_normalized == solution_normalized:
            return True, "Perfect match!"
        elif solution_normalized in user_normalized or user_normalized in solution_normalized:
            return True, "Good solution!"
        elif len(user_code) >= len(solution) * 0.5:
            return True, "Code accepted"
        return False, "Code doesn't match expected solution"
    
    match_ratio = patterns_matched / len(patterns_to_check) if patterns_to_check else 0
    
    if match_ratio >= 0.7:
        return True, "Great code!"
    elif match_ratio >= 0.5:
        return True, "Good attempt!"
    elif match_ratio >= 0.3:
        return True, "Partial solution accepted"
    
    return False, "Code doesn't include required elements"

# ============== PROGRAMMING LANGUAGES DATA ==============

LANGUAGES = [
    {"id": "python", "name": "Python", "icon": "logo-python", "color": "#3776AB", "description": "Great for beginners and AI", "difficulty": "beginner"},
    {"id": "javascript", "name": "JavaScript", "icon": "logo-javascript", "color": "#F7DF1E", "description": "The language of the web", "difficulty": "beginner"},
    {"id": "java", "name": "Java", "icon": "cafe", "color": "#ED8B00", "description": "Enterprise & Android apps", "difficulty": "intermediate"},
    {"id": "cpp", "name": "C++", "icon": "code-slash", "color": "#00599C", "description": "Performance & game dev", "difficulty": "advanced"},
    {"id": "csharp", "name": "C#", "icon": "game-controller", "color": "#239120", "description": "Unity & Windows apps", "difficulty": "intermediate"},
    {"id": "ruby", "name": "Ruby", "icon": "diamond", "color": "#CC342D", "description": "Elegant web development", "difficulty": "beginner"},
    {"id": "go", "name": "Go", "icon": "rocket", "color": "#00ADD8", "description": "Fast & concurrent", "difficulty": "intermediate"},
    {"id": "rust", "name": "Rust", "icon": "shield-checkmark", "color": "#DEA584", "description": "Safe systems programming", "difficulty": "advanced"},
    {"id": "swift", "name": "Swift", "icon": "logo-apple", "color": "#FA7343", "description": "iOS & macOS apps", "difficulty": "intermediate"},
    {"id": "kotlin", "name": "Kotlin", "icon": "logo-android", "color": "#7F52FF", "description": "Modern Android dev", "difficulty": "intermediate"},
    {"id": "typescript", "name": "TypeScript", "icon": "code-working", "color": "#3178C6", "description": "Typed JavaScript", "difficulty": "intermediate"},
    {"id": "php", "name": "PHP", "icon": "server", "color": "#777BB4", "description": "Web server scripting", "difficulty": "beginner"},
    {"id": "sql", "name": "SQL", "icon": "file-tray-stacked", "color": "#4479A1", "description": "Database queries", "difficulty": "beginner"},
    {"id": "html_css", "name": "HTML/CSS", "icon": "globe", "color": "#E34F26", "description": "Web page structure", "difficulty": "beginner"},
    {"id": "skript", "name": "Skript", "icon": "cube", "color": "#6B8E23", "description": "Minecraft scripting", "difficulty": "beginner"},
    {"id": "lua", "name": "Lua", "icon": "moon", "color": "#000080", "description": "Game scripting & Roblox", "difficulty": "beginner"},
    # New languages
    {"id": "zig", "name": "Zig", "icon": "flash", "color": "#F7A41D", "description": "Modern systems language", "difficulty": "advanced"},
    {"id": "elixir", "name": "Elixir", "icon": "water", "color": "#4B275F", "description": "Functional & concurrent", "difficulty": "intermediate"},
    {"id": "shell", "name": "Shell", "icon": "terminal", "color": "#4EAA25", "description": "Bash & command line", "difficulty": "beginner"},
    {"id": "haskell", "name": "Haskell", "icon": "analytics", "color": "#5D4F85", "description": "Pure functional", "difficulty": "advanced"},
]

# ============== BADGES ==============

BADGES = [
    {"id": "first_lesson", "name": "First Steps", "description": "Complete your first lesson", "icon": "footsteps", "xp_reward": 10},
    {"id": "streak_3", "name": "On Fire!", "description": "3 day streak", "icon": "flame", "xp_reward": 25},
    {"id": "streak_7", "name": "Week Warrior", "description": "7 day streak", "icon": "calendar", "xp_reward": 50},
    {"id": "streak_30", "name": "Monthly Master", "description": "30 day streak", "icon": "trophy", "xp_reward": 200},
    {"id": "xp_100", "name": "Century Club", "description": "Earn 100 XP", "icon": "star", "xp_reward": 20},
    {"id": "xp_500", "name": "XP Hunter", "description": "Earn 500 XP", "icon": "medal", "xp_reward": 50},
    {"id": "xp_1000", "name": "XP Legend", "description": "Earn 1000 XP", "icon": "ribbon", "xp_reward": 100},
    {"id": "xp_5000", "name": "XP Master", "description": "Earn 5000 XP", "icon": "diamond", "xp_reward": 250},
    {"id": "perfect_lesson", "name": "Perfectionist", "description": "100% on a lesson", "icon": "checkmark-circle", "xp_reward": 15},
    {"id": "polyglot", "name": "Polyglot", "description": "Study 3 languages", "icon": "language", "xp_reward": 50},
    {"id": "polyglot_master", "name": "Polyglot Master", "description": "Study 5 languages", "icon": "earth", "xp_reward": 100},
    {"id": "night_owl", "name": "Night Owl", "description": "Study after midnight", "icon": "moon", "xp_reward": 10},
    {"id": "early_bird", "name": "Early Bird", "description": "Study before 6 AM", "icon": "sunny", "xp_reward": 10},
    {"id": "social_butterfly", "name": "Social Butterfly", "description": "Add 5 friends", "icon": "people", "xp_reward": 30},
    {"id": "speed_demon", "name": "Speed Demon", "description": "Complete lesson under 2 min", "icon": "speedometer", "xp_reward": 25},
    {"id": "combo_king", "name": "Combo King", "description": "Get 5x combo multiplier", "icon": "flash", "xp_reward": 40},
    {"id": "daily_achiever", "name": "Daily Achiever", "description": "Meet daily goal 7 days", "icon": "fitness", "xp_reward": 75},
    {"id": "lesson_master", "name": "Lesson Master", "description": "Complete 50 lessons", "icon": "school", "xp_reward": 100},
    {"id": "lesson_legend", "name": "Lesson Legend", "description": "Complete 100 lessons", "icon": "library", "xp_reward": 200},
    {"id": "no_mistakes", "name": "Flawless", "description": "Complete 5 lessons with no mistakes", "icon": "shield", "xp_reward": 60},
]

# ============== LESSON GENERATION WITH 10 EXERCISES ==============

def generate_exercises_python(lesson_id: str, lesson_title: str, unit: int) -> List[dict]:
    """Generate 10 exercises for Python lessons"""
    exercises = []
    
    if "hello world" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "What function prints output in Python?", "options": ["print()", "echo()", "console.log()", "System.out.println()"], "correct": 0},
            {"type": "multiple_choice", "question": "Which is the correct syntax to print 'Hello'?", "options": ["print('Hello')", "print Hello", "echo 'Hello'", "printf('Hello')"], "correct": 0},
            {"type": "code", "question": "Write code to print 'Hello, World!'", "starter": "", "solution": "print('Hello, World!')", "hint": "Use the print() function with a string"},
            {"type": "fill_blank", "question": "Complete: ___('Hello')", "answer": "print"},
            {"type": "multiple_choice", "question": "What type of quotes can you use for strings?", "options": ["Both single and double", "Only single", "Only double", "Neither"], "correct": 0},
            {"type": "code", "question": "Print your name", "starter": "", "solution": "print('YourName')", "hint": "Replace YourName with any name"},
            {"type": "multiple_choice", "question": "What happens if you forget the closing parenthesis?", "options": ["Syntax error", "Nothing prints", "Prints None", "Program crashes"], "correct": 0},
            {"type": "fill_blank", "question": "print('Hi')  # This is a ___", "answer": "comment"},
            {"type": "code", "question": "Print two lines: 'Line 1' and 'Line 2'", "starter": "", "solution": "print('Line 1')\nprint('Line 2')", "hint": "Use two print statements"},
            {"type": "multiple_choice", "question": "Which prints on a new line by default?", "options": ["print() in Python", "printf() in C", "echo in PHP", "All of the above"], "correct": 0},
        ]
    elif "variable" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "How do you create a variable in Python?", "options": ["name = 'John'", "var name = 'John'", "let name = 'John'", "String name = 'John'"], "correct": 0},
            {"type": "code", "question": "Create a variable called 'age' with value 25", "starter": "", "solution": "age = 25", "hint": "variable_name = value"},
            {"type": "multiple_choice", "question": "What type is the variable: x = 3.14?", "options": ["float", "int", "str", "bool"], "correct": 0},
            {"type": "fill_blank", "question": "x ___ 10  # Assign 10 to x", "answer": "="},
            {"type": "multiple_choice", "question": "Which is a valid variable name?", "options": ["my_var", "2var", "my-var", "my var"], "correct": 0},
            {"type": "code", "question": "Create two variables: x=5 and y=10, then print their sum", "starter": "", "solution": "x = 5\ny = 10\nprint(x + y)", "hint": "Create variables then use + to add"},
            {"type": "multiple_choice", "question": "Can you change a variable's value after creating it?", "options": ["Yes", "No", "Only if it's a number", "Only once"], "correct": 0},
            {"type": "fill_blank", "question": "To check a variable's type, use _____(x)", "answer": "type"},
            {"type": "code", "question": "Swap values of a=1 and b=2", "starter": "a = 1\nb = 2\n", "solution": "a = 1\nb = 2\na, b = b, a", "hint": "Python allows tuple unpacking"},
            {"type": "multiple_choice", "question": "What is None in Python?", "options": ["Absence of value", "Zero", "Empty string", "False"], "correct": 0},
        ]
    elif "data type" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "Which is a string?", "options": ["'Hello'", "42", "3.14", "True"], "correct": 0},
            {"type": "code", "question": "Create a boolean variable 'is_active' set to True", "starter": "", "solution": "is_active = True", "hint": "Boolean values are True or False"},
            {"type": "fill_blank", "question": "Convert '42' to int: int(___)", "answer": "'42'"},
            {"type": "multiple_choice", "question": "What is type(42)?", "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'num'>"], "correct": 0},
            {"type": "code", "question": "Convert the integer 10 to a string", "starter": "", "solution": "str(10)", "hint": "Use str() function"},
            {"type": "multiple_choice", "question": "What is 5 / 2 in Python 3?", "options": ["2.5", "2", "3", "2.0"], "correct": 0},
            {"type": "fill_blank", "question": "True and False are ___ values", "answer": "boolean"},
            {"type": "code", "question": "Create a list with numbers 1, 2, 3", "starter": "", "solution": "numbers = [1, 2, 3]", "hint": "Use square brackets"},
            {"type": "multiple_choice", "question": "Which is mutable?", "options": ["list", "tuple", "string", "int"], "correct": 0},
            {"type": "code", "question": "Check if 'hello' is a string using type()", "starter": "", "solution": "type('hello')", "hint": "type() returns the type"},
        ]
    elif "string" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "How to get string length?", "options": ["len(s)", "s.length", "s.size()", "length(s)"], "correct": 0},
            {"type": "code", "question": "Concatenate 'Hello' and 'World' with a space", "starter": "", "solution": "'Hello' + ' ' + 'World'", "hint": "Use + to join strings"},
            {"type": "multiple_choice", "question": "What is 'Python'[0]?", "options": ["P", "y", "Python", "Error"], "correct": 0},
            {"type": "fill_blank", "question": "'hello'.___() returns 'HELLO'", "answer": "upper"},
            {"type": "code", "question": "Get the last character of 'Python'", "starter": "", "solution": "'Python'[-1]", "hint": "Use negative indexing"},
            {"type": "multiple_choice", "question": "What does 'abc' * 3 return?", "options": ["'abcabcabc'", "'abc3'", "Error", "9"], "correct": 0},
            {"type": "code", "question": "Split 'a,b,c' by comma", "starter": "", "solution": "'a,b,c'.split(',')", "hint": "Use .split() method"},
            {"type": "fill_blank", "question": "'  hello  '.___() removes whitespace", "answer": "strip"},
            {"type": "multiple_choice", "question": "f-strings start with?", "options": ["f'...'", "s'...'", "'...'.format()", "str(...)"], "correct": 0},
            {"type": "code", "question": "Create f-string: 'Name: {name}' where name='Alice'", "starter": "name = 'Alice'\n", "solution": "name = 'Alice'\nf'Name: {name}'", "hint": "Use f-string syntax"},
        ]
    elif "number" in lesson_title.lower() or "math" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "What is 7 // 2 in Python?", "options": ["3", "3.5", "4", "2"], "correct": 0},
            {"type": "code", "question": "Calculate 2 to the power of 8", "starter": "", "solution": "2 ** 8", "hint": "Use ** for exponentiation"},
            {"type": "fill_blank", "question": "Modulo operator: 10 ___ 3 = 1", "answer": "%"},
            {"type": "multiple_choice", "question": "What is abs(-5)?", "options": ["5", "-5", "0", "Error"], "correct": 0},
            {"type": "code", "question": "Round 3.7 to nearest integer", "starter": "", "solution": "round(3.7)", "hint": "Use round() function"},
            {"type": "multiple_choice", "question": "What is max(1, 5, 3)?", "options": ["5", "1", "3", "9"], "correct": 0},
            {"type": "fill_blank", "question": "import ___ to use sqrt()", "answer": "math"},
            {"type": "code", "question": "Get the minimum of 4, 2, 8", "starter": "", "solution": "min(4, 2, 8)", "hint": "Use min() function"},
            {"type": "multiple_choice", "question": "10 / 3 returns what type?", "options": ["float", "int", "str", "None"], "correct": 0},
            {"type": "code", "question": "Calculate floor division of 17 by 5", "starter": "", "solution": "17 // 5", "hint": "Use // for floor division"},
        ]
    elif "if" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "What keyword starts a conditional?", "options": ["if", "when", "case", "check"], "correct": 0},
            {"type": "code", "question": "Write if statement: if age >= 18 print 'Adult'", "starter": "age = 20\n", "solution": "age = 20\nif age >= 18:\n    print('Adult')", "hint": "Remember the colon and indentation"},
            {"type": "fill_blank", "question": "if x > 5___", "answer": ":"},
            {"type": "multiple_choice", "question": "What is the comparison operator for 'not equal'?", "options": ["!=", "<>", "=/=", "not="], "correct": 0},
            {"type": "code", "question": "Check if number is positive, negative, or zero", "starter": "num = 5\n", "solution": "num = 5\nif num > 0:\n    print('Positive')\nelif num < 0:\n    print('Negative')\nelse:\n    print('Zero')", "hint": "Use if, elif, else"},
            {"type": "multiple_choice", "question": "What does 'and' do in conditions?", "options": ["Both must be True", "Either can be True", "Neither must be True", "Inverts the condition"], "correct": 0},
            {"type": "fill_blank", "question": "if x > 0 ___ x < 10:  # both conditions", "answer": "and"},
            {"type": "code", "question": "Write: if x is between 1 and 10 (inclusive)", "starter": "x = 5\n", "solution": "x = 5\nif 1 <= x <= 10:\n    print('In range')", "hint": "Python allows chained comparisons"},
            {"type": "multiple_choice", "question": "What is 'not True'?", "options": ["False", "True", "None", "Error"], "correct": 0},
            {"type": "code", "question": "Check if a string is empty", "starter": "s = ''\n", "solution": "s = ''\nif not s:\n    print('Empty')", "hint": "Empty strings are falsy"},
        ]
    elif "loop" in lesson_title.lower() and "for" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "What does range(5) produce?", "options": ["0,1,2,3,4", "1,2,3,4,5", "0,1,2,3,4,5", "1,2,3,4"], "correct": 0},
            {"type": "code", "question": "Print numbers 1 to 5 using for loop", "starter": "", "solution": "for i in range(1, 6):\n    print(i)", "hint": "range(start, end) - end is exclusive"},
            {"type": "fill_blank", "question": "for item ___ my_list:", "answer": "in"},
            {"type": "multiple_choice", "question": "What is range(0, 10, 2)?", "options": ["0,2,4,6,8", "0,2,4,6,8,10", "2,4,6,8,10", "0,1,2,3,4"], "correct": 0},
            {"type": "code", "question": "Sum numbers from 1 to 10 using for loop", "starter": "", "solution": "total = 0\nfor i in range(1, 11):\n    total += i", "hint": "Use += to accumulate"},
            {"type": "multiple_choice", "question": "Can you loop through a string?", "options": ["Yes, character by character", "No", "Only with index", "Only backwards"], "correct": 0},
            {"type": "code", "question": "Print each character in 'hello'", "starter": "", "solution": "for char in 'hello':\n    print(char)", "hint": "Strings are iterable"},
            {"type": "fill_blank", "question": "for i in ___(len(items)):", "answer": "range"},
            {"type": "code", "question": "Print indices and values of [10, 20, 30]", "starter": "", "solution": "for i, val in enumerate([10, 20, 30]):\n    print(i, val)", "hint": "Use enumerate()"},
            {"type": "multiple_choice", "question": "What is enumerate() used for?", "options": ["Index and value", "Just index", "Just value", "Sorting"], "correct": 0},
        ]
    elif "while" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "When does a while loop stop?", "options": ["When condition is False", "After 10 iterations", "Never", "When break is called only"], "correct": 0},
            {"type": "code", "question": "Count down from 5 to 1 using while", "starter": "", "solution": "count = 5\nwhile count > 0:\n    print(count)\n    count -= 1", "hint": "Don't forget to decrement!"},
            {"type": "fill_blank", "question": "___ x > 0:", "answer": "while"},
            {"type": "multiple_choice", "question": "What is an infinite loop?", "options": ["Loop that never ends", "Loop with no body", "Loop with break", "Nested loop"], "correct": 0},
            {"type": "code", "question": "Sum numbers until sum exceeds 100", "starter": "", "solution": "total = 0\ni = 1\nwhile total <= 100:\n    total += i\n    i += 1", "hint": "Keep adding until condition fails"},
            {"type": "multiple_choice", "question": "What does 'break' do?", "options": ["Exit the loop", "Skip iteration", "Pause loop", "Restart loop"], "correct": 0},
            {"type": "code", "question": "Find first number divisible by 7 starting from 1", "starter": "", "solution": "num = 1\nwhile num % 7 != 0:\n    num += 1\nprint(num)", "hint": "Use modulo to check divisibility"},
            {"type": "fill_blank", "question": "Use ___ to skip to next iteration", "answer": "continue"},
            {"type": "code", "question": "Print numbers 1-10, skip number 5", "starter": "", "solution": "i = 0\nwhile i < 10:\n    i += 1\n    if i == 5:\n        continue\n    print(i)", "hint": "Use continue to skip"},
            {"type": "multiple_choice", "question": "while True creates what?", "options": ["Infinite loop", "Error", "Single iteration", "No loop"], "correct": 0},
        ]
    elif "function" in lesson_title.lower() and "defin" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "Which keyword defines a function?", "options": ["def", "function", "func", "define"], "correct": 0},
            {"type": "code", "question": "Create a function greet() that prints 'Hello!'", "starter": "", "solution": "def greet():\n    print('Hello!')", "hint": "def function_name():"},
            {"type": "fill_blank", "question": "___ my_function():", "answer": "def"},
            {"type": "multiple_choice", "question": "How do you call a function named 'test'?", "options": ["test()", "call test", "run test()", "test"], "correct": 0},
            {"type": "code", "question": "Create function add(a, b) that returns a + b", "starter": "", "solution": "def add(a, b):\n    return a + b", "hint": "Use return to give back a value"},
            {"type": "multiple_choice", "question": "What if a function has no return?", "options": ["Returns None", "Error", "Returns 0", "Returns empty string"], "correct": 0},
            {"type": "code", "question": "Create function is_even(n) that returns True if n is even", "starter": "", "solution": "def is_even(n):\n    return n % 2 == 0", "hint": "Even numbers have no remainder when divided by 2"},
            {"type": "fill_blank", "question": "def greet(name='Guest'):  # 'Guest' is a ___ argument", "answer": "default"},
            {"type": "code", "question": "Create function that takes *args and returns their sum", "starter": "", "solution": "def sum_all(*args):\n    return sum(args)", "hint": "*args collects all positional arguments"},
            {"type": "multiple_choice", "question": "What is **kwargs used for?", "options": ["Keyword arguments", "All arguments", "No arguments", "Required arguments"], "correct": 0},
        ]
    elif "list" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "How to create an empty list?", "options": ["[]", "{}", "()", "list{}"], "correct": 0},
            {"type": "code", "question": "Create a list with 1, 2, 3 and append 4", "starter": "", "solution": "nums = [1, 2, 3]\nnums.append(4)", "hint": "Use .append() method"},
            {"type": "fill_blank", "question": "my_list.___(5)  # add 5 to end", "answer": "append"},
            {"type": "multiple_choice", "question": "What does pop() do?", "options": ["Remove and return last item", "Remove first item", "Add item", "Clear list"], "correct": 0},
            {"type": "code", "question": "Get the first 3 elements of [1,2,3,4,5]", "starter": "", "solution": "[1,2,3,4,5][:3]", "hint": "Use slicing [:3]"},
            {"type": "multiple_choice", "question": "How to insert at index 0?", "options": [".insert(0, x)", ".add(0, x)", ".put(0, x)", "[0] = x"], "correct": 0},
            {"type": "code", "question": "Reverse the list [1, 2, 3]", "starter": "", "solution": "[1, 2, 3][::-1]", "hint": "Use [::-1] slicing"},
            {"type": "fill_blank", "question": "list1 ___ list2  # combine lists", "answer": "+"},
            {"type": "code", "question": "Create list of squares from 1 to 5 using comprehension", "starter": "", "solution": "[x**2 for x in range(1, 6)]", "hint": "[expression for item in iterable]"},
            {"type": "multiple_choice", "question": "What is [1,2,3].index(2)?", "options": ["1", "2", "0", "3"], "correct": 0},
        ]
    elif "dict" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "Dict syntax?", "options": ["{'key': 'value'}", "['key': 'value']", "('key': 'value')", "{key = value}"], "correct": 0},
            {"type": "code", "question": "Create a dict with name='John' and age=30", "starter": "", "solution": "person = {'name': 'John', 'age': 30}", "hint": "Use curly braces and colons"},
            {"type": "fill_blank", "question": "Get all keys: dict.___()", "answer": "keys"},
            {"type": "multiple_choice", "question": "How to access dict['key'] safely?", "options": ["dict.get('key')", "dict.safe('key')", "dict.find('key')", "dict('key')"], "correct": 0},
            {"type": "code", "question": "Add 'city': 'NYC' to existing dict", "starter": "person = {'name': 'John'}\n", "solution": "person = {'name': 'John'}\nperson['city'] = 'NYC'", "hint": "dict['new_key'] = value"},
            {"type": "multiple_choice", "question": "What returns dict values?", "options": [".values()", ".items()", ".keys()", ".data()"], "correct": 0},
            {"type": "code", "question": "Loop through dict items (key and value)", "starter": "d = {'a': 1, 'b': 2}\n", "solution": "d = {'a': 1, 'b': 2}\nfor k, v in d.items():\n    print(k, v)", "hint": "Use .items()"},
            {"type": "fill_blank", "question": "dict.get('key', ___) returns default if key missing", "answer": "default"},
            {"type": "code", "question": "Merge two dicts using {**d1, **d2}", "starter": "d1 = {'a': 1}\nd2 = {'b': 2}\n", "solution": "d1 = {'a': 1}\nd2 = {'b': 2}\nmerged = {**d1, **d2}", "hint": "Use ** to unpack dicts"},
            {"type": "multiple_choice", "question": "Can dict keys be lists?", "options": ["No, must be immutable", "Yes", "Only strings", "Only numbers"], "correct": 0},
        ]
    elif "class" in lesson_title.lower():
        exercises = [
            {"type": "multiple_choice", "question": "Keyword to define a class?", "options": ["class", "def", "object", "new"], "correct": 0},
            {"type": "code", "question": "Create an empty class called Dog", "starter": "", "solution": "class Dog:\n    pass", "hint": "Use pass for empty body"},
            {"type": "fill_blank", "question": "___ MyClass:", "answer": "class"},
            {"type": "multiple_choice", "question": "Constructor method name?", "options": ["__init__", "__new__", "__create__", "__start__"], "correct": 0},
            {"type": "code", "question": "Add __init__ with name parameter to Dog class", "starter": "", "solution": "class Dog:\n    def __init__(self, name):\n        self.name = name", "hint": "First param is always self"},
            {"type": "fill_blank", "question": "def __init__(___,  name):", "answer": "self"},
            {"type": "code", "question": "Add bark() method that prints 'Woof!'", "starter": "class Dog:\n    def __init__(self, name):\n        self.name = name\n", "solution": "class Dog:\n    def __init__(self, name):\n        self.name = name\n    def bark(self):\n        print('Woof!')", "hint": "def method_name(self):"},
            {"type": "multiple_choice", "question": "How to create an instance?", "options": ["Dog('Rex')", "new Dog('Rex')", "Dog.create('Rex')", "create Dog('Rex')"], "correct": 0},
            {"type": "code", "question": "Create Puppy class that inherits from Dog", "starter": "class Dog:\n    pass\n", "solution": "class Dog:\n    pass\n\nclass Puppy(Dog):\n    pass", "hint": "class Child(Parent):"},
            {"type": "multiple_choice", "question": "Call parent's __init__ using?", "options": ["super().__init__()", "parent.__init__()", "base.__init__()", "this.__init__()"], "correct": 0},
        ]
    else:
        # Generic exercises for other lessons
        exercises = [
            {"type": "multiple_choice", "question": f"What is the main concept in '{lesson_title}'?", "options": ["Fundamental programming concept", "Advanced only", "Not important", "Optional"], "correct": 0},
            {"type": "code", "question": f"Write a basic example of {lesson_title.lower()}", "starter": "# Your code here\n", "solution": "# Example code", "hint": f"Think about how {lesson_title.lower()} works"},
            {"type": "fill_blank", "question": "Complete this example: ___", "answer": "code"},
            {"type": "multiple_choice", "question": "Why is this concept important?", "options": ["Code organization", "Not needed", "Only for experts", "Deprecated"], "correct": 0},
            {"type": "code", "question": "Implement a simple version", "starter": "", "solution": "pass", "hint": "Start simple"},
            {"type": "fill_blank", "question": "Key keyword: ___", "answer": "def"},
            {"type": "multiple_choice", "question": "Common use case?", "options": ["Data processing", "Never used", "Only testing", "Graphics only"], "correct": 0},
            {"type": "code", "question": "Write another example", "starter": "", "solution": "# Code", "hint": "Practice makes perfect"},
            {"type": "multiple_choice", "question": "Best practice?", "options": ["Keep it simple", "Make it complex", "Avoid using", "Copy paste"], "correct": 0},
            {"type": "fill_blank", "question": "Remember: ___ is key", "answer": "practice"},
        ]
    
    return exercises

def generate_lessons(language_id: str) -> List[dict]:
    """Generate comprehensive lessons with 10 exercises each"""
    
    # Define units and lessons per unit
    units_config = {
        "python": [
            ("Basics", ["Hello World", "Variables", "Data Types", "String Operations", "Numbers & Math"]),
            ("Control Flow", ["If Statements", "Else & Elif", "For Loops", "While Loops", "Break & Continue"]),
            ("Functions", ["Defining Functions", "Parameters", "Return Values", "Lambda Functions", "Scope"]),
            ("Data Structures", ["Lists", "List Methods", "Dictionaries", "Tuples", "Sets"]),
            ("OOP", ["Classes Intro", "Constructor", "Methods", "Inheritance", "Encapsulation"]),
            ("Advanced", ["List Comprehension", "File Handling", "Exception Handling", "Decorators", "Generators"]),
        ],
        "javascript": [
            ("Basics", ["Hello World", "Variables", "Data Types", "Strings", "Operators"]),
            ("Control Flow", ["If Statements", "Ternary Operator", "For Loops", "While Loops", "Array Methods"]),
            ("Functions", ["Function Declaration", "Arrow Functions", "Parameters", "Callbacks", "Closures"]),
            ("Objects", ["Object Basics", "Methods", "Destructuring", "Spread & Rest", "Classes"]),
            ("Async", ["Promises", "Async/Await", "Fetch API", "Error Handling", "Promise.all"]),
            ("DOM", ["Selecting Elements", "Modifying Elements", "Events", "Creating Elements", "Forms"]),
        ],
        "shell": [
            ("Basics", ["Echo & Print", "Variables", "Comments", "Command Syntax", "Exit Codes"]),
            ("Files", ["File Operations", "Directory Commands", "Permissions", "File Content", "Finding Files"]),
            ("Control Flow", ["If Statements", "Case Statements", "For Loops", "While Loops", "Until Loops"]),
            ("Text Processing", ["Grep", "Sed", "Awk", "Cut & Sort", "Pipes"]),
            ("Scripting", ["Script Structure", "Arguments", "Functions", "Arrays", "Error Handling"]),
            ("Advanced", ["Process Management", "Cron Jobs", "Debugging", "Best Practices", "Real Scripts"]),
        ],
        "elixir": [
            ("Basics", ["Hello World", "Data Types", "Variables", "Pattern Matching", "Operators"]),
            ("Collections", ["Lists", "Tuples", "Keyword Lists", "Maps", "Enum Module"]),
            ("Control Flow", ["If & Unless", "Case", "Cond", "With", "Comprehensions"]),
            ("Functions", ["Anonymous Functions", "Named Functions", "Guards", "Default Arguments", "Pipe Operator"]),
            ("Modules", ["Module Basics", "Attributes", "Structs", "Protocols", "Behaviours"]),
            ("Concurrency", ["Processes", "Message Passing", "GenServer", "Supervisors", "Tasks"]),
        ],
        "zig": [
            ("Basics", ["Hello World", "Variables", "Types", "Comments", "Operators"]),
            ("Control Flow", ["If Expressions", "For Loops", "While Loops", "Switch", "Optionals"]),
            ("Functions", ["Function Basics", "Parameters", "Error Handling", "Inline Functions", "Comptime"]),
            ("Memory", ["Pointers", "Slices", "Arrays", "Allocators", "Memory Safety"]),
            ("Structs", ["Struct Basics", "Methods", "Packed Structs", "Enums", "Unions"]),
            ("Advanced", ["Generics", "Build System", "C Interop", "SIMD", "Async I/O"]),
        ],
    }
    
    # Get config for this language or use generic
    if language_id in units_config:
        units = units_config[language_id]
    else:
        units = [
            ("Basics", ["Hello World", "Variables", "Data Types", "Comments", "Basic I/O"]),
            ("Control Flow", ["If Statements", "Else & Elif", "Switch/Match", "For Loops", "While Loops"]),
            ("Functions", ["Defining Functions", "Parameters", "Return Values", "Scope", "Recursion"]),
            ("Data Structures", ["Arrays/Lists", "Strings", "Dictionaries/Maps", "Sets", "Tuples"]),
            ("OOP", ["Classes", "Objects", "Inheritance", "Encapsulation", "Polymorphism"]),
            ("Advanced", ["Error Handling", "File I/O", "Modules", "Libraries", "Best Practices"]),
        ]
    
    lessons = []
    for unit_num, (unit_name, topics) in enumerate(units, 1):
        for topic_idx, topic in enumerate(topics):
            lesson_id = f"{language_id}_{unit_num}_{topic_idx + 1}"
            
            # Generate exercises based on language
            if language_id == "python":
                exercises = generate_exercises_python(lesson_id, topic, unit_num)
            else:
                # Generic exercises with 10 questions
                exercises = generate_generic_exercises(language_id, topic, unit_num)
            
            lessons.append({
                "id": lesson_id,
                "title": topic,
                "description": f"Learn about {topic.lower()}",
                "xp": 15 + (unit_num * 5) + (topic_idx * 3),
                "unit": unit_num,
                "unit_name": unit_name,
                "exercises": exercises,
            })
    
    return lessons

def generate_generic_exercises(language_id: str, topic: str, unit: int) -> List[dict]:
    """Generate 10 generic exercises for any language"""
    exercises = []
    
    # Create varied exercise types
    exercise_templates = [
        {"type": "multiple_choice", "question": f"What is {topic.lower()} used for?", "options": ["Core functionality", "Optional feature", "Deprecated", "Not available"], "correct": 0},
        {"type": "code", "question": f"Write a basic {topic.lower()} example", "starter": f"// {topic} example\n", "solution": f"// {topic} implementation", "hint": f"Think about {topic.lower()} syntax"},
        {"type": "fill_blank", "question": f"The key concept in {topic.lower()} is ___", "answer": "code"},
        {"type": "multiple_choice", "question": f"Why is {topic.lower()} important?", "options": ["Improves code quality", "Not important", "Only for experts", "Rarely used"], "correct": 0},
        {"type": "code", "question": f"Implement a {topic.lower()} function", "starter": "", "solution": "// Implementation", "hint": "Start with the basics"},
        {"type": "multiple_choice", "question": f"Common mistake with {topic.lower()}?", "options": ["Forgetting syntax", "Using too much", "No mistakes possible", "Never happens"], "correct": 0},
        {"type": "fill_blank", "question": f"Best practice for {topic.lower()}: ___ your code", "answer": "test"},
        {"type": "code", "question": f"Write another {topic.lower()} example", "starter": "", "solution": "// Code here", "hint": "Practice makes perfect"},
        {"type": "multiple_choice", "question": f"When to use {topic.lower()}?", "options": ["Appropriate situations", "Never", "Always", "Randomly"], "correct": 0},
        {"type": "fill_blank", "question": f"Remember: {topic.lower()} requires ___", "answer": "practice"},
    ]
    
    return exercise_templates

# Pre-generate lessons for all languages
LESSONS_CACHE = {lang["id"]: generate_lessons(lang["id"]) for lang in LANGUAGES}

# ============== DAILY CHALLENGES ==============

def generate_daily_challenge() -> dict:
    """Generate a random daily challenge"""
    challenge_types = [
        {
            "type": "speed_round",
            "title": "Speed Round",
            "description": "Answer 5 questions in 2 minutes",
            "xp_reward": 50,
            "gem_reward": 5,
            "time_limit": 120,
            "exercises": random.sample([
                {"type": "multiple_choice", "question": "What is 2 + 2?", "options": ["3", "4", "5", "6"], "correct": 1},
                {"type": "fill_blank", "question": "print('Hello ___')", "answer": "World"},
                {"type": "multiple_choice", "question": "Which is a loop?", "options": ["for", "if", "def", "class"], "correct": 0},
                {"type": "fill_blank", "question": "def function___:", "answer": "()"},
                {"type": "multiple_choice", "question": "String + String is?", "options": ["Concatenation", "Addition", "Error", "None"], "correct": 0},
            ], 5),
        },
        {
            "type": "code_master",
            "title": "Code Master",
            "description": "Solve 3 coding challenges",
            "xp_reward": 75,
            "gem_reward": 10,
            "time_limit": 300,
            "exercises": [
                {"type": "code", "question": "Write a function to add two numbers", "starter": "", "solution": "def add(a, b):\n    return a + b", "hint": "Use return"},
                {"type": "code", "question": "Create a list with 1,2,3", "starter": "", "solution": "nums = [1, 2, 3]", "hint": "Use square brackets"},
                {"type": "code", "question": "Print numbers 1 to 5", "starter": "", "solution": "for i in range(1, 6):\n    print(i)", "hint": "Use for loop"},
            ],
        },
        {
            "type": "knowledge_quiz",
            "title": "Knowledge Quiz",
            "description": "Test your programming knowledge",
            "xp_reward": 40,
            "gem_reward": 3,
            "time_limit": 180,
            "exercises": [
                {"type": "multiple_choice", "question": "Python was created by?", "options": ["Guido van Rossum", "Dennis Ritchie", "James Gosling", "Bjarne Stroustrup"], "correct": 0},
                {"type": "multiple_choice", "question": "JavaScript runs in?", "options": ["Browser", "Only server", "Only desktop", "Only mobile"], "correct": 0},
                {"type": "multiple_choice", "question": "HTML stands for?", "options": ["HyperText Markup Language", "High Tech ML", "Home Tool ML", "Hyper Transfer ML"], "correct": 0},
            ],
        },
    ]
    
    challenge = random.choice(challenge_types)
    challenge["id"] = f"daily_{datetime.utcnow().strftime('%Y%m%d')}"
    challenge["date"] = datetime.utcnow().strftime('%Y-%m-%d')
    return challenge

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register")
async def register(user: UserCreate):
    existing = await db.users.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_dict = {
        "id": str(uuid.uuid4()),
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password),
        "xp": 0,
        "level": 1,
        "streak": 0,
        "hearts": 5,
        "max_hearts": 5,
        "gems": 10,  # Starting gems
        "last_activity": None,
        "badges": [],
        "friends": [],
        "friend_requests": [],
        "languages_studied": [],
        "daily_goal": 50,
        "daily_xp": 0,
        "daily_goal_streak": 0,
        "combo_multiplier": 1.0,
        "consecutive_correct": 0,
        "total_lessons_completed": 0,
        "perfect_lessons": 0,
        "settings": {
            "font_size": "medium",
            "high_contrast": False,
            "reduced_motion": False,
            "sound_effects": True,
            "notifications": True,
            "daily_reminder": True,
            "theme": "dark",
        },
        "daily_challenges_completed": [],
        "created_at": datetime.utcnow().isoformat(),
    }
    await db.users.insert_one(user_dict)
    
    token = generate_token()
    await db.sessions.insert_one({"token": token, "user_id": user_dict["id"]})
    
    return {"token": token, "user": user_dict}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or user["password"] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    now = datetime.utcnow()
    if user.get("last_activity"):
        last = datetime.fromisoformat(user["last_activity"])
        days_diff = (now.date() - last.date()).days
        if days_diff == 1:
            user["streak"] += 1
        elif days_diff > 1:
            user["streak"] = 1
    else:
        user["streak"] = 1
    
    user["last_activity"] = now.isoformat()
    user["hearts"] = user.get("max_hearts", 5)
    user["daily_xp"] = 0  # Reset daily XP
    user["combo_multiplier"] = 1.0  # Reset combo
    user["consecutive_correct"] = 0
    
    await db.users.update_one({"id": user["id"]}, {"$set": user})
    
    token = generate_token()
    await db.sessions.insert_one({"token": token, "user_id": user["id"]})
    
    user.pop("password", None)
    user.pop("_id", None)
    return {"token": token, "user": user}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    user.pop("password", None)
    user.pop("_id", None)
    return user

@api_router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    await db.sessions.delete_one({"token": credentials.credentials})
    return {"message": "Logged out"}

# ============== SETTINGS ROUTES ==============

@api_router.put("/settings")
async def update_settings(settings_update: SettingsUpdate, user: dict = Depends(get_current_user)):
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"settings": settings_update.settings}}
    )
    return {"message": "Settings updated", "settings": settings_update.settings}

@api_router.get("/settings")
async def get_settings(user: dict = Depends(get_current_user)):
    return user.get("settings", {})

# ============== LANGUAGE ROUTES ==============

@api_router.get("/languages")
async def get_languages():
    return LANGUAGES

@api_router.get("/languages/{language_id}/lessons")
async def get_lessons(language_id: str, request: Request):
    if language_id not in LESSONS_CACHE:
        raise HTTPException(status_code=404, detail="Language not found")
    
    lessons = LESSONS_CACHE[language_id]
    completed_ids = set()
    
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        session = await db.sessions.find_one({"token": token})
        if session:
            user = await db.users.find_one({"id": session["user_id"]})
            if user:
                progress = await db.progress.find({"user_id": user["id"], "language": language_id}).to_list(1000)
                completed_ids = {p["lesson_id"] for p in progress if p.get("completed")}
    
    result = []
    for lesson in lessons:
        lesson_copy = lesson.copy()
        lesson_copy["completed"] = lesson["id"] in completed_ids
        lesson_copy["exercise_count"] = len(lesson.get("exercises", []))
        lesson_copy.pop("exercises", None)
        result.append(lesson_copy)
    
    return result

@api_router.get("/languages/{language_id}/lessons/{lesson_id}")
async def get_lesson(language_id: str, lesson_id: str):
    if language_id not in LESSONS_CACHE:
        raise HTTPException(status_code=404, detail="Language not found")
    
    for lesson in LESSONS_CACHE[language_id]:
        if lesson["id"] == lesson_id:
            return lesson
    
    raise HTTPException(status_code=404, detail="Lesson not found")

# ============== PROGRESS ROUTES ==============

@api_router.post("/progress/complete")
async def complete_lesson(answer: LessonAnswer, user: dict = Depends(get_current_user)):
    if answer.language not in LESSONS_CACHE:
        raise HTTPException(status_code=404, detail="Language not found")
    
    lesson = None
    for l in LESSONS_CACHE[answer.language]:
        if l["id"] == answer.lesson_id:
            lesson = l
            break
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Calculate score with enhanced validation
    exercises = lesson.get("exercises", [])
    correct = 0
    for i, ex in enumerate(exercises):
        if i < len(answer.answers):
            user_answer = answer.answers[i]
            if ex["type"] == "multiple_choice" and user_answer.get("selected") == ex.get("correct"):
                correct += 1
            elif ex["type"] == "code":
                is_correct, _ = validate_code(
                    user_answer.get("code", ""),
                    ex.get("solution", ""),
                    answer.language,
                    ex["type"]
                )
                if is_correct:
                    correct += 1
            elif ex["type"] == "fill_blank":
                user_fill = user_answer.get("answer", "").strip().lower()
                expected = ex.get("answer", "").strip().lower()
                if user_fill == expected:
                    correct += 1
    
    total = len(exercises)
    score = int((correct / total) * 100) if total > 0 else 100
    base_xp = lesson.get("xp", 15)
    
    # Calculate XP with combo multiplier
    combo_multiplier = user.get("combo_multiplier", 1.0)
    if score == 100:
        combo_multiplier = min(combo_multiplier + 0.5, 5.0)  # Max 5x
    elif score < 70:
        combo_multiplier = 1.0  # Reset on poor performance
    
    xp_earned = int(base_xp * (score / 100) * combo_multiplier)
    
    # Speed bonus
    if answer.time_taken and answer.time_taken < 120 and score >= 70:
        xp_earned = int(xp_earned * 1.25)  # 25% speed bonus
    
    # Update hearts
    hearts_lost = max(0, (total - correct) // 2)  # Lose heart for every 2 wrong
    new_hearts = max(0, user.get("hearts", 5) - hearts_lost)
    
    # Check existing progress
    existing = await db.progress.find_one({
        "user_id": user["id"],
        "language": answer.language,
        "lesson_id": answer.lesson_id
    })
    
    new_badges = []
    gems_earned = 0
    
    if not existing:
        await db.progress.insert_one({
            "user_id": user["id"],
            "language": answer.language,
            "lesson_id": answer.lesson_id,
            "completed": True,
            "score": score,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        new_xp = user.get("xp", 0) + xp_earned
        new_level = 1 + (new_xp // 100)
        daily_xp = user.get("daily_xp", 0) + xp_earned
        total_lessons = user.get("total_lessons_completed", 0) + 1
        perfect_lessons = user.get("perfect_lessons", 0) + (1 if score == 100 else 0)
        
        languages_studied = user.get("languages_studied", [])
        if answer.language not in languages_studied:
            languages_studied.append(answer.language)
        
        badges = user.get("badges", [])
        
        # Check badges
        if "first_lesson" not in badges:
            badges.append("first_lesson")
            new_badges.append("first_lesson")
            gems_earned += 5
        
        if score == 100 and "perfect_lesson" not in badges:
            badges.append("perfect_lesson")
            new_badges.append("perfect_lesson")
        
        if perfect_lessons >= 5 and "no_mistakes" not in badges:
            badges.append("no_mistakes")
            new_badges.append("no_mistakes")
            gems_earned += 10
        
        if new_xp >= 100 and "xp_100" not in badges:
            badges.append("xp_100")
            new_badges.append("xp_100")
        if new_xp >= 500 and "xp_500" not in badges:
            badges.append("xp_500")
            new_badges.append("xp_500")
        if new_xp >= 1000 and "xp_1000" not in badges:
            badges.append("xp_1000")
            new_badges.append("xp_1000")
        if new_xp >= 5000 and "xp_5000" not in badges:
            badges.append("xp_5000")
            new_badges.append("xp_5000")
            gems_earned += 25
        
        if len(languages_studied) >= 3 and "polyglot" not in badges:
            badges.append("polyglot")
            new_badges.append("polyglot")
        if len(languages_studied) >= 5 and "polyglot_master" not in badges:
            badges.append("polyglot_master")
            new_badges.append("polyglot_master")
            gems_earned += 15
        
        if combo_multiplier >= 5.0 and "combo_king" not in badges:
            badges.append("combo_king")
            new_badges.append("combo_king")
            gems_earned += 10
        
        if answer.time_taken and answer.time_taken < 120 and score >= 80 and "speed_demon" not in badges:
            badges.append("speed_demon")
            new_badges.append("speed_demon")
        
        if total_lessons >= 50 and "lesson_master" not in badges:
            badges.append("lesson_master")
            new_badges.append("lesson_master")
        if total_lessons >= 100 and "lesson_legend" not in badges:
            badges.append("lesson_legend")
            new_badges.append("lesson_legend")
            gems_earned += 20
        
        streak = user.get("streak", 0)
        if streak >= 3 and "streak_3" not in badges:
            badges.append("streak_3")
            new_badges.append("streak_3")
        if streak >= 7 and "streak_7" not in badges:
            badges.append("streak_7")
            new_badges.append("streak_7")
        if streak >= 30 and "streak_30" not in badges:
            badges.append("streak_30")
            new_badges.append("streak_30")
        
        # Check daily goal
        daily_goal = user.get("daily_goal", 50)
        daily_goal_met = daily_xp >= daily_goal
        daily_goal_streak = user.get("daily_goal_streak", 0)
        if daily_goal_met:
            daily_goal_streak += 1
            gems_earned += 2
        
        if daily_goal_streak >= 7 and "daily_achiever" not in badges:
            badges.append("daily_achiever")
            new_badges.append("daily_achiever")
        
        new_gems = user.get("gems", 0) + gems_earned
        
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "xp": new_xp,
                "level": new_level,
                "hearts": new_hearts,
                "gems": new_gems,
                "badges": badges,
                "languages_studied": languages_studied,
                "daily_xp": daily_xp,
                "daily_goal_streak": daily_goal_streak,
                "combo_multiplier": combo_multiplier,
                "total_lessons_completed": total_lessons,
                "perfect_lessons": perfect_lessons,
                "last_activity": datetime.utcnow().isoformat()
            }}
        )
        
        return {
            "score": score,
            "xp_earned": xp_earned,
            "new_xp": new_xp,
            "new_level": new_level,
            "hearts": new_hearts,
            "gems": new_gems,
            "gems_earned": gems_earned,
            "combo_multiplier": combo_multiplier,
            "new_badges": new_badges,
            "correct": correct,
            "total": total,
            "daily_xp": daily_xp,
            "daily_goal": daily_goal,
            "daily_goal_met": daily_goal_met,
        }
    else:
        if score > existing.get("score", 0):
            await db.progress.update_one(
                {"_id": existing["_id"]},
                {"$set": {"score": score}}
            )
        
        return {
            "score": score,
            "xp_earned": 0,
            "new_xp": user.get("xp", 0),
            "new_level": user.get("level", 1),
            "hearts": new_hearts,
            "gems": user.get("gems", 0),
            "gems_earned": 0,
            "combo_multiplier": combo_multiplier,
            "new_badges": [],
            "correct": correct,
            "total": total,
            "already_completed": True,
            "daily_xp": user.get("daily_xp", 0),
            "daily_goal": user.get("daily_goal", 50),
        }

@api_router.get("/progress/{language_id}")
async def get_language_progress(language_id: str, request: Request):
    total_lessons = len(LESSONS_CACHE.get(language_id, []))
    completed = 0
    progress_list = []
    
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        session = await db.sessions.find_one({"token": token})
        if session:
            user = await db.users.find_one({"id": session["user_id"]})
            if user:
                progress = await db.progress.find({
                    "user_id": user["id"],
                    "language": language_id
                }).to_list(1000)
                for p in progress:
                    p_dict = dict(p)
                    p_dict.pop("_id", None)
                    progress_list.append(p_dict)
                completed = len([p for p in progress if p.get("completed")])
    
    return {
        "total_lessons": total_lessons,
        "completed_lessons": completed,
        "progress_percent": int((completed / total_lessons) * 100) if total_lessons > 0 else 0,
        "lessons": progress_list
    }

# ============== DAILY CHALLENGE ROUTES ==============

@api_router.get("/daily-challenge")
async def get_daily_challenge(user: dict = Depends(get_current_user)):
    challenge = generate_daily_challenge()
    completed_today = challenge["id"] in user.get("daily_challenges_completed", [])
    challenge["completed"] = completed_today
    return challenge

@api_router.post("/daily-challenge/complete")
async def complete_daily_challenge(answer: DailyChallengeAnswer, user: dict = Depends(get_current_user)):
    challenge = generate_daily_challenge()
    
    if challenge["id"] in user.get("daily_challenges_completed", []):
        raise HTTPException(status_code=400, detail="Already completed today's challenge")
    
    # Calculate score
    exercises = challenge["exercises"]
    correct = 0
    for i, ex in enumerate(exercises):
        if i < len(answer.answers):
            user_answer = answer.answers[i]
            if ex["type"] == "multiple_choice" and user_answer.get("selected") == ex.get("correct"):
                correct += 1
            elif ex["type"] == "code":
                is_correct, _ = validate_code(user_answer.get("code", ""), ex.get("solution", ""), "python", "code")
                if is_correct:
                    correct += 1
            elif ex["type"] == "fill_blank":
                if user_answer.get("answer", "").strip().lower() == ex.get("answer", "").strip().lower():
                    correct += 1
    
    total = len(exercises)
    score = int((correct / total) * 100) if total > 0 else 0
    
    xp_earned = 0
    gems_earned = 0
    
    if score >= 70:
        xp_earned = challenge["xp_reward"]
        gems_earned = challenge["gem_reward"]
        
        completed_challenges = user.get("daily_challenges_completed", [])
        completed_challenges.append(challenge["id"])
        
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "xp": user.get("xp", 0) + xp_earned,
                "gems": user.get("gems", 0) + gems_earned,
                "daily_xp": user.get("daily_xp", 0) + xp_earned,
                "daily_challenges_completed": completed_challenges,
            }}
        )
    
    return {
        "score": score,
        "correct": correct,
        "total": total,
        "xp_earned": xp_earned,
        "gems_earned": gems_earned,
        "passed": score >= 70,
    }

# ============== SOCIAL ROUTES ==============

@api_router.get("/leaderboard")
async def get_leaderboard():
    users = await db.users.find().sort("xp", -1).limit(50).to_list(50)
    return [
        {
            "username": u["username"],
            "xp": u.get("xp", 0),
            "level": u.get("level", 1),
            "streak": u.get("streak", 0),
            "badges_count": len(u.get("badges", []))
        }
        for u in users
    ]

@api_router.post("/friends/add")
async def add_friend(request: FriendRequest, user: dict = Depends(get_current_user)):
    friend = await db.users.find_one({"username": request.friend_username})
    if not friend:
        raise HTTPException(status_code=404, detail="User not found")
    
    if friend["id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot add yourself")
    
    if friend["id"] in user.get("friends", []):
        raise HTTPException(status_code=400, detail="Already friends")
    
    await db.users.update_one({"id": user["id"]}, {"$addToSet": {"friends": friend["id"]}})
    await db.users.update_one({"id": friend["id"]}, {"$addToSet": {"friends": user["id"]}})
    
    updated_user = await db.users.find_one({"id": user["id"]})
    friends_count = len(updated_user.get("friends", []))
    if friends_count >= 5 and "social_butterfly" not in updated_user.get("badges", []):
        await db.users.update_one({"id": user["id"]}, {"$addToSet": {"badges": "social_butterfly"}})
    
    return {"message": f"Added {request.friend_username} as friend"}

@api_router.get("/friends")
async def get_friends(user: dict = Depends(get_current_user)):
    friend_ids = user.get("friends", [])
    if not friend_ids:
        return []
    
    friends = await db.users.find({"id": {"$in": friend_ids}}).to_list(100)
    return [
        {
            "username": f["username"],
            "xp": f.get("xp", 0),
            "level": f.get("level", 1),
            "streak": f.get("streak", 0)
        }
        for f in friends
    ]

@api_router.get("/badges")
async def get_badges():
    return BADGES

# ============== SHOP/GEMS ROUTES ==============

@api_router.post("/shop/buy-hearts")
async def buy_hearts(user: dict = Depends(get_current_user)):
    gem_cost = 10
    if user.get("gems", 0) < gem_cost:
        raise HTTPException(status_code=400, detail="Not enough gems")
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "hearts": user.get("max_hearts", 5),
            "gems": user.get("gems", 0) - gem_cost
        }}
    )
    return {"message": "Hearts refilled!", "hearts": user.get("max_hearts", 5)}

@api_router.post("/shop/buy-streak-freeze")
async def buy_streak_freeze(user: dict = Depends(get_current_user)):
    gem_cost = 20
    if user.get("gems", 0) < gem_cost:
        raise HTTPException(status_code=400, detail="Not enough gems")
    
    streak_freezes = user.get("streak_freezes", 0) + 1
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "streak_freezes": streak_freezes,
            "gems": user.get("gems", 0) - gem_cost
        }}
    )
    return {"message": "Streak freeze purchased!", "streak_freezes": streak_freezes}

# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {"message": "Codero API v2 - Learn to code with enhanced features!"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
