#!/usr/bin/env python3
"""Debug test to understand the progress/complete behavior"""

import requests
import json
from datetime import datetime

BASE_URL = "https://codero-stack.preview.emergentagent.com/api"

# Register a new user
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
user_data = {
    "username": f"debugtest_{timestamp}",
    "email": f"debugtest_{timestamp}@codero.com",
    "password": "test123"
}

print("Registering user...")
response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
print(f"Register status: {response.status_code}")
data = response.json()
token = data["token"]
user = data["user"]
print(f"User XP: {user['xp']}, Gems: {user['gems']}, Hearts: {user['hearts']}")

headers = {"Authorization": f"Bearer {token}"}

# Get first Python lesson
print("\nGetting Python lessons...")
response = requests.get(f"{BASE_URL}/languages/python/lessons", headers=headers)
lessons = response.json()
first_lesson = lessons[0]
print(f"First lesson: {first_lesson['id']} - {first_lesson['title']}")
print(f"Exercises in lesson: {len(first_lesson.get('exercises', []))}")

# Complete lesson with ALL 10 answers (all correct)
print("\nCompleting lesson with 10 correct answers...")
lesson_completion = {
    "lesson_id": first_lesson["id"],
    "language": "python",
    "answers": [
        {"question_index": i, "user_answer": "correct", "correct": True, "selected": 0}
        for i in range(10)
    ],
    "time_taken": 45,
    "practice_mode": False
}

response = requests.post(f"{BASE_URL}/progress/complete", json=lesson_completion, headers=headers)
print(f"Complete status: {response.status_code}")
completion_data = response.json()
print(f"Completion response: {json.dumps(completion_data, indent=2)}")

# Get user profile
print("\nGetting user profile...")
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
user = response.json()
print(f"User XP: {user['xp']}, Gems: {user['gems']}, Hearts: {user['hearts']}")
print(f"Total lessons completed: {user.get('total_lessons_completed', 0)}")
print(f"Badges: {user.get('badges', [])}")

# Try completing the same lesson again
print("\n\nCompleting the SAME lesson again...")
response = requests.post(f"{BASE_URL}/progress/complete", json=lesson_completion, headers=headers)
print(f"Complete status: {response.status_code}")
completion_data = response.json()
print(f"Completion response: {json.dumps(completion_data, indent=2)}")

# Get user profile again
print("\nGetting user profile after 2nd completion...")
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
user = response.json()
print(f"User XP: {user['xp']}, Gems: {user['gems']}, Hearts: {user['hearts']}")
print(f"Total lessons completed: {user.get('total_lessons_completed', 0)}")
