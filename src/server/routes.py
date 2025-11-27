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
            
            # Initialize extractors
            json_extractor = JsonExtractor()
            # Note: llm_func is passed as parameter to this function
            
            # PHASE 1: TEXT EXTRACTION (for custom ontology extraction)
            text_chunks = []
            for item in filtered_content:
                # Filter ONLY text blocks (tables/images handled by RAG-Anything processors)
                if item.get('type') == 'text':
                    content_text = item.get('text', '')  # MinerU uses 'text' field, not 'content'
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
                text_entity_count = 0
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
        
        # PHASE 2: CUSTOM ONTOLOGY EXTRACTION (text only - tables handled by processor)
        logger.info("🚀 Running custom ontology extraction with Pydantic schema (TEXT)...")
        
        all_entities = []
        all_relationships = []
        
        try:
            for i, chunk_text in enumerate(chunked_texts):
                logger.info(f"   Processing text chunk {i+1}/{len(chunked_texts)}...")
                extraction_result = await json_extractor.extract(chunk_text)
                all_entities.extend(extraction_result.entities)
                all_relationships.extend(extraction_result.relationships)
            
            # De-duplicate entities by name
            unique_entities = {}
            for entity in all_entities:
                if entity.entity_name not in unique_entities:
                    unique_entities[entity.entity_name] = entity
            
            all_entities = list(unique_entities.values())
            
            logger.info(
                f"✅ TEXT EXTRACTION: "
                f"{len(all_entities)} unique entities, "
                f"{len(all_relationships)} relationships "
                f"from {len(chunked_texts)} text chunks"
            )
            
            # Convert Pydantic extraction to LightRAG custom_kg format
            custom_kg = {
                "chunks": [],
                "entities": [],
                "relationships": []
            }
            
            # Convert text chunks only (tables handled by RAG-Anything's modal processors)
            # NOTE: Use file_name (clean filename) not file_path (temp path) for citations
            for i, chunk_text in enumerate(chunked_texts):
                custom_kg["chunks"].append({
                    "content": chunk_text,
                    "source_id": doc_id,
                    "file_path": file_name,
                    "chunk_order_index": i
                })
            
            # Convert entities from text extraction
            for entity in all_entities:
                custom_kg["entities"].append({
                    "entity_name": entity.entity_name,
                    "entity_type": entity.entity_type,
                    "description": entity.entity_name,  # Use entity_name for embedding - full text is in chunks
                    "source_id": doc_id,
                    "file_path": file_name
                })
            
            # Convert relationships
            for rel in all_relationships:
                custom_kg["relationships"].append({
                    "src_id": rel.source_entity.entity_name,
                    "tgt_id": rel.target_entity.entity_name,
                    "description": rel.relationship_type,  # Use relationship_type as description
                    "keywords": rel.relationship_type,
                    "weight": 1.0,
                    "source_id": doc_id
                })
            
            # PHASE 3: PROCESS MULTIMODAL CONTENT (tables, images) with custom processor
            logger.info("📊 Registering GovconMultimodalProcessor for tables/images/equations...")
            
            # Create custom processor instance
            govcon_processor = GovconMultimodalProcessor(
                lightrag=rag_instance.lightrag,
                modal_caption_func=llm_func,
                context_extractor=rag_instance.context_extractor
            )
            
            # Override RAG-Anything's default processors with our ontology-aware processor
            rag_instance.modal_processors["table"] = govcon_processor
            rag_instance.modal_processors["image"] = govcon_processor
            rag_instance.modal_processors["equation"] = govcon_processor
            
            logger.info("✅ Custom processors registered")
            
            # Insert text entities + process multimodal content
            logger.info("💾 Inserting custom text ontology and processing multimodal content...")
            await rag_instance.lightrag.ainsert_custom_kg(custom_kg, full_doc_id=doc_id)
            
            # Process multimodal content (tables, images) through RAG-Anything pipeline
            # This will use our GovconMultimodalProcessor for entity extraction
            multimodal_items = [item for item in filtered_content if item.get('type') in ['table', 'image', 'equation']]
            if multimodal_items:
                logger.info(f"📊 Processing {len(multimodal_items)} multimodal items with govcon ontology...")
                await rag_instance.insert_content_list(
                    content_list=multimodal_items,
                    file_path=file_name,  # Use clean filename for citations, not temp path
                    doc_id=doc_id
                )
                logger.info("✅ Multimodal content processed")
            
            logger.info("✅ Complete knowledge graph inserted")
            
            # Log queue status
            stats = await _queue_tracker.get_stats()
            if _queue_tracker.last_completion_time:
                time_since = (datetime.now() - _queue_tracker.last_completion_time).total_seconds()
                logger.info(f"⏭️  Document added to batch | Queue: {stats['processing']} processing, {stats['completed']} completed | {time_since:.0f}s since last completion (timeout: {_queue_tracker.batch_timeout_seconds}s)")
            else:
                logger.info(f"⏭️  Document added to batch | Queue: {stats['processing']} processing, {stats['completed']} completed")
            
            return {
                "entities_extracted": len(all_entities),
                "relationships_extracted": len(all_relationships),
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
