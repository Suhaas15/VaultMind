from ..config import settings
import uuid
import requests
import json
from typing import Dict, List, Any
class SkyflowService:
    def __init__(self):
        self.vault_id = settings.SKYFLOW_VAULT_ID
        self.vault_url = settings.SKYFLOW_VAULT_URL
        self._bearer_token = settings.SKYFLOW_BEARER_TOKEN
    @property
    def bearer_token(self):
        token = self._bearer_token or settings.SKYFLOW_BEARER_TOKEN
        if not token or token == "placeholder":
            raise ValueError("Skyflow Bearer Token not configured. Run: python3 generate_skyflow_token.py")
        return token
    def _mock_tokenize(self, value: str, field_type: str) -> str:
        import base64
        if not value:
            return ""
        encoded = base64.b64encode(str(value).encode()).decode()
        return f"mock_{field_type}_{encoded}"
    def _mock_detokenize(self, token: str) -> str:
        import base64
        if not token or not token.startswith("mock_"):
            return token
        try:
            parts = token.split("_")
            if len(parts) >= 3:
                encoded = parts[-1]
                return base64.b64decode(encoded).decode()
        except Exception:
            pass
        return token
    def tokenize(self, data: dict) -> dict:
        pii_fields = {}
        non_pii_data = {}
        field_mapping = {
            "name": "name",
            "ssn": "ssn",
            "dob": "date_of_birth",
            "address": "state",
            "email": "email_address"
        }
        for key, value in data.items():
            if key in field_mapping:
                pii_fields[field_mapping[key]] = value
            else:
                non_pii_data[key] = value
        if not pii_fields:
            return data
        try:
            if settings.SKYFLOW_VAULT_ID == "placeholder" or not self.vault_id:
                raise ValueError("Skyflow Vault ID not configured")
            if not self.bearer_token or self.bearer_token == "placeholder":
                raise ValueError("Skyflow Bearer Token not configured")
            print(f"Skyflow: Tokenizing {list(pii_fields.keys())}...")
            result = self.insert_record("persons", pii_fields)
            skyflow_record = result['records'][0]
            skyflow_id = skyflow_record.get("skyflow_id")
            tokenized_data = non_pii_data.copy()
            returned_fields = skyflow_record.get("fields", {})
            for key, col_name in field_mapping.items():
                if key in data:
                    token = returned_fields.get(col_name)
                    if not token:
                        token = f"{skyflow_id}#{col_name}"
                    tokenized_data[f"{key}_token"] = token
            return tokenized_data
        except Exception as e:
            print(f"⚠️ Skyflow tokenization failed: {e}")
            print("🔄 Falling back to local mock tokenization...")
            tokenized_data = non_pii_data.copy()
            for key, value in data.items():
                if key in field_mapping:
                    token = self._mock_tokenize(value, key)
                    tokenized_data[f"{key}_token"] = token
            return tokenized_data
    def insert_record(self, table: str, fields: dict) -> dict:
        if settings.SKYFLOW_VAULT_ID == "placeholder" or not self.vault_id:
            raise ValueError("Skyflow Vault ID not configured")
        if not self.bearer_token or self.bearer_token == "placeholder":
            raise ValueError("Skyflow Bearer Token not configured")
        formatted_fields = fields.copy()
        if "date_of_birth" in formatted_fields:
            dob_value = formatted_fields["date_of_birth"]
            if "/" in str(dob_value):
                parts = str(dob_value).split("/")
                if len(parts) == 3:
                    formatted_fields["date_of_birth"] = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
        url = f"{self.vault_url}/v1/vaults/{self.vault_id}/{table}"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "records": [{"fields": formatted_fields}],
            "tokenization": True,
            "quorum": False
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Skyflow Insert Record API Error: {e}")
            raise Exception(f"Failed to insert record into Skyflow: {e}") from e
    def detokenize(self, token: str) -> str:
        if token and str(token).startswith("mock_"):
            return self._mock_detokenize(token)
        try:
            if settings.SKYFLOW_VAULT_ID == "placeholder" or not self.vault_id:
                raise ValueError("Skyflow Vault ID not configured")
            if not self.bearer_token or self.bearer_token == "placeholder":
                raise ValueError("Skyflow Bearer Token not configured")
            target_field = None
            skyflow_id_to_query = token
            if "#" in token:
                parts = token.split("#")
                if len(parts) == 2:
                    skyflow_id_to_query = parts[0]
                    target_field = parts[1]
            import re
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            is_uuid = re.match(uuid_pattern, skyflow_id_to_query.lower()) is not None
            if is_uuid:
                try:
                    query_url = f"{self.vault_url}/v1/vaults/{self.vault_id}/persons"
                    headers = {
                        "Authorization": f"Bearer {self.bearer_token}",
                        "Content-Type": "application/json"
                    }
                    query_params = {
                        "skyflow_ids": skyflow_id_to_query,
                        "redaction": "PLAIN_TEXT"
                    }
                    response = requests.get(query_url, params=query_params, headers=headers, timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        if "records" in result and len(result["records"]) > 0:
                            record = result["records"][0]
                            fields = record.get("fields", {})
                            if target_field:
                                value = fields.get(target_field)
                                if value:
                                    return str(value)
                            for field_name, field_value in fields.items():
                                if field_value:
                                    return str(field_value)
                except Exception as query_err:
                    print(f"⚠️ Query by skyflow_id failed: {query_err}")
            url = f"{self.vault_url}/v1/vaults/{self.vault_id}/tokens/detokenize"
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "detokenizationParameters": [{"token": token}]
            }
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            if "records" in result and len(result["records"]) > 0:
                return result["records"][0].get("value", "Unknown")
            return "Unknown"
        except Exception as e:
            print(f"⚠️ Skyflow detokenization failed: {e}")
            if str(token).startswith("mock_"):
                return self._mock_detokenize(token)
            return f"[{token[:8]}...]"
    def detect_pii(self, text: str) -> Dict[str, Any]:
        print(f"DEBUG: detect_pii called with text length {len(text)}")
        if settings.SKYFLOW_VAULT_ID == "placeholder" or not self.vault_id:
            print("DEBUG: Using mock detection (config)")
            return self._mock_detect_pii(text)
        try:
            return self._real_detect_pii(text)
        except Exception as e:
            print(f"⚠️ PII Detection failed: {e}")
            return self._mock_detect_pii(text)
    def _real_detect_pii(self, text: str) -> Dict[str, Any]:
        # Placeholder for real implementation
        raise NotImplementedError("Real PII detection not implemented yet")
    def _mock_detect_pii(self, text: str) -> Dict[str, Any]:
        import re
        entities = []
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        for match in re.finditer(ssn_pattern, text):
            val = match.group()
            entities.append({
                "type": "SSN",
                "value": val,
                "confidence": 0.99,
                "start_pos": match.start(),
                "end_pos": match.end(),
                "token": self._mock_tokenize(val, "ssn")
            })
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            val = match.group()
            entities.append({
                "type": "EMAIL",
                "value": val,
                "confidence": 0.99,
                "start_pos": match.start(),
                "end_pos": match.end(),
                "token": self._mock_tokenize(val, "email")
            })
        dob_pattern = r'\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b'
        for match in re.finditer(dob_pattern, text):
            val = match.group()
            entities.append({
                "type": "DOB",
                "value": val,
                "confidence": 0.99,
                "start_pos": match.start(),
                "end_pos": match.end(),
                "token": self._mock_tokenize(val, "dob")
            })
            
        # Name detection (heuristics for mock data)
        # Look for "Name: Value" or "Patient: Value" or "Patient Name: Value"
        name_pattern = r'(?:Name|Patient|Patient Name):\s*([A-Za-z\s]+)(?:\n|$)'
        for match in re.finditer(name_pattern, text, re.IGNORECASE):
            val = match.group(1).strip()
            if val and len(val) > 2 and "confidential" not in val.lower():
                entities.append({
                    "type": "NAME",
                    "value": val,
                    "confidence": 0.95,
                    "start_pos": match.start(1),
                    "end_pos": match.end(1),
                    "token": self._mock_tokenize(val, "name")
                })
        redacted_text = text
        for entity in sorted(entities, key=lambda x: x["start_pos"], reverse=True):
            redacted_text = (
                redacted_text[:entity["start_pos"]] + 
                entity["token"] + 
                redacted_text[entity["end_pos"]:]
            )
        return {
            "entities": entities,
            "redacted_text": redacted_text,
            "total_entities_found": len(entities)
        }

    def auto_tokenize_detected(self, detect_result: Dict[str, Any]) -> Dict[str, str]:
        """
        Takes the result from detect_pii and returns a dictionary of tokens.
        """
        tokens = {}
        entities = detect_result.get("entities", [])
        
        # Extract tokens for known types
        for entity in entities:
            entity_type = entity.get("type")
            token = entity.get("token")
            
            if entity_type == "SSN":
                tokens["ssn_token"] = token
                tokens["ssn_confidence"] = entity.get("confidence", 0)
            elif entity_type == "EMAIL":
                tokens["email_token"] = token
                tokens["email_confidence"] = entity.get("confidence", 0)
            elif entity_type == "DOB":
                tokens["dob_token"] = token
                tokens["dob_confidence"] = entity.get("confidence", 0)
            elif entity_type == "NAME":
                tokens["name_token"] = token
                tokens["name_confidence"] = entity.get("confidence", 0)
                
        return tokens
    def invoke_function(self, function_id: str, payload: dict):
        try:
            if not function_id or function_id == "placeholder":
                raise ValueError("Skyflow Function ID not configured")
            if settings.SKYFLOW_VAULT_ID == "placeholder" or not self.vault_id:
                raise ValueError("Skyflow Vault ID not configured")
            if not self.bearer_token or self.bearer_token == "placeholder":
                raise ValueError("Skyflow Bearer Token not configured")
            url = f"{self.vault_url}/v1/vaults/{self.vault_id}/functions/{function_id}"
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            request_payload = {"body": payload}
            print(f"Skyflow: Invoking function {function_id}...")
            response = requests.post(url, json=request_payload, headers=headers, timeout=60)
            if response.status_code == 404:
                url = f"{self.vault_url}/v1/functions/{function_id}"
                response = requests.post(url, json=request_payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            if isinstance(result, dict):
                if "result" in result:
                    result = result["result"]
                elif "body" in result:
                    result = result["body"]
            return result
        except Exception as e:
            print(f"⚠️ Skyflow Function invocation failed: {e}")
            print("🔄 Returning mock function response (failure handled by agent_service)...")
            return {"success": False, "error": str(e)}
skyflow_service = SkyflowService()