#!/usr/bin/env python3
"""
Codero Backend Health Test - Auth/Login/Data Persistence
Tests all critical backend functionality after system startup
"""

import requests
import json
from datetime import datetime
import sys

# Backend URL from frontend/.env
BASE_URL = "https://codero-stack.preview.emergentagent.com/api"

# Test results tracking
tests_passed = 0
tests_failed = 0
test_results = []

def log_test(name, passed, details=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        status = "✅ PASS"
    else:
        tests_failed += 1
        status = "❌ FAIL"
    
    result = f"{status} - {name}"
    if details:
        result += f"\n    {details}"
    print(result)
    test_results.append({"name": name, "passed": passed, "details": details})

def test_1_api_health():
    """Test 1: Verify basic API health/root endpoint"""
    print("\n=== Test 1: API Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "Codero" in data["message"]:
                log_test("API Root Endpoint", True, f"Response: {data['message']}")
                return True
            else:
                log_test("API Root Endpoint", False, f"Unexpected response: {data}")
                return False
        else:
            log_test("API Root Endpoint", False, f"Status: {response.status_code}, Body: {response.text}")
            return False
    except Exception as e:
        log_test("API Root Endpoint", False, f"Exception: {str(e)}")
        return False

def test_2_languages_endpoint():
    """Test 2: Verify /api/languages returns data"""
    print("\n=== Test 2: Languages Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/languages", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                log_test("Languages Endpoint", True, f"Found {len(data)} languages")
                return data
            else:
                log_test("Languages Endpoint", False, f"Empty or invalid response: {data}")
                return None
        else:
            log_test("Languages Endpoint", False, f"Status: {response.status_code}")
            return None
    except Exception as e:
        log_test("Languages Endpoint", False, f"Exception: {str(e)}")
        return None

def test_3_register_user():
    """Test 3: Register a fresh timestamped user"""
    print("\n=== Test 3: User Registration ===")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    user_data = {
        "username": f"healthtest_{timestamp}",
        "email": f"healthtest_{timestamp}@codero.com",
        "password": "test123secure"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Verify token exists
            if "token" not in data:
                log_test("User Registration - Token", False, "No token in response")
                return None
            
            # Verify user object exists
            if "user" not in data:
                log_test("User Registration - User Object", False, "No user object in response")
                return None
            
            user = data["user"]
            
            # Verify default values
            checks = []
            if user.get("gems") == 10:
                checks.append("✓ gems=10")
            else:
                checks.append(f"✗ gems={user.get('gems')} (expected 10)")
            
            if user.get("hearts") == 5:
                checks.append("✓ hearts=5")
            else:
                checks.append(f"✗ hearts={user.get('hearts')} (expected 5)")
            
            if "settings" in user and isinstance(user["settings"], dict):
                settings = user["settings"]
                if "theme" in settings and "font_size" in settings:
                    checks.append("✓ settings present")
                else:
                    checks.append("✗ settings incomplete")
            else:
                checks.append("✗ settings missing")
            
            if user.get("xp") == 0:
                checks.append("✓ xp=0")
            else:
                checks.append(f"✗ xp={user.get('xp')} (expected 0)")
            
            all_passed = all("✓" in check for check in checks)
            log_test("User Registration", all_passed, ", ".join(checks))
            
            if all_passed:
                return {
                    "token": data["token"],
                    "user": user,
                    "credentials": user_data
                }
            else:
                return None
        else:
            log_test("User Registration", False, f"Status: {response.status_code}, Body: {response.text}")
            return None
    except Exception as e:
        log_test("User Registration", False, f"Exception: {str(e)}")
        return None

def test_4_login_user(credentials):
    """Test 4: Login with the registered user"""
    print("\n=== Test 4: User Login ===")
    login_data = {
        "email": credentials["email"],
        "password": credentials["password"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Check for ObjectId serialization error
            response_text = response.text
            if "ObjectId" in response_text or "_id" in response_text:
                log_test("Login - No ObjectId Error", False, "ObjectId found in response (serialization bug)")
                return None
            
            # Verify token and user
            if "token" not in data:
                log_test("Login - Token", False, "No token in response")
                return None
            
            if "user" not in data:
                log_test("Login - User Object", False, "No user object in response")
                return None
            
            log_test("User Login", True, "Login successful, token and user returned")
            return {
                "token": data["token"],
                "user": data["user"]
            }
        else:
            log_test("User Login", False, f"Status: {response.status_code}, Body: {response.text}")
            return None
    except Exception as e:
        log_test("User Login", False, f"Exception: {str(e)}")
        return None

def test_5_protected_endpoint(token):
    """Test 5: Access protected endpoint /api/auth/me"""
    print("\n=== Test 5: Protected Endpoint Access ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "email" in data and "username" in data:
                log_test("Protected Endpoint (/auth/me)", True, f"User: {data.get('username')}")
                return data
            else:
                log_test("Protected Endpoint (/auth/me)", False, f"Invalid user data: {data}")
                return None
        else:
            log_test("Protected Endpoint (/auth/me)", False, f"Status: {response.status_code}")
            return None
    except Exception as e:
        log_test("Protected Endpoint (/auth/me)", False, f"Exception: {str(e)}")
        return None

def test_6_unauthorized_access():
    """Test 6: Verify unauthorized access is rejected"""
    print("\n=== Test 6: Unauthorized Access Check ===")
    
    # Try accessing protected endpoint without token
    try:
        response = requests.get(f"{BASE_URL}/auth/me", timeout=10)
        if response.status_code == 401 or response.status_code == 403:
            log_test("Unauthorized Access Rejected", True, f"Correctly rejected with status {response.status_code}")
            return True
        else:
            log_test("Unauthorized Access Rejected", False, f"Expected 401/403, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Unauthorized Access Rejected", False, f"Exception: {str(e)}")
        return False

def test_7_settings_persistence(token, credentials):
    """Test 7: Update settings and verify persistence"""
    print("\n=== Test 7: Settings Persistence ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Update settings
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
    
    try:
        # PUT settings
        response = requests.put(f"{BASE_URL}/settings", json=new_settings, headers=headers, timeout=10)
        if response.status_code != 200:
            log_test("Settings Update (PUT)", False, f"Status: {response.status_code}")
            return False
        
        log_test("Settings Update (PUT)", True, "Settings updated successfully")
        
        # Step 2: GET settings to verify
        response = requests.get(f"{BASE_URL}/settings", headers=headers, timeout=10)
        if response.status_code != 200:
            log_test("Settings Fetch (GET)", False, f"Status: {response.status_code}")
            return False
        
        fetched_settings = response.json()
        if fetched_settings.get("theme") == "light" and fetched_settings.get("font_size") == "large":
            log_test("Settings Fetch (GET)", True, "Settings retrieved correctly")
        else:
            log_test("Settings Fetch (GET)", False, f"Settings mismatch: {fetched_settings}")
            return False
        
        # Step 3: Login again and verify settings persisted in MongoDB
        login_data = {
            "email": credentials["email"],
            "password": credentials["password"]
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        if response.status_code != 200:
            log_test("Settings Persistence (Re-login)", False, f"Login failed: {response.status_code}")
            return False
        
        user_data = response.json()
        user_settings = user_data.get("user", {}).get("settings", {})
        
        if user_settings.get("theme") == "light" and user_settings.get("font_size") == "large":
            log_test("Settings Persistence (MongoDB)", True, "Settings persisted after re-login")
            return True
        else:
            log_test("Settings Persistence (MongoDB)", False, f"Settings not persisted: {user_settings}")
            return False
            
    except Exception as e:
        log_test("Settings Persistence", False, f"Exception: {str(e)}")
        return False

def test_8_progress_data_saving(token):
    """Test 8: Complete a lesson and verify progress persistence"""
    print("\n=== Test 8: Progress/Data Saving ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Step 1: Get lessons for Python
        response = requests.get(f"{BASE_URL}/languages/python/lessons", headers=headers, timeout=10)
        if response.status_code != 200:
            log_test("Get Lessons", False, f"Status: {response.status_code}")
            return False
        
        lessons = response.json()
        if not lessons or len(lessons) == 0:
            log_test("Get Lessons", False, "No lessons found")
            return False
        
        first_lesson = lessons[0]
        lesson_id = first_lesson.get("id")
        log_test("Get Lessons", True, f"Found lesson: {lesson_id}")
        
        # Step 2: Complete the lesson with answers
        lesson_completion = {
            "lesson_id": lesson_id,
            "language": "python",
            "answers": [
                {"question_index": 0, "user_answer": "print()", "correct": True},
                {"question_index": 1, "user_answer": "print('Hello')", "correct": True},
                {"question_index": 2, "user_answer": "print", "correct": True},
            ],
            "time_taken": 45,
            "practice_mode": False
        }
        
        response = requests.post(f"{BASE_URL}/progress/complete", json=lesson_completion, headers=headers, timeout=10)
        if response.status_code != 200:
            log_test("Complete Lesson", False, f"Status: {response.status_code}, Body: {response.text}")
            return False
        
        completion_data = response.json()
        xp_earned = completion_data.get("xp_earned", 0)
        gems = completion_data.get("gems", 0)
        
        log_test("Complete Lesson", True, f"XP earned: {xp_earned}, Gems: {gems}")
        
        # Step 3: Fetch progress to verify it was saved
        response = requests.get(f"{BASE_URL}/progress/python", headers=headers, timeout=10)
        if response.status_code != 200:
            log_test("Fetch Progress", False, f"Status: {response.status_code}")
            return False
        
        progress_data = response.json()
        completed_lessons = progress_data.get("completed_lessons", 0)
        
        if completed_lessons >= 1:
            log_test("Progress Persistence", True, f"Completed lessons: {completed_lessons}")
        else:
            log_test("Progress Persistence", False, f"No completed lessons found: {progress_data}")
            return False
        
        # Step 4: Fetch user profile to verify XP/gems persisted
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
        if response.status_code != 200:
            log_test("Profile Stats Persistence", False, f"Status: {response.status_code}")
            return False
        
        user = response.json()
        user_xp = user.get("xp", 0)
        user_gems = user.get("gems", 0)
        
        if user_xp > 0:
            log_test("Profile Stats Persistence", True, f"XP: {user_xp}, Gems: {user_gems}")
            return True
        else:
            log_test("Profile Stats Persistence", False, f"XP not updated: {user}")
            return False
            
    except Exception as e:
        log_test("Progress/Data Saving", False, f"Exception: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("CODERO BACKEND HEALTH TEST - Auth/Login/Data Persistence")
    print("=" * 70)
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Test 1: API Health
    test_1_api_health()
    
    # Test 2: Languages endpoint
    languages = test_2_languages_endpoint()
    
    # Test 3: Register user
    registration = test_3_register_user()
    if not registration:
        print("\n❌ CRITICAL: User registration failed. Cannot continue with remaining tests.")
        print_summary()
        sys.exit(1)
    
    token = registration["token"]
    credentials = registration["credentials"]
    
    print(f"\n📝 Test User Created:")
    print(f"   Email: {credentials['email']}")
    print(f"   Password: {credentials['password']}")
    print(f"   Username: {credentials['username']}")
    
    # Test 4: Login
    login_result = test_4_login_user(credentials)
    if login_result:
        token = login_result["token"]  # Use new token from login
    
    # Test 5: Protected endpoint
    test_5_protected_endpoint(token)
    
    # Test 6: Unauthorized access
    test_6_unauthorized_access()
    
    # Test 7: Settings persistence
    test_7_settings_persistence(token, credentials)
    
    # Test 8: Progress/data saving
    test_8_progress_data_saving(token)
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    if tests_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

def print_summary():
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"Success Rate: {(tests_passed / (tests_passed + tests_failed) * 100):.1f}%")
    print("=" * 70)
    
    if tests_failed > 0:
        print("\n❌ FAILED TESTS:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['name']}")
                if result["details"]:
                    print(f"    {result['details']}")
    else:
        print("\n✅ ALL TESTS PASSED!")

if __name__ == "__main__":
    main()
