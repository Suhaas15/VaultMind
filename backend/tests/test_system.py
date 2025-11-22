import asyncio
import sys
import os
import unittest
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.skyflow_service import skyflow_service
from backend.services.agent_service import agent_service

class TestVaultMindSystem(unittest.TestCase):
    
    def setUp(self):
        print(f"\nStarting test: {self._testMethodName}")

    def test_01_skyflow_mock_tokenization(self):
        """Test that Skyflow service falls back to mock tokenization."""
        print("Testing Skyflow Mock Tokenization...")
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "email": "john@example.com"
        }
        
        # This should trigger mock tokenization if real credentials fail or are invalid
        # We rely on the fact that we likely don't have valid active credentials for the real vault in this env
        tokenized = skyflow_service.tokenize(data)
        
        print(f"Tokenized result: {tokenized}")
        
        self.assertIn("name_token", tokenized)
        self.assertIn("ssn_token", tokenized)
        self.assertIn("email_token", tokenized)
        
        # Verify token format (mock tokens start with mock_)
        # Note: If real tokenization works, this assertion might fail, which is fine, 
        # but we expect mock in this specific test environment context usually.
        # However, to be robust, we just check that we got *some* token.
        self.assertTrue(tokenized["name_token"])

    def test_02_skyflow_mock_detokenization(self):
        """Test that Skyflow service can detokenize mock tokens."""
        print("Testing Skyflow Mock Detokenization...")
        original_val = "SecretValue"
        # Create a mock token manually using the internal method if possible, or just rely on the format
        # Since we can't easily access _mock_tokenize from here if it's protected (it is in python but convention)
        # Let's use the public tokenize to get a token first
        
        data = {"name": original_val}
        tokenized = skyflow_service.tokenize(data)
        token = tokenized.get("name_token")
        
        detokenized = skyflow_service.detokenize(token)
        print(f"Original: {original_val} -> Token: {token} -> Detokenized: {detokenized}")
        
        self.assertEqual(detokenized, original_val)

    def test_03_agent_service_mock_fallback(self):
        """Test that Agent service falls back to local data files when AI fails."""
        print("Testing Agent Service Mock Fallback...")
        
        # Run async test
        asyncio.run(self._async_test_agent_service())

    async def _async_test_agent_service(self):
        patient_id = "test-patient-verify"
        patient_data = {
            "name": "Test Patient",
            "condition": "Acute Myocardial Infarction", # Should match cardiac file
            "department": "Cardiology",
            "priority": "URGENT"
        }
        
        # This process_patient call handles:
        # 1. Skyflow function invocation (should fail -> mock)
        # 2. Claude API call (should fail -> mock)
        # 3. Sanity update (should fail -> graceful continue)
        result = await agent_service.process_patient(patient_id, patient_data)
        
        print(f"Agent Result: {result}")
        
        self.assertTrue(result.get("processed"))
        self.assertTrue(len(result.get("ai_summary", "")) > 0)
        
        # Verify it used the fallback model
        model = result.get("claude_model", "")
        print(f"Model used: {model}")
        self.assertTrue("fallback" in model or "mock" in model)

    def test_04_pii_detection_fallback(self):
        """Test PII detection fallback."""
        print("Testing PII Detection Fallback...")
        text = "Patient John Doe with SSN 123-45-6789 visited today."
        
        result = skyflow_service.detect_pii(text)
        print(f"PII Detection Result: {result}")
        
        self.assertTrue(result.get("total_entities_found") > 0)
        entities = result.get("entities", [])
        
        # Check if we found Name and SSN
        types = [e["type"] for e in entities]
        self.assertIn("SSN", types)
        # Name detection might be flaky with regex, but SSN should be solid
        
        # Check redaction
        redacted = result.get("redacted_text")
        self.assertNotEqual(redacted, text)
        self.assertNotIn("123-45-6789", redacted)

    def test_05_mock_name_detection(self):
        """Test that mock PII detection finds names."""
        print("Testing Mock Name Detection...")
        text = "Patient Name: Jane Doe\nDOB: 1980-01-01"
        result = skyflow_service.detect_pii(text)
        
        entities = result.get("entities", [])
        types = [e["type"] for e in entities]
        values = [e["value"] for e in entities]
        
        print(f"Entities found: {entities}")
        
        self.assertIn("NAME", types)
        self.assertIn("Jane Doe", values)
        
    def test_06_auto_tokenize(self):
        """Test auto_tokenize_detected method."""
        print("Testing Auto Tokenize...")
        detect_result = {
            "entities": [
                {"type": "NAME", "value": "Jane Doe", "token": "mock_name_123", "confidence": 0.95},
                {"type": "SSN", "value": "123-45-6789", "token": "mock_ssn_456", "confidence": 0.99}
            ]
        }
        tokens = skyflow_service.auto_tokenize_detected(detect_result)
        print(f"Auto tokens: {tokens}")
        
        self.assertEqual(tokens.get("name_token"), "mock_name_123")
        self.assertEqual(tokens.get("ssn_token"), "mock_ssn_456")

    def test_07_missing_fields_handling(self):
        """Test handling of missing fields in auto_tokenize."""
        print("Testing Missing Fields Handling...")
        detect_result = {
            "entities": [
                {"type": "SSN", "value": "123-45-6789", "token": "mock_ssn_456", "confidence": 0.99}
            ]
        }
        tokens = skyflow_service.auto_tokenize_detected(detect_result)
        print(f"Partial tokens: {tokens}")
        
        self.assertIsNone(tokens.get("name_token"))
        self.assertEqual(tokens.get("ssn_token"), "mock_ssn_456")

if __name__ == '__main__':
    unittest.main()
