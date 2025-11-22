from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from .config import settings
app = FastAPI(title="VaultMind Pro API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
fastapi_app = app
app = socketio.ASGIApp(sio, fastapi_app)
from .api import patients, webhooks, feedback
fastapi_app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
fastapi_app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
fastapi_app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
@fastapi_app.get("/")
async def root():
    return {"message": "VaultMind Pro API is running"}
@fastapi_app.get("/health")
async def health_check():
    return {"status": "healthy"}