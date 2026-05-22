#!/usr/bin/env python3
"""
Final Comprehensive Backend Health Test
Covers all scenarios from the review request
"""

import requests
import json
from datetime import datetime
import sys

BASE_URL = "https://codero-stack.preview.emergentagent.com/api"

tests_passed = 0
tests_failed = 0

def log_test(name, passed, details=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        print(f"✅ {name}")
    else:
        tests_failed += 1
        print(f"❌ {name}")
    if details:
        print(f"   {details}")

print("=" * 80)
print("CODERO BACKEND COMPREHENSIVE HEALTH TEST")
print("=" * 80)
print(f"Time: {datetime.now().isoformat()}")
print(f"Backend: {BASE_URL}\n")

# Scenario 1: Basic API health
print("1. Testing API Health & Languages Endpoint")
print("-" * 80)
try:
    resp = requests.get(f"{BASE_URL}/", timeout=10)
    if resp.status_code == 200 and "Codero" in resp.json().get("message", ""):
        log_test("API Root Endpoint", True, resp.json()["message"])
    else:
        log_test("API Root Endpoint", False, f"Status: {resp.status_code}")
except Exception as e:
    log_test("API Root Endpoint", False, str(e))

try:
    resp = requests.get(f"{BASE_URL}/languages", timeout=10)
    if resp.status_code == 200:
        langs = resp.json()
        log_test("Languages Endpoint", True, f"{len(langs)} languages available")
    else:
        log_test("Languages Endpoint", False, f"Status: {resp.status_code}")
except Exception as e:
    log_test("Languages Endpoint", False, str(e))

# Scenario 2: Register fresh timestamped user
print("\n2. Registering Fresh Timestamped User")
print("-" * 80)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
user_data = {
    "username": f"finaltest_{timestamp}",
    "email": f"finaltest_{timestamp}@codero.com",
    "password": "secure123test"
}

try:
    resp = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        token = data["token"]
        user = data["user"]
        
        # Verify defaults
        checks = []
        if user.get("gems") == 10:
            checks.append("gems=10 ✓")
        else:
            checks.append(f"gems={user.get('gems')} ✗")
        
        if user.get("hearts") == 5:
            checks.append("hearts=5 ✓")
        else:
            checks.append(f"hearts={user.get('hearts')} ✗")
        
        if "settings" in user and user["settings"].get("theme"):
            checks.append("settings ✓")
        else:
            checks.append("settings ✗")
        
        all_ok = all("✓" in c for c in checks)
        log_test("User Registration with Defaults", all_ok, ", ".join(checks))
        
        print(f"\n   📝 Test User: {user_data['email']}")
        print(f"   Password: {user_data['password']}")
    else:
        log_test("User Registration", False, f"Status: {resp.status_code}")
        sys.exit(1)
except Exception as e:
    log_test("User Registration", False, str(e))
    sys.exit(1)

# Scenario 3: Login with same user (check no ObjectId error)
print("\n3. Login with Registered User (ObjectId Bug Check)")
print("-" * 80)
try:
    login_data = {"email": user_data["email"], "password": user_data["password"]}
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
    
    if resp.status_code == 200:
        data = resp.json()
        
        # Check for ObjectId serialization error
        if "ObjectId" in resp.text or '"_id"' in resp.text:
            log_test("Login - No ObjectId Error", False, "ObjectId found in response")
        else:
            log_test("Login - No ObjectId Error", True, "Clean JSON response")
        
        if "token" in data and "user" in data:
            token = data["token"]
            log_test("Login - Token & User Returned", True)
        else:
            log_test("Login - Token & User Returned", False, "Missing token or user")
    else:
        log_test("Login", False, f"Status: {resp.status_code}")
except Exception as e:
    log_test("Login", False, str(e))

# Scenario 4: Access protected endpoint
print("\n4. Protected Endpoint Access (/api/auth/me)")
print("-" * 80)
headers = {"Authorization": f"Bearer {token}"}
try:
    resp = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
    if resp.status_code == 200:
        user_profile = resp.json()
        log_test("Protected Endpoint Access", True, f"User: {user_profile.get('username')}")
    else:
        log_test("Protected Endpoint Access", False, f"Status: {resp.status_code}")
except Exception as e:
    log_test("Protected Endpoint Access", False, str(e))

# Scenario 5: Settings persistence
print("\n5. Settings Persistence (PUT → GET → Re-login)")
print("-" * 80)
try:
    # PUT settings
    new_settings = {
        "settings": {
            "theme": "light",
            "font_size": "large",
            "sound_effects": False,
            "notifications": True,
            "high_contrast": True,
            "reduced_motion": False,
            "daily_reminder": True
        }
    }
    resp = requests.put(f"{BASE_URL}/settings", json=new_settings, headers=headers, timeout=10)
    if resp.status_code == 200:
        log_test("Settings Update (PUT)", True)
    else:
        log_test("Settings Update (PUT)", False, f"Status: {resp.status_code}")
    
    # GET settings
    resp = requests.get(f"{BASE_URL}/settings", headers=headers, timeout=10)
    if resp.status_code == 200:
        settings = resp.json()
        if settings.get("theme") == "light" and settings.get("font_size") == "large":
            log_test("Settings Fetch (GET)", True, "Settings match")
        else:
            log_test("Settings Fetch (GET)", False, f"Mismatch: {settings}")
    else:
        log_test("Settings Fetch (GET)", False, f"Status: {resp.status_code}")
    
    # Re-login and check persistence
    login_data = {"email": user_data["email"], "password": user_data["password"]}
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
    if resp.status_code == 200:
        user_after_login = resp.json()["user"]
        user_settings = user_after_login.get("settings", {})
        if user_settings.get("theme") == "light" and user_settings.get("font_size") == "large":
            log_test("Settings Persistence (MongoDB)", True, "Settings persisted after re-login")
        else:
            log_test("Settings Persistence (MongoDB)", False, f"Not persisted: {user_settings}")
        token = resp.json()["token"]  # Update token
        headers = {"Authorization": f"Bearer {token}"}
    else:
        log_test("Settings Persistence", False, f"Re-login failed: {resp.status_code}")
except Exception as e:
    log_test("Settings Persistence", False, str(e))

# Scenario 6: Progress/data saving with actual lesson
print("\n6. Progress/Data Saving (Complete Lesson → Verify Persistence)")
print("-" * 80)
try:
    # Get Python lessons
    resp = requests.get(f"{BASE_URL}/languages/python/lessons", headers=headers, timeout=10)
    if resp.status_code == 200:
        lessons = resp.json()
        if lessons and len(lessons) > 0:
            first_lesson = lessons[0]
            lesson_id = first_lesson["id"]
            log_test("Get Lessons", True, f"Lesson: {lesson_id}")
            
            # Complete lesson with 10 correct answers
            lesson_completion = {
                "lesson_id": lesson_id,
                "language": "python",
                "answers": [
                    {"question_index": i, "selected": 0, "correct": True}
                    for i in range(10)
                ],
                "time_taken": 60,
                "practice_mode": False
            }
            
            resp = requests.post(f"{BASE_URL}/progress/complete", json=lesson_completion, headers=headers, timeout=10)
            if resp.status_code == 200:
                completion = resp.json()
                xp = completion.get("xp_earned", 0)
                gems = completion.get("gems", 0)
                
                # XP should be > 0 for first completion
                if xp > 0:
                    log_test("Lesson Completion (XP Earned)", True, f"XP: {xp}, Gems: {gems}")
                else:
                    # Could be already completed if test ran before
                    if completion.get("already_completed"):
                        log_test("Lesson Completion", True, "Already completed (expected if test re-run)")
                    else:
                        log_test("Lesson Completion", False, f"XP=0 but not marked as completed: {completion}")
            else:
                log_test("Lesson Completion", False, f"Status: {resp.status_code}")
            
            # Verify progress saved
            resp = requests.get(f"{BASE_URL}/progress/python", headers=headers, timeout=10)
            if resp.status_code == 200:
                progress = resp.json()
                completed = progress.get("completed_lessons", 0)
                if completed >= 1:
                    log_test("Progress Persistence", True, f"{completed} lesson(s) completed")
                else:
                    log_test("Progress Persistence", False, f"No completed lessons: {progress}")
            else:
                log_test("Progress Persistence", False, f"Status: {resp.status_code}")
            
            # Verify user stats updated
            resp = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
            if resp.status_code == 200:
                user_profile = resp.json()
                total_lessons = user_profile.get("total_lessons_completed", 0)
                user_xp = user_profile.get("xp", 0)
                user_gems = user_profile.get("gems", 0)
                
                if total_lessons >= 1:
                    log_test("User Stats Persistence", True, f"Lessons: {total_lessons}, XP: {user_xp}, Gems: {user_gems}")
                else:
                    log_test("User Stats Persistence", False, f"No lessons counted: {user_profile}")
            else:
                log_test("User Stats Persistence", False, f"Status: {resp.status_code}")
        else:
            log_test("Get Lessons", False, "No lessons found")
    else:
        log_test("Get Lessons", False, f"Status: {resp.status_code}")
except Exception as e:
    log_test("Progress/Data Saving", False, str(e))

# Scenario 7: Unauthorized access rejection
print("\n7. Unauthorized Access Rejection")
print("-" * 80)
try:
    resp = requests.get(f"{BASE_URL}/auth/me", timeout=10)
    if resp.status_code in [401, 403]:
        log_test("Unauthorized Access Rejected", True, f"Status: {resp.status_code}")
    else:
        log_test("Unauthorized Access Rejected", False, f"Expected 401/403, got {resp.status_code}")
except Exception as e:
    log_test("Unauthorized Access Rejected", False, str(e))

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
total = tests_passed + tests_failed
print(f"Total Tests: {total}")
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"Success Rate: {(tests_passed / total * 100):.1f}%")
print("=" * 80)

if tests_failed == 0:
    print("\n✅ ALL TESTS PASSED - Backend is healthy!")
    sys.exit(0)
else:
    print(f"\n❌ {tests_failed} test(s) failed - Review required")
    sys.exit(1)
