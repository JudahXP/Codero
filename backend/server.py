from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets

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
    last_activity: Optional[str] = None
    badges: List[str] = []
    friends: List[str] = []
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

class FriendRequest(BaseModel):
    friend_username: str

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

# ============== PROGRAMMING LANGUAGES DATA ==============

LANGUAGES = [
    {"id": "python", "name": "Python", "icon": "logo-python", "color": "#3776AB", "description": "Great for beginners and AI"},
    {"id": "javascript", "name": "JavaScript", "icon": "logo-javascript", "color": "#F7DF1E", "description": "The language of the web"},
    {"id": "java", "name": "Java", "icon": "cafe", "color": "#ED8B00", "description": "Enterprise & Android apps"},
    {"id": "cpp", "name": "C++", "icon": "code-slash", "color": "#00599C", "description": "Performance & game dev"},
    {"id": "csharp", "name": "C#", "icon": "game-controller", "color": "#239120", "description": "Unity & Windows apps"},
    {"id": "ruby", "name": "Ruby", "icon": "diamond", "color": "#CC342D", "description": "Elegant web development"},
    {"id": "go", "name": "Go", "icon": "rocket", "color": "#00ADD8", "description": "Fast & concurrent"},
    {"id": "rust", "name": "Rust", "icon": "shield-checkmark", "color": "#DEA584", "description": "Safe systems programming"},
    {"id": "swift", "name": "Swift", "icon": "logo-apple", "color": "#FA7343", "description": "iOS & macOS apps"},
    {"id": "kotlin", "name": "Kotlin", "icon": "logo-android", "color": "#7F52FF", "description": "Modern Android dev"},
    {"id": "typescript", "name": "TypeScript", "icon": "code-working", "color": "#3178C6", "description": "Typed JavaScript"},
    {"id": "php", "name": "PHP", "icon": "server", "color": "#777BB4", "description": "Web server scripting"},
    {"id": "sql", "name": "SQL", "icon": "file-tray-stacked", "color": "#4479A1", "description": "Database queries"},
    {"id": "html_css", "name": "HTML/CSS", "icon": "globe", "color": "#E34F26", "description": "Web page structure"},
    {"id": "skript", "name": "Skript", "icon": "cube", "color": "#6B8E23", "description": "Minecraft scripting"},
    {"id": "lua", "name": "Lua", "icon": "moon", "color": "#000080", "description": "Game scripting & Roblox"},
]

# ============== LESSON DATA (TONS OF LESSONS) ==============

