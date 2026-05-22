#!/usr/bin/env python3
"""
Backend API Testing for Codero Language Coverage
Tests that all game APIs return language-specific content, not Python fallback
"""

import requests
import sys
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://codero-stack.preview.emergentagent.com/api"

# Test languages
TEST_LANGUAGES = ["skript", "haskell", "kotlin", "sql"]

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_success(msg: str):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg: str):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg: str):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_header(msg: str):
    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"{BOLD}{msg}{RESET}")
    print(f"{BOLD}{'='*80}{RESET}\n")

def test_bug_hunter_language(language: str) -> Dict[str, Any]:
    """Test Bug Hunter endpoint for a specific language"""
    print(f"\n{BOLD}Testing Bug Hunter for {language.upper()}{RESET}")
    
    url = f"{BACKEND_URL}/games/bug-hunter/{language}"
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print_error(f"Bug Hunter {language}: HTTP {response.status_code}")
            return {"passed": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        
        # Check structure
        if "challenges" not in data:
            print_error(f"Bug Hunter {language}: Missing 'challenges' key")
            return {"passed": False, "error": "Missing challenges key"}
        
        challenges = data["challenges"]
        
        if len(challenges) != 5:
            print_error(f"Bug Hunter {language}: Expected 5 challenges, got {len(challenges)}")
            return {"passed": False, "error": f"Wrong count: {len(challenges)}"}
        
        # Check for Python fallback by examining IDs
        python_fallback = False
        language_specific = True
        challenge_ids = []
        
        for challenge in challenges:
            challenge_id = challenge.get("id", "")
            challenge_ids.append(challenge_id)
            
            # Check if ID starts with py_ (Python fallback)
            if challenge_id.startswith("py_"):
                python_fallback = True
                language_specific = False
            
            # Check if ID contains the language prefix
            # For generic challenges, ID should be like "{language}_bug_1"
            expected_prefix = f"{language}_"
            if not challenge_id.startswith(expected_prefix):
                # Could be custom content with different naming
                # Check if it's not Python
                if not challenge_id.startswith("py_"):
                    # Might be custom naming like "hs_bug_1" for haskell
                    pass
        
        # Print challenge IDs
        print(f"  Challenge IDs: {', '.join(challenge_ids)}")
        
        # Check if all IDs are Python IDs (fallback issue)
        all_python = all(cid.startswith("py_") for cid in challenge_ids)
        
        if all_python:
            print_error(f"Bug Hunter {language}: ALL challenges are Python fallback (py_*)")
            return {
                "passed": False, 
                "error": "Python fallback detected",
                "challenge_ids": challenge_ids,
                "data": data
            }
        
        # Check for language-specific content in question or code
        has_language_reference = False
        for challenge in challenges:
            question = challenge.get("question", "").lower()
            code = challenge.get("code", "").lower()
            
            # Check if language name appears in question or code
            if language.lower() in question or language.lower() in code:
                has_language_reference = True
                break
        
        print_success(f"Bug Hunter {language}: Returns 5 challenges with IDs: {', '.join(challenge_ids)}")
        
        return {
            "passed": True,
            "challenge_ids": challenge_ids,
            "has_language_reference": has_language_reference,
            "data": data
        }
        
    except Exception as e:
        print_error(f"Bug Hunter {language}: Exception - {str(e)}")
        return {"passed": False, "error": str(e)}

def test_code_puzzle_language(language: str) -> Dict[str, Any]:
    """Test Code Puzzle endpoint for a specific language"""
    print(f"\n{BOLD}Testing Code Puzzle for {language.upper()}{RESET}")
    
    url = f"{BACKEND_URL}/games/code-puzzle/{language}"
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print_error(f"Code Puzzle {language}: HTTP {response.status_code}")
            return {"passed": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        
        # Check structure
        if "puzzles" not in data:
            print_error(f"Code Puzzle {language}: Missing 'puzzles' key")
            return {"passed": False, "error": "Missing puzzles key"}
        
        puzzles = data["puzzles"]
        
        if len(puzzles) == 0:
            print_error(f"Code Puzzle {language}: No puzzles returned")
            return {"passed": False, "error": "No puzzles"}
        
        # Check for Python fallback by examining IDs
        puzzle_ids = []
        
        for puzzle in puzzles:
            puzzle_id = puzzle.get("id", "")
            puzzle_ids.append(puzzle_id)
        
        # Print puzzle IDs
        print(f"  Puzzle IDs: {', '.join(puzzle_ids)}")
        
        # Check if all IDs are Python IDs (fallback issue)
        all_python = all(pid.startswith("py_") for pid in puzzle_ids)
        
        if all_python:
            print_error(f"Code Puzzle {language}: ALL puzzles are Python fallback (py_*)")
            return {
                "passed": False,
                "error": "Python fallback detected",
                "puzzle_ids": puzzle_ids,
                "data": data
            }
        
        print_success(f"Code Puzzle {language}: Returns {len(puzzles)} puzzles with IDs: {', '.join(puzzle_ids)}")
        
        return {
            "passed": True,
            "puzzle_ids": puzzle_ids,
            "data": data
        }
        
    except Exception as e:
        print_error(f"Code Puzzle {language}: Exception - {str(e)}")
        return {"passed": False, "error": str(e)}

def test_speed_code_language(language: str) -> Dict[str, Any]:
    """Test Speed Code endpoint for a specific language"""
    print(f"\n{BOLD}Testing Speed Code for {language.upper()}{RESET}")
    
    url = f"{BACKEND_URL}/games/speed-code/{language}"
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print_error(f"Speed Code {language}: HTTP {response.status_code}")
            return {"passed": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        
        # Check structure
        if "challenges" not in data:
            print_error(f"Speed Code {language}: Missing 'challenges' key")
            return {"passed": False, "error": "Missing challenges key"}
        
        challenges = data["challenges"]
        
        if len(challenges) != 5:
            print_error(f"Speed Code {language}: Expected 5 challenges, got {len(challenges)}")
            return {"passed": False, "error": f"Wrong count: {len(challenges)}"}
        
        # Check for Python fallback by examining IDs
        challenge_ids = []
        
        for challenge in challenges:
            challenge_id = challenge.get("id", "")
            challenge_ids.append(challenge_id)
        
        # Print challenge IDs
        print(f"  Challenge IDs: {', '.join(challenge_ids)}")
        
        # Check if all IDs are Python IDs (fallback issue)
        all_python = all(cid.startswith("py_") for cid in challenge_ids)
        
        if all_python:
            print_error(f"Speed Code {language}: ALL challenges are Python fallback (py_*)")
            return {
                "passed": False,
                "error": "Python fallback detected",
                "challenge_ids": challenge_ids,
                "data": data
            }
        
        print_success(f"Speed Code {language}: Returns 5 challenges with IDs: {', '.join(challenge_ids)}")
        
        return {
            "passed": True,
            "challenge_ids": challenge_ids,
            "data": data
        }
        
    except Exception as e:
        print_error(f"Speed Code {language}: Exception - {str(e)}")
        return {"passed": False, "error": str(e)}

def test_challenge_validation(language: str, challenge_id: str, game_type: str) -> Dict[str, Any]:
    """Test that a challenge can be validated by ID without 404"""
    print(f"\n{BOLD}Testing Challenge Validation: {game_type} - {challenge_id}{RESET}")
    
    if game_type == "bug-hunter":
        url = f"{BACKEND_URL}/games/bug-hunter/{language}/check"
        payload = {"challenge_id": challenge_id, "selected": 0}
    elif game_type == "code-puzzle":
        url = f"{BACKEND_URL}/games/code-puzzle/{language}/check"
        payload = {"puzzle_id": challenge_id, "order": [0, 1, 2]}
    elif game_type == "speed-code":
        url = f"{BACKEND_URL}/games/speed-code/{language}/check"
        payload = {"challenge_id": challenge_id, "code": "test"}
    else:
        print_error(f"Unknown game type: {game_type}")
        return {"passed": False, "error": "Unknown game type"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 404:
            print_error(f"Challenge validation: 404 Not Found for {challenge_id}")
            return {"passed": False, "error": "404 Not Found"}
        
        if response.status_code != 200:
            print_error(f"Challenge validation: HTTP {response.status_code}")
            return {"passed": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        
        # Check that response has expected keys
        if game_type == "bug-hunter" and "correct" not in data:
            print_error(f"Challenge validation: Missing 'correct' key in response")
            return {"passed": False, "error": "Missing correct key"}
        
        print_success(f"Challenge validation: {challenge_id} validated successfully")
        
        return {"passed": True, "data": data}
        
    except Exception as e:
        print_error(f"Challenge validation: Exception - {str(e)}")
        return {"passed": False, "error": str(e)}

def main():
    print_header("CODERO BACKEND API - LANGUAGE COVERAGE TEST")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Testing languages: {', '.join(TEST_LANGUAGES)}")
    
    results = {
        "bug_hunter": {},
        "code_puzzle": {},
        "speed_code": {},
        "validation": {}
    }
    
    # Test each language across all three game types
    for language in TEST_LANGUAGES:
        print_header(f"TESTING LANGUAGE: {language.upper()}")
        
        # Test Bug Hunter
        results["bug_hunter"][language] = test_bug_hunter_language(language)
        
        # Test Code Puzzle
        results["code_puzzle"][language] = test_code_puzzle_language(language)
        
        # Test Speed Code
        results["speed_code"][language] = test_speed_code_language(language)
        
        # Test validation for one challenge from each game type
        if results["bug_hunter"][language]["passed"]:
            challenge_id = results["bug_hunter"][language]["challenge_ids"][0]
            results["validation"][f"{language}_bug_hunter"] = test_challenge_validation(
                language, challenge_id, "bug-hunter"
            )
        
        if results["code_puzzle"][language]["passed"]:
            puzzle_id = results["code_puzzle"][language]["puzzle_ids"][0]
            results["validation"][f"{language}_code_puzzle"] = test_challenge_validation(
                language, puzzle_id, "code-puzzle"
            )
        
        if results["speed_code"][language]["passed"]:
            challenge_id = results["speed_code"][language]["challenge_ids"][0]
            results["validation"][f"{language}_speed_code"] = test_challenge_validation(
                language, challenge_id, "speed-code"
            )
    
    # Summary
    print_header("TEST SUMMARY")
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for game_type in ["bug_hunter", "code_puzzle", "speed_code"]:
        print(f"\n{BOLD}{game_type.replace('_', ' ').title()}:{RESET}")
        for language in TEST_LANGUAGES:
            total_tests += 1
            result = results[game_type][language]
            if result["passed"]:
                passed_tests += 1
                print_success(f"{language}: PASSED")
            else:
                print_error(f"{language}: FAILED - {result.get('error', 'Unknown error')}")
                failed_tests.append(f"{game_type}/{language}")
    
    print(f"\n{BOLD}Validation Tests:{RESET}")
    for key, result in results["validation"].items():
        total_tests += 1
        if result["passed"]:
            passed_tests += 1
            print_success(f"{key}: PASSED")
        else:
            print_error(f"{key}: FAILED - {result.get('error', 'Unknown error')}")
            failed_tests.append(f"validation/{key}")
    
    print_header("FINAL RESULTS")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {GREEN}{passed_tests}{RESET}")
    print(f"Failed: {RED}{total_tests - passed_tests}{RESET}")
    
    if failed_tests:
        print(f"\n{RED}Failed Tests:{RESET}")
        for test in failed_tests:
            print(f"  - {test}")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"\n{BOLD}Success Rate: {success_rate:.1f}%{RESET}")
    
    if success_rate == 100:
        print_success("ALL TESTS PASSED! 🎉")
        return 0
    else:
        print_error("SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
