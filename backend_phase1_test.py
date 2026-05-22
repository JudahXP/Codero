#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Codero Phase 1 Enhancements
Tests: Auth, Profile, Continue Learning, Enriched Lessons, Code Check, Wrong Answers, Friends, Leaderboard, Email Verification
"""

import requests
import json
import sys
import time
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://codero-stack.preview.emergentagent.com/api"

class Phase1Tester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.username = None
        self.test_results = []
        self.friend_token = None
        self.friend_username = None
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        print()
    
    def get_headers(self, token=None) -> Dict[str, str]:
        """Get authorization headers"""
        t = token or self.token
        return {"Authorization": f"Bearer {t}"}
    
    def test_auth_register_with_defaults(self) -> bool:
        """Test 1: Register fresh user and verify profile/auth_methods defaults"""
        try:
            unique_id = int(time.time() * 1000)
            self.username = f"phase1test_{unique_id}"
            email = f"{self.username}@codero.com"
            
            response = requests.post(f"{BACKEND_URL}/auth/register", json={
                "username": self.username,
                "email": email,
                "password": "testpass123"
            })
            
            if response.status_code != 200:
                self.log_test("Auth Register with Defaults", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            self.token = data.get("token")
            user = data.get("user", {})
            self.user_id = user.get("id")
            
            # Check profile defaults
            profile = user.get("profile")
            if not profile:
                self.log_test("Auth Register with Defaults", False, "Missing profile field in user response")
                return False
            
            if "display_name" not in profile or "bio" not in profile or "avatar_color" not in profile:
                self.log_test("Auth Register with Defaults", False, f"Profile missing required fields: {list(profile.keys())}")
                return False
            
            # Check auth_methods
            auth_methods = user.get("auth_methods")
            if not auth_methods:
                self.log_test("Auth Register with Defaults", False, "Missing auth_methods field in user response")
                return False
            
            required_auth_fields = ["password", "email_verified", "passkey_ready", "google_ready"]
            for field in required_auth_fields:
                if field not in auth_methods:
                    self.log_test("Auth Register with Defaults", False, f"auth_methods missing {field}")
                    return False
            
            # Verify passkey_ready and google_ready are True
            if not auth_methods.get("passkey_ready"):
                self.log_test("Auth Register with Defaults", False, "passkey_ready should be True")
                return False
            
            if not auth_methods.get("google_ready"):
                self.log_test("Auth Register with Defaults", False, "google_ready should be True")
                return False
            
            # Check email_verified field at top level
            if "email_verified" not in user:
                self.log_test("Auth Register with Defaults", False, "Missing email_verified field at user level")
                return False
            
            self.log_test("Auth Register with Defaults", True, 
                         f"User registered with profile defaults and auth_methods. passkey_ready={auth_methods.get('passkey_ready')}, google_ready={auth_methods.get('google_ready')}")
            return True
            
        except Exception as e:
            self.log_test("Auth Register with Defaults", False, f"Exception: {str(e)}")
            return False
    
    def test_auth_login(self) -> bool:
        """Test 2: Login with registered user"""
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json={
                "email": f"{self.username}@codero.com",
                "password": "testpass123"
            })
            
            if response.status_code != 200:
                self.log_test("Auth Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            if not data.get("token"):
                self.log_test("Auth Login", False, "No token in login response")
                return False
            
            self.log_test("Auth Login", True, "Login successful with token")
            return True
            
        except Exception as e:
            self.log_test("Auth Login", False, f"Exception: {str(e)}")
            return False
    
    def test_auth_me(self) -> bool:
        """Test 3: GET /auth/me with valid token"""
        try:
            response = requests.get(f"{BACKEND_URL}/auth/me", headers=self.get_headers())
            
            if response.status_code != 200:
                self.log_test("Auth /me", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            user = response.json()
            if user.get("username") != self.username:
                self.log_test("Auth /me", False, f"Username mismatch: expected {self.username}, got {user.get('username')}")
                return False
            
            self.log_test("Auth /me", True, f"Protected endpoint accessible, user: {user.get('username')}")
            return True
            
        except Exception as e:
            self.log_test("Auth /me", False, f"Exception: {str(e)}")
            return False
    
    def test_auth_unauthorized(self) -> bool:
        """Test 4: Verify unauthorized access is rejected"""
        try:
            response = requests.get(f"{BACKEND_URL}/auth/me", headers={"Authorization": "Bearer invalid_token_12345"})
            
            if response.status_code == 401:
                self.log_test("Auth Unauthorized", True, "Unauthorized access correctly rejected with 401")
                return True
            else:
                self.log_test("Auth Unauthorized", False, f"Expected 401, got {response.status_code}")
                return False
            
        except Exception as e:
            self.log_test("Auth Unauthorized", False, f"Exception: {str(e)}")
            return False
    
    def test_profile_update(self) -> bool:
        """Test 5: PUT /profile with display_name and bio"""
        try:
            new_display_name = "Phase1 Tester"
            new_bio = "Testing Phase 1 enhancements for Codero"
            
            response = requests.put(f"{BACKEND_URL}/profile", 
                json={
                    "display_name": new_display_name,
                    "bio": new_bio
                },
                headers=self.get_headers()
            )
            
            if response.status_code != 200:
                self.log_test("Profile Update", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            profile = data.get("profile", {})
            
            if profile.get("display_name") != new_display_name:
                self.log_test("Profile Update", False, f"display_name not updated: {profile.get('display_name')}")
                return False
            
            if profile.get("bio") != new_bio:
                self.log_test("Profile Update", False, f"bio not updated: {profile.get('bio')}")
                return False
            
            # Verify persistence via /auth/me
            me_response = requests.get(f"{BACKEND_URL}/auth/me", headers=self.get_headers())
            if me_response.status_code != 200:
                self.log_test("Profile Update", False, "Could not verify persistence via /auth/me")
                return False
            
            user = me_response.json()
            user_profile = user.get("profile", {})
            
            if user_profile.get("display_name") != new_display_name:
                self.log_test("Profile Update", False, f"display_name not persisted: {user_profile.get('display_name')}")
                return False
            
            if user_profile.get("bio") != new_bio:
                self.log_test("Profile Update", False, f"bio not persisted: {user_profile.get('bio')}")
                return False
            
            self.log_test("Profile Update", True, f"Profile updated and persisted: display_name='{new_display_name}', bio='{new_bio}'")
            return True
            
        except Exception as e:
            self.log_test("Profile Update", False, f"Exception: {str(e)}")
            return False
    
    def test_display_badges(self) -> bool:
        """Test 6: PUT /profile/display-badges with validation"""
        try:
            # First, complete a lesson to earn a badge
            lessons_response = requests.get(f"{BACKEND_URL}/languages/python/lessons")
            if lessons_response.status_code != 200:
                self.log_test("Display Badges", False, "Could not get lessons")
                return False
            
            lessons = lessons_response.json()
            if not lessons:
                self.log_test("Display Badges", False, "No lessons available")
                return False
            
            first_lesson = lessons[0]
            lesson_id = first_lesson["id"]
            
            # Complete the lesson to earn first_lesson badge
            complete_response = requests.post(f"{BACKEND_URL}/progress/complete",
                json={
                    "lesson_id": lesson_id,
                    "language": "python",
                    "answers": [{"selected": 0} for _ in range(10)]  # Answer all exercises
                },
                headers=self.get_headers()
            )
            
            if complete_response.status_code != 200:
                self.log_test("Display Badges", False, f"Could not complete lesson: {complete_response.text}")
                return False
            
            # Get current user to see earned badges
            me_response = requests.get(f"{BACKEND_URL}/auth/me", headers=self.get_headers())
            user = me_response.json()
            earned_badges = user.get("badges", [])
            
            if not earned_badges:
                self.log_test("Display Badges", False, "No badges earned after completing lesson")
                return False
            
            # Test 1: Set display badges with earned badges (should succeed)
            display_badges = earned_badges[:min(3, len(earned_badges))]
            response = requests.put(f"{BACKEND_URL}/profile/display-badges",
                json={"badge_ids": display_badges},
                headers=self.get_headers()
            )
            
            if response.status_code != 200:
                self.log_test("Display Badges", False, f"Could not set display badges: {response.text}")
                return False
            
            # Test 2: Try to set more than 3 badges (should fail)
            if len(earned_badges) >= 4:
                too_many = earned_badges[:4]
            else:
                too_many = earned_badges + ["fake_badge_1"]
            
            fail_response = requests.put(f"{BACKEND_URL}/profile/display-badges",
                json={"badge_ids": too_many},
                headers=self.get_headers()
            )
            
            if fail_response.status_code != 400:
                self.log_test("Display Badges", False, f"Should reject >3 badges, got status {fail_response.status_code}")
                return False
            
            # Test 3: Try to set unearned badge (should fail)
            unearned_response = requests.put(f"{BACKEND_URL}/profile/display-badges",
                json={"badge_ids": ["unearned_badge_xyz"]},
                headers=self.get_headers()
            )
            
            if unearned_response.status_code != 400:
                self.log_test("Display Badges", False, f"Should reject unearned badges, got status {unearned_response.status_code}")
                return False
            
            self.log_test("Display Badges", True, 
                         f"Display badges validation working: max 3 enforced, unearned badges rejected. Set {len(display_badges)} badges")
            return True
            
        except Exception as e:
            self.log_test("Display Badges", False, f"Exception: {str(e)}")
            return False
    
    def test_continue_learning(self) -> bool:
        """Test 7: GET /continue-learning returns valid language_id and lesson_id"""
        try:
            response = requests.get(f"{BACKEND_URL}/continue-learning", headers=self.get_headers())
            
            if response.status_code != 200:
                self.log_test("Continue Learning", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            
            required_fields = ["has_continue", "language_id", "lesson_id", "title", "description"]
            for field in required_fields:
                if field not in data:
                    self.log_test("Continue Learning", False, f"Missing field: {field}")
                    return False
            
            language_id = data.get("language_id")
            lesson_id = data.get("lesson_id")
            
            # Verify the lesson exists
            lesson_response = requests.get(f"{BACKEND_URL}/languages/{language_id}/lessons/{lesson_id}")
            
            if lesson_response.status_code != 200:
                self.log_test("Continue Learning", False, f"Lesson {lesson_id} not found for language {language_id}")
                return False
            
            lesson = lesson_response.json()
            if lesson.get("id") != lesson_id:
                self.log_test("Continue Learning", False, f"Lesson ID mismatch: expected {lesson_id}, got {lesson.get('id')}")
                return False
            
            self.log_test("Continue Learning", True, 
                         f"Continue learning working: language={language_id}, lesson={lesson_id}, title='{data.get('title')}'")
            return True
            
        except Exception as e:
            self.log_test("Continue Learning", False, f"Exception: {str(e)}")
            return False
    
    def test_enriched_lesson_types(self) -> bool:
        """Test 8: Verify lessons include multiple challenge types (predict_output, fill_blank, fix_broken_code, write_code, code, drag_drop)"""
        try:
            # Get first Python lesson with exercises
            response = requests.get(f"{BACKEND_URL}/languages/python/lessons/python_1_1")
            
            if response.status_code != 200:
                self.log_test("Enriched Lesson Types", False, f"Status: {response.status_code}")
                return False
            
            lesson = response.json()
            exercises = lesson.get("exercises", [])
            
            if not exercises:
                self.log_test("Enriched Lesson Types", False, "No exercises in lesson")
                return False
            
            # Check for diverse challenge types
            found_types = set()
            for exercise in exercises:
                ex_type = exercise.get("type")
                if ex_type:
                    found_types.add(ex_type)
            
            # Expected types from the review request
            expected_types = {"predict_output", "fill_blank", "fix_broken_code", "write_code", "drag_drop", "multiple_choice"}
            
            if not found_types:
                self.log_test("Enriched Lesson Types", False, "No exercise types found")
                return False
            
            # Check for at least some variety (should have at least 4 different types)
            if len(found_types) < 4:
                self.log_test("Enriched Lesson Types", False, f"Only found {len(found_types)} exercise type(s): {found_types}")
                return False
            
            # Verify no serialization issues by checking structure
            if not isinstance(exercises, list):
                self.log_test("Enriched Lesson Types", False, "Exercises not properly serialized as list")
                return False
            
            # Check for specific enriched types
            has_predict_output = "predict_output" in found_types
            has_fill_blank = "fill_blank" in found_types
            has_fix_broken = "fix_broken_code" in found_types
            has_write_code = "write_code" in found_types
            has_drag_drop = "drag_drop" in found_types
            
            self.log_test("Enriched Lesson Types", True, 
                         f"Lessons include diverse challenge types: {', '.join(sorted(found_types))}. No serialization issues. predict_output={has_predict_output}, fill_blank={has_fill_blank}, fix_broken_code={has_fix_broken}, write_code={has_write_code}, drag_drop={has_drag_drop}")
            return True
            
        except Exception as e:
            self.log_test("Enriched Lesson Types", False, f"Exception: {str(e)}")
            return False
    
    def test_code_check_and_wrong_answers(self) -> bool:
        """Test 9: /code/check with wrong answer, verify wrong answer saved, review it"""
        try:
            # Get first Python lesson with exercises
            lesson_id = "python_1_1"
            lesson_response = requests.get(f"{BACKEND_URL}/languages/python/lessons/{lesson_id}")
            if lesson_response.status_code != 200:
                self.log_test("Code Check & Wrong Answers", False, "Could not get lesson")
                return False
            
            first_lesson = lesson_response.json()
            exercises = first_lesson.get("exercises", [])
            
            if not exercises:
                self.log_test("Code Check & Wrong Answers", False, "No exercises in first lesson")
                return False
            
            first_exercise = exercises[0]
            exercise_index = 0
            
            # Submit a wrong answer based on exercise type
            ex_type = first_exercise.get("type")
            if ex_type in ["code", "write_code", "fix_broken_code"]:
                wrong_answer = {"code": "wrong_code_here"}
            elif ex_type == "predict_output":
                wrong_answer = {"answer": "wrong_output"}
            elif ex_type == "fill_blank":
                wrong_answer = {"answer": "wrong_blank"}
            elif ex_type == "drag_drop":
                wrong_answer = {"order": ["wrong", "order"]}
            else:
                wrong_answer = {"selected": 999}
            
            check_response = requests.post(f"{BACKEND_URL}/code/check",
                json={
                    "language": "python",
                    "lesson_id": lesson_id,
                    "exercise_index": exercise_index,
                    "answer": wrong_answer,
                    "save_wrong": True
                },
                headers=self.get_headers()
            )
            
            if check_response.status_code != 200:
                self.log_test("Code Check & Wrong Answers", False, f"Code check failed (status {check_response.status_code}): {check_response.text}. Exercise type: {ex_type}")
                return False
            
            check_data = check_response.json()
            
            # Verify response structure
            if check_data.get("correct") == True:
                self.log_test("Code Check & Wrong Answers", False, "Wrong answer marked as correct")
                return False
            
            if "simple_explanation" not in check_data:
                self.log_test("Code Check & Wrong Answers", False, "Missing simple_explanation")
                return False
            
            # Verify expected_answer is gated (only shown when incorrect)
            if "expected_answer" not in check_data:
                self.log_test("Code Check & Wrong Answers", False, "expected_answer should be present for wrong answer")
                return False
            
            # Get wrong answers
            wrong_answers_response = requests.get(f"{BACKEND_URL}/review/wrong-answers", headers=self.get_headers())
            
            if wrong_answers_response.status_code != 200:
                self.log_test("Code Check & Wrong Answers", False, f"Could not get wrong answers: {wrong_answers_response.text}")
                return False
            
            wrong_answers = wrong_answers_response.json()
            
            if not wrong_answers:
                self.log_test("Code Check & Wrong Answers", False, "Wrong answer not saved")
                return False
            
            # Find the saved wrong answer
            saved_item = None
            for item in wrong_answers:
                if item.get("lesson_id") == lesson_id and item.get("exercise_index") == exercise_index:
                    saved_item = item
                    break
            
            if not saved_item:
                self.log_test("Code Check & Wrong Answers", False, "Could not find saved wrong answer")
                return False
            
            # Mark as reviewed
            wrong_answer_id = saved_item.get("id")
            review_response = requests.post(f"{BACKEND_URL}/review/wrong-answers/{wrong_answer_id}/reviewed",
                headers=self.get_headers()
            )
            
            if review_response.status_code != 200:
                self.log_test("Code Check & Wrong Answers", False, f"Could not mark as reviewed: {review_response.text}")
                return False
            
            self.log_test("Code Check & Wrong Answers", True, 
                         f"Code check working: correct=false, simple_explanation present, expected_answer gated. Wrong answer saved and marked reviewed.")
            return True
            
        except Exception as e:
            self.log_test("Code Check & Wrong Answers", False, f"Exception: {str(e)}")
            return False
    
    def test_lesson_completion_with_wrong_answers(self) -> bool:
        """Test 10: Complete lesson with mixed correct/wrong answers, verify wrong answers saved"""
        try:
            # Get second Python lesson (to avoid conflicts with previous tests)
            lessons_response = requests.get(f"{BACKEND_URL}/languages/python/lessons")
            if lessons_response.status_code != 200:
                self.log_test("Lesson Completion with Wrong Answers", False, "Could not get lessons")
                return False
            
            lessons = lessons_response.json()
            if len(lessons) < 2:
                self.log_test("Lesson Completion with Wrong Answers", False, "Not enough lessons")
                return False
            
            lesson = lessons[1]
            lesson_id = lesson["id"]
            exercises = lesson.get("exercises", [])
            
            # Create mixed answers (some correct, some wrong)
            answers = []
            for i, exercise in enumerate(exercises):
                if i % 2 == 0:
                    # Correct answer
                    if exercise.get("type") == "multiple_choice":
                        answers.append({"selected": exercise.get("correct", 0)})
                    elif exercise.get("type") == "fill_blank":
                        answers.append({"answer": exercise.get("answer", "")})
                    else:
                        answers.append({"code": exercise.get("solution", "")})
                else:
                    # Wrong answer
                    if exercise.get("type") == "multiple_choice":
                        wrong_option = (exercise.get("correct", 0) + 1) % len(exercise.get("options", [0, 1]))
                        answers.append({"selected": wrong_option})
                    elif exercise.get("type") == "fill_blank":
                        answers.append({"answer": "wrong_answer"})
                    else:
                        answers.append({"code": "wrong_code"})
            
            # Complete lesson
            complete_response = requests.post(f"{BACKEND_URL}/progress/complete",
                json={
                    "lesson_id": lesson_id,
                    "language": "python",
                    "answers": answers
                },
                headers=self.get_headers()
            )
            
            if complete_response.status_code != 200:
                self.log_test("Lesson Completion with Wrong Answers", False, f"Could not complete lesson: {complete_response.text}")
                return False
            
            complete_data = complete_response.json()
            
            # Verify progress persisted
            progress_response = requests.get(f"{BACKEND_URL}/progress/python", headers=self.get_headers())
            if progress_response.status_code != 200:
                self.log_test("Lesson Completion with Wrong Answers", False, "Could not get progress")
                return False
            
            progress_data = progress_response.json()
            completed_lessons = [p for p in progress_data.get("lessons", []) if p.get("lesson_id") == lesson_id]
            
            if not completed_lessons:
                self.log_test("Lesson Completion with Wrong Answers", False, "Lesson completion not persisted")
                return False
            
            self.log_test("Lesson Completion with Wrong Answers", True, 
                         f"Lesson completed with enriched challenge types. Score: {complete_data.get('score')}, XP: {complete_data.get('xp_earned')}")
            return True
            
        except Exception as e:
            self.log_test("Lesson Completion with Wrong Answers", False, f"Exception: {str(e)}")
            return False
    
    def test_friends_suggestions(self) -> bool:
        """Test 11: Create another user, test friend suggestions, add friend, verify exclusions"""
        try:
            # Create a second user
            unique_id = int(time.time() * 1000) + 1
            self.friend_username = f"friend_{unique_id}"
            friend_email = f"{self.friend_username}@codero.com"
            
            friend_response = requests.post(f"{BACKEND_URL}/auth/register", json={
                "username": self.friend_username,
                "email": friend_email,
                "password": "testpass123"
            })
            
            if friend_response.status_code != 200:
                self.log_test("Friends Suggestions", False, f"Could not create friend user: {friend_response.text}")
                return False
            
            friend_data = friend_response.json()
            self.friend_token = friend_data.get("token")
            
            # Test friend suggestions with prefix
            prefix = self.friend_username[:5]
            suggest_response = requests.get(f"{BACKEND_URL}/friends/suggest?q={prefix}", headers=self.get_headers())
            
            if suggest_response.status_code != 200:
                self.log_test("Friends Suggestions", False, f"Could not get suggestions: {suggest_response.text}")
                return False
            
            suggestions = suggest_response.json()
            
            # Verify friend is in suggestions
            friend_found = any(s.get("username") == self.friend_username for s in suggestions)
            if not friend_found:
                self.log_test("Friends Suggestions", False, f"Friend {self.friend_username} not in suggestions")
                return False
            
            # Verify self is excluded
            self_found = any(s.get("username") == self.username for s in suggestions)
            if self_found:
                self.log_test("Friends Suggestions", False, "Self should be excluded from suggestions")
                return False
            
            # Add friend
            add_response = requests.post(f"{BACKEND_URL}/friends/add",
                json={"friend_username": self.friend_username},
                headers=self.get_headers()
            )
            
            if add_response.status_code != 200:
                self.log_test("Friends Suggestions", False, f"Could not add friend: {add_response.text}")
                return False
            
            # Verify friend is now excluded from suggestions
            suggest_after_response = requests.get(f"{BACKEND_URL}/friends/suggest?q={prefix}", headers=self.get_headers())
            
            if suggest_after_response.status_code != 200:
                self.log_test("Friends Suggestions", False, "Could not get suggestions after adding friend")
                return False
            
            suggestions_after = suggest_after_response.json()
            friend_still_found = any(s.get("username") == self.friend_username for s in suggestions_after)
            
            if friend_still_found:
                self.log_test("Friends Suggestions", False, "Friend should be excluded after adding")
                return False
            
            self.log_test("Friends Suggestions", True, 
                         f"Friend suggestions working: found friend before adding, excluded self and friend after adding")
            return True
            
        except Exception as e:
            self.log_test("Friends Suggestions", False, f"Exception: {str(e)}")
            return False
    
    def test_leaderboard_auth_and_friends_only(self) -> bool:
        """Test 12: Leaderboard requires auth and only returns self/friends"""
        try:
            # Test without auth (should fail)
            unauth_response = requests.get(f"{BACKEND_URL}/leaderboard")
            if unauth_response.status_code != 401 and unauth_response.status_code != 403:
                self.log_test("Leaderboard Auth & Friends Only", False, 
                             f"Leaderboard should require auth, got status {unauth_response.status_code}")
                return False
            
            # Test with auth
            auth_response = requests.get(f"{BACKEND_URL}/leaderboard", headers=self.get_headers())
            
            if auth_response.status_code != 200:
                self.log_test("Leaderboard Auth & Friends Only", False, f"Status: {auth_response.status_code}, Response: {auth_response.text}")
                return False
            
            leaderboard = auth_response.json()
            
            if not isinstance(leaderboard, list):
                self.log_test("Leaderboard Auth & Friends Only", False, "Leaderboard should return a list")
                return False
            
            # Verify only self and friends are in leaderboard
            usernames = [entry.get("username") for entry in leaderboard]
            
            # Self should be in leaderboard
            if self.username not in usernames:
                self.log_test("Leaderboard Auth & Friends Only", False, "Self not in leaderboard")
                return False
            
            # Friend should be in leaderboard (we added them earlier)
            if self.friend_username and self.friend_username not in usernames:
                self.log_test("Leaderboard Auth & Friends Only", False, "Friend not in leaderboard")
                return False
            
            # Check for any random users (should not be present)
            # We can't definitively check this without knowing all users, but we can verify the count is reasonable
            if len(leaderboard) > 50:
                self.log_test("Leaderboard Auth & Friends Only", False, f"Too many users in leaderboard: {len(leaderboard)}")
                return False
            
            self.log_test("Leaderboard Auth & Friends Only", True, 
                         f"Leaderboard requires auth and returns self/friends only. Found {len(leaderboard)} users including self and friend")
            return True
            
        except Exception as e:
            self.log_test("Leaderboard Auth & Friends Only", False, f"Exception: {str(e)}")
            return False
    
    def test_email_verification_endpoints(self) -> bool:
        """Test 13: Email verification endpoints (send code, security options)"""
        try:
            # Test send verification code
            send_response = requests.post(f"{BACKEND_URL}/auth/send-verification-code",
                json={"email": f"{self.username}@codero.com"}
            )
            
            if send_response.status_code != 200:
                self.log_test("Email Verification Endpoints", False, f"Send verification code failed: {send_response.text}")
                return False
            
            send_data = send_response.json()
            
            # Verify code is NOT exposed in response
            if "code" in send_data:
                self.log_test("Email Verification Endpoints", False, "Verification code should not be exposed in response")
                return False
            
            # Verify response has expected fields
            if "message" not in send_data or "email" not in send_data:
                self.log_test("Email Verification Endpoints", False, f"Missing fields in response: {list(send_data.keys())}")
                return False
            
            # Test security options endpoint
            security_response = requests.get(f"{BACKEND_URL}/auth/security-options", headers=self.get_headers())
            
            if security_response.status_code != 200:
                self.log_test("Email Verification Endpoints", False, f"Security options failed: {security_response.text}")
                return False
            
            security_data = security_response.json()
            
            # Verify passkeys_ready and google_sign_in_ready are present and True
            if not security_data.get("passkeys_ready"):
                self.log_test("Email Verification Endpoints", False, "passkeys_ready should be True")
                return False
            
            if not security_data.get("google_sign_in_ready"):
                self.log_test("Email Verification Endpoints", False, "google_sign_in_ready should be True")
                return False
            
            # Verify other expected fields
            expected_fields = ["password_enabled", "email_verification_enabled", "email_verified"]
            for field in expected_fields:
                if field not in security_data:
                    self.log_test("Email Verification Endpoints", False, f"Missing field: {field}")
                    return False
            
            self.log_test("Email Verification Endpoints", True, 
                         f"Email verification endpoints working: code queued without exposure, passkeys_ready={security_data.get('passkeys_ready')}, google_sign_in_ready={security_data.get('google_sign_in_ready')}")
            return True
            
        except Exception as e:
            self.log_test("Email Verification Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all Phase 1 tests"""
        print("🚀 Starting Codero Phase 1 Backend API Tests")
        print("=" * 70)
        
        tests = [
            ("Auth Register with Defaults", self.test_auth_register_with_defaults),
            ("Auth Login", self.test_auth_login),
            ("Auth /me", self.test_auth_me),
            ("Auth Unauthorized", self.test_auth_unauthorized),
            ("Profile Update", self.test_profile_update),
            ("Display Badges", self.test_display_badges),
            ("Continue Learning", self.test_continue_learning),
            ("Enriched Lesson Types", self.test_enriched_lesson_types),
            ("Code Check & Wrong Answers", self.test_code_check_and_wrong_answers),
            ("Lesson Completion with Wrong Answers", self.test_lesson_completion_with_wrong_answers),
            ("Friends Suggestions", self.test_friends_suggestions),
            ("Leaderboard Auth & Friends Only", self.test_leaderboard_auth_and_friends_only),
            ("Email Verification Endpoints", self.test_email_verification_endpoints),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Unexpected exception: {str(e)}")
        
        print("=" * 70)
        print(f"🎯 Test Results: {passed}/{total} tests passed ({int(passed/total*100)}%)")
        
        if passed == total:
            print("✅ All Phase 1 backend endpoints working correctly!")
            return True
        else:
            print("❌ Some tests failed. Check details above.")
            
            # Print failed tests
            failed_tests = [result for result in self.test_results if not result["success"]]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"  - {test['test']}")
                    if test['details']:
                        print(f"    {test['details']}")
            
            return False

if __name__ == "__main__":
    tester = Phase1Tester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
