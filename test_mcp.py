#!/usr/bin/env python3
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

vault_id = os.getenv('SKYFLOW_VAULT_ID')
vault_url = os.getenv('SKYFLOW_VAULT_URL')
token = os.getenv('SKYFLOW_BEARER_TOKEN')

mcp_url = f'https://www.pii-mcp.dev/mcp?vaultId={vault_id}&vaultUrl={vault_url}'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/event-stream'
}

# First, list available tools
list_payload = {
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'tools/list'
}

print("Listing available tools...")
response = requests.post(mcp_url, json=list_payload, headers=headers, timeout=10)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    result = response.json()
    print(f'Available tools: {json.dumps(result, indent=2)}')
else:
    print(f'Error: {response.text}')

print("\n" + "="*80 + "\n")

# Now try calling a tool with different possible names
tool_names = ['detect_pii', 'detectPII', 'detect-pii', 'pii_detect', 'piiDetect']
for tool_name in tool_names:
    payload = {
        'jsonrpc': '2.0',
        'id': 2,
        'method': 'tools/call',
        'params': {
            'name': tool_name,
            'arguments': {
                'text': 'Patient name is John Smith, SSN 123-45-6789, DOB 01/15/1980'
            }
        }
    }
    print(f"Trying tool name: {tool_name}")
    response = requests.post(mcp_url, json=payload, headers=headers, timeout=10)
    if response.status_code == 200:
        result = response.json()
        if 'error' not in result:
            print(f"✅ Success with {tool_name}!")
            print(f'Response: {json.dumps(result, indent=2)[:500]}')
            break
        else:
            print(f"   Error: {result.get('error', {}).get('message', 'Unknown')}")
    else:
        print(f"   Status {response.status_code}: {response.text[:200]}")

response = requests.post(mcp_url, json=payload, headers=headers, timeout=10)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    result = response.json()
    print(f'Response: {json.dumps(result, indent=2)[:1000]}')
else:
    print(f'Error: {response.text}')

