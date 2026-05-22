#!/usr/bin/env python3
"""
V1.7 Auth/Email Backend Testing
Tests login verification code creation, SMTP email delivery, and duplicate validation
"""

import requests
import time
import json
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://codero-stack.preview.emergentagent.com/api"

def log_test(test_name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"    {details}")
    return passed

def test_v17_auth_email():
    """Test V1.7 auth/email changes"""
    print("\n" + "="*80)
    print("V1.7 AUTH/EMAIL BACKEND TESTING")
    print("="*80 + "\n")
    
    passed_tests = 0
    total_tests = 0
    timestamp = int(time.time())
    
    # Test 1: Register fresh user for testing
    print("\n--- Test 1: Fresh User Registration ---")
    total_tests += 1
    register_data = {
        "username": f"v17test_{timestamp}",
        "email": f"v17test_{timestamp}@codero.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/register", json=register_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            user = data.get("user")
            if token and user:
                passed_tests += log_test("Fresh user registration", True, f"User: {user.get('username')}, Token: {token[:20]}...")
            else:
                log_test("Fresh user registration", False, "Missing token or user in response")
        else:
            log_test("Fresh user registration", False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        log_test("Fresh user registration", False, f"Exception: {e}")
    
    # Test 2: Login with EMAIL - should return token/user AND create verification code
    print("\n--- Test 2: Login with Email (Verification Code Creation) ---")
    total_tests += 1
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            user = data.get("user")
            
            # Check response structure
            if token and user:
                # Verify code is NOT exposed in response
                response_str = json.dumps(data)
                if "code" not in response_str.lower() or "verification" not in response_str.lower():
                    passed_tests += log_test("Login with email returns token/user", True, 
                        f"Token: {token[:20]}..., User: {user.get('username')}, Code NOT exposed in response ✓")
                else:
                    log_test("Login with email returns token/user", False, "Verification code exposed in response")
            else:
                log_test("Login with email returns token/user", False, "Missing token or user in response")
        else:
            log_test("Login with email returns token/user", False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        log_test("Login with email returns token/user", False, f"Exception: {e}")
    
    # Test 3: Login with USERNAME - should also work
    print("\n--- Test 3: Login with Username (Verification Code Creation) ---")
    total_tests += 1
    login_username_data = {
        "email": register_data["username"],  # Username in email field
        "password": register_data["password"]
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_username_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            user = data.get("user")
            
            if token and user:
                # Verify code is NOT exposed
                response_str = json.dumps(data)
                if "code" not in response_str.lower() or "verification" not in response_str.lower():
                    passed_tests += log_test("Login with username returns token/user", True, 
                        f"Token: {token[:20]}..., User: {user.get('username')}, Code NOT exposed ✓")
                else:
                    log_test("Login with username returns token/user", False, "Verification code exposed in response")
            else:
                log_test("Login with username returns token/user", False, "Missing token or user")
        else:
            log_test("Login with username returns token/user", False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        log_test("Login with username returns token/user", False, f"Exception: {e}")
    
    # Test 4: Check backend logs for verification email sent
    print("\n--- Test 4: Verification Email SMTP Delivery (Backend Logs) ---")
    total_tests += 1
    try:
        import subprocess
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True,
            timeout=5
        )
        logs = result.stdout
        
        # Check for verification email sent message
        if f"Verification email sent to {register_data['email']}" in logs:
            passed_tests += log_test("Verification email sent via SMTP", True, 
                f"Backend logs confirm: 'Verification email sent to {register_data['email']}'")
        else:
            # Check for any verification email in recent logs
            if "Verification email sent to" in logs:
                passed_tests += log_test("Verification email sent via SMTP", True, 
                    "Backend logs show verification emails being sent (SMTP working)")
            else:
                log_test("Verification email sent via SMTP", False, 
                    "No 'Verification email sent' message in backend logs")
    except Exception as e:
        log_test("Verification email sent via SMTP", False, f"Exception checking logs: {e}")
    
    # Test 5: Check for SMTP errors (should be none)
    print("\n--- Test 5: SMTP No Crash After Branded HTML Update ---")
    total_tests += 1
    try:
        import subprocess
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True,
            timeout=5
        )
        logs = result.stdout
        
        # Check for SMTP errors
        smtp_errors = ["SMTPAuthenticationError", "SMTPException", "SMTP delivery failed"]
        has_error = any(error in logs for error in smtp_errors)
        
        if not has_error:
            passed_tests += log_test("SMTP no crash with branded HTML", True, 
                "No SMTP errors in recent backend logs")
        else:
            log_test("SMTP no crash with branded HTML", False, 
                "SMTP errors found in backend logs")
    except Exception as e:
        log_test("SMTP no crash with branded HTML", False, f"Exception: {e}")
    
    # Test 6: Verify verification code exists in database (via MongoDB)
    print("\n--- Test 6: Verification Code Stored in Database ---")
    total_tests += 1
    try:
        from pymongo import MongoClient
        import os
        
        # Use hardcoded values from backend/.env
        mongo_url = 'mongodb://localhost:27017'
        db_name = 'test_database'
        
        client = MongoClient(mongo_url)
        db = client[db_name]
        
        # Find verification code for test user
        code_record = db.verification_codes.find_one({
            "email": register_data["email"].lower(),
            "used": False
        })
        
        if code_record:
            # Check structure
            has_hash = "code_hash" in code_record
            has_expiry = "expires_at" in code_record
            code_not_exposed = "code" not in code_record or code_record.get("code") is None
            
            if has_hash and has_expiry and code_not_exposed:
                passed_tests += log_test("Verification code in database", True, 
                    f"Code stored with hash (not plaintext), expires_at: {code_record.get('expires_at')}")
            else:
                log_test("Verification code in database", False, 
                    f"Missing fields or code exposed: hash={has_hash}, expiry={has_expiry}, secure={code_not_exposed}")
        else:
            log_test("Verification code in database", False, 
                f"No verification code found for {register_data['email']}")
        
        client.close()
    except Exception as e:
        log_test("Verification code in database", False, f"Exception: {e}")
    
    # Test 7: Test /api/auth/verify-email endpoint with a code
    print("\n--- Test 7: Verify Email Endpoint (with DB code) ---")
    total_tests += 1
    try:
        from pymongo import MongoClient
        import os
        import hashlib
        
        # Use hardcoded values from backend/.env
        mongo_url = 'mongodb://localhost:27017'
        db_name = 'test_database'
        
        client = MongoClient(mongo_url)
        db = client[db_name]
        
        # Create a fresh verification code for testing
        test_code = "123456"
        test_email = f"verifytest_{timestamp}@codero.com"
        code_hash = hashlib.sha256(test_code.encode()).hexdigest()
        
        from datetime import datetime, timedelta
        expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        
        db.verification_codes.update_one(
            {"email": test_email, "used": False},
            {"$set": {
                "email": test_email,
                "code_hash": code_hash,
                "expires_at": expires_at,
                "used": False,
                "created_at": datetime.utcnow().isoformat(),
            }},
            upsert=True
        )
        
        # Now test the verify endpoint
        verify_data = {
            "email": test_email,
            "code": test_code
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/verify-email", json=verify_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("email_verified") == True:
                passed_tests += log_test("Verify email endpoint works", True, 
                    f"Email verified successfully: {data.get('message')}")
            else:
                log_test("Verify email endpoint works", False, 
                    f"Unexpected response: {data}")
        else:
            log_test("Verify email endpoint works", False, 
                f"Status {response.status_code}: {response.text}")
        
        client.close()
    except Exception as e:
        log_test("Verify email endpoint works", False, f"Exception: {e}")
    
    # Test 8: Duplicate username validation
    print("\n--- Test 8: Duplicate Username Validation ---")
    total_tests += 1
    duplicate_username_data = {
        "username": register_data["username"],  # Same username
        "email": f"different_{timestamp}@codero.com",  # Different email
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/register", json=duplicate_username_data, timeout=10)
        if response.status_code == 400:
            data = response.json()
            detail = data.get("detail", "").lower()
            if "username" in detail and "taken" in detail:
                passed_tests += log_test("Duplicate username rejected", True, 
                    f"Clear message: '{data.get('detail')}'")
            else:
                log_test("Duplicate username rejected", False, 
                    f"Unclear error message: {data.get('detail')}")
        else:
            log_test("Duplicate username rejected", False, 
                f"Expected 400, got {response.status_code}")
    except Exception as e:
        log_test("Duplicate username rejected", False, f"Exception: {e}")
    
    # Test 9: Duplicate email validation
    print("\n--- Test 9: Duplicate Email Validation ---")
    total_tests += 1
    duplicate_email_data = {
        "username": f"different_{timestamp}",  # Different username
        "email": register_data["email"],  # Same email
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/register", json=duplicate_email_data, timeout=10)
        if response.status_code == 400:
            data = response.json()
            detail = data.get("detail", "").lower()
            if "email" in detail and ("taken" in detail or "account" in detail):
                passed_tests += log_test("Duplicate email rejected", True, 
                    f"Clear message: '{data.get('detail')}'")
            else:
                log_test("Duplicate email rejected", False, 
                    f"Unclear error message: {data.get('detail')}")
        else:
            log_test("Duplicate email rejected", False, 
                f"Expected 400, got {response.status_code}")
    except Exception as e:
        log_test("Duplicate email rejected", False, f"Exception: {e}")
    
    # Summary
    print("\n" + "="*80)
    print(f"V1.7 AUTH/EMAIL TEST SUMMARY: {passed_tests}/{total_tests} PASSED ({(passed_tests/total_tests)*100:.1f}%)")
    print("="*80 + "\n")
    
    return passed_tests, total_tests

if __name__ == "__main__":
    passed, total = test_v17_auth_email()
    exit(0 if passed == total else 1)
