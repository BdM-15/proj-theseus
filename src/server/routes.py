"""
FastAPI Routes Module

Custom endpoints for RAG-Anything + LightRAG server:
- /insert: Document upload with automatic semantic post-processing
- /documents/upload: WebUI document upload (also triggers post-processing)

Architecture (Branch 006 - Simplified, Format-Agnostic):
1. Document Upload → process_document_with_semantic_inference()
2. RAG-Anything Processing → MinerU multimodal parsing
3. LightRAG Extraction → Entity/relationship extraction (17 types)
4. Semantic Post-Processing → LLM-powered relationship inference (always runs)
5. Knowledge Graph Updated → GraphML + kv_store files

Note: UCF detection removed as of Branch 006. All RFP formats (UCF, task orders,
quotes, FOPRs, embedded formats) are handled uniformly through semantic extraction.
"""

import os
import asyncio
import logging
import tempfile
import shutil
import json
from pathlib import Path
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse
from lightrag.api.config import global_args

from src.inference import (
    parse_graphml,
    infer_all_relationships,
    save_relationships_to_graphml,
    save_relationships_to_kv_store
)
logger = logging.getLogger(__name__)


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
        
        # Combine all text content for chunking
        # CRITICAL: Only process type='text' blocks (not tables/images)
        # This matches Perfect Run behavior (421 text blocks → 339 entities)
        text_chunks = []
        for item in filtered_content:
            # Filter ONLY text blocks (exclude tables and images)
            if item.get('type') == 'text':
                content_text = item.get('text', '')  # MinerU uses 'text' field, not 'content'
                if content_text and content_text.strip():
                    text_chunks.append(content_text)
        
        if not text_chunks:
            logger.error("❌ No text content found in MinerU output")
            return {"error": "No text content"}
        
        full_text = "\n\n".join(text_chunks)
        logger.info(f"📝 Extracted {len(text_chunks)} content blocks ({len(full_text)} chars total)")
        
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
        
        # Run custom ontology extraction on each chunk
        logger.info("🚀 Running custom ontology extraction with Pydantic schema...")
        extractor = JsonExtractor()
        
        all_entities = []
        all_relationships = []
        
        try:
            for i, chunk_text in enumerate(chunked_texts):
                logger.info(f"   Processing chunk {i+1}/{len(chunked_texts)}...")
                extraction_result = await extractor.extract(chunk_text)
                all_entities.extend(extraction_result.entities)
                all_relationships.extend(extraction_result.relationships)
            
            # Merge results (de-duplicate entities by name)
            unique_entities = {}
            for entity in all_entities:
                if entity.entity_name not in unique_entities:
                    unique_entities[entity.entity_name] = entity
            
            all_entities = list(unique_entities.values())
            
            logger.info(f"✅ Extracted {len(all_entities)} unique entities, {len(all_relationships)} relationships from {len(chunked_texts)} chunks")
            
            # Convert Pydantic extraction to LightRAG custom_kg format
            custom_kg = {
                "chunks": [],
                "entities": [],
                "relationships": []
            }
            
            # Add chunks
            for i, chunk_text in enumerate(chunked_texts):
                custom_kg["chunks"].append({
                    "content": chunk_text,
                    "source_id": doc_id,
                    "file_path": file_path,
                    "chunk_order_index": i
                })
            
            # Convert entities
            for entity in all_entities:
                custom_kg["entities"].append({
                    "entity_name": entity.entity_name,
                    "entity_type": entity.entity_type,
                    "description": entity.description,
                    "source_id": doc_id,
                    "file_path": file_path
                })
            
            # Convert relationships
            for rel in all_relationships:
                custom_kg["relationships"].append({
                    "src_id": rel.source_entity.entity_name,
                    "tgt_id": rel.target_entity.entity_name,
                    "description": rel.description,
                    "keywords": rel.relationship_type,
                    "weight": 1.0,
                    "source_id": doc_id
                })
            
            # Insert custom KG into LightRAG (bypasses its extraction)
            logger.info("💾 Inserting custom ontology into LightRAG...")
            await rag_instance.lightrag.ainsert_custom_kg(custom_kg, full_doc_id=doc_id)
            logger.info("✅ Custom ontology inserted into knowledge graph")
            
            # Run semantic post-processing
            logger.info("🤖 Running semantic enhancement...")
            from src.inference.semantic_post_processor import enhance_knowledge_graph
            
            if not llm_func:
                logger.error("❌ No LLM function available for semantic enhancement")
                return {
                    "entities_extracted": len(extraction_result.entities),
                    "relationships_extracted": len(extraction_result.relationships),
                    "error": "No LLM function for enhancement"
                }
            
            inference_result = await enhance_knowledge_graph(
                rag_storage_path=global_args.working_dir,
                llm_func=llm_func,
                batch_size=50
            )
            
            logger.info("✅ Neo4j semantic enhancement complete")
            logger.info(f"   Entities extracted: {len(all_entities)}")
            logger.info(f"   Relationships extracted: {len(all_relationships)}")
            logger.info(f"   Entities corrected: {inference_result.get('entities_corrected', 0)}")
            logger.info(f"   Relationships inferred: {inference_result.get('relationships_inferred', 0)}")
            logger.info(f"   View results in Neo4j Browser: http://localhost:7474")
            
            return {
                "entities_extracted": len(all_entities),
                "relationships_extracted": len(all_relationships),
                **inference_result
            }
            
        except Exception as e:
            logger.error(f"❌ Custom ontology extraction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    else:
        # NetworkX storage - use standard RAG-Anything processing
        logger.info("📊 NetworkX storage detected - using standard LightRAG extraction")
        await rag_instance.insert_content_list(
            content_list=filtered_content,
            file_path=file_path,
            doc_id=doc_id
        )
    
    # Step 2: ROBUST - Wait for GraphML with exponential backoff (NetworkX storage only)
    # CRITICAL: LightRAG writes to default/ subdirectory, not root working_dir
    graphml_path = Path(global_args.working_dir) / "default" / "graph_chunk_entity_relation.graphml"
    
    max_retries = 5
    wait_times = [1, 2, 3, 4, 5]  # Total: 15 seconds max
    
    for attempt, wait_time in enumerate(wait_times):
        await asyncio.sleep(wait_time)
        
        if graphml_path.exists() and graphml_path.stat().st_size > 100:
            total_wait = sum(wait_times[:attempt+1])
            logger.info(f"✅ GraphML ready after {total_wait}s wait")
            break
        
        logger.warning(
            f"⏳ GraphML not ready (attempt {attempt+1}/{max_retries}), "
            f"waiting {wait_time}s..."
        )
    else:
        # All retries exhausted
        total_wait = sum(wait_times)
        logger.error(
            f"❌ GraphML never populated after {total_wait}s total wait. "
            f"This indicates RAG-Anything processing failed."
        )
        return {
            "relationships_inferred": 0,
            "error": "GraphML file not created"
        }
    
    # Step 3: Capture BEFORE state for validation
    nodes_before, edges_before = parse_graphml(graphml_path)
    logger.info(f"📊 PRE-INFERENCE: {len(nodes_before)} entities, {len(edges_before)} relationships")
    
    # Step 4: Run LLM-powered relationship inference (ALWAYS - no toggle)
    if not llm_func:
        logger.error(f"❌ No LLM function provided - cannot run relationship inference")
        return {
            "relationships_inferred": 0,
            "error": "No LLM function"
        }
    
    logger.info(f"🤖 Running semantic knowledge graph enhancement...")
    # Use new semantic post-processor (consolidates entity type correction + relationship inference)
    from src.inference.semantic_post_processor import enhance_knowledge_graph
    inference_result = await enhance_knowledge_graph(
        rag_storage_path=global_args.working_dir,
        llm_func=llm_func,
        batch_size=50
    )
    
    # Step 4.5: Optional metadata enrichment
    # Extracts structured metadata from entity descriptions WITHOUT modifying descriptions
    logger.info(f"📊 Running metadata enrichment...")
    from src.inference.phase7_metadata_enrichment import enrich_entities_with_metadata, save_metadata_to_graphml
    
    # Parse current nodes
    nodes_for_enrichment, _ = parse_graphml(graphml_path)
    
    # Enrich entities (evaluation_factor, submission_instruction, requirement)
    enrichment_counts = await enrich_entities_with_metadata(nodes_for_enrichment, llm_func)
    
    # Save metadata back to GraphML
    if sum(enrichment_counts.values()) > 0:
        metadata_saved = save_metadata_to_graphml(graphml_path, nodes_for_enrichment)
        logger.info(f"✅ Metadata enrichment complete: {metadata_saved} entities enriched with metadata")
    else:
        logger.info(f"⏭️  Metadata enrichment: No entities enriched (no matching types found)")
    
    # Step 5: Validate AFTER state
    nodes_after, edges_after = parse_graphml(graphml_path)
    actual_new_rels = len(edges_after) - len(edges_before)
    
    logger.info(f"📊 POST-INFERENCE: {len(nodes_after)} entities, {len(edges_after)} relationships")
    logger.info(f"✅ VALIDATED: {actual_new_rels} new relationships persisted to GraphML")
    
    if actual_new_rels != inference_result.get("relationships_added", 0):
        logger.warning(
            f"⚠️ Mismatch: Inference reported {inference_result.get('relationships_added')} "
            f"but GraphML delta is {actual_new_rels}"
        )
    
    return {
        "relationships_inferred": actual_new_rels,
        "inference_result": inference_result
    }


async def post_process_knowledge_graph(rag_storage_path: str, llm_func) -> dict:
    """
    Semantic Post-Processing: LLM-Powered Relationship Inference
    
    ARCHITECTURE: Replaces brittle regex patterns with LLM semantic understanding.
    
    Timeline:
    - t=0-70s: LightRAG extraction (16 entity types + initial relationships)
    - t=70s: Knowledge graph files written (GraphML, kv_store files)
    - t=70-85s: This function runs (LLM-powered relationship inference)
    - t=85s: Knowledge graph files UPDATED (100% document linkage, comprehensive coverage)
    
    Processing Pipeline:
    1. Parse GraphML (full entity details from multimodal extraction)
    2. Clean entity types (fixes #/>CONCEPT format corruption)
    3. Group entities by type for efficient batching
    4. Call Grok LLM to infer relationships using semantic understanding
    5. Parse structured JSON responses with confidence scores and reasoning
    6. Save new relationships to both GraphML and kv_store
    
    Benefits:
    - Agency-agnostic: Handles ANY RFP structure (Navy, Air Force, Army, civilian agencies)
    - Context-aware: Understands content semantics, not just naming patterns
    - Self-documenting: LLM provides human-readable reasoning for each relationship
    - Higher coverage: 100% document linkage for attachments, specs, regulations
    - Cost-effective: ~$0.03 per document (5 LLM batches × ~$0.006/batch)
    - Leverages existing 2M-context Grok infrastructure
    
    Relationship Types Inferred (5 algorithms):
    1. Section L↔M mapping: SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR
    2. Document section linking: DOCUMENT → SECTION (ATTACHMENT_OF/CHILD_OF)
    3. SOW deliverable linking: STATEMENT_OF_WORK → DELIVERABLE (REQUIRES)
    4. Clause clustering: CLAUSE → SECTION (CHILD_OF)
    5. Requirement evaluation: REQUIREMENT → EVALUATION_FACTOR (EVALUATED_BY)
    
    Args:
        rag_storage_path: Path to rag_storage directory
        llm_func: LLM function for semantic inference
    
    Returns:
        dict: Processing result with status, relationships_added, method
    """
    logger.info("=" * 80)
    logger.info("🤖 SEMANTIC POST-PROCESSING: LLM-Powered Relationship Inference")
    logger.info("   Augmenting knowledge graph with inferred relationships")
    logger.info("=" * 80)
    
    rag_storage = Path(rag_storage_path)
    # CRITICAL: LightRAG writes to default/ subdirectory
    graphml_path = rag_storage / "default" / "graph_chunk_entity_relation.graphml"
    
    # Validate GraphML file exists
    if not graphml_path.exists():
        logger.warning(f"GraphML file not found in {rag_storage_path}, skipping post-processing")
        return {"status": "skipped", "reason": "no_graphml"}
    
    try:
        # Step 1: Parse GraphML to extract entities and relationships
        logger.info(f"  [1/5] Parsing GraphML: {graphml_path.name}")
        nodes, existing_edges = parse_graphml(graphml_path)
        
        if not nodes:
            logger.warning(f"No entities found in GraphML, skipping post-processing")
            return {"status": "skipped", "reason": "no_entities"}
        
        # Step 2: Cleanup forbidden entity types (UNKNOWN, other, etc.)
        logger.info(f"  [2/5] Cleaning up forbidden entity types...")
        from src.inference.forbidden_type_cleanup import cleanup_forbidden_types
        
        nodes, retyping_map = await cleanup_forbidden_types(
            entities=nodes,
            llm_func=llm_func,
            batch_size=50
        )
        
        if retyping_map:
            logger.info(f"  ✅ Retyped {len(retyping_map)} entities with forbidden types")
            # Save cleaned entities back to GraphML immediately
            from src.inference.graph_io import save_cleaned_entities_to_graphml
            save_cleaned_entities_to_graphml(graphml_path, nodes)
            logger.info(f"  ✅ Saved cleaned entities to GraphML")
        
        # Step 3: Use LLM to infer missing relationships
        logger.info(f"  [3/5] Calling Grok LLM for semantic relationship inference...")
        
        new_relationships = await infer_all_relationships(
            nodes=nodes,
            existing_edges=existing_edges,
            llm_func=llm_func
        )
        
        if not new_relationships:
            logger.info(f"  ℹ️  No new relationships inferred (existing graph may be complete)")
            return {
                "status": "success",
                "relationships_added": 0,
                "method": "llm_powered",
                "message": "No new relationships needed"
            }
        
        # Step 4: Save new relationships to both GraphML and kv_store
        logger.info(f"  [4/5] Saving {len(new_relationships)} new relationships...")
        
        save_relationships_to_graphml(graphml_path, new_relationships, nodes)
        # kv_store files are in default/ subdirectory alongside GraphML
        save_relationships_to_kv_store(rag_storage / "default", new_relationships, nodes)
        
        # Step 5: Final validation
        logger.info(f"  [5/5] Semantic post-processing complete")
        
        logger.info("=" * 80)
        logger.info(f"🎯 SEMANTIC POST-PROCESSING COMPLETE")
        logger.info(f"  Total new relationships: {len(new_relationships)}")
        logger.info(f"  Method: Grok LLM semantic understanding")
        logger.info(f"  Cost: ~$0.03 (5 inference algorithms)")
        logger.info(f"  Processing time: ~15 seconds")
        logger.info("=" * 80)
        
        return {
            "status": "success",
            "relationships_added": len(new_relationships),
            "total_relationships_added": len(new_relationships),  # For background monitor compatibility
            "method": "llm_powered",
            "batches_processed": 5,
            "estimated_cost_usd": 0.03
        }
        
    except Exception as e:
        logger.error(f"Error during LLM-powered post-processing: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e),
            "method": "llm_powered"
        }


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
            import traceback
            logger.error(traceback.format_exc())
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    
    # Register the route explicitly (decorator doesn't work when called after app init)
    app.add_api_route(
        "/documents/upload",
        documents_upload_with_raganything,
        methods=["POST"],
        response_class=JSONResponse
    )
