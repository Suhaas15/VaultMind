#!/usr/bin/env python3
"""
Regenerate Skyflow bearer token and update .env file automatically
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Import the token generation function
sys.path.insert(0, str(Path(__file__).parent))
from generate_skyflow_token import generate_bearer_token

def update_env_file(env_path, new_token):
    """Update SKYFLOW_BEARER_TOKEN in .env file"""
    try:
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
        
        if not token_updated:
            lines.append(f'\nSKYFLOW_BEARER_TOKEN={new_token}\n')
        
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        return True
    except Exception as e:
        print(f"Error updating .env file: {e}", file=sys.stderr)
        return False

def main():
    env_path = Path(__file__).parent / ".env"
    
    print("Regenerating Skyflow bearer token...")
    print("=" * 80)
    
    try:
        # Generate new token (with OAuth exchange)
        new_token = generate_bearer_token(exchange=True)
        
        if new_token:
            # Update .env file
            if update_env_file(env_path, new_token):
                print(f"\n✅ Successfully updated .env file with new token")
                print(f"   File: {env_path}")
                print("\n💡 Restart your application to use the new token")
            else:
                print(f"\n⚠️  Token generated but failed to update .env file")
                print(f"   Manually update .env with:")
                print(f"   SKYFLOW_BEARER_TOKEN={new_token[:50]}...")
        else:
            print("\n❌ Failed to generate token")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

