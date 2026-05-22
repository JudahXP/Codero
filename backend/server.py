from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, BackgroundTasks, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets
import random
import smtplib
import ssl
from email.message import EmailMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
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

class LessonAnswer(BaseModel):
    lesson_id: str
    language: str
    answers: List[dict]
    time_taken: Optional[int] = None
    practice_mode: bool = False  # NEW: Practice mode flag

class FriendRequest(BaseModel):
    friend_username: str

class SettingsUpdate(BaseModel):
    settings: Dict[str, Any]

class DailyChallengeAnswer(BaseModel):
    challenge_id: str
    answers: List[dict]

class VIPPurchase(BaseModel):
    payment_method: str = "card"  # card, paypal, etc.

class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_color: Optional[str] = None

class DisplayBadgesUpdate(BaseModel):
    badge_ids: List[str]

class CodeCheckRequest(BaseModel):
    language: str
    lesson_id: Optional[str] = None
    exercise_index: Optional[int] = None
    exercise: Optional[Dict[str, Any]] = None
    answer: Dict[str, Any]
    save_wrong: bool = True

class VerificationCodeRequest(BaseModel):
    email: EmailStr

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str

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

def is_vip_active(user: dict) -> bool:
    """Check if user has active VIP - earned through 7+ day streak"""
    return user.get("streak", 0) >= 7

def public_user(user: dict) -> dict:
    """Return a clean user payload with forward-compatible profile/auth defaults."""
    clean = dict(user)
    clean.pop("password", None)
    clean.pop("_id", None)
    clean.setdefault("profile", {
        "display_name": clean.get("username", "Coder"),
        "bio": "",
        "avatar_color": "#00FF88",
        "display_badges": clean.get("badges", [])[:3],
    })
    clean.setdefault("auth_methods", {
        "password": True,
        "email_verified": clean.get("email_verified", False),
        "passkey_ready": True,
        "google_ready": True,
    })
    clean.setdefault("email_verified", clean.get("auth_methods", {}).get("email_verified", False))
    clean["is_vip"] = is_vip_active(clean)
    clean["vip_perks"] = get_vip_perks(clean)
    return clean

def explain_error_simple(message: str) -> str:
    lower = (message or "").lower()
    if "print" in lower or "output" in lower:
        return "The answer needs the right output command. Check the function name and punctuation."
    if "required" in lower or "element" in lower:
        return "Your code is missing one of the main pieces the challenge asks for."
    if "blank" in lower:
        return "The blank does not match yet. Check spelling and symbols."
    if "order" in lower:
        return "The blocks are not in the right order yet. Put setup first, logic next, output last."
    return "Something is close, but not exact yet. Compare the goal, syntax, and missing keywords."

def check_exercise_answer(exercise: dict, user_answer: dict, language: str) -> tuple:
    """Simulated, safe code checking. No arbitrary code is executed."""
    exercise_type = exercise.get("type", "code")
    if exercise_type == "multiple_choice":
        correct = user_answer.get("selected") == exercise.get("correct")
        expected = exercise.get("options", [None])[exercise.get("correct", 0)] if exercise.get("options") else exercise.get("correct")
        return correct, "Great choice!" if correct else "That option does not match the concept.", expected
    if exercise_type == "fill_blank":
        expected = str(exercise.get("answer", "")).strip()
        actual = str(user_answer.get("answer", "")).strip()
        correct = actual.lower() == expected.lower()
        return correct, "Blank filled correctly!" if correct else "The blank is not exact yet.", expected
    if exercise_type in ["code", "write_code", "fix_broken_code"]:
        expected = exercise.get("solution", "")
        actual = user_answer.get("code", "")
        correct, message = validate_code(actual, expected, language, "code")
        return correct, message, expected
    if exercise_type == "predict_output":
        expected = str(exercise.get("answer", "")).strip()
        actual = str(user_answer.get("answer", user_answer.get("selected", ""))).strip()
        if exercise.get("options") and isinstance(user_answer.get("selected"), int):
            actual = str(exercise["options"][user_answer["selected"]]).strip()
        correct = actual.lower() == expected.lower()
        return correct, "You predicted the output!" if correct else "Run through the code line by line and track the value.", expected
    if exercise_type == "drag_drop":
        expected = exercise.get("correct_order", [])
        actual = user_answer.get("order", [])
        correct = actual == expected
        return correct, "The code blocks are in order!" if correct else "The order is not quite right.", expected
    return False, "Unsupported challenge type", None

async def save_wrong_answer(user_id: str, language: str, lesson_id: Optional[str], exercise_index: Optional[int], exercise: dict, user_answer: dict, expected: Any, explanation: str):
    await db.wrong_answers.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "language": language,
        "lesson_id": lesson_id,
        "exercise_index": exercise_index,
        "exercise_type": exercise.get("type"),
        "question": exercise.get("question", exercise.get("title", "Challenge")),
        "user_answer": user_answer,
        "expected_answer": expected,
        "explanation": explanation,
        "reviewed": False,
        "created_at": datetime.utcnow().isoformat(),
    })

def send_verification_email(to_email: str, code: str):
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    if not smtp_user or not smtp_pass:
        logger.warning("SMTP credentials are not configured; verification email not sent")
        return
    msg = EmailMessage()
    msg["Subject"] = "Your Codero verification code"
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.set_content(f"Your Codero verification code is {code}. It expires in 10 minutes.")
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info("Verification email sent to %s", to_email)
    except smtplib.SMTPException as exc:
        logger.error("Verification email delivery failed for %s: %s", to_email, exc)
    except Exception as exc:
        logger.error("Unexpected verification email error for %s: %s", to_email, exc)

def get_vip_perks(user: dict) -> dict:
    """Get VIP perks for user"""
    if is_vip_active(user):
        return {
            "xp_multiplier": 1.5,
            "max_hearts": 10,
            "hints_per_lesson": 5,
            "streak_freeze_per_week": 2,
            "ad_free": True,
            "exclusive_badges": True,
            "priority_support": True,
            "early_access": True,
        }
    return {
        "xp_multiplier": 1.0,
        "max_hearts": 5,
        "hints_per_lesson": 1,
        "streak_freeze_per_week": 0,
        "ad_free": False,
        "exclusive_badges": False,
        "priority_support": False,
        "early_access": False,
    }

# ============== CODE VALIDATION ==============

def validate_code(user_code: str, solution: str, language: str, exercise_type: str = "code") -> tuple:
    """Enhanced code validation with multiple checks"""
    user_code = user_code.strip()
    solution = solution.strip()
    
    if not user_code:
        return False, "No code provided"
    
    user_normalized = re.sub(r'\s+', ' ', user_code.lower())
    solution_normalized = re.sub(r'\s+', ' ', solution.lower())
    
    patterns_to_check = []
    
    if language == "python":
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
            patterns_to_check.append(r'return\s*')
        if "import " in solution.lower():
            patterns_to_check.append(r'import\s+')
        if "lambda" in solution.lower():
            patterns_to_check.append(r'lambda\s+')
        if "=" in solution and "==" not in solution:
            patterns_to_check.append(r'\w+\s*=\s*')
            
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
        if "while " in solution.lower():
            patterns_to_check.append(r'while\s+')
        if "case " in solution.lower():
            patterns_to_check.append(r'case\s+')
        if "function " in solution.lower() or "()" in solution:
            patterns_to_check.append(r'(function\s+\w+|\w+\s*\(\))')
        if "read " in solution.lower():
            patterns_to_check.append(r'read\s+')
        if "$" in solution:
            patterns_to_check.append(r'\$\w+|\$\{')
        if "grep" in solution.lower():
            patterns_to_check.append(r'grep\s+')
        if "|" in solution:
            patterns_to_check.append(r'\|')
        if "#!/" in solution:
            patterns_to_check.append(r'#!')
            
    elif language == "rust":
        if "println!" in solution:
            patterns_to_check.append(r'println!\s*\(')
        if "fn " in solution.lower():
            patterns_to_check.append(r'fn\s+\w+')
        if "let " in solution.lower():
            patterns_to_check.append(r'let\s+(mut\s+)?\w+')
        if "struct " in solution.lower():
            patterns_to_check.append(r'struct\s+\w+')
        if "impl " in solution.lower():
            patterns_to_check.append(r'impl\s+\w+')
        if "match " in solution.lower():
            patterns_to_check.append(r'match\s+')
            
    elif language == "go":
        if "fmt.Print" in solution:
            patterns_to_check.append(r'fmt\.Print')
        if "func " in solution.lower():
            patterns_to_check.append(r'func\s+\w*')
        if "package " in solution.lower():
            patterns_to_check.append(r'package\s+\w+')
        if "import " in solution.lower():
            patterns_to_check.append(r'import\s+')
        if ":=" in solution:
            patterns_to_check.append(r':=')
            
    elif language == "elixir":
        if "IO.puts" in solution:
            patterns_to_check.append(r'IO\.puts')
        if "IO.inspect" in solution:
            patterns_to_check.append(r'IO\.inspect')
        if "def " in solution.lower():
            patterns_to_check.append(r'def\s+\w+')
        if "defp " in solution.lower():
            patterns_to_check.append(r'defp\s+\w+')
        if "defmodule" in solution.lower():
            patterns_to_check.append(r'defmodule\s+\w+')
        if "|>" in solution:
            patterns_to_check.append(r'\|>')
        if "case " in solution.lower():
            patterns_to_check.append(r'case\s+')
        if "cond " in solution.lower() or "cond\n" in solution.lower():
            patterns_to_check.append(r'cond\s+do')
        if "Enum." in solution:
            patterns_to_check.append(r'Enum\.\w+')
        if "fn " in solution.lower():
            patterns_to_check.append(r'fn\s+')
        if "->" in solution:
            patterns_to_check.append(r'->')
        if "do" in solution.lower():
            patterns_to_check.append(r'\bdo\b')
            
    elif language == "zig":
        if "std.debug.print" in solution:
            patterns_to_check.append(r'std\.debug\.print')
        if "fn " in solution.lower():
            patterns_to_check.append(r'fn\s+\w+')
        if "const " in solution.lower():
            patterns_to_check.append(r'const\s+\w+')
        if "var " in solution.lower():
            patterns_to_check.append(r'var\s+\w+')
        if "pub " in solution.lower():
            patterns_to_check.append(r'pub\s+')
        if "struct " in solution.lower():
            patterns_to_check.append(r'struct\s*\{')
        if "while " in solution.lower():
            patterns_to_check.append(r'while\s*\(')
        if "for " in solution.lower():
            patterns_to_check.append(r'for\s*\(')
        if "return " in solution.lower():
            patterns_to_check.append(r'return\s+')
        if "@import" in solution:
            patterns_to_check.append(r'@import')
            
    elif language == "haskell":
        if "putStrLn" in solution:
            patterns_to_check.append(r'putStrLn\s+')
        if "putStr " in solution:
            patterns_to_check.append(r'putStr\s+')
        if "print " in solution.lower():
            patterns_to_check.append(r'print\s+')
        if "main " in solution.lower() or "main=" in solution.lower().replace(" ", ""):
            patterns_to_check.append(r'main\s*[=:]')
        if "where" in solution.lower():
            patterns_to_check.append(r'where')
        if "let " in solution.lower():
            patterns_to_check.append(r'let\s+')
        if "in " in solution.lower():
            patterns_to_check.append(r'\bin\b')
        if "do" in solution.lower():
            patterns_to_check.append(r'\bdo\b')
        if "import " in solution.lower():
            patterns_to_check.append(r'import\s+')
        if "::" in solution:
            patterns_to_check.append(r'::')
        if "if " in solution.lower():
            patterns_to_check.append(r'if\s+')
        if "then " in solution.lower():
            patterns_to_check.append(r'then\s+')
        if "else " in solution.lower():
            patterns_to_check.append(r'else\s+')
        if "case " in solution.lower():
            patterns_to_check.append(r'case\s+')
        if "data " in solution.lower():
            patterns_to_check.append(r'data\s+\w+')
        if "class " in solution.lower():
            patterns_to_check.append(r'class\s+\w+')
        if "->" in solution:
            patterns_to_check.append(r'->')
        if "map " in solution.lower():
            patterns_to_check.append(r'map\s+')
        if "filter " in solution.lower():
            patterns_to_check.append(r'filter\s+')
            
    elif language == "lua":
        if "print" in solution.lower():
            patterns_to_check.append(r'print\s*\(')
        if "function " in solution.lower():
            patterns_to_check.append(r'function\s+\w*')
        if "local " in solution.lower():
            patterns_to_check.append(r'local\s+\w+')
        if "if " in solution.lower():
            patterns_to_check.append(r'if\s+')
        if "then" in solution.lower():
            patterns_to_check.append(r'then')
        if "end" in solution.lower():
            patterns_to_check.append(r'\bend\b')
        if "for " in solution.lower():
            patterns_to_check.append(r'for\s+\w+')
        if "while " in solution.lower():
            patterns_to_check.append(r'while\s+')
        if "repeat" in solution.lower():
            patterns_to_check.append(r'repeat')
        if "require" in solution.lower():
            patterns_to_check.append(r'require\s*\(')
        if "return " in solution.lower():
            patterns_to_check.append(r'return\s+')
        if "table." in solution.lower():
            patterns_to_check.append(r'table\.\w+')
        if ".." in solution:
            patterns_to_check.append(r'\.\.')
            
    elif language == "skript":
        if "broadcast" in solution.lower():
            patterns_to_check.append(r'broadcast\s+')
        if "send" in solution.lower():
            patterns_to_check.append(r'send\s+')
        if "command" in solution.lower():
            patterns_to_check.append(r'command\s+')
        if "trigger" in solution.lower():
            patterns_to_check.append(r'trigger')
        if "set " in solution.lower():
            patterns_to_check.append(r'set\s+')
        if "if " in solution.lower():
            patterns_to_check.append(r'if\s+')
        if "loop " in solution.lower():
            patterns_to_check.append(r'loop\s+')
        if "on " in solution.lower():
            patterns_to_check.append(r'on\s+')
        if "player" in solution.lower():
            patterns_to_check.append(r'player')
        if "event" in solution.lower():
            patterns_to_check.append(r'event')
    
    # Check patterns
    patterns_matched = 0
    for pattern in patterns_to_check:
        if re.search(pattern, user_code, re.IGNORECASE):
            patterns_matched += 1
    
    if not patterns_to_check:
        if user_normalized == solution_normalized:
            return True, "Perfect match!"
        elif solution_normalized in user_normalized or user_normalized in solution_normalized:
            return True, "Good solution!"
        elif len(user_code) >= len(solution) * 0.3:
            return True, "Code accepted"
        return False, "Code doesn't match expected solution"
    
    match_ratio = patterns_matched / len(patterns_to_check) if patterns_to_check else 0
    
    if match_ratio >= 0.6:
        return True, "Great code!"
    elif match_ratio >= 0.4:
        return True, "Good attempt!"
    elif match_ratio >= 0.2:
        return True, "Partial solution accepted"
    
    return False, "Code doesn't include required elements"

# ============== PROGRAMMING LANGUAGES ==============

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
    # VIP Exclusive Badges
    {"id": "vip_member", "name": "VIP Member", "description": "Subscribe to VIP", "icon": "star", "xp_reward": 100, "vip_only": True},
    {"id": "vip_veteran", "name": "VIP Veteran", "description": "VIP for 3 months", "icon": "ribbon", "xp_reward": 200, "vip_only": True},
    {"id": "practice_master", "name": "Practice Master", "description": "Complete 100 practice sessions", "icon": "barbell", "xp_reward": 50},
]

# ============== VIP PERKS INFO ==============

VIP_INFO = {
    "how_to_earn": "Maintain a 7-day streak to earn VIP status!",
    "streak_required": 7,
    "perks": [
        {"icon": "heart", "title": "10 HEARTS", "description": "Double the lives to keep learning"},
        {"icon": "flash", "title": "1.5X XP", "description": "Level up 50% faster"},
        {"icon": "bulb", "title": "5 HINTS/LESSON", "description": "More help when you're stuck"},
        {"icon": "snow", "title": "2 STREAK FREEZES/WEEK", "description": "Protect your streak"},
        {"icon": "star", "title": "EXCLUSIVE BADGES", "description": "VIP-only achievements"},
        {"icon": "rocket", "title": "EARLY ACCESS", "description": "New features first"},
    ]
}

