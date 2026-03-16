"""Statistics routes for financial data analysis and PDF visualization."""
from fastapi import APIRouter
from fastapi.responses import Response
from pathlib import Path
import os
import sys
import json
import io

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.api.schemas.statistics import (
    CompaniesResponse,
    CompanyInfo,
    FinancialDataResponse,
    ExplainRequest,
    ExplainResponse,
    PageContentResponse,
)

router = APIRouter()

# Directory where PDF files are stored for visualization
PDF_DIR = Path(__file__).parent.parent.parent / "data_for_visualization"
PARSE_RESULTS_DIR = Path(__file__).parent.parent.parent.parent / "parse_results"


def _find_pdf_for_source(source: str) -> Path | None:
    """Find the PDF file matching a source name."""
    if not PDF_DIR.exists():
        return None
    # Try exact match with .pdf
    pdf_path = PDF_DIR / f"{source}.pdf"
    if pdf_path.exists():
        return pdf_path
    # Try case-insensitive search
    for f in PDF_DIR.iterdir():
        if f.suffix.lower() == ".pdf" and f.stem.lower() == source.lower():
            return f
    return None


def _find_parse_results(source: str) -> dict | None:
    """Find and load parse results JSON for a source."""
    if not PARSE_RESULTS_DIR.exists():
        return None
    for f in PARSE_RESULTS_DIR.iterdir():
        if f.suffix == ".json" and source in f.stem:
            with open(f, "r", encoding="utf-8") as fh:
                return json.load(fh)
    return None


@router.get("/statistics/companies", response_model=CompaniesResponse)
async def get_companies():
    """Get list of all companies with financial data in MongoDB."""
    try:
        from backend.implementations.mongodb_manager import get_mongodb_manager

        mongo = get_mongodb_manager()
        docs = mongo.get_financial_data()

        companies = []
        for doc in docs:
            companies.append(
                CompanyInfo(
                    source=doc.get("source", ""),
                    company=doc.get("company", ""),
                    period=doc.get("period", ""),
                    currency=doc.get("currency", "VND"),
                )
            )

        return CompaniesResponse(success=True, data=companies)

    except Exception as e:
        return CompaniesResponse(success=False, error=str(e))


@router.get("/statistics/industry-averages")
async def get_industry_averages():
    """Get the average of calculated ratios across all companies."""
    try:
        from backend.implementations.mongodb_manager import get_mongodb_manager

        mongo = get_mongodb_manager()
        docs = mongo.get_financial_data()
        
        sums = {}
        counts = {}
        for doc in docs:
            ratios = doc.get("calculated_ratios", {})
            for ratio_key, ratio_data in ratios.items():
                if not isinstance(ratio_data, dict):
                    continue
                result = ratio_data.get("result")
                if result is not None and isinstance(result, (int, float)):
                    sums[ratio_key] = sums.get(ratio_key, 0) + result
                    counts[ratio_key] = counts.get(ratio_key, 0) + 1
                    
        averages = {k: sums[k] / counts[k] for k in sums if counts[k] > 0}
        return {"success": True, "data": averages}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/statistics/financial-data/{source}", response_model=FinancialDataResponse)
