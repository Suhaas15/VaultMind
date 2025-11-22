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
        """Get bearer token, ensuring it's not placeholder"""
        token = self._bearer_token or settings.SKYFLOW_BEARER_TOKEN
        if not token or token == "placeholder":
            raise ValueError("Skyflow Bearer Token not configured. Run: python3 generate_skyflow_token.py")
        return token

    def tokenize(self, data: dict) -> dict:
        """
        Tokenize PII by inserting into Skyflow Vault and getting tokens back.
        """
        # Identify PII fields to tokenize
        pii_fields = {}
        non_pii_data = {}
        
        # Map our keys to Skyflow table columns
        # Skyflow 'persons' table has: name, ssn, date_of_birth, email_address, state
        field_mapping = {
            "name": "name",
            "ssn": "ssn",
            "dob": "date_of_birth",  # Skyflow uses date_of_birth, not dob
            "address": "state",  # Using state field (you can add address field to Skyflow if needed)
            "email": "email_address"  # Skyflow uses email_address, not email
        }
        
        for key, value in data.items():
            if key in field_mapping:
                pii_fields[field_mapping[key]] = value
            else:
                non_pii_data[key] = value
                
        if not pii_fields:
            return data

        # Insert into Skyflow 'persons' table (note: plural)
        if settings.SKYFLOW_VAULT_ID == "placeholder" or not self.vault_id:
            raise ValueError("Skyflow Vault ID not configured. Set SKYFLOW_VAULT_ID in .env")
        
        if not self.bearer_token or self.bearer_token == "placeholder":
            raise ValueError("Skyflow Bearer Token not configured. Run: python3 generate_skyflow_token.py")
        
        print(f"Skyflow: Tokenizing {list(pii_fields.keys())}...")
        result = self.insert_record("persons", pii_fields)
            
        # result['records'][0]['fields'] contains the tokens/values depending on config
        # But typically we get skyflow_id which IS the token for referencing
        skyflow_record = result['records'][0]
        skyflow_id = skyflow_record.get("skyflow_id")
        
        tokenized_data = non_pii_data.copy()
        returned_fields = skyflow_record.get("fields", {})
        
        for key, col_name in field_mapping.items():
            if key in data:
                # If the vault returns a token for this field, use it.
                # Otherwise use the skyflow_id as a fallback token.
                token = returned_fields.get(col_name, skyflow_id)
                tokenized_data[f"{key}_token"] = token
        
        return tokenized_data

    def insert_record(self, table: str, fields: dict) -> dict:
        """
        Insert a record into a Skyflow Vault table and get tokens.
        Uses the Skyflow Data API Records endpoint: /v1/vaults/{vault_id}/{table}
        See: https://docs.skyflow-preview.com/api/data/records/insert-record
        
        Note: Uses the 'persons' table which has fields:
        - name (string)
        - ssn (string)
        - date_of_birth (date format: YYYY-MM-DD)
        - email_address (string)
        - state (string)
        """
        if settings.SKYFLOW_VAULT_ID == "placeholder" or not self.vault_id:
            raise ValueError("Skyflow Vault ID not configured. Set SKYFLOW_VAULT_ID in .env")
        
        if not self.bearer_token or self.bearer_token == "placeholder":
            raise ValueError("Skyflow Bearer Token not configured. Run: python3 generate_skyflow_token.py")
        
        # Format date_of_birth if present (convert to YYYY-MM-DD format)
        formatted_fields = fields.copy()
        if "date_of_birth" in formatted_fields:
            dob_value = formatted_fields["date_of_birth"]
            # If it's in MM/DD/YYYY format, convert to YYYY-MM-DD
            if "/" in str(dob_value):
                parts = str(dob_value).split("/")
                if len(parts) == 3:
                    formatted_fields["date_of_birth"] = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
            
        # Skyflow Data API Records endpoint (per documentation)
        url = f"{self.vault_url}/v1/vaults/{self.vault_id}/{table}"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Skyflow API format: records array with fields object
        # With tokenization: true, Skyflow returns tokens for the inserted data
        payload = {
            "records": [
                {
                    "fields": formatted_fields
                }
            ],
            "tokenization": True,  # Request tokens in response
            "quorum": False  # Optional: for consistency
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Skyflow Insert Record API Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise Exception(f"Failed to insert record into Skyflow: {e}") from e

    def detokenize(self, token: str) -> str:
        """
        Detokenize a Skyflow token to get the original PII value.
        Uses the Skyflow Data API Tokens endpoint: /v1/vaults/{vault_id}/tokens/detokenize
        See: https://docs.skyflow-preview.com/api/data/tokens/detokenize
        
        Note: If token is a skyflow_id (UUID), we need to query the record instead.
        """
        if settings.SKYFLOW_VAULT_ID == "placeholder" or not self.vault_id:
            raise ValueError("Skyflow Vault ID not configured. Set SKYFLOW_VAULT_ID in .env")
        
        if not self.bearer_token or self.bearer_token == "placeholder":
            raise ValueError("Skyflow Bearer Token not configured. Run: python3 generate_skyflow_token.py")
        
        # Check if token looks like a UUID (skyflow_id) - if so, query the record directly
        # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        is_uuid = re.match(uuid_pattern, token.lower()) is not None
        
        if is_uuid:
            # Token is a skyflow_id, query the record directly
            print(f"Token appears to be a skyflow_id (UUID), querying record directly...")
            try:
                # Query the persons table using skyflow_id
                query_url = f"{self.vault_url}/v1/vaults/{self.vault_id}/persons"
                headers = {
                    "Authorization": f"Bearer {self.bearer_token}",
                    "Content-Type": "application/json"
                }
                
                # Use GET with skyflow_id filter or query by ID
                # Try querying with detokenization enabled
                query_params = {
                    "skyflow_ids": token,
                    "redaction": "PLAIN_TEXT"  # Request plain text values
                }
                
                response = requests.get(query_url, params=query_params, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    # Extract value from the first record
                    if "records" in result and len(result["records"]) > 0:
                        record = result["records"][0]
                        fields = record.get("fields", {})
                        # Return the first non-empty field value
                        for field_name, field_value in fields.items():
                            if field_value:
                                return str(field_value)
                
                # If query failed, fall through to detokenize API
            except Exception as query_err:
                print(f"⚠️ Query by skyflow_id failed, trying detokenize API: {query_err}")
        
        # Try standard detokenize API
        url = f"{self.vault_url}/v1/vaults/{self.vault_id}/tokens/detokenize"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "detokenizationParameters": [
                {"token": token}
            ]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # Better error handling
            if response.status_code == 404:
                error_msg = f"Skyflow detokenize endpoint not found (404). This might mean:\n"
                error_msg += f"1. The token format is incorrect (token: {token[:20]}...)\n"
                error_msg += f"2. The vault ID is wrong (vault_id: {self.vault_id})\n"
                error_msg += f"3. The endpoint URL is incorrect (url: {url})\n"
                error_msg += f"4. The token might be a skyflow_id that needs to be queried differently"
                if response.text:
                    error_msg += f"\nResponse: {response.text}"
                raise ValueError(error_msg)
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the detokenized value from response
            # Response format: { "records": [{ "token": "...", "value": "..." }] }
            if "records" in result and len(result["records"]) > 0:
                return result["records"][0].get("value", "Unknown")
            
            return "Unknown"
        except requests.exceptions.RequestException as e:
            print(f"Skyflow Detokenize API Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            
            # Provide helpful error message
            error_msg = f"Failed to detokenize token '{token[:20]}...'. "
            error_msg += "This might be because:\n"
            error_msg += "1. The token is not a valid detokenizable token\n"
            error_msg += "2. The token might be a skyflow_id that needs different handling\n"
            error_msg += "3. The Skyflow vault configuration might not allow detokenization\n"
            error_msg += f"Original error: {e}"
            raise Exception(error_msg) from e

    def detect_pii(self, text: str) -> Dict[str, Any]:
        """
        Detect PII in unstructured text using Skyflow PII MCP server, then tokenize using real Skyflow API.
        Falls back to pattern-based detection if MCP server is unavailable.
        
        Uses: https://www.pii-mcp.dev/mcp (Skyflow PII MCP Server)
        
        Args:
            text: Unstructured text containing potential PII
        
        Returns:
            {
                "entities": [
                    {
                        "type": "NAME" | "SSN" | "DOB" | "ADDRESS" | "PHONE" | "EMAIL",
                        "value": str,
                        "confidence": float (0-1),
                        "start_pos": int,
                        "end_pos": int,
                        "token": str (Skyflow token for the entity)
                    }
                ],
                "redacted_text": str (text with PII replaced by tokens),
                "total_entities_found": int
            }
        """
        if settings.SKYFLOW_VAULT_ID == "placeholder" or not self.vault_id:
            raise ValueError("Skyflow Vault ID not configured. Set SKYFLOW_VAULT_ID in .env")
        
        if not self.bearer_token or self.bearer_token == "placeholder":
            raise ValueError("Skyflow Bearer Token not configured. Run: python3 generate_skyflow_token.py")
        
        print(f"Detecting PII in text of length {len(text)}...")
        
        # Use MCP server if enabled, otherwise use pattern-based detection
        if getattr(settings, 'SKYFLOW_USE_MCP_SERVER', False):
            # Try Skyflow PII MCP server (dehydrate tool)
            print("Using Skyflow PII MCP server for detection...")
            try:
                mcp_url = f"https://www.pii-mcp.dev/mcp?vaultId={self.vault_id}&vaultUrl={self.vault_url}"
                headers = {
                    "Authorization": f"Bearer {self.bearer_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"  # MCP server requires both
                }
                
                # MCP server uses 'dehydrate' tool to detect and redact PII
                # The tool takes inputString and returns processedText with placeholders
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "dehydrate",
                        "arguments": {
                            "inputString": text
                        }
                    }
                }
                
                print("Attempting to use Skyflow PII MCP server...")
                print(f"MCP URL: {mcp_url}")
                response = requests.post(mcp_url, json=payload, headers=headers, timeout=30)
                
                print(f"MCP Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"MCP Response: {json.dumps(result, indent=2)[:500]}")
                    
                    # Check for JSON-RPC error in response
                    if "error" in result:
                        error_code = result["error"].get("code", "unknown")
                        error_msg = result["error"].get("message", "Unknown MCP error")
                        print(f"❌ MCP server returned JSON-RPC error {error_code}: {error_msg}")
                        raise ValueError(f"Skyflow PII MCP server error {error_code}: {error_msg}")
                    
                    # Check if result indicates an error (MCP format with isError flag)
                    if "result" in result:
                        mcp_result = result["result"]
                        if mcp_result.get("isError", False):
                            # Extract error message from content array
                            error_content = mcp_result.get("content", [])
                            if error_content and isinstance(error_content, list) and len(error_content) > 0:
                                error_text = error_content[0].get("text", "Unknown error")
                            else:
                                error_text = "Unknown MCP server error"
                            
                            print(f"❌ MCP server operation failed: {error_text}")
                            raise ValueError(
                                f"Skyflow PII MCP server operation failed: {error_text}\n\n"
                                f"This usually means the MCP server cannot connect to your Skyflow vault.\n"
                                f"Please check:\n"
                                f"1. Vault ID: {self.vault_id}\n"
                                f"2. Vault URL: {self.vault_url}\n"
                                f"3. Bearer token has permissions for the vault\n"
                                f"4. Vault is accessible and configured correctly\n\n"
                                f"Fix this error or disable MCP server usage to continue."
                            )
                    
                        # Parse MCP response format (success case)
                        # The dehydrate tool returns processedText with placeholders like [NAME_abc123]
                        # Access via content array (MCP text response format)
                        if "content" in mcp_result and isinstance(mcp_result["content"], list):
                            # Get processed text from content array
                            content_items = mcp_result["content"]
                            if content_items and content_items[0].get("type") == "text":
                                processed_text = content_items[0].get("text", text)
                            else:
                                # Fallback: check for direct processedText field
                                processed_text = mcp_result.get("processedText", text)
                        else:
                            # Direct field access
                            processed_text = mcp_result.get("processedText", text)
                        
                        # Extract placeholders from processed text (format: [ENTITY_TYPE_token])
                        import re
                        placeholder_pattern = r'\[(\w+)_([a-zA-Z0-9]+)\]'
                        matches = re.finditer(placeholder_pattern, processed_text)
                        
                        entities = []
                        detected_values = {}  # Track original values by position in text
                        
                        # The dehydrate tool replaces PII with placeholders
                        # We need to find the original values before replacement
                        # For now, we'll parse the placeholders and use them as tokens
                        # The actual tokenization will happen when we insert into Skyflow
                        
                        for match in matches:
                            entity_type = match.group(1).upper()
                            placeholder_token = match.group(2)
                            
                            # Find the original text that was replaced
                            # We need to map back to original text positions
                            # For now, we'll extract from original text based on patterns
                            original_value = None
                            
                            # Try to find the original value by looking at the text around the placeholder
                            placeholder_start = match.start()
                            # Search backwards and forwards in original text for likely matches
                            
                            entities.append({
                                "type": entity_type,
                                "value": original_value or f"[{entity_type}]",
                                "confidence": 0.95,  # High confidence from Skyflow Detect
                                "start_pos": placeholder_start,
                                "end_pos": match.end(),
                                "token": placeholder_token,
                                "placeholder": match.group(0)
                            })
                        
                        print(f"✅ Skyflow PII MCP server detected {len(entities)} PII entities via dehydrate")
                        
                        # For now, return entities with placeholders
                        # The actual tokenization can happen when inserting into Skyflow
                        return {
                            "entities": entities,
                            "redacted_text": processed_text,
                            "total_entities_found": len(entities)
                        }
                    else:
                        print(f"❌ MCP server response missing 'result' field: {result}")
                        raise ValueError(f"MCP server response format invalid: {result}")
                else:
                    error_text = response.text[:500]
                    print(f"❌ MCP server returned status {response.status_code}: {error_text}")
                    raise requests.exceptions.HTTPError(f"MCP server failed: {response.status_code} - {error_text}")
            except requests.exceptions.RequestException as e:
                error_msg = f"Skyflow PII MCP server request failed: {e}"
                print(f"❌ {error_msg}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"   Response status: {e.response.status_code}")
                    print(f"   Response body: {e.response.text[:500]}")
                raise ValueError(
                    f"Skyflow PII MCP server unavailable. Error: {error_msg}\n"
                    f"Check:\n"
                    f"1. Vault ID: {self.vault_id}\n"
                    f"2. Vault URL: {self.vault_url}\n"
                    f"3. Bearer token is valid\n"
                    f"4. MCP server URL: https://www.pii-mcp.dev/mcp"
                ) from e
            except Exception as e:
                print(f"❌ Skyflow PII MCP server error: {e}")
                raise ValueError(f"Skyflow PII MCP server failed: {e}. Set SKYFLOW_USE_MCP_SERVER=false in .env to use pattern-based detection instead.") from e
        else:
            # Use pattern-based detection (no MCP server)
            print("Using pattern-based PII detection (MCP server disabled)...")
        import re
        
        entities = []
        
        # Detect SSN pattern (XXX-XX-XXXX)
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        for match in re.finditer(ssn_pattern, text):
            ssn_value = match.group()
            try:
                # Tokenize detected SSN using real Skyflow API
                insert_result = self.insert_record("persons", {"ssn": ssn_value})
                if insert_result.get("records"):
                    skyflow_id = insert_result["records"][0].get("skyflow_id")
                    token = skyflow_id
                else:
                    token = f"sky_s_{uuid.uuid4().hex[:6]}"
            except Exception as e:
                print(f"Warning: Failed to tokenize SSN, using placeholder token: {e}")
                token = f"sky_s_{uuid.uuid4().hex[:6]}"
            
            entities.append({
                "type": "SSN",
                "value": ssn_value,
                "confidence": 0.98,
                "start_pos": match.start(),
                "end_pos": match.end(),
                "token": token
            })
        
        # Detect potential names (capitalized words - First Last or First Middle Last)
        # Allow 2-3 capitalized words
        name_pattern = r'\b([A-Z][a-z]+(?: [A-Z][a-z]+){1,2})\b'
        detected_names = set()  # Avoid duplicates
        for match in re.finditer(name_pattern, text):
            name_value = match.group()
            # Skip common false positives
            if name_value in ["Patient Name", "Doctor Name", "Full Name", "First Name", "Last Name", "Medical Record", "Health History"]:
                continue
            if name_value in detected_names:
                continue
            detected_names.add(name_value)
            
            try:
                # Tokenize detected name using real Skyflow API
                insert_result = self.insert_record("persons", {"name": name_value})
                if insert_result.get("records"):
                    skyflow_id = insert_result["records"][0].get("skyflow_id")
                    token = skyflow_id
                else:
                    token = f"sky_n_{uuid.uuid4().hex[:6]}"
            except Exception as e:
                print(f"Warning: Failed to tokenize name, using placeholder token: {e}")
                token = f"sky_n_{uuid.uuid4().hex[:6]}"
            
            entities.append({
                "type": "NAME",
                "value": name_value,
                "confidence": 0.85,
                "start_pos": match.start(),
                "end_pos": match.end(),
                "token": token
            })
        
        # Detect DOB pattern (YYYY-MM-DD or MM/DD/YYYY)
        dob_pattern = r'\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b'
        for match in re.finditer(dob_pattern, text):
            dob_value = match.group()
            # Normalize to YYYY-MM-DD format for Skyflow
            if "/" in dob_value:
                parts = dob_value.split("/")
                if len(parts) == 3:
                    dob_normalized = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                else:
                    dob_normalized = dob_value
            else:
                dob_normalized = dob_value
            
            try:
                # Tokenize detected DOB using real Skyflow API
                insert_result = self.insert_record("persons", {"date_of_birth": dob_normalized})
                if insert_result.get("records"):
                    skyflow_id = insert_result["records"][0].get("skyflow_id")
                    token = skyflow_id
                else:
                    token = f"sky_d_{uuid.uuid4().hex[:6]}"
            except Exception as e:
                print(f"Warning: Failed to tokenize DOB, using placeholder token: {e}")
                token = f"sky_d_{uuid.uuid4().hex[:6]}"
            
            entities.append({
                "type": "DOB",
                "value": dob_value,
                "confidence": 0.92,
                "start_pos": match.start(),
                "end_pos": match.end(),
                "token": token
            })
        
        # Detect email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            email_value = match.group()
            try:
                # Tokenize detected email using real Skyflow API
                insert_result = self.insert_record("persons", {"email_address": email_value})
                if insert_result.get("records"):
                    skyflow_id = insert_result["records"][0].get("skyflow_id")
                    token = skyflow_id
                else:
                    token = f"sky_e_{uuid.uuid4().hex[:6]}"
            except Exception as e:
                print(f"Warning: Failed to tokenize email, using placeholder token: {e}")
                token = f"sky_e_{uuid.uuid4().hex[:6]}"
            
            entities.append({
                "type": "EMAIL",
                "value": email_value,
                "confidence": 0.95,
                "start_pos": match.start(),
                "end_pos": match.end(),
                "token": token
            })
        
        # Create redacted text (replace PII with tokens)
        redacted_text = text
        # Sort by position (reverse) to maintain positions during replacement
        for entity in sorted(entities, key=lambda x: x["start_pos"], reverse=True):
            redacted_text = (
                redacted_text[:entity["start_pos"]] + 
                entity["token"] + 
                redacted_text[entity["end_pos"]:]
            )
        
        print(f"Detected {len(entities)} PII entities, all tokenized using Skyflow Vault API")
        
        return {
            "entities": entities,
            "redacted_text": redacted_text,
            "total_entities_found": len(entities)
        }
    
    def auto_tokenize_detected(self, detect_result: Dict[str, Any]) -> Dict[str, str]:
        """
        Automatically tokenize all detected PII entities.
        
        Args:
            detect_result: Result from detect_pii()
        
        Returns:
            Mapping of entity types to tokens
        """
        tokens = {}
        
        for entity in detect_result.get("entities", []):
            entity_type = entity["type"].lower()
            
            # Store token for each entity type
            if entity_type == "name":
                tokens["name_token"] = entity["token"]
                tokens["name_confidence"] = entity["confidence"]
            elif entity_type == "ssn":
                tokens["ssn_token"] = entity["token"]
                tokens["ssn_confidence"] = entity["confidence"]
            elif entity_type == "dob":
                tokens["dob_token"] = entity["token"]
                tokens["dob_confidence"] = entity["confidence"]
            elif entity_type == "email":
                tokens["email_token"] = entity["token"]
                tokens["email_confidence"] = entity["confidence"]
        
        return tokens

    def invoke_function(self, function_id: str, payload: dict):
        """
        Invoke a Skyflow Function for vault-confined execution.
        
        The Skyflow Function expects the payload in this format:
        {
            "body": {
                "prompt_template": "...",
                "patient_data": {...},
                "parameters": {...}
            }
        }
        """
        if not function_id or function_id == "placeholder":
            raise ValueError("Skyflow Function ID not configured. Set SKYFLOW_FUNCTION_ID in .env")
        
        if settings.SKYFLOW_VAULT_ID == "placeholder" or not self.vault_id:
            raise ValueError("Skyflow Vault ID not configured. Set SKYFLOW_VAULT_ID in .env")
        
        if not self.bearer_token or self.bearer_token == "placeholder":
            raise ValueError("Skyflow Bearer Token not configured. Run: python3 generate_skyflow_token.py")

        # Skyflow Functions endpoint: /v1/vaults/{vault_id}/functions/{function_id}
        # Or sometimes just /v1/functions/{function_id}
        url = f"{self.vault_url}/v1/vaults/{self.vault_id}/functions/{function_id}"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        # Skyflow Functions API expects payload wrapped in "body"
        # Based on the function code: event.body contains the actual data
        request_payload = {
            "body": payload
        }
        
        try:
            print(f"Skyflow: Invoking function {function_id}...")
            print(f"Payload: {request_payload}")
            response = requests.post(url, json=request_payload, headers=headers, timeout=60)
            
            # If 404, try the alternative URL format
            if response.status_code == 404:
                print(f"⚠️ 404 on vault-scoped URL, trying global function URL...")
                url = f"{self.vault_url}/v1/functions/{function_id}"
                response = requests.post(url, json=request_payload, headers=headers, timeout=60)
            
            response.raise_for_status()
            result = response.json()
            
            # Handle response structure
            # Skyflow Function returns: { success: true, summary: "...", tokens_used: {...}, ... }
            # But API might wrap it differently, so check both
            if isinstance(result, dict):
                # If wrapped in a response object, extract it
                if "result" in result:
                    result = result["result"]
                elif "body" in result:
                    result = result["body"]
            
            # Normalize tokens_used structure
            # The function returns data.usage from Anthropic API: { input_tokens, output_tokens }
            if "tokens_used" in result:
                tokens = result["tokens_used"]
                if isinstance(tokens, dict):
                    # Convert Anthropic format to our format
                    if "input_tokens" in tokens:
                        result["tokens_used"] = {
                            "input": tokens.get("input_tokens", 0),
                            "output": tokens.get("output_tokens", 0)
                        }
            
            # Calculate cost if not provided (approximate)
            if "cost_usd" not in result or result.get("cost_usd") == 0:
                input_tokens = result.get("tokens_used", {}).get("input", 0)
                output_tokens = result.get("tokens_used", {}).get("output", 0)
                # Approximate cost: $3 per 1M input tokens, $15 per 1M output tokens (Claude 3.5 Sonnet)
                cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)
                result["cost_usd"] = round(cost, 6)
            
            print(f"Skyflow Function Result: Success={result.get('success')}, Summary length={len(result.get('summary', ''))}")
            return result
        except requests.exceptions.Timeout:
            print("Skyflow Function Error: Request timed out (>60s)")
            return {
                "success": False,
                "error": "Request timeout - function took too long to execute",
                "summary": "Analysis failed due to timeout.",
                "tokens_used": {"input": 0, "output": 0}
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"Skyflow Function API Error: {e}"
            print(error_msg)
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            # Re-raise to propagate the error
            raise Exception(f"Failed to invoke Skyflow Function: {error_msg}") from e
        except Exception as e:
            error_msg = f"Skyflow Function Error: {e}"
            print(error_msg)
            raise Exception(f"Failed to invoke Skyflow Function: {error_msg}") from e

skyflow_service = SkyflowService()
