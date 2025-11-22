import requests
import os
from dotenv import load_dotenv

load_dotenv()

project_id = os.getenv("SANITY_PROJECT_ID")
dataset = os.getenv("SANITY_DATASET")
token = os.getenv("SANITY_API_TOKEN")

print(f"Testing Sanity connection...")
print(f"Project ID: {project_id}")
print(f"Dataset: {dataset}")
print(f"Token: {token[:20]}..." if token else "Token: None")

# Test query endpoint
query_url = f"https://{project_id}.api.sanity.io/v2021-06-07/data/query/{dataset}"
query = '*[_type == "patient"] | order(_createdAt desc)[0...5]'

headers = {"Authorization": f"Bearer {token}"}
params = {"query": query}

try:
    response = requests.get(query_url, params=params, headers=headers)
    print(f"\nQuery Response Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        patients = result.get("result", [])
        print(f"✅ Successfully connected to Sanity!")
        print(f"Found {len(patients)} patients")
        for p in patients[:3]:
            print(f"  - {p.get('_id')}: {p.get('condition', 'Unknown')}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test mutate endpoint
print(f"\nTesting mutate endpoint...")
mutate_url = f"https://{project_id}.api.sanity.io/v2021-06-07/data/mutate/{dataset}"
test_mutation = {
    "mutations": [
        {
            "create": {
                "_type": "patient",
                "condition": "Test",
                "processed": False
            }
        }
    ]
}

try:
    response = requests.post(mutate_url, json=test_mutation, headers=headers)
    print(f"Mutate Response Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Mutate endpoint works!")
        result = response.json()
        if "results" in result and len(result["results"]) > 0:
            doc_id = result["results"][0].get("id")
            print(f"Created test document: {doc_id}")
            
            # Clean up - delete the test document
            delete_mutation = {
                "mutations": [{"delete": {"id": doc_id}}]
            }
            requests.post(mutate_url, json=delete_mutation, headers=headers)
            print(f"Cleaned up test document")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")
