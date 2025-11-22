from celery import Celery
from ..config import settings
from ..services.agent_service import agent_service
import asyncio

# Initialize Celery
celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task(name="process_patient_task")
def process_patient_task(patient_id: str, patient_data: dict):
    # Run async agent service in sync celery task
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(agent_service.process_patient(patient_id, patient_data))
    return result
