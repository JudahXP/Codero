#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Codero App
Tests VIP subscription system, practice mode, login fix, and lesson completion flows
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://pixel-coder-3.preview.emergentagent.com/api"
import time
timestamp = int(time.time())
TEST_USER = {
    "username": f"viptest{timestamp}",
    "email": f"viptest{timestamp}@codero.com", 
    "password": "test123"
}

class CoderoAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if self.token:
            default_headers["Authorization"] = f"Bearer {self.token}"
            
        if headers:
            default_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def test_auth_register(self):
        """Test 1: Auth Register"""
        print("🔐 Testing Auth Register...")
        
        response = self.make_request("POST", "/auth/register", TEST_USER)
        
        if not response:
            self.log_test("Auth Register", False, "Request failed")
            return False
            
        if response.status_code in [200, 201]:
            data = response.json()
            if "token" in data and "user" in data:
                self.token = data["token"]
                self.user_id = data["user"]["id"]
                self.log_test("Auth Register", True, f"User registered with ID: {self.user_id}")
                return True
            else:
                self.log_test("Auth Register", False, f"Missing token/user in response: {data}")
                return False
        else:
            self.log_test("Auth Register", False, f"Status {response.status_code}: {response.text}")
            return False
    
    def test_auth_login(self):
        """Test 2: Auth Login (ObjectId bug fix)"""
        print("🔑 Testing Auth Login...")
        
        login_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        
        if not response:
            self.log_test("Auth Login", False, "Request failed")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "token" in data and "user" in data:
                # Update token in case it changed
                self.token = data["token"]
                self.log_test("Auth Login", True, "Login successful, ObjectId bug fixed")
                return True
            else:
                self.log_test("Auth Login", False, f"Missing token/user in response: {data}")
                return False
        else:
            self.log_test("Auth Login", False, f"Status {response.status_code}: {response.text}")
            return False
    
    def test_vip_info(self):
        """Test 3: VIP Info"""
        print("💎 Testing VIP Info...")
        
        response = self.make_request("GET", "/vip/info")
        
        if not response:
            self.log_test("VIP Info", False, "Request failed")
            return False
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ["price", "perks"]
            if all(field in data for field in required_fields):
                self.log_test("VIP Info", True, f"Price: ${data['price']}, Perks: {len(data['perks'])} items")
                return True
            else:
                self.log_test("VIP Info", False, f"Missing required fields: {data}")
                return False
        else:
            self.log_test("VIP Info", False, f"Status {response.status_code}: {response.text}")
            return False
    
    def test_vip_status_before(self):
        """Test 4: VIP Status Before Subscribe"""
        print("📊 Testing VIP Status (Before Subscribe)...")
        
        response = self.make_request("GET", "/vip/status")
        
        if not response:
            self.log_test("VIP Status Before", False, "Request failed")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "is_vip" in data and data["is_vip"] == False:
                self.log_test("VIP Status Before", True, "User is not VIP (expected)")
                return True
            else:
                self.log_test("VIP Status Before", False, f"Unexpected VIP status: {data}")
                return False
        else:
            self.log_test("VIP Status Before", False, f"Status {response.status_code}: {response.text}")
            return False
    
    def test_vip_subscribe(self):
        """Test 5: VIP Subscribe"""
        print("💳 Testing VIP Subscribe...")
        
        subscribe_data = {"payment_method": "card"}
        response = self.make_request("POST", "/vip/subscribe", subscribe_data)
        
        if not response:
            self.log_test("VIP Subscribe", False, "Request failed")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "success" in data and data["success"] == True:
                self.log_test("VIP Subscribe", True, f"VIP activated until: {data.get('vip_until', 'N/A')}")
                return True
            else:
                self.log_test("VIP Subscribe", False, f"Subscription failed: {data}")
                return False
        else:
            self.log_test("VIP Subscribe", False, f"Status {response.status_code}: {response.text}")
            return False
    
    def test_vip_status_after(self):
        """Test 6: VIP Status After Subscribe"""
        print("✨ Testing VIP Status (After Subscribe)...")
        
        response = self.make_request("GET", "/vip/status")
        
        if not response:
            self.log_test("VIP Status After", False, "Request failed")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "is_vip" in data and data["is_vip"] == True:
                perks = data.get("perks", {})
                expected_perks = ["xp_multiplier", "max_hearts", "hints_per_lesson"]
                if all(perk in perks for perk in expected_perks):
                    self.log_test("VIP Status After", True, f"VIP active with perks: {list(perks.keys())}")
                    return True
                else:
                    self.log_test("VIP Status After", False, f"Missing expected perks: {perks}")
                    return False
            else:
                self.log_test("VIP Status After", False, f"User should be VIP: {data}")
                return False
        else:
            self.log_test("VIP Status After", False, f"Status {response.status_code}: {response.text}")
            return False
    
    def test_practice_content(self):
        """Test 7: Practice Content"""
        print("📚 Testing Practice Content...")
        
        response = self.make_request("GET", "/languages/python/lessons/python_1_1/practice")
        
        if not response:
            self.log_test("Practice Content", False, "Request failed")
            return False
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ["lesson_id", "practice_content"]
            if all(field in data for field in required_fields):
                practice_content = data["practice_content"]
                if "explanation" in practice_content and "syntax" in practice_content:
                    self.log_test("Practice Content", True, f"Practice content available for {data['lesson_id']}")
                    return True
                else:
                    self.log_test("Practice Content", False, f"Incomplete practice content: {practice_content}")
                    return False
            else:
                self.log_test("Practice Content", False, f"Missing required fields: {data}")
                return False
        else:
            self.log_test("Practice Content", False, f"Status {response.status_code}: {response.text}")
            return False
    
    def test_lesson_completion_normal(self):
        """Test 8: Lesson Completion (Normal Mode)"""
        print("🎯 Testing Lesson Completion (Normal Mode)...")
        
        completion_data = {
            "lesson_id": "python_1_1",
            "language": "python",
            "answers": [
                {"selected": 0},
                {"selected": 0},
                {"code": "print('Hello, World!')"},
                {"answer": "print"},
                {"selected": 0},
                {"code": "print('Name')"},
                {"selected": 0},
                {"answer": "comment"},
                {"code": "print('Line 1')\nprint('Line 2')"},
                {"selected": 0}
            ]
        }
        
        response = self.make_request("POST", "/progress/complete", completion_data)
        
        if not response:
            self.log_test("Lesson Completion Normal", False, "Request failed")
            return False
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ["score", "xp_earned", "correct"]
            if all(field in data for field in required_fields):
                self.log_test("Lesson Completion Normal", True, 
                            f"Score: {data['score']}%, XP: {data['xp_earned']}, Correct: {data['correct']}")
                return True
            else:
                self.log_test("Lesson Completion Normal", False, f"Missing required fields: {data}")
                return False
        else:
            self.log_test("Lesson Completion Normal", False, f"Status {response.status_code}: {response.text}")
            return False
    
    def test_lesson_completion_practice(self):
        """Test 9: Practice Mode Completion"""
        print("🏃 Testing Practice Mode Completion...")
        
        practice_data = {
            "lesson_id": "python_1_2",
            "language": "python",
            "answers": [
                {"selected": 0},
                {"code": "age = 25"},
                {"selected": 0},
                {"answer": "="},
                {"selected": 0},
                {"code": "x = 5\ny = 10\nprint(x + y)"},
                {"selected": 0},
                {"answer": "type"},
                {"code": "name = 'Alice'\nprint(name)"},
                {"selected": 0}
            ],
            "practice_mode": True
        }
        
        response = self.make_request("POST", "/progress/complete", practice_data)
        
        if not response:
            self.log_test("Practice Mode Completion", False, "Request failed")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if (data.get("practice_mode") == True and 
                data.get("xp_earned") == 0 and 
                data.get("hearts_lost") == 0):
                self.log_test("Practice Mode Completion", True, 
                            f"Practice mode working: XP={data['xp_earned']}, Hearts lost={data['hearts_lost']}")
                return True
            else:
                self.log_test("Practice Mode Completion", False, f"Practice mode not working correctly: {data}")
                return False
        else:
            self.log_test("Practice Mode Completion", False, f"Status {response.status_code}: {response.text}")
            return False
    
    def test_auth_me_vip(self):
        """Test 10: Auth Me (VIP check)"""
        print("👤 Testing Auth Me (VIP check)...")
        
        response = self.make_request("GET", "/auth/me")
        
        if not response:
            self.log_test("Auth Me VIP", False, "Request failed")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "is_vip" in data and data["is_vip"] == True:
                vip_perks = data.get("vip_perks", {})
                if vip_perks:
                    self.log_test("Auth Me VIP", True, f"User data includes VIP status and perks: {list(vip_perks.keys())}")
                    return True
                else:
                    self.log_test("Auth Me VIP", False, "VIP perks missing from user data")
                    return False
            else:
                self.log_test("Auth Me VIP", False, f"User should be VIP: {data}")
                return False
        else:
            self.log_test("Auth Me VIP", False, f"Status {response.status_code}: {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Codero Backend API Tests")
        print("=" * 50)
        
        tests = [
            self.test_auth_register,
            self.test_auth_login,
            self.test_vip_info,
            self.test_vip_status_before,
            self.test_vip_subscribe,
            self.test_vip_status_after,
            self.test_practice_content,
            self.test_lesson_completion_normal,
            self.test_lesson_completion_practice,
            self.test_auth_me_vip
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! Backend API is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
            
        return passed == total

def main():
    """Main test runner"""
    tester = CoderoAPITester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()