# ============== LESSON GENERATION WITH PRACTICE MODE ==============

def generate_practice_content(language_id: str, topic: str) -> dict:
    """Generate detailed practice/learning content for a topic"""
    practice_content = {
        "python": {
            "hello world": {
                "explanation": "The print() function outputs text to the screen. It's the most basic way to display information in Python.",
                "syntax": "print('Your text here')",
                "examples": [
                    {"code": "print('Hello, World!')", "output": "Hello, World!"},
                    {"code": "print('Python is fun!')", "output": "Python is fun!"},
                    {"code": "print(42)", "output": "42"},
                ],
                "tips": [
                    "Use single or double quotes for strings",
                    "print() adds a newline automatically",
                    "You can print numbers without quotes",
                ],
                "common_mistakes": [
                    "Forgetting the parentheses: print 'hello' ❌",
                    "Mismatched quotes: print('hello\") ❌",
                ],
            },
            "variables": {
                "explanation": "Variables store data that can be used and changed throughout your program. In Python, you don't need to declare the type.",
                "syntax": "variable_name = value",
                "examples": [
                    {"code": "name = 'Alice'", "output": "Creates a string variable"},
                    {"code": "age = 25", "output": "Creates an integer variable"},
                    {"code": "price = 19.99", "output": "Creates a float variable"},
                ],
                "tips": [
                    "Use descriptive names (user_age, not x)",
                    "Python is case-sensitive (Name ≠ name)",
                    "Use snake_case for variable names",
                ],
                "common_mistakes": [
                    "Starting with a number: 2name = 'test' ❌",
                    "Using spaces: my name = 'test' ❌",
                ],
            },
            "data types": {
                "explanation": "Python has several built-in data types: strings (text), integers (whole numbers), floats (decimals), booleans (True/False), lists, and dictionaries.",
                "syntax": "type(variable) - check the type",
                "examples": [
                    {"code": "type('hello')", "output": "<class 'str'>"},
                    {"code": "type(42)", "output": "<class 'int'>"},
                    {"code": "type(3.14)", "output": "<class 'float'>"},
                    {"code": "type(True)", "output": "<class 'bool'>"},
                ],
                "tips": [
                    "Strings are for text data",
                    "Use int for counting, float for measurements",
                    "Booleans are for yes/no conditions",
                ],
                "common_mistakes": [
                    "Confusing '42' (string) with 42 (int)",
                    "Using 'true' instead of True",
                ],
            },
        },
        "javascript": {
            "hello world": {
                "explanation": "console.log() outputs to the browser console. It's essential for debugging and displaying information.",
                "syntax": "console.log('Your text here');",
                "examples": [
                    {"code": "console.log('Hello, World!');", "output": "Hello, World!"},
                    {"code": "console.log(100 + 50);", "output": "150"},
                ],
                "tips": [
                    "Open browser DevTools (F12) to see output",
                    "End statements with semicolons",
                    "Use template literals: `Hello ${name}`",
                ],
                "common_mistakes": [
                    "Typing Console.log (capital C)",
                    "Forgetting the semicolon",
                ],
            },
            "variables": {
                "explanation": "JavaScript uses let, const, and var to declare variables. Use const for values that won't change, let for values that will.",
                "syntax": "let variableName = value;",
                "examples": [
                    {"code": "let name = 'Bob';", "output": "Mutable variable"},
                    {"code": "const PI = 3.14;", "output": "Constant (can't change)"},
                ],
                "tips": [
                    "Prefer const over let when possible",
                    "Avoid var (outdated)",
                    "Use camelCase for variable names",
                ],
                "common_mistakes": [
                    "Reassigning a const variable",
                    "Using var in modern code",
                ],
            },
        },
    }
    
    lang_content = practice_content.get(language_id, {})
    topic_lower = topic.lower()
    
    for key, content in lang_content.items():
        if key in topic_lower:
            return content
    
    # Default content
    return {
        "explanation": f"Learn about {topic} - an important concept in {language_id}.",
        "syntax": f"// {topic} syntax example",
        "examples": [
            {"code": f"// Example of {topic}", "output": "Result"},
        ],
        "tips": [
            "Practice makes perfect",
            "Read the documentation",
            "Try different variations",
        ],
        "common_mistakes": [
            "Not understanding the basics first",
            "Copying code without understanding",
        ],
    }

