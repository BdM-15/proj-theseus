"""
Structured Data Extractor for Cost Estimators

Converts RAG query responses (markdown) into structured JSON
suitable for Excel export, BOE worksheets, and agent consumption.
"""

import json
import os
from typing import List, Optional
from pydantic import BaseModel, Field
import instructor
from openai import OpenAI


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

class WorkloadDriver(BaseModel):
    """Single workload driver for BOE development."""
    section: str = Field(..., description="Document section/subsection (e.g., F.2.3.1)")
    category: str = Field(..., description="Category: equipment, frequency, quantity, coverage, personnel")
    item: str = Field(..., description="What is being measured/counted")
    value: str = Field(..., description="The numeric or descriptive value")
    unit: Optional[str] = Field(None, description="Unit of measure (e.g., per day, per month, each)")
    condition: Optional[str] = Field(None, description="When/where this applies (e.g., peak hours, special events)")
    responsibility: Optional[str] = Field(None, description="Contractor or Government")


class WorkloadDriverList(BaseModel):
    """List of extracted workload drivers."""
    drivers: List[WorkloadDriver] = Field(..., description="All extracted workload drivers")
    summary: Optional[str] = Field(None, description="Brief summary for estimators")


# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACTION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_structured_workload_drivers(
    markdown_response: str,
    model: str = "grok-3-mini"
) -> WorkloadDriverList:
    """
    Extract structured workload drivers from a markdown RAG response.
    
    Args:
        markdown_response: The markdown text from RAG query
        model: LLM model to use for extraction
        
    Returns:
        WorkloadDriverList with structured data
    """
    # Initialize Instructor-wrapped client
    client = instructor.from_openai(
        OpenAI(
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1"
        ),
        mode=instructor.Mode.JSON
    )
    
    extraction_prompt = """
Extract ALL workload drivers from this document into structured JSON format.

For each workload driver, capture:
- section: The exact section number (e.g., F.2.3.1, 3.2.1)
- category: One of [equipment, frequency, quantity, coverage, personnel, threshold]
- item: What is being measured (e.g., "registers", "cleaning cycles", "staff")
- value: The exact number or value
- unit: Unit of measure if applicable
- condition: Any conditions (e.g., "peak hours", "special events")
- responsibility: "Contractor" or "Government" if specified

IMPORTANT: Extract EVERY quantifiable item. Do not summarize or skip any data.

Document:
"""
    
    result = client.chat.completions.create(
        model=model,
        response_model=WorkloadDriverList,
        messages=[
            {"role": "system", "content": "You are a precise data extractor for government contracting cost estimation."},
            {"role": "user", "content": extraction_prompt + markdown_response}
        ],
        temperature=0.1
    )
    
    return result


def to_excel_rows(drivers: WorkloadDriverList) -> List[dict]:
    """Convert to flat rows suitable for Excel/pandas."""
    return [
        {
            "Section": d.section,
            "Category": d.category,
            "Item": d.item,
            "Value": d.value,
            "Unit": d.unit or "",
            "Condition": d.condition or "",
            "Responsibility": d.responsibility or ""
        }
        for d in drivers.drivers
    ]


def to_json(drivers: WorkloadDriverList) -> str:
    """Convert to JSON string."""
    return drivers.model_dump_json(indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI FOR TESTING
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python structured_extractor.py <markdown_file>")
        sys.exit(1)
    
    # Read markdown file
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        markdown_content = f.read()
    
    print("Extracting structured workload drivers...")
    result = extract_structured_workload_drivers(markdown_content)
    
    print(f"\nExtracted {len(result.drivers)} workload drivers:\n")
    print(to_json(result))
    
    # Optionally export to Excel
    try:
        import pandas as pd
        rows = to_excel_rows(result)
        df = pd.DataFrame(rows)
        output_file = sys.argv[1].replace(".md", "_structured.xlsx")
        df.to_excel(output_file, index=False)
        print(f"\nExported to: {output_file}")
    except ImportError:
        print("\nInstall pandas and openpyxl for Excel export: uv add pandas openpyxl")

