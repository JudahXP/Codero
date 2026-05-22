#!/usr/bin/env python3
"""
Codero V1.7 Phase 1 Backend Testing
Tests all 10 requirements from the review request
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://codero-stack.preview.emergentagent.com/api"

# Test results tracking
test_results = []
failed_tests = []

def log_test(test_name, passed, details=""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{status}: {test_name}"
    if details:
        result += f" - {details}"
    print(result)
    test_results.append({"name": test_name, "passed": passed, "details": details})
    if not passed:
        failed_tests.append({"name": test_name, "details": details})

def test_1_register_fresh_user():
    """Test 1: Register fresh timestamp user with verification code"""
    print("\n=== TEST 1: Fresh User Registration ===")
    
    timestamp = int(time.time())
    username = f"phase1test_{timestamp}"
    email = f"phase1test_{timestamp}@codero.com"
    password = "testpass123"
    
    # Register user
    response = requests.post(f"{BACKEND_URL}/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    
    # Check response
    if response.status_code != 200:
        log_test("1.1 Registration succeeds", False, f"Status {response.status_code}: {response.text}")
        return None, None
    
    data = response.json()
    log_test("1.1 Registration succeeds", True, f"User {username} created")
    
    # Check token and user in response
    has_token = "token" in data
    has_user = "user" in data
    log_test("1.2 Response includes token", has_token, f"Token present: {has_token}")
    log_test("1.3 Response includes user", has_user, f"User present: {has_user}")
    
    if not has_token or not has_user:
        return None, None
    
    token = data["token"]
    user = data["user"]
    
    # Check user defaults
    log_test("1.4 User has gems=10", user.get("gems") == 10, f"Gems: {user.get('gems')}")
    log_test("1.5 User has hearts=5", user.get("hearts") == 5, f"Hearts: {user.get('hearts')}")
    log_test("1.6 User has settings", "settings" in user, f"Settings present: {'settings' in user}")
    
    # Check tutorial lesson available for python
    response = requests.get(f"{BACKEND_URL}/languages/python/lessons", headers={"Authorization": f"Bearer {token}"})
    if response.status_code == 200:
        lessons = response.json()
        tutorial_lessons = [l for l in lessons if "tutorial" in l.get("id", "").lower()]
        log_test("1.7 Python tutorial lessons available", len(tutorial_lessons) > 0, f"Found {len(tutorial_lessons)} tutorial lessons")
    else:
        log_test("1.7 Python tutorial lessons available", False, f"Failed to fetch lessons: {response.status_code}")
    
    # Check verification code was queued (should not be exposed in response)
    code_exposed = "code" in data or "verification_code" in data
    log_test("1.8 Verification code NOT exposed in response", not code_exposed, f"Code exposed: {code_exposed}")
    
    return token, username

def test_2_duplicate_registration(username, email):
    """Test 2: Duplicate username and email registration"""
    print("\n=== TEST 2: Duplicate Registration Errors ===")
    
    # Test duplicate username (case-insensitive)
    response = requests.post(f"{BACKEND_URL}/auth/register", json={
        "username": username.upper(),  # Different case
        "email": f"different_{email}",
        "password": "testpass123"
    })
    
    is_400 = response.status_code == 400
    has_username_message = "username" in response.text.lower() and "taken" in response.text.lower()
    log_test("2.1 Duplicate username returns 400", is_400, f"Status: {response.status_code}")
    log_test("2.2 Duplicate username clear message", has_username_message, f"Message: {response.text[:100]}")
    
    # Test duplicate email
    response = requests.post(f"{BACKEND_URL}/auth/register", json={
        "username": f"different_{username}",
        "email": email,
        "password": "testpass123"
    })
    
    is_400 = response.status_code == 400
    has_email_message = "email" in response.text.lower() and "account" in response.text.lower()
    log_test("2.3 Duplicate email returns 400", is_400, f"Status: {response.status_code}")
    log_test("2.4 Duplicate email clear message", has_email_message, f"Message: {response.text[:100]}")

def test_3_login_email_and_username(username, email, password="testpass123"):
    """Test 3: Login using both email and username"""
    print("\n=== TEST 3: Login with Email and Username ===")
    
    # Login with email
    response = requests.post(f"{BACKEND_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    
    email_login_success = response.status_code == 200
    email_token = response.json().get("token") if email_login_success else None
    log_test("3.1 Login with email succeeds", email_login_success, f"Status: {response.status_code}")
    
    # Login with username
    response = requests.post(f"{BACKEND_URL}/auth/login", json={
        "email": username,  # API accepts username in email field
        "password": password
    })
    
    username_login_success = response.status_code == 200
    username_token = response.json().get("token") if username_login_success else None
    log_test("3.2 Login with username succeeds", username_login_success, f"Status: {response.status_code}")
    
    # Both should work for same user
    both_work = email_login_success and username_login_success
    log_test("3.3 Both login methods work", both_work, f"Email: {email_login_success}, Username: {username_login_success}")
    
    return email_token or username_token

def test_4_admin_behavior():
    """Test 4: Admin user behavior"""
    print("\n=== TEST 4: Admin User Behavior ===")
    
    admin_email = "judahxpbusiness@gmail.com"
    admin_username = "Judahxp"
    admin_password = "admin123"
    
    # Try to register admin if doesn't exist (will fail if exists, that's ok)
    requests.post(f"{BACKEND_URL}/auth/register", json={
        "username": admin_username,
        "email": admin_email,
        "password": admin_password
    })
    
    # Login as admin
    response = requests.post(f"{BACKEND_URL}/auth/login", json={
        "email": admin_email,
        "password": admin_password
    })
    
    if response.status_code != 200:
        log_test("4.1 Admin login", False, f"Status {response.status_code}: {response.text}")
        return
    
    token = response.json().get("token")
    log_test("4.1 Admin login succeeds", True, "Admin logged in")
    
    # Check /auth/me
    response = requests.get(f"{BACKEND_URL}/auth/me", headers={"Authorization": f"Bearer {token}"})
    
    if response.status_code != 200:
        log_test("4.2 /auth/me accessible", False, f"Status: {response.status_code}")
        return
    
    user = response.json()
    is_admin = user.get("is_admin") == True
    admin_tag = user.get("admin_tag") == "ADMIN"
    
    log_test("4.2 /auth/me returns is_admin=true", is_admin, f"is_admin: {user.get('is_admin')}")
    log_test("4.3 /auth/me returns admin_tag=ADMIN", admin_tag, f"admin_tag: {user.get('admin_tag')}")

def test_5_tutorial_gating(token):
    """Test 5: Tutorial gating enforcement"""
    print("\n=== TEST 5: Tutorial Gating ===")
    
    # Get python lessons
    response = requests.get(f"{BACKEND_URL}/languages/python/lessons", headers={"Authorization": f"Bearer {token}"})
    
    if response.status_code != 200:
        log_test("5.1 Fetch python lessons", False, f"Status: {response.status_code}")
        return
    
    lessons = response.json()
    tutorial_lesson = None
    non_tutorial_lesson = None
    
    for lesson in lessons:
        lesson_id = lesson.get("id", "")
        if "tutorial" in lesson_id.lower():
            tutorial_lesson = lesson
        elif not non_tutorial_lesson:
            non_tutorial_lesson = lesson
    
    if not tutorial_lesson or not non_tutorial_lesson:
        log_test("5.1 Find tutorial and non-tutorial lessons", False, f"Tutorial: {tutorial_lesson is not None}, Non-tutorial: {non_tutorial_lesson is not None}")
        return
    
    log_test("5.1 Find tutorial and non-tutorial lessons", True, f"Tutorial: {tutorial_lesson['id']}, Non-tutorial: {non_tutorial_lesson['id']}")
    
    # Try to complete non-tutorial lesson BEFORE tutorial
    response = requests.post(f"{BACKEND_URL}/progress/complete", 
        headers={"Authorization": f"Bearer {token}"},
        json={
            "lesson_id": non_tutorial_lesson["id"],
            "language": "python",
            "answers": [{"selected": 0}] * 10  # Dummy answers
        }
    )
    
    is_403 = response.status_code == 403
    has_tutorial_message = "tutorial" in response.text.lower()
    log_test("5.2 Non-tutorial before tutorial returns 403", is_403, f"Status: {response.status_code}")
    log_test("5.3 Error message mentions tutorial", has_tutorial_message, f"Message: {response.text[:100]}")
    
    # Complete tutorial lesson
    response = requests.post(f"{BACKEND_URL}/progress/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "lesson_id": tutorial_lesson["id"],
            "language": "python",
            "answers": [{"selected": 0}] * 10  # Dummy answers
        }
    )
    
    tutorial_completed = response.status_code == 200
    log_test("5.4 Tutorial lesson completion succeeds", tutorial_completed, f"Status: {response.status_code}")
    
    # Now try non-tutorial lesson again
    response = requests.post(f"{BACKEND_URL}/progress/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "lesson_id": non_tutorial_lesson["id"],
            "language": "python",
            "answers": [{"selected": 0}] * 10
        }
    )
    
    non_tutorial_allowed = response.status_code == 200
    log_test("5.5 Non-tutorial allowed after tutorial", non_tutorial_allowed, f"Status: {response.status_code}")

def test_6_wrong_answer_review(token):
    """Test 6: Wrong answer review system"""
    print("\n=== TEST 6: Wrong Answer Review ===")
    
    # Get a lesson
    response = requests.get(f"{BACKEND_URL}/languages/python/lessons", headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        log_test("6.1 Fetch lessons", False, f"Status: {response.status_code}")
        return
    
    lessons = response.json()
    # Find a completed tutorial lesson
    tutorial_lesson = next((l for l in lessons if "tutorial" in l.get("id", "").lower()), None)
    if not tutorial_lesson:
        log_test("6.1 Find tutorial lesson", False, "No tutorial lesson found")
        return
    
    # Get lesson details
    response = requests.get(f"{BACKEND_URL}/languages/python/lessons/{tutorial_lesson['id']}", 
                           headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        log_test("6.1 Fetch lesson details", False, f"Status: {response.status_code}")
        return
    
    lesson = response.json()
    exercises = lesson.get("exercises", [])
    
    if not exercises:
        log_test("6.1 Lesson has exercises", False, "No exercises found")
        return
    
    # Submit with WRONG answers
    wrong_answers = []
    for i, ex in enumerate(exercises[:3]):  # Test first 3 exercises
        if ex.get("type") == "multiple_choice":
            # Pick wrong answer (not the correct one)
            correct = ex.get("correct", 0)
            wrong = (correct + 1) % len(ex.get("options", [0, 1]))
            wrong_answers.append({"selected": wrong})
        elif ex.get("type") == "code":
            wrong_answers.append({"code": "wrong code"})
        elif ex.get("type") == "fill_blank":
            wrong_answers.append({"answer": "wrong"})
        else:
            wrong_answers.append({"selected": 0})
    
    # Complete lesson with wrong answers
    response = requests.post(f"{BACKEND_URL}/progress/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "lesson_id": tutorial_lesson["id"],
            "language": "python",
            "answers": wrong_answers,
            "practice_mode": True  # Use practice mode to avoid affecting progress
        }
    )
    
    if response.status_code != 200:
        log_test("6.1 Submit with wrong answers", False, f"Status: {response.status_code}")
        return
    
    data = response.json()
    has_wrong_review = "wrong_review" in data
    log_test("6.1 Response includes wrong_review", has_wrong_review, f"wrong_review present: {has_wrong_review}")
    
    if has_wrong_review:
        wrong_review = data["wrong_review"]
        if len(wrong_review) > 0:
            first_review = wrong_review[0]
            has_question = "question" in first_review
            has_expected = "expected_answer" in first_review
            has_explanation = "explanation" in first_review
            
            log_test("6.2 wrong_review has question", has_question, f"Question present: {has_question}")
            log_test("6.3 wrong_review has expected_answer", has_expected, f"Expected present: {has_expected}")
            log_test("6.4 wrong_review has explanation", has_explanation, f"Explanation present: {has_explanation}")
        else:
            log_test("6.2 wrong_review has items", False, "wrong_review is empty")
    
    # Check wrong_answers collection endpoint
    response = requests.get(f"{BACKEND_URL}/review/wrong-answers", headers={"Authorization": f"Bearer {token}"})
    
    if response.status_code != 200:
        log_test("6.5 GET /review/wrong-answers accessible", False, f"Status: {response.status_code}")
        return
    
    wrong_answers_list = response.json()
    has_saved_items = len(wrong_answers_list) > 0
    log_test("6.5 GET /review/wrong-answers returns saved items", has_saved_items, f"Found {len(wrong_answers_list)} items")

def test_7_fix_broken_code_starter(token):
    """Test 7: Fix-broken-code exercise has empty starter"""
    print("\n=== TEST 7: Fix-Broken-Code Empty Starter ===")
    
    # Get python lessons
    response = requests.get(f"{BACKEND_URL}/languages/python/lessons", headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        log_test("7.1 Fetch lessons", False, f"Status: {response.status_code}")
        return
    
    lessons = response.json()
    
    # Find a lesson with fix_broken_code exercise
    fix_broken_found = False
    for lesson_summary in lessons[:10]:  # Check first 10 lessons
        response = requests.get(f"{BACKEND_URL}/languages/python/lessons/{lesson_summary['id']}", 
                               headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            lesson = response.json()
            exercises = lesson.get("exercises", [])
            
            for ex in exercises:
                if ex.get("type") == "fix_broken_code":
                    fix_broken_found = True
                    starter = ex.get("starter", "NOT_EMPTY")
                    is_empty = starter == ""
                    log_test("7.1 fix_broken_code exercise found", True, f"Lesson: {lesson['id']}")
                    log_test("7.2 fix_broken_code starter is empty", is_empty, f"Starter: '{starter}'")
                    return
    
    if not fix_broken_found:
        log_test("7.1 fix_broken_code exercise found", False, "No fix_broken_code exercise found in first 10 lessons")

def test_8_friends_system(token1, username1):
    """Test 8: Friends system with search, add, and favorite"""
    print("\n=== TEST 8: Friends System ===")
    
    # Create a second user for friend testing
    timestamp = int(time.time())
    username2 = f"friend_{timestamp}"
    email2 = f"friend_{timestamp}@codero.com"
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json={
        "username": username2,
        "email": email2,
        "password": "testpass123"
    })
    
    if response.status_code != 200:
        log_test("8.1 Create second user", False, f"Status: {response.status_code}")
        return
    
    token2 = response.json().get("token")
    log_test("8.1 Create second user", True, f"User: {username2}")
    
    # Test friend search suggestions (case-insensitive)
    search_query = username2[:4].upper()  # Search with uppercase
    response = requests.get(f"{BACKEND_URL}/friends/suggest?q={search_query}", 
                           headers={"Authorization": f"Bearer {token1}"})
    
    if response.status_code != 200:
        log_test("8.2 Friend search suggestions", False, f"Status: {response.status_code}")
        return
    
    suggestions = response.json()
    found_friend = any(s.get("username", "").lower() == username2.lower() for s in suggestions)
    log_test("8.2 Friend search case-insensitive", found_friend, f"Found {len(suggestions)} suggestions, friend found: {found_friend}")
    
    # Add friend
    response = requests.post(f"{BACKEND_URL}/friends/add",
        headers={"Authorization": f"Bearer {token1}"},
        json={"friend_username": username2}
    )
    
    add_success = response.status_code == 200
    log_test("8.3 Add friend succeeds", add_success, f"Status: {response.status_code}")
    
    # Get friends list
    response = requests.get(f"{BACKEND_URL}/friends", headers={"Authorization": f"Bearer {token1}"})
    
    if response.status_code != 200:
        log_test("8.4 GET /friends accessible", False, f"Status: {response.status_code}")
        return
    
    friends = response.json()
    friend_found = any(f.get("username", "").lower() == username2.lower() for f in friends)
    log_test("8.4 GET /friends returns added friend", friend_found, f"Found {len(friends)} friends")
    
    if not friend_found:
        return
    
    friend_id = next((f["id"] for f in friends if f.get("username", "").lower() == username2.lower()), None)
    
    # Check initial favorite status (should be false)
    initial_favorite = next((f.get("favorite", False) for f in friends if f["id"] == friend_id), False)
    log_test("8.5 Initial favorite status is false", not initial_favorite, f"Favorite: {initial_favorite}")
    
    # Toggle favorite ON
    response = requests.post(f"{BACKEND_URL}/friends/{friend_id}/favorite",
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    if response.status_code != 200:
        log_test("8.6 POST /friends/{id}/favorite works", False, f"Status: {response.status_code}")
        return
    
    data = response.json()
    favorite_on = data.get("favorite") == True
    log_test("8.6 Toggle favorite ON", favorite_on, f"Favorite: {data.get('favorite')}")
    
    # Check friends list shows favorite
    response = requests.get(f"{BACKEND_URL}/friends", headers={"Authorization": f"Bearer {token1}"})
    friends = response.json()
    friend_data = next((f for f in friends if f["id"] == friend_id), None)
    
    if friend_data:
        is_favorite = friend_data.get("favorite") == True
        log_test("8.7 GET /friends shows favorite=true", is_favorite, f"Favorite: {friend_data.get('favorite')}")
    else:
        log_test("8.7 GET /friends shows favorite=true", False, "Friend not found in list")
    
    # Toggle favorite OFF
    response = requests.post(f"{BACKEND_URL}/friends/{friend_id}/favorite",
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        favorite_off = data.get("favorite") == False
        log_test("8.8 Toggle favorite OFF", favorite_off, f"Favorite: {data.get('favorite')}")

def test_9_settings_persistence(token):
    """Test 9: Settings update persists and doesn't drop defaults"""
    print("\n=== TEST 9: Settings Persistence ===")
    
    # Get initial settings
    response = requests.get(f"{BACKEND_URL}/settings", headers={"Authorization": f"Bearer {token}"})
    
    if response.status_code != 200:
        log_test("9.1 GET /settings accessible", False, f"Status: {response.status_code}")
        return
    
    initial_settings = response.json()
    log_test("9.1 GET /settings returns defaults", True, f"Settings keys: {len(initial_settings)}")
    
    # Check default settings are present
    has_theme = "theme" in initial_settings
    has_font_size = "font_size" in initial_settings
    has_sound = "sound_effects" in initial_settings
    has_notifications = "notifications" in initial_settings
    
    log_test("9.2 Default settings present", has_theme and has_font_size and has_sound and has_notifications, 
             f"theme:{has_theme}, font_size:{has_font_size}, sound:{has_sound}, notifications:{has_notifications}")
    
    # Update only some settings
    response = requests.put(f"{BACKEND_URL}/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "settings": {
                "theme": "light",
                "font_size": "large"
            }
        }
    )
    
    if response.status_code != 200:
        log_test("9.3 PUT /settings succeeds", False, f"Status: {response.status_code}")
        return
    
    log_test("9.3 PUT /settings succeeds", True, "Settings updated")
    
    # Get settings again
    response = requests.get(f"{BACKEND_URL}/settings", headers={"Authorization": f"Bearer {token}"})
    updated_settings = response.json()
    
    # Check updated values
    theme_updated = updated_settings.get("theme") == "light"
    font_updated = updated_settings.get("font_size") == "large"
    log_test("9.4 Updated settings persist", theme_updated and font_updated, 
             f"theme:{updated_settings.get('theme')}, font_size:{updated_settings.get('font_size')}")
    
    # Check defaults NOT dropped
    sound_preserved = "sound_effects" in updated_settings
    notifications_preserved = "notifications" in updated_settings
    log_test("9.5 Default settings NOT dropped", sound_preserved and notifications_preserved,
             f"sound_effects:{sound_preserved}, notifications:{notifications_preserved}")
    
    # Verify via /auth/me
    response = requests.get(f"{BACKEND_URL}/auth/me", headers={"Authorization": f"Bearer {token}"})
    if response.status_code == 200:
        user = response.json()
        settings_in_user = user.get("settings", {})
        theme_in_user = settings_in_user.get("theme") == "light"
        sound_in_user = "sound_effects" in settings_in_user
        log_test("9.6 Settings persist in /auth/me", theme_in_user and sound_in_user,
                 f"theme:{settings_in_user.get('theme')}, sound_effects present:{sound_in_user}")