def generate_exercises(language_id: str, topic: str, unit: int) -> List[dict]:
    """Generate 10 exercises for a lesson"""
    exercises = []
    topic_lower = topic.lower()
    
    # Python exercises
    if language_id == "python":
        if "hello world" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "What function prints output in Python?", "options": ["print()", "echo()", "console.log()", "System.out.println()"], "correct": 0, "explanation": "print() is Python's built-in function for displaying output."},
                {"type": "multiple_choice", "question": "Which is the correct syntax to print 'Hello'?", "options": ["print('Hello')", "print Hello", "echo 'Hello'", "printf('Hello')"], "correct": 0, "explanation": "Python uses print() with parentheses and quotes around strings."},
                {"type": "code", "question": "Write code to print 'Hello, World!'", "starter": "", "solution": "print('Hello, World!')", "hint": "Use the print() function with a string", "explanation": "The basic print statement outputs text to the console."},
                {"type": "fill_blank", "question": "Complete: ___('Hello')", "answer": "print", "explanation": "print() is the function name."},
                {"type": "multiple_choice", "question": "What type of quotes can you use for strings?", "options": ["Both single and double", "Only single", "Only double", "Neither"], "correct": 0, "explanation": "Python accepts both 'text' and \"text\" as valid strings."},
                {"type": "code", "question": "Print your name using print()", "starter": "", "solution": "print('Name')", "hint": "Replace Name with any name in quotes", "explanation": "Any text in quotes is a valid string."},
                {"type": "multiple_choice", "question": "What happens if you forget the closing parenthesis?", "options": ["Syntax error", "Nothing prints", "Prints None", "Program crashes"], "correct": 0, "explanation": "Python requires balanced parentheses."},
                {"type": "fill_blank", "question": "print('Hi')  # This symbol starts a ___", "answer": "comment", "explanation": "# starts a comment in Python."},
                {"type": "code", "question": "Print 'Line 1' and 'Line 2' on separate lines", "starter": "", "solution": "print('Line 1')\nprint('Line 2')", "hint": "Use two print statements", "explanation": "Each print() creates a new line."},
                {"type": "multiple_choice", "question": "print() automatically adds what at the end?", "options": ["A newline", "A space", "Nothing", "A tab"], "correct": 0, "explanation": "print() adds \\n (newline) by default."},
            ]
        elif "variable" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "How do you create a variable in Python?", "options": ["name = 'John'", "var name = 'John'", "let name = 'John'", "String name = 'John'"], "correct": 0, "explanation": "Python uses simple assignment: variable = value"},
                {"type": "code", "question": "Create a variable called 'age' with value 25", "starter": "", "solution": "age = 25", "hint": "variable_name = value", "explanation": "No type declaration needed in Python."},
                {"type": "multiple_choice", "question": "What type is: x = 3.14?", "options": ["float", "int", "str", "bool"], "correct": 0, "explanation": "Numbers with decimals are floats."},
                {"type": "fill_blank", "question": "x ___ 10  # Assign 10 to x", "answer": "=", "explanation": "= is the assignment operator."},
                {"type": "multiple_choice", "question": "Which is a valid variable name?", "options": ["my_var", "2var", "my-var", "my var"], "correct": 0, "explanation": "Use letters, numbers, underscores. Can't start with number."},
                {"type": "code", "question": "Create x=5 and y=10, then print their sum", "starter": "", "solution": "x = 5\ny = 10\nprint(x + y)", "hint": "Create variables then use + to add", "explanation": "Variables can be used in expressions."},
                {"type": "multiple_choice", "question": "Can you change a variable's value?", "options": ["Yes", "No", "Only numbers", "Only once"], "correct": 0, "explanation": "Variables can be reassigned anytime."},
                {"type": "fill_blank", "question": "Check type with _____(x)", "answer": "type", "explanation": "type() returns the data type."},
                {"type": "code", "question": "Create name='Alice' and print it", "starter": "", "solution": "name = 'Alice'\nprint(name)", "hint": "Create string variable then print", "explanation": "Print can output variable values."},
                {"type": "multiple_choice", "question": "What is None in Python?", "options": ["Absence of value", "Zero", "Empty string", "False"], "correct": 0, "explanation": "None represents 'nothing' or 'no value'."},
            ]
        elif "data type" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "Which is a string?", "options": ["'Hello'", "42", "3.14", "True"], "correct": 0, "explanation": "Strings are text in quotes."},
                {"type": "code", "question": "Create a boolean variable 'is_active' set to True", "starter": "", "solution": "is_active = True", "hint": "Boolean values are True or False (capitalized)", "explanation": "Booleans represent yes/no values."},
                {"type": "fill_blank", "question": "Convert '42' to int: int(___)", "answer": "'42'", "explanation": "int() converts strings to integers."},
                {"type": "multiple_choice", "question": "What is type(42)?", "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'num'>"], "correct": 0, "explanation": "Whole numbers are integers (int)."},
                {"type": "code", "question": "Convert the integer 10 to a string", "starter": "", "solution": "str(10)", "hint": "Use str() function", "explanation": "str() converts to string type."},
                {"type": "multiple_choice", "question": "What is 5 / 2 in Python 3?", "options": ["2.5", "2", "3", "2.0"], "correct": 0, "explanation": "Division always returns float in Python 3."},
                {"type": "fill_blank", "question": "True and False are ___ values", "answer": "boolean", "explanation": "Booleans are True/False types."},
                {"type": "code", "question": "Create a list with numbers 1, 2, 3", "starter": "", "solution": "numbers = [1, 2, 3]", "hint": "Use square brackets []", "explanation": "Lists use square brackets."},
                {"type": "multiple_choice", "question": "Which is mutable (changeable)?", "options": ["list", "tuple", "string", "int"], "correct": 0, "explanation": "Lists can be modified after creation."},
                {"type": "code", "question": "Create a dictionary with key 'name' and value 'Bob'", "starter": "", "solution": "data = {'name': 'Bob'}", "hint": "Use curly braces {key: value}", "explanation": "Dictionaries store key-value pairs."},
            ]
        elif "if" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "What keyword starts a conditional?", "options": ["if", "when", "case", "check"], "correct": 0, "explanation": "if is the conditional keyword."},
                {"type": "code", "question": "Write: if age >= 18 print 'Adult'", "starter": "age = 20\n", "solution": "age = 20\nif age >= 18:\n    print('Adult')", "hint": "Remember the colon and indentation", "explanation": "Colon and indent are required."},
                {"type": "fill_blank", "question": "if x > 5___  # What comes after?", "answer": ":", "explanation": "Colon ends the if statement."},
                {"type": "multiple_choice", "question": "What is 'not equal' operator?", "options": ["!=", "<>", "=/=", "not="], "correct": 0, "explanation": "!= means not equal in Python."},
                {"type": "code", "question": "Check if number is positive (> 0)", "starter": "num = 5\n", "solution": "num = 5\nif num > 0:\n    print('Positive')", "hint": "Use > for greater than", "explanation": "Comparison operators return True/False."},
                {"type": "multiple_choice", "question": "What does 'and' do?", "options": ["Both must be True", "Either can be True", "Neither True", "Inverts"], "correct": 0, "explanation": "and requires both conditions True."},
                {"type": "fill_blank", "question": "if x > 0 ___ x < 10:", "answer": "and", "explanation": "and combines conditions."},
                {"type": "code", "question": "Write if-else: if x > 0 print 'Positive' else 'Not positive'", "starter": "x = -5\n", "solution": "x = -5\nif x > 0:\n    print('Positive')\nelse:\n    print('Not positive')", "hint": "else handles the opposite case", "explanation": "else catches all other cases."},
                {"type": "multiple_choice", "question": "What is 'not True'?", "options": ["False", "True", "None", "Error"], "correct": 0, "explanation": "not inverts boolean values."},
                {"type": "code", "question": "Check if string is empty", "starter": "s = ''\n", "solution": "s = ''\nif not s:\n    print('Empty')", "hint": "Empty strings are falsy", "explanation": "Empty containers are False in boolean context."},
            ]
        elif "for" in topic_lower and "loop" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "What does range(5) produce?", "options": ["0,1,2,3,4", "1,2,3,4,5", "0,1,2,3,4,5", "1,2,3,4"], "correct": 0, "explanation": "range(n) goes from 0 to n-1."},
                {"type": "code", "question": "Print numbers 1 to 5 using for loop", "starter": "", "solution": "for i in range(1, 6):\n    print(i)", "hint": "range(1, 6) gives 1,2,3,4,5", "explanation": "range(start, end) - end is exclusive."},
                {"type": "fill_blank", "question": "for item ___ my_list:", "answer": "in", "explanation": "in iterates over collections."},
                {"type": "multiple_choice", "question": "What is range(0, 10, 2)?", "options": ["0,2,4,6,8", "0,2,4,6,8,10", "2,4,6,8,10", "0,1,2"], "correct": 0, "explanation": "Third argument is the step."},
                {"type": "code", "question": "Print each letter in 'hello'", "starter": "", "solution": "for char in 'hello':\n    print(char)", "hint": "Strings are iterable", "explanation": "For loops work on any sequence."},
                {"type": "multiple_choice", "question": "Can you loop through a string?", "options": ["Yes", "No", "Only with index", "Only backwards"], "correct": 0, "explanation": "Strings are sequences of characters."},
                {"type": "code", "question": "Sum numbers 1 to 5 using for loop", "starter": "", "solution": "total = 0\nfor i in range(1, 6):\n    total += i\nprint(total)", "hint": "Use += to accumulate", "explanation": "+= adds to existing value."},
                {"type": "fill_blank", "question": "for i in ___(len(items)):", "answer": "range", "explanation": "range() with len() for index-based loops."},
                {"type": "code", "question": "Print indices and values of [10, 20, 30]", "starter": "", "solution": "for i, val in enumerate([10, 20, 30]):\n    print(i, val)", "hint": "Use enumerate()", "explanation": "enumerate() gives index and value."},
                {"type": "multiple_choice", "question": "What does enumerate() return?", "options": ["Index and value", "Just index", "Just value", "Length"], "correct": 0, "explanation": "enumerate() returns (index, item) pairs."},
            ]
        elif "function" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "Which keyword defines a function?", "options": ["def", "function", "func", "define"], "correct": 0, "explanation": "def is Python's function keyword."},
                {"type": "code", "question": "Create function greet() that prints 'Hello!'", "starter": "", "solution": "def greet():\n    print('Hello!')", "hint": "def function_name():", "explanation": "Functions group reusable code."},
                {"type": "fill_blank", "question": "___ my_function():", "answer": "def", "explanation": "def starts function definition."},
                {"type": "multiple_choice", "question": "How do you call function 'test'?", "options": ["test()", "call test", "run test()", "test"], "correct": 0, "explanation": "Parentheses call the function."},
                {"type": "code", "question": "Create add(a, b) that returns a + b", "starter": "", "solution": "def add(a, b):\n    return a + b", "hint": "Use return to give back value", "explanation": "return sends value back to caller."},
                {"type": "multiple_choice", "question": "What if function has no return?", "options": ["Returns None", "Error", "Returns 0", "Returns ''"], "correct": 0, "explanation": "Functions return None by default."},
                {"type": "code", "question": "Create square(n) returning n squared", "starter": "", "solution": "def square(n):\n    return n ** 2", "hint": "** is the power operator", "explanation": "n ** 2 means n squared."},
                {"type": "fill_blank", "question": "def greet(name='Guest'):  # 'Guest' is a ___ argument", "answer": "default", "explanation": "Default values are used when argument not provided."},
                {"type": "code", "question": "Create is_even(n) returning True if n is even", "starter": "", "solution": "def is_even(n):\n    return n % 2 == 0", "hint": "Even numbers have no remainder when divided by 2", "explanation": "% (modulo) gives remainder."},
                {"type": "multiple_choice", "question": "What is **kwargs used for?", "options": ["Keyword arguments", "All arguments", "No arguments", "Required args"], "correct": 0, "explanation": "**kwargs captures keyword arguments as dict."},
            ]
        elif "list" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "How to create an empty list?", "options": ["[]", "{}", "()", "list{}"], "correct": 0, "explanation": "[] creates an empty list."},
                {"type": "code", "question": "Create list [1, 2, 3] and append 4", "starter": "", "solution": "nums = [1, 2, 3]\nnums.append(4)", "hint": "Use .append() method", "explanation": "append() adds to the end."},
                {"type": "fill_blank", "question": "my_list.___(5)  # add 5 to end", "answer": "append", "explanation": "append() adds single item to end."},
                {"type": "multiple_choice", "question": "What does pop() do?", "options": ["Remove & return last item", "Remove first", "Add item", "Clear list"], "correct": 0, "explanation": "pop() removes and returns the last item."},
                {"type": "code", "question": "Get first 3 elements of [1,2,3,4,5]", "starter": "", "solution": "[1,2,3,4,5][:3]", "hint": "Use slicing [:3]", "explanation": "Slicing extracts portions of list."},
                {"type": "multiple_choice", "question": "How to insert at index 0?", "options": [".insert(0, x)", ".add(0, x)", ".put(0, x)", "[0] = x"], "correct": 0, "explanation": "insert(index, item) adds at position."},
                {"type": "code", "question": "Reverse the list [1, 2, 3]", "starter": "", "solution": "[1, 2, 3][::-1]", "hint": "Use [::-1] slicing", "explanation": "[::-1] reverses any sequence."},
                {"type": "fill_blank", "question": "list1 ___ list2  # combine lists", "answer": "+", "explanation": "+ concatenates lists."},
                {"type": "code", "question": "Create squares of 1-5 using list comprehension", "starter": "", "solution": "[x**2 for x in range(1, 6)]", "hint": "[expression for item in iterable]", "explanation": "List comprehension is concise list creation."},
                {"type": "multiple_choice", "question": "What is [1,2,3].index(2)?", "options": ["1", "2", "0", "3"], "correct": 0, "explanation": "index() returns position of value."},
            ]
        elif "class" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "Keyword to define a class?", "options": ["class", "def", "object", "new"], "correct": 0, "explanation": "class defines a new class."},
                {"type": "code", "question": "Create an empty class called Dog", "starter": "", "solution": "class Dog:\n    pass", "hint": "Use pass for empty body", "explanation": "pass is a placeholder that does nothing."},
                {"type": "fill_blank", "question": "___ MyClass:", "answer": "class", "explanation": "class keyword starts class definition."},
                {"type": "multiple_choice", "question": "Constructor method name?", "options": ["__init__", "__new__", "__create__", "__start__"], "correct": 0, "explanation": "__init__ initializes new objects."},
                {"type": "code", "question": "Add __init__ with name parameter to Dog", "starter": "", "solution": "class Dog:\n    def __init__(self, name):\n        self.name = name", "hint": "First param is always self", "explanation": "self refers to the instance."},
                {"type": "fill_blank", "question": "def __init__(___,  name):", "answer": "self", "explanation": "self is always first parameter."},
                {"type": "code", "question": "Add bark() method that prints 'Woof!'", "starter": "class Dog:\n    def __init__(self, name):\n        self.name = name\n", "solution": "class Dog:\n    def __init__(self, name):\n        self.name = name\n    def bark(self):\n        print('Woof!')", "hint": "Methods need self parameter", "explanation": "Instance methods take self first."},
                {"type": "multiple_choice", "question": "How to create an instance?", "options": ["Dog('Rex')", "new Dog('Rex')", "Dog.create('Rex')", "create Dog('Rex')"], "correct": 0, "explanation": "Call class like a function to create instance."},
                {"type": "code", "question": "Create Puppy class that inherits from Dog", "starter": "class Dog:\n    pass\n", "solution": "class Dog:\n    pass\n\nclass Puppy(Dog):\n    pass", "hint": "class Child(Parent):", "explanation": "Inheritance uses parentheses."},
                {"type": "multiple_choice", "question": "Call parent's __init__ using?", "options": ["super().__init__()", "parent.__init__()", "base.__init__()", "this.__init__()"], "correct": 0, "explanation": "super() accesses the parent class."},
            ]
    
    # ===== SHELL (BASH) EXERCISES =====
    if language_id == "shell":
        if "echo" in topic_lower or "hello" in topic_lower or "print" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "What command prints text in bash?", "options": ["echo", "print", "say", "write"], "correct": 0, "explanation": "echo is the primary output command in bash."},
                {"type": "code", "question": "Print 'Hello, World!' using echo", "starter": "", "solution": "echo 'Hello, World!'", "hint": "echo followed by text", "explanation": "echo outputs text to stdout."},
                {"type": "fill_blank", "question": "___ 'Hello World'", "answer": "echo", "explanation": "echo is the command."},
                {"type": "multiple_choice", "question": "What does echo -n do?", "options": ["No trailing newline", "Print numbers", "Echo to file", "Silent mode"], "correct": 0, "explanation": "-n suppresses the trailing newline."},
                {"type": "code", "question": "Print 'Name: Alice' using echo", "starter": "", "solution": "echo 'Name: Alice'", "hint": "Just use echo with the text", "explanation": "echo prints whatever string you give it."},
                {"type": "multiple_choice", "question": "Difference between single and double quotes?", "options": ["Double quotes expand variables", "No difference", "Single quotes expand vars", "Neither expands"], "correct": 0, "explanation": "Double quotes allow $variable expansion."},
                {"type": "code", "question": "Print value of $HOME variable", "starter": "", "solution": "echo $HOME", "hint": "$ accesses variable values", "explanation": "$VARIABLE accesses environment variables."},
                {"type": "fill_blank", "question": "echo -___ suppresses newline", "answer": "n", "explanation": "-n flag for no newline."},
                {"type": "code", "question": "Print 'Line 1' and 'Line 2' on separate lines", "starter": "", "solution": "echo 'Line 1'\necho 'Line 2'", "hint": "Use two echo commands", "explanation": "Each echo adds a newline by default."},
                {"type": "multiple_choice", "question": "What does printf do vs echo?", "options": ["Formatted output like C", "Same as echo", "Only prints numbers", "Prints to file"], "correct": 0, "explanation": "printf gives C-style formatted output."},
            ]
        elif "variable" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "How to create a variable in bash?", "options": ["name=value (no spaces)", "name = value", "set name value", "var name = value"], "correct": 0, "explanation": "No spaces around = in bash variable assignment!"},
                {"type": "code", "question": "Create variable name with value 'Alice'", "starter": "", "solution": "name='Alice'", "hint": "No spaces around =", "explanation": "Bash is strict about no spaces in assignment."},
                {"type": "fill_blank", "question": "Access variable: echo $___", "answer": "name", "explanation": "$ prefix accesses variable value."},
                {"type": "multiple_choice", "question": "What does readonly do?", "options": ["Makes variable constant", "Read from file", "Read user input", "Print variable"], "correct": 0, "explanation": "readonly prevents reassignment."},
                {"type": "code", "question": "Read user input into variable 'age'", "starter": "", "solution": "read -p 'Enter age: ' age", "hint": "read -p 'prompt' variable", "explanation": "read captures user input."},
                {"type": "multiple_choice", "question": "How to use variable in string?", "options": ["echo \"Hello $name\"", "echo 'Hello $name'", "echo Hello + name", "echo Hello name"], "correct": 0, "explanation": "Double quotes expand variables, single quotes don't."},
                {"type": "code", "question": "Create x=5 and y=10 then echo their sum", "starter": "", "solution": "x=5\ny=10\necho $((x + y))", "hint": "$(( )) for arithmetic", "explanation": "$(( )) does integer arithmetic in bash."},
                {"type": "fill_blank", "question": "$((3 + 4)) uses ___ expansion", "answer": "arithmetic", "explanation": "$(( )) is arithmetic expansion."},
                {"type": "code", "question": "Export a variable PATH_EXTRA='/usr/local'", "starter": "", "solution": "export PATH_EXTRA='/usr/local'", "hint": "export makes it available to subprocesses", "explanation": "export shares variable with child processes."},
                {"type": "multiple_choice", "question": "What does $? contain?", "options": ["Exit code of last command", "Current PID", "Username", "Home directory"], "correct": 0, "explanation": "$? holds the last command's exit status."},
            ]
        elif "if" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "Bash if statement ends with?", "options": ["fi", "end", "endif", "}"], "correct": 0, "explanation": "fi closes the if block (if backwards!)."},
                {"type": "code", "question": "If x=5, check if x equals 5", "starter": "x=5\n", "solution": "x=5\nif [ $x -eq 5 ]; then\n    echo 'Five!'\nfi", "hint": "Use [ $x -eq 5 ] for numeric compare", "explanation": "-eq is 'equals' for numbers."},
                {"type": "fill_blank", "question": "if [ $a ___ $b ]; then  # greater than", "answer": "-gt", "explanation": "-gt means 'greater than' for integers."},
                {"type": "multiple_choice", "question": "String equality operator?", "options": ["=", "-eq", "==", "equals"], "correct": 0, "explanation": "= compares strings in [ ] brackets."},
                {"type": "code", "question": "Check if file /etc/passwd exists", "starter": "", "solution": "if [ -f /etc/passwd ]; then\n    echo 'File exists'\nfi", "hint": "-f tests if file exists", "explanation": "-f checks regular file existence."},
                {"type": "multiple_choice", "question": "What does -d check?", "options": ["Directory exists", "File deleted", "Data type", "Debug mode"], "correct": 0, "explanation": "-d checks if directory exists."},
                {"type": "code", "question": "Write if-else: if x>0 echo 'positive' else 'not positive'", "starter": "x=-3\n", "solution": "x=-3\nif [ $x -gt 0 ]; then\n    echo 'positive'\nelse\n    echo 'not positive'\nfi", "hint": "else goes before fi", "explanation": "else handles the other case."},
                {"type": "fill_blank", "question": "if [ -___ filename ]  # check file exists", "answer": "f", "explanation": "-f tests for regular file."},
                {"type": "code", "question": "Check if string is empty: s=''", "starter": "s=''\n", "solution": "s=''\nif [ -z \"$s\" ]; then\n    echo 'Empty'\nfi", "hint": "-z checks if string length is zero", "explanation": "-z is true when string is empty."},
                {"type": "multiple_choice", "question": "What's the && operator in bash?", "options": ["AND - run next if previous succeeded", "OR operator", "Always run both", "Pipe"], "correct": 0, "explanation": "&& runs the next command only if the first succeeds."},
            ]

    # ===== HASKELL EXERCISES =====
    elif language_id == "haskell":
        if "hello" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "What function prints a line in Haskell?", "options": ["putStrLn", "print", "echo", "console.log"], "correct": 0, "explanation": "putStrLn prints a string with a newline."},
                {"type": "code", "question": "Print 'Hello, World!' in Haskell", "starter": "", "solution": "main = putStrLn \"Hello, World!\"", "hint": "main = putStrLn \"text\"", "explanation": "main is the entry point; putStrLn prints text."},
                {"type": "fill_blank", "question": "main = ___ \"Hello\"", "answer": "putStrLn", "explanation": "putStrLn outputs a string line."},
                {"type": "multiple_choice", "question": "What is the entry point of a Haskell program?", "options": ["main", "start", "init", "run"], "correct": 0, "explanation": "main is always the entry point."},
                {"type": "code", "question": "Print the number 42 using print", "starter": "", "solution": "main = print 42", "hint": "print works for showable types", "explanation": "print shows any Showable value."},
                {"type": "multiple_choice", "question": "Difference between putStrLn and print?", "options": ["putStrLn is for strings, print adds quotes", "No difference", "print is for strings", "putStrLn is deprecated"], "correct": 0, "explanation": "print adds quotes around strings; putStrLn doesn't."},
                {"type": "fill_blank", "question": "main = ___ 42  -- print a number", "answer": "print", "explanation": "print displays any Show instance."},
                {"type": "code", "question": "Print two lines using do notation", "starter": "", "solution": "main = do\n    putStrLn \"Line 1\"\n    putStrLn \"Line 2\"", "hint": "do notation sequences IO actions", "explanation": "do lets you sequence multiple IO actions."},
                {"type": "multiple_choice", "question": "Haskell strings use which quotes?", "options": ["Double quotes", "Single quotes", "Backticks", "No quotes"], "correct": 0, "explanation": "Haskell uses double quotes for strings, single quotes for Char."},
                {"type": "code", "question": "Concatenate two strings and print", "starter": "", "solution": "main = putStrLn (\"Hello\" ++ \" World\")", "hint": "++ concatenates strings/lists", "explanation": "++ is the list/string concatenation operator."},
            ]
        elif "type" in topic_lower or "function" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "What is Haskell's type for whole numbers?", "options": ["Int or Integer", "Number", "Num", "float"], "correct": 0, "explanation": "Int is fixed-size, Integer is arbitrary precision."},
                {"type": "code", "question": "Define a function double that multiplies by 2", "starter": "", "solution": "double x = x * 2", "hint": "functionName param = expression", "explanation": "Haskell functions are defined with pattern = expression."},
                {"type": "fill_blank", "question": "add x y = x ___ y", "answer": "+", "explanation": "Operators work naturally in expressions."},
                {"type": "multiple_choice", "question": "What does :: mean in Haskell?", "options": ["Has type (type annotation)", "Assignment", "Comparison", "Concatenation"], "correct": 0, "explanation": ":: declares the type of a value or function."},
                {"type": "code", "question": "Write type signature: add takes two Ints, returns Int", "starter": "", "solution": "add :: Int -> Int -> Int\nadd x y = x + y", "hint": "funcName :: Type -> Type -> ReturnType", "explanation": "-> separates parameter and return types."},
                {"type": "multiple_choice", "question": "Are Haskell functions pure by default?", "options": ["Yes, no side effects", "No, they can mutate", "Only in main", "Depends on module"], "correct": 0, "explanation": "Haskell functions are pure — same input always gives same output."},
                {"type": "code", "question": "Define isEven that returns True for even numbers", "starter": "", "solution": "isEven n = n `mod` 2 == 0", "hint": "Use mod for remainder", "explanation": "mod gives remainder; backticks make it infix."},
                {"type": "fill_blank", "question": "factorial 0 = 1\nfactorial n = n * factorial (n-___)", "answer": "1", "explanation": "Recursion: base case 0=1, recursive case n*(n-1)!."},
                {"type": "code", "question": "Use where clause: area of circle with radius r", "starter": "", "solution": "circleArea r = pi * r * r\n    where pi = 3.14159", "hint": "where defines local bindings", "explanation": "where lets you name intermediate values."},
                {"type": "multiple_choice", "question": "What is a guard in Haskell?", "options": ["Conditional branches using |", "Error handler", "Type checker", "Import guard"], "correct": 0, "explanation": "Guards use | to define conditional function bodies."},
            ]

    # ===== ELIXIR EXERCISES =====
    elif language_id == "elixir":
        if "hello" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "What function prints in Elixir?", "options": ["IO.puts", "print", "echo", "console.log"], "correct": 0, "explanation": "IO.puts prints a string with a newline."},
                {"type": "code", "question": "Print 'Hello, World!' in Elixir", "starter": "", "solution": "IO.puts(\"Hello, World!\")", "hint": "IO.puts(\"text\")", "explanation": "IO.puts outputs to stdout."},
                {"type": "fill_blank", "question": "IO.___(\"Hello\")", "answer": "puts", "explanation": "IO.puts prints with newline."},
                {"type": "multiple_choice", "question": "What does IO.inspect do?", "options": ["Prints and returns the value", "Only prints", "Inspects types", "Debugs code"], "correct": 0, "explanation": "IO.inspect is great for debugging — it prints AND returns the value."},
                {"type": "code", "question": "Use IO.inspect to debug a value", "starter": "", "solution": "IO.inspect([1, 2, 3])", "hint": "IO.inspect(value)", "explanation": "IO.inspect returns the value, useful in pipelines."},
                {"type": "multiple_choice", "question": "What is an atom in Elixir?", "options": [":name — a constant whose name is its value", "A number type", "A string type", "A variable"], "correct": 0, "explanation": "Atoms like :ok, :error are constants — their name IS the value."},
                {"type": "code", "question": "Create an atom called :hello and inspect it", "starter": "", "solution": "IO.inspect(:hello)", "hint": "Atoms start with :", "explanation": ":hello is an atom literal."},
                {"type": "fill_blank", "question": "Elixir atoms start with ___", "answer": ":", "explanation": "The colon prefix creates an atom."},
                {"type": "code", "question": "String interpolation: print 'Hello, name!'", "starter": "name = \"Alice\"\n", "solution": "name = \"Alice\"\nIO.puts(\"Hello, #{name}!\")", "hint": "#{variable} inside double-quoted strings", "explanation": "String interpolation uses #{} syntax."},
                {"type": "multiple_choice", "question": "How does Elixir handle immutability?", "options": ["All data is immutable", "Only atoms are immutable", "Nothing is immutable", "Optional immutability"], "correct": 0, "explanation": "All data in Elixir is immutable — you create new values, not modify."},
            ]
        elif "pattern" in topic_lower or "match" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "What does = do in Elixir?", "options": ["Pattern matching (not just assignment)", "Only assignment", "Comparison", "Type check"], "correct": 0, "explanation": "= is the match operator. It does pattern matching!"},
                {"type": "code", "question": "Pattern match to extract first element", "starter": "", "solution": "[head | _tail] = [1, 2, 3]\nIO.puts(head)", "hint": "[head | tail] splits a list", "explanation": "| separates head from tail of a list."},
                {"type": "fill_blank", "question": "{a, _} = {1, 2}  # a = ___", "answer": "1", "explanation": "Pattern matching extracts the first element."},
                {"type": "multiple_choice", "question": "What does _ mean in pattern matching?", "options": ["Ignore this value", "Any value assigned", "Error", "Nil"], "correct": 0, "explanation": "_ is a wildcard — it matches anything and discards it."},
                {"type": "code", "question": "Use case to match on atoms", "starter": "", "solution": "status = :ok\ncase status do\n  :ok -> IO.puts(\"Success\")\n  :error -> IO.puts(\"Failed\")\nend", "hint": "case value do pattern -> result end", "explanation": "case matches against patterns."},
                {"type": "multiple_choice", "question": "What is the pipe operator |> ?", "options": ["Passes result to next function", "Or operator", "Pattern match", "Assignment"], "correct": 0, "explanation": "|> passes the result of the left side as the first argument to the right."},
                {"type": "code", "question": "Use pipe operator to uppercase a string", "starter": "", "solution": "\"hello\" |> String.upcase() |> IO.puts()", "hint": "value |> function |> function", "explanation": "Pipe chains make data flow readable."},
                {"type": "fill_blank", "question": "\"hello\" |> String.___()  # uppercase", "answer": "upcase", "explanation": "String.upcase() converts to uppercase."},
                {"type": "code", "question": "Define a function that greets using pattern matching", "starter": "", "solution": "defmodule Greeter do\n  def greet(:morning), do: IO.puts(\"Good morning!\")\n  def greet(:evening), do: IO.puts(\"Good evening!\")\nend", "hint": "Multiple function clauses match different patterns", "explanation": "Elixir allows multiple function definitions with different patterns."},
                {"type": "multiple_choice", "question": "Can you match on function arguments?", "options": ["Yes, with multiple clauses", "No", "Only in case", "Only with guards"], "correct": 0, "explanation": "Function heads can pattern match on arguments."},
            ]

    # ===== ZIG EXERCISES =====
    elif language_id == "zig":
        if "hello" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "How do you print in Zig?", "options": ["std.debug.print", "printf", "console.log", "print"], "correct": 0, "explanation": "std.debug.print is Zig's debug output function."},
                {"type": "code", "question": "Print 'Hello, World!' in Zig", "starter": "", "solution": "const std = @import(\"std\");\npub fn main() void {\n    std.debug.print(\"Hello, World!\\n\", .{});\n}", "hint": "Use std.debug.print with .{} for args", "explanation": "Zig uses @import for the standard library."},
                {"type": "fill_blank", "question": "const std = @___(\"std\");", "answer": "import", "explanation": "@import brings in modules."},
                {"type": "multiple_choice", "question": "What does pub mean in Zig?", "options": ["Public — accessible from outside", "Publish", "Pure", "Put"], "correct": 0, "explanation": "pub makes a declaration visible outside the file."},
                {"type": "code", "question": "Declare a constant integer in Zig", "starter": "", "solution": "const x: i32 = 42;", "hint": "const name: type = value;", "explanation": "const declares immutable bindings in Zig."},
                {"type": "multiple_choice", "question": "What is Zig's philosophy?", "options": ["No hidden allocations, explicit control", "Garbage collected", "Object-oriented", "Dynamic typing"], "correct": 0, "explanation": "Zig gives you explicit control over memory with no hidden behavior."},
                {"type": "fill_blank", "question": "pub fn main() ___ { }", "answer": "void", "explanation": "main returns void (nothing)."},
                {"type": "code", "question": "Create a mutable variable in Zig", "starter": "", "solution": "var x: i32 = 5;\nx = 10;", "hint": "var for mutable, const for immutable", "explanation": "var allows mutation, const does not."},
                {"type": "multiple_choice", "question": "What type is i32?", "options": ["32-bit signed integer", "32-bit float", "32 characters", "32 bytes"], "correct": 0, "explanation": "i32 = signed integer with 32 bits. u32 = unsigned."},
                {"type": "code", "question": "Print a variable using std.debug.print", "starter": "", "solution": "const x: i32 = 42;\nstd.debug.print(\"x = {}\\n\", .{x});", "hint": "{} is the format placeholder", "explanation": ".{x} passes x as a format argument."},
            ]
        elif "variable" in topic_lower or "const" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "Which keyword makes an immutable binding?", "options": ["const", "var", "let", "final"], "correct": 0, "explanation": "const creates immutable bindings in Zig."},
                {"type": "code", "question": "Create const pi with value 3.14", "starter": "", "solution": "const pi: f64 = 3.14;", "hint": "const name: f64 = value;", "explanation": "f64 is a 64-bit floating point."},
                {"type": "fill_blank", "question": "___ x: i32 = 5;  // mutable", "answer": "var", "explanation": "var creates mutable bindings."},
                {"type": "multiple_choice", "question": "Can you reassign a const?", "options": ["No, compile error", "Yes", "Only in functions", "Only once"], "correct": 0, "explanation": "const is truly immutable in Zig."},
                {"type": "code", "question": "Create array of 5 integers", "starter": "", "solution": "const arr = [5]i32{ 1, 2, 3, 4, 5 };", "hint": "[length]type{ values }", "explanation": "Zig arrays have compile-time known lengths."},
                {"type": "multiple_choice", "question": "What is comptime in Zig?", "options": ["Compile-time evaluation", "Runtime check", "Comment time", "Compare time"], "correct": 0, "explanation": "comptime forces evaluation at compile time for optimization."},
                {"type": "code", "question": "Use defer to print 'Done' at end of scope", "starter": "", "solution": "defer std.debug.print(\"Done\\n\", .{});", "hint": "defer runs at scope exit", "explanation": "defer ensures cleanup runs when leaving scope."},
                {"type": "fill_blank", "question": "const slice = arr[0..___];  // first 3", "answer": "3", "explanation": "Slicing uses [start..end] with exclusive end."},
                {"type": "code", "question": "Use optional type for nullable integer", "starter": "", "solution": "var maybe_x: ?i32 = null;\nmaybe_x = 42;", "hint": "?Type makes it optional", "explanation": "?i32 means 'maybe an i32, maybe null'."},
                {"type": "multiple_choice", "question": "Error handling in Zig uses?", "options": ["Error unions (!) and try/catch", "Exceptions", "Error codes only", "Panic only"], "correct": 0, "explanation": "Zig uses ! for error unions, try to unwrap, catch to handle."},
            ]

    # ===== LUA EXERCISES =====
    elif language_id == "lua":
        if "hello" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "How do you print in Lua?", "options": ["print()", "echo", "console.log", "puts"], "correct": 0, "explanation": "print() is Lua's output function."},
                {"type": "code", "question": "Print 'Hello, World!' in Lua", "starter": "", "solution": "print('Hello, World!')", "hint": "print('text')", "explanation": "print() outputs text to stdout."},
                {"type": "fill_blank", "question": "___('Hello World')", "answer": "print", "explanation": "print is the output function."},
                {"type": "multiple_choice", "question": "Lua is commonly used for?", "options": ["Game scripting (Roblox, game engines)", "Web servers", "Operating systems", "Databases"], "correct": 0, "explanation": "Lua is popular for game scripting, especially Roblox."},
                {"type": "code", "question": "Concatenate two strings and print", "starter": "", "solution": "print('Hello' .. ' World')", "hint": ".. is string concatenation", "explanation": "In Lua, .. joins strings together."},
                {"type": "multiple_choice", "question": "What operator concatenates strings in Lua?", "options": ["..", "+", "&", "concat"], "correct": 0, "explanation": ".. is the string concatenation operator."},
                {"type": "code", "question": "Print a number and a string together", "starter": "", "solution": "print('Score: ' .. tostring(42))", "hint": "Use tostring() to convert numbers", "explanation": "tostring() converts numbers for concatenation."},
                {"type": "fill_blank", "question": "'Hello' ___ ' World'  -- concatenate", "answer": "..", "explanation": ".. joins strings in Lua."},
                {"type": "code", "question": "Print multiple values separated by tab", "starter": "", "solution": "print('Name', 'Age', 'Score')", "hint": "print() with commas adds tabs", "explanation": "Multiple arguments to print are tab-separated."},
                {"type": "multiple_choice", "question": "Lua arrays start at index?", "options": ["1", "0", "-1", "Any number"], "correct": 0, "explanation": "Lua tables/arrays are 1-indexed by convention!"},
            ]
        elif "variable" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "How to create a local variable?", "options": ["local x = 5", "var x = 5", "let x = 5", "int x = 5"], "correct": 0, "explanation": "local declares a variable with local scope."},
                {"type": "code", "question": "Create local variable name = 'Alice'", "starter": "", "solution": "local name = 'Alice'\nprint(name)", "hint": "local varname = value", "explanation": "local limits scope to current block."},
                {"type": "fill_blank", "question": "___ x = 10  -- local variable", "answer": "local", "explanation": "local keyword for local scope."},
                {"type": "multiple_choice", "question": "What happens without 'local'?", "options": ["Variable becomes global", "Error", "Stays local", "Read-only"], "correct": 0, "explanation": "Without local, variables are global (bad practice!)."},
                {"type": "code", "question": "Create a table (object) with name and age", "starter": "", "solution": "local person = {name = 'Alice', age = 25}\nprint(person.name)", "hint": "local t = {key = value}", "explanation": "Tables are Lua's only data structure."},
                {"type": "multiple_choice", "question": "What is nil in Lua?", "options": ["Absence of value (like null)", "Zero", "Empty string", "False"], "correct": 0, "explanation": "nil means 'no value' in Lua."},
                {"type": "code", "question": "Create array with numbers 10, 20, 30", "starter": "", "solution": "local arr = {10, 20, 30}\nprint(arr[1])", "hint": "Arrays are tables with numeric keys", "explanation": "Remember: Lua arrays start at index 1!"},
                {"type": "fill_blank", "question": "Check type: ___(x)  -- returns type name", "answer": "type", "explanation": "type() returns the type as a string."},
                {"type": "code", "question": "Multiple assignment: a=1, b=2, c=3", "starter": "", "solution": "local a, b, c = 1, 2, 3\nprint(a, b, c)", "hint": "Lua supports multiple assignment", "explanation": "Multiple variables can be assigned at once."},
                {"type": "multiple_choice", "question": "How many data types does Lua have?", "options": ["8 (nil, boolean, number, string, table, function, thread, userdata)", "3", "Unlimited", "1"], "correct": 0, "explanation": "Lua has 8 basic types — tables handle arrays, dicts, objects."},
            ]

    # ===== SKRIPT EXERCISES =====
    elif language_id == "skript":
        if "hello" in topic_lower or "message" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "How to send a message to all players?", "options": ["broadcast", "send", "tell", "say"], "correct": 0, "explanation": "broadcast sends a message to every player on the server."},
                {"type": "code", "question": "Broadcast 'Hello World' to the server", "starter": "", "solution": "broadcast \"Hello World\"", "hint": "broadcast \"text\"", "explanation": "broadcast shows a message to all players."},
                {"type": "fill_blank", "question": "___ \"Welcome to the server!\"", "answer": "broadcast", "explanation": "broadcast is for server-wide messages."},
                {"type": "multiple_choice", "question": "How to send message to one player?", "options": ["send \"msg\" to player", "broadcast \"msg\"", "tell player \"msg\"", "dm player \"msg\""], "correct": 0, "explanation": "send \"message\" to player sends to one player."},
                {"type": "code", "question": "Send a message to the event player", "starter": "", "solution": "send \"Hello %player%!\" to player", "hint": "send \"text\" to player", "explanation": "%player% inserts the player's name."},
                {"type": "multiple_choice", "question": "What does %player% do in Skript?", "options": ["Inserts the player's name", "Creates a player", "Kills a player", "Nothing"], "correct": 0, "explanation": "% wraps expressions that get evaluated."},
                {"type": "code", "question": "Create a command /hello that broadcasts", "starter": "", "solution": "command /hello:\n    trigger:\n        broadcast \"Hello from %player%!\"", "hint": "command /name: trigger: effects", "explanation": "Commands need command, trigger, and effects."},
                {"type": "fill_blank", "question": "command /greet:\n    ___:\n        broadcast \"Hi!\"", "answer": "trigger", "explanation": "trigger defines what happens when command runs."},
                {"type": "code", "question": "Send a colored message (green)", "starter": "", "solution": "broadcast \"&aThis is green text!\"", "hint": "&a is green color code", "explanation": "Minecraft color codes: &a=green, &c=red, &e=yellow."},
                {"type": "multiple_choice", "question": "What is the Skript file extension?", "options": [".sk", ".skript", ".mc", ".txt"], "correct": 0, "explanation": "Skript files use the .sk extension."},
            ]
        elif "event" in topic_lower or "join" in topic_lower:
            exercises = [
                {"type": "multiple_choice", "question": "How to detect when a player joins?", "options": ["on join:", "on player join:", "event join:", "when join:"], "correct": 0, "explanation": "on join: triggers when any player joins."},
                {"type": "code", "question": "Welcome a player when they join", "starter": "", "solution": "on join:\n    send \"Welcome, %player%!\" to player", "hint": "on join: + send to player", "explanation": "on join triggers for each joining player."},
                {"type": "fill_blank", "question": "on ___:\n    broadcast \"%player% left!\"", "answer": "quit", "explanation": "on quit: triggers when player leaves."},
                {"type": "multiple_choice", "question": "How to detect block breaking?", "options": ["on break:", "on mine:", "on destroy:", "on click:"], "correct": 0, "explanation": "on break: detects block breaking."},
                {"type": "code", "question": "Cancel damage to players (no PvP)", "starter": "", "solution": "on damage of player:\n    cancel event", "hint": "cancel event stops it from happening", "explanation": "cancel event prevents the default action."},
                {"type": "multiple_choice", "question": "What does 'cancel event' do?", "options": ["Prevents the event from happening", "Logs the event", "Delays the event", "Nothing"], "correct": 0, "explanation": "cancel event stops the default Minecraft behavior."},
                {"type": "code", "question": "Give player diamond sword on join", "starter": "", "solution": "on join:\n    give player diamond sword", "hint": "give player [item]", "explanation": "give directly puts items in inventory."},
                {"type": "fill_blank", "question": "on death:\n    ___ event  # prevent death", "answer": "cancel", "explanation": "cancel event prevents the death."},
                {"type": "code", "question": "Broadcast when a player breaks a diamond ore", "starter": "", "solution": "on break of diamond ore:\n    broadcast \"%player% found diamonds!\"", "hint": "on break of [block type]:", "explanation": "You can filter events by specific items/blocks."},
                {"type": "multiple_choice", "question": "Which event fires on right-click?", "options": ["on right click:", "on click:", "on use:", "on interact:"], "correct": 0, "explanation": "on right click: detects right-click interactions."},
            ]

    # If no specific exercises, generate generic ones
    if not exercises:
        exercises = [
            {"type": "multiple_choice", "question": f"What is {topic} used for in {language_id}?", "options": ["Core functionality", "Optional feature", "Deprecated", "Not available"], "correct": 0, "explanation": f"{topic} is a fundamental concept."},
            {"type": "code", "question": f"Write a basic {topic} example", "starter": f"# {topic} example\n", "solution": f"# {topic} implementation", "hint": f"Think about {topic} syntax", "explanation": "Practice the basic syntax."},
            {"type": "fill_blank", "question": f"The key concept in {topic} is ___", "answer": "code", "explanation": "Understanding is key."},
            {"type": "multiple_choice", "question": f"Why is {topic} important?", "options": ["Improves code quality", "Not important", "Only for experts", "Rarely used"], "correct": 0, "explanation": "It's a building block for more complex features."},
            {"type": "code", "question": f"Implement a simple {topic}", "starter": "", "solution": "# Implementation", "hint": "Start with the basics", "explanation": "Start simple and build up."},
            {"type": "multiple_choice", "question": f"Common mistake with {topic}?", "options": ["Forgetting syntax", "Using too much", "No mistakes possible", "Never happens"], "correct": 0, "explanation": "Pay attention to syntax details."},
            {"type": "fill_blank", "question": f"Best practice: ___ your code", "answer": "test", "explanation": "Always test your code."},
            {"type": "code", "question": f"Another {topic} example", "starter": "", "solution": "# Code here", "hint": "Practice makes perfect", "explanation": "Repetition builds skill."},
            {"type": "multiple_choice", "question": f"When to use {topic}?", "options": ["Appropriate situations", "Never", "Always", "Randomly"], "correct": 0, "explanation": "Use it when it fits the problem."},
            {"type": "fill_blank", "question": f"{topic} requires ___", "answer": "practice", "explanation": "Keep practicing!"},
        ]
    
    return exercises

