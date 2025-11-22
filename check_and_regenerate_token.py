#!/usr/bin/env python3
"""
Check if Skyflow bearer token is expired and regenerate if needed
"""

import os
import sys
import json
import time
import jwt
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

def check_token_expiry(token):
    """Check if token is expired or expires soon (within 5 minutes)"""
    try:
        decoded = jwt.decode(token, options={'verify_signature': False})
        exp = decoded.get('exp', 0)
        if exp:
            exp_time = datetime.fromtimestamp(exp)
            now = datetime.now()
            time_until_expiry = exp_time - now
            
            # Check if expired or expires within 5 minutes
            if time_until_expiry <= timedelta(minutes=5):
                return True, time_until_expiry
            return False, time_until_expiry
        return True, None  # No expiration found, assume expired
    except Exception as e:
        # If we can't decode, assume expired
        return True, None

def exchange_jwt_for_access_token(signed_jwt, token_uri, client_id=None):
    """Exchange JWT for OAuth access token"""
    try:
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed_jwt
        }
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
            return result.get("accessToken") or result.get("access_token")
        return None
    except Exception:
        return None

def generate_new_token(credentials_path="credentials.json"):
    """Generate a new bearer token from credentials"""
    try:
        with open(credentials_path, 'r') as f:
            credentials = json.load(f)
        
        private_key = credentials['privateKey']
        key_id = credentials['keyID']
        token_uri = credentials['tokenURI']
        client_id = credentials.get('clientID')
        
        # Use clientID as issuer (Skyflow service accounts use clientID)
        issuer = client_id if client_id else key_id
        
        claims = {
            "iss": issuer,
            "key": key_id,
            "aud": token_uri,
            "exp": int(time.time()) + 3600,  # 1 hour
            "sub": issuer,
        }
        
        signed_jwt = jwt.encode(
            claims,
            private_key,
            algorithm='RS256',
            headers={"kid": key_id}
        )
        
        # Exchange JWT for OAuth access token
        oauth_token = exchange_jwt_for_access_token(signed_jwt, token_uri, client_id)
        if oauth_token:
            return oauth_token
        
        # Fallback to JWT if OAuth exchange fails
        return signed_jwt
    except Exception as e:
        print(f"Error generating token: {e}", file=sys.stderr)
        return None

def update_env_file(env_path, new_token):
    """Update SKYFLOW_BEARER_TOKEN in .env file"""
    try:
        # Read current .env
        lines = []
        token_updated = False
        
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if line.strip().startswith('SKYFLOW_BEARER_TOKEN='):
                        lines.append(f'SKYFLOW_BEARER_TOKEN={new_token}\n')
                        token_updated = True
                    else:
                        lines.append(line)
        
        # If token line not found, add it
        if not token_updated:
            lines.append(f'SKYFLOW_BEARER_TOKEN={new_token}\n')
        
        # Write back
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        return True
    except Exception as e:
        print(f"Error updating .env: {e}", file=sys.stderr)
        return False

def main():
    # Find .env file
    script_dir = Path(__file__).parent
    env_path = script_dir / ".env"
    credentials_path = script_dir / "credentials.json"
    
    if not env_path.exists():
        print("⚠️  .env file not found, skipping token check", file=sys.stderr)
        return 0
    
    if not credentials_path.exists():
        print("⚠️  credentials.json not found, skipping token regeneration", file=sys.stderr)
        return 0
    
    # Load current token
    load_dotenv(env_path)
    current_token = os.getenv("SKYFLOW_BEARER_TOKEN", "").strip()
    
    if not current_token or current_token == "placeholder":
        print("ℹ️  SKYFLOW_BEARER_TOKEN not set, generating new token...")
        new_token = generate_new_token(credentials_path)
        if new_token:
            if update_env_file(env_path, new_token):
                print("✅ Generated and saved new Skyflow bearer token")
                return 0
            else:
                print("❌ Failed to update .env file", file=sys.stderr)
                return 1
        else:
            print("❌ Failed to generate token", file=sys.stderr)
            return 1
    
    # Check if expired
    is_expired, time_remaining = check_token_expiry(current_token)
    
    if is_expired:
        if time_remaining and time_remaining.total_seconds() > 0:
            minutes = time_remaining.total_seconds() / 60
            print(f"⚠️  Skyflow bearer token expires in {minutes:.0f} minutes, regenerating...")
        else:
            print(f"⚠️  Skyflow bearer token expired, regenerating...")
        new_token = generate_new_token(credentials_path)
        if new_token:
            if update_env_file(env_path, new_token):
                print("✅ Regenerated and saved new Skyflow bearer token (valid for 60 minutes)")
                return 0
            else:
                print("❌ Failed to update .env file", file=sys.stderr)
                return 1
        else:
            print("❌ Failed to regenerate token", file=sys.stderr)
            return 1
    else:
        # Token is still valid
        hours = time_remaining.total_seconds() / 3600
        minutes = (time_remaining.total_seconds() % 3600) / 60
        if hours >= 1:
            print(f"✅ Skyflow bearer token is valid for {hours:.1f} hours")
        else:
            print(f"✅ Skyflow bearer token is valid for {minutes:.0f} minutes")
        return 0

if __name__ == "__main__":
    sys.exit(main())

