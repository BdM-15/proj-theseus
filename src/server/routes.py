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
from lightrag.api.routers.query_routes import QueryRequest
from lightrag.base import QueryParam

# REMOVED: Query-time custom context and prompt loading
# from src.query.ontology_context import build_query_context
# from src.core.prompt_loader import load_prompt
# REASON: Using LightRAG defaults for query processing improves retrieval quality.
# Domain knowledge is applied at extraction time, not query time.

logger = logging.getLogger(__name__)

def _should_enable_vlm(query: str) -> bool:
    """
    RAG-Anything auto-enables VLM when vision_model_func exists.
    For GovCon workflows, default to text-only unless the user explicitly asks about images/figures.
    """
    q = (query or "").lower()
    return any(k in q for k in ("image", "images", "figure", "figures", "chart", "charts", "diagram", "diagrams"))

def _json_safe(obj):
    """
    Convert Neo4j and other non-JSON-serializable objects into JSON-safe primitives.
    Primarily used for WebUI graph endpoints where Neo4j temporal types may appear.
    """
    # Neo4j temporal types (neo4j.time.DateTime / Date / Time / Duration)
    try:
        import neo4j  # noqa: F401
        from neo4j.time import DateTime as Neo4jDateTime
        from neo4j.time import Date as Neo4jDate
        from neo4j.time import Time as Neo4jTime
        from neo4j.time import Duration as Neo4jDuration

        if isinstance(obj, Neo4jDateTime):
            return obj.iso_format()
        if isinstance(obj, Neo4jDate):
            return obj.iso_format()
        if isinstance(obj, Neo4jTime):
            return obj.iso_format()
        if isinstance(obj, Neo4jDuration):
            # Duration doesn't have a universally standard ISO string everywhere;
            # repr is stable enough for UI/debug and avoids 500s.
            return str(obj)
    except Exception:
        # If neo4j isn't installed/available, just fall through.
        pass

    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(v) for v in obj]

    return obj


def create_query_stream_endpoint(app, rag_instance) -> None:
    """
    Override LightRAG's /query/stream to route queries through RAG-Anything.

    DESIGN PRINCIPLE: Pure LightRAG Default Passthrough
    ====================================================
    This endpoint uses LightRAG's native query behavior without modifications:
    - No custom user_prompt injection (LightRAG handles response formatting)
    - No ontology context appending (extraction-time prompts handle domain knowledge)
    - No custom keyword overrides (LightRAG's keyword extraction is well-tuned)
    - Parameters from request are passed through unchanged (user controls behavior)

    This aligns with LightRAG/RAG-Anything design intent for reliable retrieval.
    """

    async def query_stream_override(request: QueryRequest):
        try:
            from fastapi.responses import StreamingResponse

            stream_mode = request.stream if request.stream is not None else True
            param: QueryParam = request.to_query_params(stream_mode)
            logger.info(
                "🔎 /query/stream request: mode=%s top_k=%s chunk_top_k=%s",
                getattr(param, "mode", None),
                getattr(param, "top_k", None),
                getattr(param, "chunk_top_k", None),
            )

            # ══════════════════════════════════════════════════════════════════════════
            # LIGHTRAG DEFAULT BEHAVIOR (Restored)
            # ══════════════════════════════════════════════════════════════════════════
            # REMOVED: Custom user_prompt loading (base_user_prompt.md)
            # REMOVED: Ontology context injection (build_query_context)
            # REASON: These modifications fragmented hybrid retrieval and caused generic responses.
            #
            # Domain-specific knowledge is now applied only at extraction time:
            # - Entity extraction prompts (prompts/extraction/)
            # - 18-entity GovCon ontology (src/ontology/schema.py)
            # - Semantic post-processing (8 algorithms)
            #
            # Users who need custom formatting can provide user_prompt in the request.
            # ══════════════════════════════════════════════════════════════════════════

            # Use RAG-Anything query entrypoint with LightRAG defaults
            # Only pass parameters that were explicitly provided in the request
            query_kwargs = {
                "stream": stream_mode,
            }

            # Pass through user-provided parameters (preserve user control)
            if getattr(param, "only_need_context", None) is not None:
                query_kwargs["only_need_context"] = param.only_need_context
            if getattr(param, "response_type", None) is not None:
                query_kwargs["response_type"] = param.response_type
            if getattr(param, "top_k", None) is not None:
                query_kwargs["top_k"] = param.top_k
            if getattr(param, "chunk_top_k", None) is not None:
                query_kwargs["chunk_top_k"] = param.chunk_top_k
            if getattr(param, "max_total_tokens", None) is not None:
                query_kwargs["max_total_tokens"] = param.max_total_tokens
            if getattr(param, "user_prompt", None) is not None:
                query_kwargs["user_prompt"] = param.user_prompt
            if getattr(param, "include_references", None) is not None:
                query_kwargs["include_references"] = param.include_references
            if getattr(param, "conversation_history", None) is not None:
                query_kwargs["conversation_history"] = param.conversation_history
            if getattr(param, "history_turns", None) is not None:
                query_kwargs["history_turns"] = param.history_turns

            # VLM: Only enable for explicit image/figure queries (avoids unnecessary cost)
            if _should_enable_vlm(request.query):
                query_kwargs["vlm_enhanced"] = True

            result = await rag_instance.aquery(request.query, mode=param.mode, **query_kwargs)

            async def stream_generator():
                # LightRAG API expects references in first chunk, but RAG-Anything returns only text.
                # We still emit an empty references list when requested so the client schema is stable;
                # the model is instructed to include a '### References' section in the text output.
                if request.include_references:
                    yield f"{json.dumps({'references': []})}\n"

                if hasattr(result, "__aiter__"):
                    async for chunk in result:
                        if chunk:
                            yield f"{json.dumps({'response': chunk})}\n"
                else:
                    response_content = result or "No relevant context found for the query."
                    yield f"{json.dumps({'response': response_content})}\n"

            return StreamingResponse(
                stream_generator(),
                media_type="application/x-ndjson",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "application/x-ndjson",
                    "X-Accel-Buffering": "no",
                },
            )
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    app.add_api_route(
        "/query/stream",
        query_stream_override,
        methods=["POST"],
    )