def generate_lessons(language_id: str) -> List[dict]:
    """Generate comprehensive lessons for each language"""
    
    # Base lesson templates that adapt per language
    lesson_templates = {
        "python": {
            "basics": [
                {"id": f"{language_id}_1_1", "title": "Hello World", "description": "Print your first message", "xp": 10, "unit": 1,
                 "exercises": [
                     {"type": "multiple_choice", "question": "What function prints output in Python?", "options": ["print()", "echo()", "console.log()", "System.out"], "correct": 0},
                     {"type": "code", "question": "Write code to print 'Hello, World!'", "starter": "", "solution": "print('Hello, World!')", "hint": "Use the print() function"},
                     {"type": "fill_blank", "question": "Complete: ___('Hello')", "answer": "print"},
                 ]},
                {"id": f"{language_id}_1_2", "title": "Variables", "description": "Store data in variables", "xp": 15, "unit": 1,
                 "exercises": [
                     {"type": "multiple_choice", "question": "How do you create a variable in Python?", "options": ["name = 'John'", "var name = 'John'", "let name = 'John'", "String name = 'John'"], "correct": 0},
                     {"type": "code", "question": "Create a variable called 'age' with value 25", "starter": "", "solution": "age = 25", "hint": "variable_name = value"},
                     {"type": "multiple_choice", "question": "What type is the variable: x = 3.14?", "options": ["int", "float", "str", "bool"], "correct": 1},
                 ]},
                {"id": f"{language_id}_1_3", "title": "Data Types", "description": "Learn about strings, integers, floats", "xp": 15, "unit": 1,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Which is a string?", "options": ["42", "'Hello'", "3.14", "True"], "correct": 1},
                     {"type": "code", "question": "Create a boolean variable 'is_active' set to True", "starter": "", "solution": "is_active = True", "hint": "Boolean values are True or False"},
                     {"type": "fill_blank", "question": "Convert '42' to int: int(___)", "answer": "'42'"},
                 ]},
                {"id": f"{language_id}_1_4", "title": "String Operations", "description": "Manipulate text data", "xp": 20, "unit": 1,
                 "exercises": [
                     {"type": "multiple_choice", "question": "How to get string length?", "options": ["len(s)", "s.length", "s.size()", "length(s)"], "correct": 0},
                     {"type": "code", "question": "Concatenate 'Hello' and 'World' with a space", "starter": "", "solution": "'Hello' + ' ' + 'World'", "hint": "Use + to join strings"},
                     {"type": "multiple_choice", "question": "What is 'Python'[0]?", "options": ["P", "y", "Python", "Error"], "correct": 0},
                 ]},
                {"id": f"{language_id}_1_5", "title": "Numbers & Math", "description": "Arithmetic operations", "xp": 20, "unit": 1,
                 "exercises": [
                     {"type": "multiple_choice", "question": "What is 7 // 2 in Python?", "options": ["3.5", "3", "4", "2"], "correct": 1},
                     {"type": "code", "question": "Calculate 2 to the power of 8", "starter": "", "solution": "2 ** 8", "hint": "Use ** for exponentiation"},
                     {"type": "fill_blank", "question": "Modulo operator: 10 ___ 3 = 1", "answer": "%"},
                 ]},
            ],
            "control_flow": [
                {"id": f"{language_id}_2_1", "title": "If Statements", "description": "Make decisions in code", "xp": 25, "unit": 2,
                 "exercises": [
                     {"type": "multiple_choice", "question": "What keyword starts a conditional?", "options": ["if", "when", "case", "check"], "correct": 0},
                     {"type": "code", "question": "Write an if statement that prints 'Adult' if age >= 18", "starter": "age = 20\n", "solution": "age = 20\nif age >= 18:\n    print('Adult')", "hint": "Remember the colon and indentation"},
                     {"type": "fill_blank", "question": "if x > 5___", "answer": ":"},
                 ]},
                {"id": f"{language_id}_2_2", "title": "Else & Elif", "description": "Handle multiple conditions", "xp": 25, "unit": 2,
                 "exercises": [
                     {"type": "multiple_choice", "question": "What is elif short for?", "options": ["else if", "elif if", "else elif", "end if"], "correct": 0},
                     {"type": "code", "question": "Add else clause to print 'Minor' if age < 18", "starter": "age = 15\nif age >= 18:\n    print('Adult')\n", "solution": "age = 15\nif age >= 18:\n    print('Adult')\nelse:\n    print('Minor')", "hint": "else doesn't need a condition"},
                     {"type": "multiple_choice", "question": "How many elif can you have?", "options": ["1", "2", "Unlimited", "0"], "correct": 2},
                 ]},
                {"id": f"{language_id}_2_3", "title": "For Loops", "description": "Repeat with for", "xp": 30, "unit": 2,
                 "exercises": [
                     {"type": "multiple_choice", "question": "What does range(5) produce?", "options": ["0,1,2,3,4", "1,2,3,4,5", "0,1,2,3,4,5", "1,2,3,4"], "correct": 0},
                     {"type": "code", "question": "Print numbers 1 to 5 using a for loop", "starter": "", "solution": "for i in range(1, 6):\n    print(i)", "hint": "range(start, end) - end is exclusive"},
                     {"type": "fill_blank", "question": "for item ___ my_list:", "answer": "in"},
                 ]},
                {"id": f"{language_id}_2_4", "title": "While Loops", "description": "Repeat while condition true", "xp": 30, "unit": 2,
                 "exercises": [
                     {"type": "multiple_choice", "question": "When does a while loop stop?", "options": ["When condition is False", "After 10 iterations", "Never", "When break is called"], "correct": 0},
                     {"type": "code", "question": "Count down from 5 to 1 using while", "starter": "count = 5\n", "solution": "count = 5\nwhile count > 0:\n    print(count)\n    count -= 1", "hint": "Don't forget to decrement!"},
                     {"type": "fill_blank", "question": "___ x > 0:", "answer": "while"},
                 ]},
                {"id": f"{language_id}_2_5", "title": "Break & Continue", "description": "Control loop flow", "xp": 25, "unit": 2,
                 "exercises": [
                     {"type": "multiple_choice", "question": "What does break do?", "options": ["Exit the loop", "Skip iteration", "Pause loop", "Restart loop"], "correct": 0},
                     {"type": "code", "question": "Exit loop when i equals 3", "starter": "for i in range(10):\n    ", "solution": "for i in range(10):\n    if i == 3:\n        break\n    print(i)", "hint": "Use break inside an if"},
                     {"type": "multiple_choice", "question": "What does continue do?", "options": ["Exit loop", "Skip to next iteration", "Stop program", "Print value"], "correct": 1},
                 ]},
            ],
            "functions": [
                {"id": f"{language_id}_3_1", "title": "Defining Functions", "description": "Create reusable code blocks", "xp": 35, "unit": 3,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Which keyword defines a function?", "options": ["def", "function", "func", "define"], "correct": 0},
                     {"type": "code", "question": "Create a function greet() that prints 'Hello!'", "starter": "", "solution": "def greet():\n    print('Hello!')", "hint": "def function_name():"},
                     {"type": "fill_blank", "question": "___ my_function():", "answer": "def"},
                 ]},
                {"id": f"{language_id}_3_2", "title": "Parameters", "description": "Pass data to functions", "xp": 35, "unit": 3,
                 "exercises": [
                     {"type": "multiple_choice", "question": "What are parameters?", "options": ["Inputs to functions", "Return values", "Variables", "Loops"], "correct": 0},
                     {"type": "code", "question": "Create add(a, b) that returns a + b", "starter": "", "solution": "def add(a, b):\n    return a + b", "hint": "Use return to give back a value"},
                     {"type": "multiple_choice", "question": "Default param syntax?", "options": ["def f(x=5)", "def f(x:5)", "def f(x->5)", "def f(5=x)"], "correct": 0},
                 ]},
                {"id": f"{language_id}_3_3", "title": "Return Values", "description": "Get results from functions", "xp": 35, "unit": 3,
                 "exercises": [
                     {"type": "multiple_choice", "question": "What if no return statement?", "options": ["Returns None", "Error", "Returns 0", "Infinite loop"], "correct": 0},
                     {"type": "code", "question": "Create square(n) returning n squared", "starter": "", "solution": "def square(n):\n    return n ** 2", "hint": "n squared is n ** 2"},
                     {"type": "fill_blank", "question": "def double(x):\n    ___ x * 2", "answer": "return"},
                 ]},
                {"id": f"{language_id}_3_4", "title": "Lambda Functions", "description": "Quick anonymous functions", "xp": 40, "unit": 3,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Lambda syntax?", "options": ["lambda x: x*2", "-> x: x*2", "func x: x*2", "(x) => x*2"], "correct": 0},
                     {"type": "code", "question": "Create a lambda that adds 10 to x", "starter": "", "solution": "add_ten = lambda x: x + 10", "hint": "lambda parameter: expression"},
                     {"type": "multiple_choice", "question": "Lambdas are also called?", "options": ["Anonymous functions", "Named functions", "Loops", "Classes"], "correct": 0},
                 ]},
                {"id": f"{language_id}_3_5", "title": "Scope", "description": "Variable visibility", "xp": 40, "unit": 3,
                 "exercises": [
                     {"type": "multiple_choice", "question": "What is local scope?", "options": ["Inside function", "Everywhere", "In class only", "In module"], "correct": 0},
                     {"type": "code", "question": "Use global keyword to modify x inside function", "starter": "x = 10\ndef change():\n    ", "solution": "x = 10\ndef change():\n    global x\n    x = 20", "hint": "global variable_name"},
                     {"type": "fill_blank", "question": "___ x  # to use global x in function", "answer": "global"},
                 ]},
            ],
            "data_structures": [
                {"id": f"{language_id}_4_1", "title": "Lists", "description": "Ordered collections", "xp": 30, "unit": 4,
                 "exercises": [
                     {"type": "multiple_choice", "question": "How to create an empty list?", "options": ["[]", "{}", "()", "list{}"], "correct": 0},
                     {"type": "code", "question": "Create a list with 1, 2, 3 and append 4", "starter": "", "solution": "nums = [1, 2, 3]\nnums.append(4)", "hint": "Use .append() method"},
                     {"type": "fill_blank", "question": "my_list.___(5)  # add 5", "answer": "append"},
                 ]},
                {"id": f"{language_id}_4_2", "title": "List Methods", "description": "Manipulate lists", "xp": 35, "unit": 4,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Remove last item?", "options": [".pop()", ".remove()", ".delete()", ".drop()"], "correct": 0},
                     {"type": "code", "question": "Sort list [3,1,2] in ascending order", "starter": "nums = [3, 1, 2]\n", "solution": "nums = [3, 1, 2]\nnums.sort()", "hint": ".sort() modifies in place"},
                     {"type": "multiple_choice", "question": "Insert at index 0?", "options": [".insert(0, x)", ".add(0, x)", ".put(0, x)", ".push(0, x)"], "correct": 0},
                 ]},
                {"id": f"{language_id}_4_3", "title": "Dictionaries", "description": "Key-value pairs", "xp": 35, "unit": 4,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Dict syntax?", "options": ["{'key': 'value'}", "['key': 'value']", "('key': 'value')", "{key = value}"], "correct": 0},
                     {"type": "code", "question": "Create a dict with name='John' and age=30", "starter": "", "solution": "person = {'name': 'John', 'age': 30}", "hint": "Use curly braces and colons"},
                     {"type": "fill_blank", "question": "Get all keys: dict.___()", "answer": "keys"},
                 ]},
                {"id": f"{language_id}_4_4", "title": "Tuples", "description": "Immutable sequences", "xp": 30, "unit": 4,
                 "exercises": [
                     {"type": "multiple_choice", "question": "What makes tuples different from lists?", "options": ["Immutable", "No order", "No duplicates", "Keys required"], "correct": 0},
                     {"type": "code", "question": "Create a tuple with coordinates (10, 20)", "starter": "", "solution": "coords = (10, 20)", "hint": "Use parentheses"},
                     {"type": "multiple_choice", "question": "Single element tuple?", "options": ["(5,)", "(5)", "[5]", "{5}"], "correct": 0},
                 ]},
                {"id": f"{language_id}_4_5", "title": "Sets", "description": "Unique collections", "xp": 30, "unit": 4,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Sets allow duplicates?", "options": ["No", "Yes", "Sometimes", "Only strings"], "correct": 0},
                     {"type": "code", "question": "Create a set from list [1,1,2,2,3]", "starter": "", "solution": "unique = set([1, 1, 2, 2, 3])", "hint": "set() removes duplicates"},
                     {"type": "fill_blank", "question": "Add to set: my_set.___(5)", "answer": "add"},
                 ]},
            ],
            "oop": [
                {"id": f"{language_id}_5_1", "title": "Classes Intro", "description": "Create blueprints for objects", "xp": 45, "unit": 5,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Keyword to define a class?", "options": ["class", "def", "object", "new"], "correct": 0},
                     {"type": "code", "question": "Create an empty class called Dog", "starter": "", "solution": "class Dog:\n    pass", "hint": "Use pass for empty body"},
                     {"type": "fill_blank", "question": "___ MyClass:", "answer": "class"},
                 ]},
                {"id": f"{language_id}_5_2", "title": "Constructor", "description": "Initialize objects", "xp": 45, "unit": 5,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Constructor method name?", "options": ["__init__", "__new__", "__create__", "__start__"], "correct": 0},
                     {"type": "code", "question": "Add __init__ with name parameter to Dog class", "starter": "class Dog:\n    ", "solution": "class Dog:\n    def __init__(self, name):\n        self.name = name", "hint": "First param is always self"},
                     {"type": "fill_blank", "question": "def __init__(___,  name):", "answer": "self"},
                 ]},
                {"id": f"{language_id}_5_3", "title": "Methods", "description": "Add behaviors to classes", "xp": 45, "unit": 5,
                 "exercises": [
                     {"type": "multiple_choice", "question": "First param of instance method?", "options": ["self", "this", "me", "instance"], "correct": 0},
                     {"type": "code", "question": "Add bark() method that prints 'Woof!'", "starter": "class Dog:\n    def __init__(self, name):\n        self.name = name\n    ", "solution": "class Dog:\n    def __init__(self, name):\n        self.name = name\n    def bark(self):\n        print('Woof!')", "hint": "def method_name(self):"},
                     {"type": "multiple_choice", "question": "Call method on object?", "options": ["obj.method()", "method(obj)", "obj->method()", "obj::method()"], "correct": 0},
                 ]},
                {"id": f"{language_id}_5_4", "title": "Inheritance", "description": "Extend existing classes", "xp": 50, "unit": 5,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Inherit from Animal class?", "options": ["class Dog(Animal):", "class Dog extends Animal:", "class Dog : Animal:", "class Dog inherits Animal:"], "correct": 0},
                     {"type": "code", "question": "Create Puppy class inheriting from Dog", "starter": "class Dog:\n    def bark(self):\n        print('Woof!')\n\n", "solution": "class Dog:\n    def bark(self):\n        print('Woof!')\n\nclass Puppy(Dog):\n    pass", "hint": "class Child(Parent):"},
                     {"type": "fill_blank", "question": "Call parent method: super().___", "answer": "__init__"},
                 ]},
                {"id": f"{language_id}_5_5", "title": "Encapsulation", "description": "Private attributes", "xp": 50, "unit": 5,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Convention for private attr?", "options": ["_name", "private name", "#name", "@name"], "correct": 0},
                     {"type": "code", "question": "Create private attribute _balance = 0", "starter": "class Account:\n    def __init__(self):\n        ", "solution": "class Account:\n    def __init__(self):\n        self._balance = 0", "hint": "self._attribute_name"},
                     {"type": "multiple_choice", "question": "Name mangling prefix?", "options": ["__", "_", "@@", "##"], "correct": 0},
                 ]},
            ],
            "advanced": [
                {"id": f"{language_id}_6_1", "title": "List Comprehension", "description": "Elegant list creation", "xp": 40, "unit": 6,
                 "exercises": [
                     {"type": "multiple_choice", "question": "[x*2 for x in range(5)] produces?", "options": ["[0,2,4,6,8]", "[2,4,6,8,10]", "[0,1,2,3,4]", "[1,2,3,4,5]"], "correct": 0},
                     {"type": "code", "question": "Create squares of 1-5 using comprehension", "starter": "", "solution": "squares = [x**2 for x in range(1, 6)]", "hint": "[expression for item in iterable]"},
                     {"type": "fill_blank", "question": "[x for x ___ nums if x > 0]", "answer": "in"},
                 ]},
                {"id": f"{language_id}_6_2", "title": "File Handling", "description": "Read and write files", "xp": 45, "unit": 6,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Best way to open file?", "options": ["with open()", "open()", "file()", "read()"], "correct": 0},
                     {"type": "code", "question": "Read entire file content", "starter": "", "solution": "with open('file.txt', 'r') as f:\n    content = f.read()", "hint": "with open() as f:"},
                     {"type": "fill_blank", "question": "open('file.txt', '___')  # write mode", "answer": "w"},
                 ]},
                {"id": f"{language_id}_6_3", "title": "Exception Handling", "description": "Handle errors gracefully", "xp": 45, "unit": 6,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Catch all exceptions?", "options": ["except Exception:", "catch Exception:", "error Exception:", "handle Exception:"], "correct": 0},
                     {"type": "code", "question": "Try to convert 'abc' to int, handle error", "starter": "", "solution": "try:\n    int('abc')\nexcept ValueError:\n    print('Invalid number')", "hint": "try/except block"},
                     {"type": "fill_blank", "question": "___:\n    risky_code()", "answer": "try"},
                 ]},
                {"id": f"{language_id}_6_4", "title": "Decorators", "description": "Modify function behavior", "xp": 55, "unit": 6,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Decorator syntax?", "options": ["@decorator", "#decorator", "!decorator", "$decorator"], "correct": 0},
                     {"type": "code", "question": "Apply @staticmethod to a method", "starter": "class Math:\n    ", "solution": "class Math:\n    @staticmethod\n    def add(a, b):\n        return a + b", "hint": "@decorator above function"},
                     {"type": "multiple_choice", "question": "Decorators are?", "options": ["Functions wrapping functions", "Classes", "Variables", "Loops"], "correct": 0},
                 ]},
                {"id": f"{language_id}_6_5", "title": "Generators", "description": "Lazy iterators", "xp": 55, "unit": 6,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Generator keyword?", "options": ["yield", "return", "generate", "iterate"], "correct": 0},
                     {"type": "code", "question": "Create generator counting 1 to 3", "starter": "", "solution": "def count():\n    yield 1\n    yield 2\n    yield 3", "hint": "Use yield instead of return"},
                     {"type": "fill_blank", "question": "def gen():\n    ___ value", "answer": "yield"},
                 ]},
            ],
        },
        "javascript": {
            "basics": [
                {"id": f"{language_id}_1_1", "title": "Hello World", "description": "Output in JavaScript", "xp": 10, "unit": 1,
                 "exercises": [
                     {"type": "multiple_choice", "question": "How to print to console?", "options": ["console.log()", "print()", "echo()", "System.out"], "correct": 0},
                     {"type": "code", "question": "Print 'Hello, World!' to console", "starter": "", "solution": "console.log('Hello, World!');", "hint": "Use console.log()"},
                     {"type": "fill_blank", "question": "console.___('Hi');", "answer": "log"},
                 ]},
                {"id": f"{language_id}_1_2", "title": "Variables", "description": "Declare variables", "xp": 15, "unit": 1,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Best way to declare variable?", "options": ["let", "var", "const", "variable"], "correct": 0},
                     {"type": "code", "question": "Create variable name with value 'Alice'", "starter": "", "solution": "let name = 'Alice';", "hint": "let variable = value;"},
                     {"type": "multiple_choice", "question": "const variables can be changed?", "options": ["No", "Yes", "Sometimes", "Only strings"], "correct": 0},
                 ]},
                {"id": f"{language_id}_1_3", "title": "Data Types", "description": "Numbers, strings, booleans", "xp": 15, "unit": 1,
                 "exercises": [
                     {"type": "multiple_choice", "question": "typeof 'hello' returns?", "options": ["string", "text", "str", "char"], "correct": 0},
                     {"type": "code", "question": "Create array with 1, 2, 3", "starter": "", "solution": "let arr = [1, 2, 3];", "hint": "Use square brackets"},
                     {"type": "fill_blank", "question": "typeof 42 returns '___'", "answer": "number"},
                 ]},
                {"id": f"{language_id}_1_4", "title": "Strings", "description": "Text manipulation", "xp": 20, "unit": 1,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Template literal syntax?", "options": ["`Hello ${name}`", "'Hello {name}'", "\"Hello #{name}\"", "f'Hello {name}'"], "correct": 0},
                     {"type": "code", "question": "Join 'Hello' and name using template literal", "starter": "let name = 'World';\n", "solution": "let name = 'World';\nlet greeting = `Hello ${name}`;", "hint": "Use backticks and ${}"},
                     {"type": "fill_blank", "question": "'hello'.toUpperCase() = '___'", "answer": "HELLO"},
                 ]},
                {"id": f"{language_id}_1_5", "title": "Operators", "description": "Math and comparison", "xp": 20, "unit": 1,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Strict equality operator?", "options": ["===", "==", "=", "!="], "correct": 0},
                     {"type": "code", "question": "Check if 5 strictly equals '5'", "starter": "", "solution": "5 === '5'; // false", "hint": "=== checks type too"},
                     {"type": "multiple_choice", "question": "10 % 3 equals?", "options": ["1", "3", "3.33", "0"], "correct": 0},
                 ]},
            ],
            "control_flow": [
                {"id": f"{language_id}_2_1", "title": "If Statements", "description": "Conditional logic", "xp": 25, "unit": 2,
                 "exercises": [
                     {"type": "multiple_choice", "question": "If syntax requires?", "options": ["Parentheses and braces", "Just braces", "Just parentheses", "Colons"], "correct": 0},
                     {"type": "code", "question": "If age >= 18, log 'Adult'", "starter": "let age = 20;\n", "solution": "let age = 20;\nif (age >= 18) {\n    console.log('Adult');\n}", "hint": "if (condition) { }"},
                     {"type": "fill_blank", "question": "if (x > 5) ___", "answer": "{"},
                 ]},
                {"id": f"{language_id}_2_2", "title": "Else & Ternary", "description": "Alternative paths", "xp": 25, "unit": 2,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Ternary operator syntax?", "options": ["a ? b : c", "a : b ? c", "a if b else c", "if a then b else c"], "correct": 0},
                     {"type": "code", "question": "Use ternary: if x>10 return 'big' else 'small'", "starter": "let x = 15;\n", "solution": "let x = 15;\nlet result = x > 10 ? 'big' : 'small';", "hint": "condition ? true : false"},
                     {"type": "fill_blank", "question": "x > 5 ___ 'yes' : 'no'", "answer": "?"},
                 ]},
                {"id": f"{language_id}_2_3", "title": "For Loops", "description": "Iterate with for", "xp": 30, "unit": 2,
                 "exercises": [
                     {"type": "multiple_choice", "question": "for loop has how many parts?", "options": ["3", "2", "4", "1"], "correct": 0},
                     {"type": "code", "question": "Print 0 to 4 using for loop", "starter": "", "solution": "for (let i = 0; i < 5; i++) {\n    console.log(i);\n}", "hint": "for (init; condition; update)"},
                     {"type": "fill_blank", "question": "for (let i=0; i<5; i___)", "answer": "++"},
                 ]},
                {"id": f"{language_id}_2_4", "title": "While & Do-While", "description": "Conditional loops", "xp": 30, "unit": 2,
                 "exercises": [
                     {"type": "multiple_choice", "question": "do-while runs at least?", "options": ["Once", "Zero times", "Twice", "Depends"], "correct": 0},
                     {"type": "code", "question": "While x < 5, log x and increment", "starter": "let x = 0;\n", "solution": "let x = 0;\nwhile (x < 5) {\n    console.log(x);\n    x++;\n}", "hint": "while (condition) { }"},
                     {"type": "fill_blank", "question": "___ (count > 0) { }", "answer": "while"},
                 ]},
                {"id": f"{language_id}_2_5", "title": "Array Iteration", "description": "forEach, map, filter", "xp": 35, "unit": 2,
                 "exercises": [
                     {"type": "multiple_choice", "question": "map() returns?", "options": ["New array", "Nothing", "Boolean", "Number"], "correct": 0},
                     {"type": "code", "question": "Double each number in [1,2,3] using map", "starter": "let nums = [1, 2, 3];\n", "solution": "let nums = [1, 2, 3];\nlet doubled = nums.map(x => x * 2);", "hint": "array.map(item => newItem)"},
                     {"type": "fill_blank", "question": "nums.___(x => x > 2)  // keep > 2", "answer": "filter"},
                 ]},
            ],
            "functions": [
                {"id": f"{language_id}_3_1", "title": "Function Declaration", "description": "Create functions", "xp": 35, "unit": 3,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Function keyword?", "options": ["function", "def", "func", "fn"], "correct": 0},
                     {"type": "code", "question": "Create function greet() that logs 'Hello'", "starter": "", "solution": "function greet() {\n    console.log('Hello');\n}", "hint": "function name() { }"},
                     {"type": "fill_blank", "question": "___ add(a, b) { return a+b; }", "answer": "function"},
                 ]},
                {"id": f"{language_id}_3_2", "title": "Arrow Functions", "description": "Modern function syntax", "xp": 35, "unit": 3,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Arrow function syntax?", "options": ["() => {}", "-> {}", "=> ()", "function =>"], "correct": 0},
                     {"type": "code", "question": "Create arrow function square that returns x*x", "starter": "", "solution": "const square = x => x * x;", "hint": "param => expression"},
                     {"type": "fill_blank", "question": "const add = (a,b) ___ a + b;", "answer": "=>"},
                 ]},
                {"id": f"{language_id}_3_3", "title": "Parameters & Defaults", "description": "Function inputs", "xp": 35, "unit": 3,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Default parameter syntax?", "options": ["param = value", "param: value", "param -> value", "param == value"], "correct": 0},
                     {"type": "code", "question": "Create greet(name='Guest') with default", "starter": "", "solution": "function greet(name = 'Guest') {\n    console.log(`Hello ${name}`);\n}", "hint": "function f(param = default)"},
                     {"type": "fill_blank", "question": "function say(msg ___ 'Hi')", "answer": "="},
                 ]},
                {"id": f"{language_id}_3_4", "title": "Callbacks", "description": "Functions as arguments", "xp": 40, "unit": 3,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Callback is?", "options": ["Function passed to function", "Return value", "Variable", "Loop"], "correct": 0},
                     {"type": "code", "question": "Use setTimeout to log 'Done' after 1000ms", "starter": "", "solution": "setTimeout(() => {\n    console.log('Done');\n}, 1000);", "hint": "setTimeout(callback, delay)"},
                     {"type": "multiple_choice", "question": "Array.forEach takes a?", "options": ["Callback function", "Number", "String", "Boolean"], "correct": 0},
                 ]},
                {"id": f"{language_id}_3_5", "title": "Closures", "description": "Functions remembering scope", "xp": 45, "unit": 3,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Closure allows access to?", "options": ["Outer function scope", "Only global scope", "Nothing", "Inner scope only"], "correct": 0},
                     {"type": "code", "question": "Create counter function using closure", "starter": "", "solution": "function counter() {\n    let count = 0;\n    return () => ++count;\n}", "hint": "Return function that uses outer variable"},
                     {"type": "fill_blank", "question": "Inner function ___ outer scope", "answer": "remembers"},
                 ]},
            ],
            "objects": [
                {"id": f"{language_id}_4_1", "title": "Object Basics", "description": "Create objects", "xp": 30, "unit": 4,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Object literal syntax?", "options": ["{ key: value }", "[ key: value ]", "( key: value )", "< key: value >"], "correct": 0},
                     {"type": "code", "question": "Create person object with name and age", "starter": "", "solution": "const person = {\n    name: 'John',\n    age: 30\n};", "hint": "{ property: value }"},
                     {"type": "fill_blank", "question": "person.name = person___'name'___", "answer": "[,]"},
                 ]},
                {"id": f"{language_id}_4_2", "title": "Object Methods", "description": "Functions in objects", "xp": 35, "unit": 4,
                 "exercises": [
                     {"type": "multiple_choice", "question": "'this' refers to?", "options": ["Current object", "Window", "Function", "Class"], "correct": 0},
                     {"type": "code", "question": "Add greet method that uses this.name", "starter": "const user = {\n    name: 'Alice',\n    ", "solution": "const user = {\n    name: 'Alice',\n    greet() {\n        console.log(`Hi, I'm ${this.name}`);\n    }\n};", "hint": "methodName() { this.property }"},
                     {"type": "fill_blank", "question": "greet() { return ___.name; }", "answer": "this"},
                 ]},
                {"id": f"{language_id}_4_3", "title": "Destructuring", "description": "Extract object properties", "xp": 35, "unit": 4,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Destructure name from person?", "options": ["const { name } = person", "const name = person.name", "const [name] = person", "person -> name"], "correct": 0},
                     {"type": "code", "question": "Destructure x and y from point object", "starter": "const point = { x: 10, y: 20 };\n", "solution": "const point = { x: 10, y: 20 };\nconst { x, y } = point;", "hint": "const { prop1, prop2 } = obj"},
                     {"type": "fill_blank", "question": "const ___ name, age } = user;", "answer": "{"},
                 ]},
                {"id": f"{language_id}_4_4", "title": "Spread & Rest", "description": "... operator", "xp": 40, "unit": 4,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Spread operator copies?", "options": ["Array/object elements", "References only", "Nothing", "First element"], "correct": 0},
                     {"type": "code", "question": "Merge obj1 and obj2 using spread", "starter": "const obj1 = { a: 1 };\nconst obj2 = { b: 2 };\n", "solution": "const obj1 = { a: 1 };\nconst obj2 = { b: 2 };\nconst merged = { ...obj1, ...obj2 };", "hint": "{ ...obj1, ...obj2 }"},
                     {"type": "fill_blank", "question": "const copy = [___arr];", "answer": "..."},
                 ]},
                {"id": f"{language_id}_4_5", "title": "Classes", "description": "ES6 class syntax", "xp": 45, "unit": 4,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Constructor method is called?", "options": ["When object created", "When method called", "Never", "On delete"], "correct": 0},
                     {"type": "code", "question": "Create Person class with name in constructor", "starter": "", "solution": "class Person {\n    constructor(name) {\n        this.name = name;\n    }\n}", "hint": "class Name { constructor() }"},
                     {"type": "fill_blank", "question": "class Dog ___ Animal { }", "answer": "extends"},
                 ]},
            ],
            "async": [
                {"id": f"{language_id}_5_1", "title": "Promises", "description": "Handle async operations", "xp": 45, "unit": 5,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Promise states?", "options": ["pending, fulfilled, rejected", "start, success, fail", "waiting, done, error", "begin, end, stop"], "correct": 0},
                     {"type": "code", "question": "Create promise that resolves with 'Done'", "starter": "", "solution": "const promise = new Promise((resolve, reject) => {\n    resolve('Done');\n});", "hint": "new Promise((resolve, reject) => {})"},
                     {"type": "fill_blank", "question": "promise.___(result => console.log(result))", "answer": "then"},
                 ]},
                {"id": f"{language_id}_5_2", "title": "Async/Await", "description": "Cleaner async code", "xp": 45, "unit": 5,
                 "exercises": [
                     {"type": "multiple_choice", "question": "await can only be used in?", "options": ["async function", "Any function", "Loops", "Callbacks"], "correct": 0},
                     {"type": "code", "question": "Create async function that awaits promise", "starter": "", "solution": "async function getData() {\n    const result = await fetch('/api/data');\n    return result.json();\n}", "hint": "async function name() { await }"},
                     {"type": "fill_blank", "question": "___ function fetchData() { await... }", "answer": "async"},
                 ]},
                {"id": f"{language_id}_5_3", "title": "Fetch API", "description": "HTTP requests", "xp": 50, "unit": 5,
                 "exercises": [
                     {"type": "multiple_choice", "question": "fetch returns?", "options": ["Promise", "Data directly", "Error", "Array"], "correct": 0},
                     {"type": "code", "question": "Fetch data from '/api/users'", "starter": "", "solution": "fetch('/api/users')\n    .then(res => res.json())\n    .then(data => console.log(data));", "hint": "fetch(url).then().then()"},
                     {"type": "fill_blank", "question": "const res = await ___(url);", "answer": "fetch"},
                 ]},
                {"id": f"{language_id}_5_4", "title": "Error Handling", "description": "try/catch with async", "xp": 50, "unit": 5,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Catch async errors with?", "options": ["try/catch", ".error()", ".fail()", "if/else"], "correct": 0},
                     {"type": "code", "question": "Wrap fetch in try/catch", "starter": "async function getData() {\n    ", "solution": "async function getData() {\n    try {\n        const res = await fetch('/api');\n        return res.json();\n    } catch (error) {\n        console.error(error);\n    }\n}", "hint": "try { await } catch (e) { }"},
                     {"type": "fill_blank", "question": "promise.catch(___ => console.log(e))", "answer": "e"},
                 ]},
                {"id": f"{language_id}_5_5", "title": "Promise.all", "description": "Multiple promises", "xp": 55, "unit": 5,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Promise.all resolves when?", "options": ["All promises resolve", "First resolves", "Last resolves", "Any rejects"], "correct": 0},
                     {"type": "code", "question": "Wait for p1 and p2 using Promise.all", "starter": "const p1 = fetch('/api/1');\nconst p2 = fetch('/api/2');\n", "solution": "const p1 = fetch('/api/1');\nconst p2 = fetch('/api/2');\nconst [r1, r2] = await Promise.all([p1, p2]);", "hint": "Promise.all([promises])"},
                     {"type": "fill_blank", "question": "Promise.___(promises)  // wait for all", "answer": "all"},
                 ]},
            ],
            "dom": [
                {"id": f"{language_id}_6_1", "title": "Selecting Elements", "description": "Query the DOM", "xp": 35, "unit": 6,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Select by ID?", "options": ["getElementById", "querySelector", "getElement", "findById"], "correct": 0},
                     {"type": "code", "question": "Select element with class 'btn'", "starter": "", "solution": "const btn = document.querySelector('.btn');", "hint": "Use CSS selector syntax"},
                     {"type": "fill_blank", "question": "document.___('#myId')", "answer": "querySelector"},
                 ]},
                {"id": f"{language_id}_6_2", "title": "Modifying Elements", "description": "Change content and styles", "xp": 35, "unit": 6,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Change text content?", "options": ["textContent", "innerHTML", "text", "value"], "correct": 0},
                     {"type": "code", "question": "Change paragraph text to 'Hello'", "starter": "const p = document.querySelector('p');\n", "solution": "const p = document.querySelector('p');\np.textContent = 'Hello';", "hint": "element.textContent = 'text'"},
                     {"type": "fill_blank", "question": "el.style.___ = 'red';", "answer": "color"},
                 ]},
                {"id": f"{language_id}_6_3", "title": "Event Listeners", "description": "Handle user actions", "xp": 40, "unit": 6,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Add click handler?", "options": ["addEventListener", "onClick", "onEvent", "clickHandler"], "correct": 0},
                     {"type": "code", "question": "Add click listener that logs 'Clicked!'", "starter": "const btn = document.querySelector('button');\n", "solution": "const btn = document.querySelector('button');\nbtn.addEventListener('click', () => {\n    console.log('Clicked!');\n});", "hint": "addEventListener('event', callback)"},
                     {"type": "fill_blank", "question": "btn.___('click', handler)", "answer": "addEventListener"},
                 ]},
                {"id": f"{language_id}_6_4", "title": "Creating Elements", "description": "Dynamic DOM creation", "xp": 40, "unit": 6,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Create new div?", "options": ["createElement('div')", "new Element('div')", "createDiv()", "addElement('div')"], "correct": 0},
                     {"type": "code", "question": "Create li element and append to ul", "starter": "const ul = document.querySelector('ul');\n", "solution": "const ul = document.querySelector('ul');\nconst li = document.createElement('li');\nli.textContent = 'Item';\nul.appendChild(li);", "hint": "createElement then appendChild"},
                     {"type": "fill_blank", "question": "parent.___(child)", "answer": "appendChild"},
                 ]},
                {"id": f"{language_id}_6_5", "title": "Forms", "description": "Handle form data", "xp": 45, "unit": 6,
                 "exercises": [
                     {"type": "multiple_choice", "question": "Get input value?", "options": ["input.value", "input.text", "input.content", "input.data"], "correct": 0},
                     {"type": "code", "question": "Prevent form submit and log input value", "starter": "const form = document.querySelector('form');\nconst input = document.querySelector('input');\n", "solution": "const form = document.querySelector('form');\nconst input = document.querySelector('input');\nform.addEventListener('submit', (e) => {\n    e.preventDefault();\n    console.log(input.value);\n});", "hint": "e.preventDefault() stops submit"},
                     {"type": "fill_blank", "question": "e.___()  // stop default action", "answer": "preventDefault"},
                 ]},
            ],
        }
    }
    
    # Get language-specific lessons or generate generic ones
    if language_id in lesson_templates:
        lessons = []
        for category, category_lessons in lesson_templates[language_id].items():
            lessons.extend(category_lessons)
        return lessons
    
    # Generate generic lessons for other languages
    generic_lessons = []
    units = [
        ("Basics", ["Hello World", "Variables", "Data Types", "Comments", "Basic I/O"]),
        ("Control Flow", ["If Statements", "Else & Elif", "Switch/Match", "For Loops", "While Loops"]),
        ("Functions", ["Defining Functions", "Parameters", "Return Values", "Scope", "Recursion"]),
        ("Data Structures", ["Arrays/Lists", "Strings", "Dictionaries/Maps", "Sets", "Tuples"]),
        ("OOP", ["Classes", "Objects", "Inheritance", "Encapsulation", "Polymorphism"]),
        ("Advanced", ["Error Handling", "File I/O", "Modules", "Libraries", "Best Practices"]),
    ]
    
    lesson_id = 1
    for unit_num, (unit_name, topics) in enumerate(units, 1):
        for topic in topics:
            generic_lessons.append({
                "id": f"{language_id}_{unit_num}_{lesson_id}",
                "title": topic,
                "description": f"Learn about {topic.lower()} in {language_id}",
                "xp": 10 + (unit_num * 5) + (lesson_id * 2),
                "unit": unit_num,
                "exercises": [
                    {"type": "multiple_choice", "question": f"What is the concept of {topic.lower()}?", 
                     "options": ["Fundamental concept", "Advanced topic", "Not important", "Optional"], "correct": 0},
                    {"type": "code", "question": f"Write a basic example of {topic.lower()}", 
                     "starter": f"// Write your {topic.lower()} code here\n", 
                     "solution": f"// Example {topic.lower()} code",
                     "hint": f"Think about how {topic.lower()} works"},
                    {"type": "fill_blank", "question": f"Complete this {topic.lower()} example: ___", "answer": "code"},
                ]
            })
            lesson_id += 1
    
    return generic_lessons

