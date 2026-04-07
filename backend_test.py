#!/usr/bin/env python3
"""
Enhanced Codero Backend API Test Suite
Tests all enhanced features including 20 languages, gems, daily challenges, shop, and settings.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://pixel-coder-3.preview.emergentagent.com/api"
TEST_USER = {
    "username": "enhancedtest",
    "email": "enhanced@codero.com", 
    "password": "test123"
}

class CoderoAPITester:
    def __init__(self):
        self.token = None
        self.user_data = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
        
    def make_request(self, method, endpoint, data=None, auth_required=True):
        """Make HTTP request with proper error handling"""
        url = f"{BASE_URL}{endpoint}"
        
        headers = {}
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            return None
            
    def test_api_health(self):
        """Test if API is responding"""
        self.log("Testing API health...")
        response = self.make_request('GET', '/', auth_required=False)
        
        if response and response.status_code == 200:
            data = response.json()
            self.log(f"✅ API is healthy: {data.get('message', 'OK')}")
            return True
        else:
            self.log(f"❌ API health check failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_user_registration(self):
        """Test enhanced user registration with gems and settings"""
        self.log("Testing enhanced user registration...")
        
        # Try login first since user might already exist
        if self.test_user_login():
            return True
            
        response = self.make_request('POST', '/auth/register', TEST_USER, auth_required=False)
        
        if response and response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            self.user_data = data.get('user')
            
            # Verify enhanced features
            gems = self.user_data.get('gems', 0)
            settings = self.user_data.get('settings', {})
            
            if gems == 10:
                self.log("✅ User starts with 10 gems")
            else:
                self.log(f"❌ Expected 10 gems, got {gems}", "ERROR")
                
            if settings and 'theme' in settings:
                self.log("✅ User has default settings")
            else:
                self.log("❌ User missing default settings", "ERROR")
                
            self.log(f"✅ User registered successfully with ID: {self.user_data.get('id')}")
            return True
        else:
            if response:
                try:
                    error_msg = response.json().get('detail', 'Unknown error')
                    if 'already exists' in error_msg:
                        self.log("User already exists, attempting login...")
                        return self.test_user_login()
                    else:
                        self.log(f"❌ Registration failed: {error_msg}", "ERROR")
                        return False
                except:
                    self.log(f"❌ Registration failed with status {response.status_code}", "ERROR")
                    return False
            else:
                self.log("❌ Registration failed: No response", "ERROR")
                return False
                
    def test_user_login(self):
        """Test user login with enhanced features"""
        self.log("Testing user login...")
        
        login_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        
        response = self.make_request('POST', '/auth/login', login_data, auth_required=False)
        
        if response and response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            self.user_data = data.get('user')
            
            # Verify enhanced features
            gems = self.user_data.get('gems', 0)
            settings = self.user_data.get('settings', {})
            
            self.log(f"✅ Login successful. Gems: {gems}, Settings: {bool(settings)}")
            return True
        else:
            if response:
                try:
                    error_msg = response.json().get('detail', 'Unknown error')
                    self.log(f"❌ Login failed: {error_msg}", "ERROR")
                    return False
                except:
                    self.log(f"❌ Login failed with status {response.status_code}", "ERROR")
                    return False
            else:
                self.log("❌ Login failed: No response", "ERROR")
                return False
            
    def test_languages_count(self):
        """Test that we have 20 programming languages including new ones"""
        self.log("Testing languages endpoint...")
        
        response = self.make_request('GET', '/languages', auth_required=False)
        
        if response and response.status_code == 200:
            languages = response.json()
            
            if len(languages) == 20:
                self.log(f"✅ Found {len(languages)} languages (expected 20)")
            else:
                self.log(f"❌ Expected 20 languages, found {len(languages)}", "ERROR")
                
            # Check for new languages
            language_ids = [lang['id'] for lang in languages]
            new_languages = ['zig', 'elixir', 'shell', 'haskell']
            
            for new_lang in new_languages:
                if new_lang in language_ids:
                    self.log(f"✅ Found new language: {new_lang}")
                else:
                    self.log(f"❌ Missing new language: {new_lang}", "ERROR")
                    
            return len(languages) == 20 and all(lang in language_ids for lang in new_languages)
        else:
            self.log(f"❌ Languages request failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_lessons_count(self):
        """Test that each language has 30 lessons"""
        self.log("Testing lessons count...")
        
        # Test Python lessons
        response = self.make_request('GET', '/languages/python/lessons', auth_required=False)
        
        if response and response.status_code == 200:
            lessons = response.json()
            
            if len(lessons) == 30:
                self.log(f"✅ Python has {len(lessons)} lessons (expected 30)")
            else:
                self.log(f"❌ Python expected 30 lessons, found {len(lessons)}", "ERROR")
                
            # Test Shell lessons (new language)
            response = self.make_request('GET', '/languages/shell/lessons', auth_required=False)
            
            if response and response.status_code == 200:
                shell_lessons = response.json()
                
                if len(shell_lessons) == 30:
                    self.log(f"✅ Shell has {len(shell_lessons)} lessons (expected 30)")
                else:
                    self.log(f"❌ Shell expected 30 lessons, found {len(shell_lessons)}", "ERROR")
                    
                return len(lessons) == 30 and len(shell_lessons) == 30
            else:
                self.log(f"❌ Shell lessons request failed: {response.status_code if response else 'No response'}", "ERROR")
                return False
        else:
            self.log(f"❌ Python lessons request failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_lesson_exercises(self):
        """Test that lessons have 10 exercises each"""
        self.log("Testing lesson exercises...")
        
        response = self.make_request('GET', '/languages/python/lessons/python_1_1', auth_required=False)
        
        if response and response.status_code == 200:
            lesson = response.json()
            exercises = lesson.get('exercises', [])
            
            if len(exercises) == 10:
                self.log(f"✅ Lesson has {len(exercises)} exercises (expected 10)")
                
                # Check exercise types
                types = [ex.get('type') for ex in exercises]
                expected_types = ['multiple_choice', 'code', 'fill_blank']
                
                if any(t in types for t in expected_types):
                    self.log("✅ Lesson has varied exercise types")
                    return True
                else:
                    self.log("❌ Lesson missing expected exercise types", "ERROR")
                    return False
            else:
                self.log(f"❌ Expected 10 exercises, found {len(exercises)}", "ERROR")
                return False
        else:
            self.log(f"❌ Lesson request failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_settings_api(self):
        """Test settings API endpoints"""
        self.log("Testing settings API...")
        
        if not self.token:
            self.log("❌ No auth token for settings test", "ERROR")
            return False
            
        # Get current settings
        response = self.make_request('GET', '/settings')
        
        if response and response.status_code == 200:
            current_settings = response.json()
            self.log(f"✅ Retrieved current settings: {len(current_settings)} items")
            
            # Update settings
            new_settings = {
                "settings": {
                    "theme": "light",
                    "font_size": "large",
                    "sound_effects": False,
                    "notifications": True
                }
            }
            
            response = self.make_request('PUT', '/settings', new_settings)
            
            if response and response.status_code == 200:
                self.log("✅ Settings updated successfully")
                
                # Verify settings were updated
                response = self.make_request('GET', '/settings')
                if response and response.status_code == 200:
                    updated_settings = response.json()
                    if updated_settings.get('theme') == 'light':
                        self.log("✅ Settings update verified")
                        return True
                    else:
                        self.log("❌ Settings update not reflected", "ERROR")
                        return False
                else:
                    self.log("❌ Failed to verify settings update", "ERROR")
                    return False
            else:
                self.log(f"❌ Settings update failed: {response.status_code if response else 'No response'}", "ERROR")
                return False
        else:
            self.log(f"❌ Get settings failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_enhanced_progress(self):
        """Test enhanced progress tracking with combo multipliers and gems"""
        self.log("Testing enhanced progress tracking...")
        
        if not self.token:
            self.log("❌ No auth token for progress test", "ERROR")
            return False
            
        # Complete a lesson to test enhanced features
        lesson_data = {
            "lesson_id": "python_1_1",
            "language": "python",
            "answers": [
                {"selected": 0},  # Correct answer for first question
                {"selected": 0},  # Correct answer for second question
                {"code": "print('Hello, World!')"},  # Code exercise
                {"answer": "print"},  # Fill blank
                {"selected": 0},  # Multiple choice
                {"code": "print('YourName')"},  # Code
                {"selected": 0},  # Multiple choice
                {"answer": "comment"},  # Fill blank
                {"code": "print('Line 1')\nprint('Line 2')"},  # Code
                {"selected": 0},  # Multiple choice
            ],
            "time_taken": 90  # Under 2 minutes for speed bonus
        }
        
        response = self.make_request('POST', '/progress/complete', lesson_data)
        
        if response and response.status_code == 200:
            result = response.json()
            
            # Check enhanced features
            combo_multiplier = result.get('combo_multiplier', 1.0)
            gems_earned = result.get('gems_earned', 0)
            daily_xp = result.get('daily_xp', 0)
            daily_goal = result.get('daily_goal', 50)
            
            self.log(f"✅ Lesson completed successfully")
            self.log(f"   Combo multiplier: {combo_multiplier}")
            self.log(f"   Gems earned: {gems_earned}")
            self.log(f"   Daily XP: {daily_xp}/{daily_goal}")
            
            # Verify enhanced features
            if 1.0 <= combo_multiplier <= 5.0:
                self.log("✅ Combo multiplier in valid range")
            else:
                self.log(f"❌ Invalid combo multiplier: {combo_multiplier}", "ERROR")
                
            if gems_earned >= 0:
                self.log("✅ Gems system working")
            else:
                self.log("❌ Gems system issue", "ERROR")
                
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log(f"❌ Progress completion failed: {error_msg}", "ERROR")
            return False
            
    def test_daily_challenge(self):
        """Test daily challenge system"""
        self.log("Testing daily challenge system...")
        
        if not self.token:
            self.log("❌ No auth token for daily challenge test", "ERROR")
            return False
            
        # Get daily challenge
        response = self.make_request('GET', '/daily-challenge')
        
        if response and response.status_code == 200:
            challenge = response.json()
            
            challenge_id = challenge.get('id')
            exercises = challenge.get('exercises', [])
            xp_reward = challenge.get('xp_reward', 0)
            gem_reward = challenge.get('gem_reward', 0)
            
            self.log(f"✅ Daily challenge retrieved: {challenge.get('title', 'Unknown')}")
            self.log(f"   Exercises: {len(exercises)}")
            self.log(f"   XP reward: {xp_reward}")
            self.log(f"   Gem reward: {gem_reward}")
            
            if challenge.get('completed'):
                self.log("ℹ️  Challenge already completed today")
                return True
                
            # Complete the challenge
            answers = []
            for ex in exercises:
                if ex['type'] == 'multiple_choice':
                    answers.append({"selected": ex.get('correct', 0)})
                elif ex['type'] == 'code':
                    answers.append({"code": ex.get('solution', '')})
                elif ex['type'] == 'fill_blank':
                    answers.append({"answer": ex.get('answer', '')})
                    
            completion_data = {
                "challenge_id": challenge_id,
                "answers": answers
            }
            
            response = self.make_request('POST', '/daily-challenge/complete', completion_data)
            
            if response and response.status_code == 200:
                result = response.json()
                
                score = result.get('score', 0)
                xp_earned = result.get('xp_earned', 0)
                gems_earned = result.get('gems_earned', 0)
                passed = result.get('passed', False)
                
                self.log(f"✅ Daily challenge completed")
                self.log(f"   Score: {score}%")
                self.log(f"   XP earned: {xp_earned}")
                self.log(f"   Gems earned: {gems_earned}")
                self.log(f"   Passed: {passed}")
                
                return True
            else:
                error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
                if 'Already completed' in error_msg:
                    self.log("ℹ️  Challenge already completed today")
                    return True
                else:
                    self.log(f"❌ Challenge completion failed: {error_msg}", "ERROR")
                    return False
        else:
            self.log(f"❌ Daily challenge request failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_shop_system(self):
        """Test shop system for buying hearts and streak freezes"""
        self.log("Testing shop system...")
        
        if not self.token:
            self.log("❌ No auth token for shop test", "ERROR")
            return False
            
        # Get current user data to check gems
        response = self.make_request('GET', '/auth/me')
        
        if response and response.status_code == 200:
            user = response.json()
            current_gems = user.get('gems', 0)
            current_hearts = user.get('hearts', 5)
            
            self.log(f"Current gems: {current_gems}, hearts: {current_hearts}")
            
            if current_gems >= 10:
                # Test buying hearts
                response = self.make_request('POST', '/shop/buy-hearts')
                
                if response and response.status_code == 200:
                    result = response.json()
                    self.log(f"✅ Hearts purchased: {result.get('message', 'Success')}")
                    
                    # Test buying streak freeze if enough gems
                    if current_gems >= 20:
                        response = self.make_request('POST', '/shop/buy-streak-freeze')
                        
                        if response and response.status_code == 200:
                            result = response.json()
                            self.log(f"✅ Streak freeze purchased: {result.get('message', 'Success')}")
                            return True
                        else:
                            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
                            self.log(f"❌ Streak freeze purchase failed: {error_msg}", "ERROR")
                            return False
                    else:
                        self.log("ℹ️  Not enough gems for streak freeze (need 20)")
                        return True
                else:
                    error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
                    self.log(f"❌ Heart purchase failed: {error_msg}", "ERROR")
                    return False
            else:
                self.log("ℹ️  Not enough gems for shop purchases (need 10 for hearts)")
                return True
        else:
            self.log(f"❌ Failed to get user data: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def test_badges_count(self):
        """Test that we have 20 badges"""
        self.log("Testing badges system...")
        
        response = self.make_request('GET', '/badges', auth_required=False)
        
        if response and response.status_code == 200:
            badges = response.json()
            
            if len(badges) == 20:
                self.log(f"✅ Found {len(badges)} badges (expected 20)")
                
                # Check for some specific badges
                badge_ids = [badge['id'] for badge in badges]
                expected_badges = ['combo_king', 'daily_achiever', 'lesson_master', 'no_mistakes']
                
                found_badges = [badge for badge in expected_badges if badge in badge_ids]
                self.log(f"✅ Found enhanced badges: {', '.join(found_badges)}")
                
                return len(badges) == 20
            else:
                self.log(f"❌ Expected 20 badges, found {len(badges)}", "ERROR")
                return False
        else:
            self.log(f"❌ Badges request failed: {response.status_code if response else 'No response'}", "ERROR")
            return False
            
    def run_all_tests(self):
        """Run all test cases"""
        self.log("=" * 60)
        self.log("STARTING ENHANCED CODERO BACKEND API TESTS")
        self.log("=" * 60)
        
        tests = [
            ("API Health", self.test_api_health),
            ("User Registration", self.test_user_registration),
            ("20 Languages", self.test_languages_count),
            ("30 Lessons per Language", self.test_lessons_count),
            ("10 Exercises per Lesson", self.test_lesson_exercises),
            ("Settings API", self.test_settings_api),
            ("Enhanced Progress", self.test_enhanced_progress),
            ("Daily Challenge", self.test_daily_challenge),
            ("Shop System", self.test_shop_system),
            ("20 Badges", self.test_badges_count),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n--- Testing {test_name} ---")
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name} PASSED")
                else:
                    self.log(f"❌ {test_name} FAILED", "ERROR")
            except Exception as e:
                self.log(f"❌ {test_name} ERROR: {e}", "ERROR")
                
        self.log("\n" + "=" * 60)
        self.log(f"TEST RESULTS: {passed}/{total} tests passed ({int(passed/total*100)}%)")
        self.log("=" * 60)
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! Enhanced Codero backend is working correctly.")
        else:
            self.log(f"⚠️  {total - passed} tests failed. Please check the issues above.")
            
        return passed == total

if __name__ == "__main__":
    tester = CoderoAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)