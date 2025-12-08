"""
FastAPI Routes Module

Custom endpoints for RAG-Anything + LightRAG server:
- /insert: Document upload with automatic semantic post-processing
- /documents/upload: WebUI document upload (also triggers post-processing)

Architecture (Branch 022b1 - Batch-Aware Auto-Enhancement):
1. Document Upload → process_document_with_semantic_inference()
2. RAG-Anything Processing → MinerU multimodal parsing
3. LightRAG Extraction → Entity/relationship extraction (17 types)
4. Queue Tracking → Detect when batch completes
5. Auto-Enhancement → Semantic post-processing runs ONCE after last document
6. Knowledge Graph Updated → Complete cross-document relationships

Key Innovation: Queue-aware processing detects batch completion automatically,
triggering cumulative semantic enhancement only after all documents are uploaded.
"""

import os
import asyncio
import logging
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse
from lightrag.api.config import global_args

logger = logging.getLogger(__name__)

# ============================================================================
# BATCH PROCESSING STATE TRACKER
# ============================================================================
# Tracks document upload queue to detect when batch completes and trigger
# cumulative semantic enhancement automatically (no manual API call needed)

class DocumentQueueTracker:
    """Track document upload batches to detect completion"""
    
    def __init__(self):
        self.processing_docs = set()  # Currently processing doc_ids (post-parsing)
        self.pending_uploads = set()  # Files currently in upload/parsing phase (pre-processing)
        self.completed_docs = set()   # Completed doc_ids in current batch
        self.last_upload_time = None  # Timestamp of last upload
        self.last_completion_time = None  # Timestamp of last document completion
        self.enhancement_pending = False  # Whether enhancement needs to run
        self.enhancement_running = False  # Prevent duplicate enhancement
        self.lock = asyncio.Lock()    # Thread-safe state updates
        self.batch_timeout_seconds = int(os.getenv("BATCH_TIMEOUT_SECONDS", "30"))  # Time to wait after last completion
    
    async def register_request_start(self, filename: str):
        """Register that an upload request has started (before parsing)"""
        async with self.lock:
            self.pending_uploads.add(filename)
            self.last_upload_time = datetime.now()
            self.enhancement_pending = True
            logger.info(f"📥 Upload request started: {filename} (pending: {len(self.pending_uploads)})")

    async def register_request_end(self, filename: str):
        """Register that an upload request has finished (after processing)"""
        async with self.lock:
            if filename in self.pending_uploads:
                self.pending_uploads.remove(filename)
            logger.info(f"🏁 Upload request finished: {filename} (pending: {len(self.pending_uploads)})")

    async def document_started(self, doc_id: str):
        """Register document processing started (after parsing)"""
        async with self.lock:
            self.processing_docs.add(doc_id)
            logger.info(f"⚙️ Document processing started: {doc_id} (queue: {len(self.processing_docs)} processing)")
    
    async def document_completed(self, doc_id: str):
        """Register document processing completed"""
        async with self.lock:
            if doc_id in self.processing_docs:
                self.processing_docs.remove(doc_id)
            self.completed_docs.add(doc_id)
            self.last_completion_time = datetime.now()
            logger.info(f"✅ Document completed: {doc_id} (queue: {len(self.processing_docs)} remaining)")
    
    async def is_batch_complete(self) -> bool:
        """Check if all documents in current batch have completed
        
        Uses timeout-based detection: batch is complete when no documents
        are processing AND no new documents arrive within timeout window.
        """
        async with self.lock:
            # Batch is complete when:
            # 1. No documents currently processing (post-parse)
            # 2. No documents currently pending upload/parsing (pre-parse)
            # 3. At least one document completed (not just empty queue)
            # 4. Enhancement is pending (documents were uploaded)
            # 5. Timeout has elapsed since last completion (no new uploads)
            
            if len(self.pending_uploads) > 0:
                return False  # Still receiving/parsing files
                
            if (
                len(self.processing_docs) == 0 and
                len(self.completed_docs) > 0 and
                self.enhancement_pending and
                not self.enhancement_running and
                self.last_completion_time is not None
            ):
                time_since_completion = (datetime.now() - self.last_completion_time).total_seconds()
                return time_since_completion >= self.batch_timeout_seconds
            return False
    
    async def mark_enhancement_running(self):
        """Mark that enhancement is now running"""
        async with self.lock:
            self.enhancement_running = True
    
    async def reset_batch(self):
        """Reset tracker after enhancement completes"""
        async with self.lock:
            self.completed_docs.clear()
            self.enhancement_pending = False
            self.enhancement_running = False
            logger.info("🔄 Batch state reset - ready for next upload batch")
    
    async def get_stats(self) -> dict:
        """Get current queue statistics"""
        async with self.lock:
            return {
                "pending_uploads": len(self.pending_uploads),
                "processing": len(self.processing_docs),
                "completed": len(self.completed_docs),
                "enhancement_pending": self.enhancement_pending,
                "enhancement_running": self.enhancement_running
            }

