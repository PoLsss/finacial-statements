"""Status route for system health checks."""
from fastapi import APIRouter
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.api.schemas.status import StatusResponse, StatusData, ServicesStatus

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get system status and health information.

    Returns database stats and service availability.
    """

    try:
        db_initialized = False
        total_chunks = 0
        total_embeddings = 0
        total_variables = 0

        try:
            from backend.implementations.mongodb_manager import get_mongodb_manager
            mongo = get_mongodb_manager()
            status = mongo.get_status()
            total_chunks = status["chunks_count"]
            total_embeddings = status["embeddings_count"]
            total_variables = status["variables_count"]
            db_initialized = total_embeddings > 0
        except Exception:
            pass

        services = ServicesStatus(
            openai=bool(os.getenv("OPENAI_API_KEY")),
            landing_ai=bool(os.getenv("VISION_AGENT_API_KEY")),
            mongodb=db_initialized,
        )

        return StatusResponse(
            success=True,
            data=StatusData(
                database_initialized=db_initialized,
                total_chunks=total_chunks,
                total_embeddings=total_embeddings,
                total_variables=total_variables,
                embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                llm_model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                services=services,
            )
        )

    except Exception as e:
        return StatusResponse(
            success=False,
            error=str(e)
        )
