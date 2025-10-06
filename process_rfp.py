"""
Navy MBOS RFP Processing Script using RAG-Anything

This script processes RFP documents using RAG-Anything with multimodal capabilities.
It shares the same ./rag_storage with the LightRAG server, so processed documents
appear in the WebUI immediately.

Usage:
    python process_rfp.py <path_to_rfp.pdf>
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import RAG-Anything components
from raganything import RAGAnything, RAGAnythingConfig
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc


async def process_rfp(file_path: str):
    """
    Process an RFP document using RAG-Anything following the official example pattern.
    
    Args:
        file_path: Path to RFP PDF file
    """
    print("\n" + "="*80)
    print(" Navy MBOS RFP Processing with RAG-Anything")
    print("="*80)
    
    # Validate file exists
    if not Path(file_path).exists():
        print(f"\n❌ Error: File not found: {file_path}")
        return
    
    print(f"\n📄 Processing: {file_path}")
    print(f"📁 Storage: ./rag_storage (shared with LightRAG server)")
    
    # Get API credentials (using RAG-Anything official variable names)
    xai_api_key = os.getenv("LLM_BINDING_API_KEY")
    xai_base_url = os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
    openai_api_key = os.getenv("EMBEDDING_BINDING_API_KEY")
    
    if not xai_api_key or not openai_api_key:
        print("\n❌ Error: Missing API keys in .env file")
        print("   Required: LLM_BINDING_API_KEY and EMBEDDING_BINDING_API_KEY")
        return
    
    print("\n🔧 Initializing RAG-Anything with govcon configuration...")
    
    # Create RAGAnything configuration (following official example)
    config = RAGAnythingConfig(
        working_dir="./rag_storage",
        parser="mineru",  # Use MinerU for multimodal parsing
        parse_method="auto",  # Auto-detect best parsing method
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
    )
    
    # Define LLM model function for xAI Grok
    def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        return openai_complete_if_cache(
            "grok-4-fast-reasoning",
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=xai_api_key,
            base_url=xai_base_url,
            **kwargs,
        )
    
    # Define vision model function (Grok 4 supports multimodal)
    def vision_model_func(
        prompt,
        system_prompt=None,
        history_messages=[],
        image_data=None,
        messages=None,
        **kwargs,
    ):
        # If messages format is provided (for multimodal VLM enhanced query), use it directly
        if messages:
            return openai_complete_if_cache(
                "grok-4-fast-reasoning",
                "",
                system_prompt=None,
                history_messages=[],
                messages=messages,
                api_key=xai_api_key,
                base_url=xai_base_url,
                **kwargs,
            )
        # Traditional single image format
        elif image_data:
            return openai_complete_if_cache(
                "grok-4-fast-reasoning",
                "",
                system_prompt=None,
                history_messages=[],
                messages=[
                    {"role": "system", "content": system_prompt}
                    if system_prompt
                    else None,
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                },
                            },
                        ],
                    }
                    if image_data
                    else {"role": "user", "content": prompt},
                ],
                api_key=xai_api_key,
                base_url=xai_base_url,
                **kwargs,
            )
        # Pure text format
        else:
            return llm_model_func(prompt, system_prompt, history_messages, **kwargs)
    
    # Define embedding function
    embedding_func = EmbeddingFunc(
        embedding_dim=3072,
        max_token_size=8192,
        func=lambda texts: openai_embed(
            texts,
            model="text-embedding-3-large",
            api_key=openai_api_key,
        ),
    )
    
    # Initialize RAGAnything (following official example pattern)
    rag = RAGAnything(
        config=config,
        llm_model_func=llm_model_func,
        vision_model_func=vision_model_func,
        embedding_func=embedding_func,
    )
    
    # Process document
    print(f"\n🚀 Starting multimodal document processing...")
    print("   This will:")
    print("   1. Parse PDF with MinerU (images, tables, equations)")
    print("   2. Extract entities using LightRAG with 12 govcon types")
    print("   3. Build knowledge graph in ./rag_storage")
    print("   4. Make document queryable via WebUI\n")
    
    await rag.process_document_complete(
        file_path=file_path,
        output_dir="./output",
        parse_method="auto"
    )
    
    print("\n✅ Processing complete!")
    
    print("\n🌐 Access the WebUI:")
    print(f"   - URL: http://localhost:9621/webui")
    print(f"   - Query the document through the WebUI")
    print(f"   - View knowledge graph visualization")
    
    # Run test queries
    print("\n🔍 Running test queries...")
    
    test_queries = [
        "What are the key evaluation factors in this RFP?",
        "What is the period of performance?",
        "What are the main deliverables?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        result = await rag.aquery(query, mode="hybrid")
        print(f"💡 Answer: {result[:300]}...")
    
    print("\n" + "="*80)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python process_rfp.py <path_to_rfp.pdf>")
        print("\nExample:")
        print("  python process_rfp.py ./inputs/__enqueued__/_N6945025R0003.pdf")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Run processing
    asyncio.run(process_rfp(file_path))


if __name__ == "__main__":
    main()
