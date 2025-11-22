import requests
import time
import os
import json

BASE_URL = "http://localhost:8000/api"

def test_full_flow():
    print("🚀 Starting full flow verification...")
    
    # 1. Create a test document
    filename = "test_patient_flow.txt"
    content = """
    Patient Record
    Name: Sarah Connor
    SSN: 987-65-4321
    DOB: 1985-05-20
    Condition: Asthma
    Notes: Patient reports shortness of breath.
    """
    
    with open(filename, "w") as f:
        f.write(content)
        
    try:
        # 2. Upload document
        print("\n📤 Uploading document...")
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "text/plain")}
            response = requests.post(f"{BASE_URL}/patients/upload-document", files=files)
            
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.text}")
            return
            
        result = response.json()
        print(f"✅ Upload successful! Response: {json.dumps(result, indent=2)}")
        
        if result.get("status") != "success":
            print(f"❌ Upload status not success: {result.get('status')}")
            return
            
        patient_id = result.get("patient_id")
        print(f"🆔 Patient ID: {patient_id}")
        
        # 3. Poll for processing status
        print("\n⏳ Waiting for processing...")
        max_retries = 10
        for i in range(max_retries):
            response = requests.get(f"{BASE_URL}/patients/{patient_id}")
            if response.status_code != 200:
                print(f"⚠️ Failed to get patient details: {response.status_code}")
                time.sleep(2)
                continue
                
            patient = response.json()
            print(f"   Attempt {i+1}: Processed={patient.get('processed')}")
            
            if patient.get("processed"):
                print("\n✅ Patient processed successfully!")
                print(f"   AI Summary: {patient.get('ai_summary')}")
                print(f"   Condition: {patient.get('condition')}")
                print(f"   Tokens Used: {patient.get('tokens_used')}")
                break
            
            time.sleep(2)
        else:
            print("\n❌ Timeout waiting for processing")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_full_flow()
