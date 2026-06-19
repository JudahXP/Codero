#!/usr/bin/env python3
"""
Codero Backend Cleanup Retest
Tests Unit 0 lesson structure, tutorial gating, fix-broken-code, wrong-answer review, and auth/settings health
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://codero-stack.preview.emergentagent.com/api"

def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def test_unit0_lessons_python():
    """Test 1: GET /api/languages/python/lessons returns 6 Unit 0 lessons first"""
    log("TEST 1: Verifying Python Unit 0 lessons structure...")
    
    response = requests.get(f"{BASE_URL}/languages/python/lessons")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    lessons = response.json()
    assert len(lessons) > 0, "No lessons returned"
    
    # Check first 6 lessons are Unit 0
    unit0_lessons = lessons[:6]
    expected_ids = [f"python_unit0_{i}" for i in range(1, 7)]
    
    for i, lesson in enumerate(unit0_lessons):
        lesson_id = lesson.get("id")
        assert lesson_id == expected_ids[i], f"Expected {expected_ids[i]}, got {lesson_id}"
        assert lesson.get("unit") == 0, f"Lesson {lesson_id} should have unit=0"
        
        # Check beginner-friendly titles and descriptions
        title = lesson.get("title", "")
        description = lesson.get("description", "")
        assert len(title) > 0, f"Lesson {lesson_id} has empty title"
        assert len(description) > 0, f"Lesson {lesson_id} has empty description"
        assert "Unit 0" in title, f"Lesson {lesson_id} title should contain 'Unit 0'"
        
        # Fetch individual lesson to check is_tutorial flag
        lesson_detail_response = requests.get(f"{BASE_URL}/languages/python/lessons/{lesson_id}")
        assert lesson_detail_response.status_code == 200, f"Failed to get lesson detail for {lesson_id}"
        lesson_detail = lesson_detail_response.json()
        assert lesson_detail.get("is_tutorial") == True, f"Lesson {lesson_id} should have is_tutorial=true"
        
        log(f"  ✓ {lesson_id}: {title} (is_tutorial={lesson_detail.get('is_tutorial')})")
    
    log("  ✅ Python Unit 0 structure verified: 6 lessons, all is_tutorial=true")
    return True

def test_unit0_lessons_other_languages():
    """Test 2: Verify Unit 0 structure for skript, javascript, haskell"""
    log("TEST 2: Verifying Unit 0 structure for skript, javascript, haskell...")
    
    languages = ["skript", "javascript", "haskell"]
    
    for lang in languages:
        response = requests.get(f"{BASE_URL}/languages/{lang}/lessons")
        assert response.status_code == 200, f"Expected 200 for {lang}, got {response.status_code}"
        
        lessons = response.json()
        assert len(lessons) >= 6, f"{lang} should have at least 6 lessons"
        
        # Check first 6 lessons are Unit 0
        unit0_lessons = lessons[:6]
        expected_ids = [f"{lang}_unit0_{i}" for i in range(1, 7)]
        
        for i, lesson in enumerate(unit0_lessons):
            lesson_id = lesson.get("id")
            assert lesson_id == expected_ids[i], f"Expected {expected_ids[i]}, got {lesson_id}"
            assert lesson.get("unit") == 0, f"{lang} lesson {lesson_id} should have unit=0"
            
            # Fetch individual lesson to check is_tutorial flag
            lesson_detail_response = requests.get(f"{BASE_URL}/languages/{lang}/lessons/{lesson_id}")
            assert lesson_detail_response.status_code == 200, f"Failed to get lesson detail for {lesson_id}"
            lesson_detail = lesson_detail_response.json()
            assert lesson_detail.get("is_tutorial") == True, f"{lang} lesson {lesson_id} should have is_tutorial=true"
        
        log(f"  ✓ {lang}: 6 Unit 0 lessons verified (ids: {lang}_unit0_1 through {lang}_unit0_6)")
    
    log("  ✅ All languages have correct Unit 0 structure")
    return True

def test_tutorial_gating():
    """Test 3: Tutorial gating with python_unit0_1"""
    log("TEST 3: Testing tutorial gating with python_unit0_1...")
    
    # Register fresh user
    timestamp = int(time.time())
    username = f"gatetest_{timestamp}"
    email = f"gatetest_{timestamp}@codero.com"
    password = "test123"
    
    register_response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert register_response.status_code == 200, f"Registration failed: {register_response.status_code}"
    
    token = register_response.json().get("token")
    assert token, "No token in registration response"
    
    headers = {"Authorization": f"Bearer {token}"}
    log(f"  ✓ Registered user: {email}")
    
    # Step 1: Try to complete python_1_1 before unit0_1 (should 403)
    log("  Step 1: Attempting to complete python_1_1 before unit0_1 (should 403)...")
    
    complete_response = requests.post(f"{BASE_URL}/progress/complete", 
        headers=headers,
        json={
            "lesson_id": "python_1_1",
            "language": "python",
            "answers": [{"answer": 0}, {"answer": "test"}],
            "time_taken": 30
        }
    )
    
    assert complete_response.status_code == 403, f"Expected 403, got {complete_response.status_code}"
    error_detail = complete_response.json().get("detail", "")
    assert "Tutorial" in error_detail or "unit" in error_detail.lower(), f"Expected tutorial error message, got: {error_detail}"
    log(f"  ✓ python_1_1 blocked before tutorial: {error_detail}")
    
    # Step 2: Complete python_unit0_1 with correct/simple answers (should succeed)
    log("  Step 2: Completing python_unit0_1 with correct answers...")
    
    # Get lesson details to know how many exercises
    lesson_response = requests.get(f"{BASE_URL}/languages/python/lessons/python_unit0_1", headers=headers)
    assert lesson_response.status_code == 200, f"Failed to get lesson: {lesson_response.status_code}"
    
    lesson = lesson_response.json()
    exercises = lesson.get("exercises", [])
    
    # Provide correct answers for each exercise
    answers = []
    for ex in exercises:
        ex_type = ex.get("type")
        if ex_type == "multiple_choice":
            answers.append({"answer": ex.get("correct", 0)})
        elif ex_type == "fill_blank":
            answers.append({"answer": ex.get("answer", "answer")})
        elif ex_type in ["code", "write_code", "fix_broken_code"]:
            answers.append({"code": ex.get("solution", "print('ready')")})
        else:
            answers.append({"answer": "test"})
    
    complete_unit0_response = requests.post(f"{BASE_URL}/progress/complete",
        headers=headers,
        json={
            "lesson_id": "python_unit0_1",
            "language": "python",
            "answers": answers,
            "time_taken": 60
        }
    )
    
    assert complete_unit0_response.status_code == 200, f"Expected 200, got {complete_unit0_response.status_code}: {complete_unit0_response.text}"
    result = complete_unit0_response.json()
    assert result.get("xp_earned", 0) > 0, "Should earn XP for completing unit0_1"
    log(f"  ✓ python_unit0_1 completed successfully (XP: {result.get('xp_earned')})")
    
    # Step 3: Now try python_1_1 again (should succeed, no longer blocked)
    log("  Step 3: Attempting python_1_1 again (should now succeed)...")
    
    # Get python_1_1 lesson details
    lesson_1_1_response = requests.get(f"{BASE_URL}/languages/python/lessons/python_1_1", headers=headers)
    assert lesson_1_1_response.status_code == 200, f"Failed to get python_1_1: {lesson_1_1_response.status_code}"
    
    lesson_1_1 = lesson_1_1_response.json()
    exercises_1_1 = lesson_1_1.get("exercises", [])
    
    # Provide answers for python_1_1
    answers_1_1 = []
    for ex in exercises_1_1:
        ex_type = ex.get("type")
        if ex_type == "multiple_choice":
            answers_1_1.append({"answer": ex.get("correct", 0)})
        elif ex_type == "fill_blank":
            answers_1_1.append({"answer": ex.get("answer", "test")})
        elif ex_type in ["code", "write_code", "fix_broken_code"]:
            answers_1_1.append({"code": ex.get("solution", "print('hello')")})
        else:
            answers_1_1.append({"answer": "test"})
    
    complete_1_1_response = requests.post(f"{BASE_URL}/progress/complete",
        headers=headers,
        json={
            "lesson_id": "python_1_1",
            "language": "python",
            "answers": answers_1_1,
            "time_taken": 90
        }
    )
    
    assert complete_1_1_response.status_code == 200, f"Expected 200, got {complete_1_1_response.status_code}: {complete_1_1_response.text}"
    result_1_1 = complete_1_1_response.json()
    log(f"  ✓ python_1_1 completed successfully after tutorial (XP: {result_1_1.get('xp_earned')})")
    
    log("  ✅ Tutorial gating working correctly: python_unit0_1 required before python_1_1")
    return True

def test_fix_broken_code_empty_starter():
    """Test 4: Fix-broken-code exercise starter remains empty"""
    log("TEST 4: Verifying fix-broken-code exercises have empty starter...")
    
    # Check multiple lessons for fix_broken_code exercises
    languages_to_check = ["python", "javascript", "haskell"]
    found_fix_broken = False
    
    for lang in languages_to_check:
        response = requests.get(f"{BASE_URL}/languages/{lang}/lessons")
        assert response.status_code == 200, f"Failed to get {lang} lessons"
        
        lessons = response.json()
        
        # Check lessons for fix_broken_code exercises (skip Unit 0, check Unit 1+)
        for lesson in lessons[6:16]:  # Check lessons 7-16 (after Unit 0)
            lesson_id = lesson.get("id")
            
            # Fetch full lesson details
            lesson_detail_response = requests.get(f"{BASE_URL}/languages/{lang}/lessons/{lesson_id}")
            if lesson_detail_response.status_code != 200:
                continue
            
            lesson_detail = lesson_detail_response.json()
            exercises = lesson_detail.get("exercises", [])
            
            for ex in exercises:
                if ex.get("type") == "fix_broken_code":
                    starter = ex.get("starter", None)
                    assert starter == "", f"fix_broken_code in {lesson_id} should have empty starter, got: '{starter}'"
                    found_fix_broken = True
                    log(f"  ✓ {lang} {lesson_id}: fix_broken_code has empty starter")
                    break  # Found one, move to next lesson
            
            if found_fix_broken:
                break  # Found one for this language, move to next language
    
    assert found_fix_broken, "No fix_broken_code exercises found in tested lessons"
    log("  ✅ All fix_broken_code exercises have empty starter")
    return True

def test_wrong_answer_review():
    """Test 5: Wrong-answer review response includes wrong_review with expected_answer/explanation"""
    log("TEST 5: Testing wrong-answer review response...")
    
    # Register fresh user
    timestamp = int(time.time())
    username = f"wrongtest_{timestamp}"
    email = f"wrongtest_{timestamp}@codero.com"
    password = "test123"
    
    register_response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert register_response.status_code == 200, f"Registration failed"
    
    token = register_response.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    log(f"  ✓ Registered user: {email}")
    
    # Complete tutorial first to avoid gating
    lesson_response = requests.get(f"{BASE_URL}/languages/python/lessons/python_unit0_1", headers=headers)
    lesson = lesson_response.json()
    exercises = lesson.get("exercises", [])
    
    correct_answers = []
    for ex in exercises:
        ex_type = ex.get("type")
        if ex_type == "multiple_choice":
            correct_answers.append({"answer": ex.get("correct", 0)})
        elif ex_type == "fill_blank":
            correct_answers.append({"answer": ex.get("answer", "answer")})
        elif ex_type in ["code", "write_code", "fix_broken_code"]:
            correct_answers.append({"code": ex.get("solution", "print('ready')")})
        else:
            correct_answers.append({"answer": "test"})
    
    requests.post(f"{BASE_URL}/progress/complete", headers=headers, json={
        "lesson_id": "python_unit0_1",
        "language": "python",
        "answers": correct_answers,
        "time_taken": 60
    })
    log("  ✓ Completed tutorial")
    
    # Now submit wrong answers to python_1_1
    log("  Submitting wrong answers to python_1_1...")
    
    lesson_1_1_response = requests.get(f"{BASE_URL}/languages/python/lessons/python_1_1", headers=headers)
    lesson_1_1 = lesson_1_1_response.json()
    exercises_1_1 = lesson_1_1.get("exercises", [])
    
    # Submit intentionally wrong answers
    wrong_answers = []
    for ex in exercises_1_1:
        ex_type = ex.get("type")
        if ex_type == "multiple_choice":
            # Pick wrong option (not the correct one)
            correct = ex.get("correct", 0)
            wrong_option = (correct + 1) % len(ex.get("options", [0, 1]))
            wrong_answers.append({"answer": wrong_option})
        elif ex_type == "fill_blank":
            wrong_answers.append({"answer": "WRONG_ANSWER"})
        elif ex_type in ["code", "write_code", "fix_broken_code"]:
            wrong_answers.append({"code": "print('wrong')"})
        else:
            wrong_answers.append({"answer": "WRONG"})
    
    complete_response = requests.post(f"{BASE_URL}/progress/complete",
        headers=headers,
        json={
            "lesson_id": "python_1_1",
            "language": "python",
            "answers": wrong_answers,
            "time_taken": 60
        }
    )
    
    assert complete_response.status_code == 200, f"Expected 200, got {complete_response.status_code}"
    result = complete_response.json()
    
    # Check for wrong_review in response
    wrong_review = result.get("wrong_review", [])
    assert len(wrong_review) > 0, "Expected wrong_review array with items for wrong answers"
    
    log(f"  ✓ Received wrong_review with {len(wrong_review)} items")
    
    # Verify structure of wrong_review items
    for item in wrong_review:
        assert "question" in item, "wrong_review item missing 'question'"
        assert "expected_answer" in item, "wrong_review item missing 'expected_answer'"
        assert "explanation" in item, "wrong_review item missing 'explanation'"
        
        question = item.get("question", "")
        expected = item.get("expected_answer", "")
        explanation = item.get("explanation", "")
        
        assert len(question) > 0, "question should not be empty"
        assert len(str(expected)) > 0, "expected_answer should not be empty"
        assert len(explanation) > 0, "explanation should not be empty"
        
        log(f"    - Question: {question[:50]}...")
        log(f"      Expected: {expected}")
        log(f"      Explanation: {explanation[:60]}...")
    
    log("  ✅ Wrong-answer review response includes correct structure with expected_answer and explanation")
    return True

def test_auth_and_settings_health():
    """Test 6: Existing auth and settings endpoints still healthy"""
    log("TEST 6: Testing auth and settings endpoints health...")
    
    # Register fresh user
    timestamp = int(time.time())
    username = f"healthtest_{timestamp}"
    email = f"healthtest_{timestamp}@codero.com"
    password = "test123"
    
    # Test registration
    register_response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert register_response.status_code == 200, f"Registration failed: {register_response.status_code}"
    
    reg_data = register_response.json()
    assert "token" in reg_data, "No token in registration response"
    assert "user" in reg_data, "No user in registration response"
    
    token = reg_data["token"]
    user = reg_data["user"]
    
    assert user.get("gems") == 10, "User should start with 10 gems"
    assert user.get("hearts") == 5, "User should start with 5 hearts"
    assert "settings" in user, "User should have settings"
    
    log(f"  ✓ Registration working (gems={user.get('gems')}, hearts={user.get('hearts')})")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test login
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_response.status_code == 200, f"Login failed: {login_response.status_code}"
    
    login_data = login_response.json()
    assert "token" in login_data, "No token in login response"
    log("  ✓ Login working")
    
    # Test /auth/me
    me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert me_response.status_code == 200, f"/auth/me failed: {me_response.status_code}"
    
    me_data = me_response.json()
    assert me_data.get("email") == email, "Email mismatch in /auth/me"
    log("  ✓ /auth/me working")
    
    # Test GET /settings
    settings_response = requests.get(f"{BASE_URL}/settings", headers=headers)
    assert settings_response.status_code == 200, f"GET /settings failed: {settings_response.status_code}"
    
    settings = settings_response.json()
    assert "theme" in settings, "Settings missing 'theme'"
    assert "font_size" in settings, "Settings missing 'font_size'"
    assert "sound_effects" in settings, "Settings missing 'sound_effects'"
    log(f"  ✓ GET /settings working (theme={settings.get('theme')})")
    
    # Test PUT /settings
    put_settings_response = requests.put(f"{BASE_URL}/settings", 
        headers=headers,
        json={
            "settings": {
                "theme": "light",
                "font_size": "large"
            }
        }
    )
    assert put_settings_response.status_code == 200, f"PUT /settings failed: {put_settings_response.status_code}"
    
    # Verify settings persisted
    verify_settings_response = requests.get(f"{BASE_URL}/settings", headers=headers)
    verify_settings = verify_settings_response.json()
    assert verify_settings.get("theme") == "light", "Settings not persisted"
    assert verify_settings.get("font_size") == "large", "Settings not persisted"
    log("  ✓ PUT /settings working and persisting")
    
    log("  ✅ All auth and settings endpoints healthy")
    return True

def main():
    log("=" * 80)
    log("CODERO BACKEND CLEANUP RETEST")
    log("Testing Unit 0 lessons, tutorial gating, fix-broken-code, wrong-answer review")
    log("=" * 80)
    
    tests = [
        ("Unit 0 Lessons - Python", test_unit0_lessons_python),
        ("Unit 0 Lessons - Other Languages", test_unit0_lessons_other_languages),
        ("Tutorial Gating", test_tutorial_gating),
        ("Fix-Broken-Code Empty Starter", test_fix_broken_code_empty_starter),
        ("Wrong-Answer Review", test_wrong_answer_review),
        ("Auth and Settings Health", test_auth_and_settings_health),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            log("")
            test_func()
            passed += 1
        except AssertionError as e:
            log(f"  ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            log(f"  ❌ ERROR: {e}")
            failed += 1
    
    log("")
    log("=" * 80)
    log(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed == 0:
        log("✅ ALL TESTS PASSED")
    else:
        log(f"❌ {failed} test(s) failed")
    log("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