# Pre-generate lessons for all languages  
LESSONS_CACHE = {lang["id"]: generate_lessons(lang["id"]) for lang in LANGUAGES}

# ============== BADGES ==============

BADGES = [
    {"id": "first_lesson", "name": "First Steps", "description": "Complete your first lesson", "icon": "footsteps"},
    {"id": "streak_3", "name": "On Fire!", "description": "3 day streak", "icon": "flame"},
    {"id": "streak_7", "name": "Week Warrior", "description": "7 day streak", "icon": "calendar"},
    {"id": "streak_30", "name": "Monthly Master", "description": "30 day streak", "icon": "trophy"},
    {"id": "xp_100", "name": "Century Club", "description": "Earn 100 XP", "icon": "star"},
    {"id": "xp_500", "name": "XP Hunter", "description": "Earn 500 XP", "icon": "medal"},
    {"id": "xp_1000", "name": "XP Legend", "description": "Earn 1000 XP", "icon": "ribbon"},
    {"id": "perfect_lesson", "name": "Perfectionist", "description": "100% on a lesson", "icon": "checkmark-circle"},
    {"id": "polyglot", "name": "Polyglot", "description": "Study 3 languages", "icon": "language"},
    {"id": "night_owl", "name": "Night Owl", "description": "Study after midnight", "icon": "moon"},
    {"id": "early_bird", "name": "Early Bird", "description": "Study before 6 AM", "icon": "sunny"},
    {"id": "social_butterfly", "name": "Social Butterfly", "description": "Add 5 friends", "icon": "people"},
]

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        session = await db.sessions.find_one({"token": token})
        if not session:
            return None
        user = await db.users.find_one({"id": session["user_id"]})
        return user
    except:
        return None

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register")
async def register(user: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
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
        "last_activity": None,
        "badges": [],
        "friends": [],
        "friend_requests": [],
        "languages_studied": [],
        "created_at": datetime.utcnow().isoformat(),
    }
    await db.users.insert_one(user_dict)
    
    # Create session
    token = generate_token()
    await db.sessions.insert_one({"token": token, "user_id": user_dict["id"]})
    
    return {"token": token, "user": UserResponse(**user_dict)}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or user["password"] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update streak
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
    # Refill hearts if new day
    user["hearts"] = user.get("max_hearts", 5)
    
    await db.users.update_one({"id": user["id"]}, {"$set": user})
    
    # Create session
    token = generate_token()
    await db.sessions.insert_one({"token": token, "user_id": user["id"]})
    
    return {"token": token, "user": UserResponse(**user)}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(**user)

