#!/usr/bin/env python3
"""
Generate Skyflow Bearer Token from credentials.json

This script generates a JWT and exchanges it for an OAuth access token
that can be used for Skyflow Vault API authentication.
"""

import json
import time
import jwt
import requests
from pathlib import Path

def exchange_jwt_for_access_token(signed_jwt, token_uri, client_id=None):
    """Exchange JWT for OAuth access token using Skyflow's OAuth flow"""
    try:
        print("Exchanging JWT for OAuth access token...")
        
        # Skyflow OAuth uses urn:ietf:params:oauth:grant-type:jwt-bearer grant type
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed_jwt
        }
        
        # Some implementations might need client_id
        if client_id:
            data["client_id"] = client_id
        
        response = requests.post(
            token_uri,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            # Skyflow uses 'accessToken' (camelCase), also check 'access_token' for compatibility
            access_token = result.get("accessToken") or result.get("access_token")
            if access_token:
                print("✅ Successfully obtained OAuth access token")
                expires_in = result.get("expiresIn") or result.get("expires_in", 3600)
                print(f"   Token expires in: {expires_in} seconds ({expires_in/60:.1f} minutes)")
                print(f"   Token type: {result.get('tokenType', 'Bearer')}")
                return access_token
            else:
                print(f"⚠️  No accessToken in response: {result}")
                return signed_jwt
        else:
            error_text = response.text[:500]
            print(f"⚠️  OAuth exchange failed (status {response.status_code}): {error_text}")
            # Try alternative method
            return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Failed to exchange JWT for OAuth token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text[:500]}")
        return None
    except Exception as e:
        print(f"⚠️  Unexpected error during OAuth exchange: {e}")
        return None

def generate_bearer_token(credentials_path="credentials.json", exchange=True):
    """Generate a bearer token from Skyflow credentials."""
    
    # Load credentials
    with open(credentials_path, 'r') as f:
        credentials = json.load(f)
    
    # Extract required fields
    private_key = credentials['privateKey']
    key_id = credentials['keyID']
    token_uri = credentials['tokenURI']
    client_id = credentials.get('clientID')  # Use clientID if available
    
    # For issuer, try clientID first (Skyflow service accounts typically use clientID)
    # Fall back to keyID if clientID not available
    issuer = client_id if client_id else key_id
    
    print(f"Using issuer: {issuer} (from clientID: {client_id or 'N/A'}, keyID: {key_id})")
    
    # Create JWT claims
    # According to Skyflow docs, issuer should typically be the clientID
    claims = {
        "iss": issuer,
        "key": key_id,  # keyID used in 'key' claim
        "aud": token_uri,
        "exp": int(time.time()) + 3600,  # Token valid for 1 hour
        "sub": issuer,  # Subject should match issuer for service accounts
    }
    
    # Generate signed JWT
    signed_jwt = jwt.encode(
        claims,
        private_key,
        algorithm='RS256',
        headers={"kid": key_id}
    )
    
    # Exchange JWT for OAuth access token if requested
    bearer_token = signed_jwt
    if exchange:
        oauth_token = exchange_jwt_for_access_token(signed_jwt, token_uri, client_id)
        if oauth_token and oauth_token != signed_jwt:
            bearer_token = oauth_token
            print("\n✅ Using OAuth access token (recommended for vault API calls)")
        else:
            print("\n⚠️  OAuth exchange failed or returned JWT. The JWT token may still work for vault API calls.")
            print("   If you continue to get 401 errors, check:")
            print("   1. Service account permissions in Skyflow Studio")
            print("   2. Vault access permissions")
            print("   3. Credentials are from the correct environment (preview vs production)")
    
    print("\n" + "=" * 80)
    print("SKYFLOW BEARER TOKEN GENERATED")
    print("=" * 80)
    print("\nYour bearer token (valid for 60 minutes):")
    print("-" * 80)
    print(bearer_token)
    print("-" * 80)
    print("\n✅ Copy the token above and add it to your .env file as:")
    print("   SKYFLOW_BEARER_TOKEN=<paste_token_here>")
    print("\n⚠️  Note: This token expires in 60 minutes. Re-run this script to generate a new one.")
    print("=" * 80)
    
    return bearer_token

if __name__ == "__main__":
    try:
        token = generate_bearer_token()
    except FileNotFoundError:
        print("❌ Error: credentials.json not found in current directory")
        print("   Make sure you've downloaded the credentials file from Skyflow Studio")
    except KeyError as e:
        print(f"❌ Error: Missing required field in credentials: {e}")
    except Exception as e:
        print(f"❌ Error generating token: {e}")
