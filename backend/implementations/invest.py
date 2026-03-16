"""
Financial Report Processing Pipeline

New pipeline flow:
  PDF -> LandingAI Parse (split=page) -> Save Parse JSON
      -> Create chunks + metadata -> Store chunks in MongoDB
      -> Generate embeddings (page-level) -> Store embeddings in MongoDB
      -> LandingAI Extract (FinancialStatementSchema) -> Compute ratios
      -> Store results in MongoDB (variables collection)
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent.parent))

from pydantic import BaseModel, Field
from parser.landingai_parse import LandingAIParser
from implementations.embedding_processor import EmbeddingProcessor
from implementations.mongodb_manager import MongoDBManager


# --- Pydantic schema for financial extraction ---

class FinancialStatementSchema(BaseModel):
    Ten_cty: str = Field(
        description="Tên công ty trong báo cáo tài chính",
        title="Tên công ty"
    )
    ky_bao_cao: str = Field(
        description="Kỳ báo cáo tài chính (ví dụ: Quý 3/2025, Năm 2025).",
        title="Kỳ báo cáo"
    )
    don_vi_tien_te: str = Field(
        description="Đơn vị tiền tệ sử dụng trong báo cáo (ví dụ: VND, Triệu VND, tỷ VND).",
        title="Đơn vị tiền tệ"
    )
    tai_san_ngan_han: float = Field(
        description="Tổng tài sản ngắn hạn cuối kỳ. Có mã số: 100",
        title="Tài sản ngắn hạn"
    )
    hang_ton_kho: float = Field(
        description="Tồn kho cuối kỳ hoặc Hàng tồn kho cuối kỳ. Có mã số 140",
        title="Hang ton kho"
    )
    tien: float = Field(
        description="Tiền và các khoảng tương đương tiền cuối kỳ, có mã số 110",
        title="Tiền và tương đương tiền"
    )
    no_ngan_han: float = Field(
        description="Tổng nợ ngắn hạn cuối kỳ, có mã số 310",
        title="Nợ ngắn hạn"
    )
    tong_no_phai_tra: float = Field(
        description="Nợợ phải trả, có mã số 300 ",
        title="Tổng nợ phải trả"
    )
    tong_tai_san: float = Field(
        description="Tổng cộng tài sản cuối kỳ, có mã số 270",
        title="Tổng tài sản cuối kỳ"
    )
    tong_tai_san_dau_ky: float = Field(
        description="Tổng tài sản đầu kỳ, mã số 270",
        title="Tổng tài sản đầu kỳ"
    )
    von_chu_so_huu: float = Field(
        description="Tổng vốn chủ sở hữu cuối kỳ, mã số 400",
        title="Vốn chủ sỡ hữu"
    )
    ebit: float = Field(
        description="Lợi nhuận trước lại và thuế (EBIT), mã số 50",
        title="EBIT"
    )
    chi_phi_lai_vay: float = Field(
        description="Chi phí lãi vay trong kỳ, mã số 23",
        title="Chi phí lãi vay"
    )
    gia_von_hang_ban: float = Field(
        description="giá vốn hàng bán trong kỳ, mã số 11",
        title="giá vốn hàng bán"
    )
    hang_ton_kho_dau_ky: float = Field(
        description="Hàng tồn kho đầu kỳ, mã số 140",
        title="Hàng tồn kho đầu kỳ"
    )
    khoan_phai_thu_ngan_han: float = Field(
        description="khoảng phải thu ngắn hạn cuối kỳ, mã số 130",
        title="Khoản phải thu ngắn hạn"
    )
    khoan_phai_thu_ngan_han_dau_ky: float = Field(
        description="khoảng phải thu ngắn hạn đầu kỳ, mã số 130",
        title="Khoản phải thu ngắn hạn đầu kỳ"
    )
    doanh_thu_thuan: float = Field(
        description="Doanh thu thuần cuối kỳ, mã số 10",
        title="Doanh thu thuần"
    )
    tai_san_co_dinh_rong: float = Field(
        description="Tài sản cố định rồng cuối kỳ, mã số 220",
        title="Tài sản cố định rồng cuối kỳ"
    )
    tai_san_co_dinh_rong_dau_ky: float = Field(
        description="Tài sản cố định rồng đầu kỳ, mã số 220",
        title="Tài sản cố định rồng đầu kỳ"
    )
    loi_nhuan_sau_thue: float = Field(
        description="Lợi nhuận sau thuế cuối kỳ, mã số 60",
        title="Lợi nhuận sau thuế cuối kỳ"
    )
    loi_nhuan_sau_thue_chua_phan_phoi: float =  Field(
        description="Lợi nhuận sau thuế chưa phân phối, mã số 421",
        title="Lợi nhuận sau thuế chưa phân phối"
    )


# --- Financial ratio formulas ---

RATIO_FORMULAS = {
    "A1": "tai_san_ngan_han / no_ngan_han",
    "A2": "(tai_san_ngan_han - hang_ton_kho) / no_ngan_han",
    "A3": "tien / no_ngan_han",
    "B1": "tong_no_phai_tra / tong_tai_san",
    "B2": "tong_no_phai_tra / von_chu_so_huu",
    "B3": "ebit / chi_phi_lai_vay",
    "C1": "gia_von_hang_ban / ((hang_ton_kho_dau_ky + hang_ton_kho) / 2)",
    "C2": "((khoan_phai_thu_ngan_han_dau_ky + khoan_phai_thu_ngan_han) / 2) / doanh_thu_thuan",
    "C3": "doanh_thu_thuan / ((tai_san_co_dinh_rong_dau_ky + tai_san_co_dinh_rong) / 2)",
    "D1": "loi_nhuan_sau_thue / doanh_thu_thuan",
    "D2": "ebit / ((tong_tai_san_dau_ky + tong_tai_san) / 2)",
    "D3": "loi_nhuan_sau_thue / ((tong_tai_san_dau_ky + tong_tai_san) / 2)",
}

# Normal Statistics Fomular
NORMAL_STATISTICS_FORMULAS = {
    "X1": "(tai_san_ngan_han - no_ngan_han) / tong_tai_san",
    "X2": "loi_nhuan_sau_thue_chua_phan_phoi / tong_tai_san",
    "X3": "(ebit + chi_phi_lai_vay) / tong_tai_san",
    "X4": "von_chu_so_huu / tong_no_phai_tra",
    "X5": "doanh_thu_thuan / tong_tai_san",
}

Z_COEFFICIENTS = {
    "X1": 0.717,
    "X2": 0.847,
    "X3": 3.107,
    "X4": 0.420,
    "X5": 0.998,
}


def compute_z_score(variables: Dict) -> Dict:
    """
    Compute Altman Z-Score (modified) from extracted financial variables.

    Z = 0.717*X1 + 0.847*X2 + 3.107*X3 + 0.420*X4 + 0.998*X5

    Returns:
        Dict with 'variables' (X1..X5 each with formula/result/fields),
        'z_value', 'z_formula', and 'classification'.
    """
    x_results = {}
    for x_name, formula in NORMAL_STATISTICS_FORMULAS.items():
        try:
            result = eval(formula, {"__builtins__": {}}, variables)
        except ZeroDivisionError:
            result = None
        except Exception:
            result = None

        # Identify which extracted fields are used in the formula
        var_names = re.findall(r'\b[a-z][a-z_]*\b', formula)
        fields_used = {
            fname: {"value": variables.get(fname)}
            for fname in var_names
            if fname in variables
        }

        x_results[x_name] = {
            "formula": formula,
            "result": result,
            "fields": fields_used,
        }

    # Compute Z — only valid if ALL X values are present
    z_value = None
    try:
        all_present = all(
            x_results.get(x, {}).get("result") is not None
            for x in Z_COEFFICIENTS
        )
        if all_present:
            z_value = sum(
                Z_COEFFICIENTS[x] * x_results[x]["result"]
                for x in Z_COEFFICIENTS
            )
    except Exception:
        z_value = None

    # Classify
    if z_value is not None:
        if z_value > 2.99:
            classification = "safe"
        elif z_value > 1.81:
            classification = "grey"
        else:
            classification = "danger"
    else:
        classification = "unknown"

    return {
        "variables": x_results,
        "z_value": z_value,
        "z_formula": "0.717×X1 + 0.847×X2 + 3.107×X3 + 0.420×X4 + 0.998×X5",
        "classification": classification,
    }


def compute_financial_ratios(variables: Dict) -> Dict:
    """
    Compute financial ratios from extracted variables.

    Args:
        variables: Dict of extracted financial variables (field_name -> value)

    Returns:
        Dict of ratio_name -> {formula, result}
    """
    results = {}
    for ratio_name, formula in RATIO_FORMULAS.items():
        try:
            result = eval(formula, {"__builtins__": {}}, variables)
            results[ratio_name] = {
                "formula": formula,
                "result": result,
            }
        except ZeroDivisionError:
            results[ratio_name] = {
                "formula": formula,
                "result": None,
                "error": "Division by zero",
            }
        except Exception as e:
            results[ratio_name] = {
                "formula": formula,
                "result": None,
                "error": str(e),
            }
    return results


def extract_with_openai(markdown_content: str, api_key: Optional[str] = None) -> Dict:
    """
    Extract structured financial data from markdown using OpenAI structured output.

    Uses GPT-4o-mini with Pydantic response_format so the output is
    automatically validated against FinancialStatementSchema.

    Args:
        markdown_content: Full document markdown text.
        api_key: Optional OpenAI API key (falls back to OPENAI_API_KEY env var).

    Returns:
        Dict of extracted financial variables matching FinancialStatementSchema fields.
    """
    from openai import OpenAI as _OpenAI

    client = _OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    system_prompt = (
        "You are a financial data extractor. "
        "Read the Vietnamese financial report and extract the required fields. "
        "Return all monetary values as plain floats (no commas, no currency symbols, no spaces). "
        "If a value cannot be found, return 0.0 for numeric fields."
    )

    # Limit content to avoid exceeding context window; 120 000 chars ≈ 30 000 tokens
    content = markdown_content[:120_000]

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    print(f"    Using OpenAI structured output ({model}) …")

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        response_format=FinancialStatementSchema,
    )

    parsed: FinancialStatementSchema = completion.choices[0].message.parsed
    return parsed.model_dump()


class FinancialReportPipeline:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        embedding_model: Optional[str] = None,
        landing_ai_api_key: Optional[str] = None,
    ):
        print("\n" + "=" * 70)
        print("FINANCIAL REPORT PROCESSING PIPELINE (MongoDB)")
        print("=" * 70 + "\n")

        self.embedding_model = embedding_model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        # Initialize components
        self.landing_parser = LandingAIParser(api_key=landing_ai_api_key)
        self.embedding_processor = EmbeddingProcessor(
            api_key=openai_api_key,
            model=self.embedding_model,
        )
        self.mongo = MongoDBManager()

        print("Pipeline initialized successfully\n")

    def run(
        self,
        pdf_path: str,
        source_name: Optional[str] = None,
        parse_json_dir: str = "./parse_results",
        reset: bool = False,
        embedding_batch_size: int = 50,
        embedding_delay: float = 0.1,
    ) -> Dict:
        """
        Run the complete pipeline from a PDF file.

        If a cached parse JSON exists in parse_json_dir, it will be used
        instead of calling the LandingAI parse API again.

        Flow:
          1. Parse PDF with LandingAI (split=page) -> save JSON
          2. Create chunks + metadata from structured parse result
          3. Store chunks in MongoDB
          4. Generate page-level embeddings
          5. Store embeddings in MongoDB
          6. Extract financial data with LandingAI Extract
          7. Compute financial ratios
          8. Store results in MongoDB variables collection

        Returns:
            Dictionary with processing statistics
        """
        pdf_path = Path(pdf_path)
        if source_name is None:
            source_name = pdf_path.stem

        stats = {
            "source_name": source_name,
            "total_chunks": 0,
            "total_embeddings": 0,
            "financial_extraction": False,
            "extraction_method": None,
            "ratios_computed": False,
        }

        # STEP 1: Parse PDF with LandingAI (split=page)
        print("\n" + "=" * 70)
        print("STEP 1: PARSE PDF with LandingAI (split=page)")
        print("=" * 70)

        parse_json_dir = Path(parse_json_dir)
        parse_json_dir.mkdir(parents=True, exist_ok=True)
        parse_json_path = parse_json_dir / f"parse_{source_name}.json"

        # Check for cached parse result
        if parse_json_path.exists():
            print(f"Loading cached parse result from: {parse_json_path}")
            with open(parse_json_path, "r", encoding="utf-8") as f:
                parse_data = json.load(f)
        else:
            parse_response = self.landing_parser.parse(pdf_path)
            parse_data = parse_response.model_dump()
            with open(parse_json_path, "w", encoding="utf-8") as f:
                json.dump(parse_data, f, indent=2, default=str)
            print(f"Saved parse JSON to: {parse_json_path}")

        # STEP 2: Create chunks + metadata from the structured parse output
        print("\n" + "=" * 70)
        print("STEP 2: CREATE CHUNKS + METADATA")
        print("=" * 70)

        chunks = self._create_chunks_from_parse(parse_data, source_name)
        stats["total_chunks"] = len(chunks)
        print(f"Created {len(chunks)} chunks")

        if not chunks:
            print("No chunks created. Exiting.")
            return stats

        # STEP 3: Store chunks in MongoDB
        print("\n" + "=" * 70)
        print("STEP 3: STORE CHUNKS IN MONGODB")
        print("=" * 70)

        self.mongo.store_chunks(chunks, source_name, reset=reset)

        # STEP 4: Generate page-level embeddings
        print("\n" + "=" * 70)
        print("STEP 4: GENERATE PAGE-LEVEL EMBEDDINGS")
        print("=" * 70)

        embeddings_data = self._generate_page_embeddings(
            chunks, source_name, embedding_batch_size, embedding_delay
        )
        stats["total_embeddings"] = len(embeddings_data)

        # STEP 5: Store embeddings in MongoDB
        print("\n" + "=" * 70)
        print("STEP 5: STORE EMBEDDINGS IN MONGODB")
        print("=" * 70)

        self.mongo.store_embeddings(embeddings_data, source_name, reset=reset)

        # STEP 6: Extract financial data with LandingAI Extract
        print("\n" + "=" * 70)
        print("STEP 6: EXTRACT FINANCIAL DATA (LandingAI Extract)")
        print("=" * 70)

        try:
            # Combine all page markdown for extraction
            all_markdown = "\n\n".join(chunk["text"] for chunk in chunks)

            # ── Primary: LandingAI Extract ────────────────────────────────
            extracted_vars: Optional[Dict] = None
            extraction_method = "unknown"
            # Each entry: {value, page, location, chunk_type}  or  {value, error}
            extracted_fields: Dict = {}

            try:
                print("    Trying LandingAI Extract …")
                extracted_response = self.landing_parser.extract(
                    all_markdown, FinancialStatementSchema
                )
                raw = extracted_response.extraction
                if hasattr(raw, "model_dump"):
                    extracted_vars = raw.model_dump()
                elif isinstance(raw, dict):
                    extracted_vars = raw
                elif isinstance(raw, str):
                    extracted_vars = json.loads(raw)
                else:
                    extracted_vars = dict(raw)
                extraction_method = "landingai"
                print("    LandingAI extraction succeeded.")

                # Build extracted_fields: each field gets value + grounding metadata.
                # grounding_map comes from the JSON cache so values are plain dicts.
                grounding_map = parse_data.get("grounding", {})
                raw_extract_meta = getattr(extracted_response, "extraction_metadata", None) or {}
                if hasattr(raw_extract_meta, "model_dump"):
                    extract_meta = raw_extract_meta.model_dump()
                elif isinstance(raw_extract_meta, dict):
                    extract_meta = raw_extract_meta
                else:
                    extract_meta = {}

                for field_name, field_value in extracted_vars.items():
                    try:
                        field_meta = extract_meta[field_name]
                        refs = (
                            field_meta.get("references")
                            if isinstance(field_meta, dict)
                            else getattr(field_meta, "references", [])
                        ) or []
                        chunk_id = refs[0]
                        ground = grounding_map[chunk_id]  # plain dict from JSON
                        box = ground.get("box") or {}
                        extracted_fields[field_name] = {
                            "value": field_value,
                            "page": ground.get("page"),
                            "location": {
                                "left":   box.get("left"),
                                "top":    box.get("top"),
                                "right":  box.get("right"),
                                "bottom": box.get("bottom"),
                            },
                            "chunk_type": ground.get("type"),
                        }
                    except Exception as meta_err:
                        extracted_fields[field_name] = {
                            "value": field_value,
                            "error": str(meta_err),
                        }

                found = sum(1 for v in extracted_fields.values() if "page" in v)
                print(f"    Grounding metadata: {found}/{len(extracted_fields)} fields located.")

            except Exception as landingai_err:
                print(f"    LandingAI failed ({landingai_err})")
                print("    Falling back to OpenAI structured output …")
                extracted_vars = extract_with_openai(
                    all_markdown, api_key=os.getenv("OPENAI_API_KEY")
                )
                extraction_method = "openai"
                # No grounding metadata via OpenAI — store value only
                extracted_fields = {
                    field_name: {"value": field_value}
                    for field_name, field_value in extracted_vars.items()
                }
                print("    OpenAI extraction succeeded.")

            stats["financial_extraction"] = True
            stats["extraction_method"] = extraction_method
            print(f"\n    Company : {extracted_vars.get('Ten_cty', 'N/A')}")
            print(f"    Period  : {extracted_vars.get('ky_bao_cao', 'N/A')}")
            print(f"    Currency: {extracted_vars.get('don_vi_tien_te', 'N/A')}")
            print("\n    Extracted variables:")
            for key, val in extracted_vars.items():
                print(f"      {key}: {val}")

            # STEP 7: Compute financial ratios
            print("\n" + "=" * 70)
            print("STEP 7: COMPUTE FINANCIAL RATIOS")
            print("=" * 70)

            ratios = compute_financial_ratios(extracted_vars)

            # Build ratios_with_metadata: formula + result + per-field entries from extracted_fields
            ratios_with_metadata: Dict = {}
            for ratio_name, ratio_info in ratios.items():
                var_names = re.findall(r'\b[a-z][a-z_]*\b', ratio_info["formula"])
                fields_used = {
                    fname: extracted_fields.get(fname, {"value": extracted_vars.get(fname)})
                    for fname in var_names
                    if fname in extracted_vars
                }
                ratio_entry: Dict = {
                    "formula": ratio_info["formula"],
                    "result": ratio_info.get("result"),
                    "fields": fields_used,
                }
                if ratio_info.get("error"):
                    ratio_entry["error"] = ratio_info["error"]
                ratios_with_metadata[ratio_name] = ratio_entry

            stats["ratios_computed"] = True

            print("Computed ratios:")
            for name, info in ratios_with_metadata.items():
                result = info.get("result")
                if result is not None:
                    print(f"  {name}: {result:.6f}")
                else:
                    print(f"  {name}: ERROR - {info.get('error', 'N/A')}")

            # ── Compute Z-Score ──
            z_score_data = compute_z_score(extracted_vars)

            # Enrich Z-score fields with grounding metadata from extracted_fields
            for x_name, x_info in z_score_data.get("variables", {}).items():
                for fname in list(x_info.get("fields", {}).keys()):
                    if fname in extracted_fields:
                        x_info["fields"][fname] = extracted_fields[fname]

            if z_score_data.get("z_value") is not None:
                print(f"\n  Z-Score: {z_score_data['z_value']:.6f}")
                print(f"  Classification: {z_score_data['classification']}")
            else:
                print("\n  Z-Score: Could not compute (missing variables)")

            # STEP 8: Store results in MongoDB
            print("\n" + "=" * 70)
            print("STEP 8: STORE FINANCIAL DATA IN MONGODB")
            print("=" * 70)

            self.mongo.store_financial_data(
                source_name=source_name,
                company=extracted_vars.get("Ten_cty", "Unknown"),
                period=extracted_vars.get("ky_bao_cao", "Unknown"),
                currency=extracted_vars.get("don_vi_tien_te", "VND"),
                extracted_fields=extracted_fields,
                calculated_ratios=ratios_with_metadata,
                extraction_method=extraction_method,
                z_score=z_score_data,
                reset=reset,
            )

        except Exception as e:
            print(f"Warning: Financial extraction failed: {e}")
            print("Continuing without financial extraction...")
            import traceback
            traceback.print_exc()

        # Print summary
        self._print_summary(stats)

        return stats

    def _create_chunks_from_parse(
        self, parse_data: Dict, source_name: str
    ) -> List[Dict]:
        """
        Create page-level chunks from the structured LandingAI parse response.

        When split="page", the response contains:
          - splits: list of page-level objects, each with full page markdown
          - chunks: list of element-level objects (sub-page elements)

        We use `splits` so that each page becomes exactly ONE chunk with
        all elements in that page merged together.
        """
        chunks = []
        chunk_index = 0

        # Use splits (page-level) — each split = 1 page with merged markdown
        pages = parse_data.get("splits", [])

        if not pages:
            # Fallback: if no splits, try full markdown as single chunk
            markdown = parse_data.get("markdown", "")
            if markdown:
                chunks.append({
                    "text": markdown,
                    "metadata": {
                        "source": source_name,
                        "page_number": 1,
                        "chunk_id": f"{source_name}_page_0",
                        "chunk_index": 0,
                        "text_position": 0,
                        "text_length": len(markdown),
                    },
                })
            return chunks

        # Build a lookup of element-level chunks for grounding metadata
        element_chunks = {c["id"]: c for c in parse_data.get("chunks", [])}

        for page in pages:
            page_text = page.get("markdown", "")
            if not page_text or not page_text.strip():
                continue

            # page["pages"] is a list like [0], [1], etc. (0-indexed)
            page_numbers = page.get("pages", [chunk_index])
            page_number = page_numbers[0] + 1 if page_numbers else chunk_index + 1
            page_identifier = page.get("identifier", f"page_{chunk_index}")

            chunk_id = f"{source_name}_page_{page_number}"

            # Count element types in this page using the element chunk IDs
            element_ids = page.get("chunks", [])
            element_types = {}
            for eid in element_ids:
                el = element_chunks.get(eid, {})
                etype = el.get("type", "unknown")
                element_types[etype] = element_types.get(etype, 0) + 1

            chunk = {
                "text": page_text.strip(),
                "metadata": {
                    "source": source_name,
                    "page_number": page_number,
                    "chunk_id": chunk_id,
                    "chunk_index": chunk_index,
                    "page_identifier": page_identifier,
                    "text_position": 0,
                    "text_length": len(page_text.strip()),
                    "elements_count": len(element_ids),
                    "element_types": element_types,
                },
            }

            chunks.append(chunk)
            chunk_index += 1

        return chunks

    def _generate_page_embeddings(
        self,
        chunks: List[Dict],
        source_name: str,
        batch_size: int = 50,
        delay: float = 0.1,
    ) -> List[Dict]:
        """
        Generate embeddings at the page level and prepare for MongoDB storage.
        """
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_processor.create_embeddings_batch(
            texts, batch_size=batch_size, delay=delay
        )

        embeddings_data = []
        for chunk, embedding in zip(chunks, embeddings):
            embeddings_data.append({
                "chunk_id": chunk["metadata"]["chunk_id"],
                "page_number": chunk["metadata"]["page_number"],
                "embedding": embedding,
                "text": chunk["text"],
                "metadata": chunk["metadata"],
            })

        return embeddings_data

    def _print_summary(self, stats: Dict):
        print("\n" + "=" * 70)
        print("PIPELINE SUMMARY")
        print("=" * 70)
        print(f"Source:                {stats['source_name']}")
        print(f"Total chunks:          {stats['total_chunks']}")
        print(f"Total embeddings:      {stats['total_embeddings']}")
        print(f"Financial extraction:  {'Yes' if stats['financial_extraction'] else 'No'}"
              + (f"  (via {stats['extraction_method']})" if stats.get('extraction_method') else ""))
        print(f"Ratios computed:       {'Yes' if stats['ratios_computed'] else 'No'}")

        # Print MongoDB status
        db_status = self.mongo.get_status()
        print(f"\nMongoDB Status:")
        print(f"  Chunks:     {db_status['chunks_count']}")
        print(f"  Embeddings: {db_status['embeddings_count']}")
        print(f"  Variables:  {db_status['variables_count']}")
        print("=" * 70 + "\n")


def main():
    """Run pipeline from CLI."""
    import argparse

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    if not OPENAI_API_KEY:
        print("Warning: OPENAI_API_KEY not found in environment variables.")
        return 1

    parser = argparse.ArgumentParser(
        description="Financial Report Processing Pipeline (MongoDB)",
    )
    parser.add_argument("pdf_file", help="Path to PDF file to process")
    parser.add_argument(
        "--reset", action="store_true", help="Reset existing data for this source"
    )
    parser.add_argument(
        "--batch-size", type=int, default=50, help="Embedding batch size (default: 50)"
    )
    parser.add_argument(
        "--delay", type=float, default=0.1, help="Delay between batches (default: 0.1)"
    )
    parser.add_argument(
        "--parse-json-dir",
        default="./parse_results",
        help="Directory to save parse JSON (default: ./parse_results)",
    )

    args = parser.parse_args()

    input_path = Path(args.pdf_file)
    if not input_path.exists():
        print(f"Error: File not found: {args.pdf_file}")
        return 1

    if not input_path.suffix.lower() == ".pdf":
        print(f"Error: File must be a PDF: {args.pdf_file}")
        return 1

    pipeline = FinancialReportPipeline(openai_api_key=OPENAI_API_KEY)

    stats = pipeline.run(
        pdf_path=str(input_path),
        parse_json_dir=args.parse_json_dir,
        reset=args.reset,
        embedding_batch_size=args.batch_size,
        embedding_delay=args.delay,
    )

    return 0


if __name__ == "__main__":
    main()
