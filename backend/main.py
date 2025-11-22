from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from .config import settings

app = FastAPI(title="VaultMind Pro API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# Create the main app first for routes
fastapi_app = app

# Wrap with Socket.IO
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