@api_router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    await db.sessions.delete_one({"token": credentials.credentials})
    return {"message": "Logged out"}

# ============== LANGUAGE ROUTES ==============

@api_router.get("/languages")
async def get_languages():
    return LANGUAGES

@api_router.get("/languages/{language_id}/lessons")
async def get_lessons(language_id: str, request: Request):
    if language_id not in LESSONS_CACHE:
        raise HTTPException(status_code=404, detail="Language not found")
    
    lessons = LESSONS_CACHE[language_id]
    
    # Try to get user for progress tracking
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
    
    # Add completion status to lessons
    result = []
    for lesson in lessons:
        lesson_copy = lesson.copy()
        lesson_copy["completed"] = lesson["id"] in completed_ids
        # Remove exercises from list view for smaller response
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
    # Find the lesson
    if answer.language not in LESSONS_CACHE:
        raise HTTPException(status_code=404, detail="Language not found")
    
    lesson = None
    for l in LESSONS_CACHE[answer.language]:
        if l["id"] == answer.lesson_id:
            lesson = l
            break
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Calculate score
    exercises = lesson.get("exercises", [])
    correct = 0
    for i, ex in enumerate(exercises):
        if i < len(answer.answers):
            user_answer = answer.answers[i]
            if ex["type"] == "multiple_choice" and user_answer.get("selected") == ex.get("correct"):
                correct += 1
            elif ex["type"] == "code":
                # Simple validation - check if answer contains key parts
                user_code = user_answer.get("code", "").strip().lower()
                solution = ex.get("solution", "").strip().lower()
                if user_code and (user_code in solution or solution in user_code or len(user_code) > 5):
                    correct += 1
            elif ex["type"] == "fill_blank":
                user_fill = user_answer.get("answer", "").strip().lower()
                expected = ex.get("answer", "").strip().lower()
                if user_fill == expected:
                    correct += 1
    
    total = len(exercises)
    score = int((correct / total) * 100) if total > 0 else 100
    xp_earned = lesson.get("xp", 10)
    
    # Reduce XP for incorrect answers
    if score < 100:
        xp_earned = int(xp_earned * (score / 100))
    
    # Update hearts if wrong answers
    hearts_lost = total - correct
    new_hearts = max(0, user.get("hearts", 5) - hearts_lost)
    
    # Check if already completed
    existing = await db.progress.find_one({
        "user_id": user["id"],
        "language": answer.language,
        "lesson_id": answer.lesson_id
    })
    
    if not existing:
        # First time completing
        await db.progress.insert_one({
            "user_id": user["id"],
            "language": answer.language,
            "lesson_id": answer.lesson_id,
            "completed": True,
            "score": score,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        # Update user XP and level
        new_xp = user.get("xp", 0) + xp_earned
        new_level = 1 + (new_xp // 100)  # Level up every 100 XP
        
        # Update languages studied
        languages_studied = user.get("languages_studied", [])
        if answer.language not in languages_studied:
            languages_studied.append(answer.language)
        
        # Check for badges
        badges = user.get("badges", [])
        
        # First lesson badge
        if "first_lesson" not in badges:
            badges.append("first_lesson")
        
        # Perfect lesson badge
        if score == 100 and "perfect_lesson" not in badges:
            badges.append("perfect_lesson")
        
        # XP badges
        if new_xp >= 100 and "xp_100" not in badges:
            badges.append("xp_100")
        if new_xp >= 500 and "xp_500" not in badges:
            badges.append("xp_500")
        if new_xp >= 1000 and "xp_1000" not in badges:
            badges.append("xp_1000")
        
        # Polyglot badge
        if len(languages_studied) >= 3 and "polyglot" not in badges:
            badges.append("polyglot")
        
        # Streak badges
        streak = user.get("streak", 0)
        if streak >= 3 and "streak_3" not in badges:
            badges.append("streak_3")
        if streak >= 7 and "streak_7" not in badges:
            badges.append("streak_7")
        if streak >= 30 and "streak_30" not in badges:
            badges.append("streak_30")
        
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "xp": new_xp,
                "level": new_level,
                "hearts": new_hearts,
                "badges": badges,
                "languages_studied": languages_studied,
                "last_activity": datetime.utcnow().isoformat()
            }}
        )
        
        return {
            "score": score,
            "xp_earned": xp_earned,
            "new_xp": new_xp,
            "new_level": new_level,
            "hearts": new_hearts,
            "new_badges": badges,
            "correct": correct,
            "total": total
        }
    else:
        # Already completed, just update score if better
        if score > existing.get("score", 0):
            await db.progress.update_one(
                {"_id": existing["_id"]},
                {"$set": {"score": score}}
            )
        
        return {
            "score": score,
            "xp_earned": 0,  # No XP for repeat
            "new_xp": user.get("xp", 0),
            "new_level": user.get("level", 1),
            "hearts": new_hearts,
            "new_badges": user.get("badges", []),
            "correct": correct,
            "total": total,
            "already_completed": True
        }

