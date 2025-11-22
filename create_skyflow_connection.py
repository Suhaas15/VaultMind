#!/usr/bin/env python3
"""
Create a Skyflow Connection to invoke the secure-ai-analysis function
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
VAULT_ID = "a66c8e2f5fac40dd929723f20f49fd33"
ACCOUNT_ID = "u81740d3215e4583b26581dd83583fa6"
WORKSPACE_ID = "d214744a8e444106929ff522adb4cb9e"
FUNCTION_DEPLOYMENT_ID = "dbaa945fd78449c9a261d513d1d3a413"
BEARER_TOKEN = os.getenv("SKYFLOW_BEARER_TOKEN")

# Management API endpoint
MANAGEMENT_API_URL = "https://manage.skyflowapis-preview.com/v1"

def create_function_connection():
    """Create an inbound connection to invoke the Skyflow Function"""
    
    url = f"{MANAGEMENT_API_URL}/vaults/{VAULT_ID}/connections"
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "X-SKYFLOW-ACCOUNT-ID": ACCOUNT_ID,
        "Content-Type": "application/json"
    }
    
    # Connection configuration
    connection_config = {
        "connectionName": "vaultmind-ai-processor",
        "description": "AI processing for patient data using Claude",
        "connectionType": "INBOUND",
        "routes": [
            {
                "routeName": "process_patient",
                "path": "/process",
                "method": "POST",
                "functionDeploymentID": FUNCTION_DEPLOYMENT_ID,
                "functionMethod": "handler"
            }
        ]
    }
    
    print("Creating Skyflow Connection...")
    print(f"URL: {url}")
    print(f"Config: {connection_config}")
    
    try:
        response = requests.post(url, json=connection_config, headers=headers)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            connection_id = result.get("connectionID") or result.get("id")
            
            if connection_id:
                connection_url = f"https://a370a9658141.vault.skyflowapis-preview.com/v1/connections/{connection_id}/process"
                print(f"\n✅ Connection created successfully!")
                print(f"Connection ID: {connection_id}")
                print(f"Connection URL: {connection_url}")
                print(f"\nAdd this to your .env file:")
                print(f"SKYFLOW_CONNECTION_URL={connection_url}")
                return connection_url
            else:
                print(f"⚠️ Connection created but no ID returned: {result}")
        else:
            print(f"❌ Failed to create connection: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    if not BEARER_TOKEN:
        print("❌ SKYFLOW_BEARER_TOKEN not found in .env")
        print("Run: python3 check_and_regenerate_token.py")
        exit(1)
    
    create_function_connection()
