#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Codero Phase 2
Tests notification/settings/email and regression health
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# Backend URL from environment
BACKEND_URL = "https://codero-stack.preview.emergentagent.com/api"

class Phase2Tester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.user_email = None
        self.test_results = []
        
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
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_1_register_with_settings_defaults(self) -> bool:
        """Test 1: Register fresh user and verify settings defaults"""
        try:
            timestamp = int(time.time())
            username = f"phase2test_{timestamp}"
            email = f"phase2test_{timestamp}@codero.com"
            
            response = requests.post(f"{BACKEND_URL}/auth/register", json={
                "username": username,
                "email": email,
                "password": "test123"
            })
            
            if response.status_code != 200:
                self.log_test("Test 1: Register with Settings Defaults", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            self.token = data.get("token")
            user = data.get("user", {})
            self.user_id = user.get("id")
            self.user_email = email
            
            # Verify token and user present
            if not self.token or not self.user_id:
                self.log_test("Test 1: Register with Settings Defaults", False, 
                             "Missing token or user ID in response")
                return False
            
            # Verify settings defaults present
            settings = user.get("settings", {})
            required_settings = [
                "theme", "font_size", "high_contrast", "sound_effects", 
                "notifications", "email_login", "email_join", "email_vip", "email_daily"
            ]
            
            missing_settings = [s for s in required_settings if s not in settings]
            if missing_settings:
                self.log_test("Test 1: Register with Settings Defaults", False, 
                             f"Missing settings: {missing_settings}. Got: {list(settings.keys())}")
                return False
            
            # Verify default values
            expected_defaults = {
                "theme": "dark",
                "font_size": "medium",
                "high_contrast": False,
                "sound_effects": True,
                "notifications": True,
                "email_login": True,
                "email_join": True,
                "email_vip": True,
                "email_daily": True
            }
            
            mismatches = []
            for key, expected_value in expected_defaults.items():
                actual_value = settings.get(key)
                if actual_value != expected_value:
                    mismatches.append(f"{key}: expected {expected_value}, got {actual_value}")
            
            if mismatches:
                self.log_test("Test 1: Register with Settings Defaults", False, 
                             f"Default value mismatches: {', '.join(mismatches)}")
                return False
            
            self.log_test("Test 1: Register with Settings Defaults", True, 
                         f"User registered with correct settings defaults. Email: {email}")
            return True
            
        except Exception as e:
            self.log_test("Test 1: Register with Settings Defaults", False, f"Exception: {str(e)}")
            return False
    
    def test_2_login_and_check_health(self) -> bool:
        """Test 2: Login same user and verify backend health"""
        try:
            if not self.user_email:
                self.log_test("Test 2: Login and Check Health", False, "No user email from registration")
                return False
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json={
                "email": self.user_email,
                "password": "test123"
            })
            
            if response.status_code != 200:
                self.log_test("Test 2: Login and Check Health", False, 
                             f"Login failed. Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            login_token = data.get("token")
            user = data.get("user", {})
            
            if not login_token:
                self.log_test("Test 2: Login and Check Health", False, "No token in login response")
                return False
            
            # Update token for subsequent tests
            self.token = login_token
            
            # Check backend health by hitting a simple endpoint
            health_response = requests.get(f"{BACKEND_URL}/languages")
            if health_response.status_code != 200:
                self.log_test("Test 2: Login and Check Health", False, 
                             f"Backend unhealthy after login. /languages returned {health_response.status_code}")
                return False
            
            self.log_test("Test 2: Login and Check Health", True, 
                         "Login successful, backend healthy. Note: Check backend logs for queued login email.")
            return True
            
        except Exception as e:
            self.log_test("Test 2: Login and Check Health", False, f"Exception: {str(e)}")
            return False
    
    def test_3_settings_persistence(self) -> bool:
        """Test 3: PUT /api/settings and verify persistence"""
        try:
            if not self.token:
                self.log_test("Test 3: Settings Persistence", False, "No auth token")
                return False
            
            # Update settings
            new_settings = {
                "theme": "light",
                "font_size": "large",
                "high_contrast": True,
                "notifications": False,
                "email_login": False
            }
            
            put_response = requests.put(f"{BACKEND_URL}/settings", 
                                       json={"settings": new_settings},
                                       headers=self.get_headers())
            
            if put_response.status_code != 200:
                self.log_test("Test 3: Settings Persistence", False, 
                             f"PUT /settings failed. Status: {put_response.status_code}, Response: {put_response.text}")
                return False
            
            put_data = put_response.json()
            returned_settings = put_data.get("settings", {})
            
            # Verify updated settings in PUT response
            for key, value in new_settings.items():
                if returned_settings.get(key) != value:
                    self.log_test("Test 3: Settings Persistence", False, 
                                 f"PUT response: {key} = {returned_settings.get(key)}, expected {value}")
                    return False
            
            # Verify existing defaults not dropped (e.g., sound_effects, email_join, email_vip, email_daily)
            if "sound_effects" not in returned_settings:
                self.log_test("Test 3: Settings Persistence", False, 
                             "Existing default 'sound_effects' was dropped")
                return False
            
            # GET /api/settings to verify persistence
            get_response = requests.get(f"{BACKEND_URL}/settings", headers=self.get_headers())
            if get_response.status_code != 200:
                self.log_test("Test 3: Settings Persistence", False, 
                             f"GET /settings failed. Status: {get_response.status_code}")
                return False
            
            get_settings = get_response.json()
            for key, value in new_settings.items():
                if get_settings.get(key) != value:
                    self.log_test("Test 3: Settings Persistence", False, 
                                 f"GET /settings: {key} = {get_settings.get(key)}, expected {value}")
                    return False
            
            # GET /api/auth/me to verify persistence
            me_response = requests.get(f"{BACKEND_URL}/auth/me", headers=self.get_headers())
            if me_response.status_code != 200:
                self.log_test("Test 3: Settings Persistence", False, 
                             f"GET /auth/me failed. Status: {me_response.status_code}")
                return False
            
            me_data = me_response.json()
            me_settings = me_data.get("settings", {})
            for key, value in new_settings.items():
                if me_settings.get(key) != value:
                    self.log_test("Test 3: Settings Persistence", False, 
                                 f"GET /auth/me: {key} = {me_settings.get(key)}, expected {value}")
                    return False
            
            self.log_test("Test 3: Settings Persistence", True, 
                         "Settings updated and persisted correctly via PUT, GET /settings, and GET /auth/me")
            return True
            
        except Exception as e:
            self.log_test("Test 3: Settings Persistence", False, f"Exception: {str(e)}")
            return False
    
    def test_4_login_with_notifications_off(self) -> bool:
        """Test 4: Login with notifications off, verify no crash"""
        try:
            if not self.user_email:
                self.log_test("Test 4: Login with Notifications Off", False, "No user email")
                return False
            
            # Login again (notifications are now off from test 3)
            response = requests.post(f"{BACKEND_URL}/auth/login", json={
                "email": self.user_email,
                "password": "test123"
            })
            
            if response.status_code != 200:
                self.log_test("Test 4: Login with Notifications Off", False, 
                             f"Login crashed with notifications off. Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            if not data.get("token"):
                self.log_test("Test 4: Login with Notifications Off", False, 
                             "No token in response")
                return False
            
            # Update token
            self.token = data.get("token")
            
            self.log_test("Test 4: Login with Notifications Off", True, 
                         "Login successful with notifications off. Check logs for 'Skipping login email' message.")
            return True
            
        except Exception as e:
            self.log_test("Test 4: Login with Notifications Off", False, f"Exception: {str(e)}")
            return False
    
    def test_5_email_templates_list(self) -> bool:
        """Test 5: GET /api/email/templates returns all templates"""
        try:
            if not self.token:
                self.log_test("Test 5: Email Templates List", False, "No auth token")
                return False
            
            response = requests.get(f"{BACKEND_URL}/email/templates", headers=self.get_headers())
            
            if response.status_code != 200:
                self.log_test("Test 5: Email Templates List", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            templates = response.json()
            
            if not isinstance(templates, list):
                self.log_test("Test 5: Email Templates List", False, 
                             f"Expected list, got {type(templates)}")
                return False
            
            # Verify all required templates present
            required_events = ["join", "login", "vip", "daily", "test"]
            template_events = [t.get("event") for t in templates]
            
            missing_events = [e for e in required_events if e not in template_events]
            if missing_events:
                self.log_test("Test 5: Email Templates List", False, 
                             f"Missing templates: {missing_events}. Got: {template_events}")
                return False
            
            # Verify template structure
            for template in templates:
                if not all(k in template for k in ["event", "subject", "body"]):
                    self.log_test("Test 5: Email Templates List", False, 
                                 f"Template missing required fields: {template}")
                    return False
            
            self.log_test("Test 5: Email Templates List", True, 
                         f"All {len(templates)} email templates returned correctly: {template_events}")
            return True
            
        except Exception as e:
            self.log_test("Test 5: Email Templates List", False, f"Exception: {str(e)}")
            return False
    
    def test_6_email_template_update(self) -> bool:
        """Test 6: PUT /api/email/templates/login and verify update"""
        try:
            if not self.token:
                self.log_test("Test 6: Email Template Update", False, "No auth token")
                return False
            
            # Update login template
            new_subject = "Custom Login Alert - Phase 2 Test"
            new_body = "Hi {username}, you logged in at {time}. This is a custom template."
            
            put_response = requests.put(f"{BACKEND_URL}/email/templates/login",
                                       json={"subject": new_subject, "body": new_body},
                                       headers=self.get_headers())
            
            if put_response.status_code != 200:
                self.log_test("Test 6: Email Template Update", False, 
                             f"PUT failed. Status: {put_response.status_code}, Response: {put_response.text}")
                return False
            
            put_data = put_response.json()
            if put_data.get("event") != "login":
                self.log_test("Test 6: Email Template Update", False, 
                             f"PUT response event mismatch: {put_data.get('event')}")
                return False
            
            # GET templates to verify update
            get_response = requests.get(f"{BACKEND_URL}/email/templates", headers=self.get_headers())
            if get_response.status_code != 200:
                self.log_test("Test 6: Email Template Update", False, 
                             f"GET failed after update. Status: {get_response.status_code}")
                return False
            
            templates = get_response.json()
            login_template = next((t for t in templates if t.get("event") == "login"), None)
            
            if not login_template:
                self.log_test("Test 6: Email Template Update", False, 
                             "Login template not found in GET response")
                return False
            
            if login_template.get("subject") != new_subject:
                self.log_test("Test 6: Email Template Update", False, 
                             f"Subject not updated. Expected: {new_subject}, Got: {login_template.get('subject')}")
                return False
            
            if login_template.get("body") != new_body:
                self.log_test("Test 6: Email Template Update", False, 
                             f"Body not updated. Expected: {new_body}, Got: {login_template.get('body')}")
                return False
            
            self.log_test("Test 6: Email Template Update", True, 
                         "Login template updated and persisted correctly")
            return True
            
        except Exception as e:
            self.log_test("Test 6: Email Template Update", False, f"Exception: {str(e)}")
            return False
    
    def test_7_send_test_email(self) -> bool:
        """Test 7: POST /api/email/send-test forces email even with notifications off"""
        try:
            if not self.token:
                self.log_test("Test 7: Send Test Email", False, "No auth token")
                return False
            
            # Send test email (notifications are off from test 3, but this should force send)
            response = requests.post(f"{BACKEND_URL}/email/send-test",
                                    json={"event": "login"},
                                    headers=self.get_headers())
            
            if response.status_code != 200:
                self.log_test("Test 7: Send Test Email", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            
            # Verify response structure
            if "message" not in data or "event" not in data or "email" not in data:
                self.log_test("Test 7: Send Test Email", False, 
                             f"Missing required fields in response: {list(data.keys())}")
                return False
            
            # Verify no secrets exposed (SMTP credentials should not be in response)
            response_str = json.dumps(data).lower()
            if "smtp" in response_str or "password" in response_str or "prosz" in response_str:
                self.log_test("Test 7: Send Test Email", False, 
                             "Response may expose SMTP secrets")
                return False
            
            self.log_test("Test 7: Send Test Email", True, 
                         f"Test email queued successfully (forced despite notifications off). Check backend logs for email delivery.")
            return True
            
        except Exception as e:
            self.log_test("Test 7: Send Test Email", False, f"Exception: {str(e)}")
            return False
    
    def test_8_vip_subscribe_with_email(self) -> bool:
        """Test 8: VIP subscribe endpoint works and respects email settings"""
        try:
            if not self.token:
                self.log_test("Test 8: VIP Subscribe with Email", False, "No auth token")
                return False
            
            # First, turn notifications back on for VIP email
            requests.put(f"{BACKEND_URL}/settings",
                        json={"settings": {"notifications": True, "email_vip": True}},
                        headers=self.get_headers())
            
            # Note: VIP is now earned through 7+ day streak, not subscription
            # But the endpoint should still work for testing
            # We need to set streak to 7+ first
            
            # Check current VIP status
            me_response = requests.get(f"{BACKEND_URL}/auth/me", headers=self.get_headers())
            if me_response.status_code != 200:
                self.log_test("Test 8: VIP Subscribe with Email", False, 
                             f"GET /auth/me failed. Status: {me_response.status_code}")
                return False
            
            user_data = me_response.json()
            
            # Subscribe to VIP (mock payment)
            vip_response = requests.post(f"{BACKEND_URL}/vip/subscribe",
                                        json={"payment_method": "card"},
                                        headers=self.get_headers())
            
            if vip_response.status_code != 200:
                self.log_test("Test 8: VIP Subscribe with Email", False, 
                             f"VIP subscribe failed. Status: {vip_response.status_code}, Response: {vip_response.text}")
                return False
            
            vip_data = vip_response.json()
            
            # Verify response structure
            required_fields = ["success", "message", "vip_until", "perks"]
            if not all(f in vip_data for f in required_fields):
                self.log_test("Test 8: VIP Subscribe with Email", False, 
                             f"Missing required fields: {list(vip_data.keys())}")
                return False
            
            if not vip_data.get("success"):
                self.log_test("Test 8: VIP Subscribe with Email", False, 
                             f"VIP subscription not successful: {vip_data.get('message')}")
                return False
            
            # Verify perks structure
            perks = vip_data.get("perks", {})
            if perks.get("max_hearts") != 10:
                self.log_test("Test 8: VIP Subscribe with Email", False, 
                             f"VIP perks incorrect. Expected max_hearts=10, got {perks.get('max_hearts')}")
                return False
            
            self.log_test("Test 8: VIP Subscribe with Email", True, 
                         "VIP subscription successful. Check backend logs for VIP email (should be queued since notifications are on).")
            return True
            
        except Exception as e:
            self.log_test("Test 8: VIP Subscribe with Email", False, f"Exception: {str(e)}")
            return False
    
    def test_9_regression_languages(self) -> bool:
        """Test 9: Regression - /api/languages still works"""
        try:
            response = requests.get(f"{BACKEND_URL}/languages")
            
            if response.status_code != 200:
                self.log_test("Test 9: Regression - Languages", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            languages = response.json()
            
            if not isinstance(languages, list) or len(languages) < 20:
                self.log_test("Test 9: Regression - Languages", False, 
                             f"Expected at least 20 languages, got {len(languages) if isinstance(languages, list) else 'non-list'}")
                return False
            
            self.log_test("Test 9: Regression - Languages", True, 
                         f"Languages endpoint working. {len(languages)} languages available.")
            return True
            
        except Exception as e:
            self.log_test("Test 9: Regression - Languages", False, f"Exception: {str(e)}")
            return False
    
    def test_10_regression_games_stats(self) -> bool:
        """Test 10: Regression - /api/games/stats still works"""
        try:
            if not self.token:
                self.log_test("Test 10: Regression - Games Stats", False, "No auth token")
                return False
            
            response = requests.get(f"{BACKEND_URL}/games/stats", headers=self.get_headers())
            
            if response.status_code != 200:
                self.log_test("Test 10: Regression - Games Stats", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            stats = response.json()
            
            # Verify structure
            if not all(k in stats for k in ["total_games", "games_played", "by_type"]):
                self.log_test("Test 10: Regression - Games Stats", False, 
                             f"Missing required fields: {list(stats.keys())}")
                return False
            
            self.log_test("Test 10: Regression - Games Stats", True, 
                         f"Games stats endpoint working. Total games: {stats.get('total_games')}")
            return True
            
        except Exception as e:
            self.log_test("Test 10: Regression - Games Stats", False, f"Exception: {str(e)}")
            return False
    
    def test_11_regression_bug_hunter_python(self) -> bool:
        """Test 11: Regression - /api/games/bug-hunter/python still works"""
        try:
            response = requests.get(f"{BACKEND_URL}/games/bug-hunter/python")
            
            if response.status_code != 200:
                self.log_test("Test 11: Regression - Bug Hunter Python", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            
            # Verify structure
            if not all(k in data for k in ["language", "challenges", "total"]):
                self.log_test("Test 11: Regression - Bug Hunter Python", False, 
                             f"Missing required fields: {list(data.keys())}")
                return False
            
            if len(data.get("challenges", [])) != 5:
                self.log_test("Test 11: Regression - Bug Hunter Python", False, 
                             f"Expected 5 challenges, got {len(data.get('challenges', []))}")
                return False
            
            self.log_test("Test 11: Regression - Bug Hunter Python", True, 
                         "Bug Hunter Python endpoint working correctly.")
            return True
            
        except Exception as e:
            self.log_test("Test 11: Regression - Bug Hunter Python", False, f"Exception: {str(e)}")
            return False
    
    def test_12_regression_bug_hunter_niche(self) -> bool:
        """Test 12: Regression - /api/games/bug-hunter/skript (niche language) still works"""
        try:
            # Test skript as a niche language
            response = requests.get(f"{BACKEND_URL}/games/bug-hunter/skript")
            
            if response.status_code != 200:
                self.log_test("Test 12: Regression - Bug Hunter Skript", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            
            # Verify structure
            if not all(k in data for k in ["language", "challenges", "total"]):
                self.log_test("Test 12: Regression - Bug Hunter Skript", False, 
                             f"Missing required fields: {list(data.keys())}")
                return False
            
            challenges = data.get("challenges", [])
            if len(challenges) == 0:
                self.log_test("Test 12: Regression - Bug Hunter Skript", False, 
                             "No challenges returned for skript")
                return False
            
            # Verify challenges are skript-specific (not falling back to Python)
            first_challenge = challenges[0]
            challenge_id = first_challenge.get("id", "")
            
            # Skript challenges should have skript-specific IDs or content
            if "skript" not in challenge_id.lower() and "sk_" not in challenge_id.lower():
                # Check if code contains skript-specific keywords
                code = first_challenge.get("code", "").lower()
                if not any(keyword in code for keyword in ["broadcast", "send", "command", "trigger", "player"]):
                    self.log_test("Test 12: Regression - Bug Hunter Skript", False, 
                                 f"Challenges may be falling back to Python. ID: {challenge_id}, Code: {code[:50]}")
                    return False
            
            self.log_test("Test 12: Regression - Bug Hunter Skript", True, 
                         f"Bug Hunter Skript endpoint working with {len(challenges)} language-specific challenges.")
            return True
            
        except Exception as e:
            self.log_test("Test 12: Regression - Bug Hunter Skript", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all Phase 2 tests"""
        print("🚀 Starting Codero Phase 2 Backend API Tests")
        print("=" * 60)
        
        tests = [
            self.test_1_register_with_settings_defaults,
            self.test_2_login_and_check_health,
            self.test_3_settings_persistence,
            self.test_4_login_with_notifications_off,
            self.test_5_email_templates_list,
            self.test_6_email_template_update,
            self.test_7_send_test_email,
            self.test_8_vip_subscribe_with_email,
            self.test_9_regression_languages,
            self.test_10_regression_games_stats,
            self.test_11_regression_bug_hunter_python,
            self.test_12_regression_bug_hunter_niche,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("=" * 60)
        print(f"🎯 Test Results: {passed}/{total} tests passed ({int(passed/total*100)}%)")
        
        if passed == total:
            print("✅ All Phase 2 backend tests passed!")
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
    tester = Phase2Tester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