def generate_lessons(language_id: str) -> List[dict]:
    """Generate lessons with practice content"""
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
        "haskell": [
            ("Basics", ["Hello World", "Types & Values", "Functions", "Let & Where", "Comments"]),
            ("Types", ["Int & Integer", "Bool & Char", "Strings & Lists", "Tuples", "Type Signatures"]),
            ("Functions", ["Pattern Matching", "Guards", "Recursion", "Higher-Order Functions", "Lambda"]),
            ("Lists", ["List Operations", "List Comprehension", "Map & Filter", "Fold", "Zip"]),
            ("Type System", ["Type Classes", "Custom Types", "Data & Newtype", "Maybe & Either", "Deriving"]),
            ("Advanced", ["IO Monad", "Do Notation", "Functors", "Applicatives", "Monads"]),
        ],
        "elixir": [
            ("Basics", ["Hello World", "Variables & Atoms", "Data Types", "Strings", "Basic Operators"]),
            ("Collections", ["Lists", "Tuples", "Maps", "Keyword Lists", "Enum Module"]),
            ("Control Flow", ["Pattern Matching", "Case", "Cond & If", "With", "Pipe Operator"]),
            ("Functions", ["Named Functions", "Anonymous Functions", "Guards", "Default Arguments", "Captures"]),
            ("Modules", ["Defmodule", "Module Attributes", "Structs", "Protocols", "Behaviours"]),
            ("Concurrency", ["Processes", "Tasks", "GenServer", "Supervision", "OTP Basics"]),
        ],
        "zig": [
            ("Basics", ["Hello World", "Variables & Const", "Data Types", "Comments", "Print & Debug"]),
            ("Types", ["Integers", "Floats", "Booleans", "Arrays", "Slices"]),
            ("Control Flow", ["If Expressions", "Switch", "For Loops", "While Loops", "Defer"]),
            ("Functions", ["Function Basics", "Parameters", "Return Values", "Error Unions", "Generics"]),
            ("Memory", ["Pointers", "Allocators", "Slices & Arrays", "Optional Values", "Undefined"]),
            ("Advanced", ["Structs", "Enums", "Unions", "Comptime", "Error Handling"]),
        ],
        "lua": [
            ("Basics", ["Hello World", "Variables", "Data Types", "Comments", "Operators"]),
            ("Control Flow", ["If Statements", "Else & Elseif", "For Loops", "While Loops", "Repeat Until"]),
            ("Functions", ["Function Basics", "Parameters", "Return Values", "Closures", "Varargs"]),
            ("Tables", ["Table Basics", "Arrays", "Dictionaries", "Table Methods", "Metatables"]),
            ("Strings", ["String Basics", "String Methods", "Pattern Matching", "Formatting", "Concatenation"]),
            ("Advanced", ["Modules", "File I/O", "Coroutines", "Error Handling", "OOP with Tables"]),
        ],
        "skript": [
            ("Basics", ["Hello World", "Messages", "Variables", "Comments", "Data Types"]),
            ("Events", ["Join Event", "Click Event", "Chat Event", "Death Event", "Custom Events"]),
            ("Commands", ["Command Basics", "Arguments", "Permissions", "Aliases", "Cooldowns"]),
            ("Effects", ["Teleport", "Give Items", "Spawn Mobs", "Potions", "Particles"]),
            ("Conditions", ["If Statements", "Comparisons", "Permissions Check", "Item Check", "Player State"]),
            ("Advanced", ["Loops", "Functions", "Scoreboards", "GUIs", "Timers"]),
        ],
    }
    
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
            exercises = generate_exercises(language_id, topic, unit_num)
            practice_content = generate_practice_content(language_id, topic)
            
            lessons.append({
                "id": lesson_id,
                "title": topic,
                "description": f"Learn about {topic.lower()}",
                "xp": 15 + (unit_num * 5) + (topic_idx * 3),
                "unit": unit_num,
                "unit_name": unit_name,
                "exercises": exercises,
                "practice_content": practice_content,
            })
    
    return lessons

