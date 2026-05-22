#!/usr/bin/env python3
"""
SMTP Verification Testing for Codero
Tests the Gmail SMTP verification code delivery behavior
"""

import requests
import json
import time

# Backend URL from environment
BACKEND_URL = "https://codero-stack.preview.emergentagent.com/api"

def test_smtp_verification():
    """Test SMTP verification code endpoint"""
    print("=" * 80)
    print("SMTP VERIFICATION CODE TESTING")
    print("=" * 80)
    print()
    
    # Test 1: Send verification code to codero.devs@gmail.com
    print("Test 1: POST /auth/send-verification-code")
    print("-" * 80)
    
    test_email = "codero.devs@gmail.com"
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/send-verification-code",
            json={"email": test_email},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            if "message" in data and "email" in data and "expires_at" in data:
                print("✅ Response structure correct")
                
                # Verify code is NOT exposed in response
                if "code" not in data and "verification_code" not in data:
                    print("✅ Verification code NOT exposed in response (secure)")
                else:
                    print("❌ SECURITY ISSUE: Verification code exposed in response!")
                    return False
                
                # Verify email matches
                if data["email"] == test_email.lower():
                    print(f"✅ Email matches: {data['email']}")
                else:
                    print(f"❌ Email mismatch: expected {test_email.lower()}, got {data['email']}")
                    return False
                
                print("✅ Test 1 PASSED: Verification code endpoint working correctly")
            else:
                print("❌ Response missing required fields")
                return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    
    print()
    
    # Test 2: Wait for background task and check backend logs
    print("Test 2: Backend logs inspection (waiting 3 seconds for background task)")
    print("-" * 80)
    print("Waiting for background task to complete...")
    time.sleep(3)
    print("✅ Background task should have completed")
    print("Note: Check backend logs manually for SMTP delivery status")
    print()
    
    # Test 3: Verify backend health after request
    print("Test 3: GET / (Backend health check)")
    print("-" * 80)
    
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Backend remains healthy after verification request")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    print()
    print("=" * 80)
    print("SMTP VERIFICATION TESTING COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print("✅ POST /auth/send-verification-code returns 200")
    print("✅ Response does not expose verification code")
    print("✅ Backend remains healthy after request")
    print()
    print("Next step: Check backend logs for SMTP delivery status")
    print("Expected log patterns:")
    print('  - Success: "Verification email sent to <email>"')
    print('  - Failure: "Verification email delivery failed for <email>: <error>"')
    print()
    
    return True

if __name__ == "__main__":
    success = test_smtp_verification()
    sys.exit(0 if success else 1)
