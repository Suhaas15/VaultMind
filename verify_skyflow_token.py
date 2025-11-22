#!/usr/bin/env python3
"""
Verify Skyflow Bearer Token and diagnose authentication issues
"""

import json
import jwt
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def decode_token(token):
    """Decode JWT token without verification to inspect claims"""
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        print(f"❌ Error decoding token: {e}")
        return None

def verify_credentials(credentials_path="credentials.json"):
    """Verify credentials.json structure"""
    try:
        with open(credentials_path, 'r') as f:
            credentials = json.load(f)
        
        required_fields = ['privateKey', 'keyID', 'tokenURI']
        missing = [f for f in required_fields if f not in credentials]
        
        if missing:
            print(f"❌ Missing required fields in credentials.json: {', '.join(missing)}")
            return False
        
        print("✅ Credentials file structure is valid")
        print(f"   keyID: {credentials['keyID']}")
        print(f"   tokenURI: {credentials['tokenURI']}")
        return True
    except FileNotFoundError:
        print(f"❌ credentials.json not found at {credentials_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in credentials.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False

def verify_token_claims(token):
    """Verify JWT token claims match expected format"""
    decoded = decode_token(token)
    if not decoded:
        return False
    
    print("\n📋 JWT Token Claims:")
    print(f"   iss (issuer): {decoded.get('iss')}")
    print(f"   sub (subject): {decoded.get('sub')}")
    print(f"   aud (audience): {decoded.get('aud')}")
    print(f"   exp (expires): {decoded.get('exp')}")
    print(f"   key: {decoded.get('key')}")
    
    # Check if issuer matches key
    if decoded.get('iss') != decoded.get('key'):
        print("⚠️  Warning: 'iss' and 'key' claims should match")
        return False
    
    if decoded.get('iss') != decoded.get('sub'):
        print("⚠️  Warning: 'iss' and 'sub' claims should match")
        return False
    
    print("✅ JWT claims format looks correct")
    return True

def main():
    print("=" * 80)
    print("SKYFLOW TOKEN VERIFICATION")
    print("=" * 80)
    
    # Load .env
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from {env_path}")
    else:
        print(f"⚠️  .env file not found at {env_path}")
    
    # Check credentials
    credentials_path = Path(__file__).parent / "credentials.json"
    if not verify_credentials(credentials_path):
        print("\n❌ Cannot proceed without valid credentials.json")
        sys.exit(1)
    
    # Check token
    token = os.getenv("SKYFLOW_BEARER_TOKEN", "").strip()
    if not token or token == "placeholder":
        print("\n⚠️  SKYFLOW_BEARER_TOKEN not set in .env")
        print("   Run: python3 generate_skyflow_token.py")
        sys.exit(1)
    
    print(f"\n✅ Found SKYFLOW_BEARER_TOKEN (length: {len(token)})")
    
    # Verify token claims
    if not verify_token_claims(token):
        print("\n⚠️  Token claims may be incorrect")
        print("   Try regenerating the token:")
        print("   python3 generate_skyflow_token.py")
    
    # Load credentials to check if token matches
    try:
        with open(credentials_path, 'r') as f:
            credentials = json.load(f)
        
        decoded = decode_token(token)
        if decoded:
            expected_key_id = credentials['keyID']
            actual_issuer = decoded.get('iss')
            
            if actual_issuer != expected_key_id:
                print(f"\n❌ TOKEN ISSUER MISMATCH!")
                print(f"   Expected issuer (keyID): {expected_key_id}")
                print(f"   Actual issuer (token iss): {actual_issuer}")
                print(f"\n   The token was generated with a different keyID than in credentials.json")
                print(f"   Solution: Regenerate the token with:")
                print(f"   python3 generate_skyflow_token.py")
                sys.exit(1)
            else:
                print(f"\n✅ Token issuer matches credentials keyID: {actual_issuer}")
            
            expected_audience = credentials['tokenURI']
            actual_audience = decoded.get('aud')
            
            if actual_audience != expected_audience:
                print(f"\n⚠️  AUDIENCE MISMATCH:")
                print(f"   Expected audience (tokenURI): {expected_audience}")
                print(f"   Actual audience (token aud): {actual_audience}")
                print(f"   This might cause authentication issues")
            else:
                print(f"✅ Token audience matches credentials tokenURI: {actual_audience}")
    
    except Exception as e:
        print(f"\n⚠️  Could not verify token against credentials: {e}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nIf you're getting 401 errors:")
    print("1. Verify credentials.json has the correct keyID and tokenURI from Skyflow Studio")
    print("2. Regenerate the token: python3 generate_skyflow_token.py")
    print("3. Update .env file with the new token")
    print("4. Check Skyflow API authentication docs:")
    print("   https://docs.skyflow.com/api-authentication/")
    print("=" * 80)

if __name__ == "__main__":
    main()