# Pre-generate lessons

def infer_code_output(solution: str) -> str:
    match = re.search(r"print\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", solution or "")
    if match:
        return match.group(1)
    match = re.search(r"console\.log\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", solution or "")
    if match:
        return match.group(1)
    match = re.search(r"echo\s+['\"]?([^'\"\n]+)['\"]?", solution or "")
    if match:
        return match.group(1).strip()
    return "Result"

def add_challenge_variety(lesson: dict) -> dict:
    enriched = dict(lesson)
    exercises = [dict(ex) for ex in lesson.get("exercises", [])]
    code_seen = 0
    first_code_solution = ""
    for ex in exercises:
        if ex.get("type") == "code":
            code_seen += 1
            first_code_solution = first_code_solution or ex.get("solution", "")
            if code_seen == 1:
                ex["type"] = "fix_broken_code"
                ex["title"] = "Fix the broken code"
                ex["starter"] = ex.get("starter") or (ex.get("solution", "").replace("print(", "prnt(", 1) if "print(" in ex.get("solution", "") else "// fix this code\n" + ex.get("solution", ""))
            elif code_seen == 2:
                ex["type"] = "write_code"
                ex["title"] = "Write code from scratch"
            elif code_seen == 3:
                solution = ex.get("solution", "")
                blocks = [line for line in solution.split("\n") if line.strip()] or [part.strip() for part in solution.split(";") if part.strip()]
                if len(blocks) >= 2:
                    ex["type"] = "drag_drop"
                    ex["title"] = "Drag-and-drop code blocks"
                    ex["blocks"] = list(reversed(blocks))
                    ex["correct_order"] = blocks
                else:
                    ex["type"] = "write_code"
    if first_code_solution:
        for ex in exercises:
            if ex.get("type") == "multiple_choice":
                expected_output = infer_code_output(first_code_solution)
                ex.clear()
                ex.update({
                    "type": "predict_output",
                    "question": "Predict the output of this code.",
                    "code": first_code_solution,
                    "answer": expected_output,
                    "options": [expected_output, "Syntax error", "Nothing", "None"],
                    "hint": "Read the code from top to bottom and track what gets printed.",
                    "explanation": "Predict-output challenges train you to mentally run code before pressing Run.",
                })
                break
    enriched["exercises"] = exercises
    return enriched


LESSONS_CACHE = {lang["id"]: [add_challenge_variety(lesson) for lesson in generate_lessons(lang["id"])] for lang in LANGUAGES}

# ============== DAILY CHALLENGES ==============

