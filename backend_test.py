#!/usr/bin/env python3
"""
Backend API Testing for Codero Coding Education App
Tests all endpoints: Auth, Languages, Progress, Social
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://pixel-coder-3.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "user1": {
        "username": "testcoder1",
        "email": "test1@codero.com",
        "password": "test123"
    },
    "user2": {
        "username": "testcoder2", 
        "email": "test2@codero.com",
        "password": "test123"
    }
}

class CoderoAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_data = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def make_request(self, method, endpoint, data=None, headers=None, expect_status=200):
        """Make HTTP request with error handling"""
        url = f"{BASE_URL}{endpoint}"
        
        # Add auth header if token exists
        if self.token and headers is None:
            headers = {"Authorization": f"Bearer {self.token}"}
        elif self.token and headers:
            headers["Authorization"] = f"Bearer {self.token}"
            
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            print(f"   {method} {endpoint} -> {response.status_code}")
            
            if response.status_code != expect_status:
                print(f"   Expected {expect_status}, got {response.status_code}")
                if response.text:
                    print(f"   Response: {response.text[:200]}")
                return None, response.status_code
                
            return response.json() if response.text else {}, response.status_code
            
        except requests.exceptions.RequestException as e:
            print(f"   Request failed: {e}")
            return None, 0
        except json.JSONDecodeError as e:
            print(f"   JSON decode error: {e}")
            return None, response.status_code if 'response' in locals() else 0
            
    def test_auth_endpoints(self):
        """Test all authentication endpoints"""
        print("\n=== TESTING AUTH ENDPOINTS ===")
        
        # Test 1: Register new user
        user_data = TEST_CREDENTIALS["user1"]
        response, status = self.make_request("POST", "/auth/register", user_data)
        
        if status == 200 and response and "token" in response:
            self.token = response["token"]
            self.user_data = response["user"]
            self.log_test("POST /auth/register", True, f"User created with token")
            
            # Verify user data structure
            expected_fields = ["id", "username", "email", "xp", "level", "streak", "hearts"]
            missing_fields = [f for f in expected_fields if f not in self.user_data]
            if missing_fields:
                self.log_test("User data structure", False, f"Missing fields: {missing_fields}")
            else:
                # Check initial values
                if (self.user_data["xp"] == 0 and self.user_data["level"] == 1 and 
                    self.user_data["hearts"] == 5 and self.user_data["streak"] == 0):
                    self.log_test("Initial user values", True, "XP=0, Level=1, Hearts=5, Streak=0")
                else:
                    self.log_test("Initial user values", False, 
                                f"XP={self.user_data['xp']}, Level={self.user_data['level']}, Hearts={self.user_data['hearts']}, Streak={self.user_data['streak']}")
        else:
            self.log_test("POST /auth/register", False, f"Status: {status}, Response: {response}")
            return False
            
        # Test 2: Login with same credentials
        login_data = {"email": user_data["email"], "password": user_data["password"]}
        response, status = self.make_request("POST", "/auth/login", login_data)
        
        if status == 200 and response and "token" in response:
            self.token = response["token"]  # Update token
            self.log_test("POST /auth/login", True, "Login successful")
            
            # Check if streak was updated
            if response["user"]["streak"] >= 1:
                self.log_test("Login streak update", True, f"Streak: {response['user']['streak']}")
            else:
                self.log_test("Login streak update", False, f"Streak not updated: {response['user']['streak']}")
        else:
            self.log_test("POST /auth/login", False, f"Status: {status}")
            
        # Test 3: Get current user
        response, status = self.make_request("GET", "/auth/me")
        
        if status == 200 and response and "username" in response:
            self.log_test("GET /auth/me", True, f"User: {response['username']}")
        else:
            self.log_test("GET /auth/me", False, f"Status: {status}")
            
        # Test 4: Logout
        response, status = self.make_request("POST", "/auth/logout")
        
        if status == 200:
            self.log_test("POST /auth/logout", True, "Logout successful")
            # Clear token for next tests
            old_token = self.token
            self.token = None
            
            # Test 5: Verify token is invalid after logout
            response, status = self.make_request("GET", "/auth/me", headers={"Authorization": f"Bearer {old_token}"}, expect_status=401)
            if status == 401:
                self.log_test("Token invalidation after logout", True, "Token properly invalidated")
            else:
                self.log_test("Token invalidation after logout", False, f"Status: {status}")
        else:
            self.log_test("POST /auth/logout", False, f"Status: {status}")
            
        return True
        
    def test_languages_endpoints(self):
        """Test language and lesson endpoints"""
        print("\n=== TESTING LANGUAGES ENDPOINTS ===")
        
        # Test 1: Get all languages
        response, status = self.make_request("GET", "/languages")
        
        if status == 200 and response and isinstance(response, list):
            expected_languages = ["python", "javascript", "java", "cpp", "csharp", "ruby", 
                                "go", "rust", "swift", "kotlin", "typescript", "php", 
                                "sql", "html_css", "skript", "lua"]
            
            language_ids = [lang["id"] for lang in response]
            missing_languages = [lang for lang in expected_languages if lang not in language_ids]
            
            if len(response) == 16 and not missing_languages:
                self.log_test("GET /languages", True, f"All 16 languages present")
            else:
                self.log_test("GET /languages", False, 
                            f"Expected 16 languages, got {len(response)}. Missing: {missing_languages}")
        else:
            self.log_test("GET /languages", False, f"Status: {status}")
            return False
            
        # Test 2: Get Python lessons (should have 30 lessons)
        response, status = self.make_request("GET", "/languages/python/lessons")
        
        if status == 200 and response and isinstance(response, list):
            if len(response) == 30:
                self.log_test("GET /languages/python/lessons", True, f"Python has 30 lessons")
                
                # Check lesson structure
                first_lesson = response[0]
                expected_fields = ["id", "title", "description", "xp", "unit"]
                missing_fields = [f for f in expected_fields if f not in first_lesson]
                
                if not missing_fields:
                    self.log_test("Lesson structure", True, "All required fields present")
                else:
                    self.log_test("Lesson structure", False, f"Missing fields: {missing_fields}")
                    
                # Check units (should be 1-6)
                units = set(lesson["unit"] for lesson in response)
                if units == {1, 2, 3, 4, 5, 6}:
                    self.log_test("Python lesson units", True, "6 units present (1-6)")
                else:
                    self.log_test("Python lesson units", False, f"Units found: {sorted(units)}")
                    
            else:
                self.log_test("GET /languages/python/lessons", False, f"Expected 30 lessons, got {len(response)}")
        else:
            self.log_test("GET /languages/python/lessons", False, f"Status: {status}")
            
        # Test 3: Get specific lesson with exercises
        response, status = self.make_request("GET", "/languages/python/lessons/python_1_1")
        
        if status == 200 and response and "exercises" in response:
            exercises = response["exercises"]
            if len(exercises) >= 3:
                self.log_test("GET specific lesson", True, f"Lesson has {len(exercises)} exercises")
                
                # Check exercise types
                exercise_types = [ex["type"] for ex in exercises]
                expected_types = ["multiple_choice", "code", "fill_blank"]
                found_types = [t for t in expected_types if t in exercise_types]
                
                if len(found_types) >= 2:
                    self.log_test("Exercise types", True, f"Found types: {found_types}")
                else:
                    self.log_test("Exercise types", False, f"Expected multiple types, found: {exercise_types}")
            else:
                self.log_test("GET specific lesson", False, f"Expected 3+ exercises, got {len(exercises)}")
        else:
            self.log_test("GET specific lesson", False, f"Status: {status}")
            
        return True
        
    def test_progress_endpoints(self):
        """Test progress tracking endpoints"""
        print("\n=== TESTING PROGRESS ENDPOINTS ===")
        
        # First, login to get a token
        user_data = TEST_CREDENTIALS["user1"]
        login_data = {"email": user_data["email"], "password": user_data["password"]}
        response, status = self.make_request("POST", "/auth/login", login_data)
        
        if status != 200 or not response or "token" not in response:
            self.log_test("Login for progress tests", False, "Could not login")
            return False
            
        self.token = response["token"]
        
        # Test 1: Get progress for Python (should be empty initially)
        response, status = self.make_request("GET", "/progress/python")
        
        if status == 200 and response:
            expected_fields = ["total_lessons", "completed_lessons", "progress_percent"]
            missing_fields = [f for f in expected_fields if f not in response]
            
            if not missing_fields:
                self.log_test("GET /progress/python", True, 
                            f"Progress: {response['completed_lessons']}/{response['total_lessons']} ({response['progress_percent']}%)")
            else:
                self.log_test("GET /progress/python", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("GET /progress/python", False, f"Status: {status}")
            
        # Test 2: Complete a lesson
        lesson_completion = {
            "lesson_id": "python_1_1",
            "language": "python",
            "answers": [
                {"selected": 0},  # multiple choice
                {"code": "print('Hello, World!')"},  # code
                {"answer": "print"}  # fill blank
            ]
        }
        
        response, status = self.make_request("POST", "/progress/complete", lesson_completion)
        
        if status == 200 and response:
            expected_fields = ["score", "xp_earned", "new_xp", "new_level", "hearts", "correct", "total"]
            missing_fields = [f for f in expected_fields if f not in response]
            
            if not missing_fields:
                self.log_test("POST /progress/complete", True, 
                            f"Score: {response['score']}%, XP: +{response['xp_earned']}, Level: {response['new_level']}")
                
                # Check if XP was awarded
                if response["xp_earned"] > 0:
                    self.log_test("XP award", True, f"Earned {response['xp_earned']} XP")
                else:
                    self.log_test("XP award", False, "No XP earned")
                    
                # Check if badges were awarded
                if "new_badges" in response and response["new_badges"]:
                    self.log_test("Badge award", True, f"Badges: {response['new_badges']}")
                else:
                    self.log_test("Badge award", False, "No badges awarded")
                    
            else:
                self.log_test("POST /progress/complete", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("POST /progress/complete", False, f"Status: {status}")
            
        # Test 3: Check progress after completion
        response, status = self.make_request("GET", "/progress/python")
        
        if status == 200 and response:
            if response["completed_lessons"] >= 1:
                self.log_test("Progress after completion", True, f"Completed: {response['completed_lessons']}")
            else:
                self.log_test("Progress after completion", False, "Lesson not marked as completed")
        else:
            self.log_test("Progress after completion", False, f"Status: {status}")
            
        return True
        
    def test_social_endpoints(self):
        """Test social features: leaderboard, friends, badges"""
        print("\n=== TESTING SOCIAL ENDPOINTS ===")
        
        # Test 1: Get leaderboard
        response, status = self.make_request("GET", "/leaderboard")
        
        if status == 200 and response and isinstance(response, list):
            if len(response) <= 50:  # Should limit to 50 users
                self.log_test("GET /leaderboard", True, f"Leaderboard has {len(response)} users")
                
                if response:  # If there are users
                    first_user = response[0]
                    expected_fields = ["username", "xp", "level", "streak", "badges_count"]
                    missing_fields = [f for f in expected_fields if f not in first_user]
                    
                    if not missing_fields:
                        self.log_test("Leaderboard user structure", True, "All fields present")
                    else:
                        self.log_test("Leaderboard user structure", False, f"Missing: {missing_fields}")
            else:
                self.log_test("GET /leaderboard", False, f"Too many users: {len(response)}")
        else:
            self.log_test("GET /leaderboard", False, f"Status: {status}")
            
        # Need to be logged in for friend operations
        if not self.token:
            user_data = TEST_CREDENTIALS["user1"]
            login_data = {"email": user_data["email"], "password": user_data["password"]}
            response, status = self.make_request("POST", "/auth/login", login_data)
            if status == 200 and response and "token" in response:
                self.token = response["token"]
            else:
                self.log_test("Login for social tests", False, "Could not login")
                return False
                
        # Test 2: Create second user for friend testing
        user2_data = TEST_CREDENTIALS["user2"]
        response, status = self.make_request("POST", "/auth/register", user2_data, expect_status=200)
        
        if status == 400:  # User might already exist
            self.log_test("Second user creation", True, "User already exists (expected)")
        elif status == 200:
            self.log_test("Second user creation", True, "Second user created")
        else:
            self.log_test("Second user creation", False, f"Status: {status}")
            
        # Test 3: Add friend
        friend_request = {"friend_username": user2_data["username"]}
        response, status = self.make_request("POST", "/friends/add", friend_request)
        
        if status == 200:
            self.log_test("POST /friends/add", True, f"Added {user2_data['username']} as friend")
        elif status == 400:  # Might already be friends
            self.log_test("POST /friends/add", True, "Already friends (expected)")
        else:
            self.log_test("POST /friends/add", False, f"Status: {status}")
            
        # Test 4: Get friends list
        response, status = self.make_request("GET", "/friends")
        
        if status == 200 and response is not None:
            if isinstance(response, list):
                self.log_test("GET /friends", True, f"Friends list has {len(response)} friends")
            else:
                self.log_test("GET /friends", False, "Response is not a list")
        else:
            self.log_test("GET /friends", False, f"Status: {status}")
            
        # Test 5: Get badges
        response, status = self.make_request("GET", "/badges")
        
        if status == 200 and response and isinstance(response, list):
            if len(response) >= 10:  # Should have multiple badges available
                self.log_test("GET /badges", True, f"Found {len(response)} available badges")
                
                # Check badge structure
                if response:
                    first_badge = response[0]
                    expected_fields = ["id", "name", "description", "icon"]
                    missing_fields = [f for f in expected_fields if f not in first_badge]
                    
                    if not missing_fields:
                        self.log_test("Badge structure", True, "All fields present")
                    else:
                        self.log_test("Badge structure", False, f"Missing: {missing_fields}")
            else:
                self.log_test("GET /badges", False, f"Expected 10+ badges, got {len(response)}")
        else:
            self.log_test("GET /badges", False, f"Status: {status}")
            
        return True
        
    def test_error_handling(self):
        """Test error cases and edge conditions"""
        print("\n=== TESTING ERROR HANDLING ===")
        
        # Test 1: Invalid login credentials
        invalid_login = {"email": "nonexistent@test.com", "password": "wrong"}
        response, status = self.make_request("POST", "/auth/login", invalid_login, expect_status=401)
        
        if status == 401:
            self.log_test("Invalid login credentials", True, "Properly rejected")
        else:
            self.log_test("Invalid login credentials", False, f"Status: {status}")
            
        # Test 2: Access protected endpoint without token
        response, status = self.make_request("GET", "/auth/me", headers={}, expect_status=401)
        
        if status == 401:
            self.log_test("Protected endpoint without auth", True, "Properly rejected")
        else:
            self.log_test("Protected endpoint without auth", False, f"Status: {status}")
            
        # Test 3: Invalid language ID
        response, status = self.make_request("GET", "/languages/invalid/lessons", expect_status=404)
        
        if status == 404:
            self.log_test("Invalid language ID", True, "Properly rejected")
        else:
            self.log_test("Invalid language ID", False, f"Status: {status}")
            
        # Test 4: Invalid lesson ID
        response, status = self.make_request("GET", "/languages/python/lessons/invalid", expect_status=404)
        
        if status == 404:
            self.log_test("Invalid lesson ID", True, "Properly rejected")
        else:
            self.log_test("Invalid lesson ID", False, f"Status: {status}")
            
        return True
        
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Codero Backend API Tests")
        print(f"📍 Base URL: {BASE_URL}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run test suites
        self.test_auth_endpoints()
        self.test_languages_endpoints()
        self.test_progress_endpoints()
        self.test_social_endpoints()
        self.test_error_handling()
        
        # Summary
        print("\n" + "="*50)
        print("📊 TEST SUMMARY")
        print("="*50)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"   ❌ {test['test']}: {test['details']}")
                    
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = CoderoAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)