def create_graphs_endpoint(app, rag_instance) -> None:
    """
    Override LightRAG's /graphs endpoint to avoid FastAPI serialization errors when using Neo4j storage.

    LightRAG can return neo4j.time.DateTime (and other temporal types) in node/edge properties,
    which FastAPI/Pydantic cannot serialize by default, causing a 500 on WebUI refresh.
    """

    async def graphs_override(
        label: str,
        max_depth: int = 3,
        max_nodes: int = 1000,
    ):
        try:
            # LightRAG server uses rag.get_knowledge_graph(node_label=..., ...)
            result = await rag_instance.lightrag.get_knowledge_graph(
                node_label=label,
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
            return _json_safe(result)
        except Exception as e:
            logger.error("Graphs query failed: %s", e)
            return JSONResponse({"error": str(e)}, status_code=500)

    app.add_api_route(
        "/graphs",
        graphs_override,
        methods=["GET"],
    )

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

# NOTE: extract_with_semaphore() and extract_multimodal_with_semaphore() were removed
# in Issue #42. The lightrag_llm_adapter now intercepts ALL LightRAG extraction calls,
# providing unified Pydantic validation with the full 121K ontology prompt.
# RAG-Anything's native parallelization handles concurrency.


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
        
        # ============================================================================
        # RAG-ANYTHING PIPELINE WITH GOVCON ONTOLOGY
        # ============================================================================
        # Issue #42: RAG-Anything handles ALL content with unified extraction
        # - Text → LightRAG's text pipeline → lightrag_llm_adapter (Pydantic + ontology)
        # - Tables → OntologyTableProcessor → preserves structure → adapter extracts
        # - Images/equations → default processors → adapter extracts
        # 
        # Issue #46 Part C: OntologyTableProcessor registered for tables
        # - Preserves table structure (headers, rows, cells)
        # - Detects table type (eval matrix, CDRL, labor, compliance)
        # - Adds extraction hints for lightrag_llm_adapter
        # - NO duplicate extraction - processor formats, adapter extracts
        # ============================================================================
        
        import os
        
        # Issue #46: Register OntologyTableProcessor for structured table extraction
        # Tables contain critical GovCon data that benefits from structure preservation
        try:
            from src.processors import OntologyTableProcessor
            
            table_processor = OntologyTableProcessor(
                lightrag=rag_instance.lightrag,
                modal_caption_func=rag_instance.llm_model_func,
                context_extractor=getattr(rag_instance, 'context_extractor', None)
            )
            rag_instance.modal_processors["table"] = table_processor
            logger.info("📊 Registered OntologyTableProcessor for structured table extraction")
        except Exception as e:
            logger.warning(f"⚠️ Could not register OntologyTableProcessor: {e} - using default")
        
        try:
            # Count content types for logging
            text_count = sum(1 for item in filtered_content if item.get('type') == 'text')
            table_count = sum(1 for item in filtered_content if item.get('type') == 'table')
            image_count = sum(1 for item in filtered_content if item.get('type') == 'image')
            equation_count = sum(1 for item in filtered_content if item.get('type') == 'equation')
            
            logger.info(f"📊 Content breakdown: {text_count} text, {table_count} tables, {image_count} images, {equation_count} equations")
            
            # RAG-Anything handles ALL content in one call:
            # - Text items → LightRAG's ainsert() → lightrag_llm_adapter → Pydantic extraction
            # - Tables → OntologyTableProcessor → structured format → adapter extracts
            # - Images/equations → default processors → adapter extracts
            # - Deduplication → LightRAG's merge_nodes_and_edges() (Stage 6)
            logger.info(f"🚀 Processing {len(filtered_content)} content items through RAG-Anything pipeline...")
            
            await rag_instance.insert_content_list(
                content_list=filtered_content,
                file_path=file_name,  # Clean filename for citations
                doc_id=doc_id
            )
            
            logger.info("✅ RAG-Anything pipeline complete (unified extraction via lightrag_llm_adapter)")
            
            # Log queue status
            stats = await _queue_tracker.get_stats()
            if _queue_tracker.last_completion_time:
                time_since = (datetime.now() - _queue_tracker.last_completion_time).total_seconds()
                logger.info(f"⏭️  Document added to batch | Queue: {stats['processing']} processing, {stats['completed']} completed | {time_since:.0f}s since last completion (timeout: {_queue_tracker.batch_timeout_seconds}s)")
            else:
                logger.info(f"⏭️  Document added to batch | Queue: {stats['processing']} processing, {stats['completed']} completed")
            
            return {
                "status": "success",
                "content_processed": {
                    "text": text_count,
                    "tables": table_count,
                    "images": image_count,
                    "equations": equation_count
                },
                "message": "✅ Document processed. Enhancement will run automatically when batch completes."
            }
            
        except Exception as e:
            logger.error(f"❌ RAG-Anything pipeline failed: {e}")
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