# Global queue tracker instance
_queue_tracker = DocumentQueueTracker()


async def extract_with_semaphore(
    chunk_text: str,
    chunk_idx: int,
    json_extractor,
    semaphore: asyncio.Semaphore,
    total_chunks: int
):
    """
    Extract entities/relationships from a single chunk with concurrency control.
    
    Issue #17: Parallel chunk processing for 87% extraction time reduction.
    Uses semaphore to limit concurrent LLM calls (respects API rate limits).
    """
    from src.ontology.schema import ExtractionResult
    
    async with semaphore:
        chunk_id = f"chunk-{chunk_idx+1}"
        logger.info(f"   Processing chunk {chunk_idx+1}/{total_chunks} ({len(chunk_text):,} chars)...")
        try:
            return await json_extractor.extract(chunk_text, chunk_id=chunk_id)
        except Exception as e:
            logger.error(f"Chunk {chunk_idx+1} extraction failed: {e}")
            # Return empty result to continue pipeline (graceful degradation)
            return ExtractionResult(entities=[], relationships=[])


async def extract_multimodal_with_semaphore(
    modal_item: dict,
    item_idx: int,
    json_extractor,
    semaphore: asyncio.Semaphore,
    total_items: int
):
    """
    Extract entities/relationships from a single table/image/equation with concurrency control.
    
    Parallel multimodal processing (similar to text chunk extraction).
    Processes tables, images, equations concurrently to reduce extraction time.
    """
    from src.ontology.schema import ExtractionResult
    
    async with semaphore:
        content_type = modal_item.get('type', 'unknown')
        page_idx = modal_item.get('page_idx', 0)
        chunk_id = f"govcon_{content_type}_p{page_idx}"
        
        logger.info(f"   Processing {content_type} {item_idx+1}/{total_items} (page {page_idx}) [{chunk_id}]...")
        
        try:
            # Extract textualized content (MinerU already did vision work)
            if content_type == "table":
                text_content = modal_item.get("table_body", "")
                caption = ", ".join(modal_item.get("table_caption", []))
            elif content_type == "image":
                text_content = modal_item.get("text", "")
                caption = ", ".join(modal_item.get("image_caption", []))
            elif content_type == "equation":
                text_content = modal_item.get("latex", "")
                caption = modal_item.get("equation_caption", "")
            else:
                text_content = str(modal_item)
                caption = ""
            
            # Build ontology-aware prompt (same as GovconMultimodalProcessor)
            caption_section = f"{content_type.title()}: {caption}\n\n" if caption else ""
            ontology_prompt = f"""
{caption_section}Content:
{text_content}

Extract government contracting entities from this {content_type}:

1. REQUIREMENTS - Compliance criteria, specifications, constraints
   - Include frequencies, standards, completion criteria
   - Tag with requirement type (performance, technical, delivery)

2. METRICS - Quantifiable measures for estimation
   - Quantities (counts, volumes, capacities)
   - Frequencies (daily, weekly, monthly, yearly)
   - Coverage (hours, days, locations)
   - Thresholds (minimums, maximums, ranges)

3. DELIVERABLES - Work outputs, reports, schedules
   - Document types and formats
   - Submission frequencies and deadlines
   - Review/approval processes

4. RESOURCES - Equipment, personnel, facilities, materials
   - Specific models/types
   - Quantities required
   - Qualifications/certifications

5. RELATIONSHIPS - How entities connect
   - Requirements ↔ Metrics (compliance measurement)
   - Deliverables ↔ Requirements (evidence of compliance)
   - Resources ↔ Requirements (capability enablers)

Focus on workload drivers and basis of estimate elements.
"""
            
            result = await json_extractor.extract_from_text(
                text=ontology_prompt,
                chunk_id=chunk_id
            )
            
            logger.info(f"   ✅ [{chunk_id}] Extracted {len(result.entities)} entities from {content_type}")
            return result, modal_item
            
        except Exception as e:
            logger.error(f"{content_type.title()} {item_idx+1} extraction failed: {e}")
            # Return empty result to continue pipeline (graceful degradation)
            return ExtractionResult(entities=[], relationships=[]), modal_item


