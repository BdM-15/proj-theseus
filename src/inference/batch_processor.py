"""
Unified Batch Processor for LLM Operations
==========================================

Centralizes all batching logic to avoid duplication across Phase 6 and Phase 7.
Provides a single, configurable interface for processing large entity sets.

Usage:
    from src.inference.batch_processor import BatchProcessor
    
    processor = BatchProcessor(llm_func=my_llm_function, batch_size=50)
    
    # Process entities in batches
    results = await processor.process_batches(
        items=large_entity_list,
        process_fn=my_processing_function,
        batch_name="Entity Retyping"
    )
"""

import logging
from typing import List, Dict, Callable, Awaitable, Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Input type
R = TypeVar('R')  # Result type


class BatchProcessor:
    """
    Unified batch processor for LLM operations.
    
    Handles:
    - Progress logging (Batch 1/31: Processing 50 items...)
    - Error handling per batch (continue on failure)
    - Result aggregation across batches
    - Configurable batch size
    """
    
    def __init__(
        self,
        llm_func: Callable[[str, str], Awaitable[str]],
        batch_size: int = 50,
        log_progress: bool = True
    ):
        """
        Initialize batch processor.
        
        Args:
            llm_func: Async LLM function (prompt, system_prompt) -> response
            batch_size: Number of items per batch (default: 50)
            log_progress: Whether to log batch progress (default: True)
        """
        self.llm_func = llm_func
        self.batch_size = batch_size
        self.log_progress = log_progress
    
    async def process_batches(
        self,
        items: List[T],
        process_fn: Callable[[List[T], Callable], Awaitable[R]],
        batch_name: str = "Items",
        aggregate_fn: Callable[[List[R]], Any] = None
    ) -> Any:
        """
        Process items in batches using provided processing function.
        
        Args:
            items: List of items to process
            process_fn: Async function that processes one batch
                       Signature: async def process_batch(batch: List[T], llm_func) -> R
            batch_name: Name for logging (e.g., "Requirements", "Entities")
            aggregate_fn: Optional function to aggregate batch results
                         If None, returns list of batch results
        
        Returns:
            Aggregated results (list if aggregate_fn=None)
        
        Example:
            async def retype_batch(entities, llm_func):
                # ... LLM call to retype entities ...
                return {entity.name: new_type for entity in entities}
            
            all_retypings = await processor.process_batches(
                items=entities,
                process_fn=retype_batch,
                batch_name="Entity Retyping",
                aggregate_fn=lambda results: {k:v for r in results for k,v in r.items()}
            )
        """
        if not items:
            logger.info(f"  No {batch_name.lower()} to process")
            return [] if aggregate_fn is None else aggregate_fn([])
        
        total_batches = (len(items) + self.batch_size - 1) // self.batch_size
        batch_results = []
        
        # Log batch setup
        if self.log_progress:
            if len(items) > self.batch_size:
                logger.info(
                    f"    📦 Processing {len(items)} {batch_name.lower()} "
                    f"in {total_batches} batches of {self.batch_size}"
                )
            else:
                logger.info(f"    Processing {len(items)} {batch_name.lower()}")
        
        # Process batches
        for batch_idx in range(0, len(items), self.batch_size):
            batch = items[batch_idx:batch_idx + self.batch_size]
            batch_num = (batch_idx // self.batch_size) + 1
            
            # Log batch progress (only if multiple batches)
            if self.log_progress and total_batches > 1:
                logger.info(
                    f"    🔄 Batch {batch_num}/{total_batches}: "
                    f"Processing {len(batch)} {batch_name.lower()}..."
                )
            
            try:
                # Call processing function with batch and LLM
                result = await process_fn(batch, self.llm_func)
                batch_results.append(result)
                
            except Exception as e:
                logger.error(
                    f"    ❌ Batch {batch_num}/{total_batches} failed: {e}"
                )
                # Continue processing remaining batches
                batch_results.append(None)
        
        # Aggregate results
        if aggregate_fn:
            # Filter out None results from failed batches
            valid_results = [r for r in batch_results if r is not None]
            return aggregate_fn(valid_results)
        else:
            return batch_results


def merge_dict_results(batch_results: List[Dict]) -> Dict:
    """
    Aggregate function for dict results (e.g., entity retyping maps).
    
    Args:
        batch_results: List of dicts from each batch
    
    Returns:
        Merged dict with all key-value pairs
    """
    merged = {}
    for result in batch_results:
        if result:
            merged.update(result)
    return merged


def flatten_list_results(batch_results: List[List]) -> List:
    """
    Aggregate function for list results (e.g., relationships).
    
    Args:
        batch_results: List of lists from each batch
    
    Returns:
        Flattened list with all items
    """
    flattened = []
    for result in batch_results:
        if result:
            flattened.extend(result)
    return flattened