def generate_daily_challenge() -> dict:
    challenge_types = [
        {
            "type": "speed_round",
            "title": "Speed Round",
            "description": "Answer 5 questions in 2 minutes",
            "xp_reward": 50,
            "gem_reward": 5,
            "time_limit": 120,
            "exercises": [
                {"type": "multiple_choice", "question": "What prints output in Python?", "options": ["print()", "echo()", "log()", "out()"], "correct": 0},
                {"type": "fill_blank", "question": "print('Hello ___')", "answer": "World"},
                {"type": "multiple_choice", "question": "Which is a loop?", "options": ["for", "if", "def", "class"], "correct": 0},
                {"type": "fill_blank", "question": "def function___:", "answer": "()"},
                {"type": "multiple_choice", "question": "String + String is?", "options": ["Concatenation", "Addition", "Error", "None"], "correct": 0},
            ],
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
        "gems": 10,
        "last_activity": None,
        "badges": [],
        "friends": [],
        "languages_studied": [],
        "daily_goal": 50,
        "daily_xp": 0,
        "daily_goal_streak": 0,
        "combo_multiplier": 1.0,
        "total_lessons_completed": 0,
        "perfect_lessons": 0,
        "practice_sessions": 0,
        "hints_used_today": 0,
        "vip_until": None,  # VIP expiration date
        "vip_months": 0,
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
        "profile": {
            "display_name": user.username,
            "bio": "",
            "avatar_color": "#00FF88",
            "display_badges": [],
        },
        "auth_methods": {
            "password": True,
            "email_verified": False,
            "passkey_ready": True,
            "google_ready": True,
        },
        "email_verified": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    await db.users.insert_one(user_dict)
    
    token = generate_token()
    await db.sessions.insert_one({"token": token, "user_id": user_dict["id"]})
    
    return {"token": token, "user": public_user(user_dict)}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or user["password"] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    now = datetime.utcnow()
    streak = user.get("streak", 0)
    if user.get("last_activity"):
        last = datetime.fromisoformat(user["last_activity"])
        days_diff = (now.date() - last.date()).days
        if days_diff == 1:
            streak += 1
        elif days_diff > 1:
            streak = 1
    else:
        streak = 1
    
    # Reset daily limits
    perks = get_vip_perks(user)
    update_fields = {
        "streak": streak,
        "last_activity": now.isoformat(),
        "hearts": perks["max_hearts"],
        "max_hearts": perks["max_hearts"],
        "daily_xp": 0,
        "combo_multiplier": 1.0,
        "hints_used_today": 0,
    }
    
    await db.users.update_one({"id": user["id"]}, {"$set": update_fields})
    
    token = generate_token()
    await db.sessions.insert_one({"token": token, "user_id": user["id"]})
    
    user.update(update_fields)
    return {"token": token, "user": public_user(user)}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return public_user(user)

@api_router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    await db.sessions.delete_one({"token": credentials.credentials})
    return {"message": "Logged out"}

# ============== VIP ROUTES ==============

@api_router.post("/auth/send-verification-code")
async def send_email_verification(request: VerificationCodeRequest, background_tasks: BackgroundTasks):
    code = f"{random.randint(100000, 999999)}"
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    await db.verification_codes.update_one(
        {"email": request.email.lower(), "used": False},
        {"$set": {
            "email": request.email.lower(),
            "code_hash": hash_password(code),
            "expires_at": expires_at,
            "used": False,
            "created_at": datetime.utcnow().isoformat(),
        }},
        upsert=True,
    )
    background_tasks.add_task(send_verification_email, request.email.lower(), code)
    return {"message": "Verification code queued", "email": request.email.lower(), "expires_at": expires_at}

@api_router.post("/auth/verify-email")
async def verify_email_code(request: VerifyEmailRequest):
    record = await db.verification_codes.find_one({"email": request.email.lower(), "used": False})
    if not record:
        raise HTTPException(status_code=400, detail="No active verification code found")
    if datetime.fromisoformat(record["expires_at"]) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code expired")
    if record.get("code_hash") != hash_password(request.code):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    await db.verification_codes.update_one({"_id": record["_id"]}, {"$set": {"used": True, "verified_at": datetime.utcnow().isoformat()}})
    await db.users.update_many({"email": request.email.lower()}, {"$set": {"email_verified": True, "auth_methods.email_verified": True}})
    return {"message": "Email verified", "email_verified": True}

@api_router.get("/auth/security-options")
async def get_security_options(user: dict = Depends(get_current_user)):
    return {
        "password_enabled": True,
        "email_verification_enabled": True,
        "email_verified": user.get("email_verified", False),
        "passkeys_ready": True,
        "google_sign_in_ready": True,
        "note": "Schema and UI are ready for passkeys and Google auth; provider setup can be connected later.",
    }

@api_router.put("/profile")
async def update_profile(profile_update: ProfileUpdate, user: dict = Depends(get_current_user)):
    profile = user.get("profile") or {"display_name": user.get("username", "Coder"), "bio": "", "avatar_color": "#00FF88", "display_badges": user.get("badges", [])[:3]}
    if profile_update.display_name is not None:
        profile["display_name"] = profile_update.display_name[:32]
    if profile_update.bio is not None:
        profile["bio"] = profile_update.bio[:160]
    if profile_update.avatar_color is not None:
        profile["avatar_color"] = profile_update.avatar_color[:16]
    await db.users.update_one({"id": user["id"]}, {"$set": {"profile": profile}})
    return {"message": "Profile updated", "profile": profile}

@api_router.put("/profile/display-badges")
async def update_display_badges(update: DisplayBadgesUpdate, user: dict = Depends(get_current_user)):
    if len(update.badge_ids) > 3:
        raise HTTPException(status_code=400, detail="Choose up to 3 badges")
    earned = set(user.get("badges", []))
    if any(badge_id not in earned for badge_id in update.badge_ids):
        raise HTTPException(status_code=400, detail="You can only display earned badges")
    profile = user.get("profile") or {"display_name": user.get("username", "Coder"), "bio": "", "avatar_color": "#00FF88"}
    profile["display_badges"] = update.badge_ids
    await db.users.update_one({"id": user["id"]}, {"$set": {"profile": profile}})
    return {"message": "Display badges updated", "display_badges": update.badge_ids}

@api_router.get("/review/wrong-answers")
async def get_wrong_answers(user: dict = Depends(get_current_user)):
    items = await db.wrong_answers.find({"user_id": user["id"], "reviewed": False}).sort("created_at", -1).limit(50).to_list(50)
    for item in items:
        item.pop("_id", None)
    return items

@api_router.post("/review/wrong-answers/{wrong_answer_id}/reviewed")
async def mark_wrong_answer_reviewed(wrong_answer_id: str, user: dict = Depends(get_current_user)):
    result = await db.wrong_answers.update_one({"id": wrong_answer_id, "user_id": user["id"]}, {"$set": {"reviewed": True, "reviewed_at": datetime.utcnow().isoformat()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Wrong answer not found")
    return {"message": "Marked reviewed"}

@api_router.get("/continue-learning")
async def get_continue_learning(user: dict = Depends(get_current_user)):
    studied = user.get("languages_studied", []) or ["python"]
    for language_id in studied:
        lessons = LESSONS_CACHE.get(language_id, [])
        progress = await db.progress.find({"user_id": user["id"], "language": language_id, "completed": True}).to_list(1000)
        completed_ids = {p["lesson_id"] for p in progress}
        for lesson in lessons:
            if lesson["id"] not in completed_ids:
                return {"has_continue": True, "language_id": language_id, "lesson_id": lesson["id"], "title": lesson["title"], "description": lesson["description"], "completed_lessons": len(completed_ids), "total_lessons": len(lessons)}
    first = LESSONS_CACHE["python"][0]
    return {"has_continue": True, "language_id": "python", "lesson_id": first["id"], "title": first["title"], "description": first["description"], "completed_lessons": 0, "total_lessons": len(LESSONS_CACHE["python"])}


@api_router.get("/vip/info")
async def get_vip_info():
    return VIP_INFO

@api_router.get("/vip/status")
async def get_vip_status(user: dict = Depends(get_current_user)):
    return {
        "is_vip": is_vip_active(user),
        "vip_until": user.get("vip_until"),
        "vip_months": user.get("vip_months", 0),
        "perks": get_vip_perks(user),
    }

@api_router.post("/vip/subscribe")
async def subscribe_vip(purchase: VIPPurchase, user: dict = Depends(get_current_user)):
    """Subscribe to VIP (simulated payment)"""
    # In production, integrate with Stripe/PayPal
    now = datetime.utcnow()
    
    if is_vip_active(user):
        current_expiry = datetime.fromisoformat(user["vip_until"])
        new_expiry = current_expiry + timedelta(days=30)
    else:
        new_expiry = now + timedelta(days=30)
    
    vip_months = user.get("vip_months", 0) + 1
    badges = user.get("badges", [])
    
    # Award VIP badge
    if "vip_member" not in badges:
        badges.append("vip_member")
    
    # Award veteran badge after 3 months
    if vip_months >= 3 and "vip_veteran" not in badges:
        badges.append("vip_veteran")
    
    perks = get_vip_perks({"vip_until": new_expiry.isoformat()})
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "vip_until": new_expiry.isoformat(),
            "vip_months": vip_months,
            "max_hearts": perks["max_hearts"],
            "hearts": perks["max_hearts"],
            "badges": badges,
        }}
    )
    
    return {
        "success": True,
        "message": "VIP subscription activated!",
        "vip_until": new_expiry.isoformat(),
        "perks": perks,
    }

# ============== SETTINGS ROUTES ==============

@api_router.put("/settings")
async def update_settings(settings_update: SettingsUpdate, user: dict = Depends(get_current_user)):
    await db.users.update_one({"id": user["id"]}, {"$set": {"settings": settings_update.settings}})
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
        lesson_copy = {
            "id": lesson["id"],
            "title": lesson["title"],
            "description": lesson["description"],
            "xp": lesson["xp"],
            "unit": lesson["unit"],
            "unit_name": lesson["unit_name"],
            "exercise_count": len(lesson.get("exercises", [])),
            "completed": lesson["id"] in completed_ids,
            "has_practice": bool(lesson.get("practice_content")),
        }
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

@api_router.get("/languages/{language_id}/lessons/{lesson_id}/practice")
async def get_practice_content(language_id: str, lesson_id: str):
    """Get practice mode content for a lesson"""
    if language_id not in LESSONS_CACHE:
        raise HTTPException(status_code=404, detail="Language not found")
    
    for lesson in LESSONS_CACHE[language_id]:
        if lesson["id"] == lesson_id:
            return {
                "lesson_id": lesson_id,
                "title": lesson["title"],
                "practice_content": lesson.get("practice_content", {}),
                "exercises": lesson.get("exercises", []),
            }
    
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
    
    # PRACTICE MODE - No hearts lost, no XP gained
    if answer.practice_mode:
        practice_sessions = user.get("practice_sessions", 0) + 1
        badges = user.get("badges", [])
        
        if practice_sessions >= 100 and "practice_master" not in badges:
            badges.append("practice_master")
        
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"practice_sessions": practice_sessions, "badges": badges}}
        )
        
        # Calculate score for feedback only
        exercises = lesson.get("exercises", [])
        correct = 0
        for i, ex in enumerate(exercises):
            if i < len(answer.answers):
                user_answer = answer.answers[i]
                is_correct, message, expected = check_exercise_answer(ex, user_answer, answer.language)
                if is_correct:
                    correct += 1
        
        return {
            "practice_mode": True,
            "score": int((correct / len(exercises)) * 100) if exercises else 100,
            "correct": correct,
            "total": len(exercises),
            "xp_earned": 0,
            "hearts_lost": 0,
            "message": "Practice complete! No hearts lost, keep learning!",
            "practice_sessions": practice_sessions,
        }
    
    # NORMAL MODE
    exercises = lesson.get("exercises", [])
    correct = 0
    for i, ex in enumerate(exercises):
        if i < len(answer.answers):
            user_answer = answer.answers[i]
            is_correct, message, expected = check_exercise_answer(ex, user_answer, answer.language)
            if is_correct:
                correct += 1
            else:
                await save_wrong_answer(user["id"], answer.language, answer.lesson_id, i, ex, user_answer, expected, explain_error_simple(message))
    
    total = len(exercises)
    score = int((correct / total) * 100) if total > 0 else 100
    base_xp = lesson.get("xp", 15)
    
    # VIP XP multiplier
    perks = get_vip_perks(user)
    xp_multiplier = perks["xp_multiplier"]
    
    # Combo multiplier
    combo_multiplier = user.get("combo_multiplier", 1.0)
    if score == 100:
        combo_multiplier = min(combo_multiplier + 0.5, 5.0)
    elif score < 70:
        combo_multiplier = 1.0
    
    xp_earned = int(base_xp * (score / 100) * combo_multiplier * xp_multiplier)
    
    # Speed bonus
    if answer.time_taken and answer.time_taken < 120 and score >= 70:
        xp_earned = int(xp_earned * 1.25)
    
    # Hearts (VIP has more)
    hearts_lost = max(0, (total - correct) // 2)
    new_hearts = max(0, user.get("hearts", 5) - hearts_lost)
    
    # Check existing
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
            "hearts_lost": hearts_lost,
            "gems": new_gems,
            "gems_earned": gems_earned,
            "combo_multiplier": combo_multiplier,
            "vip_bonus": xp_multiplier > 1.0,
            "new_badges": new_badges,
            "correct": correct,
            "total": total,
            "daily_xp": daily_xp,
            "daily_goal": daily_goal,
            "daily_goal_met": daily_goal_met,
        }
    else:
        if score > existing.get("score", 0):
            await db.progress.update_one({"_id": existing["_id"]}, {"$set": {"score": score}})
        
        # Update hearts even on repeat
        await db.users.update_one({"id": user["id"]}, {"$set": {"hearts": new_hearts, "combo_multiplier": combo_multiplier}})
        
        return {
            "score": score,
            "xp_earned": 0,
            "new_xp": user.get("xp", 0),
            "new_level": user.get("level", 1),
            "hearts": new_hearts,
            "hearts_lost": hearts_lost,
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
                progress = await db.progress.find({"user_id": user["id"], "language": language_id}).to_list(1000)
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

# ============== HINT ROUTES ==============

@api_router.post("/hint/use")
async def use_hint(user: dict = Depends(get_current_user)):
    """Use a hint (limited per day, VIP gets more)"""
    perks = get_vip_perks(user)
    hints_used = user.get("hints_used_today", 0)
    max_hints = perks["hints_per_lesson"]
    
    if hints_used >= max_hints:
        return {"success": False, "message": f"No hints left today (max {max_hints})", "hints_remaining": 0}
    
    await db.users.update_one({"id": user["id"]}, {"$set": {"hints_used_today": hints_used + 1}})
    
    return {"success": True, "hints_remaining": max_hints - hints_used - 1, "hints_max": max_hints}

# ============== DAILY CHALLENGE ROUTES ==============


@api_router.post("/code/check")
async def check_code_challenge(check: CodeCheckRequest, user: dict = Depends(get_current_user)):
    exercise = check.exercise or {}
    if check.lesson_id and check.exercise_index is not None:
        lesson = next((l for l in LESSONS_CACHE.get(check.language, []) if l["id"] == check.lesson_id), None)
        if lesson and 0 <= check.exercise_index < len(lesson.get("exercises", [])):
            exercise = lesson["exercises"][check.exercise_index]
    if not exercise:
        raise HTTPException(status_code=400, detail="Exercise not found")
    correct, message, expected = check_exercise_answer(exercise, check.answer, check.language)
    simple_explanation = message if correct else explain_error_simple(message)
    if not correct and check.save_wrong:
        await save_wrong_answer(user["id"], check.language, check.lesson_id, check.exercise_index, exercise, check.answer, expected, simple_explanation)
    return {
        "correct": correct,
        "message": message,
        "simple_explanation": simple_explanation,
        "hint": exercise.get("hint"),
        "show_answer_available": not correct,
        "expected_answer": expected if not correct else None,
    }

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
    
    exercises = challenge["exercises"]
    correct = 0
    for i, ex in enumerate(exercises):
        if i < len(answer.answers):
            user_answer = answer.answers[i]
            if ex["type"] == "multiple_choice" and user_answer.get("selected") == ex.get("correct"):
                correct += 1
            elif ex["type"] == "code":
                is_correct, _ = validate_code(user_answer.get("code", ""), ex.get("solution", ""), "python")
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
        perks = get_vip_perks(user)
        xp_earned = int(challenge["xp_reward"] * perks["xp_multiplier"])
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
async def get_leaderboard(user: dict = Depends(get_current_user)):
    allowed_ids = set(user.get("friends", [])) | {user["id"]}
    users = await db.users.find({"id": {"$in": list(allowed_ids)}}, {"username": 1, "xp": 1, "level": 1, "streak": 1, "badges": 1, "vip_until": 1, "profile": 1}).sort("xp", -1).limit(50).to_list(50)
    return [
        {
            "username": u["username"],
            "display_name": (u.get("profile") or {}).get("display_name", u["username"]),
            "xp": u.get("xp", 0),
            "level": u.get("level", 1),
            "streak": u.get("streak", 0),
            "badges_count": len(u.get("badges", [])),
            "display_badges": (u.get("profile") or {}).get("display_badges", u.get("badges", [])[:3]),
            "is_vip": is_vip_active(u),
        }
        for u in users
    ]

@api_router.get("/friends/suggest")
async def suggest_friends(q: str = Query("", min_length=0), user: dict = Depends(get_current_user)):
    query = (q or "").strip()
    if len(query) < 2:
        return []
    excluded_ids = set(user.get("friends", [])) | {user["id"]}
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    users = await db.users.find({"username": pattern, "id": {"$nin": list(excluded_ids)}}, {"username": 1, "xp": 1, "level": 1, "profile": 1}).limit(8).to_list(8)
    return [
        {
            "username": u["username"],
            "display_name": (u.get("profile") or {}).get("display_name", u["username"]),
            "level": u.get("level", 1),
            "xp": u.get("xp", 0),
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
    if len(updated_user.get("friends", [])) >= 5 and "social_butterfly" not in updated_user.get("badges", []):
        await db.users.update_one({"id": user["id"]}, {"$addToSet": {"badges": "social_butterfly"}})
    
    return {"message": f"Added {request.friend_username} as friend"}

@api_router.get("/friends")
async def get_friends(user: dict = Depends(get_current_user)):
    friend_ids = user.get("friends", [])
    if not friend_ids:
        return []
    
    friends = await db.users.find({"id": {"$in": friend_ids}}).to_list(100)
    return [{"username": f["username"], "xp": f.get("xp", 0), "level": f.get("level", 1), "streak": f.get("streak", 0)} for f in friends]

@api_router.get("/badges")
async def get_badges():
    return BADGES

# ============== SHOP ROUTES ==============

@api_router.post("/shop/buy-hearts")
async def buy_hearts(user: dict = Depends(get_current_user)):
    gem_cost = 10
    if user.get("gems", 0) < gem_cost:
        raise HTTPException(status_code=400, detail="Not enough gems")
    
    perks = get_vip_perks(user)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"hearts": perks["max_hearts"], "gems": user.get("gems", 0) - gem_cost}}
    )
    return {"message": "Hearts refilled!", "hearts": perks["max_hearts"]}

@api_router.post("/shop/buy-streak-freeze")
async def buy_streak_freeze(user: dict = Depends(get_current_user)):
    gem_cost = 20
    if user.get("gems", 0) < gem_cost:
        raise HTTPException(status_code=400, detail="Not enough gems")
    
    streak_freezes = user.get("streak_freezes", 0) + 1
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"streak_freezes": streak_freezes, "gems": user.get("gems", 0) - gem_cost}}
    )
    return {"message": "Streak freeze purchased!", "streak_freezes": streak_freezes}

# ============== CODING GAMES ==============

class GameComplete(BaseModel):
    game_type: str  # bug_hunter, code_puzzle, speed_code
    score: int
    total: int
    time_taken: Optional[int] = None
    language: str = "python"

