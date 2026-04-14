"""
FastAPI Routes Module

Custom endpoints for RAG-Anything + LightRAG server:
- /insert: Document upload with automatic semantic post-processing
- /documents/upload: WebUI document upload (also triggers post-processing)

Architecture:
1. Document Upload → process_document_with_semantic_inference()
2. RAG-Anything Processing → MinerU multimodal parsing
3. Native LightRAG Extraction → Entity/relationship extraction (18 types)
4. GovConProcessingCallback → Detects batch completion via RAG-Anything callbacks
5. Auto-Enhancement → Semantic post-processing runs ONCE after last document
"""

import os
import asyncio
import logging
import tempfile
import shutil
import threading
from datetime import datetime
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse
from lightrag.api.config import global_args
from raganything.callbacks import ProcessingCallback

from src.core import get_settings

logger = logging.getLogger(__name__)


# ============================================================================
# BATCH PROCESSING CALLBACK (RAG-Anything ProcessingCallback)
# ============================================================================
# Replaces the polling-based DocumentQueueTracker with event-driven callbacks.
# Batch completion is detected via a timeout timer that resets on each document
# completion event — no asyncio.sleep polling loop.

class GovConProcessingCallback(ProcessingCallback):
    """
    Callback handler for batch document processing with auto-enhancement.
    
    Tracks document lifecycle and triggers semantic post-processing when a 
    batch completes (no new documents within timeout window).
    """
    
    def __init__(self):
        settings = get_settings()
        self.batch_timeout_seconds = settings.batch_timeout_seconds
        self.pending_uploads: set[str] = set()
        self.processing_docs: set[str] = set()
        self.completed_docs: set[str] = set()
        self.last_completion_time: datetime | None = None
        self.enhancement_pending = False
        self.enhancement_running = False
        self.lock = threading.Lock()
        self._batch_timer: asyncio.TimerHandle | None = None
        self._llm_func = None  # Set during initialization
    
    def set_llm_func(self, llm_func):
        """Set the LLM function for post-processing (called during server init)."""
        self._llm_func = llm_func
    
    async def register_request_start(self, filename: str):
        """Register that an upload request has started (HTTP layer)."""
        with self.lock:
            self.pending_uploads.add(filename)
            self.enhancement_pending = True
            self._cancel_batch_timer()
            logger.info(f"📥 Upload request started: {filename} (pending: {len(self.pending_uploads)})")

    async def register_request_end(self, filename: str):
        """Register that an upload request has finished (HTTP layer)."""
        with self.lock:
            self.pending_uploads.discard(filename)
            logger.info(f"🏁 Upload request finished: {filename} (pending: {len(self.pending_uploads)})")

    # --- RAG-Anything ProcessingCallback overrides ---
    
    def on_document_complete(self, file_path: str, doc_id: str = '', 
                              duration_seconds: float = 0.0, **kwargs):
        """Called when a document finishes processing (sync — called by dispatch)."""
        with self.lock:
            self.processing_docs.discard(doc_id)
            self.completed_docs.add(doc_id)
            self.last_completion_time = datetime.now()
            logger.info(f"✅ Document completed: {doc_id} ({duration_seconds:.1f}s, "
                        f"queue: {len(self.processing_docs)} remaining)")
            self._schedule_batch_check()

    def on_parse_complete(self, file_path: str, content_blocks: int = 0,
                           doc_id: str = '', duration_seconds: float = 0.0, **kwargs):
        """Called when MinerU parsing completes (sync — called by dispatch)."""
        with self.lock:
            self.processing_docs.add(doc_id)
            logger.info(f"⚙️ Parse complete: {doc_id} ({content_blocks} blocks, {duration_seconds:.1f}s)")

    def on_document_error(self, file_path: str, error: str = '',
                           doc_id: str = '', **kwargs):
        """Called when document processing fails (sync — called by dispatch)."""
        with self.lock:
            self.processing_docs.discard(doc_id)
            self.completed_docs.add(doc_id)  # Count as completed to not block batch
            self.last_completion_time = datetime.now()
            logger.error(f"❌ Document error: {doc_id} - {error}")
            self._schedule_batch_check()

    # --- Batch completion detection ---

    def _cancel_batch_timer(self):
        """Cancel any pending batch completion timer."""
        if self._batch_timer is not None:
            self._batch_timer.cancel()
            self._batch_timer = None

    def _schedule_batch_check(self):
        """Schedule a batch completion check after timeout. Resets on each call."""
        self._cancel_batch_timer()
        loop = asyncio.get_event_loop()
        self._batch_timer = loop.call_later(
            self.batch_timeout_seconds,
            lambda: asyncio.ensure_future(self._check_batch_complete())
        )

    async def _check_batch_complete(self):
        """Check if batch is complete and trigger enhancement."""
        settings = get_settings()
        with self.lock:
            if (
                len(self.pending_uploads) == 0
                and len(self.processing_docs) == 0
                and len(self.completed_docs) > 0
                and self.enhancement_pending
                and not self.enhancement_running
            ):
                self.enhancement_running = True
            else:
                return

        doc_count = len(self.completed_docs)

        if not settings.enable_post_processing:
            logger.info(f"🎯 BATCH COMPLETE - {doc_count} documents, "
                         f"{self.batch_timeout_seconds}s idle")
            logger.info("⏭️ Post-processing DISABLED (ENABLE_POST_PROCESSING=false). "
                         "Skipping semantic enhancement.")
            with self.lock:
                self.completed_docs.clear()
                self.enhancement_pending = False
                self.enhancement_running = False
            return

        # Run enhancement outside the lock (async from here)
        logger.info(f"🎯 BATCH COMPLETE - {doc_count} documents, "
                     f"{self.batch_timeout_seconds}s idle")
        
        try:
            from src.inference.semantic_post_processor import enhance_knowledge_graph
            
            inference_result = await enhance_knowledge_graph(
                rag_storage_path=global_args.working_dir,
                llm_func=self._llm_func,
                batch_size=50
            )
            
            logger.info("✅ Cumulative semantic enhancement complete")
            logger.info(f"   Entities corrected: {inference_result.get('entities_corrected', 0)}")
            logger.info(f"   Relationships inferred: {inference_result.get('relationships_inferred', 0)}")
            logger.info(f"   View results in Neo4j Browser: http://localhost:7474")
            
        except Exception as e:
            logger.error(f"❌ Batch enhancement failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        finally:
            with self.lock:
                self.completed_docs.clear()
                self.enhancement_pending = False
                self.enhancement_running = False
                logger.info("🔄 Batch state reset - ready for next upload batch")

    async def get_stats(self) -> dict:
        """Get current queue statistics."""
        with self.lock:
            return {
                "pending_uploads": len(self.pending_uploads),
                "processing": len(self.processing_docs),
                "completed": len(self.completed_docs),
                "enhancement_pending": self.enhancement_pending,
                "enhancement_running": self.enhancement_running,
            }

# Global callback instance
_callback = GovConProcessingCallback()


def get_processing_callback() -> GovConProcessingCallback:
    """Get the global processing callback (for registration in initialization.py)."""
    return _callback


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
    3. Semantic post-processing - Auto-triggered on batch completion via callback
    """
    logger.info(f"📄 Processing {file_name}")
    
    settings = get_settings()
    mineru_backend = settings.mineru_backend
    
    start_time = datetime.now()
    
    content_list, doc_id = await rag_instance.parse_document(
        file_path=file_path,
        output_dir=global_args.working_dir,
        parse_method="auto",
        backend=mineru_backend
    )
    
    parse_duration = (datetime.now() - start_time).total_seconds()
    
    # Dispatch parse_complete event (sync — dispatch calls handlers synchronously)
    rag_instance.callback_manager.dispatch(
        "on_parse_complete",
        file_path=file_path,
        content_blocks=len(content_list),
        doc_id=doc_id,
        duration_seconds=parse_duration
    )
    
    try:
        # Filter out MinerU discarded content types
        DISCARDED_TYPES = {
            "discarded", "header", "footer", "page_number",
            "aside_text", "page_footnote",
        }
        
        original_count = len(content_list)
        filtered_content = [
            item for item in content_list
            if item.get("type") not in DISCARDED_TYPES
        ]
        discarded_count = original_count - len(filtered_content)
        
        if discarded_count > 0:
            logger.info(f"🚫 Filtered {discarded_count} discarded content blocks "
                        f"(keeping {len(filtered_content)}/{original_count})")
        
        llm_timeout = settings.llm_timeout
        logger.info("🚀 Using RAG-Anything native end-to-end pipeline")
        logger.info(f"   Ontology: 18 govcon entity types | Timeout: {llm_timeout}s")
        
        workspace = settings.workspace
        output_dir = os.path.join(global_args.working_dir, workspace)
        
        await rag_instance.insert_content_list(
            content_list=filtered_content,
            file_path=file_path,
            doc_id=doc_id
        )
        
        total_duration = (datetime.now() - start_time).total_seconds()
        logger.info("✅ RAG-Anything processing complete")
        
        # Dispatch document_complete event — triggers batch detection (sync)
        rag_instance.callback_manager.dispatch(
            "on_document_complete",
            file_path=file_path,
            doc_id=doc_id,
            duration_seconds=total_duration
        )
        
        stats = await _callback.get_stats()
        logger.info(f"⏭️  Queue: {stats['processing']} processing, {stats['completed']} completed")
        
        return {
            "status": "success",
            "relationships_inferred": 0,
            "method": "native_rag_anything",
            "message": "✅ Document processed via RAG-Anything native pipeline.",
        }
    
    except Exception as e:
        # Dispatch error event so batch detection still works (sync)
        rag_instance.callback_manager.dispatch(
            "on_document_error",
            file_path=file_path,
            doc_id=doc_id,
            error=str(e)
        )
        raise


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
        
        await _callback.register_request_start(file.filename)
        
        try:
            temp_dir = tempfile.gettempdir()
            safe_filename = file.filename.replace('/', '_').replace('\\', '_')
            file_path = os.path.join(temp_dir, safe_filename)
            
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file.file, f)
            
            logger.info(f"📄 Processing {file.filename} via /insert endpoint")
            
            processing_result = await process_document_with_semantic_inference(
                file_path, file.filename, rag_instance, rag_instance.llm_model_func
            )
            
            logger.info(f"✅ Processing complete for {file.filename}")
            
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
            await _callback.register_request_end(file.filename)
    
    app.add_api_route(
        "/insert",
        insert_with_semantic_processing,
        methods=["POST"],
        response_class=JSONResponse
    )


def create_documents_upload_endpoint(app, rag_instance):
    """
    Override LightRAG's WebUI /documents/upload endpoint to use RAG-Anything.
    
    WebUI uses /documents/upload (not /insert), which would bypass
    RAG-Anything's multimodal processing without this override.
    """
    
    async def documents_upload_with_raganything(file: UploadFile = File(...)):
        """WebUI document upload - routes through RAG-Anything for MinerU processing."""
        logger.info(f"🔔 ENDPOINT CALLED: /documents/upload with file: {file.filename}")
        
        await _callback.register_request_start(file.filename)
        
        try:
            temp_dir = tempfile.gettempdir()
            safe_filename = file.filename.replace('/', '_').replace('\\', '_')
            file_path = os.path.join(temp_dir, safe_filename)
            
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file.file, f)
            
            logger.info(f"📄 Processing {file.filename} via WebUI /documents/upload endpoint")
            
            processing_result = await process_document_with_semantic_inference(
                file_path, file.filename, rag_instance, rag_instance.llm_model_func
            )
            
            logger.info(f"✅ Processing complete for {file.filename}")
            
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
            await _callback.register_request_end(file.filename)
    
    app.add_api_route(
        "/documents/upload",
        documents_upload_with_raganything,
        methods=["POST"],
        response_class=JSONResponse
    )


