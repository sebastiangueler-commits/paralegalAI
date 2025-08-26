from fastapi import APIRouter
from app.api.v1.endpoints import auth, sentencias, expedientes, ai

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(sentencias.router, prefix="/sentencias", tags=["legal sentences"])
api_router.include_router(expedientes.router, prefix="/expedientes", tags=["legal cases"])
api_router.include_router(ai.router, prefix="/ai", tags=["artificial intelligence"])