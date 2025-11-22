import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

project_id = os.getenv("SANITY_PROJECT_ID")
dataset = os.getenv("SANITY_DATASET")
token = os.getenv("SANITY_API_TOKEN")

mutate_url = f"https://{project_id}.api.sanity.io/v2021-06-07/data/mutate/{dataset}"
headers = {"Authorization": f"Bearer {token}"}

test_mutation = {
    "mutations": [
        {
            "create": {
                "_type": "patient",
                "condition": "Test Debug",
                "processed": False
            }
        }
    ]
}

print("Creating test patient...")
response = requests.post(mutate_url, json=test_mutation, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
