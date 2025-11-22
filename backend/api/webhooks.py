from fastapi import APIRouter, Request
from ..workers.tasks import process_patient_task
from ..main import sio
router = APIRouter()
@router.post("/sanity")
async def sanity_webhook(request: Request):
    payload = await request.json()
    print(f"Webhook received: {payload}")
    doc = payload.get('ids', {}) 
    await sio.emit('patient_created', {'patient': doc})
    return {"status": "received"}
@router.post("/process-patient")
async def process_patient_webhook(payload: dict):
    print(f"Processing webhook: {payload}")
    patient_id = payload.get('_id')
    if patient_id:
        task = process_patient_task.delay(patient_id, payload)
        await sio.emit('processing_started', {'patientId': patient_id})
        return {"status": "processing", "task_id": task.id}
    return {"status": "ignored"}