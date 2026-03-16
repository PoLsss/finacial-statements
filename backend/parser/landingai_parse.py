"""
Landing AI PDF Parser Module

Provides a class-based interface to parse PDFs using the Landing AI ADE SDK.
Supports page-level splitting and structured JSON output.
"""

import os
import json
import certifi
from pathlib import Path
from typing import Optional, Union
from dotenv import load_dotenv

# Configure SSL certificates
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Load environment variables
load_dotenv()

from landingai_ade import LandingAIADE


class LandingAIParser:
    """
    Parser for PDF documents using Landing AI ADE SDK.

    Attributes:
        client: LandingAIADE client instance
        model: Model to use for parsing (default: "dpt-2-latest")
        api_key: API key from environment or provided directly
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "dpt-2-latest"):
        self.model = model
        self.api_key = api_key or os.getenv("VISION_AGENT_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key not provided. Set VISION_AGENT_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = LandingAIADE(apikey=self.api_key)

    def parse(self, pdf_path: Union[str, Path]):
        """
        Parse a PDF document with page-level splitting.

        Args:
            pdf_path: Path to the PDF file to parse.

        Returns:
            ParseResponse object from LandingAI (structured, page-level).

        Raises:
            FileNotFoundError: If PDF file does not exist.
            Exception: If parsing fails.
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        print(f"Parsing PDF with page-level split: {pdf_path}")

        try:
            parse_response = self.client.parse(
                document=pdf_path,
                model=self.model,
                split="page",
            )
            print(f"Successfully parsed: {pdf_path}")
            return parse_response
        except Exception as e:
            print(f"Error parsing {pdf_path}: {e}")
            raise

    def parse_and_save_json(
        self,
        pdf_path: Union[str, Path],
        output_dir: Union[str, Path] = "parse_results",
    ) -> Path:
        """
        Parse a PDF and save the structured response as JSON.

        Args:
            pdf_path: Path to the PDF file to parse.
            output_dir: Directory to save the JSON output.

        Returns:
            Path to the saved JSON file.
        """
        pdf_path = Path(pdf_path)
        filename = pdf_path.stem

        response = self.parse(pdf_path)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"parse_{filename}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response.model_dump(), f, indent=2, default=str)

        print(f"Saved parse result to: {output_file}")
        return output_file

    def extract(self, markdown_content: str, schema_class):
        """
        Extract structured data from markdown using LandingAI Extract mode.

        The LandingAI extract API takes:
          - markdown: The markdown content (string) to extract from
          - schema: A JSON schema string defining what to extract
          - model: Optional model version (e.g., "extract-latest")

        Args:
            markdown_content: Markdown text (from a previous parse call).
            schema_class: Pydantic model class defining the extraction schema.

        Returns:
            ExtractResponse from LandingAI.
        """
        print(f"Extracting structured data using LandingAI Extract...")

        try:
            # Convert Pydantic model to JSON schema string
            json_schema = json.dumps(schema_class.model_json_schema())

            result = self.client.extract(
                markdown=markdown_content,
                schema=json_schema,
                model="extract-latest",
            )
            print(f"Successfully extracted structured data")
            return result
        except Exception as e:
            print(f"Error extracting data: {e}")
            raise


# Main execution for testing
if __name__ == "__main__":
    try:
        parser = LandingAIParser()

        pdf_file = Path("./data/HPG_Baocaotaichinh_Q3_2025_Congtyme_01112025110845.pdf")
        response = parser.parse(pdf_file)

        print(f"\nParse response type: {type(response)}")
        print(f"Response dump (first 500 chars): {str(response.model_dump())[:500]}")

    except FileNotFoundError as e:
        print(f"File error: {e}")
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Parsing error: {e}")
