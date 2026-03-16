"""Upload route for PDF processing."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pathlib import Path
import shutil
import time
import os
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.api.schemas.upload import UploadResponse, UploadData

router = APIRouter()

UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    reset: bool = Form(False),
):
    """
    Upload and process PDF file through the new pipeline.

    Flow:
      PDF -> LandingAI Parse (split=page) -> Save JSON
          -> Chunks + metadata -> MongoDB
          -> Embeddings (page-level) -> MongoDB
          -> LandingAI Extract -> Financial ratios -> MongoDB
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename.lower().endswith('.pdf'):
        return UploadResponse(
            success=False,
            message="Invalid file type",
            error="Only PDF files are allowed",
            error_code="INVALID_FILE"
        )

    start_time = time.time()
    file_path = None

    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Import pipeline
        from backend.implementations.invest import FinancialReportPipeline

        source_name = Path(file.filename).stem

        # Run pipeline
        pipeline = FinancialReportPipeline()

        stats = pipeline.run(
            pdf_path=str(file_path),
            source_name=source_name,
            parse_json_dir="./parse_results",
            reset=reset,
        )

        processing_time = time.time() - start_time

        return UploadResponse(
            success=True,
            message="PDF processed successfully",
            data=UploadData(
                source_name=source_name,
                total_chunks=stats.get('total_chunks', 0),
                total_embeddings=stats.get('total_embeddings', 0),
                financial_extraction=stats.get('financial_extraction', False),
                extraction_method=stats.get('extraction_method'),
                ratios_computed=stats.get('ratios_computed', False),
                processing_time_seconds=round(processing_time, 2),
            )
        )

    except Exception as e:
        return UploadResponse(
            success=False,
            message="Processing failed",
            error=str(e),
            error_code="PARSE_ERROR"
        )

    finally:
        if file_path and file_path.exists():
            try:
                os.remove(file_path)
            except:
                pass


class DeleteDocumentResponse(BaseModel):
    success: bool
    message: str
    deleted_chunks: int = 0
    deleted_embeddings: int = 0
    deleted_variables: int = 0
    error: str = ""


@router.delete("/documents/{source_name}", response_model=DeleteDocumentResponse)
async def delete_document(source_name: str):
    """
    Delete all data for a given source document.

    Removes:
      - All chunks with matching source
      - All embeddings with matching source
      - All financial variables with matching source
    """
    try:
        from backend.implementations.mongodb_manager import get_mongodb_manager

        mongo = get_mongodb_manager()

        r1 = mongo.chunks_collection.delete_many({"source": source_name})
        r2 = mongo.embeddings_collection.delete_many({"source": source_name})
        r3 = mongo.variables_collection.delete_many({"source": source_name})

        total = r1.deleted_count + r2.deleted_count + r3.deleted_count

        if total == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{source_name}' not found in database"
            )

        return DeleteDocumentResponse(
            success=True,
            message=f"Document '{source_name}' deleted successfully",
            deleted_chunks=r1.deleted_count,
            deleted_embeddings=r2.deleted_count,
            deleted_variables=r3.deleted_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        return DeleteDocumentResponse(
            success=False,
            message="Failed to delete document",
            error=str(e),
        )