def test_10_email_endpoints(token):
    """Test 10: Email endpoints send branded HTML without exposing secrets"""
    print("\n=== TEST 10: Email Endpoints ===")
    
    # Test send verification code
    test_email = f"emailtest_{int(time.time())}@codero.com"
    response = requests.post(f"{BACKEND_URL}/auth/send-verification-code",
        json={"email": test_email}
    )
    
    if response.status_code != 200:
        log_test("10.1 POST /auth/send-verification-code works", False, f"Status: {response.status_code}")
        return
    
    data = response.json()
    log_test("10.1 POST /auth/send-verification-code works", True, "Verification code queued")
    
    # Check code NOT exposed
    code_exposed = "code" in data or "verification_code" in data
    log_test("10.2 Verification code NOT exposed", not code_exposed, f"Code exposed: {code_exposed}")
    
    # Check SMTP secrets NOT exposed
    smtp_exposed = "smtp" in str(data).lower() or "password" in str(data).lower()
    log_test("10.3 SMTP secrets NOT exposed", not smtp_exposed, f"SMTP exposed: {smtp_exposed}")
    
    # Test email templates endpoint
    response = requests.get(f"{BACKEND_URL}/email/templates", headers={"Authorization": f"Bearer {token}"})
    
    if response.status_code != 200:
        log_test("10.4 GET /email/templates accessible", False, f"Status: {response.status_code}")
        return
    
    templates = response.json()
    has_templates = len(templates) > 0
    log_test("10.4 GET /email/templates returns templates", has_templates, f"Found {len(templates)} templates")
    
    # Check for branded HTML structure (templates should have subject and body)
    if has_templates:
        first_template = templates[0]
        has_subject = "subject" in first_template
        has_body = "body" in first_template
        log_test("10.5 Templates have subject and body", has_subject and has_body,
                 f"subject:{has_subject}, body:{has_body}")
    
    # Test send test email
    response = requests.post(f"{BACKEND_URL}/email/send-test",
        headers={"Authorization": f"Bearer {token}"},
        json={"event": "test"}
    )
    
    if response.status_code != 200:
        log_test("10.6 POST /email/send-test works", False, f"Status: {response.status_code}")
        return
    
    data = response.json()
    log_test("10.6 POST /email/send-test works", True, "Test email queued")
    
    # Check SMTP secrets NOT exposed in test email response
    smtp_exposed = "smtp" in str(data).lower() or "password" in str(data).lower()
    log_test("10.7 SMTP secrets NOT exposed in test", not smtp_exposed, f"SMTP exposed: {smtp_exposed}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("CODERO V1.7 PHASE 1 BACKEND TESTING")
    print("=" * 60)
    
    # Test 1: Register fresh user
    token, username = test_1_register_fresh_user()
    if not token:
        print("\n❌ CRITICAL: Registration failed, cannot continue with most tests")
        return
    
    email = f"{username}@codero.com"
    
    # Test 2: Duplicate registration
    test_2_duplicate_registration(username, email)
    
    # Test 3: Login with email and username
    token = test_3_login_email_and_username(username, email)
    
    # Test 4: Admin behavior
    test_4_admin_behavior()
    
    # Test 5: Tutorial gating
    test_5_tutorial_gating(token)
    
    # Test 6: Wrong answer review
    test_6_wrong_answer_review(token)
    
    # Test 7: Fix-broken-code starter
    test_7_fix_broken_code_starter(token)
    
    # Test 8: Friends system
    test_8_friends_system(token, username)
    
    # Test 9: Settings persistence
    test_9_settings_persistence(token)
    
    # Test 10: Email endpoints
    test_10_email_endpoints(token)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total = len(test_results)
    passed = sum(1 for t in test_results if t["passed"])
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if failed_tests:
        print("\n" + "=" * 60)
        print("FAILED TESTS DETAILS")
        print("=" * 60)
        for test in failed_tests:
            print(f"\n❌ {test['name']}")
            if test['details']:
                print(f"   {test['details']}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
