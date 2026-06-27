import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env variables
load_dotenv()

from db.session_store import init_db
from routers.sessions import router as sessions_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup database tables on startup
    init_db()
    
    # Initialize UPLOAD_DIR
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    yield

app = FastAPI(
    title="RupeeRadar API",
    description="AI-powered personal finance assistant backend",
    version="0.2.0",
    lifespan=lifespan
)

# CORS configuration
allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions_router)

@app.get("/health")
def health_check():
    """Simple API health check endpoint."""
    return {"status": "ok", "environment": os.getenv("ENV", "development")}
