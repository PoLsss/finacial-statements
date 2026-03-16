"""
Financial Reports RAG API

FastAPI application for PDF processing and RAG chatbot.
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.api.routes import upload, chat, status
from backend.api.routes.chat_stream import router as chat_stream_router
from backend.api.routes.dashboard import router as dashboard_router
from backend.api.routes.statistics import router as statistics_router

app = FastAPI(
    title="Financial Reports RAG API",
    description="API for PDF processing and RAG chatbot",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3333",  # Next.js dev server
        "http://127.0.0.1:3333",
        "http://localhost:2602",  # Backend server
        "http://127.0.0.1:2602",
        "http://localhost:2001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(chat_stream_router, prefix="/api", tags=["chat-stream"])
app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
app.include_router(statistics_router, prefix="/api", tags=["statistics"])


@app.get("/")
def root():
    """Root endpoint - API info."""
    return {
        "message": "Financial Reports RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "upload": "POST /api/upload",
            "chat": "POST /api/chat",
            "status": "GET /api/status"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