async def process_document_with_semantic_inference(
    file_path: str,
    file_name: str,
    rag_instance,
    llm_func
) -> dict:
    """
    Integrated document processing with semantic relationship inference.
    
    Works with ALL RFP formats (UCF, task orders, quotes, FOPRs, embedded formats).
    No format detection needed - LLM handles structure semantically.
    
    Pipeline:
    1. RAG-Anything multimodal processing (MinerU parser)
    2. LLM entity extraction (17 types with metadata)
    3. LLM relationship inference (5 algorithms) - ALWAYS RUNS
    4. Save complete knowledge graph
    
    Args:
        file_path: Path to document file
        file_name: Original filename
        rag_instance: Initialized RAGAnything instance
        llm_func: LLM function for relationship inference
    
    Returns:
        dict: Processing result with relationships_inferred count
    """
    logger.info(f"📄 Processing {file_name}")
    logger.info(f"🔧 Using RAG-Anything + LLM semantic inference (format-agnostic)")
    
    # Step 1: Parse document with MinerU (multimodal extraction)
    content_list, doc_id = await rag_instance.parse_document(
        file_path=file_path,
        output_dir=global_args.working_dir,
        parse_method="auto"
    )
    
    # Register document in queue tracker
    await _queue_tracker.document_started(doc_id)
    
    try:
        # Step 1.5: Filter out MinerU discarded content types (Fix #3)
        # MinerU 2.6.4 correctly identifies artifacts but RAG-Anything processes ALL content types
        # Pre-filtering prevents GenericModalProcessor from creating contaminated entities
        DISCARDED_TYPES = {
            "discarded",      # Generic discarded content (page numbers, OCR glitches)
            "header",         # Page headers
            "footer",         # Page footers
            "page_number",    # Page numbers
            "aside_text",     # Marginal notes
            "page_footnote",  # Footer notes (not document footnotes)
        }
        
        original_count = len(content_list)
        filtered_content = [
            item for item in content_list
            if item.get("type") not in DISCARDED_TYPES
        ]
        filtered_count = len(filtered_content)
        discarded_count = original_count - filtered_count
        
        if discarded_count > 0:
            logger.info(f"🚫 Filtered {discarded_count} discarded content blocks (keeping {filtered_count}/{original_count} legitimate items)")
        
        # Check if Neo4j storage is enabled - use custom ontology extraction BEFORE standard processing
        import os
        if os.getenv("GRAPH_STORAGE") == "Neo4JStorage":
            logger.info("📊 Neo4j storage detected - using custom ontology extraction (bypassing LightRAG)")
            
            # Extract text from content_list for ontology processing
            # MinerU provides: {'type': 'text'/'table'/'image', 'text': '...', 'page_idx': N}
            from src.extraction.json_extractor import JsonExtractor
            from src.processors import GovconMultimodalProcessor
            from src.processors.govcon_kg_processor import GovconKGProcessor
            from src.deduplication.entity_deduplicator import deduplicate_entities, log_deduplication_stats
            
            # Initialize processor and extractors
            kg_processor = GovconKGProcessor()
            json_extractor = JsonExtractor()
            
            # PHASE 1: TEXT EXTRACTION (chunk text blocks)
            text_chunks = []
            for item in filtered_content:
                if item.get('type') == 'text':
                    content_text = item.get('text', '')
                    if content_text and content_text.strip():
                        text_chunks.append(content_text)
            
            # FIX: Spreadsheets with only tables may have zero text content - allow empty text
            # RAG-Anything's multimodal processors will handle table extraction
            if not text_chunks:
                logger.warning(f"⚠️ No text content found in {file_name} - likely spreadsheet with only tables")
                logger.info("📊 Skipping text extraction, proceeding with multimodal processing only")
                
                # Count multimodal items to verify document has extractable content
                multimodal_count = sum(1 for item in filtered_content if item.get('type') in ['table', 'image'])
                if multimodal_count == 0:
                    logger.error(f"❌ Document {file_name} has no extractable content (no text, tables, or images)")
                    return {"error": "No extractable content", "relationships_inferred": 0}
                
                logger.info(f"✅ Found {multimodal_count} multimodal items (tables/images) to process")
                
                # Skip text processing, go directly to multimodal
                full_text = ""
                chunked_texts = []  # Empty list - no text chunks to process
            else:
                full_text = "\n\n".join(text_chunks)
                logger.info(f"📝 TEXT: Extracted {len(text_chunks)} text blocks ({len(full_text)} chars total)")
                
                # Use LightRAG's chunking strategy for consistent extraction
                import tiktoken
                chunk_size = int(os.getenv("CHUNK_SIZE", "8192"))
                chunk_overlap = int(os.getenv("CHUNK_OVERLAP_TOKEN_SIZE", "1024"))
                
                tokenizer = tiktoken.get_encoding("cl100k_base")
                tokens = tokenizer.encode(full_text)
                
                # Create overlapping chunks
                chunked_texts = []
                start = 0
                while start < len(tokens):
                    end = min(start + chunk_size, len(tokens))
                    chunk_tokens = tokens[start:end]
                    chunk_text = tokenizer.decode(chunk_tokens)
                    chunked_texts.append(chunk_text)
                    start += (chunk_size - chunk_overlap)  # Overlap for context
                
                logger.info(f"🔪 Chunked text into {len(chunked_texts)} chunks ({chunk_size} tokens, {chunk_overlap} overlap)")
        
        # PHASE 2: PARALLEL EXTRACTION (Text + Multimodal)
        logger.info("🚀 Running parallel extraction with custom ontology...")
        
        try:
            max_parallel = int(os.getenv("MAX_ASYNC", "8"))
            semaphore = asyncio.Semaphore(max_parallel)
            
            # ============================================================================
            # PHASE 2A: TEXT CHUNK EXTRACTION
            # ============================================================================
            logger.info(f"⚡ Extracting from {len(chunked_texts)} text chunks in parallel (max concurrency: {max_parallel})...")
            
            text_chunk_data = []  # Will store (chunk_id, entities, rels) tuples
            
            # Create parallel tasks for all text chunks
            tasks = [
                extract_with_semaphore(chunk, i, json_extractor, semaphore, len(chunked_texts))
                for i, chunk in enumerate(chunked_texts)
            ]
            
            # Execute in parallel, collecting results
            results = await asyncio.gather(*tasks)
            
            # Convert Pydantic results to dicts for processor
            for i, result in enumerate(results):
                chunk_id = f"text_chunk_{i}"
                
                # Convert entities to dicts
                entities_dicts = [
                    {
                        "entity_name": entity.entity_name,
                        "entity_type": entity.entity_type,
                        "description": entity.entity_name,
                        "source_id": doc_id,
                        "file_path": file_name
                    }
                    for entity in result.entities
                ]
                
                # Convert relationships to dicts
                rels_dicts = [
                    {
                        "src_id": rel.source_entity.entity_name,
                        "tgt_id": rel.target_entity.entity_name,
                        "description": rel.relationship_type,
                        "keywords": rel.relationship_type,
                        "weight": 1.0,
                        "source_id": doc_id
                    }
                    for rel in result.relationships
                ]
                
                text_chunk_data.append((chunk_id, entities_dicts, rels_dicts))
            
            logger.info(f"✅ TEXT EXTRACTION: Collected {len(text_chunk_data)} chunks for processing")
            
            # ============================================================================
            # PHASE 2B: MULTIMODAL EXTRACTION
            # ============================================================================
            multimodal_items = [item for item in filtered_content if item.get('type') in ['table', 'image', 'equation']]
            multimodal_chunk_data = []  # Will store (item_id, entities, rels) tuples
            
            if multimodal_items:
                logger.info(f"⚡ Extracting from {len(multimodal_items)} multimodal items in parallel (max concurrency: {max_parallel})...")
                
                # Create parallel tasks for all multimodal items
                tasks = [
                    extract_multimodal_with_semaphore(item, i, json_extractor, semaphore, len(multimodal_items))
                    for i, item in enumerate(multimodal_items)
                ]
                
                # Execute in parallel, collecting results
                multimodal_results = await asyncio.gather(*tasks)
                
                # Convert Pydantic results to dicts for processor
                for i, (extraction_result, modal_item) in enumerate(multimodal_results):
                    content_type = modal_item.get('type', 'unknown')
                    page_idx = modal_item.get('page_idx', i)
                    item_id = f"multimodal_{content_type}_p{page_idx}"
                    
                    # Convert entities to dicts
                    entities_dicts = [
                        {
                            "entity_name": entity.entity_name,
                            "entity_type": entity.entity_type,
                            "description": entity.entity_name,
                            "source_id": doc_id,
                            "file_path": file_name
                        }
                        for entity in extraction_result.entities
                        if entity.entity_name and entity.entity_name.strip()
                    ]
                    
                    # Convert relationships to dicts
                    rels_dicts = [
                        {
                            "src_id": rel.source_entity.entity_name,
                            "tgt_id": rel.target_entity.entity_name,
                            "description": rel.relationship_type,
                            "keywords": rel.relationship_type,
                            "weight": 1.0,
                            "source_id": doc_id
                        }
                        for rel in extraction_result.relationships
                        if (rel.source_entity.entity_name and rel.source_entity.entity_name.strip() and
                            rel.target_entity.entity_name and rel.target_entity.entity_name.strip())
                    ]
                    
                    multimodal_chunk_data.append((item_id, entities_dicts, rels_dicts))
                
                logger.info(f"✅ MULTIMODAL EXTRACTION: Collected {len(multimodal_chunk_data)} items for processing")
            
            # ============================================================================
            # PHASE 3-5: USE GOVCON KG PROCESSOR (Extract → Merge → Finalize)
            # ============================================================================
            # This replaces all the manual deduplication and custom_kg building
            processed_kg = kg_processor.process_document(
                text_chunks=text_chunk_data,
                multimodal_items=multimodal_chunk_data if multimodal_chunk_data else None
            )
            
            # ============================================================================
            # BUILD CUSTOM_KG FOR LIGHTRAG INSERTION
            # ============================================================================
            # Add chunks (needed for LightRAG's vector DB)
            custom_kg = {
                "chunks": [],
                "entities": processed_kg["entities"],
                "relationships": processed_kg["relationships"]
            }
            
            # Add text chunks
            for i, chunk_text in enumerate(chunked_texts):
                custom_kg["chunks"].append({
                    "content": chunk_text,
                    "source_id": doc_id,
                    "file_path": file_name,
                    "chunk_order_index": i
                })
            
            # Add multimodal chunks
            if multimodal_items:
                for item in multimodal_items:
                    content_type = item.get('type', 'unknown')
                    page_idx = item.get('page_idx', 0)
                    
                    # Extract raw content for chunk storage
                    if content_type == "table":
                        raw_content = item.get("table_body", "")
                    elif content_type == "image":
                        raw_content = item.get("text", "")
                    elif content_type == "equation":
                        raw_content = item.get("latex", "")
                    else:
                        raw_content = str(item)
                    
                    # Only add chunk if content is non-empty (OpenAI embeddings reject empty strings)
                    if raw_content and raw_content.strip():
                        custom_kg["chunks"].append({
                            "content": raw_content,
                            "source_id": doc_id,
                            "file_path": file_name,
                            "chunk_order_index": len(custom_kg["chunks"]),
                            "modal_type": content_type,
                            "page_idx": page_idx
                        })
            
            total_entities = len(custom_kg["entities"])
            total_rels = len(custom_kg["relationships"])
            
            logger.info(f"💾 Phase 5B: Inserting deduplicated ontology ({total_entities} entities, {total_rels} relationships)...")            # Track entities before insertion for merge detection
            entity_names_before = set()
            node_count_before = 0
            try:
                # Access Neo4j/NetworkX storage (not VDB - that's for embeddings)
                kg_storage = rag_instance.lightrag.chunk_entity_relation_graph
                if hasattr(kg_storage, 'graph') and hasattr(kg_storage.graph, 'nodes'):
                    # NetworkX/Neo4j stores nodes with entity_name attribute
                    node_count_before = kg_storage.graph.number_of_nodes()
                    entity_names_before = {
                        data.get('entity_name') 
                        for node, data in kg_storage.graph.nodes(data=True)
                        if data.get('entity_name')
                    }
                    logger.info(f"   📊 Graph state BEFORE insertion: {node_count_before} nodes, {len(entity_names_before)} unique entity_names")
            except Exception as e:
                logger.debug(f"Could not capture pre-insertion entities: {e}")
            
            await rag_instance.lightrag.ainsert_custom_kg(custom_kg, full_doc_id=doc_id)
            
            # CHECK IMMEDIATELY AFTER INSERTION (before finalize)
            try:
                kg_storage = rag_instance.lightrag.chunk_entity_relation_graph
                if hasattr(kg_storage, 'graph') and hasattr(kg_storage.graph, 'nodes'):
                    node_count_after_insert = kg_storage.graph.number_of_nodes()
                    entity_names_after_insert = {
                        data.get('entity_name')
                        for node, data in kg_storage.graph.nodes(data=True)
                        if data.get('entity_name')
                    }
                    nodes_added = node_count_after_insert - node_count_before
                    unique_names_added = len(entity_names_after_insert) - len(entity_names_before)
                    
                    logger.info(f"✅ Custom ontology inserted (text + multimodal)")
                    logger.info(f"   📊 Graph state AFTER insertion: {node_count_after_insert} nodes (+{nodes_added}), {len(entity_names_after_insert)} unique entity_names (+{unique_names_added})")
                    
                    # Calculate and show merge details like LightRAG does
                    duplicates_merged_during_upsert = total_entities - unique_names_added
                    if duplicates_merged_during_upsert > 0:
                        logger.info(f"   🔀 LightRAG upsert deduplication: {total_entities} attempted → {unique_names_added} inserted = {duplicates_merged_during_upsert} duplicates merged")
                        
                        # Show itemized merge output (top 10)
                        sample_size = min(10, len(duplicates_in_custom_kg))
                        if sample_size > 0:
                            logger.info(f"   📋 Itemized merges:")
                            for name, count in sorted(duplicates_in_custom_kg.items(), key=lambda x: -x[1])[:sample_size]:
                                logger.info(f"      Merged: `{name}` | {count-1}+1")
                            if len(duplicates_in_custom_kg) > sample_size:
                                logger.info(f"      ... and {len(duplicates_in_custom_kg) - sample_size} more entities merged")
                    else:
                        logger.info(f"   ℹ️  No duplicates merged (all {total_entities} entity names were unique)")
            except Exception as e:
                logger.info("✅ Custom ontology inserted (text + multimodal)")
                logger.debug(f"Could not check post-insertion state: {e}")
            
            # PHASE 6: TRIGGER MERGE PHASES ONLY (no chunking, no extraction)
            logger.info("🔄 Triggering LightRAG merge phases (Entity Dedup, Relationship Dedup, Graph Indexing)...")
            logger.info("   📊 Pre-merge stats:")
            logger.info(f"      • Entities inserted: {total_entities}")
            logger.info(f"      • Relationships inserted: {total_rels}")
            
            # Run merge phases (combines duplicate entities/relationships, updates embeddings)
            await rag_instance.lightrag.finalize_storages()
            
            # Query final counts and show what got merged
            try:
                kg_storage = rag_instance.lightrag.chunk_entity_relation_graph
                
                if hasattr(kg_storage, 'graph') and hasattr(kg_storage.graph, 'nodes'):
                    # Count final entities in graph
                    final_entity_count = kg_storage.graph.number_of_nodes()
                    entity_names_after = {
                        data.get('entity_name')
                        for node, data in kg_storage.graph.nodes(data=True)
                        if data.get('entity_name')
                    }
                    
                    # Calculate merge stats: duplicates = what we tried to insert - what actually got inserted
                    # This works regardless of whether workspace had prior entities
                    entities_merged = total_entities - (len(entity_names_after) - len(entity_names_before))
                    
                    logger.debug(f"   Debug: entity_names_before={len(entity_names_before)}, entity_names_after={len(entity_names_after)}, total_entities={total_entities}, entities_merged={entities_merged}")
                    
                    # Show itemized merge output
                    if entities_merged > 0:
                        logger.info(f"   🔀 Merged {entities_merged} duplicate entities:")
                        # Count entity occurrences in custom_kg
                        entity_count = {}
                        for entity_dict in custom_kg["entities"]:
                            name = entity_dict.get("entity_name")
                            if name:
                                entity_count[name] = entity_count.get(name, 0) + 1
                        
                        # Find duplicates (entities that appeared multiple times)
                        duplicates_found = {name: count for name, count in entity_count.items() if count > 1}
                        sample_size = min(10, len(duplicates_found))
                        for i, (name, count) in enumerate(sorted(duplicates_found.items(), key=lambda x: -x[1])[:sample_size]):
                            logger.info(f"      • `{name}` | {count-1}+1 (consolidated from {count} instances)")
                        
                        if len(duplicates_found) > sample_size:
                            logger.info(f"      • ... and {len(duplicates_found) - sample_size} more duplicates merged")
                else:
                    final_entity_count = total_entities
                    entities_merged = 0
                
                # Count final relationships
                if hasattr(kg_storage, 'graph') and hasattr(kg_storage.graph, 'edges'):
                    final_rel_count = kg_storage.graph.number_of_edges()
                    rels_merged = total_rels - final_rel_count
                else:
                    final_rel_count = total_rels
                    rels_merged = 0
                
                logger.info("   ✅ Post-merge stats:")
                logger.info(f"      • Final entities: {final_entity_count} (pre-deduplicated by KG processor, {entities_merged} additional duplicates merged by LightRAG)")
                logger.info(f"      • Final relationships: {final_rel_count} (pre-deduplicated by KG processor, {rels_merged} additional duplicates merged by LightRAG)")
            except Exception as e:
                logger.warning(f"   ⚠️ Could not retrieve detailed merge stats: {e}")
            
            logger.info("✅ Merge phases completed (Entity Dedup, Relationship Dedup, Graph Indexing)")
            logger.info("✅ Complete knowledge graph inserted with deduplication")
            
            # Log queue status
            stats = await _queue_tracker.get_stats()
            if _queue_tracker.last_completion_time:
                time_since = (datetime.now() - _queue_tracker.last_completion_time).total_seconds()
                logger.info(f"⏭️  Document added to batch | Queue: {stats['processing']} processing, {stats['completed']} completed | {time_since:.0f}s since last completion (timeout: {_queue_tracker.batch_timeout_seconds}s)")
            else:
                logger.info(f"⏭️  Document added to batch | Queue: {stats['processing']} processing, {stats['completed']} completed")
            
            return {
                "entities_extracted": total_entities,
                "relationships_extracted": total_rels,
                "message": "✅ Document processed. Enhancement will run automatically when batch completes."
            }
            
        except Exception as e:
            logger.error(f"❌ Custom ontology extraction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    finally:
        # CRITICAL: Always mark document as completed, even on error
        # This prevents batch detection from blocking indefinitely
        await _queue_tracker.document_completed(doc_id)
        logger.info(f"✅ Document {doc_id} marked as completed in queue tracker")
        
        # Spawn background task to monitor for batch completion
        # Each document spawns a checker that polls every 5s
        async def batch_completion_monitor():
            while True:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                if await _queue_tracker.is_batch_complete():
                    logger.info(f"🎯 BATCH COMPLETE - {len(_queue_tracker.completed_docs)} documents processed, {_queue_tracker.batch_timeout_seconds}s idle")
                    await _queue_tracker.mark_enhancement_running()
                    
                    try:
                        from src.inference.semantic_post_processor import enhance_knowledge_graph
                        
                        inference_result = await enhance_knowledge_graph(
                            rag_storage_path=global_args.working_dir,
                            llm_func=llm_func,
                            batch_size=50
                        )
                        
                        logger.info("✅ Cumulative semantic enhancement complete")
                        logger.info(f"   Entities corrected: {inference_result.get('entities_corrected', 0)}")
                        logger.info(f"   Relationships inferred: {inference_result.get('relationships_inferred', 0)}")
                        logger.info(f"   View results in Neo4j Browser: http://localhost:7474")
                        
                        await _queue_tracker.reset_batch()
                        return  # Exit monitor after successful enhancement
                        
                    except Exception as e:
                        logger.error(f"❌ Batch enhancement failed: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        await _queue_tracker.reset_batch()
                        return  # Exit even on error
                
                # Exit if enhancement already running (another task got it)
                if _queue_tracker.enhancement_running:
                    return
        
        # Fire and forget - multiple tasks may run but only first one triggers
        asyncio.create_task(batch_completion_monitor())


def create_insert_endpoint(app, rag_instance):
    """
    Create custom /insert endpoint with automatic semantic post-processing
    
    This overrides LightRAG's default /insert to automatically run
    LLM-powered relationship inference after document extraction.
    
    Args:
        app: FastAPI application instance
        rag_instance: Initialized RAGAnything instance
    """
    
    async def insert_with_semantic_processing(file: UploadFile = File(...)):
        """
        Standard LightRAG insert endpoint with semantic post-processing
        
        API clients use this endpoint directly.
        """
        logger.info(f"🔔 ENDPOINT CALLED: /insert with file: {file.filename}")
        
        # Register request start immediately to prevent premature batch completion
        await _queue_tracker.register_request_start(file.filename)
        
        try:
            # Save uploaded file with original filename to temp directory
            # This preserves human-readable names in query citations
            temp_dir = tempfile.gettempdir()
            safe_filename = file.filename.replace('/', '_').replace('\\', '_')
            file_path = os.path.join(temp_dir, safe_filename)
            
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file.file, f)
            
            logger.info(f"📄 Processing {file.filename} via /insert endpoint")
            
            # Integrated processing: Entity extraction + relationship inference in one pipeline
            # NOTE: Pass safe_filename (not file_path) as the stored reference
            # The temp path is only for reading the file - citations should use the clean filename
            processing_result = await process_document_with_semantic_inference(
                file_path, safe_filename, rag_instance, rag_instance.llm_model_func
            )
            
            logger.info(f"✅ Processing complete for {file.filename}")
            logger.info(f"   Relationships inferred: {processing_result['relationships_inferred']}")
            
            # Clean up temp file
            os.unlink(file_path)
            
            return JSONResponse({
                "status": "success",
                "message": f"Document {file.filename} processed successfully",
                "relationships_inferred": processing_result["relationships_inferred"],
                "method": "RAG-Anything + LLM semantic inference (format-agnostic)"
            })
            
        except Exception as e:
            logger.error(f"❌ Error processing document: {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
        
        finally:
            # Always unregister request to allow batch completion
            await _queue_tracker.register_request_end(file.filename)
    
    # Register the route explicitly (decorator doesn't work when called after app init)
    app.add_api_route(
        "/insert",
        insert_with_semantic_processing,
        methods=["POST"],
        response_class=JSONResponse
    )


def create_documents_upload_endpoint(app, rag_instance):
    """
    Override LightRAG's WebUI /documents/upload endpoint to use RAG-Anything
    
    CRITICAL FIX: WebUI uses /documents/upload (not /insert), which was bypassing
    RAG-Anything's multimodal processing. This override ensures MinerU parser runs.
    
    Args:
        app: FastAPI application instance
        rag_instance: Initialized RAGAnything instance
    """
    
    async def documents_upload_with_raganything(file: UploadFile = File(...)):
        """
        WebUI document upload endpoint - routes through RAG-Anything for MinerU processing
        
        This is the endpoint the WebUI actually uses (discovered via server logs).
        """
        print(f"🔔🔔🔔 CUSTOM ENDPOINT CALLED: /documents/upload with file: {file.filename}")
        logger.info(f"🔔 ENDPOINT CALLED: /documents/upload with file: {file.filename}")
        
        # Register request start immediately to prevent premature batch completion
        await _queue_tracker.register_request_start(file.filename)
        
        try:
            # Save uploaded file with original filename to temp directory
            # This preserves human-readable names in query citations
            temp_dir = tempfile.gettempdir()
            safe_filename = file.filename.replace('/', '_').replace('\\', '_')
            file_path = os.path.join(temp_dir, safe_filename)
            
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file.file, f)
            
            logger.info(f"📄 Processing {file.filename} via WebUI /documents/upload endpoint")
            
            # Integrated processing: Entity extraction + relationship inference in one pipeline
            # NOTE: Pass safe_filename (not file_path) as the stored reference
            # The temp path is only for reading the file - citations should use the clean filename
            processing_result = await process_document_with_semantic_inference(
                file_path, safe_filename, rag_instance, rag_instance.llm_model_func
            )
            
            logger.info(f"✅ Processing complete for {file.filename}")
            if 'relationships_inferred' in processing_result:
                logger.info(f"   Relationships inferred: {processing_result['relationships_inferred']}")
            
            # Clean up temp file
            os.unlink(file_path)
            
            return JSONResponse({
                "status": "success",
                "message": f"Document {file.filename} processed successfully",
                "relationships_inferred": processing_result.get("relationships_inferred", 0),
                "method": "RAG-Anything + LLM semantic inference (format-agnostic)"
            })
            
        except Exception as e:
            logger.error(f"❌ Error processing document: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
        
        finally:
            # Always unregister request to allow batch completion
            await _queue_tracker.register_request_end(file.filename)
    
    # Register the route explicitly (decorator doesn't work when called after app init)
    app.add_api_route(
        "/documents/upload",
        documents_upload_with_raganything,
        methods=["POST"],
        response_class=JSONResponse
    )
