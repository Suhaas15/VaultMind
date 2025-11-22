#!/usr/bin/env python3
"""
Test Skyflow authentication with different methods
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

def test_token_against_vault(token, vault_id, vault_url):
    """Test if token works with vault API"""
    print(f"\n🔍 Testing token against vault API...")
    print(f"   Vault ID: {vault_id}")
    print(f"   Vault URL: {vault_url}")
    
    # Try a simple GET request to check authentication
    url = f"{vault_url}/v1/vaults/{vault_id}/persons"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"   Testing GET {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Token is valid!")
            return True
        elif response.status_code == 401:
            print("   ❌ Token authentication failed")
            print(f"   Response: {response.text}")
            return False
        elif response.status_code == 404:
            print("   ⚠️  Endpoint not found (but auth might be OK)")
            return None
        else:
            print(f"   ⚠️  Unexpected status: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_token_against_oauth(token_uri, jwt_token):
    """Test different OAuth exchange methods"""
    print(f"\n🔍 Testing OAuth token exchange...")
    print(f"   Token URI: {token_uri}")
    
    methods = [
        {
            "name": "grant_type=client_credentials",
            "data": {
                "grant_type": "client_credentials",
                "assertion": jwt_token
            }
        },
        {
            "name": "grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer",
            "data": {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_token
            }
        },
        {
            "name": "client_assertion_type",
            "data": {
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": jwt_token,
                "grant_type": "client_credentials"
            }
        }
    ]
    
    for method in methods:
        try:
            print(f"\n   Trying: {method['name']}")
            response = requests.post(
                token_uri,
                data=method["data"],
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success! Access token: {result.get('access_token', 'N/A')[:50]}...")
                return result.get('access_token')
            else:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   Error: {e}")
    
    return None

def main():
    # Load environment
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    
    token = os.getenv("SKYFLOW_BEARER_TOKEN", "").strip()
    vault_id = os.getenv("SKYFLOW_VAULT_ID", "").strip()
    vault_url = os.getenv("SKYFLOW_VAULT_URL", "").strip()
    
    if not all([token, vault_id, vault_url]):
        print("❌ Missing required environment variables")
        return
    
    print("=" * 80)
    print("SKYFLOW AUTHENTICATION TEST")
    print("=" * 80)
    
    # Test current token
    result = test_token_against_vault(token, vault_id, vault_url)
    
    if result is False:
        print("\n⚠️  Current token failed authentication")
        print("   Attempting OAuth token exchange...")
        
        # Try to exchange JWT for OAuth token
        credentials_path = Path(__file__).parent / "credentials.json"
        if credentials_path.exists():
            with open(credentials_path, 'r') as f:
                credentials = json.load(f)
            
            token_uri = credentials.get('tokenURI')
            if token_uri:
                oauth_token = test_token_against_oauth(token_uri, token)
                if oauth_token:
                    print(f"\n✅ Got OAuth token! Use this in .env:")
                    print(f"SKYFLOW_BEARER_TOKEN={oauth_token}")
                else:
                    print("\n❌ Could not exchange JWT for OAuth token")
                    print("   Check your credentials.json and Skyflow service account permissions")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