async def get_financial_data(source: str):
    """Get financial data (extracted fields + calculated ratios) for a company."""
    try:
        from backend.implementations.mongodb_manager import get_mongodb_manager

        mongo = get_mongodb_manager()
        docs = mongo.get_financial_data(source_name=source)

        if not docs:
            return FinancialDataResponse(
                success=False, error=f"No data found for source: {source}"
            )

        doc = docs[0]

        # Build extracted_fields from extracted_variables + fields_metadata
        extracted_variables = doc.get("extracted_variables", {})
        fields_metadata = doc.get("fields_metadata", {})

        extracted_fields = {}
        for field_name, value in extracted_variables.items():
            meta = fields_metadata.get(field_name, {})
            extracted_fields[field_name] = {
                "value": value,
                "page": meta.get("page"),
                "location": meta.get("location"),
                "chunk_type": meta.get("chunk_type"),
                "chunk_id": meta.get("chunk_id"),
            }

        # Enrich calculated_ratios fields with metadata
        calculated_ratios = doc.get("calculated_ratios", {})
        for ratio_key, ratio_data in calculated_ratios.items():
            fields = ratio_data.get("fields", {})
            for field_name, field_info in fields.items():
                if field_name in fields_metadata:
                    meta = fields_metadata[field_name]
                    field_info["page"] = meta.get("page")
                    field_info["location"] = meta.get("location")
                    field_info["chunk_type"] = meta.get("chunk_type")
                    field_info["chunk_id"] = meta.get("chunk_id")

        # Enrich z_score variable fields with metadata
        # If z_score is missing (old documents), compute on the fly
        z_score = doc.get("z_score")
        if not z_score:
            # Build plain-value dict for compute_z_score
            plain_vars = dict(extracted_variables) if extracted_variables else {}
            # Also try to pull values from extracted_fields (which has {value, page, ...})
            if not plain_vars:
                for fname, finfo in (doc.get("extracted_fields") or {}).items():
                    if isinstance(finfo, dict) and "value" in finfo:
                        v = finfo["value"]
                        if isinstance(v, (int, float)):
                            plain_vars[fname] = v
                        elif isinstance(v, str):
                            try:
                                plain_vars[fname] = float(v.replace(",", ""))
                            except (ValueError, TypeError):
                                pass
                    elif isinstance(finfo, (int, float)):
                        plain_vars[fname] = finfo
            if plain_vars:
                from backend.implementations.invest import compute_z_score
                z_score = compute_z_score(plain_vars)

        if z_score and isinstance(z_score, dict):
            for x_name, x_info in z_score.get("variables", {}).items():
                for field_name, field_info in x_info.get("fields", {}).items():
                    if field_name in fields_metadata:
                        meta = fields_metadata[field_name]
                        field_info["page"] = meta.get("page")
                        field_info["location"] = meta.get("location")
                        field_info["chunk_type"] = meta.get("chunk_type")
                        field_info["chunk_id"] = meta.get("chunk_id")
                    elif field_name in extracted_fields:
                        ef = extracted_fields[field_name]
                        field_info["page"] = ef.get("page")
                        field_info["location"] = ef.get("location")
                        field_info["chunk_type"] = ef.get("chunk_type")
                        field_info["chunk_id"] = ef.get("chunk_id")

        return FinancialDataResponse(
            success=True,
            data={
                "source": doc.get("source", ""),
                "company": doc.get("company", ""),
                "period": doc.get("period", ""),
                "currency": doc.get("currency", "VND"),
                "extraction_method": doc.get("extraction_method", ""),
                "extracted_fields": extracted_fields,
                "calculated_ratios": calculated_ratios,
                "z_score": z_score,
            },
        )

    except Exception as e:
        return FinancialDataResponse(success=False, error=str(e))


@router.get("/statistics/pdf-page/{source}/{page_number}")
async def get_pdf_page_image(source: str, page_number: int, dpi: int = 150):
    """Render a PDF page as a PNG image."""
    import pymupdf

    pdf_path = _find_pdf_for_source(source)
    if not pdf_path:
        return Response(content=b"PDF not found", status_code=404)

    try:
        pdf = pymupdf.open(str(pdf_path))
        if page_number < 0 or page_number >= len(pdf):
            pdf.close()
            return Response(content=b"Page not found", status_code=404)

        page = pdf[page_number]
        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")
        pdf.close()

        return Response(content=img_bytes, media_type="image/png")
    except Exception as e:
        return Response(content=str(e).encode(), status_code=500)


