#!/usr/bin/env python3
"""
Comprehensive Niche Language Testing for Codero Games
Tests Bug Hunter, Speed Code, and Lessons for niche languages: Shell, Haskell, Elixir, Zig, Lua, Skript
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://codero-stack.preview.emergentagent.com/api"

class NicheLanguageTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.test_results = []
        self.niche_languages = ["shell", "haskell", "elixir", "zig", "lua"]
        self.lesson_languages = ["haskell", "elixir", "zig", "lua", "skript"]
        
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
    
    def register_test_user(self) -> bool:
        """Register a new test user for niche language testing"""
        try:
            import time
            unique_id = int(time.time())
            response = requests.post(f"{BACKEND_URL}/auth/register", json={
                "username": f"nichetester{unique_id}",
                "email": f"nichetest{unique_id}@codero.com", 
                "password": "test123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.user_id = data.get("user", {}).get("id")
                self.log_test("User Registration", True, f"Registered niche language test user")
                return True
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_bug_hunter_niche_languages(self) -> bool:
        """Test Bug Hunter endpoints for all niche languages"""
        all_passed = True
        
        for language in self.niche_languages:
            try:
                response = requests.get(f"{BACKEND_URL}/games/bug-hunter/{language}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate response structure
                    required_fields = ["language", "challenges", "total"]
                    if not all(field in data for field in required_fields):
                        self.log_test(f"Bug Hunter GET {language}", False, f"Missing required fields. Got: {list(data.keys())}")
                        all_passed = False
                        continue
                    
                    # Check language matches
                    if data.get("language") != language:
                        self.log_test(f"Bug Hunter GET {language}", False, f"Expected language '{language}', got '{data.get('language')}'")
                        all_passed = False
                        continue
                    
                    # Check challenges structure
                    challenges = data.get("challenges", [])
                    if len(challenges) == 0:
                        self.log_test(f"Bug Hunter GET {language}", False, f"No challenges returned for {language}")
                        all_passed = False
                        continue
                    
                    # Validate challenge IDs have language prefix
                    language_specific = False
                    expected_prefixes = {
                        "shell": "sh_",
                        "haskell": "hs_", 
                        "elixir": "ex_",
                        "zig": "zig_",
                        "lua": "lua_"
                    }
                    
                    expected_prefix = expected_prefixes.get(language, f"{language}_")
                    
                    for challenge in challenges:
                        challenge_id = challenge.get("id", "")
                        if challenge_id.startswith(expected_prefix):
                            language_specific = True
                            break
                    
                    if not language_specific:
                        self.log_test(f"Bug Hunter GET {language}", False, f"No {language}-specific challenges found. IDs: {[c.get('id') for c in challenges]}")
                        all_passed = False
                        continue
                    
                    # Validate challenge structure
                    for i, challenge in enumerate(challenges):
                        required_challenge_fields = ["id", "code", "question", "options", "concept"]
                        if not all(field in challenge for field in required_challenge_fields):
                            self.log_test(f"Bug Hunter GET {language}", False, f"Challenge {i} missing fields: {list(challenge.keys())}")
                            all_passed = False
                            break
                        
                        # Ensure correct answer is NOT exposed
                        if "correct" in challenge:
                            self.log_test(f"Bug Hunter GET {language}", False, f"Challenge {i} exposes correct answer - security issue!")
                            all_passed = False
                            break
                    else:
                        self.log_test(f"Bug Hunter GET {language}", True, f"Retrieved {len(challenges)} {language}-specific challenges")
                else:
                    self.log_test(f"Bug Hunter GET {language}", False, f"Status: {response.status_code}, Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Bug Hunter GET {language}", False, f"Exception: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_bug_hunter_check_niche(self) -> bool:
        """Test Bug Hunter check endpoint for a niche language"""
        try:
            # Test with Haskell
            response = requests.get(f"{BACKEND_URL}/games/bug-hunter/haskell")
            if response.status_code != 200:
                self.log_test("Bug Hunter CHECK Haskell", False, "Could not get Haskell challenges")
                return False
            
            challenges = response.json().get("challenges", [])
            if not challenges:
                self.log_test("Bug Hunter CHECK Haskell", False, "No Haskell challenges available")
                return False
            
            challenge = challenges[0]
            challenge_id = challenge["id"]
            
            # Test with correct answer (option 0)
            check_response = requests.post(f"{BACKEND_URL}/games/bug-hunter/haskell/check", json={
                "challenge_id": challenge_id,
                "selected": 0
            })
            
            if check_response.status_code == 200:
                data = check_response.json()
                
                # Validate response structure
                required_fields = ["correct", "correct_answer", "fixed_code", "explanation"]
                if not all(field in data for field in required_fields):
                    self.log_test("Bug Hunter CHECK Haskell", False, f"Missing required fields. Got: {list(data.keys())}")
                    return False
                
                self.log_test("Bug Hunter CHECK Haskell", True, f"Haskell challenge check working. Challenge: {challenge_id}")
                return True
            else:
                self.log_test("Bug Hunter CHECK Haskell", False, f"Status: {check_response.status_code}, Response: {check_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Bug Hunter CHECK Haskell", False, f"Exception: {str(e)}")
            return False
    
    def test_speed_code_niche_languages(self) -> bool:
        """Test Speed Code endpoints for all niche languages"""
        all_passed = True
        
        for language in self.niche_languages:
            try:
                response = requests.get(f"{BACKEND_URL}/games/speed-code/{language}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate response structure
                    required_fields = ["language", "challenges", "total"]
                    if not all(field in data for field in required_fields):
                        self.log_test(f"Speed Code GET {language}", False, f"Missing required fields. Got: {list(data.keys())}")
                        all_passed = False
                        continue
                    
                    # Check language matches
                    if data.get("language") != language:
                        self.log_test(f"Speed Code GET {language}", False, f"Expected language '{language}', got '{data.get('language')}'")
                        all_passed = False
                        continue
                    
                    # Check challenges structure
                    challenges = data.get("challenges", [])
                    if len(challenges) == 0:
                        self.log_test(f"Speed Code GET {language}", False, f"No challenges returned for {language}")
                        all_passed = False
                        continue
                    
                    # Validate challenge IDs have language prefix
                    language_specific = False
                    expected_prefixes = {
                        "shell": "sh_",
                        "haskell": "hs_", 
                        "elixir": "ex_",
                        "zig": "zig_",
                        "lua": "lua_"
                    }
                    
                    expected_prefix = expected_prefixes.get(language, f"{language}_")
                    
                    for challenge in challenges:
                        challenge_id = challenge.get("id", "")
                        if challenge_id.startswith(expected_prefix):
                            language_specific = True
                            break
                    
                    if not language_specific:
                        self.log_test(f"Speed Code GET {language}", False, f"No {language}-specific challenges found. IDs: {[c.get('id') for c in challenges]}")
                        all_passed = False
                        continue
                    
                    # Validate challenge structure
                    for i, challenge in enumerate(challenges):
                        required_challenge_fields = ["id", "prompt", "time_limit", "points", "concept"]
                        if not all(field in challenge for field in required_challenge_fields):
                            self.log_test(f"Speed Code GET {language}", False, f"Challenge {i} missing fields: {list(challenge.keys())}")
                            all_passed = False
                            break
                        
                        # Ensure expected answer is NOT exposed
                        if "expected" in challenge:
                            self.log_test(f"Speed Code GET {language}", False, f"Challenge {i} exposes expected answer - security issue!")
                            all_passed = False
                            break
                    else:
                        self.log_test(f"Speed Code GET {language}", True, f"Retrieved {len(challenges)} {language}-specific speed challenges")
                else:
                    self.log_test(f"Speed Code GET {language}", False, f"Status: {response.status_code}, Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Speed Code GET {language}", False, f"Exception: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_speed_code_check_niche(self) -> bool:
        """Test Speed Code check endpoint for a niche language"""
        try:
            # Test with Shell
            check_response = requests.post(f"{BACKEND_URL}/games/speed-code/shell/check", json={
                "challenge_id": "sh_speed_1",
                "code": "echo 'Hello World'"
            })
            
            if check_response.status_code == 200:
                data = check_response.json()
                
                # Validate response structure
                required_fields = ["correct", "expected", "points"]
                if not all(field in data for field in required_fields):
                    self.log_test("Speed Code CHECK Shell", False, f"Missing required fields. Got: {list(data.keys())}")
                    return False
                
                # Should be correct
                if not data.get("correct"):
                    self.log_test("Speed Code CHECK Shell", False, f"Expected correct answer but got: {data}")
                    return False
                
                self.log_test("Speed Code CHECK Shell", True, f"Shell speed code check working. Points: {data.get('points')}")
                return True
            else:
                self.log_test("Speed Code CHECK Shell", False, f"Status: {check_response.status_code}, Response: {check_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Speed Code CHECK Shell", False, f"Exception: {str(e)}")
            return False
    
    def test_niche_language_lessons(self) -> bool:
        """Test lessons endpoints for niche languages"""
        all_passed = True
        
        expected_topics = {
            "haskell": ["Types & Values", "Pattern Matching", "Guards", "Monads"],
            "elixir": ["Atoms", "Pattern Matching", "Pipe Operator", "GenServer"],
            "zig": ["Comptime", "Allocators", "Error Unions"],
            "lua": ["Tables", "Metatables", "Coroutines"],
            "skript": ["Events", "Commands", "Effects"]
        }
        
        for language in self.lesson_languages:
            try:
                response = requests.get(f"{BACKEND_URL}/languages/{language}/lessons")
                
                if response.status_code == 200:
                    lessons = response.json()
                    
                    if not isinstance(lessons, list):
                        self.log_test(f"Lessons GET {language}", False, f"Expected list, got {type(lessons)}")
                        all_passed = False
                        continue
                    
                    # Check for 30 lessons (6 units * 5 topics)
                    if len(lessons) != 30:
                        self.log_test(f"Lessons GET {language}", False, f"Expected 30 lessons, got {len(lessons)}")
                        all_passed = False
                        continue
                    
                    # Check for language-specific topics in lesson titles
                    lesson_titles = [lesson.get("title", "") for lesson in lessons]
                    expected_for_lang = expected_topics.get(language, [])
                    
                    found_specific_topics = False
                    for expected_topic in expected_for_lang:
                        for title in lesson_titles:
                            if expected_topic.lower() in title.lower():
                                found_specific_topics = True
                                break
                        if found_specific_topics:
                            break
                    
                    if not found_specific_topics and expected_for_lang:
                        self.log_test(f"Lessons GET {language}", False, f"No {language}-specific topics found. Expected: {expected_for_lang}")
                        all_passed = False
                        continue
                    
                    # Validate lesson structure
                    for i, lesson in enumerate(lessons[:3]):  # Check first 3 lessons
                        required_fields = ["id", "title", "description", "xp", "unit", "unit_name"]
                        if not all(field in lesson for field in required_fields):
                            self.log_test(f"Lessons GET {language}", False, f"Lesson {i} missing fields: {list(lesson.keys())}")
                            all_passed = False
                            break
                    else:
                        self.log_test(f"Lessons GET {language}", True, f"Retrieved 30 {language} lessons with language-specific content")
                else:
                    self.log_test(f"Lessons GET {language}", False, f"Status: {response.status_code}, Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Lessons GET {language}", False, f"Exception: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def run_all_tests(self):
        """Run all niche language tests"""
        print("🔧 Starting Codero Niche Language Support Tests")
        print("=" * 60)
        
        # Register user first
        if not self.register_test_user():
            print("❌ Cannot proceed without user registration")
            return False
        
        # Run all niche language tests
        tests = [
            ("Bug Hunter Niche Languages", self.test_bug_hunter_niche_languages),
            ("Bug Hunter Check (Haskell)", self.test_bug_hunter_check_niche),
            ("Speed Code Niche Languages", self.test_speed_code_niche_languages),
            ("Speed Code Check (Shell)", self.test_speed_code_check_niche),
            ("Niche Language Lessons", self.test_niche_language_lessons),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            print("-" * 40)
            if test_func():
                passed += 1
        
        print("=" * 60)
        print(f"🎯 Test Results: {passed}/{total} tests passed ({int(passed/total*100)}%)")
        
        if passed == total:
            print("✅ All niche language support tests passed!")
            return True
        else:
            print("❌ Some tests failed. Check details above.")
            
            # Print failed tests
            failed_tests = [result for result in self.test_results if not result["success"]]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"  - {test['test']}: {test['details']}")
            
            return False

if __name__ == "__main__":
    tester = NicheLanguageTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)