@api_router.get("/progress/{language_id}")
async def get_language_progress(language_id: str, request: Request):
    total_lessons = len(LESSONS_CACHE.get(language_id, []))
    completed = 0
    progress_list = []
    
    # Try to get user for progress tracking
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
                # Remove MongoDB ObjectId to make it JSON serializable
                progress_list = []
                for p in progress:
                    p_dict = dict(p)
                    p_dict.pop("_id", None)  # Remove ObjectId
                    progress_list.append(p_dict)
                completed = len([p for p in progress if p.get("completed")])
    
    return {
        "total_lessons": total_lessons,
        "completed_lessons": completed,
        "progress_percent": int((completed / total_lessons) * 100) if total_lessons > 0 else 0,
        "lessons": progress_list
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
    
    # Check if already friends
    if friend["id"] in user.get("friends", []):
        raise HTTPException(status_code=400, detail="Already friends")
    
    # Add to friends list (mutual)
    await db.users.update_one(
        {"id": user["id"]},
        {"$addToSet": {"friends": friend["id"]}}
    )
    await db.users.update_one(
        {"id": friend["id"]},
        {"$addToSet": {"friends": user["id"]}}
    )
    
    # Check for social badge
    updated_user = await db.users.find_one({"id": user["id"]})
    friends_count = len(updated_user.get("friends", []))
    if friends_count >= 5 and "social_butterfly" not in updated_user.get("badges", []):
        await db.users.update_one(
            {"id": user["id"]},
            {"$addToSet": {"badges": "social_butterfly"}}
        )
    
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

# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {"message": "Codero API - Learn to code!"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
