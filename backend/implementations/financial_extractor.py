"""
Financial Data Extractor

Extracts structured financial variables from document markdown using either:
  1. LandingAI Extract API (primary)
  2. OpenAI GPT with structured output (fallback when LandingAI is unavailable)

Both paths produce the same FinancialStatementSchema result and are saved
identically to MongoDB.
"""

import os
import json
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()


def extract_with_openai(markdown_content: str, schema_class) -> Dict:
    """
    Extract financial variables from markdown using OpenAI structured output.

    Uses GPT with response_format=json_schema so the output is guaranteed
    to match FinancialStatementSchema.

    Args:
        markdown_content: Full document markdown text.
        schema_class: Pydantic model class (FinancialStatementSchema).

    Returns:
        Dict of extracted field_name -> value.
    """
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    json_schema = schema_class.model_json_schema()

    system_prompt = """Bạn là chuyên gia phân tích báo cáo tài chính.
Nhiệm vụ của bạn là trích xuất các chỉ số tài chính từ nội dung markdown của báo cáo tài chính.

Quy tắc trích xuất:
- Đọc kỹ toàn bộ nội dung, đặc biệt các bảng số liệu.
- Tất cả các giá trị số phải là số thực (float), không có dấu phẩy hoặc ký tự đơn vị.
- Nếu một chỉ số không tìm thấy, hãy sử dụng 0.0 làm giá trị mặc định.
- Các giá trị tiền tệ thường ở dạng "866.501.980.890" trong báo cáo VN — hãy đọc đúng theo đơn vị được khai báo trong trường don_vi_tien_te.
- EBIT = Lợi nhuận trước thuế + Chi phí lãi vay.
- Tổng nợ phải trả = Nợ ngắn hạn + Nợ dài hạn.
"""

    user_prompt = f"""Trích xuất các chỉ số tài chính từ báo cáo tài chính sau đây.

Nội dung báo cáo:
{markdown_content[:60000]}

Hãy trả về JSON theo đúng schema được yêu cầu."""

    print(f"  Calling OpenAI ({model}) for structured extraction...")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "FinancialStatementSchema",
                "strict": False,
                "schema": json_schema,
            },
        },
        temperature=0,
    )

    raw_json = response.choices[0].message.content
    extracted = json.loads(raw_json)
    return extracted


def extract_financial_data(
    markdown_content: str,
    schema_class,
    landing_ai_parser=None,
) -> Dict:
    """
    Extract financial data using LandingAI first, falling back to OpenAI.

    Args:
        markdown_content: Full document markdown text.
        schema_class: Pydantic model class (FinancialStatementSchema).
        landing_ai_parser: LandingAIParser instance (optional).

    Returns:
        Dict of extracted financial variables.
    """
    # --- Try LandingAI Extract first ---
    if landing_ai_parser is not None:
        try:
            print("  Trying LandingAI Extract...")
            response = landing_ai_parser.extract(markdown_content, schema_class)
            raw = response.extraction

            if hasattr(raw, "model_dump"):
                extracted = raw.model_dump()
            elif isinstance(raw, dict):
                extracted = raw
            elif isinstance(raw, str):
                extracted = json.loads(raw)
            else:
                extracted = dict(raw)

            print("  LandingAI Extract succeeded.")
            return extracted

        except Exception as e:
            err_msg = str(e)
            if "402" in err_msg or "Payment Required" in err_msg:
                print(f"  LandingAI Extract unavailable (402 - insufficient balance).")
                print("  Falling back to OpenAI structured extraction...")
            else:
                print(f"  LandingAI Extract failed: {e}")
                print("  Falling back to OpenAI structured extraction...")

    # --- Fallback: OpenAI structured output ---
    extracted = extract_with_openai(markdown_content, schema_class)
    print("  OpenAI extraction succeeded.")
    return extracted
