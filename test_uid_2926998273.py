#!/usr/bin/env python3
"""
Test script specifically for UID 2926998273 with enhanced retry logic
"""

import asyncio
import sys
import os
import requests
from app.utils import load_tokens
from app.encryption import enc
from app.request_handler import send_multiple_requests
from real_token_generator import real_token_generator

def test_token_generation_for_uid():
    """Test token generation specifically for UID 2926998273"""
    uid = "2926998273"
    print(f"🎯 Testing token generation for UID {uid}...")
    
    # Generate a fresh token for this UID from India accounts
    generator = real_token_generator
    if generator is None:
        print("❌ Token generator not available")
        return False
    
    # Try to generate tokens for India accounts
    try:
        from real_token_generator import RealTokenGenerator
        token_gen = RealTokenGenerator()
        
        # Load India accounts
        accounts = token_gen.load_accounts("IND_ACC.json")
        if not accounts:
            print("❌ No India accounts found")
            return False
        
        print(f"📄 Found {len(accounts)} India accounts")
        
        # Try to generate token for first few accounts
        successful_tokens = 0
        for i, account in enumerate(accounts[:5]):  # Test first 5
            if token_gen.validate_account_data(account):
                if "guest_account_info" in account:
                    guest_info = account.get("guest_account_info", {})
                    acc_uid = guest_info.get("com.garena.msdk.guest_uid", "")
                    password = guest_info.get("com.garena.msdk.guest_password", "")
                else:
                    acc_uid = str(account.get("uid", ""))
                    password = account.get("password", "")
                
                print(f"🔄 Testing token generation for account UID {acc_uid}...")
                token_data = token_gen.get_token(password, acc_uid, retry_count=10)
                
                if token_data:
                    print(f"✅ Successfully generated token for UID {acc_uid}")
                    
                    # Now try to generate JWT token
                    jwt_result = token_gen.generate_jwt_token(acc_uid, token_data)
                    if jwt_result:
                        print(f"✅ Successfully generated JWT token for UID {acc_uid}")
                        successful_tokens += 1
                    else:
                        print(f"❌ Failed to generate JWT token for UID {acc_uid}")
                else:
                    print(f"❌ Failed to generate token for UID {acc_uid}")
        
        print(f"📊 Successfully generated {successful_tokens}/5 tokens")
        return successful_tokens > 0
        
    except Exception as e:
        print(f"❌ Error during token generation test: {e}")
        return False

async def test_api_requests_for_uid():
    """Test API requests specifically for UID 2926998273"""
    uid = "2926998273"
    server_name = "IND"  # India server
    url = "https://ff.garena.com/api/anticheat/v1/reportRogueUser"
    
    print(f"🎯 Testing API requests for UID {uid} on {server_name} server...")
    
    # Load tokens
    tokens = load_tokens(server_name)
    if not tokens:
        print(f"❌ No tokens available for {server_name} server")
        return False
    
    print(f"📄 Found {len(tokens)} tokens for {server_name} server")
    
    # Test with multiple requests
    try:
        result = await send_multiple_requests(uid, server_name, url)
        if result and result > 0:
            print(f"✅ Successfully sent {result} like requests for UID {uid}")
            return True
        else:
            print(f"❌ Failed to send requests for UID {uid}")
            return False
    except Exception as e:
        print(f"❌ Error during API request test: {e}")
        return False

def test_player_info_for_uid():
    """Test getting player info for UID 2926998273"""
    uid = "2926998273"
    server_name = "IND"
    
    print(f"🎯 Testing player info retrieval for UID {uid}...")
    
    try:
        # Load tokens
        tokens = load_tokens(server_name)
        if not tokens:
            print(f"❌ No tokens available for {server_name} server")
            return False
        
        # Encrypt UID
        encrypted_uid = enc(uid)
        if not encrypted_uid:
            print(f"❌ Failed to encrypt UID {uid}")
            return False
        
        print(f"✅ Successfully encrypted UID {uid}")
        
        # Try to get player info with first token
        from app.request_handler import make_request
        token = tokens[0]["token"]
        
        result = make_request(encrypted_uid, server_name, token)
        if result:
            print(f"✅ Successfully retrieved player info for UID {uid}")
            return True
        else:
            print(f"❌ Failed to retrieve player info for UID {uid}")
            return False
            
    except Exception as e:
        print(f"❌ Error during player info test: {e}")
        return False

async def main():
    """Run all tests for UID 2926998273"""
    print("🚀 Starting comprehensive test for UID 2926998273...")
    print("=" * 60)
    
    # Test 1: Token Generation
    print("\n1️⃣ Testing Token Generation...")
    token_success = test_token_generation_for_uid()
    
    # Test 2: Player Info Retrieval
    print("\n2️⃣ Testing Player Info Retrieval...")
    info_success = test_player_info_for_uid()
    
    # Test 3: API Requests
    print("\n3️⃣ Testing API Requests...")
    api_success = await test_api_requests_for_uid()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"Token Generation: {'✅ PASS' if token_success else '❌ FAIL'}")
    print(f"Player Info:      {'✅ PASS' if info_success else '❌ FAIL'}")
    print(f"API Requests:     {'✅ PASS' if api_success else '❌ FAIL'}")
    
    overall_success = token_success and info_success and api_success
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)