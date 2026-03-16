"""Dashboard route for system summary metrics."""
from fastapi import APIRouter
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.api.schemas.dashboard import DashboardResponse, DashboardData

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """
    Get dashboard summary: document count, chunks, cost, tokens.
    """
    try:
        total_documents = 0
        total_chunks = 0
        total_embeddings = 0
        total_cost = 0.0
        total_tokens = 0

        try:
            from backend.implementations.mongodb_manager import get_mongodb_manager
            mongo = get_mongodb_manager()
            status = mongo.get_status()
            total_chunks = status["chunks_count"]
            total_embeddings = status["embeddings_count"]
            total_documents = status["variables_count"]
        except Exception:
            pass

        # Estimate tokens/cost from Langfuse or approximate from embeddings
        # Each embedding chunk is ~500 tokens on average
        total_tokens = total_chunks * 500
        # Cost estimate: ~$0.0001 per 1K tokens for embedding, ~$0.001 per 1K for LLM
        total_cost = round(total_tokens * 0.0015 / 1000, 4)

        return DashboardResponse(
            success=True,
            data=DashboardData(
                total_documents=total_documents,
                total_chunks=total_chunks,
                total_embeddings=total_embeddings,
                total_cost=total_cost,
                total_tokens=total_tokens,
            ),
        )

    except Exception as e:
        return DashboardResponse(success=False, error=str(e))