@router.get("/statistics/pdf-page-highlight/{source}/{page_number}")
async def get_pdf_page_with_highlight(
    source: str,
    page_number: int,
    left: float = 0,
    top: float = 0,
    right: float = 0,
    bottom: float = 0,
    dpi: int = 150,
):
    """Render a PDF page as PNG with a highlighted bounding box region."""
    import pymupdf

    pdf_path = _find_pdf_for_source(source)
    if not pdf_path:
        return Response(content=b"PDF not found", status_code=404)

    try:
        pdf = pymupdf.open(str(pdf_path))
        if page_number < 0 or page_number >= len(pdf):
            pdf.close()
            return Response(content=b"Page not found", status_code=404)

        page = pdf[page_number]
        rect = page.rect

        # Convert normalized 0-1 coords to PDF page coords
        x0 = rect.x0 + left * rect.width
        y0 = rect.y0 + top * rect.height
        x1 = rect.x0 + right * rect.width
        y1 = rect.y0 + bottom * rect.height

        # Draw highlight rectangle
        highlight_rect = pymupdf.Rect(x0, y0, x1, y1)
        shape = page.new_shape()
        shape.draw_rect(highlight_rect)
        shape.finish(color=(1, 0, 0), fill=(1, 0, 0), fill_opacity=0.15, width=2)
        shape.commit()

        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")
        pdf.close()

        return Response(content=img_bytes, media_type="image/png")
    except Exception as e:
        return Response(content=str(e).encode(), status_code=500)


@router.get("/statistics/pdf-info/{source}")
async def get_pdf_info(source: str):
    """Get PDF page count and basic info."""
    import pymupdf

    pdf_path = _find_pdf_for_source(source)
    if not pdf_path:
        return {"success": False, "error": "PDF not found"}

    try:
        pdf = pymupdf.open(str(pdf_path))
        page_count = len(pdf)
        pdf.close()
        return {"success": True, "page_count": page_count, "source": source}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/statistics/page-content/{source}/{page_number}", response_model=PageContentResponse)
async def get_page_content(source: str, page_number: int):
    """Get the text content for a specific page of a document."""
    try:
        from backend.implementations.mongodb_manager import get_mongodb_manager

        mongo = get_mongodb_manager()
        chunks = mongo.get_chunks_by_source(source)

        for chunk in chunks:
            if chunk.get("page_number") == page_number:
                return PageContentResponse(
                    success=True,
                    page_text=chunk.get("text", ""),
                    page_number=page_number,
                )

        return PageContentResponse(
            success=False, error=f"Page {page_number} not found for source: {source}"
        )

    except Exception as e:
        return PageContentResponse(success=False, error=str(e))


@router.post("/statistics/explain", response_model=ExplainResponse)
async def explain_ratios(request: ExplainRequest):
    """Generate LLM explanation and recommendations for a group of financial ratios."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        ratios_text = ""
        for key, val in request.ratios.items():
            result = val.get("result", "N/A")
            threshold = request.thresholds.get(key, {})
            threshold_val = threshold.get("value", "N/A")
            status = "Good" if result is not None and threshold_val != "N/A" and result >= threshold_val else "Risk"
            ratios_text += f"  - {key}: value={result}, threshold={threshold_val}, status={status}\n"

        prompt = f"""Bạn là chuyên gia phân tích tài chính. Hãy phân tích nhóm chỉ số tài chính sau:

Nhóm: {request.group_name} ({request.group_label})

Các chỉ số:
{ratios_text}

Hãy:
1. Giải thích mức độ rủi ro tổng thể của nhóm chỉ số này
2. Đưa ra nhận xét chi tiết cho từng chỉ số
3. Đề xuất các hành động hoặc khuyến nghị cải thiện

Trả lời bằng tiếng Việt, ngắn gọn và chuyên nghiệp."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia phân tích tài chính doanh nghiệp Việt Nam."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )

        content = response.choices[0].message.content or ""

        parts = content.split("Khuyến nghị", 1)
        explanation = parts[0].strip()
        recommendations = parts[1].strip() if len(parts) > 1 else ""

        if not recommendations:
            parts = content.split("Đề xuất", 1)
            explanation = parts[0].strip()
            recommendations = parts[1].strip() if len(parts) > 1 else ""

        return ExplainResponse(
            success=True,
            explanation=explanation or content,
            recommendations=recommendations,
        )

    except Exception as e:
        return ExplainResponse(success=False, error=str(e))