BUG_HUNTER_CHALLENGES = {
    "python": [
        {"id": "py_bug_1", "code": "prnt('Hello World')", "bug_line": 1, "question": "Find the bug in this Python code:", "options": ["prnt should be print", "Missing semicolon", "Wrong quotes", "Missing import"], "correct": 0, "fixed_code": "print('Hello World')", "explanation": "Python's print function is spelled 'print', not 'prnt'. Typos are the most common bug!", "concept": "Built-in functions"},
        {"id": "py_bug_2", "code": "for i in range(10)\n    print(i)", "bug_line": 1, "question": "This loop won't run. Why?", "options": ["Missing colon after range(10)", "range should be Range", "print needs format", "i is not defined"], "correct": 0, "fixed_code": "for i in range(10):\n    print(i)", "explanation": "Python requires a colon (:) at the end of for, if, while, def, and class statements.", "concept": "Syntax - colons"},
        {"id": "py_bug_3", "code": "x = 10\nif x = 10:\n    print('ten')", "bug_line": 2, "question": "Why does this if-statement cause an error?", "options": ["= should be == for comparison", "x is not a string", "Missing parentheses", "print is wrong"], "correct": 0, "fixed_code": "x = 10\nif x == 10:\n    print('ten')", "explanation": "= is assignment, == is comparison. This is one of the most common Python mistakes!", "concept": "Operators"},
        {"id": "py_bug_4", "code": "my_list = [1, 2, 3]\nprint(my_list[3])", "bug_line": 2, "question": "This code crashes. Why?", "options": ["Index 3 is out of range (0-2)", "Lists start at 1", "Need to use get()", "Wrong bracket type"], "correct": 0, "fixed_code": "my_list = [1, 2, 3]\nprint(my_list[2])", "explanation": "Lists are 0-indexed! A list of 3 items has indices 0, 1, 2. Index 3 doesn't exist.", "concept": "List indexing"},
        {"id": "py_bug_5", "code": "def add(a, b):\n    result = a + b\n\nprint(add(3, 4))", "bug_line": 2, "question": "add(3, 4) returns None. Why?", "options": ["Missing return statement", "result is local", "Wrong parameter names", "Need to use sum()"], "correct": 0, "fixed_code": "def add(a, b):\n    return a + b\n\nprint(add(3, 4))", "explanation": "Functions return None by default. You must use 'return' to send a value back!", "concept": "Functions - return"},
        {"id": "py_bug_6", "code": "name = 'Alice\nprint(name)", "bug_line": 1, "question": "This string causes a SyntaxError:", "options": ["Missing closing quote", "Should use double quotes", "name is reserved", "print is wrong"], "correct": 0, "fixed_code": "name = 'Alice'\nprint(name)", "explanation": "Strings must have matching opening and closing quotes. Always check your quotes!", "concept": "Strings"},
        {"id": "py_bug_7", "code": "numbers = [1, 2, 3]\nfor n in numbers:\n    numbers.append(n * 2)", "bug_line": 3, "question": "This creates an infinite loop. Why?", "options": ["Modifying list while iterating", "append is wrong method", "n * 2 is invalid", "for loop syntax wrong"], "correct": 0, "fixed_code": "numbers = [1, 2, 3]\nnew_nums = [n * 2 for n in numbers]", "explanation": "Never modify a list while iterating over it! Use a list comprehension or iterate over a copy.", "concept": "List iteration"},
        {"id": "py_bug_8", "code": "age = input('Age: ')\nif age > 18:\n    print('Adult')", "bug_line": 2, "question": "Comparing age > 18 fails. Why?", "options": ["input() returns a string, not int", "Need >= not >", "age is undefined", "print syntax wrong"], "correct": 0, "fixed_code": "age = int(input('Age: '))\nif age > 18:\n    print('Adult')", "explanation": "input() always returns a string. Use int() to convert it to a number for comparison.", "concept": "Type conversion"},
    ],
    "javascript": [
        {"id": "js_bug_1", "code": "console.log('Hello World'", "bug_line": 1, "question": "Find the syntax error:", "options": ["Missing closing parenthesis", "Wrong quotes", "Should be Console.log", "Missing semicolon"], "correct": 0, "fixed_code": "console.log('Hello World')", "explanation": "Every opening parenthesis needs a closing one. Count your brackets!", "concept": "Syntax basics"},
        {"id": "js_bug_2", "code": "const x = 5;\nx = 10;\nconsole.log(x);", "bug_line": 2, "question": "Why does reassigning x fail?", "options": ["const cannot be reassigned", "x is not declared", "Need to use var", "Wrong syntax"], "correct": 0, "fixed_code": "let x = 5;\nx = 10;\nconsole.log(x);", "explanation": "const declares a constant that cannot be changed. Use 'let' for values that change.", "concept": "Variable declarations"},
        {"id": "js_bug_3", "code": "if (x === 5) {\n    console.log('five')\n} else {\n    console.log('not five)\n}", "bug_line": 4, "question": "This code has a string error:", "options": ["Missing closing quote on 'not five'", "Wrong comparison operator", "Missing semicolon", "else syntax wrong"], "correct": 0, "fixed_code": "if (x === 5) {\n    console.log('five')\n} else {\n    console.log('not five')\n}", "explanation": "Always match your quotes! Missing a closing quote causes a SyntaxError.", "concept": "String syntax"},
        {"id": "js_bug_4", "code": "const arr = [1, 2, 3];\nconsole.log(arr.length());", "bug_line": 2, "question": "arr.length() throws an error:", "options": ["length is a property, not a method", "Should use size()", "arr is const", "Wrong brackets"], "correct": 0, "fixed_code": "const arr = [1, 2, 3];\nconsole.log(arr.length);", "explanation": "length is a property (no parentheses), not a method. arr.length gives 3.", "concept": "Array properties"},
        {"id": "js_bug_5", "code": "function greet(name) {\n    return 'Hello, ' + Name;\n}", "bug_line": 2, "question": "greet('Alice') returns an error:", "options": ["Name should be name (case sensitive)", "Wrong string concat", "Missing semicolon", "Function syntax wrong"], "correct": 0, "fixed_code": "function greet(name) {\n    return 'Hello, ' + name;\n}", "explanation": "JavaScript is case-sensitive! 'name' and 'Name' are different variables.", "concept": "Case sensitivity"},
        {"id": "js_bug_6", "code": "for (let i = 0; i <= 5; i++) {\n    setTimeout(() => console.log(i), 1000);\n}", "bug_line": 2, "question": "What's the issue with this timer loop?", "options": ["All timeouts fire after same 1s delay", "i is not accessible in arrow function", "setTimeout syntax wrong", "No issue exists"], "correct": 0, "fixed_code": "for (let i = 0; i <= 5; i++) {\n    setTimeout(() => console.log(i), i * 1000);\n}", "explanation": "All timeouts are set with the same 1000ms delay. Use i*1000 for sequential timing.", "concept": "Async & closures"},
    ],
    "java": [
        {"id": "java_bug_1", "code": "String name = \"Alice\";\nif (name == \"Alice\") {\n    System.out.println(\"Found!\");\n}", "bug_line": 2, "question": "Why might this comparison fail?", "options": ["Use .equals() for string comparison", "== works fine for strings", "name is null", "Wrong quotes"], "correct": 0, "fixed_code": "String name = \"Alice\";\nif (name.equals(\"Alice\")) {\n    System.out.println(\"Found!\");\n}", "explanation": "In Java, == compares references, not values. Always use .equals() for string comparison!", "concept": "String comparison"},
        {"id": "java_bug_2", "code": "int[] nums = {1, 2, 3};\nSystem.out.println(nums.length());", "bug_line": 2, "question": "Why does .length() fail on arrays?", "options": ["Arrays use .length (no parentheses)", "Should use size()", "Wrong array syntax", "Missing import"], "correct": 0, "fixed_code": "int[] nums = {1, 2, 3};\nSystem.out.println(nums.length);", "explanation": "In Java, arrays use .length (property), while ArrayLists use .size() (method).", "concept": "Array vs ArrayList"},
    ],
    "shell": [
        {"id": "sh_bug_1", "code": "name = 'Alice'\necho $name", "bug_line": 1, "question": "This variable assignment fails. Why?", "options": ["No spaces around = in bash", "name is reserved", "Missing quotes", "echo is wrong"], "correct": 0, "fixed_code": "name='Alice'\necho $name", "explanation": "In bash, variable assignment must have NO spaces around =. 'name=value' not 'name = value'!", "concept": "Variable assignment"},
        {"id": "sh_bug_2", "code": "if [ $x == 5 ]; then\n    echo 'five'\nfi", "bug_line": 1, "question": "What if x is empty/unset?", "options": ["Unquoted $x causes error when empty", "== is wrong operator", "fi is misspelled", "then is not needed"], "correct": 0, "fixed_code": "if [ \"$x\" -eq 5 ]; then\n    echo 'five'\nfi", "explanation": "Always quote variables in [ ]. Unquoted empty vars cause 'unary operator expected' errors!", "concept": "Quoting variables"},
        {"id": "sh_bug_3", "code": "for i in 1 2 3 4 5\ndo\n    echo i\ndone", "bug_line": 3, "question": "This prints 'i' five times. Why?", "options": ["Missing $ before i", "echo is wrong", "do is misplaced", "done is wrong"], "correct": 0, "fixed_code": "for i in 1 2 3 4 5\ndo\n    echo $i\ndone", "explanation": "You need $ to access variable values. 'i' is literal text, '$i' is the variable.", "concept": "Variable access"},
        {"id": "sh_bug_4", "code": "#!/bin/bash\ncount=0\ncat file.txt | while read line; do\n    count=$((count + 1))\ndone\necho $count", "bug_line": 3, "question": "count is always 0 after the loop. Why?", "options": ["Pipe creates subshell, changes lost", "cat is wrong", "read is wrong", "count type issue"], "correct": 0, "fixed_code": "#!/bin/bash\ncount=0\nwhile read line; do\n    count=$((count + 1))\ndone < file.txt\necho $count", "explanation": "Pipes create subshells! Variables modified inside don't affect the parent. Use redirection instead.", "concept": "Subshells"},
        {"id": "sh_bug_5", "code": "files=`ls *.txt`\nfor f in $files; do\n    echo $f\ndone", "bug_line": 1, "question": "This breaks with filenames containing spaces:", "options": ["Don't parse ls output, use globs", "Backticks are wrong", "for loop syntax", "echo is wrong"], "correct": 0, "fixed_code": "for f in *.txt; do\n    echo \"$f\"\ndone", "explanation": "Never parse ls! Use globs directly. Also quote variables to handle spaces in filenames.", "concept": "Glob patterns"},
    ],
    "haskell": [
        {"id": "hs_bug_1", "code": "main = putStrLn 'Hello World'", "bug_line": 1, "question": "This gives a type error. Why?", "options": ["Single quotes are for Char, use double quotes", "putStrLn is wrong", "main is wrong", "Missing do"], "correct": 0, "fixed_code": "main = putStrLn \"Hello World\"", "explanation": "In Haskell, 'a' is a Char, \"abc\" is a String. putStrLn needs a String!", "concept": "Strings vs Chars"},
        {"id": "hs_bug_2", "code": "double x = x * 2\nmain = putStrLn (double 5)", "bug_line": 2, "question": "putStrLn fails on the result. Why?", "options": ["double returns Int, putStrLn needs String", "double is wrong", "main syntax wrong", "Missing import"], "correct": 0, "fixed_code": "double x = x * 2\nmain = print (double 5)", "explanation": "putStrLn only accepts String. Use 'print' for other types, or 'show' to convert.", "concept": "Type system"},
        {"id": "hs_bug_3", "code": "factorial 0 = 1\nfactorial n = n * factorial n - 1", "bug_line": 2, "question": "This causes infinite recursion:", "options": ["Need parentheses: factorial (n-1)", "Base case is wrong", "* is wrong", "Missing type signature"], "correct": 0, "fixed_code": "factorial 0 = 1\nfactorial n = n * factorial (n - 1)", "explanation": "Without parentheses, Haskell reads it as (n * factorial n) - 1, causing infinite recursion!", "concept": "Function application"},
        {"id": "hs_bug_4", "code": "head []", "bug_line": 1, "question": "What happens when you call head on an empty list?", "options": ["Runtime exception - empty list", "Returns Nothing", "Returns 0", "Compile error"], "correct": 0, "fixed_code": "-- Use pattern matching or safe functions\ncase xs of\n  [] -> Nothing\n  (x:_) -> Just x", "explanation": "head crashes on empty lists! Use pattern matching or safe alternatives.", "concept": "Partial functions"},
        {"id": "hs_bug_5", "code": "add x y = x + y\nmain = do\n  let result = add 5\n  print result", "bug_line": 3, "question": "This doesn't give an error but isn't a number:", "options": ["add 5 returns a partially applied function", "let is wrong", "do is unnecessary", "print can't handle it"], "correct": 0, "fixed_code": "add x y = x + y\nmain = do\n  let result = add 5 3\n  print result", "explanation": "In Haskell, functions are curried. 'add 5' returns a function waiting for the second argument!", "concept": "Currying"},
    ],
    "elixir": [
        {"id": "ex_bug_1", "code": "name = \"Alice\"\nname = \"Bob\"\nIO.puts(name)", "bug_line": 2, "question": "Does this work? What prints?", "options": ["Prints 'Bob' — rebinding, not mutation", "Error — can't reassign", "Prints 'Alice'", "Prints both"], "correct": 0, "fixed_code": "name = \"Alice\"\nname = \"Bob\"  # rebinding, not mutating!\nIO.puts(name)  # prints Bob", "explanation": "Elixir allows rebinding (new binding), but the original value is unchanged. This is NOT mutation!", "concept": "Immutability vs rebinding"},
        {"id": "ex_bug_2", "code": "list = [1, 2, 3]\nList.push(list, 4)", "bug_line": 2, "question": "List.push doesn't exist. How to add?", "options": ["Use list ++ [4] or [4 | list]", "Use List.add", "Use List.append", "Use list.push(4)"], "correct": 0, "fixed_code": "list = [1, 2, 3]\nnew_list = list ++ [4]", "explanation": "Elixir lists don't have push. Use ++ to concatenate or [head | tail] to prepend.", "concept": "List operations"},
        {"id": "ex_bug_3", "code": "defmodule Math do\n  def add(a, b) do\n    a + b\n  end\nend\nresult = Math.add(1, 2, 3)", "bug_line": 6, "question": "This call fails. Why?", "options": ["add/2 expects 2 args, got 3", "defmodule is wrong", "def syntax wrong", "Math is reserved"], "correct": 0, "fixed_code": "defmodule Math do\n  def add(a, b) do\n    a + b\n  end\nend\nresult = Math.add(1, 2)", "explanation": "Elixir functions have fixed arity. add/2 means it takes exactly 2 arguments.", "concept": "Function arity"},
        {"id": "ex_bug_4", "code": "map = %{name: \"Alice\"}\nmap.age", "bug_line": 2, "question": "Accessing a missing key with dot notation:", "options": ["Raises KeyError for missing key", "Returns nil", "Returns 0", "Returns empty"], "correct": 0, "fixed_code": "map = %{name: \"Alice\"}\nMap.get(map, :age, \"unknown\")", "explanation": "Dot notation raises KeyError for missing keys. Use Map.get/3 with a default instead!", "concept": "Map access"},
        {"id": "ex_bug_5", "code": "Enum.map([1,2,3], fn x -> x * 2)", "bug_line": 1, "question": "This anonymous function is incomplete:", "options": ["Missing 'end' keyword", "fn is wrong", "Enum is wrong", "-> is wrong"], "correct": 0, "fixed_code": "Enum.map([1,2,3], fn x -> x * 2 end)", "explanation": "Anonymous functions need 'end'. Or use capture: &(&1 * 2)", "concept": "Anonymous functions"},
    ],
    "zig": [
        {"id": "zig_bug_1", "code": "const x = 5;\nx = 10;", "bug_line": 2, "question": "Reassigning x fails. Why?", "options": ["const is immutable, use var", "Missing type annotation", "Wrong syntax", "5 is wrong type"], "correct": 0, "fixed_code": "var x: i32 = 5;\nx = 10;", "explanation": "const creates immutable bindings. Use 'var' if you need to change the value.", "concept": "const vs var"},
        {"id": "zig_bug_2", "code": "var x: i32 = 5;\nvar y: u32 = x;", "bug_line": 2, "question": "Assigning i32 to u32 fails:", "options": ["Can't implicitly convert signed to unsigned", "Types are the same", "var is wrong", "Missing semicolon"], "correct": 0, "fixed_code": "var x: i32 = 5;\nvar y: u32 = @intCast(x);", "explanation": "Zig requires explicit casts between numeric types. Use @intCast for safe conversion.", "concept": "Type safety"},
        {"id": "zig_bug_3", "code": "const arr = [3]i32{1, 2, 3};\nstd.debug.print(\"{}\", .{arr[3]});", "bug_line": 2, "question": "This causes a panic. Why?", "options": ["Index 3 out of bounds (0-2)", "Wrong print format", "arr is const", "Missing semicolon"], "correct": 0, "fixed_code": "const arr = [3]i32{1, 2, 3};\nstd.debug.print(\"{}\", .{arr[2]});", "explanation": "Array of 3 elements has indices 0, 1, 2. Index 3 is out of bounds!", "concept": "Array bounds"},
        {"id": "zig_bug_4", "code": "fn add(a: i32, b: i32) i32 {\n    a + b\n}", "bug_line": 2, "question": "This function doesn't compile:", "options": ["Missing return keyword", "Wrong types", "Missing semicolon", "fn is wrong"], "correct": 0, "fixed_code": "fn add(a: i32, b: i32) i32 {\n    return a + b;\n}", "explanation": "Zig requires explicit return statements (unlike Rust or Haskell).", "concept": "Return statements"},
        {"id": "zig_bug_5", "code": "var maybe: ?i32 = null;\nconst val = maybe + 1;", "bug_line": 2, "question": "Can't add to an optional. How to fix?", "options": ["Unwrap with orelse or if", "Cast to i32", "Remove ?", "Use var"], "correct": 0, "fixed_code": "var maybe: ?i32 = null;\nconst val = (maybe orelse 0) + 1;", "explanation": "Optional types (?T) must be unwrapped before use. 'orelse' provides a default.", "concept": "Optional types"},
    ],
    "lua": [
        {"id": "lua_bug_1", "code": "local arr = {10, 20, 30}\nprint(arr[0])", "bug_line": 2, "question": "This prints nil. Why?", "options": ["Lua arrays start at index 1, not 0", "arr is wrong type", "print is wrong", "Missing local"], "correct": 0, "fixed_code": "local arr = {10, 20, 30}\nprint(arr[1])", "explanation": "Lua arrays are 1-indexed! The first element is at index 1, not 0.", "concept": "1-based indexing"},
        {"id": "lua_bug_2", "code": "x = 5\nif x = 5 then\n    print('five')\nend", "bug_line": 2, "question": "This code has a syntax error:", "options": ["Use == for comparison, = is assignment", "if is wrong", "then not needed", "end not needed"], "correct": 0, "fixed_code": "x = 5\nif x == 5 then\n    print('five')\nend", "explanation": "= is assignment, == is comparison. Classic bug in many languages!", "concept": "Comparison operators"},
        {"id": "lua_bug_3", "code": "function greet(name)\n    return 'Hello ' + name\nend", "bug_line": 2, "question": "String concatenation fails:", "options": ["Use .. not + for string concat", "+ only for numbers", "return is wrong", "function syntax wrong"], "correct": 0, "fixed_code": "function greet(name)\n    return 'Hello ' .. name\nend", "explanation": "In Lua, + is only for numbers. Use .. for string concatenation!", "concept": "String concatenation"},
        {"id": "lua_bug_4", "code": "t = {}\nt.insert('hello')", "bug_line": 2, "question": "This method call is wrong:", "options": ["Use table.insert(t, 'hello')", "Use t:insert", "Use t.add", "Use t.push"], "correct": 0, "fixed_code": "t = {}\ntable.insert(t, 'hello')", "explanation": "table.insert is a library function, not a method. Pass the table as first argument.", "concept": "Table library"},
        {"id": "lua_bug_5", "code": "function Counter()\n    count = 0\n    return count\nend", "bug_line": 2, "question": "count is a global variable! How to fix?", "options": ["Add 'local' keyword", "Use self.count", "Use var count", "Use let count"], "correct": 0, "fixed_code": "function Counter()\n    local count = 0\n    return count\nend", "explanation": "Without 'local', variables are global in Lua. Always use 'local' for local scope!", "concept": "Local variables"},
    ],
}

