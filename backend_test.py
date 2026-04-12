#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Codero Games
Tests all game endpoints: Bug Hunter, Code Puzzle, Speed Code, Game Completion, and Game Stats
"""

import requests
import json
import sys
from typing import Dict, Any

# Backend URL from environment
BACKEND_URL = "https://pixel-coder-3.preview.emergentagent.com/api"

class GamesTester:
    def __init__(self):
        self.token = None
        self.user_id = None
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
    
    def register_test_user(self) -> bool:
        """Register a new test user for games testing"""
        try:
            import time
            unique_id = int(time.time())
            response = requests.post(f"{BACKEND_URL}/auth/register", json={
                "username": f"gametester{unique_id}",
                "email": f"gametest{unique_id}@codero.com", 
                "password": "test123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.user_id = data.get("user", {}).get("id")
                self.log_test("User Registration", True, f"Registered user with token: {self.token[:20]}...")
                return True
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_bug_hunter_get(self) -> bool:
        """Test GET /api/games/bug-hunter/python"""
        try:
            response = requests.get(f"{BACKEND_URL}/games/bug-hunter/python")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["language", "challenges", "total"]
                if not all(field in data for field in required_fields):
                    self.log_test("Bug Hunter GET", False, f"Missing required fields. Got: {list(data.keys())}")
                    return False
                
                # Check challenges structure
                challenges = data.get("challenges", [])
                if len(challenges) != 5:
                    self.log_test("Bug Hunter GET", False, f"Expected 5 challenges, got {len(challenges)}")
                    return False
                
                # Validate challenge structure
                for i, challenge in enumerate(challenges):
                    required_challenge_fields = ["id", "code", "question", "options", "concept"]
                    if not all(field in challenge for field in required_challenge_fields):
                        self.log_test("Bug Hunter GET", False, f"Challenge {i} missing fields: {list(challenge.keys())}")
                        return False
                    
                    # Ensure correct answer is NOT exposed
                    if "correct" in challenge:
                        self.log_test("Bug Hunter GET", False, f"Challenge {i} exposes correct answer - security issue!")
                        return False
                
                self.log_test("Bug Hunter GET", True, f"Retrieved {len(challenges)} challenges correctly")
                return True
            else:
                self.log_test("Bug Hunter GET", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Bug Hunter GET", False, f"Exception: {str(e)}")
            return False
    
    def test_bug_hunter_check(self) -> bool:
        """Test POST /api/games/bug-hunter/python/check"""
        try:
            # First get a challenge
            response = requests.get(f"{BACKEND_URL}/games/bug-hunter/python")
            if response.status_code != 200:
                self.log_test("Bug Hunter CHECK", False, "Could not get challenges for testing")
                return False
            
            challenges = response.json().get("challenges", [])
            if not challenges:
                self.log_test("Bug Hunter CHECK", False, "No challenges available for testing")
                return False
            
            challenge = challenges[0]
            challenge_id = challenge["id"]
            
            # Test with correct answer (option 0 is typically correct for first challenge)
            check_response = requests.post(f"{BACKEND_URL}/games/bug-hunter/python/check", json={
                "challenge_id": challenge_id,
                "selected": 0
            })
            
            if check_response.status_code == 200:
                data = check_response.json()
                
                # Validate response structure
                required_fields = ["correct", "correct_answer", "fixed_code", "explanation"]
                if not all(field in data for field in required_fields):
                    self.log_test("Bug Hunter CHECK", False, f"Missing required fields. Got: {list(data.keys())}")
                    return False
                
                # Test with wrong answer
                wrong_response = requests.post(f"{BACKEND_URL}/games/bug-hunter/python/check", json={
                    "challenge_id": challenge_id,
                    "selected": 3  # Last option, likely wrong
                })
                
                if wrong_response.status_code == 200:
                    wrong_data = wrong_response.json()
                    if wrong_data.get("correct") == data.get("correct"):
                        self.log_test("Bug Hunter CHECK", False, "Same result for different answers - logic error")
                        return False
                
                self.log_test("Bug Hunter CHECK", True, f"Challenge check working correctly. Correct: {data.get('correct')}")
                return True
            else:
                self.log_test("Bug Hunter CHECK", False, f"Status: {check_response.status_code}, Response: {check_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Bug Hunter CHECK", False, f"Exception: {str(e)}")
            return False
    
    def test_code_puzzle_get(self) -> bool:
        """Test GET /api/games/code-puzzle/python"""
        try:
            response = requests.get(f"{BACKEND_URL}/games/code-puzzle/python")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["language", "puzzles", "total"]
                if not all(field in data for field in required_fields):
                    self.log_test("Code Puzzle GET", False, f"Missing required fields. Got: {list(data.keys())}")
                    return False
                
                # Check puzzles structure
                puzzles = data.get("puzzles", [])
                if len(puzzles) == 0:
                    self.log_test("Code Puzzle GET", False, "No puzzles returned")
                    return False
                
                # Validate puzzle structure
                for i, puzzle in enumerate(puzzles):
                    required_puzzle_fields = ["id", "title", "description", "lines", "original_indices", "concept"]
                    if not all(field in puzzle for field in required_puzzle_fields):
                        self.log_test("Code Puzzle GET", False, f"Puzzle {i} missing fields: {list(puzzle.keys())}")
                        return False
                    
                    # Check that lines are shuffled (original_indices should not be in order)
                    original_indices = puzzle.get("original_indices", [])
                    if original_indices == list(range(len(original_indices))):
                        self.log_test("Code Puzzle GET", False, f"Puzzle {i} lines not shuffled")
                        return False
                
                self.log_test("Code Puzzle GET", True, f"Retrieved {len(puzzles)} puzzles with shuffled lines")
                return True
            else:
                self.log_test("Code Puzzle GET", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Code Puzzle GET", False, f"Exception: {str(e)}")
            return False
    
    def test_code_puzzle_check(self) -> bool:
        """Test POST /api/games/code-puzzle/python/check"""
        try:
            # First get a puzzle
            response = requests.get(f"{BACKEND_URL}/games/code-puzzle/python")
            if response.status_code != 200:
                self.log_test("Code Puzzle CHECK", False, "Could not get puzzles for testing")
                return False
            
            puzzles = response.json().get("puzzles", [])
            if not puzzles:
                self.log_test("Code Puzzle CHECK", False, "No puzzles available for testing")
                return False
            
            puzzle = puzzles[0]
            puzzle_id = puzzle["id"]
            
            # Test with correct order based on known puzzle data
            if puzzle_id == "py_puz_1":
                correct_order = [0, 1, 2]
            elif puzzle_id == "py_puz_2":
                correct_order = [1, 0, 3, 2]
            elif puzzle_id == "py_puz_3":
                correct_order = [1, 0, 4, 5, 3, 2]
            elif puzzle_id == "py_puz_4":
                correct_order = [1, 5, 4, 0, 6, 2, 3]
            elif puzzle_id == "py_puz_5":
                correct_order = [1, 2, 4, 3, 0]
            else:
                # For unknown puzzles, use sequential order as fallback
                correct_order = list(range(len(puzzle.get("lines", []))))
            
            check_response = requests.post(f"{BACKEND_URL}/games/code-puzzle/python/check", json={
                "puzzle_id": puzzle_id,
                "order": correct_order
            })
            
            if check_response.status_code == 200:
                data = check_response.json()
                
                # Validate response structure
                required_fields = ["correct", "correct_order", "correct_lines", "explanation"]
                if not all(field in data for field in required_fields):
                    self.log_test("Code Puzzle CHECK", False, f"Missing required fields. Got: {list(data.keys())}")
                    return False
                
                # Test with wrong order
                if puzzle_id == "py_puz_1" and len(correct_order) == 3:
                    # For py_puz_1, use [2, 1, 0] as wrong order
                    wrong_order = [2, 1, 0]
                else:
                    # For other puzzles, reverse the order
                    wrong_order = correct_order[::-1]
                wrong_response = requests.post(f"{BACKEND_URL}/games/code-puzzle/python/check", json={
                    "puzzle_id": puzzle_id,
                    "order": wrong_order
                })
                
                if wrong_response.status_code == 200:
                    wrong_data = wrong_response.json()
                    if wrong_data.get("correct") == data.get("correct") and len(correct_order) > 1:
                        self.log_test("Code Puzzle CHECK", False, "Same result for different orders - logic error")
                        return False
                
                self.log_test("Code Puzzle CHECK", True, f"Puzzle check working correctly. Correct: {data.get('correct')}")
                return True
            else:
                self.log_test("Code Puzzle CHECK", False, f"Status: {check_response.status_code}, Response: {check_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Code Puzzle CHECK", False, f"Exception: {str(e)}")
            return False
    
    def test_speed_code_get(self) -> bool:
        """Test GET /api/games/speed-code/python"""
        try:
            response = requests.get(f"{BACKEND_URL}/games/speed-code/python")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["language", "challenges", "total"]
                if not all(field in data for field in required_fields):
                    self.log_test("Speed Code GET", False, f"Missing required fields. Got: {list(data.keys())}")
                    return False
                
                # Check challenges structure
                challenges = data.get("challenges", [])
                if len(challenges) == 0:
                    self.log_test("Speed Code GET", False, "No challenges returned")
                    return False
                
                # Validate challenge structure
                for i, challenge in enumerate(challenges):
                    required_challenge_fields = ["id", "prompt", "time_limit", "points", "concept"]
                    if not all(field in challenge for field in required_challenge_fields):
                        self.log_test("Speed Code GET", False, f"Challenge {i} missing fields: {list(challenge.keys())}")
                        return False
                    
                    # Ensure expected answer is NOT exposed
                    if "expected" in challenge:
                        self.log_test("Speed Code GET", False, f"Challenge {i} exposes expected answer - security issue!")
                        return False
                
                self.log_test("Speed Code GET", True, f"Retrieved {len(challenges)} speed challenges correctly")
                return True
            else:
                self.log_test("Speed Code GET", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Speed Code GET", False, f"Exception: {str(e)}")
            return False
    
    def test_speed_code_check(self) -> bool:
        """Test POST /api/games/speed-code/python/check"""
        try:
            # Test with known challenge (py_speed_1: print('Hello World'))
            check_response = requests.post(f"{BACKEND_URL}/games/speed-code/python/check", json={
                "challenge_id": "py_speed_1",
                "code": "print('Hello World')"
            })
            
            if check_response.status_code == 200:
                data = check_response.json()
                
                # Validate response structure
                required_fields = ["correct", "expected", "points"]
                if not all(field in data for field in required_fields):
                    self.log_test("Speed Code CHECK", False, f"Missing required fields. Got: {list(data.keys())}")
                    return False
                
                # Should be correct
                if not data.get("correct"):
                    self.log_test("Speed Code CHECK", False, f"Expected correct answer but got: {data}")
                    return False
                
                # Test with wrong answer
                wrong_response = requests.post(f"{BACKEND_URL}/games/speed-code/python/check", json={
                    "challenge_id": "py_speed_1",
                    "code": "console.log('Hello World')"  # Wrong language
                })
                
                if wrong_response.status_code == 200:
                    wrong_data = wrong_response.json()
                    if wrong_data.get("correct"):
                        self.log_test("Speed Code CHECK", False, "Wrong answer marked as correct")
                        return False
                    if wrong_data.get("points", 0) > 0:
                        self.log_test("Speed Code CHECK", False, "Points awarded for wrong answer")
                        return False
                
                self.log_test("Speed Code CHECK", True, f"Speed code check working correctly. Points: {data.get('points')}")
                return True
            else:
                self.log_test("Speed Code CHECK", False, f"Status: {check_response.status_code}, Response: {check_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Speed Code CHECK", False, f"Exception: {str(e)}")
            return False
    
    def test_game_complete(self) -> bool:
        """Test POST /api/games/complete (requires auth)"""
        try:
            if not self.token:
                self.log_test("Game Complete", False, "No auth token available")
                return False
            
            response = requests.post(f"{BACKEND_URL}/games/complete", 
                json={
                    "game_type": "bug_hunter",
                    "score": 4,
                    "total": 5,
                    "language": "python"
                },
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["xp_earned", "gems_earned", "score_pct", "games_played"]
                if not all(field in data for field in required_fields):
                    self.log_test("Game Complete", False, f"Missing required fields. Got: {list(data.keys())}")
                    return False
                
                # Validate calculations
                expected_score_pct = int((4 / 5) * 100)  # 80%
                if data.get("score_pct") != expected_score_pct:
                    self.log_test("Game Complete", False, f"Score percentage wrong. Expected {expected_score_pct}, got {data.get('score_pct')}")
                    return False
                
                # Should earn gems for 80% score (>= 70%)
                if data.get("gems_earned") != 2:
                    self.log_test("Game Complete", False, f"Expected 2 gems for 80% score, got {data.get('gems_earned')}")
                    return False
                
                # Should earn XP (base 24 XP for 80% * 1.0 multiplier = 24)
                expected_xp = int(80 * 0.3)  # 24 XP
                if data.get("xp_earned") != expected_xp:
                    self.log_test("Game Complete", False, f"Expected {expected_xp} XP, got {data.get('xp_earned')}")
                    return False
                
                self.log_test("Game Complete", True, f"Game completion working. XP: {data.get('xp_earned')}, Gems: {data.get('gems_earned')}")
                return True
            else:
                self.log_test("Game Complete", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Game Complete", False, f"Exception: {str(e)}")
            return False
    
    def test_game_stats(self) -> bool:
        """Test GET /api/games/stats (requires auth)"""
        try:
            if not self.token:
                self.log_test("Game Stats", False, "No auth token available")
                return False
            
            response = requests.get(f"{BACKEND_URL}/games/stats", headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["total_games", "games_played", "by_type"]
                if not all(field in data for field in required_fields):
                    self.log_test("Game Stats", False, f"Missing required fields. Got: {list(data.keys())}")
                    return False
                
                # After completing one game, should have stats
                if data.get("games_played") < 1:
                    self.log_test("Game Stats", False, f"Expected at least 1 game played, got {data.get('games_played')}")
                    return False
                
                # Should have bug_hunter in by_type
                by_type = data.get("by_type", {})
                if "bug_hunter" not in by_type:
                    self.log_test("Game Stats", False, f"Expected bug_hunter in by_type, got: {list(by_type.keys())}")
                    return False
                
                bug_hunter_stats = by_type["bug_hunter"]
                required_stats = ["played", "best_score", "total_xp"]
                if not all(field in bug_hunter_stats for field in required_stats):
                    self.log_test("Game Stats", False, f"Bug hunter stats missing fields: {list(bug_hunter_stats.keys())}")
                    return False
                
                self.log_test("Game Stats", True, f"Game stats working. Total games: {data.get('total_games')}, Games played: {data.get('games_played')}")
                return True
            else:
                self.log_test("Game Stats", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Game Stats", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all game endpoint tests"""
        print("🎮 Starting Codero Games Backend API Tests")
        print("=" * 50)
        
        # Register user first
        if not self.register_test_user():
            print("❌ Cannot proceed without user registration")
            return False
        
        # Run all game tests
        tests = [
            self.test_bug_hunter_get,
            self.test_bug_hunter_check,
            self.test_code_puzzle_get,
            self.test_code_puzzle_check,
            self.test_speed_code_get,
            self.test_speed_code_check,
            self.test_game_complete,
            self.test_game_stats,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("=" * 50)
        print(f"🎯 Test Results: {passed}/{total} tests passed ({int(passed/total*100)}%)")
        
        if passed == total:
            print("✅ All games backend endpoints working correctly!")
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
    tester = GamesTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)