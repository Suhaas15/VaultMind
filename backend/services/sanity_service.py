import requests
from ..config import settings
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
class SanityService:
    def __init__(self):
        self.project_id = settings.SANITY_PROJECT_ID
        self.dataset = settings.SANITY_DATASET
        self.token = settings.SANITY_API_TOKEN
        self.base_url = f"https://{self.project_id}.api.sanity.io/v2021-06-07/data/mutate/{self.dataset}"
        self.query_url = f"https://{self.project_id}.api.sanity.io/v2021-06-07/data/query/{self.dataset}"
    def create_patient(self, patient_data: dict):
        if settings.SANITY_PROJECT_ID == "placeholder" or not self.project_id:
            raise ValueError("Sanity Project ID not configured. Set SANITY_PROJECT_ID in .env")
        if not self.token or self.token == "placeholder":
            raise ValueError("Sanity API Token not configured. Set SANITY_API_TOKEN in .env")
        unique_id = str(uuid.uuid4())
        mutations = {
            "mutations": [
                {
                    "create": {
                        "_type": "patient",
                        "patientId": unique_id,  
                        **patient_data,
                        "processed": False
                    }
                }
            ]
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(self.base_url, json=mutations, headers=headers)
        response.raise_for_status()
        result = response.json()
        query = f'*[_type == "patient" && patientId == "{unique_id}"][0]'
        query_response = requests.get(
            self.query_url,
            params={"query": query},
            headers=headers
        )
        query_response.raise_for_status()
        query_result = query_response.json().get("result")
        if query_result and "_id" in query_result:
            sanity_id = query_result["_id"]
            return {"id": sanity_id, "_id": sanity_id, "patientId": unique_id, **patient_data}
        else:
            raise ValueError(f"Failed to retrieve created patient document")
    def update_patient(self, patient_id: str, updates: dict):
        if settings.SANITY_PROJECT_ID == "placeholder" or not self.project_id:
            raise ValueError("Sanity Project ID not configured. Set SANITY_PROJECT_ID in .env")
        if not self.token or self.token == "placeholder":
            raise ValueError("Sanity API Token not configured. Set SANITY_API_TOKEN in .env")
        mutations = {
            "mutations": [
                {
                    "patch": {
                        "id": patient_id,
                        "set": updates
                    }
                }
            ]
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(self.base_url, json=mutations, headers=headers)
        response.raise_for_status()
        return response.json()
    def get_patients(self):
        if settings.SANITY_PROJECT_ID == "placeholder" or not self.project_id:
            raise ValueError("Sanity Project ID not configured. Set SANITY_PROJECT_ID in .env")
        if not self.token or self.token == "placeholder":
            raise ValueError("Sanity API Token not configured. Set SANITY_API_TOKEN in .env")
        query = '*[_type == "patient"] | order(_createdAt desc)'
        params = {"query": query}
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(self.query_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json().get("result", [])
    def create_document(self, doc_type: str, document_data: dict) -> Dict[str, Any]:
        if settings.SANITY_PROJECT_ID == "placeholder" or not self.project_id:
            raise ValueError("Sanity Project ID not configured. Set SANITY_PROJECT_ID in .env")
        if not self.token or self.token == "placeholder":
            raise ValueError("Sanity API Token not configured. Set SANITY_API_TOKEN in .env")
        mutations = {
            "mutations": [
                {
                    "create": {
                        "_type": doc_type,
                        **document_data
                    }
                }
            ]
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(self.base_url, json=mutations, headers=headers)
        response.raise_for_status()
        result = response.json()
        if "results" in result and len(result["results"]) > 0:
            doc_id = result["results"][0].get("id", str(uuid.uuid4()))
        else:
            doc_id = str(uuid.uuid4())
        return {
            "_id": doc_id,
            "_type": doc_type,
            **document_data
        }
    def update_document(self, document_id: str, updates: dict) -> Dict[str, Any]:
        if settings.SANITY_PROJECT_ID == "placeholder" or not self.project_id:
            raise ValueError("Sanity Project ID not configured. Set SANITY_PROJECT_ID in .env")
        if not self.token or self.token == "placeholder":
            raise ValueError("Sanity API Token not configured. Set SANITY_API_TOKEN in .env")
        mutations = {
            "mutations": [
                {
                    "patch": {
                        "id": document_id,
                        "set": updates
                    }
                }
            ]
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(self.base_url, json=mutations, headers=headers)
        response.raise_for_status()
        return response.json()
    def query(self, groq_query: str) -> List[Dict[str, Any]]:
        if settings.SANITY_PROJECT_ID == "placeholder" or not self.project_id:
            raise ValueError("Sanity Project ID not configured. Set SANITY_PROJECT_ID in .env")
        if not self.token or self.token == "placeholder":
            raise ValueError("Sanity API Token not configured. Set SANITY_API_TOKEN in .env")
        params = {"query": groq_query}
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(self.query_url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json().get("result", [])
        if isinstance(result, dict):
            return result
        return result
    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        if settings.SANITY_PROJECT_ID == "placeholder" or not self.project_id:
            raise ValueError("Sanity Project ID not configured. Set SANITY_PROJECT_ID in .env")
        if not self.token or self.token == "placeholder":
            raise ValueError("Sanity API Token not configured. Set SANITY_API_TOKEN in .env")
        query = f'*[_type == "patient" && _id == "{patient_id}"][0]'
        params = {"query": query}
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(self.query_url, params=params, headers=headers)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        result = response.json().get("result")
        return result
    def delete_all_patients(self):
        if settings.SANITY_PROJECT_ID == "placeholder" or not self.project_id:
            raise ValueError("Sanity Project ID not configured. Set SANITY_PROJECT_ID in .env")
        if not self.token or self.token == "placeholder":
            raise ValueError("Sanity API Token not configured. Set SANITY_API_TOKEN in .env")
        query = '*[_type == "patient"]._id'
        params = {"query": query}
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(self.query_url, params=params, headers=headers)
        response.raise_for_status()
        ids = response.json().get("result", [])
        if not ids:
            return
        mutations = {
            "mutations": [
                {"delete": {"id": doc_id}} for doc_id in ids
            ]
        }
        response = requests.post(self.base_url, json=mutations, headers=headers)
        response.raise_for_status()
sanity_service = SanityService()