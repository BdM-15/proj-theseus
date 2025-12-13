"""
Simplified Table Entity Extractor

Uses a MINIMAL schema to avoid xAI API truncation issues.
Tables are processed with a simpler prompt that generates smaller JSON responses.

Design Principle:
- xAI API truncates large JSON responses (>10KB unpredictably)
- Tables often have many rows → many entities → huge JSON
- Solution: Extract table-level metadata + preserve raw content for later

This extractor captures:
1. Table-level metadata (what IS this table about?)
2. Key metrics/quantities (numbers that matter for BOE)
3. Raw table content stored verbatim for retrieval
"""

import os
import logging
import asyncio
from typing import Optional, List
from pydantic import BaseModel, Field

import instructor

logger = logging.getLogger(__name__)


class TableMetric(BaseModel):
    """Single metric extracted from a table - minimal fields to reduce JSON size."""
    name: str = Field(description="Short name for the metric (e.g., 'Daily Meals', 'Response Time')")
    value: str = Field(description="The value with units (e.g., '500 meals/day', '15 minutes')")
    context: str = Field(default="", description="Brief context if needed (max 50 chars)")


class TableSummary(BaseModel):
    """Minimal table extraction result - designed to be small JSON."""
    table_type: str = Field(description="What kind of table: 'metrics', 'schedule', 'requirements', 'pricing', 'personnel', 'equipment', 'evaluation', 'other'")
    table_topic: str = Field(description="One-line description of what this table contains (max 100 chars)")
    key_metrics: List[TableMetric] = Field(default_factory=list, description="Up to 5 most important quantifiable values from the table")
    
    class Config:
        # Limit string sizes to prevent huge responses
        str_max_length = 200


class TableExtractor:
    """
    Simplified extractor for tables that produces minimal JSON output.
    
    Designed to avoid xAI API truncation by:
    1. Using a tiny schema (TableSummary vs full ExtractionResult)
    2. Limiting to 5 key metrics max
    3. Short field lengths
    """
    
    def __init__(self):
        self.api_key = os.getenv("LLM_BINDING_API_KEY") or os.getenv("XAI_API_KEY")
        self.model = os.getenv("EXTRACTION_LLM_NAME", "grok-4-1-fast-non-reasoning")
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "5"))
        
        if not self.api_key:
            raise ValueError("LLM_BINDING_API_KEY or XAI_API_KEY required")
        
        os.environ["XAI_API_KEY"] = self.api_key
        
        self.client = instructor.from_provider(
            f"xai/{self.model}",
            async_client=True
        )
        
        # Track stats
        self.successful = 0
        self.failed = 0
        
        logger.info(f"TableExtractor initialized (minimal schema for truncation resilience)")
    
    async def extract(self, table_html: str, caption: str = "", chunk_id: str = "table") -> TableSummary:
        """
        Extract minimal metadata from a table.
        
        Args:
            table_html: HTML table content from MinerU
            caption: Table caption if available
            chunk_id: Identifier for logging
        
        Returns:
            TableSummary with table_type, topic, and up to 5 key metrics
        """
        # Truncate huge tables to prevent massive inputs
        truncated_table = table_html[:6000] + ("\n...[table continues]" if len(table_html) > 6000 else "")
        
        prompt = f"""Analyze this table and extract KEY METRICS (quantities, frequencies, thresholds).

{f'Caption: {caption}' if caption else ''}

Table:
{truncated_table}

Extract:
1. table_type: What kind of table is this? (metrics/schedule/requirements/pricing/personnel/equipment/evaluation/other)
2. table_topic: ONE SENTENCE about what it contains (max 100 chars)
3. key_metrics: Up to 5 most important numbers/values

KEEP IT BRIEF:
- metric names: 2-4 words max
- metric values: just the number + unit
- NO full sentences, NO explanations

Focus on QUANTIFIABLE data for cost estimation: counts, frequencies, durations, quantities, thresholds."""

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🔄 [{chunk_id}] Table extraction attempt {attempt}/{self.max_retries}")
                
                result = await self.client.chat.completions.create(
                    model=self.model,
                    response_model=TableSummary,
                    max_retries=2,
                    messages=[
                        {"role": "system", "content": "You extract table metadata. Keep responses EXTREMELY SHORT - max 5 metrics with brief 2-4 word names."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,  # More deterministic for tables
                )
                
                self.successful += 1
                logger.info(f"✅ [{chunk_id}] Table: {result.table_type} - {result.table_topic[:50]}... ({len(result.key_metrics)} metrics)")
                return result
                
            except Exception as e:
                logger.warning(f"⚠️ [{chunk_id}] Attempt {attempt}/{self.max_retries} failed: {type(e).__name__}: {str(e)[:150]}")
                
                if attempt < self.max_retries:
                    delay = 5 * (3 ** (attempt - 1))
                    logger.info(f"⏳ [{chunk_id}] Retrying in {delay}s...")
                    await asyncio.sleep(delay)
        
        # All retries failed - return empty summary
        self.failed += 1
        logger.warning(f"⚠️ [{chunk_id}] Table extraction failed after {self.max_retries} attempts - returning minimal result")
        
        return TableSummary(
            table_type="unknown",
            table_topic="Extraction failed - raw content preserved",
            key_metrics=[]
        )
    
    def get_stats(self) -> dict:
        """Get extraction statistics."""
        total = self.successful + self.failed
        return {
            "successful": self.successful,
            "failed": self.failed,
            "total": total,
            "failure_rate": round(self.failed / max(total, 1) * 100, 2)
        }
