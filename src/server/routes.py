"""
FastAPI Routes Module

Custom endpoints for RAG-Anything + LightRAG server:
- /insert: Document upload with automatic semantic post-processing
- /documents/upload: WebUI document upload (also triggers post-processing)
- /query/structured: Structured data retrieval (entities, relationships, sources)

Architecture (Issue #54 - Back to Basics with Native LightRAG):
1. Document Upload → process_document_with_semantic_inference()
2. RAG-Anything Processing → MinerU multimodal parsing
3. Native LightRAG Extraction → Entity/relationship extraction (18 types)
4. Queue Tracking → Detect when batch completes
5. Auto-Enhancement → Semantic post-processing runs ONCE after last document
6. Knowledge Graph Updated → Complete cross-document relationships

Key Innovation: Queue-aware processing detects batch completion automatically,
triggering cumulative semantic enhancement only after all documents are uploaded.

Issue #65 P1: /query/structured endpoint provides structured JSON output for agents,
returning entities, relationships, and sources directly without prose generation.
"""

import os
import asyncio
import logging
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse
from lightrag.api.config import global_args

from src.core import get_settings

# Note: inference imports removed - using RAG-Anything native pipeline (Branch 039/040)
# Post-processing handled by semantic_post_processor.enhance_knowledge_graph
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
        settings = get_settings()
        self.batch_timeout_seconds = settings.batch_timeout_seconds
    
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
    2. Native LightRAG entity extraction (18 govcon types)
    3. Semantic post-processing (relationship inference) - Auto-triggered on batch completion
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
    # Backend selection: MinerU 2.7.0 defaults to slow "hybrid-auto-engine"
    # Use "pipeline" for fast ONNX-based parsing (same as MinerU 2.6.x behavior)
    settings = get_settings()
    mineru_backend = settings.mineru_backend
    
    content_list, doc_id = await rag_instance.parse_document(
        file_path=file_path,
        output_dir=global_args.working_dir,
        parse_method="auto",
        backend=mineru_backend
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
        
        # ========================================================================
        # Branch 039/040 Lesson: Use RAG-Anything's native end-to-end pipeline
        # - NO custom processors needed
        # - Ontology injected through addon_params in initialization.py
        # - RAG-Anything handles all multimodal processing internally
        # - LightRAG handles chunking, extraction, parallelization natively
        # ========================================================================
        llm_timeout = settings.llm_timeout
        logger.info("🚀 Using RAG-Anything native end-to-end pipeline (Branch 039/040 approach)")
        logger.info("   Ontology: 18 govcon entity types injected via addon_params")
        logger.info(f"   Parallelization: 16 workers, {llm_timeout}s LLM timeout")
        
        # Get workspace from centralized settings
        workspace = settings.workspace
        output_dir = os.path.join(global_args.working_dir, workspace)
        
        # Use RAG-Anything's native insert_content_list for ALL storage types
        # This method handles:
        # - Text chunking with configured CHUNK_SIZE/CHUNK_OVERLAP
        # - Entity extraction with our ontology (via addon_params)
        # - Multimodal content (tables/images/equations) via built-in processors
        # - Native parallelization (llm_model_max_async)
        # - Storage to Neo4j or NetworkX based on config
        await rag_instance.insert_content_list(
            content_list=filtered_content,
            file_path=file_path,
            doc_id=doc_id
        )
        
        logger.info("✅ RAG-Anything processing complete")
        
        # Log queue status
        stats = await _queue_tracker.get_stats()
        if _queue_tracker.last_completion_time:
            time_since = (datetime.now() - _queue_tracker.last_completion_time).total_seconds()
            logger.info(f"⏭️  Document added to batch | Queue: {stats['processing']} processing, {stats['completed']} completed | {time_since:.0f}s since last completion (timeout: {_queue_tracker.batch_timeout_seconds}s)")
        else:
            logger.info(f"⏭️  Document added to batch | Queue: {stats['processing']} processing, {stats['completed']} completed")
        
        return {
            "status": "success",
            "relationships_inferred": 0,
            "method": "native_rag_anything",
            "message": "✅ Document processed via RAG-Anything native pipeline."
        }
    
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
            processing_result = await process_document_with_semantic_inference(
                file_path, file.filename, rag_instance, rag_instance.llm_model_func
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
            processing_result = await process_document_with_semantic_inference(
                file_path, file.filename, rag_instance, rag_instance.llm_model_func
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


def create_query_structured_endpoint(app, rag_instance):
    """
    Create /query/structured endpoint for structured data retrieval (Issue #65 P1)
    
    Provides structured JSON output (entities, relationships, chunks) for programmatic
    agent access to the knowledge graph WITHOUT requiring LLM prose generation.
    
    Implementation Note:
    LightRAG's native aquery_data() uses structured output parsing which has compatibility
    issues with xAI's API. This implementation uses a hybrid approach:
    - Chunks: Retrieved via naive mode (VDB similarity search)
    - Entities: Retrieved via direct VDB query
    - Relationships: Retrieved via direct VDB query
    
    This provides the same structured output without the keyword extraction step.
    """
    from lightrag import QueryParam
    from pydantic import BaseModel
    from typing import Optional, List
    
    class StructuredQueryRequest(BaseModel):
        """Request model for structured query endpoint"""
        query: str
        top_k: int = 20
        entity_top_k: int = 10
        relationship_top_k: int = 10
    
    async def query_structured(request: StructuredQueryRequest):
        """
        Return structured entity/relationship data instead of prose.
        
        This endpoint queries all three VDBs (chunks, entities, relationships) directly,
        avoiding the keyword extraction step that has xAI compatibility issues.
        
        Args:
            request: StructuredQueryRequest with query and top_k parameters
        
        Returns:
            JSON with status, data (entities, relationships, chunks)
        """
        logger.info(f"🔍 Structured query: '{request.query}'")
        
        try:
            lightrag = rag_instance.lightrag
            
            # Query all three VDBs in parallel
            import asyncio
            
            # 1. Query chunks VDB (text content)
            chunks_task = lightrag.chunks_vdb.query(request.query, top_k=request.top_k)
            
            # 2. Query entities VDB
            entities_task = lightrag.entities_vdb.query(request.query, top_k=request.entity_top_k)
            
            # 3. Query relationships VDB
            relationships_task = lightrag.relationships_vdb.query(request.query, top_k=request.relationship_top_k)
            
            # Execute all queries in parallel
            chunks_raw, entities_raw, relationships_raw = await asyncio.gather(
                chunks_task, entities_task, relationships_task
            )
            
            # Format results
            chunks = []
            for c in (chunks_raw or []):
                chunks.append({
                    "id": c.get("id", ""),
                    "content": c.get("content", ""),
                    "file_path": c.get("file_path", ""),
                    "source_id": c.get("source_id", "")
                })
            
            entities = []
            for e in (entities_raw or []):
                entities.append({
                    "entity_name": e.get("entity_name", ""),
                    "entity_type": e.get("entity_type", ""),
                    "description": e.get("description", ""),
                    "source_id": e.get("source_id", "")
                })
            
            relationships = []
            for r in (relationships_raw or []):
                relationships.append({
                    "src_id": r.get("src_id", ""),
                    "tgt_id": r.get("tgt_id", ""),
                    "description": r.get("description", ""),
                    "keywords": r.get("keywords", ""),
                    "source_id": r.get("source_id", "")
                })
            
            logger.info(f"✅ Structured query returned: {len(entities)} entities, {len(relationships)} relationships, {len(chunks)} chunks")
            
            return JSONResponse({
                "status": "success",
                "message": "Query executed successfully",
                "data": {
                    "entities": entities,
                    "relationships": relationships,
                    "chunks": chunks
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Structured query failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return JSONResponse({
                "status": "error",
                "message": str(e),
                "data": {"entities": [], "relationships": [], "chunks": []}
            }, status_code=500)
    
    # Register the route
    app.add_api_route(
        "/query/structured",
        query_structured,
        methods=["POST"],
        response_class=JSONResponse
    )
