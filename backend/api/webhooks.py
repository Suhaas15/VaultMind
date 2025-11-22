from fastapi import APIRouter, Request
from ..workers.tasks import process_patient_task
from ..main import sio

router = APIRouter()

@router.post("/sanity")
async def sanity_webhook(request: Request):
    payload = await request.json()
    print(f"Webhook received: {payload}")
    
    # Extract patient data from payload
    # Sanity webhook payload structure depends on configuration
    # Assuming we get the document
    doc = payload.get('ids', {}) # Simplified
    
    # Trigger Celery task
    # process_patient_task.delay(doc.get('id'), doc)
    
    # Notify frontend via Socket.IO
    await sio.emit('patient_created', {'patient': doc})
    
    return {"status": "received"}

@router.post("/process-patient")
async def process_patient_webhook(payload: dict):
    # This endpoint is called by Sanity webhook when a new patient is created
    print(f"Processing webhook: {payload}")
    
    patient_id = payload.get('_id')
    if patient_id:
        # Trigger background task
        task = process_patient_task.delay(patient_id, payload)
        
        # Notify frontend that processing started
        await sio.emit('processing_started', {'patientId': patient_id})
        
        return {"status": "processing", "task_id": task.id}
    
    return {"status": "ignored"}