CODE_PUZZLE_CHALLENGES = {
    "python": [
        {"id": "py_puz_1", "title": "Hello World Function", "description": "Arrange to create a function that prints Hello World", "lines": ["def greet():", "    print('Hello World')", "greet()"], "correct_order": [0, 1, 2], "explanation": "First define the function, then the body, then call it.", "concept": "Function basics"},
        {"id": "py_puz_2", "title": "Sum Calculator", "description": "Build a program that sums two numbers", "lines": ["result = a + b", "def add(a, b):", "print(add(5, 3))", "    return result"], "correct_order": [1, 0, 3, 2], "explanation": "Define function → calculate → return → call and print.", "concept": "Functions with return"},
        {"id": "py_puz_3", "title": "List Filter", "description": "Filter even numbers from a list", "lines": ["evens = []", "numbers = [1, 2, 3, 4, 5, 6]", "print(evens)", "    evens.append(n)", "for n in numbers:", "    if n % 2 == 0:"], "correct_order": [1, 0, 4, 5, 3, 2], "explanation": "Create list → init result → loop → check condition → append → print.", "concept": "Loops and filtering"},
        {"id": "py_puz_4", "title": "Class Creation", "description": "Create a Dog class with a bark method", "lines": ["    def bark(self):", "class Dog:", "my_dog = Dog('Rex')", "my_dog.bark()", "        self.name = name", "    def __init__(self, name):", "        print(f'{self.name} says Woof!')"], "correct_order": [1, 5, 4, 0, 6, 2, 3], "explanation": "class → __init__ → set attribute → method → method body → create → use.", "concept": "OOP basics"},
        {"id": "py_puz_5", "title": "Try-Except Block", "description": "Handle division by zero error", "lines": ["    print('Cannot divide by zero!')", "try:", "    result = 10 / 0", "except ZeroDivisionError:", "    print(result)"], "correct_order": [1, 2, 4, 3, 0], "explanation": "try block first, then the risky code, then except catches the specific error.", "concept": "Error handling"},
    ],
    "javascript": [
        {"id": "js_puz_1", "title": "Async Fetch", "description": "Arrange an async function to fetch data", "lines": ["const data = await response.json();", "async function getData() {", "console.log(data);", "const response = await fetch('/api');", "}"], "correct_order": [1, 3, 0, 2, 4], "explanation": "async function → fetch → parse JSON → use data → close.", "concept": "Async/Await"},
        {"id": "js_puz_2", "title": "Array Map", "description": "Double all numbers in an array", "lines": ["const doubled = numbers.map(n => n * 2);", "const numbers = [1, 2, 3, 4, 5];", "console.log(doubled);"], "correct_order": [1, 0, 2], "explanation": "Create array → transform with map → display result.", "concept": "Array methods"},
        {"id": "js_puz_3", "title": "Event Listener", "description": "Add a click handler to a button", "lines": ["});", "const btn = document.getElementById('myBtn');", "btn.addEventListener('click', () => {", "    alert('Clicked!');"], "correct_order": [1, 2, 3, 0], "explanation": "Select element → attach listener → define handler → close.", "concept": "DOM events"},
    ],
}

SPEED_CODE_CHALLENGES = {
    "python": [
        {"id": "py_speed_1", "prompt": "Print 'Hello World'", "expected": "print('Hello World')", "time_limit": 15, "points": 10, "concept": "print function"},
        {"id": "py_speed_2", "prompt": "Create variable x = 42", "expected": "x = 42", "time_limit": 10, "points": 10, "concept": "variables"},
        {"id": "py_speed_3", "prompt": "Check if x equals 5", "expected": "if x == 5:", "time_limit": 12, "points": 15, "concept": "conditionals"},
        {"id": "py_speed_4", "prompt": "Loop from 0 to 9", "expected": "for i in range(10):", "time_limit": 15, "points": 15, "concept": "for loops"},
        {"id": "py_speed_5", "prompt": "Define function named greet", "expected": "def greet():", "time_limit": 12, "points": 15, "concept": "functions"},
        {"id": "py_speed_6", "prompt": "Import the os module", "expected": "import os", "time_limit": 10, "points": 10, "concept": "imports"},
        {"id": "py_speed_7", "prompt": "Create empty list called items", "expected": "items = []", "time_limit": 10, "points": 10, "concept": "lists"},
        {"id": "py_speed_8", "prompt": "Return x + y from function", "expected": "return x + y", "time_limit": 12, "points": 15, "concept": "return values"},
        {"id": "py_speed_9", "prompt": "Create dict with key 'name'", "expected": "data = {'name': ''}", "time_limit": 15, "points": 20, "concept": "dictionaries"},
        {"id": "py_speed_10", "prompt": "List comprehension: squares of 1-5", "expected": "[x**2 for x in range(1,6)]", "time_limit": 20, "points": 25, "concept": "comprehensions"},
    ],
    "javascript": [
        {"id": "js_speed_1", "prompt": "Log 'Hello' to console", "expected": "console.log('Hello')", "time_limit": 15, "points": 10, "concept": "console.log"},
        {"id": "js_speed_2", "prompt": "Declare constant PI = 3.14", "expected": "const PI = 3.14;", "time_limit": 12, "points": 10, "concept": "constants"},
        {"id": "js_speed_3", "prompt": "Arrow function that returns x*2", "expected": "const double = x => x * 2;", "time_limit": 18, "points": 20, "concept": "arrow functions"},
        {"id": "js_speed_4", "prompt": "Destructure name from object", "expected": "const { name } = obj;", "time_limit": 15, "points": 20, "concept": "destructuring"},
        {"id": "js_speed_5", "prompt": "Template literal with name var", "expected": "`Hello ${name}`", "time_limit": 15, "points": 15, "concept": "template literals"},
    ],
    "shell": [
        {"id": "sh_speed_1", "prompt": "Print 'Hello World'", "expected": "echo 'Hello World'", "time_limit": 12, "points": 10, "concept": "echo"},
        {"id": "sh_speed_2", "prompt": "Create variable x=42", "expected": "x=42", "time_limit": 8, "points": 10, "concept": "variables"},
        {"id": "sh_speed_3", "prompt": "Print variable x", "expected": "echo $x", "time_limit": 10, "points": 10, "concept": "variable access"},
        {"id": "sh_speed_4", "prompt": "If x equals 5", "expected": "if [ $x -eq 5 ]; then", "time_limit": 18, "points": 20, "concept": "conditionals"},
        {"id": "sh_speed_5", "prompt": "Loop 1 to 5 with seq", "expected": "for i in $(seq 1 5); do", "time_limit": 18, "points": 20, "concept": "for loops"},
        {"id": "sh_speed_6", "prompt": "Shebang line for bash", "expected": "#!/bin/bash", "time_limit": 12, "points": 15, "concept": "shebang"},
        {"id": "sh_speed_7", "prompt": "Read user input into name", "expected": "read name", "time_limit": 10, "points": 10, "concept": "read input"},
    ],
    "haskell": [
        {"id": "hs_speed_1", "prompt": "Print 'Hello World'", "expected": "main = putStrLn \"Hello World\"", "time_limit": 18, "points": 15, "concept": "putStrLn"},
        {"id": "hs_speed_2", "prompt": "Double function: x times 2", "expected": "double x = x * 2", "time_limit": 15, "points": 15, "concept": "functions"},
        {"id": "hs_speed_3", "prompt": "Type signature: add Int Int Int", "expected": "add :: Int -> Int -> Int", "time_limit": 18, "points": 20, "concept": "type signatures"},
        {"id": "hs_speed_4", "prompt": "List of 1 to 5", "expected": "[1, 2, 3, 4, 5]", "time_limit": 12, "points": 10, "concept": "lists"},
        {"id": "hs_speed_5", "prompt": "Factorial base case", "expected": "factorial 0 = 1", "time_limit": 15, "points": 15, "concept": "pattern matching"},
        {"id": "hs_speed_6", "prompt": "Map double over list", "expected": "map (*2) [1,2,3]", "time_limit": 18, "points": 20, "concept": "higher-order functions"},
    ],
    "elixir": [
        {"id": "ex_speed_1", "prompt": "Print 'Hello World'", "expected": "IO.puts(\"Hello World\")", "time_limit": 15, "points": 10, "concept": "IO.puts"},
        {"id": "ex_speed_2", "prompt": "Create atom :ok", "expected": ":ok", "time_limit": 8, "points": 10, "concept": "atoms"},
        {"id": "ex_speed_3", "prompt": "Pipe string to upcase", "expected": "\"hello\" |> String.upcase()", "time_limit": 18, "points": 20, "concept": "pipe operator"},
        {"id": "ex_speed_4", "prompt": "Define module Greeter", "expected": "defmodule Greeter do", "time_limit": 15, "points": 15, "concept": "modules"},
        {"id": "ex_speed_5", "prompt": "Pattern match list head", "expected": "[head | _] = [1, 2, 3]", "time_limit": 18, "points": 20, "concept": "pattern matching"},
        {"id": "ex_speed_6", "prompt": "Map over list with Enum", "expected": "Enum.map([1,2,3], &(&1 * 2))", "time_limit": 22, "points": 25, "concept": "Enum.map"},
    ],
    "zig": [
        {"id": "zig_speed_1", "prompt": "Import std library", "expected": "const std = @import(\"std\");", "time_limit": 18, "points": 15, "concept": "@import"},
        {"id": "zig_speed_2", "prompt": "Declare const x as i32 = 5", "expected": "const x: i32 = 5;", "time_limit": 15, "points": 15, "concept": "constants"},
        {"id": "zig_speed_3", "prompt": "Declare mutable y as i32 = 10", "expected": "var y: i32 = 10;", "time_limit": 15, "points": 15, "concept": "variables"},
        {"id": "zig_speed_4", "prompt": "Main function signature", "expected": "pub fn main() void {", "time_limit": 18, "points": 20, "concept": "main function"},
        {"id": "zig_speed_5", "prompt": "Optional i32 set to null", "expected": "var x: ?i32 = null;", "time_limit": 15, "points": 20, "concept": "optionals"},
    ],
    "lua": [
        {"id": "lua_speed_1", "prompt": "Print 'Hello World'", "expected": "print('Hello World')", "time_limit": 12, "points": 10, "concept": "print"},
        {"id": "lua_speed_2", "prompt": "Local variable x = 5", "expected": "local x = 5", "time_limit": 10, "points": 10, "concept": "local variables"},
        {"id": "lua_speed_3", "prompt": "Concatenate 'Hi' and ' there'", "expected": "'Hi' .. ' there'", "time_limit": 15, "points": 15, "concept": "concatenation"},
        {"id": "lua_speed_4", "prompt": "Create empty table", "expected": "local t = {}", "time_limit": 10, "points": 10, "concept": "tables"},
        {"id": "lua_speed_5", "prompt": "Define function greet()", "expected": "function greet()", "time_limit": 12, "points": 15, "concept": "functions"},
        {"id": "lua_speed_6", "prompt": "For loop 1 to 10", "expected": "for i = 1, 10 do", "time_limit": 15, "points": 15, "concept": "for loops"},
    ],
}

@api_router.get("/games/bug-hunter/{language}")
async def get_bug_hunter(language: str):
    challenges = BUG_HUNTER_CHALLENGES.get(language, BUG_HUNTER_CHALLENGES.get("python", []))
    selected = random.sample(challenges, min(5, len(challenges)))
    # Remove correct answer info for client
    safe = []
    for c in selected:
        safe.append({
            "id": c["id"], "code": c["code"], "question": c["question"],
            "options": c["options"], "concept": c["concept"],
        })
    return {"language": language, "challenges": safe, "total": len(safe)}

@api_router.post("/games/bug-hunter/{language}/check")
async def check_bug_hunter(language: str, data: dict):
    challenge_id = data.get("challenge_id")
    selected = data.get("selected", -1)
    challenges = BUG_HUNTER_CHALLENGES.get(language, BUG_HUNTER_CHALLENGES.get("python", []))
    for c in challenges:
        if c["id"] == challenge_id:
            correct = selected == c["correct"]
            return {
                "correct": correct,
                "correct_answer": c["correct"],
                "fixed_code": c["fixed_code"],
                "explanation": c["explanation"],
            }
    raise HTTPException(status_code=404, detail="Challenge not found")

@api_router.get("/games/code-puzzle/{language}")
async def get_code_puzzle(language: str):
    puzzles = CODE_PUZZLE_CHALLENGES.get(language, CODE_PUZZLE_CHALLENGES.get("python", []))
    selected = random.sample(puzzles, min(3, len(puzzles)))
    safe = []
    for p in selected:
        shuffled = list(range(len(p["lines"])))
        random.shuffle(shuffled)
        safe.append({
            "id": p["id"], "title": p["title"], "description": p["description"],
            "lines": [p["lines"][i] for i in shuffled],
            "original_indices": shuffled,
            "concept": p["concept"],
        })
    return {"language": language, "puzzles": safe, "total": len(safe)}

@api_router.post("/games/code-puzzle/{language}/check")
async def check_code_puzzle(language: str, data: dict):
    puzzle_id = data.get("puzzle_id")
    user_order = data.get("order", [])
    puzzles = CODE_PUZZLE_CHALLENGES.get(language, CODE_PUZZLE_CHALLENGES.get("python", []))
    for p in puzzles:
        if p["id"] == puzzle_id:
            correct = user_order == p["correct_order"]
            return {
                "correct": correct,
                "correct_order": p["correct_order"],
                "correct_lines": [p["lines"][i] for i in p["correct_order"]],
                "explanation": p["explanation"],
            }
    raise HTTPException(status_code=404, detail="Puzzle not found")

@api_router.get("/games/speed-code/{language}")
async def get_speed_code(language: str):
    challenges = SPEED_CODE_CHALLENGES.get(language, SPEED_CODE_CHALLENGES.get("python", []))
    selected = random.sample(challenges, min(5, len(challenges)))
    safe = [{"id": c["id"], "prompt": c["prompt"], "time_limit": c["time_limit"], "points": c["points"], "concept": c["concept"]} for c in selected]
    return {"language": language, "challenges": safe, "total": len(safe)}

@api_router.post("/games/speed-code/{language}/check")
async def check_speed_code(language: str, data: dict):
    challenge_id = data.get("challenge_id")
    user_code = data.get("code", "").strip()
    challenges = SPEED_CODE_CHALLENGES.get(language, SPEED_CODE_CHALLENGES.get("python", []))
    for c in challenges:
        if c["id"] == challenge_id:
            expected_norm = c["expected"].strip().lower().replace(" ", "")
            user_norm = user_code.lower().replace(" ", "")
            correct = expected_norm == user_norm or c["expected"].strip().lower() in user_code.lower()
            return {
                "correct": correct,
                "expected": c["expected"],
                "points": c["points"] if correct else 0,
            }
    raise HTTPException(status_code=404, detail="Challenge not found")

@api_router.post("/games/complete")
async def complete_game(game: GameComplete, user: dict = Depends(get_current_user)):
    """Track game completion and award XP"""
    score_pct = (game.score / game.total * 100) if game.total > 0 else 0
    perks = get_vip_perks(user)
    
    base_xp = int(score_pct * 0.3)  # Up to 30 XP per game
    xp_earned = int(base_xp * perks["xp_multiplier"])
    gems_earned = 2 if score_pct >= 70 else 0
    
    games_played = user.get("games_played", 0) + 1
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "xp": user.get("xp", 0) + xp_earned,
            "gems": user.get("gems", 0) + gems_earned,
            "daily_xp": user.get("daily_xp", 0) + xp_earned,
            "games_played": games_played,
            "level": 1 + ((user.get("xp", 0) + xp_earned) // 100),
        }}
    )
    
    await db.game_scores.insert_one({
        "user_id": user["id"],
        "game_type": game.game_type,
        "language": game.language,
        "score": game.score,
        "total": game.total,
        "score_pct": score_pct,
        "xp_earned": xp_earned,
        "time_taken": game.time_taken,
        "played_at": datetime.utcnow().isoformat(),
    })
    
    return {
        "xp_earned": xp_earned,
        "gems_earned": gems_earned,
        "score_pct": int(score_pct),
        "games_played": games_played,
    }

@api_router.get("/games/stats")
async def get_game_stats(user: dict = Depends(get_current_user)):
    scores = await db.game_scores.find({"user_id": user["id"]}).sort("played_at", -1).to_list(100)
    by_type = {}
    for s in scores:
        gt = s.get("game_type", "unknown")
        if gt not in by_type:
            by_type[gt] = {"played": 0, "best_score": 0, "total_xp": 0}
        by_type[gt]["played"] += 1
        by_type[gt]["best_score"] = max(by_type[gt]["best_score"], s.get("score_pct", 0))
        by_type[gt]["total_xp"] += s.get("xp_earned", 0)
    
    return {
        "total_games": len(scores),
        "games_played": user.get("games_played", 0),
        "by_type": by_type,
    }

# ============== ROOT ==============

@api_router.get("/")
async def root():
    return {"message": "Codero API v4 - Learn to code with games & VIP perks!"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
